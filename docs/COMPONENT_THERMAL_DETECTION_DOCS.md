# Thermal Detection Component Documentation

## Overview

The thermal detection component provides IR/thermal-based object detection as an alternative to YOLO-based detection. It uses contrast-based methods similar to IR missile seekers for tracking heat-emitting targets.

## Location

- **Main module**: `src/thermal_detection.py`
- **Settings**: `src/settings.py` (`ThermalSettings`, `ThermalCameraSettings`)
- **Configuration**: `config.yaml` (thermal section)
- **Tests**: `tests/unit/test_thermal_detection.py`

## Classes

### ThermalDetectionService

Main detection service class. Creates thermal detection pipeline with configurable methods.

**Constructor**: `ThermalDetectionService(settings: Settings | None = None)`

**Key methods**:
- `detect(frame: np.ndarray) -> list[ThermalTarget]`: Detect targets in frame
- `get_primary_target(targets: list) -> ThermalTarget | None`: Get largest target
- `set_method(method: str)`: Change detection method at runtime
- `get_class_names() -> dict[int, str]`: Interface compatibility (returns `{0: "thermal_target"}`)

### ThermalDetectionMethod (Enum)

Available detection algorithms:
- `CONTOUR`: Image moments for precise centroids (default, recommended)
- `BLOB`: SimpleBlobDetector with filtering
- `HOTSPOT`: Track brightest pixel (classic IR seeker)

### ThermalTarget (Dataclass)

Detection result structure:
- `centroid`: `tuple[float, float]` - (x, y) center position
- `area`: `float` - Region area in pixels
- `bbox`: `tuple[int, int, int, int]` - (x, y, w, h) bounding box
- `intensity`: `float` - Average intensity (0-255)
- `track_id`: `int | None` - Assigned track ID

### KalmanCentroidTracker

Kalman filter for smooth centroid tracking.

**Methods**:
- `predict() -> tuple[float, float]`: Predict next position
- `correct(measurement) -> tuple[float, float]`: Update with measurement
- `reset()`: Reset filter state

## Configuration

### ThermalSettings

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | False | Toggle thermal detection mode |
| `detection_method` | str | "contour" | Method: contour, blob, hotspot |
| `threshold_value` | int | 200 | Fixed threshold (0-255) |
| `use_otsu` | bool | True | Use Otsu's auto-threshold |
| `clahe_clip_limit` | float | 2.0 | CLAHE contrast limit |
| `clahe_tile_size` | int | 8 | CLAHE tile grid size |
| `min_area` | int | 100 | Minimum blob area |
| `max_area` | int | 50000 | Maximum blob area |
| `blur_size` | int | 5 | Gaussian blur kernel |
| `use_kalman` | bool | True | Enable Kalman smoothing |
| `camera` | ThermalCameraSettings | - | Thermal camera input |

### ThermalCameraSettings

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `source` | str | "camera" | Input: camera, rtsp, video, webrtc |
| `webrtc_url` | str | None | WebRTC URL for thermal stream |
| `camera_index` | int | 0 | Camera device index |
| `rtsp_url` | str | None | RTSP URL for network camera |
| `resolution_width` | int | 640 | Frame width |
| `resolution_height` | int | 480 | Frame height |
| `fps` | int | 30 | Frame rate |

## Detection Pipeline

```
Frame → Grayscale → Blur → CLAHE → Threshold → Morphology → Contours → Centroids → Kalman
```

1. **Grayscale conversion**: BGR to grayscale if needed
2. **Gaussian blur**: Noise reduction
3. **CLAHE**: Local contrast enhancement
4. **Thresholding**: Binary mask (Otsu or fixed)
5. **Morphological ops**: Open (remove noise), Close (fill gaps)
6. **Contour/blob/hotspot**: Method-specific detection
7. **Kalman filtering**: Optional centroid smoothing

## Usage

```python
from src.settings import load_settings
from src.thermal_detection import ThermalDetectionService

settings = load_settings()
thermal = ThermalDetectionService(settings)

# Detect targets
targets = thermal.detect(frame)

# Get primary target
primary = thermal.get_primary_target(targets)
if primary:
    cx, cy = primary.centroid
    print(f"Target at ({cx:.1f}, {cy:.1f})")
```

## Dependencies

- OpenCV (`cv2`): CLAHE, thresholding, contours, Kalman filter
- NumPy: Array operations
- Loguru: Logging
