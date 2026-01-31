from __future__ import annotations

from pathlib import Path

import pytest

from src.settings import (
    LoggingSettings,
    Settings,
    SettingsValidationError,
    TrackingConfig,
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
    assert settings.visible_detection is not None
    assert settings.thermal_detection is not None
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

    # Spot-check critical defaults
    assert settings.logging == LoggingSettings()
    assert settings.visible_detection.enabled is True
    assert settings.visible_detection.confidence_threshold == 0.35
    assert settings.thermal_detection.enabled is False

    assert settings.ptz.ptz_movement_gain == 2.0
    assert settings.performance.fps_window_size == 30
    assert settings.simulator.use_ptz_simulation is True


def test_invalid_confidence_threshold_raises(tmp_path: Path) -> None:
    config_path = _write_yaml(
        tmp_path,
        """
visible_detection:
  confidence_threshold: 2.0
""",
    )

    with pytest.raises(SettingsValidationError) as exc:
        load_settings(config_path)

    msg = "\n".join(exc.value.errors)
    assert "visible_detection.confidence_threshold" in msg or "confidence_threshold" in msg
    assert "less than or equal to 1" in msg


def test_invalid_camera_resolution_raises(tmp_path: Path) -> None:
    config_path = _write_yaml(
        tmp_path,
        """
visible_detection:
  camera:
    resolution_width: 0
    resolution_height: -1
""",
    )

    with pytest.raises(SettingsValidationError) as exc:
        load_settings(config_path)

    msg = "\n".join(exc.value.errors)
    assert "resolution_width" in msg
    assert "greater than 0" in msg
    assert "resolution_height" in msg


def test_invalid_fps_raises(tmp_path: Path) -> None:
    config_path = _write_yaml(
        tmp_path,
        """
visible_detection:
  camera:
    fps: 0
""",
    )

    with pytest.raises(SettingsValidationError) as exc:
        load_settings(config_path)

    msg = "\n".join(exc.value.errors)
    assert "fps" in msg
    assert "greater than 0" in msg


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
    assert "simulator.sim_draw_original_viewport_box" in msg
    assert "simulator.sim_pan_step" in msg
    assert "greater than or equal to 0" in msg
    assert "simulator.sim_tilt_step" in msg
    assert "simulator.sim_zoom_step" in msg


def test_tracking_settings_defaults(tmp_path: Path) -> None:
    """Test that tracking settings use correct defaults."""
    config_path = tmp_path / "config.yaml"
    settings = load_settings(config_path)

    assert isinstance(settings.tracking, TrackingConfig)
    # Verify priority is a valid value (visible or thermal)
    assert settings.tracking.priority in ("visible", "thermal")


def test_tracking_settings_custom_values(tmp_path: Path) -> None:
    """Test loading custom tracking settings."""
    config_path = _write_yaml(
        tmp_path,
        """
tracking:
  priority: thermal
""",
    )

    settings = load_settings(config_path)

    assert settings.tracking.priority == "thermal"


def test_camera_conflict_validation() -> None:
    """Test that using the same camera for both visible and thermal raises an error."""
    with pytest.raises(ValueError) as exc:
        Settings(
            visible_detection={
                "enabled": True,
                "camera": {"camera_index": 0},
            },
            thermal_detection={
                "enabled": True,
                "camera": {"camera_index": 0},
            },
        )
    
    assert "Camera conflict" in str(exc.value)


def test_no_conflict_when_different_cameras() -> None:
    """Test that different cameras for visible and thermal works fine."""
    settings = Settings(
        visible_detection={
            "enabled": True,
            "camera": {"camera_index": 0},
        },
        thermal_detection={
            "enabled": True,
            "camera": {"camera_index": 1},
        },
    )
    assert settings.visible_detection.camera.camera_index == 0
    assert settings.thermal_detection.camera.camera_index == 1
