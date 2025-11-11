# Drone PTZ Tracking System

> Automated drone tracking using PTZ cameras with YOLO object detection and ONVIF control

## Quick Start (5 Minutes)

### Prerequisites

- Python 3.11
- PTZ camera with ONVIF support
- YOLO model file (`best5.pt`)

### Setup

1. **Install Pixi (if not already installed):**

   ```bash
   curl -fsSL https://pixi.sh/install.sh | bash
   ```

2. **Clone and enter the project:**

   ```bash
   cd /path/to/Drone_PTZ
   ```

3. **Install dependencies:**

   ```bash
   pixi install
   ```

4. **Configure your camera:**

   Edit `config.py` and update the camera settings:

   ```python
   # Camera Settings
   CAMERA_INDEX: int = 4  # Change to your camera index (try 0, 1, 2, etc.)

   # ONVIF Camera Credentials
   CAMERA_CREDENTIALS = {
       "ip": "192.168.1.70",      # Your camera IP
       "user": "admin",            # Your camera username
       "pass": "admin@123"         # Your camera password
   }
   ```

5. **Ensure model file exists:**

   ```bash
   ls models/best5.pt  # Should exist
   ```

6. **Run the system:**

   ```bash
   pixi run main
   ```

7. **Exit:**
   Press `q` in the video window to quit.

### PTZ Simulation Mode (Testing Without Hardware)

The system includes an optional **PTZ Simulator** for development and testing without a physical camera.

#### Quick Start with Simulation

1. **Prepare a test video:**

   Place a test video at `assets/videos/test.mp4`

2. **Enable simulation in `config.py`:**

   ```python
   USE_PTZ_SIMULATION = True
   VIDEO_SOURCE = "assets/videos/test.mp4"
   VIDEO_LOOP = True  # Rewind to start on EOF
   SIM_VIEWPORT = True  # Enable viewport cropping
   ```

3. **Run with simulation:**

   ```bash
   pixi run sim-video
   ```

4. **Two windows will display:**
   - **Detection**: Shows the simulated PTZ viewport with overlays
   - **Original**: Shows the full frame with viewport rectangle overlay

#### Simulation Features

- **Virtual PTZ Motion**: Simulates smooth pan/tilt/zoom without ONVIF
- **Viewport Cropping**: Realistic camera view simulation with cropping
- **Frame Rate Independent**: Motion is smooth regardless of frame rate
- **Video Looping**: Automatically rewind video on EOF
- **Non-Breaking**: Default behavior unchanged, fully opt-in

#### PTZ Simulator Configuration

All simulation parameters are in `config.py`:

```python
# Enable/Disable
USE_PTZ_SIMULATION: bool = False
VIDEO_SOURCE: str | None = None  # Path to video file

# Playback
VIDEO_LOOP: bool = True  # Rewind on EOF

# Viewport & Zoom
SIM_VIEWPORT: bool = True  # Enable viewport cropping
SIM_ZOOM_MIN_SCALE: float = 0.3  # Min viewport scale at max zoom
SIM_DRAW_ORIGINAL_VIEWPORT_BOX: bool = True  # Draw viewport rect on original

# Motion (defaults work well for most cases)
SIM_PAN_STEP: float = 0.05
SIM_TILT_STEP: float = 0.05
SIM_ZOOM_STEP: float = 0.05
```

#### How Simulation Works

1. **Pan/Tilt**: Virtual camera position ranges from -1 to +1 on each axis
2. **Zoom**: Scales the viewport from full frame (zoom=0) to zoomed in (zoom=1)
3. **Viewport**: Frame is cropped and resized based on current pan/tilt/zoom
4. **Detection**: Runs on the simulated viewport, not the original frame

#### Troubleshooting Simulation

**Video file not found?**

- Ensure path exists: `ls assets/videos/test.mp4`
- Use absolute path if relative path fails

**Viewport not visible?**

- Ensure `SIM_VIEWPORT = True` in config
- Check `SIM_DRAW_ORIGINAL_VIEWPORT_BOX = True` to see viewport on original

