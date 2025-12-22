# Drone PTZ Tracking System

> Automated drone tracking using PTZ cameras with YOLO-based detection, ByteTrack ID
> tracking, and ONVIF PTZ control. Supports both real PTZ cameras and a fully
> configurable PTZ simulator.

## Quick Start (5 Minutes)

### Prerequisites

- Python 3.11
- PTZ camera with ONVIF support (for hardware mode)
- YOLO model file (placed under `assets/models/yolo/`)

### Setup

1. Install Pixi (if not already installed):

   ```bash
   curl -fsSL https://pixi.sh/install.sh | bash
   ```

2. Clone and enter the project:

   ```bash
   git clone <repo-url> Drone_PTZ
   cd Drone_PTZ
   ```

3. Install dependencies:

   ```bash
   pixi install
   ```

4. Configure the system:

   Edit `config.yaml` to match your environment (see "Configuration" below for the
   full schema and example).

5. Ensure model file exists:

   ```bash
   ls assets/models/yolo
   # Ensure at least one model file is present, e.g. best5.pt or best.onnx
   ```

6. Run the system with your configured camera or simulator:

   ```bash
   pixi run main
   ```

7. Exit:

   Press `q` in the video window to quit.

---

## Analytics API Server (Metadata + Control)

This repo also ships an analytics-only HTTP/WebSocket API server (it does **not** serve video).

```bash
pixi run api
```

Optional overrides:

```bash
API_HOST=0.0.0.0 API_PORT=8080 API_PUBLISH_HZ=10 pixi run api
```

See `docs/ANALYTICS_WEB_INTEGRATION_GUIDE.md` for endpoints and browser integration.

## PTZ Simulation Mode (No Hardware Required)

The system includes an optional PTZ Simulator for development and testing without a
physical camera. Simulation is fully driven by `config.yaml`.

### Quick Start with Simulation

1. Prepare a test video:

   - Place a video under `assets/videos/`, for example:
     - `assets/videos/test.mp4`
     - `assets/videos/V_DRONE_045.mp4`

2. Enable simulation in `config.yaml` under `ptz_simulator`:

   ```yaml
   ptz_simulator:
     use_ptz_simulation: true
     video_source: "assets/videos/test.mp4"
     video_loop: true
     viewport: true
   ```

3. Run with simulation:

   ```bash
   pixi run sim-video
   ```

4. Two windows will display (depending on settings):

   - Detection / Simulated Viewport: simulated PTZ viewport with overlays
   - Original: full frame with viewport rectangle overlay (if enabled)

### Simulation Parameters

Configured via `ptz_simulator` in `config.yaml`:

```yaml
ptz_simulator:
  # Core toggles
  use_ptz_simulation: true        # Use simulator instead of real PTZ
  video_source: "assets/videos/test.mp4"  # Input video for simulation
  video_loop: true                # Rewind to start on EOF

  # Viewport & zoom
  viewport: true                  # Enable viewport cropping visualization
  zoom_min_scale: 0.3             # Min normalized viewport scale at max zoom
  draw_original_viewport_box: true  # Draw viewport rectangle over original feed

  # Motion (pan/tilt/zoom step sizes per update)
  pan_step: 0.1
  tilt_step: 0.1
  zoom_step: 0.1
```

Behavior:

- Simulated PTZ backend mirrors the public API of the real `PTZService`
  [`src/ptz_simulator.py`](src/ptz_simulator.py:1).
- `main()` [`src/main.py`](src/main.py:1) selects simulator vs real PTZ based on
  `ptz_simulator.use_ptz_simulation`.
- Detection and tracking run on the simulated viewport, giving a realistic
  representation of PTZ behavior without sending ONVIF commands.

### Troubleshooting Simulation

- Video file not found:
  - Verify path: `ls assets/videos/`
  - Ensure `ptz_simulator.video_source` is correct in `config.yaml`
- Viewport not visible:
  - Ensure `ptz_simulator.viewport: true`
  - Ensure `ptz_simulator.draw_original_viewport_box: true` if you expect overlay
- Simulation disabled but still expected:
  - Confirm `ptz_simulator.use_ptz_simulation: true` in `config.yaml`

