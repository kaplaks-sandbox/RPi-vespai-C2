#!/usr/bin/env python3
"""
VespAI Web Routes Module

This module contains all essential Flask web routes for the VespAI hornet detection system.
Routes extracted from the working web_preview.py implementation to provide a clean,
modular web interface.

Key Features:
- Live MJPEG video streaming from camera
- Real-time detection statistics API
- Detection frame viewing with SMS-friendly links
- System monitoring (CPU, RAM, temperature)
- Interactive dashboard with live updates

Routes:
- GET /: Main dashboard page
- GET /video_feed: Live MJPEG video stream
- GET /api/stats: Real-time system statistics JSON
- GET /api/detection_frame/<id>: Individual detection frame images
- GET /frame/<id>: HTML page for viewing detection frames
- GET /api/frames: List all available detection frames

Author: Jakob Zeise (Zeise Digital)
Version: 1.0
"""

import cv2
import psutil
import datetime
import logging
import base64
from flask import Response, render_template, jsonify, request
import os
import numpy as np
import time

# Set up logger
logger = logging.getLogger(__name__)


def convert_numpy_to_serializable(data):
    """
    Recursively convert numpy arrays and other non-serializable types to JSON-serializable types.
    
    Args:
        data: Any data structure that might contain numpy arrays
        
    Returns:
        JSON-serializable version of the data
    """
    if isinstance(data, np.ndarray):
        return data.tolist()
    elif isinstance(data, np.integer):
        return int(data)
    elif isinstance(data, np.floating):
        return float(data)
    elif isinstance(data, dict):
        return {key: convert_numpy_to_serializable(value) for key, value in data.items()}
    elif isinstance(data, (list, tuple)):
        return [convert_numpy_to_serializable(item) for item in data]
    else:
        return data


