# Settings Management API Plan

**Date:** December 22, 2025  
**Purpose:** Extend the `pixi run api` server to support runtime settings management

---

## Overview

Currently, the analytics API server (`pixi run api`) provides:
- Session management (`POST /sessions`, `GET /sessions/{id}`, `DELETE /sessions/{id}`)
- WebSocket streaming (`/ws/sessions/{id}`)
- Target selection commands (via WebSocket: `set_target_id`, `clear_target`)

This plan adds **settings management endpoints** to allow:
1. **Reading current settings** from the running application
2. **Updating settings dynamically** without restarting the server
3. **Persisting changes** to `config.yaml` (optional, with safety checks)
4. **Validating settings** before applying them

---

## Current State Analysis

### Settings Architecture

**Settings Module:** [src/settings.py](../src/settings.py)
- Defines typed dataclasses for all configuration sections:
  - `LoggingSettings`
  - `CameraSettings`
  - `DetectionSettings` (includes `CameraCredentials`)
  - `PTZSettings`
  - `SimulatorSettings`
  - `PerformanceSettings`
- `load_settings()` reads from `config.yaml` at project root
- `_validate_settings()` performs comprehensive validation
- Settings are validated on load (raises `SettingsValidationError` with detailed messages)

**Config File:** [config.yaml](../config.yaml)
- Hierarchical YAML structure matching the settings dataclasses
- Includes all runtime parameters: camera source, PTZ gains, detection thresholds, etc.

**API Server:** [src/api/server.py](../src/api/server.py) + [src/api/app.py](../src/api/app.py)
- aiohttp-based REST + WebSocket server
- Currently reads settings once on startup via `load_settings()`
- No hot-reload or settings mutation after initialization

### Key Constraints

1. **Session Lifecycle:** Active sessions hold references to settings; changing settings mid-session requires careful handling
2. **Thread Safety:** Sessions run in background threads; settings updates must be thread-safe
3. **Validation:** All settings changes must pass validation before acceptance
4. **Persistence:** Writing to `config.yaml` must be atomic and safe (no partial writes)
5. **Backwards Compatibility:** Existing API clients must not break

---

## Requirements

### Functional Requirements

**FR1: Read Current Settings**
- `GET /settings` - Return complete current settings as JSON
- `GET /settings/{section}` - Return specific section (e.g., `/settings/ptz`, `/settings/camera`)
- Response format mirrors the Settings dataclass structure

**FR2: Update Settings**
- `PATCH /settings` - Update one or more settings (partial update)
- `PATCH /settings/{section}` - Update specific section only
- Validate all changes before applying
- Return updated settings on success, detailed errors on failure

**FR3: Validate Without Applying**
- `POST /settings/validate` - Dry-run validation of proposed settings
- Returns validation result without modifying runtime state

**FR4: Persist to Disk (Optional)**
- `POST /settings/persist` - Write current runtime settings to `config.yaml`
- Creates backup before overwriting
- Only persists if validation passes

**FR5: Reset to File**
- `POST /settings/reload` - Reload settings from `config.yaml`, discarding runtime changes
- Validates after reload
- Affects new sessions only (existing sessions continue with old settings)

### Non-Functional Requirements

**NFR1: Safety**
- Never apply invalid settings
- Atomic writes for file persistence (no corruption on failure)
- Existing sessions continue with their original settings after changes

**NFR2: Performance**
- Settings reads must not block session threads
- Updates should complete in <100ms for normal cases

**NFR3: Observability**
- Log all settings changes with before/after values
- Emit events for settings changes (trackable via event stream)

**NFR4: Security**
- Do NOT expose passwords in GET responses (redact `camera_credentials.pass`)
- Validate all numeric bounds and file paths
- Rate-limit settings write operations (max 1/second)

---

## Design

### API Endpoints

#### `GET /settings`

**Description:** Retrieve all current runtime settings

