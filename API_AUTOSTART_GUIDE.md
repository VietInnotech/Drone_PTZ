# API Auto-Start Implementation

## Summary

Modified the API server to **automatically establish WebRTC/ONVIF connections on startup**, eliminating the need to make an API call to initialize the stream.

## What Changed

### 1. **server.py** — Auto-start Initialization

- Added `--auto-start` flag (enabled by default)
- Passes `auto_start_session=True` to `create_app()`
- Logs startup progress

### 2. **app.py** — Startup Handler

- Registered async `startup_handler()` on `app.on_startup`
- Auto-creates and starts a session before HTTP server accepts requests
- Gracefully handles errors without blocking server startup
- Logs session details (session_id, camera_id)

### 3. **pixi.toml** — Task Updates

- `pixi run api` — Now includes `--auto-start` by default
- `pixi run api-no-autostart` — New task for manual session control (if needed)

## Behavior

### Before

```
1. User: pixi run api
2. Server starts (no connection)
3. User: POST /ws/sessions/create
4. Connection initialized → frames start flowing
```

### After

```
1. User: pixi run api
2. Server starts + auto-initializes connection
3. Frames flowing immediately
4. User: GET /ws/sessions/list (session already running)
```

## Usage

### Auto-start (Default)

```bash
pixi run api
# Output:
# INFO: Auto-starting WebRTC/camera connection for camera_id=test
# INFO: Auto-started session: session_id=xyz123, camera_id=test
```

### Without Auto-start

```bash
pixi run api-no-autostart
# Manual session creation still works via API call
```

### Command-line Override

```bash
# Force disable (if pixi.toml has --auto-start)
python -m src.api.server --host 0.0.0.0 --port 8080
# Note: Must not include --auto-start flag to disable
```

## Configuration

The auto-start uses settings from `config.yaml`:

- `camera.source` — webrtc, rtsp, camera, or video
- `camera.webrtc_url` — Stream URL (if source=webrtc)
- `camera.rtsp_url` — RTSP URL (if source=rtsp)
- `ptz_control.control_mode` — onvif or simulated

**No new config keys needed.** All existing settings work as-is.

## Logs to Expect

On successful auto-start:

```
2025-12-23 10:15:30.123 | INFO | src.api.app | startup_handler | Line 90 | Auto-starting WebRTC/camera connection for camera_id=test
2025-12-23 10:15:31.456 | INFO | src.webrtc_client | start_webrtc_client | Line 375 | WebRTC client started connecting to http://localhost:8889/live/test
2025-12-23 10:15:32.789 | INFO | src.api.app | startup_handler | Line 96 | Auto-started session: session_id=sess_abc123, camera_id=test
```

## Benefits

✅ **Simpler workflow** — No extra API calls needed  
✅ **Immediate streaming** — Frames available when server is ready  
✅ **Less confusion** — Server is "ready" when `pixi run api` completes startup  
✅ **Backwards compatible** — Existing API calls still work  
✅ **Graceful fallback** — Errors don't crash server, logged and reported

## Testing

### Quick Test

```bash
pixi run api &
sleep 2
curl http://localhost:8080/healthz
# Should return: {"status": "ok"}

curl http://localhost:8080/cameras
# Should return camera_id from auto-started session

curl http://localhost:8080/sessions
# Should show running session
```

### Verify Connection Status

```bash
curl http://localhost:8080/sessions | jq '.sessions[0].status'
# Look for: "running": true, "tracking_phase": "idle"
```

## Related Files

- [src/api/server.py](src/api/server.py) — Entry point + argument parsing
- [src/api/app.py](src/api/app.py) — aiohttp app + startup handler
- [src/api/session.py](src/api/session.py) — Session management (unchanged)
- [pixi.toml](pixi.toml) — Task definitions

## Troubleshooting

### Server starts but no auto-start message

- Check `config.yaml` — `camera.source` must be set
- Verify `--auto-start` flag is passed (check pixi.toml task definition)
- Check logs for "Auto-starting..." message

### Auto-start fails with error

- Connection errors logged but don't crash server
- Check `camera.webrtc_url` or `rtsp_url` is accessible
- Verify network connectivity to stream source

### Want to disable auto-start temporarily

```bash
pixi run api-no-autostart
```