For runtime behavior and design details see
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md:1).

---

## Troubleshooting (Hardware Mode)

- Camera not found:
  - Check available devices: `ls /dev/video*`
  - Verify `camera.index` in `config.yaml`
  - Ensure user is in `video` group
- Connection timeout (ONVIF):
  - Verify camera IP reachable via `ping`
  - Ensure ONVIF is enabled on the camera
  - Verify `camera_credentials` in `config.yaml`
- Model file not found:
  - Ensure path under `assets/models/yolo/`
  - Match `detection.model_path` in `config.yaml`
- Configuration errors:
  - Invalid or missing fields are reported on startup by `load_settings()`;
    fix errors in `config.yaml` and restart.

---

## Features

### Core Capabilities

- YOLO-based object detection
- ByteTrack-style ID-based multi-object tracking
- ONVIF PTZ control with smooth ramping
- ID-locked drone tracking and automatic re-centering
- Adaptive zoom to maintain desired target coverage
- CPU-friendly pipeline with tunable performance

### Tracking Features

Tracking is implemented as an ID-based pipeline combining detection, tracking state
management, and deterministic target selection:

- YOLO detections are associated with tracks using a ByteTrack-like mechanism.
- `TrackingPhase` state machine
  [`src/tracking/state.py`](src/tracking/state.py:1) defines explicit phases:
  - `IDLE`: No active target.
  - `SEARCHING`: Looking for a candidate target that matches criteria.
  - `TRACKING`: Actively tracking a selected ID; PTZ follows this target.
  - `LOST`: Target temporarily lost; system waits for re-identification before
    dropping to `SEARCHING`/`IDLE`.
- `TrackerStatus` dataclass
  [`src/tracking/state.py`](src/tracking/state.py:21) maintains:
  - Current phase
  - Selected target ID
  - Timestamps and loss grace windows
  - Convenience helpers to transition between phases
- ID-based target selection utilities
  [`src/tracking/selector.py`](src/tracking/selector.py:1):
  - Stable selection of which track (ID) to follow
  - Prioritization rules (e.g., by label, confidence, stability)
- Integration in `main()` [`src/main.py`](src/main.py:1):
  - Consumes detections, updates `TrackerStatus`
  - Chooses a single ID-locked target
  - Drives PTZ commands based on target position and `TrackingPhase`
- PTZ behavior by phase (high level):
  - `TRACKING`: Aggressively follows and zooms to maintain coverage.
  - `LOST`: Holds position, allows brief grace period for re-acquisition.
  - `SEARCHING`: Can scan or hold home position based on configuration.
  - `IDLE`: Camera stays at home or default pose.

### NanoTrack Single-Object Tracking (SOT)

The system includes optional NanoTrack-based single-object tracking for improved
target continuity and reduced compute. When enabled, NanoTrack complements the YOLO +
ByteTrack pipeline:

- **Lightweight SOT**: Uses OpenCV's `TrackerNano` (NanoTrack ONNX models) for
  frame-to-frame tracking without running YOLO on every frame.
- **Automatic seeding**: When a target ID is locked, the system seeds NanoTrack with
  the detection bbox and switches to SOT-based PTZ control.
- **Periodic re-acquisition**: YOLO runs periodically (configurable interval) to
  validate and re-seed the tracker, preventing drift.
- **Drift detection**: Monitors center drift between SOT and YOLO detections;
  re-seeds if drift exceeds threshold.
- **Graceful fallback**: On SOT failure or excessive drift, automatically falls back
  to YOLO-based tracking.
- **Visual feedback**: SOT bbox displayed in magenta; status overlay shows SOT
  state.
- **Configuration**: Fully configurable via `tracking` section in `config.yaml`
  (see below).

Implementation details:
- Module: [`src/tracking/nanotracker.py`](src/tracking/nanotracker.py:1)
- Integration: [`src/main.py`](src/main.py:679) (TRACKING phase)
- Models: Place ONNX models in `assets/models/nanotrack/` (already included)
- Settings: [`src/settings.py`](src/settings.py:123) (TrackingSettings dataclass)