**Response (200 OK):**
```json
{
  "logging": {
    "log_file": "logs/app.log",
    "log_level": "DEBUG",
    "log_format": "<green>{time}...",
    "log_rotation": "5 MB",
    "log_retention": "30 days",
    "log_enqueue": true,
    "log_backtrace": true,
    "log_diagnose": true,
    "write_log_file": true,
    "reset_log_on_start": true
  },
  "camera": {
    "camera_index": 4,
    "resolution_width": 1280,
    "resolution_height": 720,
    "fps": 30
  },
  "detection": {
    "confidence_threshold": 0.4,
    "model_path": "assets/models/yolo/best5.pt",
    "target_labels": ["drone", "UAV"],
    "camera_credentials": {
      "ip": "192.168.1.70",
      "user": "admin",
      "password": "***REDACTED***"
    }
  },
  "ptz": {
    "ptz_movement_gain": 0.25,
    "ptz_movement_threshold": 0.025,
    "zoom_target_coverage": 0.1,
    "zoom_reset_timeout": 2.0,
    "zoom_min_interval": 0.1,
    "zoom_velocity_gain": 2.0,
    "zoom_reset_velocity": 0.5,
    "ptz_ramp_rate": 0.1,
    "no_detection_home_timeout": 5
  },
  "performance": {
    "fps_window_size": 30,
    "zoom_dead_zone": 0.03,
    "frame_queue_maxsize": 1
  },
  "simulator": {
    "use_ptz_simulation": false,
    "video_source": "assets/videos/V_DRONE_048.mp4",
    "video_loop": false,
    "sim_viewport": true,
    "sim_pan_step": 0.1,
    "sim_tilt_step": 0.1,
    "sim_zoom_step": 0.1,
    "sim_zoom_min_scale": 0.3,
    "sim_draw_original_viewport_box": true
  }
}
```

**Notes:**
- Passwords are redacted in response
- Returns current **runtime** settings (may differ from `config.yaml` if updated)

---

#### `GET /settings/{section}`

**Description:** Retrieve specific settings section

**Path Parameters:**
- `section`: One of `logging`, `camera`, `detection`, `ptz`, `performance`, `simulator`

**Example:** `GET /settings/ptz`

**Response (200 OK):**
```json
{
  "ptz_movement_gain": 0.25,
  "ptz_movement_threshold": 0.025,
  "zoom_target_coverage": 0.1,
  "zoom_reset_timeout": 2.0,
  "zoom_min_interval": 0.1,
  "zoom_velocity_gain": 2.0,
  "zoom_reset_velocity": 0.5,
  "ptz_ramp_rate": 0.1,
  "no_detection_home_timeout": 5
}
```

**Error (404):**
```json
{
  "error": "Unknown section: invalid_section",
  "valid_sections": ["logging", "camera", "detection", "ptz", "performance", "simulator"]
}
```

---

#### `PATCH /settings`

**Description:** Update settings (partial update supported)

**Request Body:**
```json
{
  "ptz": {
    "ptz_movement_gain": 0.5,
    "zoom_target_coverage": 0.15
  },
  "detection": {
    "confidence_threshold": 0.5
  }
}
```

**Response (200 OK):**
```json
{
  "status": "updated",
  "updated_sections": ["ptz", "detection"],
  "settings": { /* full updated settings */ }
}
```

**Validation Error (400):**
```json
{
  "error": "Validation failed",
  "validation_errors": [
    "confidence_threshold must be between 0.0 and 1.0, got 1.5",
    "ptz_movement_gain must be positive, got -0.2"
  ]
}
```

**Notes:**
- Only provided fields are updated (deep merge)
- Entire settings object is validated after merge
- Changes apply to **new sessions only** (existing sessions unaffected)
- Emits a `settings_updated` event to event stream

---

#### `PATCH /settings/{section}`

**Description:** Update specific section only

**Path Parameters:**
- `section`: Target section name

