# RTSP Camera Configuration Guide

## Quick Start

### Option 1: USB Camera (Default)

```yaml
camera:
  camera_index: 0
  rtsp_url: null # Leave as null to use USB camera
```

### Option 2: RTSP Stream

```yaml
camera:
  rtsp_url: "rtsp://admin:password@192.168.1.70:554/stream1"
```

### Option 3: Video File (Fallback)

```yaml
camera:
  video_source: "path/to/video.mp4"
  rtsp_url: null
```

## Priority Order

The system tries cameras in this order:

1. **RTSP URL** - Enterprise IP cameras via RTSP protocol
2. **Video file** - Local video file for testing/replay
3. **USB camera** - Default webcam/USB device

## Common RTSP URL Formats

### Hikvision Cameras

```
rtsp://admin:password@192.168.1.70:554/stream1
```

### Dahua Cameras

```
rtsp://admin:password@192.168.1.70:554/stream/main
```

### Reolink Cameras

```
rtsp://admin:password@192.168.1.70:554/h264Preview_01_main
```

### Generic Format

```
rtsp://[username]:[password]@[ip]:[port]/[stream]
```

## Troubleshooting

### "RTSP stream failed to open"

- ✓ Check network connectivity: `ping 192.168.1.70`
- ✓ Verify credentials are correct
- ✓ Check port number (usually 554)
- ✓ Verify firewall allows RTSP traffic

### "Connection timeout"

- ✓ Increase read timeout in OpenCV
- ✓ Reduce stream resolution/bitrate on camera
- ✓ Check network bandwidth

### "Stream hangs intermittently"

- ✓ Enable buffer on the camera side
- ✓ Reduce frame rate expectations
- ✓ Check camera logs for disconnects

## Advanced OpenCV Settings

For custom RTSP handling, modify frame_grabber() in src/main.py:

```python
if rtsp_url:
    cap = cv2.VideoCapture(rtsp_url)

    # Optional: Set buffer size for network streams
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    # Optional: Set frame rate
    cap.set(cv2.CAP_PROP_FPS, 30)

    # Optional: Read timeout (ms)
    cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
```

## Testing RTSP Connection

```bash
# Test with ffplay (if available)
ffplay -rtsp_transport tcp rtsp://admin:password@192.168.1.70:554/stream1

# Test with OpenCV Python
python -c "
import cv2
cap = cv2.VideoCapture('rtsp://admin:password@192.168.1.70:554/stream1')
ret, frame = cap.read()
print('Connection OK' if ret else 'Connection Failed')
cap.release()
"
```

## Performance Notes

- **RTSP streams** have ~500ms-1s latency
- **USB cameras** have <100ms latency
- **Network bandwidth** - Typically 2-10 Mbps depending on resolution
- **CPU usage** - Similar to USB cameras once frame is decoded

## Security Notes

⚠️ **Never commit credentials to version control!**

Options:

1. Use environment variables:

   ```bash
   export CAMERA_RTSP_URL="rtsp://user:pass@ip/stream"
   ```

2. Use separate config files (git-ignored):

   ```yaml
   # .gitignore
   config.secrets.yaml
   ```

3. Use system credentials store (recommended for production)

---

## Full Example Configuration

```yaml
camera:
  camera_index: 0 # Ignored when rtsp_url is set
  video_source: null
  rtsp_url: "rtsp://admin:password@192.168.1.70:554/stream1"
  resolution_width: 1280
  resolution_height: 720
  fps: 30

detection:
  model_path: "assets/models/yolo/roboflowaccurate.pt"
  confidence_threshold: 0.3

ptz:
  # PTZ controller settings...
```

---

For more information, see [CHANGES_SUMMARY.md](CHANGES_SUMMARY.md)
