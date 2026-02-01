from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import sys
import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    ValidationInfo,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

CONFIG_FILENAME = "config.yaml"


class SettingsError(ValueError):
    """Base error for settings-related issues."""


class SettingsValidationError(SettingsError):
    """Raised when one or more settings values are invalid."""

    def __init__(self, errors: list[str]):
        super().__init__("\n".join(errors))
        self.errors = errors


def _format_validation_errors(exc: ValidationError) -> list[str]:
    errors: list[str] = []
    for err in exc.errors():
        loc = ".".join(str(part) for part in err.get("loc", ()))
        msg = err.get("msg", "invalid value")
        errors.append(f"{loc}: {msg}")
    return errors


def _resolve_config_path(config_path: Path | None) -> Path:
    if config_path is not None:
        return config_path

    if getattr(sys, "frozen", False):
        root = Path(sys.executable).parent
    else:
        root = Path(__file__).parent.parent

    candidates: list[Path] = []
    for candidate in ("config.yaml", "config.yml"):
        candidate_path = root / candidate
        if candidate_path.exists():
            candidates.append(candidate_path)

    if candidates:
        return max(candidates, key=lambda p: p.stat().st_mtime)

    return root / CONFIG_FILENAME


def _load_config_file(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        return {}

    suffix = config_path.suffix.lower()
    if suffix not in {".yaml", ".yml"}:
        raise SettingsError(f"Unsupported config format: {config_path.suffix}")

    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise SettingsError(f"Expected mapping at top level of {config_path}")
    return data


class LoggingSettings(BaseModel):
    log_file: str = "logs/app.log"
    log_level: str = "DEBUG"
    log_format: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    log_rotation: str = "5 MB"
    log_retention: str = "30 days"
    log_enqueue: bool = True
    log_backtrace: bool = True
    log_diagnose: bool = True
    write_log_file: bool = True
    reset_log_on_start: bool = True

    model_config = ConfigDict(extra="ignore")


class BackupSettings(BaseModel):
    keep_last: int = Field(default=10, ge=1)

    model_config = ConfigDict(extra="ignore")


class CameraSourceConfig(BaseModel):
    """Unified camera source configuration for any detection mode."""

    # Source type: local camera, RTSP, WebRTC, or SkyShield reference
    source: Literal["camera", "rtsp", "webrtc", "skyshield"] = "camera"

    # For source="camera" (local device)
    camera_index: int = Field(default=0, ge=0)

    # For source="rtsp"
    rtsp_url: str | None = None

    # For source="webrtc" (direct URL)
    webrtc_url: str | None = None

    # For source="skyshield" (recommended) - just reference the camera ID
    # WebRTC URL is derived: http://{skyshield_host}:8889/camera_{id}/
    skyshield_camera_id: int | None = None

    # Resolution & FPS
    resolution_width: int = Field(default=1280, gt=0)
    resolution_height: int = Field(default=720, gt=0)
    fps: int = Field(default=30, gt=0)

    # Legacy credentials kept for ONVIF/RTSP direct access
    credentials_ip: str | None = None
    credentials_user: str | None = None
    credentials_password: str | None = Field(default=None, repr=False)

    model_config = ConfigDict(extra="ignore")

    @field_validator("rtsp_url", "webrtc_url", mode="before")
    @classmethod
    def _empty_string_to_none(cls, value: str | None) -> str | None:
        return value or None

    def get_unique_source_key(self) -> str:
        """Return a unique key identifying this camera source."""
        if self.source == "camera":
            return f"local:{self.camera_index}"
        if self.source == "rtsp":
            return f"rtsp:{self.rtsp_url}"
        if self.source == "webrtc":
            return f"webrtc:{self.webrtc_url}"
        if self.source == "skyshield":
            return f"skyshield:{self.skyshield_camera_id}"
        return "unknown"


class VisibleDetectionConfig(BaseModel):
    """YOLO-based visible detection configuration."""

    enabled: bool = False
    camera: CameraSourceConfig = Field(default_factory=CameraSourceConfig)
    confidence_threshold: float = Field(default=0.35, ge=0.0, le=1.0)
    model_path: str = "assets/models/yolo/best5.pt"
    target_labels: list[str] = Field(default_factory=lambda: ["drone", "UAV"])

    model_config = ConfigDict(extra="ignore")

    @field_validator("model_path")
    @classmethod
    def _model_exists(cls, value: str) -> str:
        if value and not Path(value).exists():
            raise ValueError(f"Model file not found: {value}")
        return value


class SecondaryDetectionConfig(BaseModel):
    """YOLO-based secondary detection configuration."""

    enabled: bool = False
    camera: CameraSourceConfig = Field(default_factory=CameraSourceConfig)
    confidence_threshold: float = Field(default=0.35, ge=0.0, le=1.0)
    model_path: str = "assets/models/yolo/best5.pt"
    target_labels: list[str] = Field(default_factory=lambda: ["drone", "UAV"])

    model_config = ConfigDict(extra="ignore")

    @field_validator("model_path")
    @classmethod
    def _model_exists(cls, value: str) -> str:
        if value and not Path(value).exists():
            raise ValueError(f"Model file not found: {value}")
        return value


class PTZSettings(BaseModel):
    ptz_movement_gain: float = Field(default=2.0, ge=0)
    ptz_movement_threshold: float = Field(default=0.05, ge=0.0, le=1.0)
    zoom_target_coverage: float = Field(default=0.2, ge=0.0, le=1.0)
    zoom_reset_timeout: float = Field(default=2.0, ge=0.0)
    zoom_min_interval: float = Field(default=0.1, ge=0.0)
    zoom_velocity_gain: float = Field(default=0.5, ge=0.0)
    zoom_reset_velocity: float = Field(default=0.5, ge=0.0)
    ptz_ramp_rate: float = Field(default=0.2, gt=0.0)
    no_detection_home_timeout: int = Field(default=5, ge=0)
    control_mode: Literal["onvif", "octagon", "none"] = "onvif"
    position_mode: Literal["onvif", "octagon", "auto", "none"] = "auto"
    pid_kp: float = Field(default=2.0, ge=0.0)
    pid_ki: float = Field(default=0.15, ge=0.0)
    pid_kd: float = Field(default=0.8, ge=0.0)
    pid_integral_limit: float = Field(default=1.0, gt=0.0)
    pid_dead_band: float = Field(default=0.01, ge=0.0)
    invert_pan: bool = False
    invert_tilt: bool = False
    enable_zoom_compensation: bool = True
    zoom_max_magnification: float = Field(default=20.0, ge=1.0)

    model_config = ConfigDict(extra="ignore")


class PerformanceSettings(BaseModel):
    fps_window_size: int = Field(default=30, gt=0)
    zoom_dead_zone: float = Field(default=0.03, ge=0.0, le=1.0)
    frame_queue_maxsize: int = Field(default=1, gt=0)
    publish_hz: float = Field(default=10.0, ge=1.0, le=60.0)

    model_config = ConfigDict(extra="ignore")


class SimulatorSettings(BaseModel):
    use_ptz_simulation: bool = True
    video_source: str | None = "assets/videos/V_DRONE_045.mp4"
    video_loop: bool = False
    sim_viewport: bool = True
    sim_pan_step: float = Field(default=0.1, ge=0.0)
    sim_tilt_step: float = Field(default=0.1, ge=0.0)
    sim_zoom_step: float = Field(default=0.1, ge=0.0)
    sim_zoom_min_scale: float = Field(default=0.3, ge=0.0, le=1.0)
    sim_draw_original_viewport_box: bool = True

    model_config = ConfigDict(extra="ignore")

    @field_validator("video_source")
    @classmethod
    def _video_exists(cls, value: str | None) -> str | None:
        if value and not Path(value).exists():
            raise ValueError(f"Video source not found: {value}")
        return value




class ThermalDetectionConfig(BaseModel):
    """Thermal/IR-based detection configuration."""

    enabled: bool = False
    camera: CameraSourceConfig = Field(
        default_factory=lambda: CameraSourceConfig(source="camera", camera_index=1)
    )
    detection_method: Literal["contour", "blob", "hotspot"] = "contour"
    threshold_value: int = Field(default=200, ge=0, le=255)
    use_otsu: bool = True  # Auto-determine threshold using Otsu's method
    clahe_clip_limit: float = Field(default=2.0, ge=0.0, le=40.0)
    clahe_tile_size: int = Field(default=8, ge=1, le=64)
    min_area: int = Field(default=100, ge=1)  # Minimum blob area in pixels
    max_area: int = Field(default=50000, ge=1)  # Maximum blob area
    blur_size: int = Field(default=5, ge=0)  # Gaussian blur kernel size (0 = disabled)
    use_kalman: bool = True  # Enable Kalman filter smoothing

    model_config = ConfigDict(extra="ignore")

    @field_validator("blur_size")
    @classmethod
    def _blur_must_be_odd(cls, value: int) -> int:
        if value > 0 and value % 2 == 0:
            return value + 1  # Make odd for OpenCV
        return value


class OctagonSettings(BaseModel):
    ip: str = "192.168.1.123"
    user: str = "admin"
    password: str = Field(default="!Inf2019", repr=False)

    model_config = ConfigDict(extra="ignore")


class OctagonDevices(BaseModel):
    pantilt_id: str = "pantilt"
    visible_id: str = "visible1"

    model_config = ConfigDict(extra="ignore")


class SkyShieldConfig(BaseModel):
    """SkyShield server connection settings."""

    base_url: str = "http://localhost:3000"
    mediamtx_webrtc_base: str = "http://localhost:8889"


class TrackingConfig(BaseModel):
    """PTZ tracking behavior settings."""

    # Which detection mode drives PTZ when both have targets
    priority: Literal["visible", "thermal", "secondary"] = "thermal"
    
    # Ultralytics YOLO Tracker Selection
    tracker_type: Literal["botsort", "bytetrack"] = "bytetrack"

    # Timeline settings
    confirm_after: int = Field(default=2, ge=1)
    end_after_ms: int = Field(default=1000, ge=0)

    model_config = ConfigDict(extra="ignore")


class Settings(BaseSettings):
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    backups: BackupSettings = Field(default_factory=BackupSettings)
    visible_detection: VisibleDetectionConfig = Field(
        default_factory=VisibleDetectionConfig
    )
    secondary_detection: SecondaryDetectionConfig = Field(
        default_factory=SecondaryDetectionConfig
    )
    thermal_detection: ThermalDetectionConfig = Field(
        default_factory=ThermalDetectionConfig
    )
    skyshield: SkyShieldConfig = Field(default_factory=SkyShieldConfig)
    ptz: PTZSettings = Field(default_factory=PTZSettings)
    performance: PerformanceSettings = Field(default_factory=PerformanceSettings)
    simulator: SimulatorSettings = Field(default_factory=SimulatorSettings)
    tracking: TrackingConfig = Field(default_factory=TrackingConfig)
    octagon: OctagonSettings = Field(default_factory=OctagonSettings)
    octagon_devices: OctagonDevices = Field(default_factory=OctagonDevices)

    # Added to support dynamic camera ID validation from config
    cameras: list[str] = Field(default_factory=lambda: ["default"])

    model_config = SettingsConfigDict(
        env_prefix="",
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        # Environment (and .env) override config file and defaults
        return (env_settings, dotenv_settings, init_settings, file_secret_settings)

    @model_validator(mode="after")
    def _octagon_requirements(self) -> "Settings":
        if self.ptz.control_mode == "octagon":
            if (
                not self.octagon.ip
                or not self.octagon.user
                or not self.octagon.password
            ):
                raise ValueError(
                    "octagon credentials must be set when control_mode=octagon"
                )
            if (
                not self.octagon_devices.pantilt_id
                or not self.octagon_devices.visible_id
            ):
                raise ValueError(
                    "octagon device ids must be set when control_mode=octagon"
                )
        return self

    @model_validator(mode="after")
    def _validate_camera_sources(self) -> "Settings":
        """Ensure enabled detection pipelines don't use the same camera source."""
        enabled_configs = []
        if self.visible_detection.enabled:
            enabled_configs.append(("visible", self.visible_detection.camera))
        if self.thermal_detection.enabled:
            enabled_configs.append(("thermal", self.thermal_detection.camera))
        if self.secondary_detection.enabled:
            enabled_configs.append(("secondary", self.secondary_detection.camera))

        if len(enabled_configs) < 2:
            return self
        
        seen: dict[str, str] = {}
        for name, cam in enabled_configs:
            key = cam.get_unique_source_key()
            if key == "unknown":
                continue
            if key in seen:
                raise ValueError(
                    f"Camera conflict: {seen[key]} and {name} detection both use {key}. "
                    "Assign different cameras to each detection mode."
                )
            seen[key] = name
        return self


def load_settings(
    config_path: Path | None = None,
    *,
    env_file: Path | None = None,
) -> Settings:
    path = _resolve_config_path(config_path)
    file_data: dict[str, Any] = {}
    try:
        file_data = _load_config_file(path)
    except SettingsError:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        raise SettingsError(f"Failed to read config file {path}: {exc}") from exc

    env_file_value = str(env_file) if env_file else None

    try:
        return Settings(**file_data, _env_file=env_file_value)
    except ValidationError as exc:
        raise SettingsValidationError(_format_validation_errors(exc)) from exc
