from __future__ import annotations

import copy
import threading
from pathlib import Path
from typing import Any

from loguru import logger
from pydantic import ValidationError

from src.settings import Settings, SettingsValidationError, load_settings


def _format_validation_errors(exc: ValidationError) -> list[str]:
    messages: list[str] = []
    for err in exc.errors():
        loc = ".".join(str(part) for part in err.get("loc", ()))
        msg = err.get("msg", "invalid value")
        messages.append(f"{loc}: {msg}")
    return messages


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
            return self._settings.model_copy(deep=True)

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
            settings_dict = self._settings.model_dump(mode="python")
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
                new_settings = self._merge_updates(self._settings, updates)
                self._settings = new_settings
                logger.info("Settings updated successfully")
                return self._settings.model_copy(deep=True)
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
            return self._settings.model_copy(deep=True)

    def _merge_updates(self, current: Settings, updates: dict[str, Any]) -> Settings:
        """Deep merge updates into settings dataclasses.

        Args:
            current: Current Settings object
            updates: Dictionary with section updates

        Returns:
            New Settings object with merged updates
        """
        current_dict = current.model_dump(mode="python")

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
        try:
            return Settings(**data)
        except ValidationError as exc:
            raise SettingsValidationError(_format_validation_errors(exc)) from exc
