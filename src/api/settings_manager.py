from __future__ import annotations

import copy
import threading
from dataclasses import asdict, fields, is_dataclass, replace
from pathlib import Path
from typing import Any

from loguru import logger

from src.settings import (
    CameraCredentials,
    CameraSettings,
    DetectionSettings,
    LoggingSettings,
    OctagonCredentials,
    OctagonDevices,
    PerformanceSettings,
    PTZSettings,
    Settings,
    SettingsValidationError,
    SimulatorSettings,
    TrackingSettings,
    _validate_settings,
    load_settings,
)


class SettingsManager:
    """Thread-safe manager for runtime settings.

    Provides atomic read/write access to settings and validation.
    All methods are thread-safe and can be called from multiple threads.
    """

    def __init__(self, settings: Settings):
        """Initialize the settings manager.

        Args:
            settings: Initial settings object
        """
        self._lock = threading.RLock()
        self._settings = settings

    def get_settings(self) -> Settings:
        """Return a copy of current settings.

        Returns:
            A copy of the current Settings object
        """
        with self._lock:
            # Return a deep copy to prevent external modification
            return copy.deepcopy(self._settings)

    def get_section(self, section: str) -> dict[str, Any]:
        """Return specific section as dict.

        Args:
            section: Name of the section (logging, camera, detection, ptz, performance, simulator)

        Returns:
            Dictionary containing the section data

        Raises:
            KeyError: If section name is invalid
        """
        with self._lock:
            settings_dict = asdict(self._settings)
            if section not in settings_dict:
                valid_sections = list(settings_dict.keys())
                raise KeyError(
                    f"Unknown section: {section}. Valid sections: {valid_sections}"
                )
            return copy.deepcopy(settings_dict[section])

    def update_settings(self, updates: dict[str, Any]) -> Settings:
        """Apply partial updates and validate.

        Args:
            updates: Dictionary with section names as keys and update dicts as values

        Returns:
            Updated Settings object

        Raises:
            SettingsValidationError: If validation fails
        """
        with self._lock:
            old_settings = self._settings
            logger.info(f"Updating settings with: {updates}")

            try:
                # Deep merge updates into current settings
                new_settings = self._merge_updates(self._settings, updates)

                # Validate will raise if invalid
                _validate_settings(new_settings)

                # Apply
                self._settings = new_settings
                logger.info("Settings updated successfully")
                return copy.deepcopy(self._settings)
            except Exception:
                # Rollback on any error
                self._settings = old_settings
                raise

    def reload_from_disk(self, config_path: Path | None = None) -> Settings:
        """Reload settings from config.yaml.

        Args:
            config_path: Optional path to config file. If None, uses default location.

        Returns:
            Newly loaded Settings object

        Raises:
            SettingsValidationError: If loaded settings are invalid
        """
        with self._lock:
            logger.info(f"Reloading settings from disk: {config_path or 'default'}")
            new_settings = load_settings(config_path)
            self._settings = new_settings
            logger.info("Settings reloaded successfully")
            return copy.deepcopy(self._settings)

    def _merge_updates(self, current: Settings, updates: dict[str, Any]) -> Settings:
        """Deep merge updates into settings dataclasses.

        Args:
            current: Current Settings object
            updates: Dictionary with section updates

        Returns:
            New Settings object with merged updates
        """
        # Convert current settings to dict for merging
        current_dict = asdict(current)

        # Deep merge each section
        for section_name, section_updates in updates.items():
            if section_name not in current_dict:
                raise ValueError(
                    f"Unknown section: {section_name}. "
                    f"Valid sections: {list(current_dict.keys())}"
                )

            if not isinstance(section_updates, dict):
                raise ValueError(
                    f"Section updates must be a dict, got {type(section_updates)}"
                )

            # Merge the section
            current_section = current_dict[section_name]
            if isinstance(current_section, dict):
                current_dict[section_name] = self._deep_merge_dict(
                    current_section, section_updates
                )
            else:
                current_dict[section_name] = section_updates

        # Reconstruct Settings from merged dict
        return self._dict_to_settings(current_dict)

    def _deep_merge_dict(
        self, base: dict[str, Any], updates: dict[str, Any]
    ) -> dict[str, Any]:
        """Recursively merge updates into base dict.

        Args:
            base: Base dictionary
            updates: Updates to apply

        Returns:
            Merged dictionary
        """
        result = base.copy()
        for key, value in updates.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge_dict(result[key], value)
            else:
                result[key] = value
        return result

    def _dict_to_settings(self, data: dict[str, Any]) -> Settings:
        """Convert dictionary back to Settings dataclass.

        Args:
            data: Dictionary representation of settings

        Returns:
            Settings object

        Raises:
            ValueError: If data structure is invalid
        """
        # Reconstruct nested dataclasses
        logging_data = data.get("logging", {})
        logging_settings = LoggingSettings(**logging_data)

        camera_data = data.get("camera", {})
        camera_settings = CameraSettings(**camera_data)

        detection_data = data.get("detection", {})
        camera_creds_data = detection_data.get("camera_credentials", {})
        camera_credentials = CameraCredentials(**camera_creds_data)
        detection_settings = DetectionSettings(
            confidence_threshold=detection_data.get("confidence_threshold", 0.3),
            model_path=detection_data.get(
                "model_path", "assets/models/yolo/roboflowaccurate.pt"
            ),
            target_labels=detection_data.get("target_labels", ["drone", "UAV"]),
            camera_credentials=camera_credentials,
        )

        ptz_data = data.get("ptz", {})
        ptz_settings = PTZSettings(**ptz_data)

        performance_data = data.get("performance", {})
        performance_settings = PerformanceSettings(**performance_data)

        simulator_data = data.get("simulator", {})
        simulator_settings = SimulatorSettings(**simulator_data)

        tracking_data = data.get("tracking", {})
        tracking_settings = TrackingSettings(**tracking_data)

        # Octagon credentials and devices
        octagon_data = data.get("octagon_credentials", {})
        octagon_creds = OctagonCredentials(**octagon_data)

        octagon_devices_data = data.get("octagon_devices", {})
        octagon_devices = OctagonDevices(**octagon_devices_data)

        return Settings(
            logging=logging_settings,
            camera=camera_settings,
            detection=detection_settings,
            ptz=ptz_settings,
            performance=performance_settings,
            simulator=simulator_settings,
            tracking=tracking_settings,
            octagon=octagon_creds,
            octagon_devices=octagon_devices,
        )