### PTZ Control

- Smooth pan/tilt control to center the selected target
- Zoom control based on target coverage with velocity ramping
- Auto-home after configurable period without detections
- All control parameters are configured via `config.yaml` (`ptz_control` and
  `performance` sections).

---

## Configuration

All runtime behavior is configured via `config.yaml` at the project root. The YAML
is loaded and validated by `load_settings()`
[`src/settings.py`](src/settings.py:141), which returns a strongly typed
`Settings` object composed of multiple dataclasses.

### Configuration Sections

The top-level structure:

- `logging`:
  - Log file, level, optional rotation/behavior.
- `camera`:
  - Capture index, resolution, fps.
- `detection`:
  - Confidence, model path, target labels.
- `ptz_control`:
  - PTZ movement gains, thresholds, zoom behavior.
- `performance`:
  - FPS window, zoom dead zone, frame queue.
- `camera_credentials`:
  - ONVIF connection details.
- `ptz_simulator`:
  - Simulator toggles and video source.
- `tracking`:
  - NanoTrack single-object tracking (SOT) configuration.

Note: Internally, these are mapped into the `Settings` dataclass hierarchy:
[`src/settings.py`](src/settings.py:1)
(`LoggingSettings`, `CameraSettings`, `DetectionSettings`, `PTZSettings`,
`PerformanceSettings`, `SimulatorSettings`, `TrackingSettings`, wrapped by `Settings`).

### Example config.yaml

```yaml
logging:
  log_file: "logs/app.log"
  log_level: "INFO"
  write_log_file: true      # Enable/disable file logging
  reset_log_on_start: false # If true, truncate log on startup

camera:
  source: "camera"  # one of: "camera", "video", "webrtc"
  camera_index: 0
  resolution_width: 1280
  resolution_height: 720
  fps: 30


## WebRTC input (client mode)

The application can act as a **WebRTC client** and connect to an existing
WebRTC server endpoint to receive video frames as the camera input.

1. Configure `config.yaml`:

```yaml
camera:
  source: "webrtc"
  webrtc_url: "http://localhost:8889/camera_1/"  # page or offer endpoint
```

2. Start the app (the client will POST an SDP offer to `webrtc_url + 'offer'` if needed).

3. The app will receive the remote video track and inject frames into the
   same OpenCV/detection pipeline used for local cameras.

Notes:
- The `webrtc_url` can point to the page (e.g. `http://host:port/camera_1/`) or
  directly to an offer endpoint (e.g. `http://host:port/camera_1/offer`). If the
  URL ends with `/`, the client will append `offer` automatically.
- This is a lightweight, Python-based client suitable for few streams and
  testing. For production, consider using a media server or a robust
  reconnection/monitoring solution.

camera_credentials:
  ip: "192.168.1.70"
  user: "admin"
  password: "admin@123"

detection:
  model_path: "assets/models/yolo/best5.pt"
  confidence_threshold: 0.5
  target_labels:
    - "drone"
    - "uav"

ptz_control:
  ptz_movement_gain: 2.0
  ptz_movement_threshold: 0.05
  zoom_target_coverage: 0.3
  zoom_reset_timeout: 2.0
  zoom_min_interval: 0.1
  zoom_velocity_gain: 0.5
  zoom_reset_velocity: 0.5
  ptz_ramp_rate: 0.2
  no_detection_home_timeout: 5

performance:
  fps_window_size: 30
  zoom_dead_zone: 0.03
  frame_queue_maxsize: 1

ptz_simulator:
  use_ptz_simulation: false
  video_source: "assets/videos/V_DRONE_045.mp4"
  video_loop: true
  viewport: true
  zoom_min_scale: 0.3
  draw_original_viewport_box: true
  pan_step: 0.1
  tilt_step: 0.1
  zoom_step: 0.1

