# Gap Analysis

## Resolved Issues

| ID | Issue Description | Root Cause | Resolution | Test Case |
|---|---|---|---|---|
| BUG-001 | PTZService initialization fails with `TypeError: expected str, bytes or os.PathLike object, not NoneType` | `onvif_zeep` package missing `wsdl` directory in its internal folder, and defaulting logic in `onvif_zeep/client.py` uses `os.path.join` with a potentially mismatched path. | Implemented robust WSDL discovery in `PTZService.__init__` that checks both internal package path and `site-packages` root. | Verified by successful connection to real camera in `main.py`. |
| ENH-001 | Tracking instability at high zoom | Pan/Tilt speeds were too high at high zoom levels, causing oscillations and loss of target. | Implemented **Zoom-Compensated Speed Control** which scales PTZ gains inversely to the magnification level. | Verified by smoother tracking in simulator and real camera at various zoom levels. |
| ENH-002 | Potential axis direction mismatch | Different camera models/mounting positions may have inverted axes. | Added `invert_pan` and `invert_tilt` configuration options. | Verified by flipping axes in `config.yaml` and observing inverted behavior. |
| BUG-002 | Erratic PTZ ramping when syncing positions | Position sync was overwriting `last_pan/tilt` velocity variables, causing the ramp function to jump to high values. | Separated velocity state (`last_vel_pan/tilt`) from absolute position state (`abs_pan/tilt`). | Verified by steady ramp-up behavior regardless of background position syncing. |

## Missing Features / Known Issues

### Camera Selection and Detection Mode (Updated 2026-01-31)

| ID | Issue Description | Status | Resolution |
|---|---|---|---|
| GAP-001 | No runtime camera switching API - requires restart | **Resolved** | Added `reload_services()` to `ThreadedAnalyticsSession` |
| GAP-002 | Detection mode toggle (thermal/YOLO) requires restart | **Resolved** | Added `POST /settings/reload-session` endpoint |
| GAP-003 | Camera selection not synced between SkyShield and Drone_PTZ | **Resolved** | Added "Apply & Reload Session" button in SkyShield |
| GAP-004 | No validation for MediaMTX stream availability | **Resolved** | Added `stream_validator.py` with proactive validation |
| GAP-005 | Thermal camera source type not exposed in SkyShield UI | **Resolved** | Added `thermal.camera.source` dropdown |
| GAP-006 | Missing thermal settings API tests | **Resolved** | `test_thermal_settings_api.py` - 11 tests |

### Pre-existing PTZ Controller Test Failures (27 tests)

These failures exist in `test_ptz_controller.py` and are unrelated to camera selection or detection mode. They appear to be mock/fixture configuration issues that need separate investigation.
