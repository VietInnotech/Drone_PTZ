from __future__ import annotations

import copy
import threading
from pathlib import Path

import pytest

from src.api.settings_manager import SettingsManager
from src.settings import SettingsValidationError, load_settings


@pytest.fixture
def settings_manager():
    """Fixture providing a fresh SettingsManager instance."""
    settings = load_settings()
    return SettingsManager(settings)


def test_settings_manager_get(settings_manager):
    """Test getting settings returns a copy."""
    settings1 = settings_manager.get_settings()
    settings2 = settings_manager.get_settings()

    # Should be equal but not the same object
    assert settings1.ptz.ptz_movement_gain == settings2.ptz.ptz_movement_gain
    assert settings1 is not settings2


def test_settings_manager_get_section(settings_manager):
    """Test getting specific section."""
    ptz_section = settings_manager.get_section("ptz")

    assert isinstance(ptz_section, dict)
    assert "ptz_movement_gain" in ptz_section
    assert "zoom_target_coverage" in ptz_section


def test_settings_manager_get_section_invalid(settings_manager):
    """Test getting invalid section raises KeyError."""
    with pytest.raises(KeyError) as excinfo:
        settings_manager.get_section("invalid_section")

    assert "Unknown section: invalid_section" in str(excinfo.value)


def test_settings_manager_update_valid(settings_manager):
    """Test updating with valid values."""
    updates = {"ptz": {"ptz_movement_gain": 1.5}}

    new_settings = settings_manager.update_settings(updates)

    assert new_settings.ptz.ptz_movement_gain == 1.5

    # Verify the change persisted
    retrieved = settings_manager.get_settings()
    assert retrieved.ptz.ptz_movement_gain == 1.5


def test_settings_manager_update_multiple_sections(settings_manager):
    """Test updating multiple sections at once."""
    updates = {
        "ptz": {"ptz_movement_gain": 2.0, "zoom_target_coverage": 0.25},
        "detection": {"confidence_threshold": 0.6},
    }

    new_settings = settings_manager.update_settings(updates)

    assert new_settings.ptz.ptz_movement_gain == 2.0
    assert new_settings.ptz.zoom_target_coverage == 0.25
    assert new_settings.detection.confidence_threshold == 0.6


def test_settings_manager_update_invalid(settings_manager):
    """Test updating with invalid values raises error."""
    updates = {"detection": {"confidence_threshold": 1.5}}

    with pytest.raises(SettingsValidationError) as excinfo:
        settings_manager.update_settings(updates)

    assert "confidence_threshold must be between 0.0 and 1.0" in str(excinfo.value)


def test_settings_manager_update_rollback_on_error(settings_manager):
    """Test that failed update doesn't modify settings."""
    original_threshold = settings_manager.get_settings().detection.confidence_threshold

    updates = {"detection": {"confidence_threshold": 99.0}}

    with pytest.raises(SettingsValidationError):
        settings_manager.update_settings(updates)

    # Settings should remain unchanged
    current = settings_manager.get_settings()
    assert current.detection.confidence_threshold == original_threshold


def test_settings_manager_update_unknown_section(settings_manager):
    """Test updating unknown section raises error."""
    updates = {"unknown_section": {"some_key": "value"}}

    with pytest.raises(ValueError) as excinfo:
        settings_manager.update_settings(updates)

    assert "Unknown section: unknown_section" in str(excinfo.value)


def test_settings_manager_update_nested(settings_manager):
    """Test updating nested camera credentials."""
    updates = {
        "detection": {
            "camera_credentials": {
                "ip": "192.168.1.100",
                "user": "newuser",
            }
        }
    }

    new_settings = settings_manager.update_settings(updates)

    assert new_settings.detection.camera_credentials.ip == "192.168.1.100"
    assert new_settings.detection.camera_credentials.user == "newuser"
    # Password should remain unchanged
    assert new_settings.detection.camera_credentials.password != ""


def test_settings_manager_thread_safety(settings_manager):
    """Test concurrent reads/writes are thread-safe."""
    results = []
    errors = []

    def reader():
        """Thread that reads settings repeatedly."""
        try:
            for _ in range(50):
                settings = settings_manager.get_settings()
                results.append(settings.ptz.ptz_movement_gain)
        except Exception as e:
            errors.append(e)

    def writer(value):
        """Thread that updates settings repeatedly."""
        try:
            for _ in range(10):
                updates = {"ptz": {"ptz_movement_gain": value}}
                settings_manager.update_settings(updates)
        except Exception as e:
            errors.append(e)

    # Start multiple reader and writer threads
    threads = []
    for i in range(3):
        t = threading.Thread(target=reader)
        threads.append(t)
        t.start()

    for i in range(2):
        t = threading.Thread(target=writer, args=(0.5 + i * 0.5,))
        threads.append(t)
        t.start()

    # Wait for all threads
    for t in threads:
        t.join()

    # No errors should have occurred
    assert len(errors) == 0

    # All results should be valid values
    assert len(results) > 0
    for value in results:
        assert isinstance(value, (int, float))
        assert value > 0


def test_settings_manager_reload_from_disk(settings_manager, tmp_path):
    """Test reloading settings from disk."""
    # Modify settings in memory
    updates = {"ptz": {"ptz_movement_gain": 99.0}}
    settings_manager.update_settings(updates)

    assert settings_manager.get_settings().ptz.ptz_movement_gain == 99.0

    # Reload from disk (uses default config.yaml)
    new_settings = settings_manager.reload_from_disk()

    # Should be back to file values (not 99.0)
    assert new_settings.ptz.ptz_movement_gain != 99.0


def test_settings_manager_deep_copy_isolation(settings_manager):
    """Test that returned settings are isolated from modifications."""
    settings = settings_manager.get_settings()
    original_gain = settings.ptz.ptz_movement_gain

    # Modify the returned object
    settings.ptz.ptz_movement_gain = 999.0

    # Manager's internal state should be unchanged
    current = settings_manager.get_settings()
    assert current.ptz.ptz_movement_gain == original_gain
    assert current.ptz.ptz_movement_gain != 999.0


def test_settings_manager_partial_update_preserves_others(settings_manager):
    """Test that partial updates don't affect unspecified fields."""
    original = settings_manager.get_settings()

    # Update only one field
    updates = {"ptz": {"ptz_movement_gain": 3.5}}
    settings_manager.update_settings(updates)

    current = settings_manager.get_settings()

    # Updated field should change
    assert current.ptz.ptz_movement_gain == 3.5

    # Other fields should remain unchanged
    assert current.ptz.zoom_target_coverage == original.ptz.zoom_target_coverage
    assert current.ptz.zoom_reset_timeout == original.ptz.zoom_reset_timeout
    assert (
        current.detection.confidence_threshold
        == original.detection.confidence_threshold
    )
