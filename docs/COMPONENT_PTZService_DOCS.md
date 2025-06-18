# Component: PTZService

## Description

The `PTZService` class provides an interface for controlling a PTZ (Pan-Tilt-Zoom) camera using the ONVIF protocol. It handles the connection to the camera, manages media profiles, and exposes methods for continuous and absolute PTZ movements.

## Class Details

- **Class Name**: `PTZService`
- **File Location**: [`ptz_controller.py`](ptz_controller.py)

## Key Methods

- `__init__(self, ip, port, user, password)`: Initializes the connection to the ONVIF camera and retrieves the necessary media and PTZ profiles.
- `continuous_move(self, pan, tilt, zoom)`: Sends a command for continuous PTZ movement with the specified velocities.
- `stop(self, pan, tilt, zoom)`: Stops all ongoing PTZ movements.
- `set_zoom_absolute(self, zoom_value)`: Moves the zoom to an absolute position.
- `set_home_position(self)`: Moves the camera to its predefined home position.
- `get_zoom(self)`: Retrieves the current zoom position.

## Dependencies

- `onvif-zeep`: For ONVIF communication.
- `config.py`: For camera configuration settings.
