# COMPONENT_Config_DOCS

## Overview

This document describes the configuration parameters defined in [`config.py`](config.py:3) for the PTZ camera system. All parameters are centralized in the `Config` class.

---

## Parameter Documentation

### Logging Settings

- **LOG_FILE**: Path to the log file.
- **LOG_LEVEL**: Logging level (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
- **LOG_FORMAT**: Format string for log messages.
- **LOG_ROTATION**: Log rotation policy (e.g., '10 MB', '1 week').
- **LOG_RETENTION**: How long to retain old log files.
- **LOG_ENQUEUE**: Whether to use multiprocessing-safe log handling.
- **LOG_BACKTRACE**: Enable backtrace in loguru for better error context.
- **LOG_DIAGNOSE**: Enable loguru's diagnose feature for detailed exception info.
- **write_log_file**: If True, write logs to app.log file.
- **reset_log_on_start**: If True, truncate app.log at program start.

### Camera Settings

- **CAMERA_INDEX**: Camera device index (e.g., 0 for default webcam).
- **RESOLUTION_WIDTH**: Frame width in pixels.
- **RESOLUTION_HEIGHT**: Frame height in pixels.
- **FPS**: Desired frames per second.

### Detection Settings

- **CONFIDENCE_THRESHOLD**: YOLO detection confidence threshold.
- **MODEL_PATH**: Path to YOLO model.

### PTZ Control Settings

- **PTZ_MOVEMENT_GAIN**: Gain for pan/tilt control (tuned for smoother movement).
- **PTZ_MOVEMENT_THRESHOLD**: Minimum normalized error to trigger pan/tilt (increased for stability).
- **ZOOM_TARGET_COVERAGE**: Target object coverage (fraction of frame).
- **ZOOM_RESET_TIMEOUT**: Timeout (seconds) after which zoom resets if no object detected.
- **ZOOM_MIN_INTERVAL**: Minimum interval between zoom commands.

### Continuous Zoom Control

- **ZOOM_VELOCITY_GAIN**: Proportional gain for continuous zoom velocity.
- **ZOOM_RESET_VELOCITY**: Velocity for zoom reset to home position.

### ONVIF Camera Credentials

- **CAMERA_CREDENTIALS**: Dictionary containing:
  - `ip`: Camera IP address
  - `user`: Camera username
  - `pass`: Camera password

### Other

- **NO_DETECTION_HOME_TIMEOUT**: Home timeout for no detection (seconds).

---

## Related Classes

- [`Config`](config.py:3): Central configuration class.
- [`setup_logging()`](config.py:80): Logger setup function.
