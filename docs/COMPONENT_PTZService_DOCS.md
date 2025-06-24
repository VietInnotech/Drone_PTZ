# Component: PTZService

## Description

The `PTZService` class provides an interface for controlling a PTZ (Pan-Tilt-Zoom) camera using the ONVIF protocol. It handles the connection to the camera, manages media profiles, and exposes methods for continuous and absolute PTZ movements.

## Class Details

- **Class Name**: `PTZService`
- **File Location**: [`ptz_controller.py`](ptz_controller.py)

## Key Methods

### Initialization & Connection

- `__init__(self, ip=None, port=80, user=None, password=None)`: Initializes the connection to the ONVIF camera and retrieves necessary profiles.
- `ramp(self, target, current)`: Helper method for smooth movement transitions.

### Movement Control

- `continuous_move(self, pan, tilt, zoom, threshold=0.01)`: Sends continuous PTZ movement commands.
- `stop(self, pan=True, tilt=True, zoom=True)`: Stops ongoing PTZ movements.

### Absolute Positioning

- `set_zoom_absolute(self, zoom_value)`: Moves zoom to an absolute position.
- `set_home_position(self)`: Moves camera to predefined home position.

### Zoom Control

- `set_zoom_home(self)`: Sets zoom to widest position (zmin).
- `set_zoom_relative(self, zoom_delta)`: Adjusts zoom by relative amount.
- `get_zoom(self)`: Retrieves current zoom position.

## Dependencies

### External Libraries

- `onvif-zeep`: For ONVIF communication.

### Internal Dependencies

- `config.py`: For camera configuration settings.
  - `CAMERA_CREDENTIALS`: Camera connection parameters
  - PTZ control parameters: `PTZ_MOVEMENT_GAIN`, `ZOOM_PARAMS`, etc.
- `utils.py`: Error handling helpers and logging utilities.

### Configuration Dependency

The `PTZService` class depends on centralized configuration from [`config.py`](../config.py:3). The following parameters are critical for operation:

- `CAMERA_CREDENTIALS`: Provides camera IP, username, and password for ONVIF connection.
- `PTZ_MOVEMENT_GAIN`: Gain for pan/tilt movement.
- `PTZ_MOVEMENT_THRESHOLD`: Threshold for movement activation.
- `ZOOM_TARGET_COVERAGE`, `ZOOM_RESET_TIMEOUT`, `ZOOM_MIN_INTERVAL`, `ZOOM_VELOCITY_GAIN`, `ZOOM_RESET_VELOCITY`, `NO_DETECTION_HOME_TIMEOUT`: All parameters controlling PTZ and zoom logic.

All configuration is accessed via the [`Config`](../config.py:3) class, ensuring maintainability and runtime flexibility.
