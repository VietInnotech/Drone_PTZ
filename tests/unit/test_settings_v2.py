from pathlib import Path

import pytest
import yaml

from src.api.settings_manager import SettingsManager
from src.settings import SettingsValidationError, load_settings


MODEL_PATH = Path(__file__).parent.parent.parent / "assets/models/yolo/best5.pt"


def _write_config(tmp_path: Path, payload: dict) -> Path:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return config_path


def test_env_overrides_file(monkeypatch, tmp_path: Path) -> None:
    config = {
        "camera": {
            "source": "camera",
            "credentials_ip": "10.0.0.5",
        },
        "detection": {"model_path": str(MODEL_PATH)},
        "ptz": {"pid_kp": 1.0, "pid_ki": 0.2, "pid_kd": 0.5},
    }
    config_path = _write_config(tmp_path, config)

    monkeypatch.setenv("PTZ__PID_KP", "3.0")

    settings = load_settings(config_path)

    assert settings.ptz.pid_kp == 3.0
    assert settings.ptz.pid_ki == 0.2


def test_validation_negative_pid(tmp_path: Path) -> None:
    config = {
        "camera": {"source": "camera"},
        "detection": {"model_path": str(MODEL_PATH)},
        "ptz": {"pid_kp": -1},
    }
    config_path = _write_config(tmp_path, config)

    with pytest.raises(SettingsValidationError):
        load_settings(config_path)


def test_settings_manager_update_merges(tmp_path: Path) -> None:
    config = {
        "camera": {
            "source": "camera",
            "credentials_password": "admin@123",
        },
        "detection": {"model_path": str(MODEL_PATH)},
        "ptz": {"pid_kp": 1.0},
    }
    config_path = _write_config(tmp_path, config)

    settings = load_settings(config_path)
    manager = SettingsManager(settings)

    updated = manager.update_settings(
        {
            "ptz": {"pid_kp": 2.5},
            "camera": {"credentials_password": "new-pass"},
        }
    )

    assert updated.ptz.pid_kp == 2.5
    assert manager.get_settings().camera.credentials_password == "new-pass"
