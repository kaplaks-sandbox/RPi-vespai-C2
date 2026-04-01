#!/usr/bin/env python3
"""
VespAI Main Application

Modular main application that coordinates all VespAI components for hornet detection.
This replaces the monolithic web_preview.py with a clean, testable architecture.

Author: Jakob Zeise (Zeise Digital)
Modified: Andre Jordaan
Version: 2.0
"""

import logging
import sys
import time
import threading
import signal
import os
import importlib.util
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Any, Tuple
from collections import deque

# Core modules
from .core.config import create_config_from_args
from .core.detection import CameraManager, ModelManager, DetectionProcessor
from .sms.lox24 import create_sms_manager_from_env
from .push_notification.pushover import create_push_manager_from_env
from .web.routes import register_routes

# External dependencies
try:
    from flask import Flask
    import cv2
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Please install dependencies with: pip install -r requirements.txt")
    sys.exit(1)

class FriendlyLoggerNameFormatter(logging.Formatter):
    """Format logger names using more readable labels in log output."""

    LOGGER_NAME_MAP = {
        'werkzeug': 'web-server',
    }

    def format(self, record: logging.LogRecord) -> str:
        original_name = record.name
        record.name = self.LOGGER_NAME_MAP.get(record.name, record.name)
        try:
            return super().format(record)
        finally:
            record.name = original_name


# Set up logging
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "vespai.log"

log_formatter = FriendlyLoggerNameFormatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(log_formatter)

file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
file_handler.setFormatter(log_formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[stream_handler, file_handler],
)
logger = logging.getLogger(__name__)


