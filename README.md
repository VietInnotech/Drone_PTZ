# Drone Tracking Prototype (CPU-Only, Zoom-Enhanced)

## Key Inferences from Original Program

- Uses YOLO object detection for drone tracking.
- Controls ONVIF PTZ camera for pan/tilt.
- Original code was GPU-dependent (`model.to("cuda")`).
- Tracking logic centers drone and stops PTZ if lost.
- **Annotation is now handled with OpenCV only (no supervision dependency).**

## Enhanced Tracking with ByteTrack

- Integrates ByteTrack for multi-object tracking, enabling robust ID assignment and velocity-based prediction.
- Tracking leverages OpenCV for annotation and visualization.
- Requires `lap>=0.5.12` for optimal association and tracking accuracy.
- No supervision dependency; all tracking and annotation are handled with OpenCV and ByteTrack.
- Enhanced tracking improves drone re-identification and reduces ID switches, especially in challenging scenarios.

## CPU Conversion Changes

- Model now loads with `model.to("cpu")` for CPU-only operation.
- All dependencies in `requirements.txt` are CPU-compatible and minimal (no supervision).
- Frame skipping and efficient processing retained for performance.

## New Zoom Functionality

- Zoom activates when a drone is detected and confidence > 0.6.
- Calculates bounding box coverage; aims for 30-50% of frame area.
- Proportional zoom control: `zoom_factor = target_coverage / current_coverage`.
- Smooth zoom transitions and state management.
- Zoom resets (zooms out) if drone is lost for 2+ seconds.
- Error handling for all zoom operations.

## Configuring Zoom Speed

Zoom speed can be adjusted in two ways:

1. **Continuous Zoom Speed**  
   The speed for continuous zoom operations is set by the value passed to the [`set_zoom_continuous`](work3/onvif_controller.py) or [`set_zoom_relative`](work3/onvif_controller.py) methods in [`work3/onvif_controller.py`](work3/onvif_controller.py).

   - To increase or decrease the zoom speed, modify the value you pass to these methods in your code.
   - Higher values result in faster zoom; lower values slow it down.
   - Example: `set_zoom_continuous(0.5)` for moderate speed, `set_zoom_continuous(1.0)` for maximum speed.

2. **Stepwise Zoom Speed Limit**  
   For stepwise (incremental) zoom operations, the `ZOOM_RATE_LIMIT` constant in [`work3/config.py`](work3/config.py) indirectly constrains how quickly zoom steps can be issued.
   - Lowering `ZOOM_RATE_LIMIT` allows more frequent zoom steps (faster overall zoom).
   - Increasing it slows down the rate at which zoom steps are sent.

**To modify these settings:**

- For continuous zoom, adjust the argument in your calls to `set_zoom_continuous` or `set_zoom_relative` in your application logic.
- For stepwise zoom, edit the `ZOOM_RATE_LIMIT` value in [`work3/config.py`](work3/config.py).

## Usage Instructions

1. Place `best5.pt` in the `models/` directory (already present).
2. (Recommended) Create and activate a virtual environment:
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```

## Configuration

All system parameters are now managed in [`config.py`](config.py) for easy modification and minimal design. Edit the values in the `Config` class to adjust camera, detection, PTZ, zoom, and ONVIF settings.

**Example:**

```python
class Config:
    # Camera Settings
    CAMERA_INDEX = 0
    RESOLUTION_WIDTH = 1920
    RESOLUTION_HEIGHT = 1080
    FPS = 30

    # Detection Settings
    CONFIDENCE_THRESHOLD = 0.6
    MODEL_PATH = "../models/best5.pt"
    FRAME_SKIP = 0

    # PTZ Control Settings
    PTZ_PAN_GAIN = 2.0
    PTZ_TILT_GAIN = 2.0
    PTZ_PAN_THRESHOLD = 0.02
    PTZ_TILT_THRESHOLD = 0.02
    ZOOM_TARGET_COVERAGE = 0.4
    ZOOM_RATE_LIMIT = 0.1

    # ONVIF Camera Settings
    CAMERA_IP = "192.168.1.100"
    CAMERA_USER = "admin"
    CAMERA_PASS = "password"
```

**To change a parameter:**  
Open [`config.py`](config.py), edit the desired value, and save. All scripts will use the updated configuration automatically.

Parameters are grouped and commented for clarity. No external frameworks are used. 3. Install main dependencies:

```
pip install -r requirements.txt
```

4. (For testing) Install test dependencies:
   ```
   pip install -r test_requirements.txt
   ```
5. Run the tracker:
   ```
   python yolo_tracker.py
   ```
6. The system will:
   - Detect drones in the video stream.
   - Pan/tilt to center the drone.
   - Zoom in/out to keep the drone at 30-50% of the frame.
   - Zoom out if the drone is lost for more than 2 seconds.

## Notes

- The code is modular: PTZ logic is in `onvif_controller.py`, detection/tracking in `yolo_tracker.py`.
- Kalman filtering for persistent tracking can be added in future iterations.
- For best results, use a camera compatible with ONVIF PTZ and zoom.
