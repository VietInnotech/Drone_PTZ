from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from aiohttp import web
from loguru import logger

from src.api.settings_manager import SettingsManager
from src.settings import Settings, SettingsValidationError


# Simple in-memory rate limiter
class RateLimiter:
    """Simple rate limiter for settings endpoints."""

    def __init__(self, max_requests: int = 1, window_seconds: float = 1.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(
            lambda: deque(maxlen=max_requests)
        )

    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed under rate limit."""
        now = time.time()
        requests = self._requests[client_id]

        # Remove old requests outside window
        while requests and requests[0] < now - self.window_seconds:
            requests.popleft()

        # Check if under limit
        if len(requests) >= self.max_requests:
            return False

        # Add current request
        requests.append(now)
        return True


# Global rate limiters for write operations
_update_rate_limiter = RateLimiter(max_requests=1, window_seconds=1.0)
_persist_rate_limiter = RateLimiter(max_requests=1, window_seconds=1.0)


def _settings_to_dict(
    settings: Settings, redact_passwords: bool = False
) -> dict[str, Any]:
    """Convert Settings to dict with optional password redaction.

    Args:
        settings: Settings object
        redact_passwords: If True, redact password fields

    Returns:
        Dictionary representation of settings
    """
    d = asdict(settings)
    if redact_passwords:
        if "detection" in d and "camera_credentials" in d["detection"]:
            if "password" in d["detection"]["camera_credentials"]:
                d["detection"]["camera_credentials"]["password"] = "***REDACTED***"
    return d


def _get_client_id(request: web.Request) -> str:
    """Get client identifier for rate limiting."""
    # Use X-Forwarded-For if behind proxy, otherwise use peername
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    peername = request.transport.get_extra_info("peername")
    if peername:
        return peername[0]
    return "unknown"


async def get_settings(request: web.Request) -> web.Response:
    """GET /settings - Retrieve all current runtime settings.

    Returns:
        JSON response with all settings (passwords redacted)
    """
    manager: SettingsManager = request.app["settings_manager"]
    settings = manager.get_settings()
    settings_dict = _settings_to_dict(settings, redact_passwords=True)
    return web.json_response(settings_dict)


async def get_settings_section(request: web.Request) -> web.Response:
    """GET /settings/{section} - Retrieve specific settings section.

    Args:
        section: Path parameter specifying the section name

    Returns:
        JSON response with section data or 404 error
    """
    manager: SettingsManager = request.app["settings_manager"]
    section = request.match_info["section"]

    try:
        section_data = manager.get_section(section)
        # Redact passwords in detection section
        if section == "detection" and "camera_credentials" in section_data:
            if "password" in section_data["camera_credentials"]:
                section_data["camera_credentials"]["password"] = "***REDACTED***"
        return web.json_response(section_data)
    except KeyError as e:
        settings = manager.get_settings()
        valid_sections = list(asdict(settings).keys())
        return web.json_response(
            {"error": str(e), "valid_sections": valid_sections}, status=404
        )


async def update_settings(request: web.Request) -> web.Response:
    """PATCH /settings - Update settings (partial update supported).

    Request body should be a JSON object with section names as keys.

    Returns:
        JSON response with updated settings or validation errors
    """
    manager: SettingsManager = request.app["settings_manager"]

    # Rate limiting
    client_id = _get_client_id(request)
    if not _update_rate_limiter.is_allowed(client_id):
        return web.json_response(
            {"error": "Rate limit exceeded. Max 1 request per second."}, status=429
        )

    # Parse request body
    try:
        updates = await request.json()
    except Exception as e:
        logger.warning(f"Invalid JSON in settings update: {e}")
        return web.json_response({"error": "Invalid JSON"}, status=400)

    if not isinstance(updates, dict):
        return web.json_response(
            {"error": "Request body must be a JSON object"}, status=400
        )

    # Apply updates
    try:
        new_settings = manager.update_settings(updates)
        updated_sections = list(updates.keys())
        return web.json_response(
            {
                "status": "updated",
                "updated_sections": updated_sections,
                "settings": _settings_to_dict(new_settings, redact_passwords=True),
            }
        )
    except SettingsValidationError as e:
        logger.warning(f"Settings validation failed: {e.errors}")
        return web.json_response(
            {"error": "Validation failed", "validation_errors": e.errors}, status=400
        )
    except ValueError as e:
        logger.warning(f"Invalid settings update: {e}")
        return web.json_response({"error": str(e)}, status=400)


async def update_settings_section(request: web.Request) -> web.Response:
    """PATCH /settings/{section} - Update specific section only.

    Args:
        section: Path parameter specifying the section name

    Returns:
        JSON response with updated settings or errors
    """
    manager: SettingsManager = request.app["settings_manager"]
    section = request.match_info["section"]

    # Rate limiting
    client_id = _get_client_id(request)
    if not _update_rate_limiter.is_allowed(client_id):
        return web.json_response(
            {"error": "Rate limit exceeded. Max 1 request per second."}, status=429
        )

    # Parse request body
    try:
        section_updates = await request.json()
    except Exception as e:
        logger.warning(f"Invalid JSON in section update: {e}")
        return web.json_response({"error": "Invalid JSON"}, status=400)

    if not isinstance(section_updates, dict):
        return web.json_response(
            {"error": "Request body must be a JSON object"}, status=400
        )

    # Wrap in section key
    updates = {section: section_updates}

    # Apply updates
    try:
        new_settings = manager.update_settings(updates)
        return web.json_response(
            {
                "status": "updated",
                "updated_sections": [section],
                "settings": _settings_to_dict(new_settings, redact_passwords=True),
            }
        )
    except SettingsValidationError as e:
        logger.warning(f"Settings validation failed: {e.errors}")
        return web.json_response(
            {"error": "Validation failed", "validation_errors": e.errors}, status=400
        )
    except ValueError as e:
        logger.warning(f"Invalid section update: {e}")
        return web.json_response({"error": str(e)}, status=400)


async def validate_settings(request: web.Request) -> web.Response:
    """POST /settings/validate - Validate proposed settings without applying.

    Request body should be a JSON object with proposed settings updates.

    Returns:
        JSON response with validation result
    """
    manager: SettingsManager = request.app["settings_manager"]

    # Parse request body
    try:
        updates = await request.json()
    except Exception as e:
        logger.warning(f"Invalid JSON in validation request: {e}")
        return web.json_response({"error": "Invalid JSON"}, status=400)

    if not isinstance(updates, dict):
        return web.json_response(
            {"error": "Request body must be a JSON object"}, status=400
        )

    # Try to merge and validate without applying
    try:
        current_settings = manager.get_settings()
        # Create a temporary manager to test the merge
        temp_manager = SettingsManager(current_settings)
        temp_manager.update_settings(updates)
        # If we get here, validation passed
        return web.json_response({"valid": True, "message": "All settings are valid"})
    except SettingsValidationError as e:
        return web.json_response({"valid": False, "validation_errors": e.errors})
    except ValueError as e:
        return web.json_response({"valid": False, "validation_errors": [str(e)]})


async def persist_settings(request: web.Request) -> web.Response:
    """POST /settings/persist - Write current runtime settings to config.yaml.

    Optional request body:
        {"create_backup": bool}  (default: true)

    Returns:
        JSON response with persist status or error
    """
    manager: SettingsManager = request.app["settings_manager"]

    # Rate limiting
    client_id = _get_client_id(request)
    if not _persist_rate_limiter.is_allowed(client_id):
        return web.json_response(
            {"error": "Rate limit exceeded. Max 1 request per second."}, status=429
        )

    # Parse optional request body
    create_backup = True
    if request.can_read_body:
        try:
            body = await request.json()
            if isinstance(body, dict):
                create_backup = body.get("create_backup", True)
        except Exception:
            pass

    # Get current settings
    settings = manager.get_settings()

    # Determine config path (project root)
    config_path = Path(__file__).parent.parent.parent / "config.yaml"

    try:
        # Create backup if requested
        backup_path = None
        if create_backup and config_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = config_path.with_suffix(f".yaml.backup.{timestamp}")
            backup_path.write_text(config_path.read_text(encoding="utf-8"))
            logger.info(f"Created backup: {backup_path}")

        # Convert settings to dict (without redaction for file)
        settings_dict = _settings_to_dict(settings, redact_passwords=False)

        # Normalize keys to match config.yaml expectations
        # - ptz_control is the canonical root key in config.yaml
        # - camera_credentials live at the root (not nested under detection)
        if "ptz" in settings_dict and "ptz_control" not in settings_dict:
            settings_dict["ptz_control"] = settings_dict.pop("ptz")

        detection_section = settings_dict.get("detection") or {}
        cam_creds = detection_section.pop("camera_credentials", None)
        if cam_creds is not None:
            settings_dict["camera_credentials"] = cam_creds

        # Write to temporary file first (atomic write)
        temp_path = config_path.with_suffix(".yaml.tmp")
        with temp_path.open("w", encoding="utf-8") as f:
            yaml.dump(
                settings_dict,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

        # Rename temp file to actual config (atomic on POSIX)
        temp_path.replace(config_path)
        logger.info(f"Settings persisted to: {config_path}")

        response = {
            "status": "persisted",
            "config_path": str(config_path),
        }
        if backup_path:
            response["backup_path"] = str(backup_path)

        return web.json_response(response)

    except Exception as e:
        logger.error(f"Failed to persist settings: {e}")
        return web.json_response(
            {"error": "Failed to write config file", "details": str(e)}, status=500
        )


async def reload_settings(request: web.Request) -> web.Response:
    """POST /settings/reload - Reload settings from config.yaml.

    Discards runtime changes and loads fresh from disk.

    Returns:
        JSON response with reloaded settings or error
    """
    manager: SettingsManager = request.app["settings_manager"]

    try:
        new_settings = manager.reload_from_disk()
        config_path = Path(__file__).parent.parent.parent / "config.yaml"

        return web.json_response(
            {
                "status": "reloaded",
                "config_path": str(config_path),
                "settings": _settings_to_dict(new_settings, redact_passwords=True),
            }
        )
    except SettingsValidationError as e:
        logger.error(f"Config file validation failed: {e.errors}")
        return web.json_response(
            {
                "error": "Config file validation failed",
                "validation_errors": e.errors,
            },
            status=400,
        )
    except Exception as e:
        logger.error(f"Failed to reload settings: {e}")
        return web.json_response(
            {"error": "Failed to reload settings", "details": str(e)}, status=500
        )
