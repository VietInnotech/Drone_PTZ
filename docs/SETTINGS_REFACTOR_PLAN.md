# Settings Architecture Refactor Plan

**Date:** December 22, 2025  
**Status:** Draft / Proposal  
**Goal:** Create a cleaner, more consistent, and industry-standard settings management system

---

## Executive Summary

Current settings implementation has inconsistencies between API naming (`ptz`), config file naming (`ptz_control`), and mixed responsibilities (detection holds camera credentials). This plan proposes a Pydantic-based settings architecture following 12-factor app principles with clear layering and consistent naming.

---

## Current Issues

### 1. Naming Inconsistencies
- **API responses** use dataclass field names: `ptz`, `detection`, `camera`, `performance`
- **config.yaml** expects: `ptz_control`, top-level `camera_credentials`
- **Workaround:** Manual mapping in `persist_settings()` to translate `ptz` → `ptz_control`
- **Problem:** Confusing for API consumers; error-prone maintenance

### 2. Nested Credentials in Wrong Place
- `camera_credentials` lives under `detection.camera_credentials` in dataclass
- Should be top-level or under `camera` section (it's camera auth, not detection config)
- Forces special handling during persist/load

### 3. No Environment Variable Support
- All config comes from YAML file only
- Cannot override settings via env vars (violates 12-factor principle III)
- Secrets in plaintext YAML (no vault/secret manager integration)

### 4. Manual Validation Logic
- Custom `_validate_settings()` function with ~100 LOC of validation
- Hard to extend; no automatic env var parsing/coercion
- Type hints exist but not enforced at load time

### 5. Runtime vs Persistent Semantics Unclear
- API updates are in-memory only (ephemeral)
- `/settings/persist` writes to disk but naming requires translation
- No clear guidance on when to persist vs when to keep ephemeral

### 6. Single Format (YAML) Only
- Loader/persister hardcoded to YAML
- No JSON/TOML support
- YAML dependency required even if users prefer other formats

---

## Industry Best Practices Research

### 12-Factor App Config (Factor III)
> "Store config in the environment"

- **Recommendation:** Strict separation of config from code; config varies per deployment, code does not
- **Environment variables** are the gold standard for portability
- **Files** (YAML/JSON/TOML) are acceptable for local dev but should not be the only source

### Pydantic Settings (FastAPI Standard)
- `pydantic-settings` library is the de facto standard for Python config management
- **Features:**
  - Automatic env var parsing with type coercion
  - Nested models with dot notation (`PTZ__PID_KP` or `PTZ.PID_KP`)
  - Multiple sources: env, `.env` files, custom loaders
  - JSON Schema generation for documentation
  - Built-in validation with clear error messages
- **Adoption:** FastAPI, Starlette, many production systems

### Dynaconf (Alternative)
- Dynamic configuration with layered sources
- **Features:**
  - Environment-aware (dev/staging/prod)
  - Multiple formats (YAML/JSON/TOML/INI)
  - Secret management integration (Vault, AWS Secrets Manager)
  - Hot reload support
- **Trade-off:** More complex API vs Pydantic's simplicity

### Configuration Hierarchy (Standard Pattern)
```
1. Code defaults (dataclass default values)
2. Config file (optional: config.yaml, .env)
3. Environment variables (override file)
4. Runtime API updates (override everything, ephemeral or persistent)
```

### Naming Conventions
- **Flat env vars:** `CAMERA_SOURCE`, `PTZ_PID_KP`, `DETECTION_MODEL_PATH`
- **Nested with separators:** `PTZ__PID_KP` (double underscore) or `PTZ.PID_KP` (dot)
- **API JSON:** Use consistent names that match one canonical structure
- **Files:** Allow any format but stick to one schema

---

## Proposed Architecture

### Core Principles

1. **Single Schema Definition:** One set of Pydantic models defines all settings
2. **Layered Loading:** defaults → file → env → runtime overrides
3. **Consistent Naming:** Same field names everywhere (API, config file, env vars)
4. **Type Safety:** Pydantic validates all inputs automatically
5. **Secret Management:** Support env vars and future vault integration
6. **Optional Persistence:** File writes are opt-in; primary source is code + env

### New Settings Structure

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class LoggingConfig(BaseSettings):
    log_file: str = "logs/app.log"
    log_level: str = "DEBUG"
    # ... other fields
    
class CameraConfig(BaseSettings):
    source: str = "camera"  # camera | video | webrtc | rtsp
    index: int = Field(default=4, ge=0)
    rtsp_url: str | None = None
    webrtc_url: str = "http://localhost:8889/camera_1/"
    resolution_width: int = Field(default=1280, gt=0)
    resolution_height: int = Field(default=720, gt=0)
    fps: int = Field(default=30, gt=0)
    
    # Auth moved here (camera credentials belong with camera config)
    credentials_ip: str = "192.168.1.70"
    credentials_user: str = "admin"
    credentials_password: str = Field(default="admin@123", repr=False)  # repr=False hides in logs

class PTZConfig(BaseSettings):
    movement_gain: float = Field(default=2.0, ge=0)
    movement_threshold: float = Field(default=0.05, ge=0, le=1.0)
    
    # PID gains (new unified naming)
    pid_kp: float = Field(default=2.0, ge=0)
    pid_ki: float = Field(default=0.15, ge=0)
    pid_kd: float = Field(default=0.8, ge=0)
    pid_integral_limit: float = Field(default=1.0, gt=0)
    pid_dead_band: float = Field(default=0.01, ge=0)
    
    # Zoom settings
    zoom_target_coverage: float = Field(default=0.2, ge=0, le=1.0)
    zoom_velocity_gain: float = Field(default=0.5, ge=0)
    # ... other zoom/control fields
    
    control_mode: str = Field(default="onvif", pattern="^(onvif|octagon)$")

class DetectionConfig(BaseSettings):
    model_path: str = "assets/models/yolo/best5.pt"
    confidence_threshold: float = Field(default=0.3, ge=0, le=1.0)
    target_labels: list[str] = Field(default_factory=lambda: ["drone", "UAV"])
    
    # Validation hook for model file exists
    @field_validator("model_path")
    def model_must_exist(cls, v):
        from pathlib import Path
        if not Path(v).exists():
            raise ValueError(f"Model file not found: {v}")
        return v

class PerformanceConfig(BaseSettings):
    fps_window_size: int = Field(default=30, gt=0)
    zoom_dead_zone: float = Field(default=0.03, ge=0, le=1.0)
    frame_queue_maxsize: int = Field(default=1, gt=0)

class SimulatorConfig(BaseSettings):
    use_ptz_simulation: bool = False
    video_source: str | None = "assets/videos/V_DRONE_045.mp4"
    video_loop: bool = False
    viewport: bool = True
    # ... other sim fields

class TrackingConfig(BaseSettings):
    tracker_type: str = Field(default="botsort", pattern="^(botsort|bytetrack)$")

class OctagonConfig(BaseSettings):
    """Octagon API credentials and device IDs (optional, only if control_mode=octagon)"""
    ip: str = "192.168.1.123"
    user: str = "admin"
    password: str = Field(default="!Inf2019", repr=False)
    pantilt_id: str = "pantilt"
    visible_id: str = "visible1"

class AppSettings(BaseSettings):
    """Root settings with all subsections"""
    model_config = SettingsConfigDict(
        env_prefix="",  # No global prefix; each section handles its own
        env_nested_delimiter="__",  # PTZ__PID_KP maps to ptz.pid_kp
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore unknown env vars
    )
    
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    camera: CameraConfig = Field(default_factory=CameraConfig)
    ptz: PTZConfig = Field(default_factory=PTZConfig)
    detection: DetectionConfig = Field(default_factory=DetectionConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    simulator: SimulatorConfig = Field(default_factory=SimulatorConfig)
    tracking: TrackingConfig = Field(default_factory=TrackingConfig)
    octagon: OctagonConfig = Field(default_factory=OctagonConfig)
```

### Loading Order

```python
def load_settings(
    config_file: Path | None = None,
    env_file: Path | None = None,
) -> AppSettings:
    """Load settings from all sources with proper precedence.
    
    Priority (highest to lowest):
    1. Environment variables
    2. Config file (YAML/JSON/TOML if provided)
    3. .env file (if provided)
    4. Code defaults
    """
    # Pydantic-settings automatically handles:
    # - Loading from env vars
    # - Loading from .env file
    # - Type coercion and validation
    
    # Optional: overlay config file if provided
    if config_file and config_file.exists():
        file_data = load_config_file(config_file)  # YAML/JSON/TOML
        return AppSettings.model_validate(file_data)
    
    # Default: env + .env + code defaults
    return AppSettings()
```

### Environment Variable Examples

```bash
# Camera settings
CAMERA__SOURCE=webrtc
CAMERA__WEBRTC_URL=http://localhost:8889/stream
CAMERA__CREDENTIALS_PASSWORD=secret123

# PTZ PID tuning
PTZ__PID_KP=1.5
PTZ__PID_KI=0.1
PTZ__PID_KD=0.6

# Detection
DETECTION__MODEL_PATH=/models/yolo11n.pt
DETECTION__CONFIDENCE_THRESHOLD=0.5
DETECTION__TARGET_LABELS='["drone","uav","person"]'  # JSON array

# Control mode
PTZ__CONTROL_MODE=octagon
OCTAGON__IP=192.168.1.100
OCTAGON__PASSWORD=secure_pass
```

### API Updates

#### GET `/settings`
```json
{
  "logging": { "log_file": "logs/app.log", "log_level": "DEBUG", ... },
  "camera": {
    "source": "webrtc",
    "credentials_password": "***REDACTED***",
    ...
  },
  "ptz": {
    "movement_gain": 2.0,
    "pid_kp": 2.0,
    "pid_ki": 0.15,
    ...
  },
  "detection": { "model_path": "...", ... },
  ...
}
```

**Changes:**
- Consistent naming (no more `ptz_control` vs `ptz` mismatch)
- Credentials under `camera` (not `detection`)
- Flat PID gains under `ptz` (clear hierarchy)

#### PATCH `/settings` or `/settings/{section}`
- Same JSON structure as GET
- Deep merge + validate
- Return updated settings

#### POST `/settings/persist`
- Optional `format` query param: `?format=yaml` (default), `?format=json`, `?format=toml`
- Writes effective settings to file
- Creates backup with timestamp

#### POST `/settings/reload`
- Reloads from file + env (clears runtime overrides)
- Returns new effective settings

---

## Migration Path

### Phase 1: Add Pydantic Settings (Non-Breaking)
1. Install `pydantic-settings`: `pixi add pydantic-settings`
2. Create new `src/settings_v2.py` with Pydantic models (parallel to existing)
3. Add `load_settings_v2()` function that returns `AppSettings`
4. Keep existing `load_settings()` for backward compat

**Testing:**
- Load same config with both loaders
- Compare outputs
- Validate all fields match

### Phase 2: Update API to Use V2 (Breaking for Config Files)
1. Switch `src/api/server.py` to use `load_settings_v2()`
2. Update `SettingsManager` to work with `AppSettings`
3. Fix persist logic to write consistent format
4. Update docs with new env var examples

**Migration notes for users:**
```yaml
# OLD config.yaml
ptz_control:
  ptz_movement_gain: 2.0
camera_credentials:
  ip: 192.168.1.70

# NEW config.yaml
ptz:
  movement_gain: 2.0
camera:
  credentials_ip: 192.168.1.70
```

### Phase 3: Update Main Application
1. Switch `src/main.py` to use `load_settings_v2()`
2. Update all settings access patterns
3. Remove legacy `load_settings()` and old dataclasses

### Phase 4: Add Multi-Format Support
1. Implement format detection (YAML/JSON/TOML)
2. Add `--config-format` CLI arg
3. Update persist endpoint to support format selection

### Phase 5: Deprecate YAML Requirement (Optional)
1. Make config file completely optional
2. Document env-only deployment pattern
3. Provide migration script: YAML → env template

---

## Testing Strategy

### Unit Tests
```python
def test_load_from_env(monkeypatch):
    monkeypatch.setenv("PTZ__PID_KP", "1.5")
    monkeypatch.setenv("CAMERA__SOURCE", "rtsp")
    settings = load_settings_v2()
    assert settings.ptz.pid_kp == 1.5
    assert settings.camera.source == "rtsp"

def test_validation_negative_pid():
    with pytest.raises(ValidationError):
        PTZConfig(pid_kp=-1.0)

def test_model_path_must_exist():
    with pytest.raises(ValidationError):
        DetectionConfig(model_path="/nonexistent/model.pt")
```

### Integration Tests
```python
def test_api_persist_reload_roundtrip():
    # PATCH settings
    response = await client.patch("/settings", json={"ptz": {"pid_kp": 1.8}})
    assert response.status == 200
    
    # Persist
    await client.post("/settings/persist?format=json")
    
    # Reload
    await client.post("/settings/reload")
    
    # Verify
    response = await client.get("/settings")
    assert response.json()["ptz"]["pid_kp"] == 1.8
```

### Environment Tests
```python
def test_env_overrides_file(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("ptz:\n  pid_kp: 2.0\n")
    
    os.environ["PTZ__PID_KP"] = "3.0"
    settings = load_settings_v2(config_file=config_file)
    
    assert settings.ptz.pid_kp == 3.0  # Env wins
```

---

## Benefits

### For Developers
- **Type safety:** Pydantic catches config errors at load time, not runtime
- **IDE support:** Full autocomplete and type hints
- **Less boilerplate:** No manual validation code
- **Easier testing:** Mock env vars, inject test configs

### For Operators
- **12-factor compliance:** Deploy same code, different config via env
- **Secret management:** Passwords via env or vault, not YAML
- **Hot reload:** Change env, restart process (no file editing)
- **Clear precedence:** Know which source wins (env > file > default)

### For API Consumers
- **Consistent naming:** Same field names in GET/PATCH/persist/reload
- **Better docs:** JSON Schema auto-generated from Pydantic models
- **Validation errors:** Clear messages (e.g., "pid_kp must be >= 0")

---

## Risks & Mitigations

### Risk 1: Breaking Change for Users
- **Mitigation:** Provide migration script; support both loaders temporarily
- **Timeline:** Announce v2 format; deprecate v1 after 2 releases

### Risk 2: Environment Variable Explosion
- **Mitigation:** Keep file support; env is for overrides, not primary source
- **Best practice:** Use `.env` files locally; env vars in prod

### Risk 3: Pydantic Dependency
- **Mitigation:** Already use dataclasses; Pydantic is minimal overhead
- **Alternative:** Stick with manual validation if dependency is a concern

---

## Open Questions

1. **Should we support runtime hot reload without restart?**
   - Complexity: High (need to propagate to running sessions)
   - Value: Medium (useful for tuning, but restart is acceptable)
   - Recommendation: Phase 2 feature; not MVP

2. **Secret management integration (Vault, AWS Secrets)?**
   - Pydantic-settings supports custom sources
   - Recommendation: Document extension pattern; don't implement initially

3. **Config file format preference?**
   - YAML: Human-friendly, current standard
   - JSON: Simple, universally supported
   - TOML: Python-native, gaining traction
   - Recommendation: Support all three; default to YAML for backward compat

4. **Should API persist be automatic or explicit?**
   - Current: Explicit `/settings/persist` call
   - Alternative: Auto-persist on PATCH (like database)
   - Recommendation: Keep explicit; gives operators control

---

## Timeline Estimate

- **Phase 1 (Pydantic Migration):** 2-3 days
  - Models, loaders, tests
- **Phase 2 (API Update):** 1-2 days
  - SettingsManager, persist/reload, docs
- **Phase 3 (Main App):** 1 day
  - Update main.py, remove legacy code
- **Phase 4 (Multi-Format):** 1-2 days
  - JSON/TOML support, format selection
- **Phase 5 (Optional File):** 1 day
  - Env-only mode, migration tools

**Total:** 6-9 days for full implementation + testing

---

## References

- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [FastAPI Settings Guide](https://fastapi.tiangolo.com/advanced/settings/)
- [12-Factor App: Config](https://12factor.net/config)
- [Dynaconf Documentation](https://www.dynaconf.com/)
- [Python Logging Best Practices](https://docs.python-guide.org/writing/logging/)

---

## Appendix: Example Migration Script

```python
#!/usr/bin/env python3
"""Migrate config.yaml from v1 to v2 format."""

import yaml
from pathlib import Path

def migrate_config(old_path: Path, new_path: Path):
    with old_path.open() as f:
        old_config = yaml.safe_load(f)
    
    new_config = {
        "logging": old_config.get("logging", {}),
        "camera": {
            **old_config.get("camera", {}),
            # Move credentials from camera_credentials to camera
            **{f"credentials_{k}": v for k, v in old_config.get("camera_credentials", {}).items()},
        },
        "ptz": old_config.get("ptz_control", {}),  # Rename ptz_control → ptz
        "detection": {
            k: v for k, v in old_config.get("detection", {}).items()
            if k != "camera_credentials"  # Remove nested credentials
        },
        "performance": old_config.get("performance", {}),
        "simulator": old_config.get("ptz_simulator", {}),
        "tracking": old_config.get("tracking", {}),
        "octagon": old_config.get("octagon_credentials", {}),
    }
    
    with new_path.open("w") as f:
        yaml.dump(new_config, f, default_flow_style=False, sort_keys=False)
    
    print(f"Migrated {old_path} → {new_path}")

if __name__ == "__main__":
    migrate_config(Path("config.yaml"), Path("config_v2.yaml"))
```

---

**Next Steps:** Review this plan, gather feedback, prioritize phases, and begin implementation.