**Simulation disabled but still using camera?**

- Verify `USE_PTZ_SIMULATION = False` in config
- Check that `VIDEO_SOURCE = None` (or path is invalid)

#### For More Details

See [`docs/PTZ_SIMULATOR_PLAN.md`](docs/PTZ_SIMULATOR_PLAN.md) for complete specification and advanced usage.

### Troubleshooting

**Camera not found?**

- Check available cameras: `ls /dev/video*`
- Try different `CAMERA_INDEX` values in `config.py`
- Ensure camera permissions: `sudo usermod -a -G video $USER`

**Model file not found?**

- Verify `models/best5.pt` exists
- Update `MODEL_PATH` in `config.py` if using a different model

**Connection timeout?**

- Verify camera IP is reachable: `ping 192.168.1.70`
- Check ONVIF is enabled on the camera
- Verify credentials are correct

---

## Features

### Core Capabilities

- **YOLO Object Detection**: Real-time drone detection using YOLOv8
- **ONVIF PTZ Control**: Full pan/tilt/zoom camera control via ONVIF protocol
- **BoTSORT Tracking**: Multi-object tracking with persistent IDs
- **Automatic Tracking**: Camera automatically follows detected drones
- **Adaptive Zoom**: Automatically adjusts zoom to maintain optimal target size
- **CPU-Optimized**: Runs on CPU for broader hardware compatibility

### Tracking Features

- Multi-object tracking with BoTSORT algorithm
- Persistent ID assignment across frames
- Robust re-identification in challenging scenarios
- Minimal ID switches during occlusions
- Real-time FPS monitoring and performance stats

### PTZ Control

- **Pan/Tilt**: Smooth camera movement to center target
- **Zoom Control**: Proportional zoom based on target coverage
- **Auto-Home**: Returns to home position after losing target
- **Smooth Ramping**: Gradual acceleration/deceleration for smooth movement

### Configuration

All system parameters are centralized in `config.py`:

```python
# Camera Settings
CAMERA_INDEX = 4
RESOLUTION_WIDTH = 1280
RESOLUTION_HEIGHT = 720
FPS = 30

# Detection Settings
CONFIDENCE_THRESHOLD = 0.5
MODEL_PATH = "models/best5.pt"

# PTZ Control
PTZ_MOVEMENT_GAIN = 2.0
PTZ_MOVEMENT_THRESHOLD = 0.05
ZOOM_TARGET_COVERAGE = 0.3  # Target 30% of frame

# Zoom Behavior
ZOOM_VELOCITY_GAIN = 2.0
ZOOM_RESET_VELOCITY = 0.5
ZOOM_MIN_INTERVAL = 0.1
ZOOM_DEAD_ZONE = 0.03

# Timeouts
ZOOM_RESET_TIMEOUT = 2.0  # Zoom out after 2s without detection
NO_DETECTION_HOME_TIMEOUT = 5  # Return home after 5s without detection
```

### Adjusting Zoom Speed

Zoom behavior is controlled by several parameters in `config.py`:

- **`ZOOM_VELOCITY_GAIN`**: Controls zoom speed (higher = faster)
- **`ZOOM_TARGET_COVERAGE`**: Target object size (0.0-1.0, default 0.3 = 30% of frame)
- **`ZOOM_MIN_INTERVAL`**: Minimum time between zoom adjustments (seconds)
- **`ZOOM_DEAD_ZONE`**: Minimum coverage difference to trigger zoom

**Example adjustments:**

```python
# Faster, more aggressive zoom
ZOOM_VELOCITY_GAIN = 3.0
ZOOM_MIN_INTERVAL = 0.05

# Slower, gentler zoom
ZOOM_VELOCITY_GAIN = 1.0
ZOOM_MIN_INTERVAL = 0.2

# Larger target size (more zoomed in)
ZOOM_TARGET_COVERAGE = 0.5  # 50% of frame

# Larger target size (more zoomed in)
ZOOM_TARGET_COVERAGE = 0.5  # 50% of frame
```

