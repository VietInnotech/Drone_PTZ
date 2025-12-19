from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

CONFIG_FILENAME = "config.yaml"


class SettingsError(ValueError):
    """Base error for settings-related issues."""


class SettingsValidationError(SettingsError):
    """Raised when one or more settings values are invalid."""

    def __init__(self, errors: list[str]):
        super().__init__("\n".join(errors))
        self.errors = errors


@dataclass(slots=True)
class LoggingSettings:
    """Logging configuration.

    Mirrors the logging-related behavior of Config getters while being fully typed.
    """

    log_file: str = "logs/app.log"
    log_level: str = "DEBUG"
    log_format: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:"
        "<cyan>{line}</cyan> - <level>{message}</level>"
    )
    log_rotation: str = "5 MB"
    log_retention: str = "30 days"
    log_enqueue: bool = True
    log_backtrace: bool = True
    log_diagnose: bool = True
    write_log_file: bool = True
    reset_log_on_start: bool = True


@dataclass(slots=True)
class CameraSettings:
    """Camera input configuration."""

    # Source can be: 'camera' (default), 'video' (simulator.video_source), or 'webrtc'
    source: str = "camera"
    camera_index: int = 4
    rtsp_url: str | None = None
    webrtc_url: str | None = None
    resolution_width: int = 1280
    resolution_height: int = 720
    fps: int = 30


@dataclass(slots=True)
class CameraCredentials:
    """ONVIF camera credentials."""

    ip: str = "192.168.1.70"
    user: str = "admin"
    password: str = "admin@123"


@dataclass(slots=True)
class OctagonCredentials:
    """Octagon HTTP API credentials (basic auth)."""

    ip: str = "192.168.1.123"
    user: str = "admin"
    password: str = "!Inf2019"


@dataclass(slots=True)
class OctagonDevices:
    """Octagon device IDs used in API paths (e.g., 'visible1')."""

    pantilt_id: str = "pantilt"
    visible_id: str = "visible1"


@dataclass(slots=True)
class DetectionSettings:
    """Detection / model configuration."""

    confidence_threshold: float = 0.3
    model_path: str = "assets/models/yolo/roboflowaccurate.pt"
    target_labels: list[str] = field(default_factory=lambda: ["drone", "UAV"])
    # Use default_factory to avoid shared mutable defaults between instances.
    camera_credentials: CameraCredentials = field(default_factory=CameraCredentials)


@dataclass(slots=True)
class PTZSettings:
    """PTZ control configuration."""

    ptz_movement_gain: float = 2.0
    ptz_movement_threshold: float = 0.05
    zoom_target_coverage: float = 0.2
    zoom_reset_timeout: float = 2.0
    zoom_min_interval: float = 0.1
    # Reduced from 2.0 to 0.5 for gradual zooming instead of instant aggressive zoom
    # When ID selected and target is small, coverage_diff is multiplied by this gain
    # Lower gain = smoother, more realistic PTZ behavior on real hardware
    zoom_velocity_gain: float = 0.5
    zoom_reset_velocity: float = 0.5
    ptz_ramp_rate: float = 0.2
    no_detection_home_timeout: int = 5
    # Select control path: 'onvif' or 'octagon'
    control_mode: str = "onvif"


@dataclass(slots=True)
class PerformanceSettings:
    """Performance tuning configuration."""

    fps_window_size: int = 30
    zoom_dead_zone: float = 0.03
    frame_queue_maxsize: int = 1


@dataclass(slots=True)
class SimulatorSettings:
    """PTZ simulator configuration.

    Defaults are chosen to be opt-in but use the same values as Config getters.
    """

    use_ptz_simulation: bool = True
    video_source: str | None = "assets/videos/V_DRONE_045.mp4"
    video_loop: bool = False
    sim_viewport: bool = True
    sim_pan_step: float = 0.1
    sim_tilt_step: float = 0.1
    sim_zoom_step: float = 0.1
    sim_zoom_min_scale: float = 0.3
    sim_draw_original_viewport_box: bool = True


