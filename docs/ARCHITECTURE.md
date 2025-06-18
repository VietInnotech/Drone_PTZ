# PTZ AI Control System Architecture

## Components

1. Main Controller
2. PTZ Controller
3. Object Detector
4. Configuration Manager

## Persistence

### Log File Handling

- Logs persisted to rotating files
- Configurable retention policy
- Optional file output control via write_log_file
- Log reset on startup via reset_log_on_start flag

## Interfaces

- ONVIF for camera control
- HTTP API for external integration
