from __future__ import annotations

from pathlib import Path

import pytest

from src.settings import (
    LoggingSettings,
    Settings,
    SettingsValidationError,
    TrackingSettings,
    load_settings,
)


def _write_yaml(tmp_path: Path, content: str) -> Path:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(content, encoding="utf-8")
    return config_path


def test_load_settings_with_project_config_yaml_loads_successfully(
    tmp_path: Path,
) -> None:
    # Use the real repo config.yaml as source-of-truth for this test.
    project_root = Path(__file__).parents[2]
    repo_config = project_root / "config.yaml"
    assert repo_config.exists(), "Expected config.yaml at project root"

    tmp_config = tmp_path / "config.yaml"
    tmp_config.write_text(repo_config.read_text(encoding="utf-8"), encoding="utf-8")

    settings = load_settings(tmp_config)

    # Verify settings loaded successfully with expected structure
    assert isinstance(settings, Settings)
    assert settings.logging is not None
    assert settings.camera is not None
    assert settings.detection is not None
    assert settings.ptz is not None
    assert settings.performance is not None
    assert settings.simulator is not None
    assert settings.tracking is not None


def test_load_settings_missing_config_uses_defaults(tmp_path: Path) -> None:
    # No config.yaml in tmp_path: load_settings should fall back to defaults.
    config_path = tmp_path / "config.yaml"
    assert not config_path.exists()

    settings = load_settings(config_path)

    assert isinstance(settings, Settings)

    # Spot-check critical defaults (mirroring Config)
    assert settings.logging == LoggingSettings()
    assert settings.camera.camera_index == 4
    assert settings.camera.resolution_width == 1280
    assert settings.camera.resolution_height == 720
    assert settings.camera.fps == 30

    assert settings.detection.confidence_threshold == 0.3
    assert settings.detection.model_path == "assets/models/yolo/best5.pt"

    assert settings.ptz.ptz_movement_gain == 2.0
    assert settings.performance.fps_window_size == 30
    assert settings.simulator.use_ptz_simulation is True


def test_invalid_confidence_threshold_raises(tmp_path: Path) -> None:
    config_path = _write_yaml(
        tmp_path,
        """
detection:
  confidence_threshold: 2.0
""",
    )

    with pytest.raises(SettingsValidationError) as exc:
        load_settings(config_path)

    msg = "\n".join(exc.value.errors)
    assert "detection.confidence_threshold" in msg
    assert "less than or equal to 1" in msg


def test_invalid_camera_resolution_raises(tmp_path: Path) -> None:
    config_path = _write_yaml(
        tmp_path,
        """
camera:
  resolution_width: 0
  resolution_height: -1
""",
    )

    with pytest.raises(SettingsValidationError) as exc:
        load_settings(config_path)

    msg = "\n".join(exc.value.errors)
    assert "camera.resolution_width" in msg
    assert "greater than 0" in msg
    assert "camera.resolution_height" in msg


def test_invalid_fps_raises(tmp_path: Path) -> None:
    config_path = _write_yaml(
        tmp_path,
        """
camera:
  fps: 0
""",
    )

    with pytest.raises(SettingsValidationError) as exc:
        load_settings(config_path)

    msg = "\n".join(exc.value.errors)
    assert "camera.fps" in msg
    assert "greater than 0" in msg


def test_invalid_camera_credentials_raises(tmp_path: Path) -> None:
    config_path = _write_yaml(
        tmp_path,
        """
camera:
    credentials_ip: ""
    credentials_user: ""
    credentials_password: ""
""",
    )

    with pytest.raises(SettingsValidationError) as exc:
        load_settings(config_path)

    msg = "\n".join(exc.value.errors)
    assert "camera.credentials_ip" in msg
    assert "credentials_ip must be set" in msg
    assert "camera.credentials_user" in msg
    assert "credentials_user must be set" in msg
    assert "camera.credentials_password" in msg
    assert "credentials_password must be set" in msg


def test_invalid_simulator_settings_types_and_ranges(tmp_path: Path) -> None:
    config_path = _write_yaml(
        tmp_path,
        """
simulator:
  use_ptz_simulation: "yes"
  video_loop: "no"
  sim_viewport: "maybe"
  sim_draw_original_viewport_box: "box"
  sim_pan_step: -0.1
  sim_tilt_step: -0.2
  sim_zoom_step: -0.3
""",
    )

    with pytest.raises(SettingsValidationError) as exc:
        load_settings(config_path)

    msg = "\n".join(exc.value.errors)
    assert "simulator.sim_viewport" in msg
    assert "valid boolean" in msg
    assert "simulator.sim_viewport" in msg
    assert "simulator.sim_draw_original_viewport_box" in msg
    assert "simulator.sim_pan_step" in msg
    assert "greater than or equal to 0" in msg
    assert "simulator.sim_tilt_step" in msg
    assert "simulator.sim_zoom_step" in msg


def test_model_path_must_exist(tmp_path: Path) -> None:
    config_path = _write_yaml(
        tmp_path,
        """
detection:
  model_path: "does/not/exist.pt"
""",
    )

    with pytest.raises(SettingsValidationError) as exc:
        load_settings(config_path)

    assert "Model file not found: does/not/exist.pt" in "\n".join(exc.value.errors)


def test_tracking_settings_defaults(tmp_path: Path) -> None:
    """Test that tracking settings use correct defaults."""
    config_path = tmp_path / "config.yaml"
    settings = load_settings(config_path)

    assert isinstance(settings.tracking, TrackingSettings)
    assert settings.tracking.tracker_type == "botsort"


def test_tracking_settings_custom_values(tmp_path: Path) -> None:
    """Test loading custom tracking settings."""
    config_path = _write_yaml(
        tmp_path,
        """
tracking:
  tracker_type: bytetrack
""",
    )

    settings = load_settings(config_path)

    assert settings.tracking.tracker_type == "bytetrack"