@dataclass(slots=True)
class TrackingSettings:
    """Ultralytics tracker configuration.

    Ultralytics tracker parameters are configured in separate YAML files:
    - config/trackers/botsort.yaml
    - config/trackers/bytetrack.yaml
    """

    # Ultralytics YOLO Tracker Selection
    # Detailed tracker parameters are in config/trackers/{tracker_type}.yaml
    tracker_type: str = "botsort"  # Options: botsort, bytetrack


@dataclass(slots=True)
class Settings:
    """Top-level settings object composed of all configuration sections.

    This is the future replacement for Config. It is designed to be:

    - Typed: all fields have explicit types.
    - Explicit: grouped by logical concerns (logging, camera, ptz, etc.).
    - Compatible: defaults and semantics mirror the existing Config getters.
    """

    logging: LoggingSettings
    camera: CameraSettings
    detection: DetectionSettings
    ptz: PTZSettings
    performance: PerformanceSettings
    simulator: SimulatorSettings
    tracking: TrackingSettings
    # Provide sensible defaults so tests and consumers can omit these
    # when `ptz.control_mode` is not 'octagon'.
    octagon: OctagonCredentials = field(default_factory=OctagonCredentials)
    octagon_devices: OctagonDevices = field(default_factory=OctagonDevices)


