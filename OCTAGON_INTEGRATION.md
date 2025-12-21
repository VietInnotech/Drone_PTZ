# Octagon API Integration for Position Tracking

## Summary

Updated the PTZ tracking system to use **Octagon HTTP API** for reading/syncing position status, while maintaining **ONVIF** for sending PTZ movement commands. This hybrid approach leverages the strengths of both protocols.

## Why This Was Needed

The logs showed camera position always reporting `pan=0.000, tilt=0.000, zoom=0.000` despite sending ONVIF `ContinuousMove` commands. The Octagon camera platform requires using its HTTP REST API endpoints to reliably read device position.

## Architecture

### ONVIF (Command Interface)

- **Purpose**: Send PTZ movement commands
- **Methods Used**:
  - `ContinuousMove()` - Velocity-based continuous pan/tilt/zoom
  - `Stop()` - Stop movement
  - `AbsoluteMove()` - Absolute positioning
  - `GotoHomePosition()` - Home position movement
  - `SetZoomAbsolute()` / `SetZoomRelative()` - Zoom control

### Octagon API (Status/Position Interface)

- **Purpose**: Read current camera position
- **Endpoint**: `GET http://<camera-ip>/api/devices/pantilt/position`
- **Authentication**: Basic auth (same credentials as ONVIF)
- **Response Format**:
  ```json
  {
    "success": true,
    "data": {
      "panPosition": 0.5,
      "tiltPosition": 0.3,
      "zoom": 0.8
    }
  }
  ```

## Code Changes

### 1. [src/ptz_controller.py](src/ptz_controller.py)

#### New Imports

```python
import requests  # For Octagon HTTP API calls
```

#### New Attributes (in `__init__`)

```python
# Store credentials for Octagon API access
self.octagon_ip = ip
self.octagon_user = user
self.octagon_pass = password
```

#### New Methods

**`get_position_from_octagon()` → `tuple[float, float, float] | None`**

- Queries Octagon API endpoint `/api/devices/pantilt/position`
- Returns (pan, tilt, zoom) or None if unavailable
- Handles HTTP errors gracefully
- 2-second timeout to prevent blocking

**`update_position_from_octagon()` → `bool`**

- Calls `get_position_from_octagon()` and updates internal state:
  - `self.last_pan`
  - `self.last_tilt`
  - `self.last_zoom`
  - `self.zoom_level`
- Returns True if successful, False otherwise
- Should be called periodically to sync position state

### 2. [src/main.py](src/main.py)

#### Position Sync Loop (Line ~658)

```python
# Periodically sync position from Octagon API (every 10 frames)
if frame_index % 10 == 0 and hasattr(ptz, "update_position_from_octagon"):
    ptz.update_position_from_octagon()
```

**Behavior**:

- Syncs position every 10 frames (reduces API load)
- Gracefully handles missing method (backward compatible)
- Updates internal tracking state from actual device position

#### Position Logging (Lines ~663-668)

```python
pan_pos = getattr(ptz, "pan_pos", getattr(ptz, "last_pan", 0.0))
tilt_pos = getattr(ptz, "tilt_pos", getattr(ptz, "last_tilt", 0.0))
zoom_val = getattr(ptz, "zoom_level", getattr(ptz, "last_zoom", 0.0))
logger.debug(f"Frame {frame_index}: detections={len(tracked_boxes)}, "
             f"zoom={zoom_val:.3f}, pan={pan_pos:.3f}, tilt={tilt_pos:.3f}")
```

**Improvement**: Now uses `last_pan/last_tilt/last_zoom` (updated from Octagon API) as fallback

### 3. [pixi.toml](pixi.toml)

Added dependency:

```toml
[pypi-dependencies]
requests = ">=2.31.0, <3"
```

## Expected Behavior

### Before Integration

```
Frame 2000: detections=2, zoom=0.000, pan=0.000, tilt=0.000  ← Always zero!
ContinuousMove command sent: pan=0.12, tilt=0.12, zoom=-0.29
Target tracked but position never updated
```

### After Integration

```
Frame 2000: detections=2, zoom=0.150, pan=0.045, tilt=0.089  ← Actual position!
ContinuousMove command sent: pan=0.12, tilt=0.12, zoom=-0.29
Octagon position synced (every 10 frames)
Position gradually updates as camera moves
```

## Sync Frequency

Position is synced **every 10 frames** because:

- Reduces API calls (from ~30/sec to ~3/sec at 30 FPS)
- Still provides responsive position feedback
- Prevents bottlenecking on HTTP requests

To change sync frequency, modify in `src/main.py`:

```python
if frame_index % 10 == 0:  # Change 10 to desired frame interval
    ptz.update_position_from_octagon()
```

## Error Handling

- **HTTP Request Fails**: Logs at DEBUG level, silently continues (doesn't break tracking)
- **API Response Invalid**: Parses gracefully, returns None
- **Network Timeout**: 2-second timeout prevents hanging
- **Missing Method**: Hasattr check in main loop prevents crashes on legacy PTZService

## Dependencies

- `requests>=2.31.0` - Added to pixi.toml
- Existing: `onvif-zeep`, `loguru`, `opencv`, etc.

## Installation

```bash
pixi install  # Installs requests and all dependencies
```

## Testing

To verify the integration is working:

```bash
# Run the application
pixi run main

# Check logs for:
# 1. "Octagon position: pan=X.XXX, tilt=Y.YYY, zoom=Z.ZZZ" - Position updates
# 2. Frame logging should show non-zero pan/tilt/zoom values
# 3. No "Octagon API position request error" messages
```

## Troubleshooting

### Position Still Shows Zero

- Verify camera IP is correct: `config.yaml` → `camera_credentials.ip`
- Check credentials: `camera_credentials.user` and `camera_credentials.pass`
- Test API manually:
  ```bash
  curl -u admin:!Inf2019 http://192.168.1.123/api/devices/pantilt/position
  ```

### Frequent "Octagon API position request error"

- Check network connectivity to camera
- Verify Octagon API is running on camera (not just ONVIF)
- Check API response format matches expected schema

### High Latency in Tracking

- Reduce sync frequency if getting timeouts
- Check camera network bandwidth
- Ensure API calls aren't blocking main loop (they shouldn't be)

## Future Improvements

1. **Reduce API Calls**: Use WebSocket or persistent HTTP/2 connection
2. **Position Prediction**: Estimate position between API calls based on last command
3. **Confidence Weighting**: Compare ONVIF vs Octagon positions to detect discrepancies
4. **Caching**: Short-term cache to avoid duplicate API calls within same frame batch
