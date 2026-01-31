# Drone PTZ Tracking System Architecture

This document describes the runtime architecture as implemented in the current codebase.
It reflects the typed `Settings` configuration system, the PTZ controller and simulator,
the YOLO + ByteTrack detection pipeline, and the ID-based tracking state machine.

## Components

1. Main Orchestrator
2. Detection Service
3. PTZ Service (real camera)
4. Simulated PTZ Service
5. Tracking Subsystem
6. Settings / Configuration System
7. Logging

## Source Layout

- [`src/main.py`](src/main.py:504) — main entrypoint, orchestration, frame loop, overlays.
- [`src/detection.py`](src/detection.py:22) — `DetectionService`, YOLO + ByteTrack based detector.
- [`src/ptz_controller.py`](src/ptz_controller.py:32) — `PTZService`, ONVIF PTZ control.
- [`src/ptz_simulator.py`](src/ptz_simulator.py:15) — `SimulatedPTZService`, drop-in PTZ simulation.
- [`src/tracking/state.py`](src/tracking/state.py:12) — `TrackingPhase`, `TrackerStatus` state machine.
- [`src/tracking/selector.py`](src/tracking/selector.py:10) — ID parsing and selection utilities.
- [`src/tracking/__init__.py`](src/tracking/__init__.py:1) — tracking public API re-exports.
- [`src/settings.py`](src/settings.py:123) — typed `Settings` dataclasses and `load_settings`.
- [`config.yaml`](config.yaml:1) — user-editable configuration loaded into `Settings`.

## High-Level Data Flow

```mermaid
flowchart LR
    subgraph Config
        Y[config.yaml]
        S[Settings (load_settings)]
    end

    subgraph PTZ
        PZ[PTZService]
        PS[SimulatedPTZService]
    end

    subgraph Tracking
        TS[TrackerStatus]
        TP[TrackingPhase]
        SEL[selector.py]
    end

    subgraph Detection
        DM[DetectionManager]
        DS[DetectionService (YOLO)]
        TD[ThermalDetectionService]
    end

    subgraph Runtime
        DM --> DS
        DM --> TD
        LOOP[main loop / session]
    end

    Y --> S
    S --> DM
    DM --> FG1[Visible Graber]
    DM --> FG2[Thermal Grabber]
    FG1 --> DS
    FG2 --> TD
    S --> PZ
    S --> PS

    FG --> LOOP
    LOOP --> DS
    LOOP --> TS
    LOOP --> SEL

    LOOP --> PZ
    LOOP --> PS

    DS --> LOOP
    TD --> LOOP
    TS --> LOOP
    SEL --> LOOP

    LOOP --> OV
```

At runtime, `main()` loads `Settings`, selects either `PTZService` or `SimulatedPTZService`,
starts a `frame_grabber` thread feeding a frame queue, runs YOLO+ByteTrack detection on
each frame, updates the tracking state machine, applies PTZ commands based on the
selected target and coverage, and renders overlays.

## Configuration System

Configuration is based on `config.yaml` plus a strongly-typed `Settings` model.

- [`src/settings.py`](src/settings.py:123) defines:

  - `LoggingSettings` — log file, level, format, rotation, retention, file output
    toggles.
  - `CameraSettings` — `camera_index`, `resolution_width`, `resolution_height`, `fps`.
  - `CameraCredentials` — `ip`, `user`, `password` for ONVIF camera.
  - `DetectionSettings` — `confidence_threshold`, `model_path`, `target_labels`,
    `camera_credentials`.
  - `PTZSettings` — PTZ control parameters (see below).
  - `PerformanceSettings` — tuning values (FPS window, zoom dead zone,
    frame queue size).
  - `SimulatorSettings` — all PTZ simulation toggles/parameters.
  - `Settings` — top-level aggregate of all sections.

- `load_settings()`:
  - Reads `config.yaml`.
  - Populates each section with defaults if values are missing.
  - Validates critical fields and raises `SettingsValidationError` on invalid
    configuration.
  - Ensures behavior compatible with legacy configuration while providing typed access.

`main()` uses `load_settings()` as the single source of truth for:
- PTZ gains and thresholds
- camera and video source selection
- detection thresholds and model path
- simulator enablement and behavior
- performance tunables

## Main Orchestrator (`src/main.py`)

