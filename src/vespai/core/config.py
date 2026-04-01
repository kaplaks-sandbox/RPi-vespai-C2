#!/usr/bin/env python3
"""
VespAI Configuration Module

Handles all configuration management including environment variables,
command line arguments, and default settings.

Author: Jakob Zeise (Zeise Digital)
Modified: Andre Jordaan
Version: 2.0
"""

import os
import argparse
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class VespAIConfig:
    """
    Central configuration management for VespAI.
    
    Handles environment variables, command line arguments, and default settings
    with proper precedence (CLI args override env vars override defaults).
    """
    
    def __init__(self):
        """Initialize configuration with defaults."""
        # Load environment variables from this repository's .env file and
        # force them to override ambient shell variables from other projects.
        project_root = Path(__file__).resolve().parents[3]
        dotenv_path = project_root / '.env'
        load_dotenv(dotenv_path=dotenv_path, override=True)
        
        # Default configuration
        self.defaults = {
            # Camera settings
            'resolution': '1920x1080',
            'camera_source': 'auto',
            'camera_autofocus': True,
            'camerapi_focus_mode': 'manual',
            'camerapi_focus_distance_m': 0.13,
            'camerapi_awb_mode': 'auto',
            'camerapi_awb_red_gain': 0.0,
            'camerapi_awb_blue_gain': 0.0,
            'camerapi_color_order': 'bgr',
            'camera1_source': 'auto',
            'camera1_device': '',
            'camera1_autofocus': True,
            'camera1_alias': 'Camera 1',
            'camera2_enabled': False,
            'camera2_source': 'usb',
            'camera2_device': '',
            'camera2_autofocus': True,
            'camera2_alias': 'Camera 2',
            'video_file': None,
            'dataset_path': '',

            # Tracking settings
            'tracking_mode': 'off',
            
            # Detection settings  
            'confidence_threshold': 0.8,
            'model_path': 'models/L4-YOLOV26-asianhornet_2026-03-13_08-57-52_ncnn_model',
            'model_format': 'auto',
            'class_map': '',
            'save_detections': True,
            'save_directory': 'data/detections',
            'detection_retention_days': 21,
            'detection_max_file_count': 250,
            'print_detections': False,
            
            # Motion detection
            'enable_motion_detection': True,
            'min_motion_area': 100,
            'dilation_iterations': 1,
            
            # Performance settings
            'frame_delay': 0.1,
            'dataset_frame_delay': 5.0,
            'camera1_min_infer_interval': 0.0,
            'camera2_min_infer_interval': 0.2,
            
            # Web interface
            'enable_web': True,
            'web_host': '0.0.0.0',
            'web_port': 5000,
            'web_preview_size': '960x540',
            'live_stream_quality': 72,
            'current_frame_quality': 82,
            'web_color_scale_r': 1.0,
            'web_color_scale_g': 1.0,
            'web_color_scale_b': 1.0,
            
            # SMS settings (disabled by default, use --sms to enable)
            'enable_sms': False,
            'lox24_api_key': '',
            'phone_number': '',
            'lox24_sender': 'VespAI',
            'sms_delay_minutes': 5,
            'domain_name': 'localhost',
            'use_https': False,
            
            # Pushover settings (disabled by default, use --push to enable)
            'enable_push': False,
            'pushover_token': '',
            'pushover_user': '',
            'pushover_sender': os.getenv('VESPAI_NAME', 'VespAI'),
            'push_delay_minutes': 5,
            'push_thumbnail': False,
        }
        
        # Current configuration (will be populated from env + args)
        self.config = {}
        self._load_from_environment()

    def _normalize_camera_source(self, value: Any) -> str:
        """Normalize camera source names while keeping user-facing aliases working."""
        normalized = str(value or 'auto').strip().lower()
        if normalized == 'picamera3':
            return 'picamera2'
        return normalized

    def _sanitize_camera_alias(self, value: Any, fallback: str) -> str:
        """Normalize camera alias with a strict maximum length for UI/log readability."""
        alias = str(value or '').strip()
        if not alias:
            alias = fallback
        return alias[:16]

    def _normalize_tracking_mode(self, value: Any) -> str:
        """Normalize tracker mode names while keeping aliases working."""
        normalized = str(value or 'off').strip().lower()
        aliases = {
            'none': 'off',
            'false': 'off',
            '0': 'off',
            'simple': 'centroid',
        }
        return aliases.get(normalized, normalized)

    def _normalize_model_format(self, value: Any) -> str:
        """Normalize model format preference names."""
        normalized = str(value or 'auto').strip().lower()
        aliases = {
            'none': 'auto',
            'default': 'auto',
            'automatic': 'auto',
        }
        return aliases.get(normalized, normalized)

    def _is_ncnn_model_dir(self, model_path: Any) -> bool:
        """Return True when model_path points to a valid NCNN model directory."""
        if not model_path:
            return False
        path = Path(str(model_path))
        return path.is_dir() and (path / 'model.ncnn.param').exists() and (path / 'model.ncnn.bin').exists()

    def _apply_model_format_preference(self):
        """Adjust model_path to honor requested model format when a sibling artifact exists."""
        model_path = str(self.config.get('model_path') or '').strip()
        model_format = self._normalize_model_format(self.config.get('model_format'))
        self.config['model_format'] = model_format

        if not model_path or model_format == 'auto':
            return

        path = Path(model_path)

        if model_format == 'ncnn':
            candidates = []
            if path.suffix.lower() == '.onnx':
                candidates.append(path.with_suffix(''))
                candidates.append(path.with_name(f"{path.stem}_ncnn_model"))
            elif path.suffix == '':
                candidates.append(path)
                candidates.append(path.with_name(f"{path.name}_ncnn_model"))
            else:
                candidates.append(path)

            for candidate in candidates:
                if self._is_ncnn_model_dir(candidate):
                    self.config['model_path'] = str(candidate)
                    return

            logger.warning(
                "Model format ncnn requested but no NCNN directory found for %s; using configured path",
                model_path,
            )
            return

        if model_format == 'onnx':
            candidates = []
            if self._is_ncnn_model_dir(path):
                candidates.append(path.with_suffix('.onnx'))
                if path.name.endswith('_ncnn_model'):
                    base_name = path.name[:-len('_ncnn_model')]
                    candidates.append(path.with_name(f"{base_name}.onnx"))
            elif path.suffix == '':
                candidates.append(path.with_suffix('.onnx'))
            else:
                candidates.append(path)

            for candidate in candidates:
                if candidate.exists() and candidate.is_file():
                    self.config['model_path'] = str(candidate)
                    return

            logger.warning(
                "Model format onnx requested but no ONNX file found for %s; using configured path",
                model_path,
            )
    
    def _load_from_environment(self):
        """Load configuration from environment variables."""
        def sanitize_env_value(raw_value: str) -> str:
            """Normalize env values by trimming spaces and inline comments for unquoted values."""
            if raw_value is None:
                return ''

            value = str(raw_value).strip()
            if not value:
                return ''

            # Keep quoted values intact apart from removing outer quotes.
            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                return value[1:-1].strip()

            # Support .env-style inline comments after at least one whitespace character.
            hash_index = value.find('#')
            if hash_index > 0 and value[hash_index - 1].isspace():
                value = value[:hash_index].strip()

            return value

        # Map environment variable names to config keys
        env_mapping = {
            'RESOLUTION': 'resolution',
            'VESPAI_CAMERA_SOURCE': 'camera_source',
            'VESPAI_CAMERAPI_AUTOFOCUS': 'camera_autofocus',
            'VESPAI_CAMERAPI_FOCUS_MODE': 'camerapi_focus_mode',
            'VESPAI_CAMERAPI_FOCUS_DISTANCE_M': 'camerapi_focus_distance_m',
            'VESPAI_CAMERAPI_AWB_MODE': 'camerapi_awb_mode',
            'VESPAI_CAMERAPI_AWB_RED_GAIN': 'camerapi_awb_red_gain',
            'VESPAI_CAMERAPI_AWB_BLUE_GAIN': 'camerapi_awb_blue_gain',
            'VESPAI_CAMERAPI_COLOR_ORDER': 'camerapi_color_order',
            'VESPAI_CAMERA1_SOURCE': 'camera1_source',
            'VESPAI_CAMERA1_DEVICE': 'camera1_device',
            'VESPAI_CAMERA1_AUTOFOCUS': 'camera1_autofocus',
            'VESPAI_CAMERA1_ALIAS': 'camera1_alias',
            'VESPAI_CAMERA2_ENABLED': 'camera2_enabled',
            'VESPAI_CAMERA2_SOURCE': 'camera2_source',
            'VESPAI_CAMERA2_DEVICE': 'camera2_device',
            'VESPAI_CAMERA2_AUTOFOCUS': 'camera2_autofocus',
            'VESPAI_CAMERA2_ALIAS': 'camera2_alias',
            'CONFIDENCE_THRESHOLD': 'confidence_threshold', 
            'MODEL_PATH': 'model_path',
            'VESPAI_MODEL_FORMAT': 'model_format',
            'MODEL_FORMAT': 'model_format',
            'VESPAI_CLASS_MAP': 'class_map',
            'VESPAI_DATASET_PATH': 'dataset_path',
            'VESPAI_TRACKING_MODE': 'tracking_mode',
            'SAVE_DETECTIONS': 'save_detections',
            'SAVE_DIRECTORY': 'save_directory',
            'DETECTION_RETENTION_DAYS': 'detection_retention_days',
            'DETECTION_MAX_FILE_COUNT': 'detection_max_file_count',
            'ENABLE_MOTION_DETECTION': 'enable_motion_detection',
            'MIN_MOTION_AREA': 'min_motion_area',
            'FRAME_DELAY': 'frame_delay',
            'DATASET_FRAME_DELAY': 'dataset_frame_delay',
            'VESPAI_DATASET_FRAME_DELAY': 'dataset_frame_delay',
            'VESPAI_CAMERA1_MIN_INFER_INTERVAL': 'camera1_min_infer_interval',
            'VESPAI_CAMERA2_MIN_INFER_INTERVAL': 'camera2_min_infer_interval',
            'ENABLE_WEB': 'enable_web',
            'WEB_HOST': 'web_host',
            'WEB_PORT': 'web_port',
            'WEB_PREVIEW_SIZE': 'web_preview_size',
            'LIVE_STREAM_QUALITY': 'live_stream_quality',
            'CURRENT_FRAME_QUALITY': 'current_frame_quality',
            'WEB_COLOR_SCALE_R': 'web_color_scale_r',
            'WEB_COLOR_SCALE_G': 'web_color_scale_g',
            'WEB_COLOR_SCALE_B': 'web_color_scale_b',
            'ENABLE_SMS': 'enable_sms',
            'LOX24_API_KEY': 'lox24_api_key',
            'PHONE_NUMBER': 'phone_number',
            'LOX24_SENDER': 'lox24_sender',
            'SMS_DELAY_MINUTES': 'sms_delay_minutes',
            'ENABLE_PUSH': 'enable_push',
            'PUSHOVER_TOKEN': 'pushover_token',
            'PUSHOVER_USER': 'pushover_user',
            'PUSHOVER_SENDER': 'pushover_sender',
            'PUSH_DELAY_MINUTES': 'push_delay_minutes',
            'PUSH_THUMBNAIL': 'push_thumbnail',
            'DOMAIN_NAME': 'domain_name',
            'USE_HTTPS': 'use_https',
        }
        
        # Start with defaults
        self.config = self.defaults.copy()
        
        # Override with environment variables
        for env_key, config_key in env_mapping.items():
            env_value = os.getenv(env_key)
            if env_value is not None:
                normalized_env_value = sanitize_env_value(env_value)
                # Convert types based on default value type
                default_value = self.defaults[config_key]
                try:
                    if isinstance(default_value, bool):
                        self.config[config_key] = normalized_env_value.lower() in ('true', '1', 'yes', 'on')
                    elif isinstance(default_value, int):
                        self.config[config_key] = int(normalized_env_value)
                    elif isinstance(default_value, float):
                        self.config[config_key] = float(normalized_env_value)
                    else:
                        self.config[config_key] = normalized_env_value
                        
                    logger.debug("Loaded %s from environment: %s", config_key, normalized_env_value)
                except (ValueError, TypeError) as e:
                    logger.warning("Invalid environment value for %s: %s (%s)", env_key, normalized_env_value, e)

            self.config['camera_source'] = self._normalize_camera_source(self.config.get('camera_source'))
            self.config['camera1_source'] = self._normalize_camera_source(self.config.get('camera1_source'))
            self.config['camera2_source'] = self._normalize_camera_source(self.config.get('camera2_source'))
            self.config['tracking_mode'] = self._normalize_tracking_mode(self.config.get('tracking_mode'))

        # Backward compatibility: mirror legacy source into camera1 when camera1 source is unset.
        if not self.config.get('camera1_source'):
            self.config['camera1_source'] = self.config.get('camera_source', 'auto')

        # Backward compatibility: global autofocus fallback for camera profiles.
        self.config['camera1_autofocus'] = bool(self.config.get('camera1_autofocus', self.config.get('camera_autofocus', True)))
        self.config['camera2_autofocus'] = bool(self.config.get('camera2_autofocus', self.config.get('camera_autofocus', True)))
        self.config['camera1_alias'] = self._sanitize_camera_alias(
            self.config.get('camera1_alias'),
            'Camera 1',
        )
        self.config['camera2_alias'] = self._sanitize_camera_alias(
            self.config.get('camera2_alias'),
            'Camera 2',
        )

        # Backward compatibility: mirror legacy camera device env into camera1 device.
        if not self.config.get('camera1_device'):
            legacy_device = os.getenv('VESPAI_CAMERA_DEVICE', '').strip()
            if legacy_device:
                self.config['camera1_device'] = legacy_device
    
    def parse_args(self, args=None) -> argparse.Namespace:
        """
        Parse command line arguments and update configuration.

        Args:
            args: List of arguments to parse (None for sys.argv)

        Returns:
            argparse.Namespace: Parsed arguments
        """
        parser = argparse.ArgumentParser(
            description='VespAI Hornet Detection System',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )

        # Camera settings
        parser.add_argument('-r', '--resolution',
                            default=self.config['resolution'],
                            help='Camera resolution (e.g., 1920x1080, 1080p, 720p)')
        parser.add_argument('--camera-source',
                            choices=('auto', 'usb', 'picamera2', 'picamera3'),
                            default=self.config['camera_source'],
                            help='Live camera backend selection (Camera Module 3 uses the Picamera2 backend)')
        parser.add_argument('--camera-autofocus',
                            action='store_true',
                            default=self.config['camera_autofocus'],
                            help='Enable Picamera2 continuous autofocus by default')
        parser.add_argument('--no-camera-autofocus',
                            action='store_true',
                            default=False,
                            help='Disable Picamera2 autofocus by default')
        parser.add_argument('--camera1-source',
                            choices=('auto', 'usb', 'picamera2', 'picamera3'),
                            default=self.config['camera1_source'],
                            help='Camera 1 backend selection')
        parser.add_argument('--camera1-device',
                            default=self.config['camera1_device'],
                            help='Camera 1 preferred device path (e.g., /dev/video0)')
        parser.add_argument('--camera1-autofocus',
                            action='store_true',
                            default=self.config['camera1_autofocus'],
                            help='Enable Camera 1 Picamera2 autofocus')
        parser.add_argument('--camera1-alias',
                    default=self.config['camera1_alias'],
                    help='Display alias for Camera 1 (max 16 chars)')
        parser.add_argument('--no-camera1-autofocus',
                            action='store_true',
                            default=False,
                            help='Disable Camera 1 autofocus')
        parser.add_argument('--camera2-enabled',
                            action='store_true',
                            default=self.config['camera2_enabled'],
                            help='Enable Camera 2 processing pipeline')
        parser.add_argument('--camera2-source',
                            choices=('auto', 'usb', 'picamera2', 'picamera3'),
                            default=self.config['camera2_source'],
                            help='Camera 2 backend selection')
        parser.add_argument('--camera2-device',
                            default=self.config['camera2_device'],
                            help='Camera 2 preferred device path (e.g., /dev/video1)')
        parser.add_argument('--camera2-autofocus',
                            action='store_true',
                            default=self.config['camera2_autofocus'],
                            help='Enable Camera 2 Picamera2 autofocus')
        parser.add_argument('--camera2-alias',
                    default=self.config['camera2_alias'],
                    help='Display alias for Camera 2 (max 16 chars)')
        parser.add_argument('--no-camera2-autofocus',
                            action='store_true',
                            default=False,
                            help='Disable Camera 2 autofocus')
        parser.add_argument('-v', '--video',
                            default=self.config['video_file'],
                            help='Video file, image directory, or TFRecord file/directory to process instead of live camera')
        parser.add_argument('--tracking-mode',
                            choices=('off', 'centroid', 'iou', 'simple'),
                            default=self.config['tracking_mode'],
                            help='Object tracking mode for stable IDs on detections')

        # Detection settings
        parser.add_argument('-c', '--conf', '--confidence',
                            type=float,
                            default=self.config['confidence_threshold'],
                            help='Detection confidence threshold')
        parser.add_argument('--model-path',
                            default=self.config['model_path'],
                            help='Path to model weights or export artifact')
        parser.add_argument('--model-format',
                    choices=('auto', 'onnx', 'ncnn'),
                    default=self.config['model_format'],
                    help='Preferred model artifact format when sibling files/dirs exist')
        parser.add_argument('--class-map',
                            default=self.config['class_map'],
                            help='Class-to-species mapping, e.g. "0:crabro,1:velutina" or JSON string')
        parser.add_argument('-s', '--save',
                            action='store_true',
                            default=self.config['save_detections'],
                            help='Save detection images')
        parser.add_argument('-sd', '--save-dir',
                            default=self.config['save_directory'],
                            help='Directory to save detection images')
        parser.add_argument('-p', '--print',
                            action='store_true',
                            default=self.config['print_detections'],
                            help='Print detection details to console')

        # Motion detection
        parser.add_argument('-m', '--motion',
                            action='store_true',
                            default=self.config['enable_motion_detection'],
                            help='Enable motion detection optimization')
        parser.add_argument('-a', '--min-motion-area',
                            type=int,
                            default=self.config['min_motion_area'],
                            help='Minimum motion area threshold')
        parser.add_argument('-d', '--dilation',
                            type=int,
                            default=self.config['dilation_iterations'],
                            help='Dilation iterations for motion detection')

        # Performance settings
        parser.add_argument('-b', '--brake',
                            type=float,
                            default=self.config['frame_delay'],
                            help='Frame processing delay in seconds')
        parser.add_argument('--dataset-delay',
                            type=float,
                            default=self.config['dataset_frame_delay'],
                            help='Minimum frame delay for finite dataset inputs (seconds)')
        parser.add_argument('--camera1-min-infer-interval',
                            type=float,
                            default=self.config['camera1_min_infer_interval'],
                            help='Minimum seconds between Camera 1 inference runs (0 disables throttling)')
        parser.add_argument('--camera2-min-infer-interval',
                            type=float,
                            default=self.config['camera2_min_infer_interval'],
                            help='Minimum seconds between Camera 2 inference runs (reduces dual-camera load)')

        # Web interface
        parser.add_argument('--web',
                            action='store_true',
                            default=self.config['enable_web'],
                            help='Enable web dashboard')
        parser.add_argument('--web-host',
                            default=self.config['web_host'],
                            help='Web server host address')
        parser.add_argument('--web-port',
                            type=int,
                            default=self.config['web_port'],
                            help='Web server port')

        # SMS alerts
        parser.add_argument('--sms',
                            action='store_true',
                            default=False,
                            help='Enable SMS alerts (requires LOX24_API_KEY and PHONE_NUMBER)')
        parser.add_argument('--no-sms',
                            action='store_true',
                            default=False,
                            help='Disable SMS alerts')

        # Pushover alerts
        parser.add_argument('--push',
                    action='store_true',
                    default=False,
                    help='Enable Pushover alerts (requires PUSHOVER_TOKEN and PUSHOVER_USER)')
        parser.add_argument('--no-push',
                    action='store_true',
                    default=False,
                    help='Disable Pushover alerts')

        parsed_args = parser.parse_args(args)

        # Update configuration with parsed arguments
        self._update_from_args(parsed_args)
        self.config['camera_source'] = self._normalize_camera_source(self.config.get('camera_source'))
        self.config['camera1_source'] = self._normalize_camera_source(self.config.get('camera1_source'))
        self.config['camera2_source'] = self._normalize_camera_source(self.config.get('camera2_source'))
        self.config['tracking_mode'] = self._normalize_tracking_mode(self.config.get('tracking_mode'))
        self.config['model_format'] = self._normalize_model_format(self.config.get('model_format'))
        self._apply_model_format_preference()

        if not self.config.get('camera1_source'):
            self.config['camera1_source'] = self.config.get('camera_source', 'auto')

        if hasattr(parsed_args, 'no_camera_autofocus') and parsed_args.no_camera_autofocus:
            self.config['camera_autofocus'] = False
        if hasattr(parsed_args, 'no_camera1_autofocus') and parsed_args.no_camera1_autofocus:
            self.config['camera1_autofocus'] = False
        if hasattr(parsed_args, 'no_camera2_autofocus') and parsed_args.no_camera2_autofocus:
            self.config['camera2_autofocus'] = False

        self.config['camera1_autofocus'] = bool(self.config.get('camera1_autofocus', self.config.get('camera_autofocus', True)))
        self.config['camera2_autofocus'] = bool(self.config.get('camera2_autofocus', self.config.get('camera_autofocus', True)))
        self.config['camera1_alias'] = self._sanitize_camera_alias(
            self.config.get('camera1_alias'),
            'Camera 1',
        )
        self.config['camera2_alias'] = self._sanitize_camera_alias(
            self.config.get('camera2_alias'),
            'Camera 2',
        )

        return parsed_args
    
    def _update_from_args(self, args: argparse.Namespace):
        """Update configuration from parsed command line arguments."""
        # Map argument attributes to config keys
        arg_mapping = {
            'resolution': 'resolution',
            'camera_source': 'camera_source',
            'camera1_source': 'camera1_source',
            'camera1_device': 'camera1_device',
            'camera1_autofocus': 'camera1_autofocus',
            'camera1_alias': 'camera1_alias',
            'camera2_enabled': 'camera2_enabled',
            'camera2_source': 'camera2_source',
            'camera2_device': 'camera2_device',
            'camera2_autofocus': 'camera2_autofocus',
            'camera2_alias': 'camera2_alias',
            'video': 'video_file',
            'tracking_mode': 'tracking_mode',
            'conf': 'confidence_threshold',
            'model_path': 'model_path',
            'model_format': 'model_format',
            'class_map': 'class_map',
            'save': 'save_detections',
            'save_dir': 'save_directory',
            'print': 'print_detections',
            'motion': 'enable_motion_detection',
            'min_motion_area': 'min_motion_area',
            'dilation': 'dilation_iterations',
            'brake': 'frame_delay',
            'dataset_delay': 'dataset_frame_delay',
            'camera1_min_infer_interval': 'camera1_min_infer_interval',
            'camera2_min_infer_interval': 'camera2_min_infer_interval',
            'web': 'enable_web',
            'web_host': 'web_host',
            'web_port': 'web_port',
        }
        
        for arg_key, config_key in arg_mapping.items():
            if hasattr(args, arg_key):
                value = getattr(args, arg_key)
                if value is not None:
                    self.config[config_key] = value
        
        # Handle SMS enable/disable flags
        if hasattr(args, 'sms') and args.sms:
            self.config['enable_sms'] = True
        elif hasattr(args, 'no_sms') and args.no_sms:
            self.config['enable_sms'] = False

        if hasattr(args, 'push') and args.push:
            self.config['enable_push'] = True
        elif hasattr(args, 'no_push') and args.no_push:
            self.config['enable_push'] = False

        if hasattr(args, 'no_camera_autofocus') and args.no_camera_autofocus:
            self.config['camera_autofocus'] = False
        if hasattr(args, 'no_camera1_autofocus') and args.no_camera1_autofocus:
            self.config['camera1_autofocus'] = False
        if hasattr(args, 'no_camera2_autofocus') and args.no_camera2_autofocus:
            self.config['camera2_autofocus'] = False
    
    def get(self, key: str, default=None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """
        Set configuration value.
        
        Args:
            key: Configuration key
            value: Value to set
        """
        self.config[key] = value
        logger.debug("Set %s to %s", key, value)
    
    def get_camera_resolution(self) -> Tuple[int, int]:
        """
        Get camera resolution as (width, height) tuple.
        
        Returns:
            Tuple of (width, height)
        """
        from .detection import parse_resolution
        return parse_resolution(self.config['resolution'])

    def get_camera_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Return camera profile settings for camera1 and optionally camera2."""
        profiles: Dict[str, Dict[str, Any]] = {
            'camera1': {
                'source': self._normalize_camera_source(self.config.get('camera1_source') or self.config.get('camera_source') or 'auto'),
                'device': str(self.config.get('camera1_device') or '').strip(),
                'autofocus': bool(self.config.get('camera1_autofocus', self.config.get('camera_autofocus', True))),
                'alias': self._sanitize_camera_alias(self.config.get('camera1_alias'), 'Camera 1'),
            }
        }

        if self.config.get('camera2_enabled'):
            profiles['camera2'] = {
                'source': self._normalize_camera_source(self.config.get('camera2_source') or 'usb'),
                'device': str(self.config.get('camera2_device') or '').strip(),
                'autofocus': bool(self.config.get('camera2_autofocus', self.config.get('camera_autofocus', True))),
                'alias': self._sanitize_camera_alias(self.config.get('camera2_alias'), 'Camera 2'),
            }

        return profiles
    
    def get_sms_config(self) -> Dict[str, Any]:
        """
        Get SMS configuration dictionary.
        
        Returns:
            Dictionary with SMS configuration
        """
        return {
            'enabled': self.config['enable_sms'],
            'api_key': self.config['lox24_api_key'],
            'phone_number': self.config['phone_number'],
            'sender_name': self.config['lox24_sender'],
            'delay_minutes': self.config['sms_delay_minutes'],
        }

    def get_push_config(self) -> Dict[str, Any]:
        """
        Get Pushover configuration dictionary.

        Returns:
            Dictionary with Pushover configuration
        """
        return {
            'enabled': self.config['enable_push'],
            'token': self.config['pushover_token'],
            'user': self.config['pushover_user'],
            'sender_name': self.config['pushover_sender'],
            'delay_minutes': self.config['push_delay_minutes'],
            'thumbnail': self.config['push_thumbnail'],
        }
    
    def get_web_config(self) -> Dict[str, Any]:
        """
        Get web server configuration dictionary.
        
        Returns:
            Dictionary with web configuration
        """
        protocol = 'https' if self.config['use_https'] else 'http'
        domain = self.config['domain_name']
        port = self.config['web_port']
        
        if port in (80, 443):
            public_url = f"{protocol}://{domain}"
        else:
            public_url = f"{protocol}://{domain}:{port}"
        
        return {
            'enabled': self.config['enable_web'],
            'host': self.config['web_host'],
            'port': self.config['web_port'],
            'public_url': public_url,
        }
    
    def validate(self) -> bool:
        """
        Validate configuration values.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate confidence threshold
        conf = self.config['confidence_threshold']
        if not (0.0 <= conf <= 1.0):
            raise ValueError(f"Confidence threshold must be between 0.0 and 1.0, got {conf}")
        
        # Validate resolution
        try:
            width, height = self.get_camera_resolution()
            if width <= 0 or height <= 0:
                raise ValueError("Resolution must have positive width and height")
        except Exception as e:
            raise ValueError(f"Invalid resolution format: {e}")

        camera_source = self._normalize_camera_source(self.config['camera_source'])
        if camera_source not in {'auto', 'usb', 'picamera2'}:
            raise ValueError(
                f"Camera source must be one of auto, usb, picamera2, got {self.config['camera_source']}"
            )
        self.config['camera_source'] = camera_source
        self.config['camera1_source'] = self._normalize_camera_source(
            self.config.get('camera1_source') or self.config['camera_source']
        )
        self.config['camera2_source'] = self._normalize_camera_source(
            self.config.get('camera2_source') or 'usb'
        )
        self.config['camera1_alias'] = self._sanitize_camera_alias(
            self.config.get('camera1_alias'),
            'Camera 1',
        )
        self.config['camera2_alias'] = self._sanitize_camera_alias(
            self.config.get('camera2_alias'),
            'Camera 2',
        )

        for key in ('camera1_source', 'camera2_source'):
            if self.config[key] not in {'auto', 'usb', 'picamera2'}:
                raise ValueError(
                    f"{key} must be one of auto, usb, picamera2, got {self.config[key]}"
                )

        for key, fallback in (('camera1_alias', 'Camera 1'), ('camera2_alias', 'Camera 2')):
            alias = self._sanitize_camera_alias(self.config.get(key), fallback)
            if not alias:
                raise ValueError(f"{key} cannot be empty")
            self.config[key] = alias

        tracking_mode = self._normalize_tracking_mode(self.config.get('tracking_mode'))
        if tracking_mode not in {'off', 'centroid', 'iou'}:
            raise ValueError(
                f"Tracking mode must be one of off, centroid, iou, got {self.config.get('tracking_mode')}"
            )
        self.config['tracking_mode'] = tracking_mode
        
        # Validate ports
        web_port = self.config['web_port']
        if not (1 <= web_port <= 65535):
            raise ValueError(f"Web port must be between 1 and 65535, got {web_port}")
        
        # Validate paths
        model_path = self.config['model_path']
        if not model_path:
            raise ValueError("Model path cannot be empty")

        model_format = self._normalize_model_format(self.config.get('model_format'))
        if model_format not in {'auto', 'onnx', 'ncnn'}:
            raise ValueError(
                f"Model format must be one of auto, onnx, ncnn, got {self.config.get('model_format')}"
            )
        self.config['model_format'] = model_format
        self._apply_model_format_preference()

        retention_days = self.config['detection_retention_days']
        if retention_days < 0:
            raise ValueError(f"Detection retention days must be >= 0, got {retention_days}")

        max_file_count = int(self.config.get('detection_max_file_count', 250))
        if max_file_count < 0:
            raise ValueError(f"Detection max file count must be >= 0, got {max_file_count}")
        self.config['detection_max_file_count'] = max_file_count

        for key in ('camera1_min_infer_interval', 'camera2_min_infer_interval'):
            value = float(self.config.get(key, 0.0))
            if value < 0.0:
                raise ValueError(f"{key} must be >= 0.0, got {value}")
            self.config[key] = value
        
        logger.info("Configuration validation passed")
        return True
    
    def print_summary(self):
        """Print a summary of the current configuration."""
        print("\n" + "="*60)
        print("VespAI Configuration Summary")
        print("="*60)
        
        print(f"Resolution: {self.config['resolution']}")
        print(f"Camera source: {self.config['camera_source']}")
        print(f"Tracking mode: {self.config['tracking_mode']}")
        print(f"Camera 1 source: {self.config['camera1_source']}")
        if self.config.get('camera1_device'):
            print(f"Camera 1 device: {self.config['camera1_device']}")
        print(f"Camera 1 autofocus: {self.config.get('camera1_autofocus', self.config.get('camera_autofocus', True))}")
        print(f"Camera 2 enabled: {self.config['camera2_enabled']}")
        if self.config.get('camera2_enabled'):
            print(f"Camera 2 source: {self.config['camera2_source']}")
            if self.config.get('camera2_device'):
                print(f"Camera 2 device: {self.config['camera2_device']}")
            print(f"Camera 2 autofocus: {self.config.get('camera2_autofocus', self.config.get('camera_autofocus', True))}")
        print(f"Confidence threshold: {self.config['confidence_threshold']}")
        print(f"Model path: {self.config['model_path']}")
        print(f"Model format preference: {self.config.get('model_format', 'auto')}")
        if self.config.get('class_map'):
            print(f"Class map: {self.config['class_map']}")
        print(f"Save detections: {self.config['save_detections']}")
        if self.config['save_detections']:
            print(f"Save directory: {self.config['save_directory']}")
            print(f"Detection retention: {self.config['detection_retention_days']} days")
            print(f"Detection max file count: {self.config['detection_max_file_count']}")
        
        print(f"Motion detection: {self.config['enable_motion_detection']}")
        print(f"Dataset frame delay: {self.config['dataset_frame_delay']}s")
        print(f"Camera 1 min infer interval: {self.config['camera1_min_infer_interval']}s")
        print(f"Camera 2 min infer interval: {self.config['camera2_min_infer_interval']}s")
        print(f"Web interface: {self.config['enable_web']}")
        if self.config['enable_web']:
            web_config = self.get_web_config()
            print(f"Web URL: {web_config['public_url']}")
        
        print(f"SMS alerts: {self.config['enable_sms']}")
        if self.config['enable_sms'] and self.config['lox24_api_key']:
            print(f"SMS delay: {self.config['sms_delay_minutes']} minutes")

        print(f"Pushover alerts: {self.config['enable_push']}")
        if self.config['enable_push'] and self.config['pushover_token']:
            print(f"Pushover delay: {self.config['push_delay_minutes']} minutes")
            print(f"Pushover thumbnail: {self.config['push_thumbnail']}")
        
        print("="*60 + "\n")


def create_config_from_args(args=None) -> VespAIConfig:
    """
    Create and configure VespAI configuration from command line arguments.
    
    Args:
        args: Command line arguments (None for sys.argv)
        
    Returns:
        VespAIConfig: Configured instance
    """
    config = VespAIConfig()
    config.parse_args(args)
    config.validate()
    return config