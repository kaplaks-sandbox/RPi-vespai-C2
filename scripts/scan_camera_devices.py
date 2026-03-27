#!/usr/bin/env python3
"""
Scan PCI/USB camera devices and emit VespAI-ready configuration output.

This utility inspects:
- lspci (PCI camera/video devices)
- lsusb (USB camera devices)
- /sys/class/video4linux + /dev/video* (actual capture nodes)

Primary goal: produce output that can be copied into .env or CLI args for VespAI.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional


CAMERA_KEYWORDS = (
    "camera",
    "webcam",
    "imaging",
    "uvc",
    "video",
    "capture",
    "picamera",
)


@dataclass
class PciDevice:
    slot: str
    description: str


@dataclass
class UsbDevice:
    bus_device: str
    vendor_product: str
    description: str


@dataclass
class VideoNode:
    path: str
    name: str
    bus_type: str
    driver: str
    node_index: Optional[int] = None
    usb_device_key: str = ""


def run_command(args: List[str]) -> str:
    try:
        result = subprocess.run(
            args,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return ""

    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def looks_like_camera(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in CAMERA_KEYWORDS)


def parse_lspci() -> List[PciDevice]:
    output = run_command(["lspci", "-nn"])
    devices: List[PciDevice] = []
    if not output:
        return devices

    for line in output.splitlines():
        if not line.strip():
            continue
        if not looks_like_camera(line):
            continue

        parts = line.split(" ", 1)
        if len(parts) != 2:
            continue
        devices.append(PciDevice(slot=parts[0], description=parts[1].strip()))

    return devices


def parse_lsusb() -> List[UsbDevice]:
    output = run_command(["lsusb"])
    devices: List[UsbDevice] = []
    if not output:
        return devices

    pattern = re.compile(
        r"^Bus\s+(\d+)\s+Device\s+(\d+):\s+ID\s+([0-9a-fA-F]{4}:[0-9a-fA-F]{4})\s+(.+)$"
    )

    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue

        match = pattern.match(line)
        if not match:
            continue

        bus, device, vidpid, desc = match.groups()
        if not looks_like_camera(desc):
            continue

        devices.append(
            UsbDevice(
                bus_device=f"{bus}:{device}",
                vendor_product=vidpid.lower(),
                description=desc.strip(),
            )
        )

    return devices


def discover_video_nodes() -> List[VideoNode]:
    nodes: List[VideoNode] = []
    base = Path("/sys/class/video4linux")
    if not base.exists():
        return nodes

    for video_dir in sorted(base.glob("video*")):
        dev_path = Path("/dev") / video_dir.name
        if not dev_path.exists():
            continue

        name_path = video_dir / "name"
        name = ""
        if name_path.exists():
            try:
                name = name_path.read_text(encoding="utf-8", errors="ignore").strip()
            except OSError:
                name = ""

        device_path = video_dir / "device"
        real_device = ""
        if device_path.exists():
            try:
                real_device = os.path.realpath(str(device_path)).lower()
            except OSError:
                real_device = ""

        driver_path = video_dir / "device" / "driver"
        driver = ""
        if driver_path.exists():
            try:
                driver = os.path.basename(os.path.realpath(str(driver_path)))
            except OSError:
                driver = ""

        node_index: Optional[int] = None
        index_path = video_dir / "index"
        if index_path.exists():
            try:
                raw_index = index_path.read_text(encoding="utf-8", errors="ignore").strip()
                if raw_index:
                    node_index = int(raw_index)
            except (OSError, ValueError):
                node_index = None

        usb_device_key = ""
        if real_device:
            # Normalize USB interface path like ".../1-2:1.0" to physical device key "1-2".
            usb_match = re.search(r"/(\d+-\d+(?:\.\d+)*)(?::\d+\.\d+)?$", real_device)
            if usb_match:
                usb_device_key = usb_match.group(1)

        if "usb" in real_device:
            bus_type = "usb"
        elif any(x in real_device for x in ("pci", "platform", "soc")):
            bus_type = "pci_or_soc"
        else:
            bus_type = "unknown"

        nodes.append(
            VideoNode(
                path=str(dev_path),
                name=name,
                bus_type=bus_type,
                driver=driver,
                node_index=node_index,
                usb_device_key=usb_device_key,
            )
        )

    return nodes


def detect_picamera_available() -> bool:
    """Return True when libcamera/rpicam reports at least one attached Pi camera sensor."""
    probes = [
        ["libcamera-hello", "--list-cameras"],
        ["rpicam-hello", "--list-cameras"],
    ]
    for probe in probes:
        output = run_command(probe)
        if not output:
            continue
        if "available cameras" in output.lower() and " : " in output:
            return True
    return False


def unique_usb_capture_nodes(video_nodes: List[VideoNode]) -> List[VideoNode]:
    """Pick one preferred /dev/video node per physical USB camera device."""
    usb_nodes = [node for node in video_nodes if node.bus_type == "usb"]
    if not usb_nodes:
        return []

    grouped: Dict[str, List[VideoNode]] = {}
    for node in usb_nodes:
        key = node.usb_device_key or node.path
        grouped.setdefault(key, []).append(node)

    selected: List[VideoNode] = []
    for key in sorted(grouped.keys()):
        group = grouped[key]
        # Prefer index 0 stream node, then lowest numeric index, then path sort.
        preferred = sorted(
            group,
            key=lambda node: (
                0 if node.node_index == 0 else 1,
                node.node_index if node.node_index is not None else 99,
                node.path,
            ),
        )[0]
        selected.append(preferred)

    return selected


def recommend_config(video_nodes: List[VideoNode], usb_devices: List[UsbDevice], pci_devices: List[PciDevice]) -> Dict[str, str]:
    camera1_source = "auto"
    camera1_device = ""

    usb_nodes = unique_usb_capture_nodes(video_nodes)
    picamera_available = detect_picamera_available()
    if usb_nodes:
        camera1_source = "usb"
        camera1_device = usb_nodes[0].path
    elif picamera_available or any("bcm" in dev.description.lower() or "camera" in dev.description.lower() for dev in pci_devices):
        camera1_source = "picamera2"
    elif usb_devices:
        camera1_source = "usb"

    env: Dict[str, str] = {
        "VESPAI_CAMERA1_SOURCE": camera1_source,
        "VESPAI_CAMERA2_ENABLED": "false",
    }
    if camera1_device:
        env["VESPAI_CAMERA1_DEVICE"] = camera1_device

    # If two unique USB cameras are available, suggest enabling camera2 as USB.
    if len(usb_nodes) >= 2:
        env["VESPAI_CAMERA2_ENABLED"] = "true"
        env["VESPAI_CAMERA2_SOURCE"] = "usb"
        env["VESPAI_CAMERA2_DEVICE"] = usb_nodes[1].path
    elif len(usb_nodes) == 1 and picamera_available:
        # Mixed setup: one USB camera + one Raspberry Pi CSI camera.
        env["VESPAI_CAMERA2_ENABLED"] = "true"
        env["VESPAI_CAMERA2_SOURCE"] = "picamera2"

    return env


def to_yaml_like(data: Dict) -> str:
    lines: List[str] = []

    def render(obj, indent: int = 0, key: Optional[str] = None):
        prefix = " " * indent
        if isinstance(obj, dict):
            if key is not None:
                lines.append(f"{prefix}{key}:")
                indent += 2
                prefix = " " * indent
            for k, v in obj.items():
                render(v, indent, str(k))
        elif isinstance(obj, list):
            if key is not None:
                lines.append(f"{prefix}{key}:")
                indent += 2
                prefix = " " * indent
            for item in obj:
                if isinstance(item, (dict, list)):
                    lines.append(f"{prefix}-")
                    render(item, indent + 2)
                else:
                    lines.append(f"{prefix}- {item}")
        else:
            if key is None:
                lines.append(f"{prefix}{obj}")
            else:
                lines.append(f"{prefix}{key}: {obj}")

    render(data)
    return "\n".join(lines)


def build_report() -> Dict:
    pci_devices = parse_lspci()
    usb_devices = parse_lsusb()
    video_nodes = discover_video_nodes()

    recommended_env = recommend_config(video_nodes, usb_devices, pci_devices)
    recommended_cli = [
        f"--camera1-source {recommended_env['VESPAI_CAMERA1_SOURCE']}"
    ]
    if "VESPAI_CAMERA1_DEVICE" in recommended_env:
        recommended_cli.append(
            f"--camera1-device {recommended_env['VESPAI_CAMERA1_DEVICE']}"
        )
    if recommended_env.get("VESPAI_CAMERA2_ENABLED", "false").lower() == "true":
        recommended_cli.append("--camera2-enabled true")
        if "VESPAI_CAMERA2_SOURCE" in recommended_env:
            recommended_cli.append(
                f"--camera2-source {recommended_env['VESPAI_CAMERA2_SOURCE']}"
            )
        if "VESPAI_CAMERA2_DEVICE" in recommended_env:
            recommended_cli.append(
                f"--camera2-device {recommended_env['VESPAI_CAMERA2_DEVICE']}"
            )

    return {
        "recommended_env": recommended_env,
        "recommended_cli": " ".join(recommended_cli),
        "pci_camera_devices": [asdict(dev) for dev in pci_devices],
        "usb_camera_devices": [asdict(dev) for dev in usb_devices],
        "video_nodes": [asdict(node) for node in video_nodes],
    }


def print_env_snippet(report: Dict) -> None:
    env = report["recommended_env"]
    print("# Paste into .env")
    print(f"VESPAI_CAMERA1_SOURCE={env['VESPAI_CAMERA1_SOURCE']}")
    if "VESPAI_CAMERA1_DEVICE" in env:
        print(f"VESPAI_CAMERA1_DEVICE={env['VESPAI_CAMERA1_DEVICE']}")
    print(f"VESPAI_CAMERA2_ENABLED={env.get('VESPAI_CAMERA2_ENABLED', 'false')}")
    if "VESPAI_CAMERA2_SOURCE" in env:
        print(f"VESPAI_CAMERA2_SOURCE={env['VESPAI_CAMERA2_SOURCE']}")
    if "VESPAI_CAMERA2_DEVICE" in env:
        print(f"VESPAI_CAMERA2_DEVICE={env['VESPAI_CAMERA2_DEVICE']}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan lspci/lsusb/video nodes and output camera config for VespAI"
    )
    parser.add_argument(
        "--format",
        choices=("text", "json", "yaml", "env"),
        default="text",
        help="Output format",
    )
    args = parser.parse_args()

    report = build_report()

    if args.format == "json":
        print(json.dumps(report, indent=2))
    elif args.format == "yaml":
        print(to_yaml_like(report))
    elif args.format == "env":
        print_env_snippet(report)
    else:
        print("=== Recommended VespAI camera config ===")
        print_env_snippet(report)
        print("")
        print(f"CLI hint: {report['recommended_cli']}")
        print("")
        print("=== Detected /dev/video* nodes ===")
        for node in report["video_nodes"]:
            print(
                f"- {node['path']}: name='{node['name']}', bus={node['bus_type']}, driver='{node['driver']}'"
            )
        print("")
        print("=== lspci camera-related entries ===")
        if report["pci_camera_devices"]:
            for dev in report["pci_camera_devices"]:
                print(f"- {dev['slot']} {dev['description']}")
        else:
            print("- none")

        print("")
        print("=== lsusb camera-related entries ===")
        if report["usb_camera_devices"]:
            for dev in report["usb_camera_devices"]:
                print(
                    f"- {dev['bus_device']} id={dev['vendor_product']} {dev['description']}"
                )
        else:
            print("- none")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