---

## Architecture

### Project Structure

```txt
Drone_PTZ/
├── main.py              # Main application entry point
├── config.py            # Centralized configuration
├── detection.py         # YOLO detection service
├── ptz_controller.py    # ONVIF PTZ control service
├── models/              # YOLO model files
│   └── best5.pt
├── logs/                # Application logs
├── tests/               # Unit tests
└── docs/                # Documentation
```

### Key Components

1. **DetectionService** (`detection.py`)

   - Manages YOLO model
   - Runs object detection
   - Returns detected objects with tracking IDs

2. **PTZService** (`ptz_controller.py`)

   - Handles ONVIF camera connection
   - Controls pan/tilt/zoom movements
   - Implements smooth ramping for transitions

3. **Config** (`config.py`)

   - Central configuration management
   - Parameter validation on startup
   - Logging configuration

4. **Main Loop** (`main.py`)
   - Frame acquisition thread
   - Detection and tracking
   - PTZ control logic
   - Visualization overlay

---

## Development

### Development Workflow

#### Complete Development Pipeline

Run the full development workflow (lint → test → coverage):

```bash
pixi run dev
```

This runs all quality checks, tests, and coverage analysis in sequence.

#### Individual Tasks

```bash
# Run tests with coverage
pixi run test

# Run comprehensive code quality checks
pixi run lint

# Run test coverage analysis with target validation
pixi run test-coverage

# Run pre-commit validation (fast checks)
pixi run pre-commit

# Run CI pipeline (complete validation)
pixi run ci

# Format code (ruff)
pixi run format

# Run security analysis
pixi run security

# Clean test artifacts
pixi run clean
```

#### Task Descriptions

- **`dev`**: Complete development workflow (lint → test → coverage)
- **`test`**: Run test suite with coverage reporting
- **`lint`**: Code quality checks (formatting, linting, security)
- **`test-coverage`**: Detailed coverage analysis with target validation
- **`pre-commit`**: Fast pre-commit validation (syntax, formatting)
- **`ci`**: Complete CI pipeline with artifacts
- **`format`**: Auto-format code using ruff
- **`security`**: Security analysis with bandit
- **`clean`**: Clean test artifacts and coverage reports
- **`main`**: Run the main application
- **`cam`**: Test camera detection

#### Development Scripts

For advanced usage, Python scripts are available in `scripts/`:

- `scripts/test-coverage.py` - Detailed coverage analysis
- `scripts/lint.py` - Code quality checks
- `scripts/ci.py` - CI pipeline

### Logging

Logs are written to `logs/app.log` with rotation:

- Rotation: Every 5 MB
- Retention: 30 days
- Configurable in `config.py`

### Adding New Features

1. Update configuration in `config.py`
2. Add validation in `Config.validate()`
3. Implement feature in appropriate service
4. Add tests in `tests/`
5. Update documentation

---

## Performance

### Expected Performance

- **FPS**: ~30 fps (1280x720 on modern CPU)
- **Detection Latency**: <100ms per frame
- **PTZ Response**: <200ms

### Optimization Tips

1. **Reduce resolution** for higher FPS:

   ```python
   RESOLUTION_WIDTH = 640
   RESOLUTION_HEIGHT = 480
   ```

2. **Adjust FPS window** for smoother metrics:

   ```python
   FPS_WINDOW_SIZE = 60  # More stable FPS reading
   ```

3. **Tune PTZ ramping** for smoother movement:

   ```python
   PTZ_RAMP_RATE = 0.1  # Slower, smoother transitions
   ```

---

## License

See repository for license information.

## Contributing

See `AGENTS.md` for development guidelines and coding standards.

---

## Support

For issues or questions:

1. Check the Troubleshooting section above
2. Review logs in `logs/app.log`
3. Ensure configuration is validated (errors appear on startup)
4. Check camera and network connectivity