Key responsibilities:

- Load configuration:
  - `settings = load_settings()` [`src/main.py`](src/main.py:505)
- Construct PTZ backend:
  - If `settings.simulator.use_ptz_simulation`:
    - Use `SimulatedPTZService` [`src/ptz_simulator.py`](src/ptz_simulator.py:15)
  - Else:
    - Use real `PTZService` [`src/ptz_controller.py`](src/ptz_controller.py:32)
- Initialize `DetectionManager`:
  - `DetectionManager(settings=settings)` [`src/detection_manager.py`](src/detection_manager.py)
  - Orchestrates concurrent visible and thermal pipelines.
- Start pipelines:
  - `detection_manager.start()` starts separate frame grabbers (OpenCV or WebRTC).
- Initialize PID servo:
  - `ptz_servo = PTZServo(pid_gains)` [`src/ptz_servo.py`](src/ptz_servo.py:30)
- Run main loop:
  - Consumer of `frame_queue`.
  - Applies PTZ simulation viewport if enabled (`simulate_ptz_view`).
  - Runs `DetectionService.detect(frame)`.
  - Computes FPS/processing time.
  - Applies ID-based target selection and tracking phase logic.
  - Manages PID state (resetting on target loss or re-acquisition).
  - Drives PTZ commands (real or simulated) based on target position and coverage.
  - Renders overlays (detections, PTZ status, system info, ID input).

### Frame Queue Architecture

- `frame_grabber`:
  - Runs in a daemon thread.
  - Reads from camera or video file, respecting FPS for recorded sources.
  - Uses a bounded `queue.Queue` to hold only the latest frame (dropping older frames
    to avoid lag).
- Main loop:
  - Blocks briefly on `frame_queue.get(timeout=1)`.
  - Exits gracefully if frames stop arriving.
- Pattern:
  - Classic producer/consumer with a single-frame queue for low latency.

## Detection Service (`src/detection.py`)

`DetectionService` encapsulates YOLO detection with integrated tracking:

- Loads YOLO model via `ultralytics.YOLO` using
  `settings.detection.model_path` [`src/detection.py`](src/detection.py:45).
- Uses typed `Settings` for:
  - `confidence_threshold`
  - model path
  - (credentials are stored but PTZ uses them directly)
- `detect(frame)`:
  - Validates input frame.
  - Runs `self.model.track(...)` with:
    - `tracker="bytetrack.yaml"` (ByteTrack-based multi-object tracking)
    - `conf=settings.detection.confidence_threshold`
  - Returns `results.boxes` or `[]` on failure.

Architecture implications:

- Tracking IDs used by the tracking subsystem are provided by ByteTrack, not BoTSORT.
- Detection is a pure service; it depends on `Settings` and is driven by `main()`.

## Thermal Detection Service (`src/thermal_detection.py`)

`ThermalDetectionService` provides IR/thermal-based detection as an alternative to YOLO:

- Uses similar interface to `DetectionService` for drop-in replacement.
- [`src/thermal_detection.py`](src/thermal_detection.py:138)

Key components:

- **ThermalDetectionMethod**: Enum of detection approaches:
  - `CONTOUR` — contour analysis with image moments for precise centroids (default)
  - `BLOB` — SimpleBlobDetector with size/shape filtering
  - `HOTSPOT` — classic IR seeker, tracks brightest pixel

- **ThermalTarget**: Dataclass representing detected thermal signatures:
  - `centroid`: (x, y) center position in pixels
  - `area`: detected region area
  - `bbox`: bounding box (x, y, w, h)
  - `intensity`: average region intensity (0-255)
  - `track_id`: assigned ID for tracking compatibility

- **KalmanCentroidTracker**: Kalman filter for smooth centroid tracking
  - Constant velocity model for prediction
  - Handles brief occlusions by continuing prediction

Detection pipeline:

1. **CLAHE Preprocessing**: Enhances local contrast in thermal image
2. **Gaussian Blur**: Reduces sensor noise
3. **Thresholding**: Binary mask creation (Otsu's or fixed)
4. **Morphological Operations**: Cleans up noise in binary mask
5. **Detection Method**: Contour/blob/hotspot analysis
6. **Kalman Filtering**: Optional smoothing for centroid output

Configuration (`settings.thermal`):

- `enabled`: Toggle between YOLO and thermal detection
- `detection_method`: Detection algorithm selection
- `camera`: Separate `ThermalCameraSettings` for thermal camera input

## Tracking Subsystem (`src/tracking/`)

The tracking subsystem provides ID-based target selection and a simple
tracking state machine.

### TrackingPhase (`src/tracking/state.py`)

Enum of logical tracking states:

- `IDLE` — no target locked.
- `SEARCHING` — target temporarily missing but within grace window.
- `TRACKING` — actively tracking the locked ID.
- `LOST` — target not seen beyond grace window.

### TrackerStatus (`src/tracking/state.py`)

Dataclass managing state and transitions:

- Fields:
  - `phase: TrackingPhase`
  - `target_id: int | None`
  - `last_seen_ts: float`
  - `loss_grace_s: float` (e.g. 2.0s)
- Core behavior:
  - `set_target(target_id)`:
    - Sets/clears the lock.
    - Resets timestamps and moves to `IDLE` when cleared.
  - `clear_target()`:
    - Clears target and sets `phase = IDLE`.
  - `mark_seen()` / `mark_missing()`:
    - Update timestamps when detections are observed or missed.
  - `compute_phase(found: bool)`:
    - If no `target_id`: `IDLE`.
    - If `found` is True: `TRACKING` and refresh `last_seen_ts`.
    - If `found` is False and within `loss_grace_s`: `SEARCHING`.
    - If `found` is False and beyond `loss_grace_s`: `LOST`.

The main loop uses `TrackerStatus` on each frame to determine how PTZ should behave
and what to display in overlays.

### Selector Utilities (`src/tracking/selector.py`)

- `parse_track_id(det)`:
  - Normalizes YOLO/ByteTrack detection IDs (tensors, ints, attributes) to `int | None`.
- `select_by_id(tracked_boxes, target_id)`:
  - Returns the detection (if any) with the given ID.
  - No label-based filtering; purely ID-based.
- `get_available_ids(tracked_boxes)`:
  - Returns sorted unique IDs available in current detections.

These utilities are used by `main()` to:

- Support ID-locked tracking: when a user selects an ID, only that ID is tracked.
- Drive the tracking state machine based on whether the locked ID is found.

### ID-Based Target Selection and Keyboard Input

`main()` implements an ID entry mode:

- User toggles input mode and types numeric IDs (implementation in `main.py`).
- Entered ID is applied to `TrackerStatus.set_target(...)`.
- While `TrackingPhase.TRACKING`, overlays highlight the locked ID and PTZ logic
  uses only that target for centering and zoom decisions.

## PTZ Service (`src/ptz_controller.py`)

`PTZService` provides ONVIF-based PTZ control for real cameras.

### Implementation Notes

- Configuration:
  - Uses `settings.detection.camera_credentials` and `settings.ptz` values.
- Discovery & Connection:
  - Establish connection to ONVIF camera using `CameraCredentials` from `Settings`.
  - **Robust WSDL Discovery**: Implements automatic discovery of ONVIF WSDL files, searching both the `onvif` package internal directory and the parent `site-packages` directory to handle variations in library installation paths.
  - Maintain PTZ ranges (`xmin/xmax`, `ymin/ymax`, `zmin/zmax`).

## PTZ Simulator (`src/ptz_simulator.py`)

`SimulatedPTZService` is a drop-in stand-in for `PTZService` used when
`settings.simulator.use_ptz_simulation` is enabled.

Capabilities:

- Same public API surface as `PTZService` for:
  - `continuous_move`
  - `stop`
  - `set_zoom_absolute`
  - `set_zoom_relative`
  - `set_zoom_home`
- Maintains:
  - Normalized pan/tilt ranges `[-1, 1]`.
  - Zoom range `[0, 1]`.
  - `pan_pos`, `tilt_pos`, `zoom_level` representing current absolute pose.
- Motion model:
  - Uses `ramp_rate` from `settings.ptz` plus internal acceleration and rate limits.
  - Integrates velocities over time (`dt`) with clamping and `max_dt` to avoid jumps.
  - Produces smooth, realistic PTZ motion independent of frame rate.
- Integration with `main.py`:
  - When enabled and `sim_viewport` is true, `simulate_ptz_view` in `main.py`
    crops the original frame based on `pan_pos`, `tilt_pos`, `zoom_level`, then
    resizes to configured resolution.
  - Optional `sim_draw_original_viewport_box` draws the simulated viewport on the
    original frame for visualization.

This provides a realistic virtual PTZ pipeline without requiring physical hardware.

## Settings-Driven PTZ Control

The PTZ behavior is configured via `PTZSettings` and related sections, not `config.py`.

Key fields (names as in `Settings.ptz`):

- `ptz_movement_gain`: Proportional gain used by main loop to compute pan/tilt
  command magnitudes.
- `ptz_movement_threshold`: Minimum normalized error required before PTZ commands
  are issued.
- `zoom_target_coverage`: Desired fraction of the frame that the target should occupy.
- `zoom_reset_timeout`: Time after losing target before zoom is reset.
- `zoom_min_interval`: Minimum time between zoom adjustments.
- `zoom_velocity_gain`: Gain used to scale zoom velocity (used by main loop).
- `zoom_reset_velocity`: Velocity applied when resetting zoom to home.
- `ptz_ramp_rate`: Maximum per-command change for smooth ramping (used by both
  real and simulated PTZ).
- `no_detection_home_timeout`: Time without detections before returning to home.

Additional relevant sections:

- `PerformanceSettings`:
  - `fps_window_size` for FPS smoothing.
  - `zoom_dead_zone` to avoid zoom oscillations.
  - `frame_queue_maxsize` (typically 1) for latest-frame processing.
- `SimulatorSettings`:
  - `use_ptz_simulation`, `video_source`, `video_loop`, `sim_viewport`,
    `sim_zoom_min_scale`, `sim_draw_original_viewport_box`, etc.

## Logging and Persistence

Logging is controlled by `LoggingSettings`:

- Log files and rotation/retention.
- Console/file toggles via `write_log_file` and `reset_log_on_start`.
- Structured, high-detail format for debugging system behavior.

Logs capture:

- PTZ connection and command behavior.
- Detection and tracking summaries.
- Simulator state for debugging viewport and motion behavior.

## External Interfaces

Current implementation exposes:

- ONVIF protocol usage internally via `PTZService` for real cameras.

It does NOT expose:

- An HTTP API.
- A separate PresetManager component.


## Distribution & Security

To safely and easily raise the reverse-engineering cost, the application can be compiled into a standalone executable using `PyInstaller`. This packages the Python interpreter and bytecode into a single binary, making it significantly harder to inspect than source scripts.

### Build Process

Run the build task via Pixi:

```bash
pixi run build
```

This executes `pyinstaller` with the following configuration:
- `--onefile`: Packages everything into a single binary.
- `--name DronePTZ`: Names the executable `DronePTZ`.
- `--add-data 'src:src'`: Includes source modules required for dynamic loading if any.

### Deployment Structure

The built executables have **tracker configurations and WSDL files bundled internally**, so they only need the following external assets in the same directory:

```txt
release_dir/
├── DronePTZ            # The compiled main application executable
├── DronePTZ-API        # The compiled API server executable (optional)
├── config.yaml         # Configuration file (must match sys.executable location)
└── assets/             # Assets folder containing models and videos
    ├── models/
    │   └── yolo/       # YOLO model files (.pt or .onnx)
    └── videos/         # Test videos for simulation mode
```

**Note**: The `config/trackers/` directory is **bundled inside the executables** and does not need to be distributed separately.

### Security Notes

- **Binary Compilation**: Compiling to a binary strips docstrings and comments and requires a decompiler to recover logic, raising the barrier for casual reverse engineering.
- **Obfuscation**: For higher security, `PyArmor` can be used to obfuscate the scripts before compilation. The `src_obfuscated/` directory in the repository assumes a PyArmor workflow if required.

## Model Management API

The Model Management API enables dynamic lifecycle management of YOLO models:

- **Storage**: Models reside in `assets/models/yolo/`.
- **Discovery**: `GET /models` scans the directory for `.pt` and `.onnx` files.
- **Activation**: `POST /models/{name}/activate` updates the `DetectionSettings.model_path` in the `SettingsManager`.
- **Safety**: 
  - Prevents deletion of the currently active model.
  - Validates file extensions on upload (.pt, .onnx).
  - Enforces 200MB size limit.
  - Basic path traversal protection.