**Example:** `PATCH /settings/ptz`

**Request Body:**
```json
{
  "ptz_movement_gain": 0.5,
  "zoom_target_coverage": 0.15
}
```

**Response:** Same as `PATCH /settings`

---

#### `POST /settings/validate`

**Description:** Validate proposed settings without applying

**Request Body:** Same as `PATCH /settings`

**Response (200 OK - Valid):**
```json
{
  "valid": true,
  "message": "All settings are valid"
}
```

**Response (200 OK - Invalid):**
```json
{
  "valid": false,
  "validation_errors": [
    "confidence_threshold must be between 0.0 and 1.0, got 1.5"
  ]
}
```

**Notes:**
- Does NOT modify runtime settings
- Useful for frontend validation before submission

---

#### `POST /settings/persist`

**Description:** Write current runtime settings to `config.yaml`

**Request Body (optional):**
```json
{
  "create_backup": true
}
```

**Response (200 OK):**
```json
{
  "status": "persisted",
  "config_path": "config.yaml",
  "backup_path": "config.yaml.backup.20251222_143025"
}
```

**Error (500):**
```json
{
  "error": "Failed to write config file",
  "details": "Permission denied: config.yaml"
}
```

**Notes:**
- Creates timestamped backup by default
- Atomic write (writes to temp file, then renames)
- Validates settings before writing

---

#### `POST /settings/reload`

**Description:** Reload settings from `config.yaml`, discarding runtime changes

**Response (200 OK):**
```json
{
  "status": "reloaded",
  "config_path": "config.yaml",
  "settings": { /* newly loaded settings */ }
}
```

**Error (400):**
```json
{
  "error": "Config file validation failed",
  "validation_errors": [
    "Model file not found: assets/models/yolo/missing.pt"
  ]
}
```

**Notes:**
- Loads and validates before applying
- Existing sessions continue with old settings
- New sessions use reloaded settings

---

### Implementation Architecture

#### 1. Settings Manager (`src/api/settings_manager.py`)

**Purpose:** Thread-safe singleton to hold and manage runtime settings

```python
from __future__ import annotations

import threading
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

from src.settings import Settings, SettingsValidationError, load_settings


class SettingsManager:
    """Thread-safe manager for runtime settings.
    
    Provides atomic read/write access to settings and validation.
    """
    
    def __init__(self, settings: Settings):
        self._lock = threading.RLock()
        self._settings = settings
    
    def get_settings(self) -> Settings:
        """Return a copy of current settings."""
        with self._lock:
            return self._settings
    
    def get_section(self, section: str) -> dict[str, Any]:
        """Return specific section as dict."""
        with self._lock:
            settings_dict = asdict(self._settings)
            if section not in settings_dict:
                raise KeyError(f"Unknown section: {section}")
            return settings_dict[section]
    
    def update_settings(self, updates: dict[str, Any]) -> Settings:
        """Apply partial updates and validate.
        
        Raises SettingsValidationError if invalid.
        Returns new settings on success.
        """
        with self._lock:
            # Deep merge updates into current settings
            new_settings = self._merge_updates(self._settings, updates)
            # Validate will raise if invalid
            from src.settings import _validate_settings
            _validate_settings(new_settings)
            # Apply
            self._settings = new_settings
            return self._settings
    
    def reload_from_disk(self, config_path: Path | None = None) -> Settings:
        """Reload settings from config.yaml."""
        with self._lock:
            new_settings = load_settings(config_path)
            self._settings = new_settings
            return self._settings
    
    def _merge_updates(self, current: Settings, updates: dict[str, Any]) -> Settings:
        """Deep merge updates into settings dataclasses."""
        # Implementation: convert to dict, merge, reconstruct Settings
        ...
```

**Responsibilities:**
- Hold current runtime settings
- Provide thread-safe read/write access
- Validate before applying changes
- Emit events on changes (future: integrate with event system)

---

