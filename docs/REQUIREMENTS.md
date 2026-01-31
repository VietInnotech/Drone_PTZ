# PTZ AI Control System Requirements

## Functional Requirements

1. Camera Control
2. Object Detection
3. PTZ Automation
   - Pan range: -180° to +180° (full coverage)
   - Tilt range: -30° to +90° (mechanical limits)
   - Zoom range: 1x to 30x optical zoom
   - Preset management: 16 programmable presets
   - Automatic tracking of detected objects
4. Logging System
5. Control System Stability
   -16. Zoom-Compensated Speed Control: PTZ gains are scaled by zoom level.
17. Axis Inversion: Support for inverting pan/tilt axes via config.
18. Concurrent Detection: Support for running visible and thermal detection simultaneously.
19. SkyShield Integration: Support for fetching and using camera sources from SkyShield registry.
20. Tracking Priority: Selectable priority (Visible/Thermal) for PTZ control.
18. Model Management
    - List available models via API
    - Upload new model files (.pt, .onnx)
    - Delete existing models (prevent deleting active model)
    - Activate model via API (switches runtime detection model)

## Non-Functional Requirements

### Performance

- Real-time response: <500ms latency
  - PTZ control latency: <200ms
- High availability: 99.9% uptime
  - PTZ reliability: 99% operational reliability
- Camera control frame rate: 30fps minimum

### Security
- Reverse Engineering Protection: Artifacts must be compiled to binary executable (e.g., PyInstaller) to prevent casual source inspection.

### Logging


- Logging system must support file output and log rotation
- Configurable log levels (DEBUG, INFO, WARNING, ERROR)
- Log rotation based on size and time

## Configuration Options

### Logging

- LOG_FILE (str): Path to the log file
- LOG_LEVEL (str): Logging level
- LOG_FORMAT (str): Format string for log messages
- LOG_ROTATION (str): Log rotation policy
- LOG_RETENTION (str): Log retention duration
- LOG_ENQUEUE (bool): Multiprocessing-safe log handling
- LOG_BACKTRACE (bool): Enable backtrace in loguru
- LOG_DIAGNOSE (bool): Enable diagnose feature in loguru
- write_log_file (bool): Enable/disable writing logs to file
- reset_log_on_start (bool): Clear log file on application start

- CAMERA_SOURCE_CONFIG (Model): Unified config for camera, RTSP, WebRTC, or SkyShield.
- SKYSHIELD_CONFIG (Model): Base URL and MediaMTX settings for SkyShield integration.

### Detection

- CONFIDENCE_THRESHOLD (float): YOLO detection confidence threshold
- MODEL_PATH (str): Path to YOLO model

### PTZ Control

- PTZ_MOVEMENT_GAIN (float): Gain for pan/tilt control
- PTZ_MOVEMENT_THRESHOLD (float): Minimum normalized error to trigger pan/tilt
- ZOOM_TARGET_COVERAGE (float): Target object coverage (fraction of frame)
- ZOOM_RESET_TIMEOUT (float): Timeout after which zoom resets if no object detected
- ZOOM_MIN_INTERVAL (float): Minimum interval between zoom commands
- ZOOM_VELOCITY_GAIN (float): Proportional gain for continuous zoom velocity
- ZOOM_RESET_VELOCITY (float): Velocity for zoom reset to home position
- NO_DETECTION_HOME_TIMEOUT (int): Home timeout for no detection (seconds)
- INVERT_PAN (bool): Invert pan direction
- INVERT_TILT (bool): Invert tilt direction
- ENABLE_ZOOM_COMPENSATION (bool): scale PTZ speed based on zoom
- ZOOM_MAX_MAGNIFICATION (float): Max magnification for zoom compensation

- VISIBLE_DETECTION (Model): Enabled, camera source, confidence, and target labels.
- THERMAL_DETECTION (Model): Enabled, camera source, method, and parameters.
- TRACKING_PRIORITY (str): Selection of visibility mode for PTZ control.
- THERMAL_DETECTION_METHOD (str): Detection method - "contour", "blob", or "hotspot"
- THERMAL_THRESHOLD_VALUE (int): Fixed threshold value for binary mask (0-255)
- THERMAL_USE_OTSU (bool): Use Otsu's automatic thresholding
- THERMAL_CLAHE_CLIP_LIMIT (float): CLAHE contrast enhancement clip limit
- THERMAL_CLAHE_TILE_SIZE (int): CLAHE tile grid size
- THERMAL_MIN_AREA (int): Minimum blob/contour area in pixels
- THERMAL_MAX_AREA (int): Maximum blob/contour area in pixels
- THERMAL_USE_KALMAN (bool): Enable Kalman filter smoothing for centroid tracking
- THERMAL_CAMERA_SOURCE (str): Thermal camera input source (camera, rtsp, video, webrtc)
- THERMAL_CAMERA_INDEX (int): Thermal camera device index (separate from visible camera)
- THERMAL_CAMERA_WEBRTC_URL (str): MediaMTX/WebRTC URL for thermal stream