def _load_raw_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load raw YAML configuration.

    Does not perform validation. Missing file results in an empty dict so that
    Settings can be constructed entirely from defaults, matching the behavior
    where Config getters all have safe defaults.
    """
    if config_path is None:
        # Mirror src/config.py behavior: config.yaml lives at project root.
        config_path = Path(__file__).parent.parent / CONFIG_FILENAME

    if not config_path.exists():
        # Phase 1 requirement: handle missing config.yaml gracefully using defaults.
        return {}

    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if data is None:
        return {}
    if not isinstance(data, dict):
        msg = f"Expected top-level mapping in {config_path}, got {type(data)}"
        raise SettingsError(msg)
    return data


def _get_section(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key, {}) or {}
    if not isinstance(value, dict):
        # Treat non-dict as invalid; rely on validation to surface detailed errors.
        return {}
    return value


def load_settings(config_path: Path | None = None) -> Settings:
    """Load, validate, and return a Settings instance.

    Behavior:
    - Reads `config.yaml` from the project root (or the provided path).
    - Applies defaults identical to `Config` getters when values are missing.
    - Handles missing config.yaml by using all defaults.
    - Performs validation similar to `Config.validate()` and raises
      SettingsValidationError with descriptive messages when invalid.

    This function is side-effect free and can be safely used in both runtime
    code and tests. It is intended to coexist with the legacy Config during
    the migration period.
    """
    raw = _load_raw_config(config_path)

    logging_section = _get_section(raw, "logging")
    camera_section = _get_section(raw, "camera")
    detection_section = _get_section(raw, "detection")
    ptz_control_section = _get_section(raw, "ptz_control")
    performance_section = _get_section(raw, "performance")
    camera_credentials_section = _get_section(raw, "camera_credentials")
    octagon_credentials_section = _get_section(raw, "octagon_credentials")
    octagon_devices_section = _get_section(raw, "octagon_devices")
    ptz_simulator_section = _get_section(raw, "ptz_simulator")
    tracking_section = _get_section(raw, "tracking")

    logging_settings = LoggingSettings(
        # Use concrete literals instead of dataclass attributes to avoid
        # member_descriptor issues and to mirror Config defaults exactly.
        log_file=str(logging_section.get("log_file", "logs/app.log")),
        log_level=str(logging_section.get("log_level", "DEBUG")),
        log_format=str(
            logging_section.get(
                "log_format",
                (
                    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                    "<level>{level: <8}</level> | "
                    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:"
                    "<cyan>{line}</cyan> - <level>{message}</level>"
                ),
            )
        ),
        log_rotation=str(logging_section.get("log_rotation", "5 MB")),
        log_retention=str(logging_section.get("log_retention", "30 days")),
        log_enqueue=bool(logging_section.get("log_enqueue", True)),
        log_backtrace=bool(logging_section.get("log_backtrace", True)),
        log_diagnose=bool(logging_section.get("log_diagnose", True)),
        write_log_file=bool(logging_section.get("write_log_file", True)),
        reset_log_on_start=bool(logging_section.get("reset_log_on_start", True)),
    )

    # Use literal defaults instead of class attributes to avoid dataclass
    # descriptor/member_descriptor issues and to keep parity with Config.
    camera_settings = CameraSettings(
        source=str(camera_section.get("source", "camera")),
        camera_index=int(camera_section.get("camera_index", 4)),
        rtsp_url=camera_section.get("rtsp_url", None),
        webrtc_url=camera_section.get("webrtc_url", None),
        resolution_width=int(camera_section.get("resolution_width", 1280)),
        resolution_height=int(camera_section.get("resolution_height", 720)),
        fps=int(camera_section.get("fps", 30)),
    )

    camera_credentials = CameraCredentials(
        # Use literal defaults instead of dataclass attribute descriptors to
        # avoid member_descriptor issues and to mirror legacy Config defaults.
        ip=str(camera_credentials_section.get("ip", "192.168.1.70")),
        user=str(camera_credentials_section.get("user", "admin")),
        password=str(
            camera_credentials_section.get("pass", "admin@123"),
        ),
    )

    detection_settings = DetectionSettings(
        confidence_threshold=float(
            detection_section.get("confidence_threshold", 0.3),
        ),
        model_path=str(
            detection_section.get(
                "model_path",
                "assets/models/yolo/roboflowaccurate.pt",
            ),
        ),
        target_labels=list(
            detection_section.get("target_labels", ["drone", "UAV"]),
        ),
        camera_credentials=camera_credentials,
    )

    ptz_settings = PTZSettings(
        ptz_movement_gain=float(
            ptz_control_section.get("ptz_movement_gain", 2.0),
        ),
        ptz_movement_threshold=float(
            ptz_control_section.get("ptz_movement_threshold", 0.05),
        ),
        zoom_target_coverage=float(
            ptz_control_section.get("zoom_target_coverage", 0.2),
        ),
        zoom_reset_timeout=float(
            ptz_control_section.get("zoom_reset_timeout", 2.0),
        ),
        zoom_min_interval=float(
            ptz_control_section.get("zoom_min_interval", 0.1),
        ),
        zoom_velocity_gain=float(
            ptz_control_section.get("zoom_velocity_gain", 2.0),
        ),
        zoom_reset_velocity=float(
            ptz_control_section.get("zoom_reset_velocity", 0.5),
        ),
        ptz_ramp_rate=float(
            ptz_control_section.get("ptz_ramp_rate", 0.2),
        ),
        no_detection_home_timeout=int(
            ptz_control_section.get("no_detection_home_timeout", 5),
        ),
        control_mode=str(ptz_control_section.get("control_mode", "onvif")),
    )

    performance_settings = PerformanceSettings(
        fps_window_size=int(
            performance_section.get("fps_window_size", 30),
        ),
        zoom_dead_zone=float(
            performance_section.get("zoom_dead_zone", 0.03),
        ),
        frame_queue_maxsize=int(
            performance_section.get("frame_queue_maxsize", 1),
        ),
    )

    simulator_settings = SimulatorSettings(
        # Keep raw YAML values for booleans here so that _validate_settings can
        # detect invalid/non-bool values and mirror legacy Config error behavior.
        use_ptz_simulation=ptz_simulator_section.get(
            "use_ptz_simulation",
            True,
        ),
        video_source=(
            str(ptz_simulator_section.get("video_source"))
            if ptz_simulator_section.get("video_source") is not None
            else "assets/videos/V_DRONE_045.mp4"
        ),
        video_loop=ptz_simulator_section.get(
            "video_loop",
            False,
        ),
        sim_viewport=ptz_simulator_section.get(
            "sim_viewport",
            True,
        ),
        sim_pan_step=float(
            ptz_simulator_section.get("sim_pan_step", 0.1),
        ),
        sim_tilt_step=float(
            ptz_simulator_section.get("sim_tilt_step", 0.1),
        ),
        sim_zoom_step=float(
            ptz_simulator_section.get("sim_zoom_step", 0.1),
        ),
        sim_zoom_min_scale=float(
            ptz_simulator_section.get("sim_zoom_min_scale", 0.3),
        ),
        sim_draw_original_viewport_box=ptz_simulator_section.get(
            "sim_draw_original_viewport_box",
            True,
        ),
    )

    tracking_settings = TrackingSettings(
        # Ultralytics YOLO Tracker Selection
        tracker_type=str(tracking_section.get("tracker_type", "botsort")),
    )

    octagon_credentials = OctagonCredentials(
        ip=str(octagon_credentials_section.get("ip", "192.168.1.123")),
        user=str(octagon_credentials_section.get("user", "admin")),
        password=str(octagon_credentials_section.get("pass", "!Inf2019")),
    )

    octagon_devices = OctagonDevices(
        pantilt_id=str(octagon_devices_section.get("pantilt_id", "pantilt")),
        visible_id=str(octagon_devices_section.get("visible_id", "visible1")),
    )

    settings = Settings(
        logging=logging_settings,
        camera=camera_settings,
        detection=detection_settings,
        ptz=ptz_settings,
        performance=performance_settings,
        simulator=simulator_settings,
        tracking=tracking_settings,
        octagon=octagon_credentials,
        octagon_devices=octagon_devices,
    )

    _validate_settings(settings)
    return settings


def _validate_settings(settings: Settings) -> None:
    """Validate a Settings instance.

    Mirrors the behavior of Config.validate() as closely as possible while using
    the new typed structure.
    """
    errors: list[str] = []

    # Detection: confidence threshold
    ct = settings.detection.confidence_threshold
    if not (0.0 <= ct <= 1.0):
        errors.append(
            f"confidence_threshold must be between 0.0 and 1.0, got {ct}",
        )

    # Camera resolution
    if settings.camera.resolution_width <= 0 or settings.camera.resolution_height <= 0:
        errors.append(
            "resolution_width/resolution_height must be positive integers, "
            f"got {settings.camera.resolution_width}x{settings.camera.resolution_height}",
        )

    # FPS
    if settings.camera.fps <= 0:
        errors.append(f"fps must be positive, got {settings.camera.fps}")

    # Camera source selection
    src_val = getattr(settings.camera, "source", "camera")
    if src_val not in ("camera", "video", "webrtc"):
        errors.append(
            f"camera.source must be 'camera', 'video', or 'webrtc', got '{src_val}'",
        )

    # Model path exists
    model_path = Path(settings.detection.model_path)
    if not model_path.exists():
        errors.append(f"Model file not found: {settings.detection.model_path}")

    # PTZ movement gain
    if settings.ptz.ptz_movement_gain < 0:
        errors.append(
            f"ptz_movement_gain must be positive, got {settings.ptz.ptz_movement_gain}",
        )

    # PTZ movement threshold
    if not (0.0 <= settings.ptz.ptz_movement_threshold <= 1.0):
        errors.append(
            "ptz_movement_threshold must be between 0.0 and 1.0, "
            f"got {settings.ptz.ptz_movement_threshold}",
        )

    # Zoom target coverage
    if not (0.0 <= settings.ptz.zoom_target_coverage <= 1.0):
        errors.append(
            "zoom_target_coverage must be between 0.0 and 1.0, "
            f"got {settings.ptz.zoom_target_coverage}",
        )

    # Zoom reset timeout / interval
    if settings.ptz.zoom_reset_timeout < 0:
        errors.append(
            "zoom_reset_timeout must be non-negative, "
            f"got {settings.ptz.zoom_reset_timeout}",
        )
    if settings.ptz.zoom_min_interval < 0:
        errors.append(
            "zoom_min_interval must be non-negative, "
            f"got {settings.ptz.zoom_min_interval}",
        )

    # Camera credentials
    creds = settings.detection.camera_credentials
    if not creds.ip:
        errors.append("camera_credentials.ip must be set")
    if not creds.user:
        errors.append("camera_credentials.user must be set")
    if not creds.password:
        errors.append("camera_credentials.pass must be set")

    # Performance
    if settings.performance.fps_window_size <= 0:
        errors.append(
            "fps_window_size must be positive, "
            f"got {settings.performance.fps_window_size}",
        )
    if settings.ptz.ptz_ramp_rate <= 0:
        errors.append(
            f"ptz_ramp_rate must be positive, got {settings.ptz.ptz_ramp_rate}",
        )

    # Simulator section
    sim = settings.simulator
    if not isinstance(sim.use_ptz_simulation, bool):
        errors.append(
            f"use_ptz_simulation must be bool, got {type(sim.use_ptz_simulation)}",
        )

    if sim.video_source is not None and not isinstance(sim.video_source, str):
        errors.append(
            f"video_source must be str or None, got {type(sim.video_source)}",
        )
    elif sim.video_source:
        video_path = Path(sim.video_source)
        if not video_path.exists():
            errors.append(f"VIDEO_SOURCE file not found: {sim.video_source}")

    for name, value in (
        ("video_loop", sim.video_loop),
        ("sim_viewport", sim.sim_viewport),
        ("sim_draw_original_viewport_box", sim.sim_draw_original_viewport_box),
    ):
        if not isinstance(value, bool):
            errors.append(f"{name} must be bool, got {type(value)}")

    if sim.sim_pan_step < 0:
        errors.append(f"sim_pan_step must be non-negative, got {sim.sim_pan_step}")
    if sim.sim_tilt_step < 0:
        errors.append(f"sim_tilt_step must be non-negative, got {sim.sim_tilt_step}")
    if sim.sim_zoom_step < 0:
        errors.append(
            f"sim_zoom_step must be non-negative, got {sim.sim_zoom_step}",
        )

    # Tracking section
    track = settings.tracking

    # Ultralytics YOLO Tracker validation
    # Detailed tracker parameters are validated by Ultralytics from config/trackers/*.yaml
    if track.tracker_type not in ("botsort", "bytetrack"):
        errors.append(
            f"tracker_type must be 'botsort' or 'bytetrack', got '{track.tracker_type}'"
        )

    # PTZ control mode
    if settings.ptz.control_mode not in ("onvif", "octagon"):
        errors.append(
            f"ptz.control_mode must be 'onvif' or 'octagon', got '{settings.ptz.control_mode}'"
        )
    if settings.ptz.control_mode == "octagon":
        oct = settings.octagon
        if not oct.ip:
            errors.append(
                "octagon_credentials.ip must be set when control_mode=octagon"
            )
        if not oct.user:
            errors.append(
                "octagon_credentials.user must be set when control_mode=octagon"
            )
        if not oct.password:
            errors.append(
                "octagon_credentials.pass must be set when control_mode=octagon"
            )
        devs = settings.octagon_devices
        if not devs.pantilt_id:
            errors.append(
                "octagon_devices.pantilt_id must be set when control_mode=octagon"
            )
        if not devs.visible_id:
            errors.append(
                "octagon_devices.visible_id must be set when control_mode=octagon"
            )

    if errors:
        raise SettingsValidationError(errors)
