#!/usr/bin/env python3
"""Diagnostic probe for PiCamera color shifts across processing libraries.

This script captures one frame from Picamera2 and runs it through multiple
transform variants that mirror common VespAI paths (RGB/BGR conversion,
OpenCV resize, JPEG encode/decode). It writes all outputs and a metrics report
so yellow->blue shifts can be isolated to a specific step.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import cv2
import numpy as np


@dataclass
class ProbeResult:
    name: str
    path: str
    metrics: Dict[str, float]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe color pipeline for PiCamera frames")
    parser.add_argument(
        "--out-dir",
        default="monitor/debug_color_probe",
        help="Directory to store probe images and report",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=72,
        help="JPEG quality used for encode/decode variants",
    )
    parser.add_argument(
        "--capture-timeout-ms",
        type=int,
        default=1200,
        help="Capture timeout for rpicam-still reference shot",
    )
    return parser.parse_args()


def clamp_quality(value: int) -> int:
    return max(10, min(100, int(value)))


def color_metrics_bgr(image: np.ndarray) -> Dict[str, float]:
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hue = hsv[:, :, 0]
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]

    mask = (sat > 50) & (val > 60)
    selected = hue[mask]
    if selected.size == 0:
        return {"pixels": 0}

    yellow = int(((selected >= 15) & (selected <= 45)).sum())
    blue = int(((selected >= 90) & (selected <= 130)).sum())
    total = int(selected.size)

    return {
        "pixels": total,
        "yellow_pct": round(100.0 * yellow / total, 2),
        "blue_pct": round(100.0 * blue / total, 2),
        "mean_hue": round(float(selected.mean()), 2),
    }


def write_bgr(path: Path, image_bgr: np.ndarray) -> None:
    cv2.imwrite(str(path), image_bgr)


def encode_decode_jpeg_bgr(image_bgr: np.ndarray, quality: int) -> np.ndarray:
    ok, encoded = cv2.imencode(".jpg", image_bgr, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise RuntimeError("cv2.imencode failed")
    decoded = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if decoded is None:
        raise RuntimeError("cv2.imdecode failed")
    return decoded


def capture_reference_rpicam(path: Path, timeout_ms: int) -> Optional[str]:
    if shutil.which("rpicam-still") is None:
        return "rpicam-still not found"

    cmd = ["rpicam-still", "-n", "--timeout", str(timeout_ms), "-o", str(path)]
    try:
        completed = subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        return stderr or f"rpicam-still failed with code {exc.returncode}"
    return None


def capture_picamera2_rgb() -> np.ndarray:
    from picamera2 import Picamera2

    picam = Picamera2()
    try:
        config = picam.create_video_configuration(
            main={"size": (1280, 720), "format": "RGB888"},
            controls={"FrameRate": 30},
        )
        picam.configure(config)
        picam.start()
        frame = picam.capture_array()
    finally:
        try:
            picam.stop()
        except Exception:
            pass
        try:
            picam.close()
        except Exception:
            pass

    if frame is None:
        raise RuntimeError("Picamera2 returned no frame")
    if len(frame.shape) != 3 or frame.shape[2] != 3:
        raise RuntimeError(f"Unexpected frame shape: {frame.shape}")
    return frame


def main() -> int:
    args = parse_args()
    quality = clamp_quality(args.quality)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    report = {
        "timestamp": ts,
        "quality": quality,
        "results": [],
        "notes": [],
    }

    # Optional direct libcamera reference shot.
    direct_path = out_dir / f"direct_rpicam_{ts}.png"
    ref_error = capture_reference_rpicam(direct_path, args.capture_timeout_ms)
    if ref_error:
        report["notes"].append(f"direct_reference_error: {ref_error}")
    elif direct_path.exists():
        direct_img = cv2.imread(str(direct_path), cv2.IMREAD_COLOR)
        if direct_img is not None:
            report["results"].append(
                ProbeResult("direct_rpicam", str(direct_path), color_metrics_bgr(direct_img)).__dict__
            )

    # Capture one frame from Picamera2 as RGB888.
    frame_rgb = capture_picamera2_rgb()

    # Variant A: Treat frame as BGR without conversion (tests if source is already BGR-like).
    a_bgr_assumed = frame_rgb.copy()
    a_path = out_dir / f"a_raw_assumed_bgr_{ts}.png"
    write_bgr(a_path, a_bgr_assumed)
    report["results"].append(
        ProbeResult("a_raw_assumed_bgr", str(a_path), color_metrics_bgr(a_bgr_assumed)).__dict__
    )

    # Variant B: Convert RGB->BGR (matches current VespAI camera path for Picamera2).
    b_rgb_to_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
    b_path = out_dir / f"b_rgb_to_bgr_{ts}.png"
    write_bgr(b_path, b_rgb_to_bgr)
    report["results"].append(
        ProbeResult("b_rgb_to_bgr", str(b_path), color_metrics_bgr(b_rgb_to_bgr)).__dict__
    )

    # Variant C: RGB->BGR then VespAI-like web resize and JPEG roundtrip.
    c_pipeline = cv2.resize(b_rgb_to_bgr, (480, 270), interpolation=cv2.INTER_AREA)
    c_pipeline = encode_decode_jpeg_bgr(c_pipeline, quality)
    c_path = out_dir / f"c_rgb_to_bgr_resize_jpeg_{ts}.png"
    write_bgr(c_path, c_pipeline)
    report["results"].append(
        ProbeResult("c_rgb_to_bgr_resize_jpeg", str(c_path), color_metrics_bgr(c_pipeline)).__dict__
    )

    # Variant D: No RGB->BGR, then resize and JPEG roundtrip.
    d_pipeline = cv2.resize(a_bgr_assumed, (480, 270), interpolation=cv2.INTER_AREA)
    d_pipeline = encode_decode_jpeg_bgr(d_pipeline, quality)
    d_path = out_dir / f"d_no_swap_resize_jpeg_{ts}.png"
    write_bgr(d_path, d_pipeline)
    report["results"].append(
        ProbeResult("d_no_swap_resize_jpeg", str(d_path), color_metrics_bgr(d_pipeline)).__dict__
    )

    report_path = out_dir / f"probe_report_{ts}.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Probe complete. Report: {report_path}")
    for item in report["results"]:
        print(f"- {item['name']}: {item['metrics']}")
    if report["notes"]:
        for note in report["notes"]:
            print(f"NOTE: {note}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