#### 2. Settings Endpoints (`src/api/settings_routes.py`)

**Purpose:** aiohttp route handlers for settings API

```python
from aiohttp import web
from src.api.settings_manager import SettingsManager


async def get_settings(request: web.Request) -> web.Response:
    manager: SettingsManager = request.app["settings_manager"]
    settings = manager.get_settings()
    settings_dict = _settings_to_dict(settings, redact_passwords=True)
    return web.json_response(settings_dict)


async def get_settings_section(request: web.Request) -> web.Response:
    manager: SettingsManager = request.app["settings_manager"]
    section = request.match_info["section"]
    try:
        section_data = manager.get_section(section)
        return web.json_response(section_data)
    except KeyError as e:
        return web.json_response({"error": str(e)}, status=404)


async def update_settings(request: web.Request) -> web.Response:
    manager: SettingsManager = request.app["settings_manager"]
    try:
        updates = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    
    try:
        new_settings = manager.update_settings(updates)
        return web.json_response({
            "status": "updated",
            "settings": _settings_to_dict(new_settings, redact_passwords=True)
        })
    except SettingsValidationError as e:
        return web.json_response({
            "error": "Validation failed",
            "validation_errors": e.errors
        }, status=400)


# ... other handlers
```

---

#### 3. Integration with API Server

**Modify [src/api/app.py](../src/api/app.py):**

```python
from src.api.settings_manager import SettingsManager
from src.api.settings_routes import (
    get_settings,
    get_settings_section,
    update_settings,
    update_settings_section,
    validate_settings,
    persist_settings,
    reload_settings,
)

def create_app(
    session_manager: SessionManager,
    settings_manager: SettingsManager,  # NEW
    *,
    publish_hz: float = 10.0,
) -> web.Application:
    # ... existing middleware ...
    
    app = web.Application(middlewares=[cors_middleware])
    app["session_manager"] = session_manager
    app["settings_manager"] = settings_manager  # NEW
    app["publish_hz"] = float(publish_hz)
    
    # ... existing routes ...
    
    # NEW: Settings routes
    app.router.add_get("/settings", get_settings)
    app.router.add_get("/settings/{section}", get_settings_section)
    app.router.add_patch("/settings", update_settings)
    app.router.add_patch("/settings/{section}", update_settings_section)
    app.router.add_post("/settings/validate", validate_settings)
    app.router.add_post("/settings/persist", persist_settings)
    app.router.add_post("/settings/reload", reload_settings)
    
    return app
```

**Modify [src/api/server.py](../src/api/server.py):**

```python
from src.api.settings_manager import SettingsManager

def main() -> None:
    # ... existing setup ...
    
    settings = load_settings()
    settings_manager = SettingsManager(settings)  # NEW
    
    camera_id = _derive_camera_id_from_settings(settings)
    
    manager = SessionManager(
        cameras=[camera_id], session_factory=default_session_factory
    )
    app = create_app(
        manager,
        settings_manager,  # NEW
        publish_hz=args.publish_hz
    )
    web.run_app(app, host=args.host, port=args.port)
```

---

#### 4. Session Factory Updates

**Challenge:** New sessions must use latest settings from `SettingsManager`

**Solution:** Modify `default_session_factory` to accept `SettingsManager`

**[src/api/session.py](../src/api/session.py):**

```python
def default_session_factory(
    *,
    camera_id: str,
    settings_manager: SettingsManager,  # NEW: instead of loading settings
) -> ThreadedAnalyticsSession:
    session_id = str(uuid.uuid4())
    settings = settings_manager.get_settings()  # Get latest runtime settings
    return ThreadedAnalyticsSession(
        session_id=session_id,
        camera_id=camera_id,
        settings=settings,
        publish_debug_logs=False,
    )
```

**[src/api/session_manager.py](../src/api/session_manager.py):**

```python
# Update signature to pass settings_manager instead of just settings
```

