# Position Tracking Enhancement

## Summary

Enhanced the PTZ position tracking system to support **both ONVIF and Octagon cameras** with unified position feedback. Previously, position tracking was only implemented for Octagon API cameras.

## Changes Made

### 1. Added ONVIF Position Tracking ([src/ptz_controller.py](src/ptz_controller.py))

#### New Method: `get_position_from_onvif()`

```python
def get_position_from_onvif(self) -> tuple[float, float, float] | None:
    """Get current pan, tilt, and zoom position from ONVIF GetStatus."""
```

- Queries ONVIF camera via `GetStatus` method
- Extracts pan, tilt, and zoom from position data
- Returns tuple of (pan, tilt, zoom) or None if unavailable
- Handles protocol errors gracefully with debug logging

#### New Method: `update_position_from_onvif()`

```python
def update_position_from_onvif(self) -> bool:
    """Update internal position tracking from ONVIF GetStatus."""
```

- Calls `get_position_from_onvif()` to fetch current position
- Updates internal state: `last_pan`, `last_tilt`, `last_zoom`, `zoom_level`
- Returns True if successful, False otherwise
- Called periodically when `control_mode=onvif`

### 2. Unified Position Update Interface

#### New Method: `update_position()`

```python
def update_position(self) -> bool:
    """Update internal position tracking based on control mode."""
    if self.control_mode == "octagon":
        return self.update_position_from_octagon()
    else:
        return self.update_position_from_onvif()
```

- Single interface for position updates regardless of camera type
- Automatically routes to appropriate implementation based on `control_mode`
- Simplifies calling code in main tracking loop

### 3. Updated Main Tracking Loop ([src/main.py](src/main.py#L770))

**Before:**

```python
# Periodically sync position from Octagon API (every 10 frames)
if frame_index % 10 == 0 and hasattr(ptz, "update_position_from_octagon"):
    ptz.update_position_from_octagon()
```

**After:**

```python
# Periodically sync position from camera (every 10 frames)
# Uses ONVIF GetStatus or Octagon API depending on control_mode
if frame_index % 10 == 0 and hasattr(ptz, "update_position"):
    ptz.update_position()
```

### 4. Documentation Updates

#### Created New Documentation

- **[CAMERA_MODES.md](CAMERA_MODES.md)**: Comprehensive guide comparing ONVIF vs Octagon modes
  - Setup instructions for both modes
  - Feature comparison
  - Troubleshooting guide
  - Configuration examples

#### Updated Existing Documentation

- **[README.md](README.md)**: Enhanced quick start with camera mode information
- **[OCTAGON_INTEGRATION.md](OCTAGON_INTEGRATION.md)**: Added ONVIF position methods documentation
- **[CAMERA_MODES.md](CAMERA_MODES.md)**: Position tracking section updated to reflect both modes

## Technical Details

### Position Update Frequency

- Position is synced every 10 frames (not every frame)
- Reduces network/API overhead
- Balances accuracy with performance

### ONVIF Position Extraction

The ONVIF implementation extracts position data from the `GetStatus` response:

- **Pan/Tilt**: From `status.Position.PanTilt.x` and `.y`
- **Zoom**: From `status.Position.Zoom.x` (or direct value)
- Falls back to defaults if any component is unavailable

### Error Handling

Both implementations include robust error handling:

- Graceful degradation if position unavailable
- Debug logging for troubleshooting
- No impact on PTZ command execution if position read fails

## Benefits

### For ONVIF Cameras

- **Now includes position feedback** previously missing
- Enables accurate tracking state monitoring
- Improves closed-loop control accuracy
- Better debugging visibility

### For Octagon Cameras

- **No changes to existing functionality**
- Continues to use optimized Octagon API
- Maintains low-latency position updates

### For Developers

- **Unified interface** (`update_position()`) simplifies code
- **Mode-agnostic** main loop implementation
- **Extensible** design for future camera types
- **Backward compatible** with hasattr check

## Configuration

No configuration changes required! The system automatically uses the correct method based on existing `ptz.control_mode` setting:

```yaml
ptz:
  control_mode: onvif    # Uses ONVIF GetStatus
  # OR
  control_mode: octagon  # Uses Octagon API
```

## Testing

### Validation Steps

1. ✅ Code passes lint/format checks
2. ✅ No syntax errors in modified files
3. ✅ Existing tests remain valid (no test modifications needed)
4. ✅ Backward compatible with existing configurations

### Manual Testing Recommended

For users with ONVIF cameras:

1. Set `control_mode: onvif` in config.yaml
2. Enable debug logging: `log_level: DEBUG`
3. Run system and observe logs for "ONVIF position:" messages
4. Verify position values update correctly

For users with Octagon cameras:

1. No changes needed - existing setup continues to work
2. Can verify with "Octagon position:" debug messages

## Performance Impact

- **Minimal**: Position reads are limited to once per 10 frames
- **ONVIF overhead**: Single HTTP request per update (~10-50ms typical)
- **No blocking**: All position reads use timeouts and error handling
- **Graceful degradation**: Failed reads don't affect PTZ commands

## Migration Guide

### For Existing Users

**No migration needed!** The update is fully backward compatible:

- Existing Octagon configurations work unchanged
- Existing ONVIF configurations gain position tracking automatically
- No config file changes required

### For New Users

Refer to [CAMERA_MODES.md](CAMERA_MODES.md) for:

- Choosing between ONVIF and Octagon modes
- Configuration examples
- Troubleshooting common issues

## Related Files

### Modified

- `src/ptz_controller.py`: Added ONVIF position methods + unified interface
- `src/main.py`: Updated to use unified `update_position()` method
- `OCTAGON_INTEGRATION.md`: Added ONVIF methods documentation
- `README.md`: Enhanced with camera mode information

### Created

- `CAMERA_MODES.md`: New comprehensive camera modes guide
- `POSITION_TRACKING_UPDATE.md`: This document

### Unchanged (No Impact)

- All test files (backward compatible)
- API server code (uses abstract interface)
- Analytics engine (mode-agnostic)
- Settings/configuration structure

## Future Enhancements

Potential areas for future improvement:

1. **Adaptive update frequency**: Adjust based on PTZ activity
2. **Position prediction**: Interpolate between updates
3. **Multi-camera position sync**: Coordinate multiple cameras
4. **WebSocket position streaming**: Real-time position broadcasts via API

## References

- [CAMERA_MODES.md](CAMERA_MODES.md) - Comprehensive camera modes guide
- [OCTAGON_INTEGRATION.md](OCTAGON_INTEGRATION.md) - Octagon API integration details
- [src/ptz_controller.py](src/ptz_controller.py) - PTZService implementation
- [ONVIF Specification](https://www.onvif.org/specs/core/ONVIF-Core-Specification.pdf)