def register_routes(app, stats, hourly_detections, app_instance):
    """
    Register all essential web routes with the Flask app.
    
    Args:
        app (Flask): The Flask application instance
        stats (dict): Global statistics dictionary containing detection counts, system stats, etc.
        hourly_detections (dict): Dictionary tracking detections per hour (24-hour format)
        app_instance (VespAIApplication): The main application instance with web_frame and web_lock
    """
    
    # Cache for hourly data to avoid recalculating on every request
    hourly_data_cache = {
        'last_update': 0,
        'data_24h': [],
        'data_4h': []
    }

    app_config = getattr(app_instance, 'config', {}) or {}

    def clamp_quality(value, default):
        """Clamp JPEG quality to OpenCV-safe bounds."""
        try:
            return max(10, min(100, int(value)))
        except (TypeError, ValueError):
            return default

    def parse_preview_size(value):
        """Parse WxH preview size strings like 960x540."""
        default_width, default_height = 960, 540
        try:
            raw = str(value or '').lower().replace(' ', '')
            if 'x' not in raw:
                return default_width, default_height
            width_str, height_str = raw.split('x', 1)
            width = int(width_str)
            height = int(height_str)
            if width <= 0 or height <= 0:
                return default_width, default_height
            return width, height
        except (TypeError, ValueError):
            return default_width, default_height

    live_stream_quality_default = clamp_quality(app_config.get('live_stream_quality', 72), 72)
    current_frame_quality_default = clamp_quality(app_config.get('current_frame_quality', 82), 82)
    web_preview_width, web_preview_height = parse_preview_size(app_config.get('web_preview_size', '960x540'))
    try:
        confidence_threshold_default = float(app_config.get('confidence_threshold', 0.5) or 0.5)
    except (TypeError, ValueError):
        confidence_threshold_default = 0.5

    def parse_color_scale(value, default):
        try:
            scale = float(value)
            return max(0.0, min(4.0, scale))
        except (TypeError, ValueError):
            return default

    web_scale_r = parse_color_scale(app_config.get('web_color_scale_r', 1.0), 1.0)
    web_scale_g = parse_color_scale(app_config.get('web_color_scale_g', 1.0), 1.0)
    web_scale_b = parse_color_scale(app_config.get('web_color_scale_b', 1.0), 1.0)

    def apply_web_color_scaling(frame):
        if frame is None:
            return frame
        if web_scale_r == 1.0 and web_scale_g == 1.0 and web_scale_b == 1.0:
            return frame
        if len(frame.shape) != 3 or frame.shape[2] != 3:
            return frame

        scaled = frame.astype(np.float32)
        scaled[:, :, 2] *= web_scale_r
        scaled[:, :, 1] *= web_scale_g
        scaled[:, :, 0] *= web_scale_b
        return np.clip(scaled, 0, 255).astype(np.uint8)
    
    @app.route('/')
    def index():
        """
        Serve the main dashboard page with live video feed and statistics.
        Returns:
            str: HTML content for the main VespAI dashboard
        """
        # Get model name/path for display
        model_path = getattr(getattr(app_instance, 'model_manager', None), 'model_path', None)
        model_name = None
        if model_path:
            import os
            # Show last two path components for clarity
            parts = os.path.normpath(model_path).split(os.sep)
            model_name = '/'.join(parts[-2:]) if len(parts) > 1 else parts[-1]

        camera_aliases = dict(getattr(app_instance, 'camera_aliases', {}) or {})
        camera_aliases.setdefault('camera1', 'Camera 1')
        camera_aliases.setdefault('camera2', 'Camera 2')
        response = app.make_response(render_template(
            'dashboard.html',
            timestamp=int(time.time()),
            model_name=model_name,
            web_preview_width=web_preview_width,
            web_preview_height=web_preview_height,
            live_stream_quality=live_stream_quality_default,
            current_frame_quality=current_frame_quality_default,
            confidence_threshold=confidence_threshold_default,
            camera_aliases=camera_aliases,
        ))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    @app.route('/favicon.ico')
    def favicon():
        """Serve favicon to prevent 404 errors."""
        return app.send_static_file('img/favicon.svg')

    @app.route('/video_feed')
    @app.route('/video_feed/<camera_id>')
    def video_feed(camera_id='camera1'):
        """
        Provide live MJPEG video stream from the camera.
        
        This endpoint streams live video frames in Motion JPEG format using 
        multipart HTTP response. Frames are continuously encoded and sent
        to connected clients.
        
        Returns:
            Response: Flask Response object with MJPEG stream mimetype
        """
        stream_quality = clamp_quality(request.args.get('quality', live_stream_quality_default), live_stream_quality_default)

        def generate():
            """
            Generator function that yields MJPEG frames for streaming.
            
            Yields:
                bytes: MJPEG frame data with HTTP multipart boundaries
            """
            frame_timeout = 0
            while True:
                try:
                    with app_instance.web_lock:
                        frame_ref = app_instance.web_frames.get(camera_id)
                        if frame_ref is None and camera_id == 'camera1':
                            frame_ref = app_instance.web_frame

                        if frame_ref is None:
                            frame_timeout += 1
                            if frame_timeout > 100:  # 10 seconds without frame
                                logger.warning("No frames available for streaming on %s", camera_id)
                                frame_timeout = 0
                            time.sleep(0.1)
                            continue
                        frame = frame_ref.copy()
                        frame = apply_web_color_scaling(frame)
                        frame_timeout = 0

                    # Optimized quality for Raspberry Pi performance
                    (flag, encodedImage) = cv2.imencode(
                        ".jpg",
                        frame,
                        [cv2.IMWRITE_JPEG_QUALITY, stream_quality],
                    )
                    if not flag:
                        continue

                    yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
                           bytearray(encodedImage) + b'\r\n')
                           
                except Exception as e:
                    logger.error(f"Video feed error: {e}")
                    time.sleep(0.5)
                    continue

        response = Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    @app.route('/api/current_frame')
    @app.route('/api/current_frame/<camera_id>')
    def get_current_frame(camera_id='camera1'):
        """Return the latest processed frame as a single JPEG image."""
        with app_instance.web_lock:
            frame_ref = app_instance.web_frames.get(camera_id)
            if frame_ref is None and camera_id == 'camera1':
                frame_ref = app_instance.web_frame

            if frame_ref is None:
                # Return a lightweight placeholder image during startup/warmup
                # to avoid repeated 404 spam from dashboard polling.
                frame = np.zeros((270, 480, 3), dtype=np.uint8)
                cv2.putText(
                    frame,
                    f"{camera_id}: waiting for frame",
                    (18, 145),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (180, 180, 180),
                    2,
                    cv2.LINE_AA,
                )
            else:
                frame = frame_ref.copy()

        frame = apply_web_color_scaling(frame)

        frame_quality = clamp_quality(request.args.get('quality', current_frame_quality_default), current_frame_quality_default)
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, frame_quality])
        if not ret:
            return "Failed to encode frame", 500

        response = Response(buffer.tobytes(), mimetype='image/jpeg')
        if frame_ref is None:
            response.headers['X-VespAI-Frame-State'] = 'waiting'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    @app.route('/api/detection_frame/<frame_id>')
    def get_detection_frame(frame_id):
        """
        Return a specific detection frame as JPEG image.
        
        Args:
            frame_id (str): Unique identifier for the detection frame
            
        Returns:
            Response: JPEG image data or 404 error if frame not found
        """
        if frame_id in stats["detection_frames"]:
            frame = stats["detection_frames"][frame_id]
            frame = apply_web_color_scaling(frame)
            frame_quality = clamp_quality(request.args.get('quality', current_frame_quality_default), current_frame_quality_default)
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, frame_quality])
            if ret:
                response = Response(buffer.tobytes(), mimetype='image/jpeg')
                # Add caching headers for better performance
                response.headers['Cache-Control'] = 'public, max-age=3600'
                response.headers['ETag'] = f'"{frame_id}"'
                return response
        return "Frame not found", 404

    @app.route('/frame/<frame_id>')
    def serve_detection_frame(frame_id):
        """
        Serve detection frame with HTML page for SMS links and viewing.
        
        This creates a user-friendly HTML page that displays the detection frame
        with navigation options. Primarily used for SMS alert links.
        
        Args:
            frame_id (str): Unique identifier for the detection frame
            
        Returns:
            str: HTML page with detection frame or 404 error message
        """
        if frame_id not in stats["detection_frames"]:
            return f"Frame {frame_id} not found", 404

        frame = stats["detection_frames"][frame_id]
        frame = apply_web_color_scaling(frame)
        image_data_url = None
        detection_info = None
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, current_frame_quality_default])
        if ret:
            image_data_url = 'data:image/jpeg;base64,' + base64.b64encode(buffer.tobytes()).decode('ascii')

        for entry in list(stats.get("detection_log", [])):
            if entry.get("frame_id") == frame_id:
                detection_info = {
                    "name": entry.get("model_label") or entry.get("species") or "Unknown",
                    "class_id": entry.get("class_id", "-"),
                    "confidence": entry.get("confidence", "-"),
                    "species": entry.get("species", "other"),
                    "timestamp": entry.get("timestamp", "-"),
                }
                break
            
        # Add caching headers for the HTML page as well
        response = app.make_response(render_template(
            'frame.html',
            frame_id=frame_id,
            image_data_url=image_data_url,
            detection_info=detection_info,
        ))
        response.headers['Cache-Control'] = 'public, max-age=300'  # 5 minutes cache
        return response

    @app.route('/api/frames')
    def list_frames():
        """
        List all available detection frames for debugging purposes.
        
        Returns:
            dict: JSON response containing list of available frame IDs and count
        """
        return jsonify({
            "available_frames": list(stats["detection_frames"].keys()),
            "total_frames": len(stats["detection_frames"])
        })

    @app.route('/api/input_source', methods=['POST'])
    def update_input_source():
        """Switch runtime input source between camera and dataset."""
        payload = request.get_json(silent=True) or {}
        mode = str(payload.get('mode', '')).strip().lower()
        dataset_path = str(payload.get('dataset_path', '')).strip()

        success, message = app_instance.switch_input_source(mode, dataset_path)
        status_code = 200 if success else 400

        source_state = app_instance.get_input_source_state()
        return jsonify({
            'success': success,
            'message': message,
            'mode': source_state.get('mode', 'camera'),
            'dataset_path': source_state.get('dataset_path', ''),
        }), status_code

    @app.route('/api/camera_state', methods=['POST'])
    def update_camera_state():
        """Enable or disable an individual camera at runtime."""
        payload = request.get_json(silent=True) or {}
        camera_id = str(payload.get('camera_id', '')).strip().lower()
        enabled = bool(payload.get('enabled', False))

        if not camera_id:
            return jsonify({'success': False, 'message': 'camera_id is required'}), 400

        success, message = app_instance.set_camera_enabled(camera_id, enabled)
        status_code = 200 if success else 400
        source_state = app_instance.get_input_source_state()
        return jsonify({
            'success': success,
            'message': message,
            'camera_id': camera_id,
            'enabled': source_state.get('camera_enabled', {}).get(camera_id, enabled),
            'camera_enabled': source_state.get('camera_enabled', {}),
        }), status_code

    @app.route('/api/perf_breakdown')
    def api_perf_breakdown():
        """Return rolling performance timing split for capture/inference/postprocess/web."""
        window_raw = request.args.get('window_s', '').strip()
        window_s = None
        if window_raw:
            try:
                window_s = float(window_raw)
            except ValueError:
                return jsonify({'success': False, 'message': 'window_s must be numeric'}), 400

        breakdown = app_instance.get_perf_breakdown(window_s=window_s)
        breakdown['success'] = True
        return jsonify(breakdown)

    @app.route('/api/stats')
    def api_stats():
        """
        Return current system and detection statistics as JSON.
        
        This endpoint provides real-time statistics including:
        - Detection counts (Asian/European hornets, total)
        - System performance (CPU, RAM, temperature, uptime)
        - SMS alert statistics
        - Hourly detection data for charts
        - Recent detection log entries
        
        Returns:
            dict: JSON response with complete system statistics
        """
        # Calculate uptime (matching original format)
        uptime = datetime.datetime.now() - stats["start_time"]
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        stats["uptime"] = f"{hours}h {minutes}m"

        # Get system stats (non-blocking)
        try:
            stats["cpu_usage"] = psutil.cpu_percent(interval=None)  # Non-blocking
            stats["ram_usage"] = psutil.virtual_memory().percent
            stats["disk_usage"] = psutil.disk_usage('/').percent
        except:
            pass

        # CPU temperature (Raspberry Pi)
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = int(f.read()) / 1000
                stats["cpu_temp"] = temp
        except:
            stats["cpu_temp"] = 0

        # Prepare hourly data with caching (only recalculate if detections changed)
        current_total_detections = stats.get("total_detections", 0)
        if hourly_data_cache['last_update'] != current_total_detections:
            # Recalculate hourly data
            hourly_data_cache['last_update'] = current_total_detections
            
            # 24-hour detailed data (matching original)
            hourly_data_cache['data_24h'] = []
            for hour in range(24):
                hourly_data_cache['data_24h'].append({
                    "hour": f"{hour:02d}:00",
                    "velutina": hourly_detections[hour]["velutina"],
                    "crabro": hourly_detections[hour]["crabro"],
                    "total": hourly_detections[hour]["velutina"] + hourly_detections[hour]["crabro"]
                })
            
            # 4-hour grouped data (for mobile)
            hourly_data_cache['data_4h'] = []
            for block in range(6):  # 6 blocks of 4 hours each
                start_hour = block * 4
                end_hour = start_hour + 3
                
                # Sum up detections for this 4-hour block
                block_velutina = 0
                block_crabro = 0
                for hour in range(start_hour, start_hour + 4):
                    block_velutina += hourly_detections[hour]["velutina"]
                    block_crabro += hourly_detections[hour]["crabro"]
                
                hourly_data_cache['data_4h'].append({
                    "hour": f"{start_hour:02d}-{end_hour:02d}h",
                    "velutina": block_velutina,
                    "crabro": block_crabro,
                    "total": block_velutina + block_crabro
                })
        
        # Use cached data
        hourly_data_24h = hourly_data_cache['data_24h']
        hourly_data_4h = hourly_data_cache['data_4h']

        response_data = dict(stats)
        # Inject config values for UI LEDs (always current)
        try:
            from vespai.main import VespAIApplication
            if app_config:
                response_data['enable_motion_detection'] = app_config.get('enable_motion_detection', False)
                response_data['save_detections'] = app_config.get('save_detections', False)
                response_data['confidence_threshold'] = float(app_config.get('confidence_threshold', 0.5) or 0.5)
                color_order = str(app_config.get('camerapi_color_order', 'bgr')).lower()
                response_data['camera_startup_log'] = f"Camera startup: color_order={color_order}"
                retention_days = int(app_config.get('detection_retention_days', 21) or 0)
                max_file_count = int(app_config.get('detection_max_file_count', 250) or 0)
                response_data['detection_cleanup_log'] = (
                    f"Detection cleanup: retention_days={retention_days}, max_file_count={max_file_count}"
                )
        except Exception as e:
            logger.warning(f"Could not inject config values for LEDs: {e}")
        response_data.pop("detection_frames", None)
        response_data["hourly_data"] = hourly_data_24h  # Default to 24h for backward compatibility
        response_data["hourly_data_24h"] = hourly_data_24h  # Detailed 24-hour data
        response_data["hourly_data_4h"] = hourly_data_4h   # Grouped 4-hour data
        
        # Add missing fields with defaults if not present
        response_data.setdefault("sms_sent", 0)
        response_data.setdefault("sms_cost", 0.0)
        response_data.setdefault("saved_images", 0)
        response_data.setdefault("last_sms_time", None)
        
        # Convert deque to list for JSON serialization
        if "detection_log" in response_data:
            response_data["detection_log"] = list(response_data["detection_log"])
        if "inference_timing_recent" in response_data:
            response_data["inference_timing_recent"] = list(response_data["inference_timing_recent"])
        if "hourly_stats" in response_data:
            response_data["hourly_stats"] = list(response_data["hourly_stats"])
        
        # Format timestamps
        if response_data.get("last_detection_time"):
            response_data["last_detection_time"] = response_data["last_detection_time"].strftime("%H:%M:%S")
        if response_data.get("last_sms_time"):
            response_data["last_sms_time"] = response_data["last_sms_time"].strftime("%H:%M:%S")
            
        if response_data.get("start_time"):
            response_data["start_time"] = response_data["start_time"].strftime("%H:%M:%S")

        # Convert any numpy arrays to JSON-serializable types
        response_data = convert_numpy_to_serializable(response_data)
        
        # Add health check information
        current_time = time.time()
        if 'last_update' in stats:
            response_data['system_health'] = {
                'last_update': current_time,
                'time_since_last_frame': current_time - stats.get('last_update', current_time),
                'status': 'healthy' if current_time - stats.get('last_update', current_time) < 30 else 'warning'
            }
        else:
            response_data['system_health'] = {
                'last_update': current_time,
                'status': 'unknown'
            }

        source_state = app_instance.get_input_source_state()
        response_data['input_mode'] = source_state.get('mode', 'camera')
        response_data['dataset_path'] = source_state.get('dataset_path', '')
        response_data['camera_modes'] = source_state.get('camera_modes', {})
        response_data['camera_enabled'] = source_state.get('camera_enabled', {})
        response_data['camera_aliases'] = source_state.get('camera_aliases', {})
        response_data['per_camera'] = stats.get('per_camera', {})

        camera_aliases = dict(response_data.get('camera_aliases') or {})
        camera_aliases.setdefault('camera1', 'Camera 1')
        camera_aliases.setdefault('camera2', 'Camera 2')
        response_data['camera_aliases'] = camera_aliases

        for entry in response_data.get('detection_log', []):
            camera_id = str(entry.get('camera_id', 'camera1')).strip().lower() or 'camera1'
            if not entry.get('camera_alias'):
                fallback = 'Camera 2' if camera_id == 'camera2' else 'Camera 1'
                entry['camera_alias'] = str(camera_aliases.get(camera_id, fallback))[:16]

        per_camera_stats = response_data.get('per_camera', {})
        for camera_id, camera_stats in per_camera_stats.items():
            if isinstance(camera_stats, dict) and not camera_stats.get('camera_alias'):
                fallback = 'Camera 2' if camera_id == 'camera2' else 'Camera 1'
                camera_stats['camera_alias'] = str(camera_aliases.get(camera_id, fallback))[:16]

        model_path = getattr(getattr(app_instance, 'model_manager', None), 'model_path', None)
        if model_path:
            parts = os.path.normpath(model_path).split(os.sep)
            response_data['model_name'] = '/'.join(parts[-2:]) if len(parts) > 1 else parts[-1]
        else:
            response_data['model_name'] = ''
        
        # Debug log frame_id periodically
        if hasattr(stats, 'get') and stats.get('frame_id', 0) % 50 == 0:
            print(f"DEBUG: API returning frame_id: {response_data.get('frame_id', 'NOT_FOUND')}")
        
        return jsonify(response_data)


# Template files have been extracted to separate files:
# - dashboard.html: Main modern dashboard with custom styling and orange neon cursor
# - frame.html: Detection frame viewer page
# - legacy_dashboard.html: Legacy backup template for fallback compatibility