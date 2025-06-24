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

## Non-Functional Requirements

### Performance

- Real-time response: <500ms latency
  - PTZ control latency: <200ms
- High availability: 99.9% uptime
  - PTZ reliability: 99% operational reliability
- Camera control frame rate: 30fps minimum

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

### Camera

- CAMERA_INDEX (int): Camera device index
- RESOLUTION_WIDTH (int): Frame width in pixels
- RESOLUTION_HEIGHT (int): Frame height in pixels
- FPS (int): Desired frames per second
- CAMERA_CREDENTIALS (dict): {ip, user, pass}

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