tracking:
  use_nanotrack: false                      # Enable NanoTrack SOT
  nanotrack_backbone_path: "assets/models/nanotrack/nanotrack_backbone_sim.onnx"
  nanotrack_head_path: "assets/models/nanotrack/nanotrack_head_sim.onnx"
  reacquire_interval_frames: 10             # YOLO re-run interval while SOT active
  max_center_drift: 0.15                    # Max drift before re-seeding (fraction)
  max_failed_updates: 5                     # Max consecutive SOT failures before release
  dnn_backend: default                      # default|opencv|cuda|vulkan|openvino
  dnn_target: cpu                           # cpu|cuda|opencl|vulkan
```

### load_settings() and Settings Hierarchy

- `load_settings()` [`src/settings.py`](src/settings.py:141):

  - Loads `config.yaml` from the project root.
  - Applies defaults when fields are omitted.
  - Constructs a typed `Settings` instance:
    - `Settings.logging: LoggingSettings`
    - `Settings.camera: CameraSettings`
    - `Settings.detection: DetectionSettings`
    - `Settings.ptz: PTZSettings`
    - `Settings.performance: PerformanceSettings`
    - `Settings.simulator: SimulatorSettings`
    - `Settings.tracking: TrackingSettings`

- Usage in `main`:

  ```python
  from src.settings import load_settings

  def main() -> None:
      settings = load_settings()
      # settings is passed into detection, tracking, PTZ, and simulator components
  ```

### Configuration Validation and Error Handling

- `load_settings()` performs structured validation:

  - Ensures required sections/fields exist or have safe defaults.
  - Validates numeric ranges where appropriate (e.g., thresholds, gains).
  - Validates paths where necessary (e.g., `detection.model_path` existence
    is checked when initializing detection).
  - Validates that ONVIF credentials are present when required.

- On error:

  - Raises descriptive exceptions (e.g., invalid type, missing critical field).
  - Errors are surfaced early at startup so misconfiguration is clear.
  - Logging configuration is applied early so issues are visible in console and/or
    log file.

---

## Architecture

### Project Structure

```txt
Drone_PTZ/
├── src/                           # Source code directory
│   ├── main.py                    # Main application entry point
│   ├── detection.py               # YOLO detection service
│   ├── ptz_controller.py          # ONVIF PTZ control service
│   ├── ptz_simulator.py           # PTZ simulation service
│   ├── settings.py                # YAML-based configuration system
│   └── tracking/                  # Tracking subsystem
│       ├── __init__.py
│       ├── state.py               # TrackingPhase/TrackerStatus state machine
│       ├── selector.py            # ID-based target selection utilities
│       └── nanotracker.py         # NanoTrack SOT wrapper
├── assets/                        # Static assets
│   ├── models/
│   │   ├── yolo/                  # YOLO model files
│   │   └── nanotrack/             # NanoTrack ONNX models
│   └── videos/                    # Test and demo videos
├── tests/                         # Test suite (unit + integration)
├── docs/                          # Additional documentation
├── config.yaml                    # Main configuration file
├── pixi.toml                      # Environment and task definitions
└── pyproject.toml                 # Python project configuration
```

For a detailed runtime and component-level view, see
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md:1).

### Key Components

1. Detection Service
   - [`src/detection.py`](src/detection.py:1)
   - Loads YOLO model from `detection.model_path`.
   - Runs inference and provides detections for tracking.

2. PTZ Service
   - [`src/ptz_controller.py`](src/ptz_controller.py:1)
   - Handles ONVIF camera connection and PTZ control.
   - Uses config-driven gains, thresholds, and ramping parameters.

3. PTZ Simulator
   - [`src/ptz_simulator.py`](src/ptz_simulator.py:1)
   - Implements a PTZ-like API purely in software.
   - Driven by `ptz_simulator` settings in `config.yaml`.

4. Tracking State Machine
   - [`src/tracking/state.py`](src/tracking/state.py:1)
   - `TrackingPhase` enum and `TrackerStatus` dataclass.
   - Encapsulates tracking lifecycle and transitions.

5. Target Selector
   - [`src/tracking/selector.py`](src/tracking/selector.py:1)
   - Deterministic ID-based selection based on configured criteria.

6. Main Orchestrator
   - [`src/main.py`](src/main.py:1)
   - Calls `load_settings()`.
   - Sets up:
     - Frame producer (real camera or simulator) → queue
     - Detection → tracking → PTZ control consumer loop
   - Applies ID-locked tracking and PTZ behavior according to `TrackingPhase`.
   - Uses settings to tune performance, logging, and behavior.

---

## Development

### Pixi Tasks (Authoritative)

Run all commands via Pixi to ensure the correct environment:

```bash
# Complete development workflow (lint → test → coverage)
pixi run dev