---

### Data Flow

```
┌──────────────────────────────────────────────────────────┐
│                     Client (Frontend)                     │
└────────────┬─────────────────────────────────┬───────────┘
             │                                 │
             │ PATCH /settings                 │ GET /settings
             │ {"ptz": {...}}                  │
             │                                 │
             v                                 v
┌────────────────────────────────────────────────────────────┐
│                    API Server (aiohttp)                    │
│  ┌──────────────────────────────────────────────────────┐ │
│  │            settings_routes.py handlers               │ │
│  └────────────┬─────────────────────────────┬───────────┘ │
│               │                             │              │
│               v                             v              │
│  ┌──────────────────────────────────────────────────────┐ │
│  │           SettingsManager (thread-safe)              │ │
│  │  • _settings: Settings (current runtime state)       │ │
│  │  • get_settings() -> Settings                        │ │
│  │  • update_settings(dict) -> Settings                 │ │
│  │  • reload_from_disk() -> Settings                    │ │
│  └────────────┬─────────────────────────────┬───────────┘ │
└───────────────┼─────────────────────────────┼─────────────┘
                │                             │
                │ Used by new sessions        │ Validates using
                v                             v
┌───────────────────────────────┐  ┌─────────────────────────┐
│   SessionManager.create()     │  │  settings.py validation │
│   → default_session_factory   │  │  • _validate_settings() │
│   → ThreadedAnalyticsSession  │  │  • raises ValidationErr │
└───────────────────────────────┘  └─────────────────────────┘
                │
                v
      New session uses latest
      settings from manager
```

---

### Security & Validation

**Password Redaction:**
```python
def _settings_to_dict(settings: Settings, redact_passwords: bool = False) -> dict:
    d = asdict(settings)
    if redact_passwords:
        if "detection" in d and "camera_credentials" in d["detection"]:
            d["detection"]["camera_credentials"]["password"] = "***REDACTED***"
    return d
```

**Rate Limiting:**
- Implement simple in-memory rate limiter for `PATCH /settings` and `POST /settings/persist`
- Max 1 request per second per IP
- Return 429 (Too Many Requests) if exceeded

**Validation:**
- All updates go through `_validate_settings()` before acceptance
- File path checks (ensure model files exist)
- Numeric bounds checks (thresholds between 0-1, positive values, etc.)

---

## Testing Strategy

### Unit Tests (`tests/unit/test_settings_manager.py`)

```python
def test_settings_manager_get():
    """Test getting settings."""
    settings = load_settings()
    manager = SettingsManager(settings)
    retrieved = manager.get_settings()
    assert retrieved.ptz.ptz_movement_gain == settings.ptz.ptz_movement_gain


def test_settings_manager_update_valid():
    """Test updating with valid values."""
    manager = SettingsManager(load_settings())
    updates = {"ptz": {"ptz_movement_gain": 1.5}}
    new_settings = manager.update_settings(updates)
    assert new_settings.ptz.ptz_movement_gain == 1.5


def test_settings_manager_update_invalid():
    """Test updating with invalid values raises error."""
    manager = SettingsManager(load_settings())
    updates = {"detection": {"confidence_threshold": 1.5}}
    with pytest.raises(SettingsValidationError):
        manager.update_settings(updates)


def test_settings_manager_thread_safety():
    """Test concurrent reads/writes."""
    # Use threading to verify no race conditions
    ...
```

### Integration Tests (`tests/integration/test_settings_api.py`)