class VespAIApplication:
    """
    Main VespAI application that orchestrates all components.
    
    Provides a clean, modular architecture for hornet detection with
    camera management, model inference, web interface, and SMS alerts.
    """
    
    def __init__(self):
        """Initialize the VespAI application."""
        self.config = None
        self.camera_manager = None
        self.camera_managers: Dict[str, CameraManager] = {}
        self.camera_frame_counts: Dict[str, int] = {}
        self.model_manager = None
        self.detection_processor = None
        self.sms_manager = None
        self.push_manager = None
        self.flask_app = None
        self.web_thread = None
        self.running = False
        self.source_lock = threading.Lock()
        self.current_input_mode = 'camera'
        self.current_dataset_path = ''
        self.camera_modes: Dict[str, Dict[str, str]] = {}
        self.camera_enabled: Dict[str, bool] = {}
        self.camera_aliases: Dict[str, str] = {}
        self.camera_last_inference_ts: Dict[str, float] = {}
        self.dataset_executor = None
        self.dataset_prediction_queue = deque()
        self.perf_samples = deque(maxlen=4096)
        self.perf_window_seconds = 60.0
        self.perf_lock = threading.Lock()
        
        # Global state for web interface
        self.web_frame = None
        self.web_frames: Dict[str, Any] = {}
        self.web_lock = threading.Lock()
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def initialize(self, args=None):
        """
        Initialize all application components.
        
        Args:
            args: Command line arguments (None for sys.argv)
        """
        logger.info("Initializing VespAI application...")
        
        # Load configuration
        self.config = create_config_from_args(args)
        self.config.print_summary()
        
        # Initialize components
        self._initialize_camera()
        self._initialize_model()
        self._initialize_detection_processor()
        self._initialize_sms()
        self._initialize_push()
        
        if self.config.get('enable_web'):
            self._initialize_web_interface()
        
        logger.info("VespAI application initialized successfully")
    
    def _initialize_camera(self):
        """Initialize camera manager(s)."""
        logger.info("Initializing camera(s)...")
        resolution = self.config.get_camera_resolution()

        self.camera_managers = {}
        self.camera_modes = {}
        self.camera_enabled = {}
        self.camera_aliases = {}
        self.camera_frame_counts = {}

        camera_profiles = self.config.get_camera_profiles()
        video_file = self.config.get('video_file')
        for camera_id, profile in camera_profiles.items():
            manager = CameraManager(
                resolution,
                camera_source=profile.get('source', self.config.get('camera_source', 'auto')),
                preferred_device=profile.get('device', ''),
                autofocus_enabled=bool(profile.get('autofocus', True)),
                camerapi_focus_mode=self.config.get('camerapi_focus_mode', 'manual'),
                camerapi_focus_distance_m=float(self.config.get('camerapi_focus_distance_m', 0.13)),
                camerapi_awb_mode=self.config.get('camerapi_awb_mode', 'auto'),
                camerapi_awb_red_gain=float(self.config.get('camerapi_awb_red_gain', 0.0)),
                camerapi_awb_blue_gain=float(self.config.get('camerapi_awb_blue_gain', 0.0)),
                camerapi_color_order=self.config.get('camerapi_color_order', 'bgr'),
            )

            # In dataset mode, initialize all configured cameras with the same dataset source.
            if video_file:
                manager.initialize_camera(video_file)
                dataset_path = video_file or self.config.get('dataset_path', '') or ''
                input_mode = 'dataset'
                self.current_input_mode = input_mode
                self.current_dataset_path = dataset_path
            else:
                manager.initialize_camera(None)
                input_mode = 'camera'
                dataset_path = ''

            self.camera_managers[camera_id] = manager
            self.camera_modes[camera_id] = {
                'mode': input_mode,
                'dataset_path': dataset_path,
            }
            self.camera_enabled[camera_id] = True
            fallback_alias = 'Camera 2' if camera_id == 'camera2' else 'Camera 1'
            alias_raw = profile.get('alias', fallback_alias)
            self.camera_aliases[camera_id] = str(alias_raw or fallback_alias).strip()[:16] or fallback_alias
            self.camera_frame_counts[camera_id] = 0

        # Keep legacy alias pointing to camera1 manager for compatibility with routes/helpers.
        self.camera_manager = self.camera_managers.get('camera1')
        self.camera_last_inference_ts = {camera_id: 0.0 for camera_id in self.camera_managers}

    def get_input_source_state(self) -> Dict[str, Any]:
        """Return current runtime input source state for web API/UI."""
        primary_state = self.camera_modes.get('camera1', {
            'mode': self.current_input_mode,
            'dataset_path': self.current_dataset_path,
        })
        return {
            'mode': primary_state.get('mode', 'camera'),
            'dataset_path': primary_state.get('dataset_path', ''),
            'camera_modes': self.camera_modes,
            'camera_enabled': self.camera_enabled,
            'camera_aliases': self.camera_aliases,
        }

    def set_camera_enabled(self, camera_id: str, enabled: bool) -> Tuple[bool, str]:
        """Enable or disable a camera at runtime to reduce system load."""
        if camera_id not in self.camera_modes:
            return False, f"Unknown camera_id: {camera_id}"

        target_enabled = bool(enabled)
        if self.camera_enabled.get(camera_id, True) == target_enabled:
            return True, f"{camera_id} already {'enabled' if target_enabled else 'disabled'}"

        with self.source_lock:
            manager = self.camera_managers.get(camera_id)
            if manager is None:
                return False, f"Camera manager missing for {camera_id}"

            if not target_enabled:
                try:
                    manager.release()
                except Exception:
                    pass

                self.camera_enabled[camera_id] = False
                camera_stats = self.detection_processor._ensure_camera_stats(camera_id)
                camera_stats['online'] = False
                camera_stats['status'] = 'disabled'
                camera_stats['fps'] = 0.0
                camera_stats['last_frame_age_s'] = -1.0
                camera_stats['current_frame_source'] = 'disabled'

                with self.web_lock:
                    self.web_frames[camera_id] = None
                    if camera_id == 'camera1':
                        self.web_frame = None

                # Remove queued async dataset predictions for disabled camera.
                if self.dataset_prediction_queue:
                    self.dataset_prediction_queue = deque(
                        item for item in self.dataset_prediction_queue if item[0] != camera_id
                    )

                return True, f"{camera_id} disabled"

            # Reinitialize camera when re-enabling.
            try:
                if self.current_input_mode == 'dataset':
                    manager.initialize_camera(self.current_dataset_path)
                else:
                    manager.initialize_camera(None)
            except Exception as error:
                self.camera_enabled[camera_id] = False
                return False, f"Failed to enable {camera_id}: {error}"

            self.camera_enabled[camera_id] = True
            camera_stats = self.detection_processor._ensure_camera_stats(camera_id)
            camera_stats['status'] = 'online'
            camera_stats['current_frame_source'] = ''
            return True, f"{camera_id} enabled"

    def _resolve_dataset_path_candidate(self, raw_path: str) -> str:
        """Resolve a dataset path candidate and return it only when it exists."""
        candidate = str(raw_path or '').strip()
        if not candidate:
            return ''

        candidate_path = Path(candidate).expanduser()
        if candidate_path.exists():
            return str(candidate_path)

        project_candidate = (PROJECT_ROOT / candidate).resolve()
        if project_candidate.exists():
            return str(project_candidate)

        return ''

    def _find_default_dataset_path(self) -> str:
        """Find a sensible default dataset source from common project locations."""
        configured_candidates = [
            self.current_dataset_path,
            self.config.get('video_file') or '',
            self.config.get('dataset_path') or '',
            os.environ.get('VESPAI_DATASET_PATH') or '',
        ]

        for candidate in configured_candidates:
            resolved = self._resolve_dataset_path_candidate(candidate)
            if resolved:
                return resolved

        datasets_root = PROJECT_ROOT / 'datasets'
        if not datasets_root.exists():
            return ''

        video_suffixes = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.mjpg', '.mjpeg'}
        for video_path in sorted(datasets_root.rglob('*')):
            if video_path.is_file() and video_path.suffix.lower() in video_suffixes:
                return str(video_path)

        image_suffixes = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
        for dir_path in sorted(datasets_root.rglob('*')):
            if not dir_path.is_dir():
                continue
            has_images = any(
                child.is_file() and child.suffix.lower() in image_suffixes
                for child in dir_path.iterdir()
            )
            if has_images:
                return str(dir_path)

        tfrecord_available = importlib.util.find_spec('tfrecord') is not None
        if tfrecord_available:
            for tfrecord_path in sorted(datasets_root.rglob('*.tfrecord')):
                if tfrecord_path.is_file():
                    return str(tfrecord_path)

        return ''

    def switch_input_source(self, mode: str, dataset_path: str = '') -> Tuple[bool, str]:
        """Switch live input source between camera and dataset at runtime."""
        mode_normalized = (mode or '').strip().lower()
        if mode_normalized not in ('camera', 'dataset'):
            return False, "Invalid mode. Use 'camera' or 'dataset'."

        target_dataset_path = self._resolve_dataset_path_candidate(dataset_path)
        if mode_normalized == 'dataset' and not target_dataset_path:
            target_dataset_path = self._find_default_dataset_path()

        if mode_normalized == 'dataset' and not target_dataset_path:
            tfrecord_available = importlib.util.find_spec('tfrecord') is not None
            tfrecord_hint = ''
            if not tfrecord_available:
                tfrecord_hint = " Install dependency 'tfrecord' to use .tfrecord datasets."
            return False, (
                "Dataset path is required when mode is 'dataset'. "
                "Set VESPAI_DATASET_PATH or place a dataset under ./datasets."
                f"{tfrecord_hint}"
            )

        resolution = self.config.get_camera_resolution()

        with self.source_lock:
            new_managers: Dict[str, CameraManager] = {}
            old_managers: Dict[str, CameraManager] = {}

            for camera_id in list(self.camera_managers.keys()):
                camera_source = self.config.get(f'{camera_id}_source', self.config.get('camera_source', 'auto'))
                preferred_device = self.config.get(f'{camera_id}_device', '')
                new_manager = CameraManager(
                    resolution,
                    camera_source=camera_source,
                    preferred_device=preferred_device,
                    autofocus_enabled=bool(self.config.get(f'{camera_id}_autofocus', self.config.get('camera_autofocus', True))),
                    camerapi_focus_mode=self.config.get('camerapi_focus_mode', 'manual'),
                    camerapi_focus_distance_m=float(self.config.get('camerapi_focus_distance_m', 0.13)),
                    camerapi_awb_mode=self.config.get('camerapi_awb_mode', 'auto'),
                    camerapi_awb_red_gain=float(self.config.get('camerapi_awb_red_gain', 0.0)),
                    camerapi_awb_blue_gain=float(self.config.get('camerapi_awb_blue_gain', 0.0)),
                    camerapi_color_order=self.config.get('camerapi_color_order', 'bgr'),
                )

                initialize_with_dataset = mode_normalized == 'dataset' and self.camera_enabled.get(camera_id, True)
                init_source = target_dataset_path if initialize_with_dataset else None
                try:
                    new_manager.initialize_camera(init_source)
                except Exception as error:
                    for created_manager in new_managers.values():
                        try:
                            created_manager.release()
                        except Exception:
                            pass
                    return False, f"Failed to switch source on {camera_id}: {error}"

                old_managers[camera_id] = self.camera_managers.get(camera_id)
                new_managers[camera_id] = new_manager

            self.camera_managers.update(new_managers)
            self.camera_manager = self.camera_managers.get('camera1')

            if mode_normalized == 'camera':
                self.current_input_mode = 'camera'
                self.config.set('video_file', None)
                self.detection_processor.stats['current_frame_source'] = ''
                self.current_dataset_path = ''
                for camera_id in self.camera_modes.keys():
                    self.camera_modes[camera_id] = {'mode': 'camera', 'dataset_path': ''}
            else:
                self.current_input_mode = 'dataset'
                self.current_dataset_path = target_dataset_path
                self.config.set('video_file', target_dataset_path)
                self.config.set('dataset_path', target_dataset_path)
                self.detection_processor.stats['current_frame_source'] = ''
                for camera_id in self.camera_modes.keys():
                    self.camera_modes[camera_id] = {
                        'mode': 'dataset',
                        'dataset_path': target_dataset_path,
                    }

            with self.web_lock:
                self.web_frame = None
                for camera_id in self.camera_managers.keys():
                    self.web_frames[camera_id] = None

            for old_manager in old_managers.values():
                try:
                    old_manager.release()
                except Exception:
                    pass

        logger.info("Input source switched to %s", self.current_input_mode)
        return True, "Input source updated"

    def _record_perf_sample(
        self,
        camera_id: str,
        capture_ms: float = 0.0,
        inference_ms: float = 0.0,
        postprocess_ms: float = 0.0,
        web_ms: float = 0.0,
    ):
        """Record lightweight per-frame performance timings for rolling API summaries."""
        sample = {
            'ts': time.time(),
            'camera_id': camera_id,
            'capture_ms': max(0.0, float(capture_ms or 0.0)),
            'inference_ms': max(0.0, float(inference_ms or 0.0)),
            'postprocess_ms': max(0.0, float(postprocess_ms or 0.0)),
            'web_ms': max(0.0, float(web_ms or 0.0)),
        }
        with self.perf_lock:
            self.perf_samples.append(sample)

    def get_perf_breakdown(self, window_s: Optional[float] = None) -> Dict[str, Any]:
        """Return rolling performance breakdown for capture/inference/postprocess/web sections."""
        if window_s is None:
            window = float(self.perf_window_seconds)
        else:
            window = max(1.0, min(float(window_s), 600.0))

        cutoff = time.time() - window
        with self.perf_lock:
            relevant = [sample for sample in self.perf_samples if sample.get('ts', 0.0) >= cutoff]

        sections = ('capture_ms', 'inference_ms', 'postprocess_ms', 'web_ms')
        totals = {section: round(sum(float(sample.get(section, 0.0)) for sample in relevant), 3) for section in sections}
        total_ms = sum(totals.values())

        percentages: Dict[str, float] = {}
        averages: Dict[str, float] = {}
        for section in sections:
            section_total = totals[section]
            percentages[section.replace('_ms', '')] = round((section_total / total_ms) * 100.0, 2) if total_ms > 0 else 0.0
            averages[section.replace('_ms', '')] = round((section_total / len(relevant)), 3) if relevant else 0.0

        per_camera: Dict[str, Dict[str, float]] = {}
        for sample in relevant:
            camera_id = str(sample.get('camera_id', 'unknown'))
            camera_totals = per_camera.setdefault(
                camera_id,
                {'capture_ms': 0.0, 'inference_ms': 0.0, 'postprocess_ms': 0.0, 'web_ms': 0.0, 'samples': 0},
            )
            camera_totals['samples'] += 1
            for section in sections:
                camera_totals[section] += float(sample.get(section, 0.0) or 0.0)

        for camera_id, camera_totals in per_camera.items():
            camera_total_ms = (
                camera_totals['capture_ms']
                + camera_totals['inference_ms']
                + camera_totals['postprocess_ms']
                + camera_totals['web_ms']
            )
            camera_totals['total_ms'] = round(camera_total_ms, 3)
            camera_totals['capture_ms'] = round(camera_totals['capture_ms'], 3)
            camera_totals['inference_ms'] = round(camera_totals['inference_ms'], 3)
            camera_totals['postprocess_ms'] = round(camera_totals['postprocess_ms'], 3)
            camera_totals['web_ms'] = round(camera_totals['web_ms'], 3)
            camera_totals['inference_pct'] = round((camera_totals['inference_ms'] / camera_total_ms) * 100.0, 2) if camera_total_ms > 0 else 0.0

        return {
            'window_seconds': window,
            'sample_count': len(relevant),
            'totals_ms': {
                'capture': totals['capture_ms'],
                'inference': totals['inference_ms'],
                'postprocess': totals['postprocess_ms'],
                'web': totals['web_ms'],
                'total': round(total_ms, 3),
            },
            'avg_ms_per_sample': averages,
            'percentages': percentages,
            'per_camera': per_camera,
        }
    
    def _initialize_model(self):
        """Initialize model manager."""
        logger.info("Initializing detection model...")
        model_path = self.config.get('model_path')
        confidence = self.config.get('confidence_threshold')

        class_map = self.config.get('class_map', '')
        if class_map:
            os.environ['VESPAI_CLASS_MAP'] = class_map
        
        self.model_manager = ModelManager(model_path, confidence)
        self.model_manager.load_model()
    
    def _initialize_detection_processor(self):
        """Initialize detection processor."""
        logger.info("Initializing detection processor...")
        self.detection_processor = DetectionProcessor(
            tracking_mode=self.config.get('tracking_mode', 'off'),
            web_preview_size=self.config.get('web_preview_size', '960x540'),
            preview_quality=self.config.get('current_frame_quality', 82),
            camera_aliases=self.camera_aliases,
        )
        if self.model_manager:
            self.detection_processor.set_class_names(
                self.model_manager.class_names,
                self.config.get('class_map', ''),
            )
    
    def _initialize_sms(self):
        """Initialize SMS manager."""
        if self.config.get('enable_sms'):
            logger.info("Initializing SMS alerts...")
            self.sms_manager = create_sms_manager_from_env()
            if self.sms_manager:
                logger.info("SMS alerts enabled")
            else:
                logger.warning("SMS configuration incomplete - alerts disabled")
        else:
            logger.info("SMS alerts disabled")

    def _initialize_push(self):
        """Initialize push notification manager."""
        if self.config.get('enable_push'):
            logger.info("Initializing push alerts...")
            self.push_manager = create_push_manager_from_env()
            if self.push_manager:
                logger.info("Push alerts enabled")
            else:
                logger.warning("Push configuration incomplete - alerts disabled")
        else:
            logger.info("Push alerts disabled")
    
    def _initialize_web_interface(self):
        """Initialize Flask web interface."""
        logger.info("Initializing web interface...")
        
        # Configure Flask with template and static directories
        import os
        web_dir = os.path.join(os.path.dirname(__file__), 'web')
        template_dir = os.path.join(web_dir, 'templates')
        static_dir = os.path.join(web_dir, 'static')
        
        self.flask_app = Flask(__name__, 
                              template_folder=template_dir,
                              static_folder=static_dir,
                              static_url_path='/static')
        
        # Register web routes
        register_routes(
            self.flask_app,
            self.detection_processor.stats,
            self.detection_processor.hourly_detections,
            self
        )
        
        # Start web server in background thread (matching web_preview.py approach)
        web_config = self.config.get_web_config()
        self.web_thread = threading.Thread(
            target=self._run_web_server,
            args=(web_config['host'], web_config['port']),
            daemon=True  # Use daemon thread like original - auto-dies on main exit
        )
        self.web_thread.start()
        
        # Quick web server startup check
        time.sleep(0.5)
        logger.info("Web interface starting at %s", web_config['public_url'])
    
    def _run_web_server(self, host: str, port: int):
        """Run Flask web server (called in background thread) - simplified like web_preview.py."""
        try:
            # Match web_preview.py parameters exactly
            self.flask_app.run(host=host, port=port, threaded=True, debug=False)
        except Exception as e:
            logger.error("Web server error: %s", e)
    
    def run(self):
        """
        Run the main detection loop.
        
        This is the core application loop that processes camera frames,
        runs detection, handles alerts, and updates the web interface.
        """
        if not self._validate_initialization():
            logger.error("Application not properly initialized")
            return False
        
        logger.info("Starting VespAI detection system...")
        logger.info("Press Ctrl+C to stop")
        
        self.running = True
        frame_count = 0
        fps_start_time = time.time()
        fps_counter = 0
        per_camera_fps_counters: Dict[str, int] = {
            camera_id: 0 for camera_id in self.camera_managers
        }
        per_camera_fps_timers: Dict[str, float] = {
            camera_id: time.time() for camera_id in self.camera_managers
        }
        camera_stall_age_s = 3.0
        camera_offline_age_s = 15.0
        
        # Add watchdog timer for system health
        last_frame_time = time.time()
        last_stats_update = time.time()
        
        try:
            while self.running:
                loop_start = time.time()
                self._drain_completed_dataset_predictions()
                
                # Watchdog: Detect if system is hanging
                current_time = time.time()
                if current_time - last_frame_time > 30:  # No frame for 30 seconds
                    logger.warning("System appears to be hanging - attempting recovery...")
                    self._attempt_recovery()
                    last_frame_time = current_time
                
                camera_ids = list(self.camera_managers.keys())
                if not camera_ids:
                    logger.error("No active camera managers found")
                    self.running = False
                    break

                dataset_shared_mode = self.current_input_mode == 'dataset'
                shared_dataset_manager = None
                if dataset_shared_mode:
                    preferred_shared_id = None
                    if self.camera_enabled.get('camera1', True) and self.camera_managers.get('camera1'):
                        preferred_shared_id = 'camera1'
                    else:
                        for candidate_id in camera_ids:
                            if self.camera_enabled.get(candidate_id, True) and self.camera_managers.get(candidate_id):
                                preferred_shared_id = candidate_id
                                break
                    if preferred_shared_id:
                        shared_dataset_manager = self.camera_managers.get(preferred_shared_id)

                for camera_id in camera_ids:
                    if not self.camera_enabled.get(camera_id, True):
                        camera_stats = self.detection_processor._ensure_camera_stats(camera_id)
                        camera_stats['online'] = False
                        camera_stats['status'] = 'disabled'
                        camera_stats['fps'] = 0.0
                        camera_stats['current_frame_source'] = 'disabled'
                        camera_stats['last_frame_age_s'] = -1.0
                        continue

                    capture_ms = 0.0
                    inference_ms = 0.0
                    postprocess_ms = 0.0
                    web_ms = 0.0

                    camera_stats = self.detection_processor._ensure_camera_stats(camera_id)
                    now = time.time()
                    last_ts = float(camera_stats.get('last_frame_ts', 0.0) or 0.0)
                    if last_ts > 0.0:
                        age_s = max(0.0, now - last_ts)
                        camera_stats['last_frame_age_s'] = round(age_s, 1)
                        if age_s >= camera_offline_age_s:
                            camera_stats['online'] = False
                            camera_stats['status'] = 'offline'
                        elif age_s >= camera_stall_age_s:
                            camera_stats['online'] = False
                            camera_stats['status'] = 'stalled'

                    # Read frame from camera with timeout
                    frame_source_manager = None
                    try:
                        with self.source_lock:
                            active_camera_manager = self.camera_managers.get(camera_id)
                            if active_camera_manager is None:
                                continue

                            if dataset_shared_mode and shared_dataset_manager is not None:
                                frame_source_manager = shared_dataset_manager
                            else:
                                frame_source_manager = active_camera_manager

                            capture_started = time.time()
                            success, frame = frame_source_manager.read_frame()
                            capture_ms = (time.time() - capture_started) * 1000.0
                            source_exhausted = frame_source_manager.source_exhausted()
                            finite_source = frame_source_manager.is_finite_source()

                        if not success or frame is None:
                            if camera_stats.get('last_frame_ts'):
                                age_s = max(0.0, time.time() - float(camera_stats.get('last_frame_ts', 0.0)))
                                camera_stats['last_frame_age_s'] = round(age_s, 1)
                                if age_s >= camera_offline_age_s:
                                    camera_stats['online'] = False
                                    camera_stats['status'] = 'offline'
                                elif age_s >= camera_stall_age_s:
                                    camera_stats['online'] = False
                                    camera_stats['status'] = 'stalled'
                            else:
                                camera_stats['online'] = False
                                camera_stats['status'] = 'offline'

                            if source_exhausted and (camera_id == 'camera1' or dataset_shared_mode):
                                logger.info("Input dataset exhausted on %s - switching back to live camera", camera_id)
                                switched, message = self.switch_input_source('camera')
                                if not switched:
                                    logger.error("Failed to switch back to live camera: %s", message)
                                    self.running = False
                                    break
                                time.sleep(0.2)
                                continue
                            logger.warning("Failed to read frame on %s, retrying...", camera_id)
                            time.sleep(0.05)
                            continue

                        last_frame_time = current_time

                    except Exception as e:
                        if camera_stats.get('last_frame_ts'):
                            age_s = max(0.0, time.time() - float(camera_stats.get('last_frame_ts', 0.0)))
                            camera_stats['last_frame_age_s'] = round(age_s, 1)
                            if age_s >= camera_offline_age_s:
                                camera_stats['online'] = False
                                camera_stats['status'] = 'offline'
                            elif age_s >= camera_stall_age_s:
                                camera_stats['online'] = False
                                camera_stats['status'] = 'stalled'
                        else:
                            camera_stats['online'] = False
                            camera_stats['status'] = 'offline'
                        logger.error("Camera error on %s: %s", camera_id, e)
                        time.sleep(0.1)
                        continue

                    frame_count += 1
                    fps_counter += 1
                    self.camera_frame_counts[camera_id] = self.camera_frame_counts.get(camera_id, 0) + 1
                    per_camera_fps_counters[camera_id] = per_camera_fps_counters.get(camera_id, 0) + 1

                    with self.source_lock:
                        current_source = frame_source_manager.get_last_frame_source() if frame_source_manager else 'unknown'
                    self.detection_processor.stats['current_frame_source'] = f"{camera_id}:{current_source}"
                    camera_stats['current_frame_source'] = current_source
                    camera_stats['frame_id'] = self.camera_frame_counts[camera_id]
                    camera_stats['last_frame_ts'] = now
                    camera_stats['last_frame_age_s'] = 0.0
                    camera_stats['online'] = True
                    camera_stats['status'] = 'online'

                    now_for_fps = time.time()
                    if now_for_fps - per_camera_fps_timers.get(camera_id, now_for_fps) >= 1.0:
                        elapsed_fps = max(now_for_fps - per_camera_fps_timers[camera_id], 0.001)
                        camera_stats['fps'] = round(per_camera_fps_counters.get(camera_id, 0) / elapsed_fps, 1)
                        per_camera_fps_counters[camera_id] = 0
                        per_camera_fps_timers[camera_id] = now_for_fps

                    # Update frame count in stats (for web dashboard)
                    self.detection_processor.stats['frame_id'] = frame_count

                    # Debug logging every 30 global frames
                    if frame_count % 30 == 0:
                        logger.debug("Frame count updated: %d", frame_count)

                    # Update FPS calculation
                    if time.time() - fps_start_time >= 1.0:
                        self.detection_processor.stats['fps'] = fps_counter
                        fps_counter = 0
                        fps_start_time = time.time()

                    if finite_source and self.config.get('enable_web'):
                        try:
                            web_started = time.time()
                            display_frame = cv2.resize(frame, (480, 270))
                            with self.web_lock:
                                self.web_frames[camera_id] = display_frame.copy()
                                if camera_id == 'camera1':
                                    self.web_frame = display_frame.copy()
                            web_ms += (time.time() - web_started) * 1000.0
                        except Exception as e:
                            logger.error("Web frame update error on %s: %s", camera_id, e)

                    if finite_source:
                        dataset_delay = self.config.get('dataset_frame_delay', 5.0)
                        min_interval = float(self.config.get(f'{camera_id}_min_infer_interval', 0.0) or 0.0)
                        infer_due = (time.time() - self.camera_last_inference_ts.get(camera_id, 0.0)) >= min_interval
                        if dataset_delay >= 4.0:
                            if infer_due:
                                velutina_count, crabro_count, annotated_frame, inference_ms, postprocess_ms = self._run_detection_step(
                                    frame,
                                    frame_count,
                                    finite_source,
                                    current_source,
                                    camera_id=camera_id,
                                )
                                self.camera_last_inference_ts[camera_id] = time.time()
                            else:
                                velutina_count, crabro_count, annotated_frame = 0, 0, frame

                            if velutina_count > 0 or crabro_count > 0:
                                self._handle_detection(
                                    velutina_count,
                                    crabro_count,
                                    frame_count,
                                    annotated_frame,
                                    camera_id=camera_id,
                                )

                            if self.config.get('enable_web'):
                                try:
                                    web_started = time.time()
                                    display_frame = cv2.resize(annotated_frame, (480, 270))
                                    with self.web_lock:
                                        self.web_frames[camera_id] = display_frame.copy()
                                        if camera_id == 'camera1':
                                            self.web_frame = display_frame.copy()
                                    web_ms += (time.time() - web_started) * 1000.0
                                except Exception as e:
                                    logger.error("Web frame update error on %s: %s", camera_id, e)
                        else:
                            if infer_due:
                                self._submit_dataset_prediction(camera_id, frame_count, frame)
                                self.camera_last_inference_ts[camera_id] = time.time()
                            if len(self.dataset_prediction_queue) > 4:
                                self._drain_completed_dataset_predictions(wait_for_one=True)
                    else:
                        min_interval = float(self.config.get(f'{camera_id}_min_infer_interval', 0.0) or 0.0)
                        infer_due = (time.time() - self.camera_last_inference_ts.get(camera_id, 0.0)) >= min_interval
                        if infer_due:
                            velutina_count, crabro_count, annotated_frame, inference_ms, postprocess_ms = self._run_detection_step(
                                frame,
                                frame_count,
                                finite_source,
                                current_source,
                                camera_id=camera_id,
                            )
                            self.camera_last_inference_ts[camera_id] = time.time()
                        else:
                            velutina_count, crabro_count, annotated_frame = 0, 0, frame

                        # Handle detections
                        if velutina_count > 0 or crabro_count > 0:
                            self._handle_detection(
                                velutina_count,
                                crabro_count,
                                frame_count,
                                annotated_frame,
                                camera_id=camera_id,
                            )

                        # Update web frame (optimized for Raspberry Pi) with error handling
                        if self.config.get('enable_web'):
                            try:
                                web_started = time.time()
                                display_frame = cv2.resize(annotated_frame, (480, 270))
                                with self.web_lock:
                                    self.web_frames[camera_id] = display_frame.copy()
                                    if camera_id == 'camera1':
                                        self.web_frame = display_frame.copy()
                                web_ms += (time.time() - web_started) * 1000.0
                            except Exception as e:
                                logger.error("Web frame update error on %s: %s", camera_id, e)
                
                    # Print detection info if enabled
                    if self.config.get('print_detections') and (velutina_count > 0 or crabro_count > 0):
                        confidence = self.detection_processor.stats.get('confidence_avg', 0)
                        print(
                            f"{camera_id} frame {frame_count}: {velutina_count} Velutina, {crabro_count} Crabro "
                            f"(confidence: {confidence:.1f}%)"
                        )

                    # Print periodic frame progress even when there are no detections.
                    if self.config.get('print_detections') and velutina_count == 0 and crabro_count == 0:
                        with self.source_lock:
                            source_manager = frame_source_manager or active_camera_manager
                            source = source_manager.get_last_frame_source()
                            should_print = source_manager.is_finite_source() or (frame_count % 30 == 0)
                        if should_print:
                            print(f"{camera_id} frame {frame_count}: processed (no detections) | source: {source}")

                    self._record_perf_sample(
                        camera_id=camera_id,
                        capture_ms=capture_ms,
                        inference_ms=inference_ms,
                        postprocess_ms=postprocess_ms,
                        web_ms=web_ms,
                    )

                # Force stats update every 10 seconds to keep web interface alive
                if current_time - last_stats_update > 10:
                    self.detection_processor.stats['last_update'] = current_time
                    last_stats_update = current_time
                
                # Frame rate control (optimized for Raspberry Pi)
                frame_delay = self.config.get('frame_delay', 0.3)
                with self.source_lock:
                    primary_manager = self.camera_managers.get('camera1')
                    if primary_manager and primary_manager.is_finite_source():
                        frame_delay = max(frame_delay, self.config.get('dataset_frame_delay', 5.0))
                elapsed = time.time() - loop_start
                if elapsed < frame_delay:
                    time.sleep(frame_delay - elapsed)
        
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
            self.running = False
        except Exception as e:
            logger.error("Unexpected error in detection loop: %s", e)
            self.running = False
            return False
        finally:
            self._drain_completed_dataset_predictions(wait_for_all=True)
            self._shutdown_dataset_executor()
            # Simple cleanup like web_preview.py
            self._cleanup()
        
        logger.info("VespAI detection system stopped")
        return True

    def _run_detection_step(self, frame, frame_count: int, finite_source: bool, source_label: str = "", camera_id: str = 'camera1'):
        """Run one detection step and return counts, annotated frame, and timing details."""
        try:
            predict_started = time.time()
            results = self.model_manager.predict(frame)
            inference_ms = (time.time() - predict_started) * 1000.0
            self.detection_processor.record_inference_timing(frame_count, source_label, inference_ms, camera_id=camera_id)
            if isinstance(results, dict):
                self.detection_processor.stats['model_debug_summary'] = results.get('debug_summary', '')
            else:
                self.detection_processor.stats['model_debug_summary'] = ''
            postprocess_started = time.time()
            velutina_count, crabro_count, annotated_frame = self.detection_processor.process_detections(
                results,
                frame,
                frame_count,
                self.config.get('confidence_threshold'),
                log_frame_prediction=finite_source,
                camera_id=camera_id,
            )
            postprocess_ms = (time.time() - postprocess_started) * 1000.0
            return velutina_count, crabro_count, annotated_frame, inference_ms, postprocess_ms
        except Exception as e:
            logger.error(f"Detection error: {e}")
            self.detection_processor.stats['model_debug_summary'] = ''
            return 0, 0, frame.copy(), 0.0, 0.0

    def _ensure_dataset_executor(self):
        if self.dataset_executor is None:
            self.dataset_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='vespai-dataset')
        return self.dataset_executor

    def _submit_dataset_prediction(self, camera_id: str, frame_count: int, frame):
        executor = self._ensure_dataset_executor()
        with self.source_lock:
            manager = self.camera_managers.get(camera_id)
            source_label = manager.get_last_frame_source() if manager else f"{camera_id}-frame-{frame_count}"
        future = executor.submit(self._predict_with_timing, frame.copy())
        self.dataset_prediction_queue.append((camera_id, frame_count, frame.copy(), source_label, future))

    def _predict_with_timing(self, frame):
        predict_started = time.time()
        results = self.model_manager.predict(frame)
        inference_ms = (time.time() - predict_started) * 1000.0
        return results, inference_ms

    def _drain_completed_dataset_predictions(self, wait_for_one: bool = False, wait_for_all: bool = False):
        while self.dataset_prediction_queue:
            camera_id, frame_count, frame, source_label, future = self.dataset_prediction_queue[0]
            if not wait_for_all and not future.done():
                if wait_for_one:
                    try:
                        future.result()
                    except Exception:
                        pass
                else:
                    break

            self.dataset_prediction_queue.popleft()
            try:
                results, inference_ms = future.result()
            except Exception as error:
                logger.error("Detection error: %s", error)
                self.detection_processor.stats['model_debug_summary'] = ''
                continue

            self.detection_processor.record_inference_timing(frame_count, source_label, inference_ms, camera_id=camera_id)

            postprocess_started = time.time()
            velutina_count, crabro_count, annotated_frame = self.detection_processor.process_detections(
                results,
                frame,
                frame_count,
                self.config.get('confidence_threshold'),
                log_frame_prediction=True,
                camera_id=camera_id,
            )
            postprocess_ms = (time.time() - postprocess_started) * 1000.0
            if isinstance(results, dict):
                self.detection_processor.stats['model_debug_summary'] = results.get('debug_summary', '')
            else:
                self.detection_processor.stats['model_debug_summary'] = ''

            self._record_perf_sample(
                camera_id=camera_id,
                capture_ms=0.0,
                inference_ms=inference_ms,
                postprocess_ms=postprocess_ms,
                web_ms=0.0,
            )

            if velutina_count > 0 or crabro_count > 0:
                self._handle_detection(velutina_count, crabro_count, frame_count, annotated_frame, camera_id=camera_id)

            if not wait_for_all and not wait_for_one:
                continue

    def _shutdown_dataset_executor(self):
        if self.dataset_executor is not None:
            self.dataset_executor.shutdown(wait=False, cancel_futures=False)
            self.dataset_executor = None
        self.dataset_prediction_queue.clear()
    
    def _handle_detection(self, velutina_count: int, crabro_count: int, frame_id: int, frame, camera_id: str = 'camera1'):
        """
        Handle a detection event with alerts and logging.
        
        Args:
            velutina_count: Number of Asian hornets detected
            crabro_count: Number of European hornets detected  
            frame_id: Current frame ID
            frame: Detection frame with annotations
        """
        # Save detection image if enabled
        if self.config.get('save_detections'):
            self._save_detection_image(frame, frame_id, velutina_count, crabro_count, camera_id=camera_id)
        
        # Send SMS alert if configured
        if self.sms_manager:
            self._send_sms_alert(velutina_count, crabro_count, frame_id, camera_id=camera_id)

        # Send push alert if configured
        if self.push_manager:
            self._send_push_alert(velutina_count, crabro_count, frame_id, frame, camera_id=camera_id)
    
    def _save_detection_image(self, frame, frame_id: int, velutina: int, crabro: int, camera_id: str = 'camera1'):
        """Save detection image to disk."""
        import os
        from datetime import datetime
        
        save_dir = self.config.get('save_directory', 'data/detections')
        os.makedirs(save_dir, exist_ok=True)
        self._prune_saved_detection_images(save_dir)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        species = 'velutina' if velutina > 0 else 'crabro'
        filename = f"{timestamp}_{camera_id}_frame{frame_id}_{species}_{velutina}v_{crabro}c.jpg"
        filepath = os.path.join(save_dir, filename)
        
        cv2.imwrite(filepath, frame)
        self._prune_saved_detection_images(save_dir)
        logger.info("Saved detection image: %s", filepath)

    def _prune_saved_detection_images(self, save_dir: str):
        """Prune saved detection images by retention age and max file count."""
        retention_days = int(self.config.get('detection_retention_days', 21))
        max_file_count = int(self.config.get('detection_max_file_count', 250))
        cutoff = time.time() - (retention_days * 24 * 60 * 60) if retention_days > 0 else None
        deleted_by_age = 0
        deleted_by_count = 0
        remaining_entries = []

        try:
            with os.scandir(save_dir) as entries:
                for entry in entries:
                    if not entry.is_file():
                        continue
                    try:
                        mtime = entry.stat().st_mtime
                        if cutoff is not None and mtime < cutoff:
                            os.remove(entry.path)
                            deleted_by_age += 1
                        else:
                            remaining_entries.append((entry.path, mtime))
                    except FileNotFoundError:
                        continue
                    except Exception as error:
                        logger.warning("Failed to prune old detection file %s: %s", entry.path, error)
        except FileNotFoundError:
            return
        except Exception as error:
            logger.warning("Failed to scan detection save directory %s: %s", save_dir, error)
            return

        if max_file_count > 0 and len(remaining_entries) > max_file_count:
            remaining_entries.sort(key=lambda item: item[1])
            excess = len(remaining_entries) - max_file_count
            for path, _ in remaining_entries[:excess]:
                try:
                    os.remove(path)
                    deleted_by_count += 1
                except FileNotFoundError:
                    continue
                except Exception as error:
                    logger.warning("Failed to prune excess detection file %s: %s", path, error)

        if deleted_by_age:
            logger.info(
                "Pruned %d detection image(s) older than %d day(s) from %s",
                deleted_by_age,
                retention_days,
                save_dir,
            )
        if deleted_by_count:
            logger.info(
                "Pruned %d detection image(s) to enforce max file count %d in %s",
                deleted_by_count,
                max_file_count,
                save_dir,
            )
    
    def _send_sms_alert(self, velutina_count: int, crabro_count: int, frame_id: int, camera_id: str = 'camera1'):
        """Send SMS alert for detection."""
        if not self.sms_manager:
            return
        
        # Create frame URL for SMS
        web_config = self.config.get_web_config()
        current_time = time.strftime('%H%M%S')
        detection_key = f"{camera_id}_{frame_id}_{current_time}"
        frame_url = f"{web_config['public_url']}/frame/{detection_key}"
        
        # Determine hornet type and create alert
        if velutina_count > 0:
            hornet_type = 'velutina'
            count = velutina_count
        else:
            hornet_type = 'crabro'
            count = crabro_count
        
        confidence = self.detection_processor.stats.get('confidence_avg', 0)
        message = self.sms_manager.create_hornet_alert(hornet_type, count, confidence, frame_url)
        
        # Send alert
        success, status = self.sms_manager.send_alert(message)
        if success:
            logger.info("SMS alert sent: %s", status)
        else:
            logger.warning("SMS alert failed: %s", status)

    def _send_push_alert(self, velutina_count: int, crabro_count: int, frame_id: int, frame, camera_id: str = 'camera1'):
        """Send push alert for detection."""
        if not self.push_manager:
            return

        web_config = self.config.get_web_config()
        current_time = time.strftime('%H%M%S')
        detection_key = f"{camera_id}_{frame_id}_{current_time}"
        frame_url = f"{web_config['public_url']}/frame/{detection_key}"

        if velutina_count > 0:
            hornet_type = 'velutina'
            count = velutina_count
        else:
            hornet_type = 'crabro'
            count = crabro_count

        confidence = self.detection_processor.stats.get('confidence_avg', 0)
        fallback_alias = 'Camera 2' if camera_id == 'camera2' else 'Camera 1'
        source_name = str(self.camera_aliases.get(camera_id, fallback_alias) or fallback_alias).strip()[:16]
        message = self.push_manager.create_hornet_alert(
            hornet_type,
            count,
            confidence,
            frame_url,
            source_name=source_name,
        )

        attachment = None
        if self.config.get('push_thumbnail') and frame is not None:
            try:
                height, width = frame.shape[:2]
                if width > 0 and height > 0:
                    thumb_width = min(320, width)
                    thumb_height = max(1, int((height / width) * thumb_width))
                    thumb = cv2.resize(frame, (thumb_width, thumb_height))
                    encoded_ok, encoded_thumb = cv2.imencode('.jpg', thumb, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
                    if encoded_ok:
                        attachment = encoded_thumb.tobytes()
            except Exception as e:
                logger.warning("Failed to build push thumbnail for frame %s on %s: %s", frame_id, camera_id, e)

        success, status = self.push_manager.send_alert(message, attachment=attachment)
        if success:
            self.detection_processor.stats['push_sent'] = int(self.detection_processor.stats.get('push_sent', 0)) + 1
            logger.info("Push alert sent: %s", status)
        else:
            logger.warning("Push alert failed: %s", status)
    
    def _validate_initialization(self) -> bool:
        """Validate that all required components are initialized."""
        if not self.camera_managers:
            logger.error("Camera manager not initialized")
            return False
        
        if not self.model_manager or not self.model_manager.model:
            logger.error("Model manager not initialized") 
            return False
        
        if not self.detection_processor:
            logger.error("Detection processor not initialized")
            return False
        
        return True
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info("Received signal %d, shutting down...", signum)
        self.running = False
        
        # Force immediate shutdown on second Ctrl+C
        if hasattr(self, '_shutdown_requested'):
            logger.info("Force shutdown requested, terminating immediately...")
            import os
            os._exit(0)
        self._shutdown_requested = True
    
    def _attempt_recovery(self):
        """Attempt to recover from system hang."""
        logger.info("Attempting system recovery...")
        
        try:
            # Force garbage collection
            import gc
            gc.collect()
            
            # Reset camera connection
            if self.camera_managers:
                logger.info("Resetting camera connection(s)...")
                with self.source_lock:
                    for manager in self.camera_managers.values():
                        manager.release()
                    time.sleep(2)
                    for camera_id, manager in self.camera_managers.items():
                        if not self.camera_enabled.get(camera_id, True):
                            continue
                        if self.current_input_mode == 'dataset':
                            manager.initialize_camera(self.current_dataset_path)
                        else:
                            manager.initialize_camera(None)
            
            # Clear any stuck web frames
            with self.web_lock:
                self.web_frame = None
                self.web_frames = {}
                
            logger.info("Recovery attempt completed")
            
        except Exception as e:
            logger.error(f"Recovery failed: {e}")
    
    def _cleanup(self):
        """Clean up resources on shutdown - simplified like web_preview.py."""
        logger.info("Cleaning up resources...")
        
        # Release camera (web server will auto-die as daemon thread)
        if self.camera_managers:
            with self.source_lock:
                for manager in self.camera_managers.values():
                    manager.release()
        
        # Final statistics
        if self.detection_processor:
            stats = self.detection_processor.stats
            logger.info("Final statistics:")
            logger.info("  Total frames processed: %d", stats.get('frame_id', 0))
            logger.info("  Total detections: %d", stats.get('total_detections', 0))
            logger.info("  Asian hornets: %d", stats.get('total_velutina', 0))
            logger.info("  European hornets: %d", stats.get('total_crabro', 0))


def main():
    """Main entry point for the VespAI application."""
    app = VespAIApplication()
    
    try:
        app.initialize()
        success = app.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error("Fatal error: %s", e)
        sys.exit(1)


if __name__ == '__main__':
    main()