# Run tests with coverage
pixi run test

# Lint and static checks
pixi run lint

# Coverage analysis
pixi run test-coverage

# Fast pre-commit checks
pixi run pre-commit

# Full CI pipeline
pixi run ci

# Auto-format code (ruff)
pixi run format

# Security scan (bandit)
pixi run security

# Clean artifacts
pixi run clean

# Run main application (uses config.yaml)
pixi run main

# Run in simulation/video mode (uses ptz_simulator config)
pixi run sim-video

# Camera detection test
pixi run cam
```

Task semantics are defined in [`pixi.toml`](pixi.toml).

### Frame Pipeline Architecture

The runtime follows a producer/consumer model (see
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md:117)):

- Producer:
  - A dedicated frame grabber uses `camera` or `ptz_simulator.video_source` config
    to push frames into a bounded queue (`performance.frame_queue_maxsize`).
- Consumer:
  - Main loop pulls frames:
    - Optionally applies simulated PTZ viewport.
    - Runs detection and tracking.
    - Uses `TrackerStatus` / `TrackingPhase` to decide PTZ commands.
    - Issues PTZ commands through real or simulated backend.
- This decoupling allows:
  - Stable FPS management (`performance.fps_window_size`).
  - Back-pressure control via queue sizing.
  - Clear separation of capture, detection, and control logic.

### Settings-Driven PTZ and Performance Tuning

Developers adjust behavior by editing `config.yaml`:

- Adjust `ptz_control` for:
  - Aggressiveness of pan/tilt corrections.
  - Target coverage and zoom responsiveness.
  - Home/timeout behavior when no target is visible.
- Adjust `performance` for:
  - FPS smoothing window.
  - Zoom dead zone to avoid jitter.
  - Frame queue size to balance latency vs stability.
- No code changes are required for typical tuning.

---

## Assets and Models

- YOLO models are stored in:

  ```txt
  assets/models/yolo/
  ```

  Example files:

  - `best5.pt`
  - `best10.pt`
  - `best18.pt`
  - `best55.pt`
  - `30-5.11s.pt`
  - `roboflow3.0v8.pt`
  - `roboflowaccurate.pt`
  - `best.onnx`

- Configure which model to use via `config.yaml`:

  ```yaml
  detection:
    model_path: "assets/models/yolo/best5.pt"
  ```

- Sample videos live under:

  ```txt
  assets/videos/
  ```

  Use these paths in `ptz_simulator.video_source` for reproducible tests and demos.

---

## Performance

Baseline expectations (dependent on model and hardware):

- ~30 FPS at 1280x720 on a modern CPU with suitable model.
- PTZ control latency typically < 200 ms in stable environments.

To optimize:

- Lower resolution via `camera` section in `config.yaml`.
- Tune `performance.fps_window_size` and PTZ gains in `ptz_control`.
- Use lighter YOLO models from `assets/models/yolo/`.

---

## Logging

Logging behavior is driven by `logging` in `config.yaml`:

- Log file path and verbosity configurable.
- Intended to support rotation/retention as needed.
- Startup and validation errors are logged to help diagnose configuration and
  connectivity issues.

---

## Contributing

- Follow repository standards in [`AGENTS.md`](AGENTS.md).
- Use Pixi for all tasks.
- Add or update tests under `tests/` for any behavior change.
- Keep documentation in sync with code (README + `docs/`).

---

## License

See the repository for license information.

---

## Support

For issues or questions:

1. Check this README and `docs/ARCHITECTURE.md`.
2. Inspect logs as configured in `config.yaml`.
3. Verify `config.yaml` is valid and `load_settings()` completes without errors.
4. Check camera, network connectivity, and ONVIF configuration when using real PTZ.