```python
async def test_get_settings(aiohttp_client):
    """Test GET /settings endpoint."""
    app = create_test_app()
    client = await aiohttp_client(app)
    resp = await client.get("/settings")
    assert resp.status == 200
    data = await resp.json()
    assert "ptz" in data
    assert "camera" in data


async def test_update_settings(aiohttp_client):
    """Test PATCH /settings endpoint."""
    app = create_test_app()
    client = await aiohttp_client(app)
    resp = await client.patch("/settings", json={
        "ptz": {"ptz_movement_gain": 2.5}
    })
    assert resp.status == 200
    data = await resp.json()
    assert data["status"] == "updated"


async def test_update_settings_validation_error(aiohttp_client):
    """Test PATCH with invalid data."""
    app = create_test_app()
    client = await aiohttp_client(app)
    resp = await client.patch("/settings", json={
        "detection": {"confidence_threshold": 99.0}
    })
    assert resp.status == 400
    data = await resp.json()
    assert "validation_errors" in data
```

---

## Migration & Rollout

### Phase 1: Core Implementation
1. Create `SettingsManager` class in `src/api/settings_manager.py`
2. Create route handlers in `src/api/settings_routes.py`
3. Add unit tests for `SettingsManager`
4. Integrate into `app.py` and `server.py`

### Phase 2: Testing & Validation
1. Add integration tests for all endpoints
2. Test with live sessions (ensure isolation)
3. Validate thread safety under load

### Phase 3: Documentation & Deployment
1. Update [ANALYTICS_WEB_INTEGRATION_GUIDE.md](ANALYTICS_WEB_INTEGRATION_GUIDE.md) with settings API examples
2. Add settings API section to [api_guide.md](../api_guide.md) (distinct from Octagon API)
3. Update [README.md](../README.md) with new API capabilities

### Phase 4: Frontend Integration (Future)
1. Build settings panel UI in frontend
2. Add real-time settings sync
3. Implement validation feedback

---

## Open Questions & Future Enhancements

### Open Questions
1. **Should settings updates restart active sessions?**
   - Current plan: No (only new sessions use updated settings)
   - Alternative: Add `POST /sessions/{id}/restart` to apply new settings to specific session

2. **Should we support environment variable overrides for settings?**
   - Example: `PTZ_MOVEMENT_GAIN=0.5 pixi run api` overrides config.yaml
   - Requires change detection and precedence rules

3. **How to handle settings that affect hardware (e.g., camera credentials)?**
   - Camera credentials changes require reconnection
   - Should we add a `POST /settings/apply-hardware` endpoint?

### Future Enhancements
1. **Settings History:**
   - Track changes over time
   - `GET /settings/history` endpoint
   - Support rollback to previous values

2. **Settings Profiles:**
   - Save named configurations (e.g., "outdoor", "night_mode")
   - `POST /settings/profiles`, `GET /settings/profiles/{name}`

3. **WebSocket Settings Updates:**
   - Push settings changes to connected clients via WebSocket
   - Emit `settings_updated` events on metadata stream

4. **Import/Export:**
   - `POST /settings/import` (upload config.yaml)
   - `GET /settings/export` (download current settings as YAML)

5. **Settings Diff:**
   - `GET /settings/diff` - Compare runtime settings vs file
   - Show which values have changed since load

---

## Success Criteria

**Definition of Done:**
1. ✅ All 7 endpoints implemented and tested
2. ✅ `SettingsManager` is thread-safe (proven via tests)
3. ✅ Settings validation prevents invalid values
4. ✅ Passwords are redacted in GET responses
5. ✅ Unit test coverage >90% for new code
6. ✅ Integration tests cover all endpoints
7. ✅ Documentation updated with API examples
8. ✅ No breaking changes to existing API clients

**Non-Goals (Out of Scope for v1):**
- Settings profiles
- History/rollback
- Automatic hardware reconfiguration
- Settings UI (frontend responsibility)

---

## References

- [ANALYTICS_BACKEND_PLAN.md](ANALYTICS_BACKEND_PLAN.md) - Original backend architecture
- [src/settings.py](../src/settings.py) - Settings dataclasses and validation
- [src/api/app.py](../src/api/app.py) - Current API routes
- [config.yaml](../config.yaml) - Settings schema
- [pixi.toml](../pixi.toml) - Task definitions
