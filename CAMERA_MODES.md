# Camera Control Modes

The PTZ tracking system supports **two camera control modes** for maximum compatibility:

1. **ONVIF Mode** - Standard ONVIF cameras (normal cameras)
2. **Octagon Mode** - Infiniti Electro-Optics cameras with Octagon API

## Mode Selection

Set the control mode in [config.yaml](config.yaml):

```yaml
ptz:
  control_mode: onvif # or "octagon"
```

---

## ONVIF Mode (Standard Cameras)

### Overview

Uses pure ONVIF protocol for all PTZ operations. This is the default and works with any ONVIF-compliant PTZ camera.

### When to Use

- Standard PTZ cameras from manufacturers like Axis, Hikvision, Dahua, etc.
- Any camera with ONVIF Profile S or Profile T support
- When you need standard, protocol-compliant operation

### Configuration

```yaml
ptz:
  control_mode: onvif # Enable ONVIF mode

camera:
  credentials_ip: 192.168.1.100 # Camera IP address
  credentials_user: admin # ONVIF username
  credentials_password: "yourpass" # ONVIF password

# No octagon settings needed
```

### How It Works

- **PTZ Commands**: Sent via ONVIF (`ContinuousMove`, `Stop`, `AbsoluteMove`, etc.)
- **Position Reading**: Via ONVIF `GetStatus` (called every 10 frames)
- **Home Position**: Uses ONVIF `GotoHomePosition` with fallbacks
- **Zoom Control**: Via ONVIF absolute/relative zoom commands

### Benefits

- Standard protocol, wide camera support
- No vendor-specific dependencies
- Proven compatibility across manufacturers
- **Now includes position feedback tracking**

### Limitations

- Position feedback may have latency (ONVIF HTTP ov
- Position accuracy depends on camera's ONVIF implementation qualityerhead)
- Some cameras have slow `GetStatus` response times

---

## Octagon Mode (Infiniti Cameras)

### Overview

Uses Infiniti's Octagon HTTP API for PTZ control and position tracking. Designed specifically for Infiniti Electro-Optics camera systems.

### When to Use

- Infiniti cameras with Octagon platform
- When you need low-latency position feedback
- When ONVIF position reporting is unreliable

### Configuration

```yaml
ptz:
  control_mode: octagon # Enable Octagon mode
  position_mode: auto # Use Octagon API for position (auto uses control_mode)

camera:
  credentials_ip: 192.168.1.123 # Camera IP for video stream (RTSP)
  credentials_user: admin # Video stream auth
  credentials_password: "!Inf2019" # Video stream auth

octagon:
  ip: 192.168.1.122 # Octagon API IP (may differ from camera IP)
  user: admin # Octagon API username
  password: "!Inf2019" # Octagon API password

octagon_devices:
  pantilt_id: pantilt # Pan/tilt device ID
  visible_id: visible1 # Visible camera device ID (for zoom)
```

### How It Works

- **PTZ Commands**: Sent via Octagon HTTP API
  - Movement: `GET /api/devices/{pantilt_id}?command=move&direction={dir}&panSpeed={pct}&tiltSpeed={pct}`
  - Stop: `GET /api/devices/{pantilt_id}?command=stop`
  - Home: `GET /api/devices/{pantilt_id}?command=home`
- **Position Reading**: Via Octagon REST API
  - Pan/Tilt: `GET /api/devices/{pantilt_id}/position`
  - Zoom: `GET /api/devices/{visible_id}/position`
- **Feedback Loop**: Position synced every 10 frames for accurate tracking

### Benefits

- Low-latency position feedback
- Accurate real-time position tracking
- Optimized for Infiniti systems

### Limitations

- Only works with Infiniti/Octagon cameras
- Requires separate API credentials and endpoints

---

## Implementation Details

### Code Architecture

The [PTZService](src/ptz_controller.py) class handles both modes internally:

```python
# Mode-aware command routing
if self.control_mode == "octagon":
    self._octagon_move(pan, tilt)  # Use Octagon API
else:
    self.ptz.ContinuousMove(...)   # Use ONVIF

# Unified position tracking
def update_position(self) -> bool:
    if self.control_mode == "octagon":
        return self.update_position_from_octagon()
    else:
        return self.update_position_from_onvif()
```

### Position Tracking

Both modes automatically sync camera position:

```yaml
ptz:
  control_mode: onvif # Method for sending PTZ commands
  position_mode: auto # Method for reading position: onvif | octagon | auto
```

**Position Mode Options:**

- `auto` (default): Uses the same method as `control_mode`
- `onvif`: Always use ONVIF `GetStatus` for position reading
- `octagon`: Always use Octagon API for position reading

**Example: Mixed Modes**

You can use ONVIF for commands but Octagon for position reading if ONVIF GetStatus is slow:

```yaml
ptz:
  control_mode: onvif # Send commands via ONVIF
  position_mode: octagon # But read position via Octagon API
```

This ensures the internal tracking state matches the actual camera position, synced every 10 frames.

---

## Switching Between Modes

### From ONVIF to Octagon

1. Change `control_mode` to `octagon`
2. Add `octagon` and `octagon_devices` sections to config
3. Ensure Octagon API is accessible
4. Restart the application

### From Octagon to ONVIF

1. Change `control_mode` to `onvif`
2. Verify camera supports ONVIF
3. Update camera credentials if needed
4. Restart the application

---

## Troubleshooting

### ONVIF Mode Issues

- **Connection timeout**: Verify camera IP with `ping`, ensure ONVIF is enabled
- **No media profiles**: Camera may not support ONVIF Profile S
- **Slow response**: Some cameras have high ONVIF latency (inherent limitation)
- **Position always zero**: Check ONVIF implementation quality on camera

### Octagon Mode Issues

- **Connection refused**: Verify `octagon.ip` is correct and API is accessible
- **401 Unauthorized**: Check `octagon.user` and `octagon.password`
- **Position not updating**: Verify `octagon_devices` IDs match your system
- **Movement not working**: Check device IDs and network connectivity

### Verification Commands

```bash
# Test ONVIF connectivity (requires onvif-zeep)
pixi shell
python -c "from onvif import ONVIFCamera; c = ONVIFCamera('192.168.1.100', 80, 'admin', 'pass'); print(c.create_media_service().GetProfiles())"

# Test Octagon API connectivity
curl -u admin:password http://192.168.1.122/api/devices/pantilt/position
```

---

## Best Practices

1. **Choose the right mode for your hardware**

   - ONVIF for standard cameras
   - Octagon for Infiniti systems

2. **Keep credentials secure**

   - Use environment variables for production
   - Don't commit passwords to version control

3. **Verify connectivity before deployment**

   - Test camera/API access from the server
   - Ensure network paths are stable

4. **Monitor logs during startup**

   - Check for connection errors
   - Verify mode selection is correct

5. **Tune PID parameters per mode**
   - ONVIF may need different gains due to latency
   - Octagon can use more aggressive tuning

---

## Related Documentation

- [OCTAGON_INTEGRATION.md](OCTAGON_INTEGRATION.md) - Detailed Octagon implementation
- [api_guide.md](api_guide.md) - Full Octagon API reference
- [README.md](README.md) - General system overview
- [src/ptz_controller.py](src/ptz_controller.py) - PTZService implementation
