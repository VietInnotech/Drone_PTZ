from __future__ import annotations

import time
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from aiohttp import web
from loguru import logger

from src.api.settings_manager import SettingsManager
from src.api.skyshield_client import fetch_camera_list
from src.settings import Settings, SettingsError, SettingsValidationError, load_settings


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
    data = settings.model_dump(mode="python")

    if redact_passwords:
        # Redact Visible Camera credentials
        vis_cam = data.get("visible_detection", {}).get("camera", {})
        if vis_cam.get("credentials_password"):
            vis_cam["credentials_password"] = "***REDACTED***"

        # Redact Thermal Camera credentials
        therm_cam = data.get("thermal_detection", {}).get("camera", {})
        if therm_cam.get("credentials_password"):
            therm_cam["credentials_password"] = "***REDACTED***"

        # Redact Secondary Camera credentials
        sec_cam = data.get("secondary_detection", {}).get("camera", {})
        if sec_cam.get("credentials_password"):
            sec_cam["credentials_password"] = "***REDACTED***"

        octagon_section = data.get("octagon", {})
        if "password" in octagon_section:
            octagon_section["password"] = "***REDACTED***"

    return data


def _default_config_path() -> Path:
    root_dir = Path(__file__).parent.parent.parent
    candidates: list[Path] = []
    for candidate in ("config.yaml", "config.yml"):
        candidate_path = root_dir / candidate
        if candidate_path.exists():
            candidates.append(candidate_path)

    if candidates:
        return max(candidates, key=lambda p: p.stat().st_mtime)

    return root_dir / "config.yaml"


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _get_config_path(app: web.Application) -> Path:
    config_path = app.get("config_path")
    if config_path:
        return Path(config_path)
    return Path(__file__).parent.parent.parent / "config.yaml"


def _list_config_backups(config_path: Path) -> list[Path]:
    pattern = f"{config_path.name}.backup.*"
    backups = list(config_path.parent.glob(pattern))
    return sorted(backups, key=lambda path: path.stat().st_mtime, reverse=True)


def _prune_config_backups(config_path: Path, keep_last: int) -> list[Path]:
    if keep_last < 1:
        return []

    backups = _list_config_backups(config_path)
    to_remove = backups[keep_last:]
    removed: list[Path] = []
    for backup in to_remove:
        try:
            backup.unlink()
            removed.append(backup)
        except FileNotFoundError:
            continue
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(f"Failed to remove backup {backup}: {exc}")
    return removed


def _persist_settings_snapshot(
    settings: Settings, config_path: Path, *, create_backup: bool
) -> tuple[Path | None, list[Path]]:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path = None
    if create_backup and config_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = config_path.with_suffix(f".yaml.backup.{timestamp}")
        backup_path.write_text(config_path.read_text(encoding="utf-8"))
        logger.info(f"Created backup: {backup_path}")

    settings_dict = _settings_to_dict(settings, redact_passwords=False)

    temp_path = config_path.with_suffix(f"{config_path.suffix}.tmp")
    with temp_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(
            settings_dict,
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

    temp_path.replace(config_path)
    logger.info(f"Settings persisted to: {config_path}")

    removed: list[Path] = []
    if create_backup:
        removed = _prune_config_backups(config_path, keep_last=settings.backups.keep_last)
        if removed:
            logger.info(f"Pruned {len(removed)} config backup(s)")

    return backup_path, removed


async def _validate_skyshield_settings(settings: Settings) -> tuple[bool, str, int]:
    camera_ids: list[int] = []
    for cam in (
        settings.visible_detection.camera,
        settings.thermal_detection.camera,
        settings.secondary_detection.camera,
    ):
        if cam.source == "skyshield" and cam.skyshield_camera_id is not None:
            camera_ids.append(cam.skyshield_camera_id)

    if not camera_ids:
        return True, "", 200

    cameras = await fetch_camera_list(settings.skyshield.base_url)
    if not cameras:
        return False, "SkyShield camera list unavailable", 503

    available = {cam.id for cam in cameras}
    missing = sorted({cid for cid in camera_ids if cid not in available})
    if missing:
        return False, f"Unknown SkyShield camera id(s): {missing}", 400

    return True, "", 200


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
        # Redact passwords
        if section in ("visible_detection", "thermal_detection", "secondary_detection"):
            cam = section_data.get("camera", {})
            if cam.get("credentials_password"):
                cam["credentials_password"] = "***REDACTED***"
        elif section == "octagon" and "password" in section_data:
            section_data["password"] = "***REDACTED***"
        return web.json_response(section_data)
    except KeyError as e:
        settings = manager.get_settings()
        valid_sections = list(settings.model_dump(mode="python").keys())
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

    logger.info(f"Received settings update request: {updates}")

    persist = _parse_bool(request.query.get("persist"), default=False)
    validate_skyshield = _parse_bool(
        request.query.get("validate_skyshield"), default=persist
    )
    create_backup = _parse_bool(request.query.get("create_backup"), default=True)

    # Apply updates
    try:
        old_settings = manager.get_settings() if persist or validate_skyshield else None
        new_settings = manager.update_settings(updates)
        if validate_skyshield:
            ok, message, status = await _validate_skyshield_settings(new_settings)
            if not ok:
                if old_settings is not None:
                    manager.replace_settings(old_settings)
                return web.json_response(
                    {"error": message, "validation": "skyshield"}, status=status
                )
        backup_path = None
        config_path = None
        if persist:
            config_path = _get_config_path(request.app)
            try:
                backup_path, _ = _persist_settings_snapshot(
                    new_settings,
                    config_path,
                    create_backup=create_backup,
                )
            except Exception as exc:
                if old_settings is not None:
                    manager.replace_settings(old_settings)
                logger.error(f"Failed to persist settings: {exc}")
                return web.json_response(
                    {
                        "error": "Failed to persist settings",
                        "details": str(exc),
                        "rolled_back": True,
                    },
                    status=500,
                )
        updated_sections = list(updates.keys())
        response: dict[str, Any] = {
            "status": "updated",
            "updated_sections": updated_sections,
            "settings": _settings_to_dict(new_settings, redact_passwords=True),
        }
        if persist:
            response["persisted"] = True
            response["config_path"] = str(config_path)
            if backup_path:
                response["backup_path"] = str(backup_path)
        return web.json_response(response)
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

    persist = _parse_bool(request.query.get("persist"), default=False)
    validate_skyshield = _parse_bool(
        request.query.get("validate_skyshield"), default=persist
    )
    create_backup = _parse_bool(request.query.get("create_backup"), default=True)

    # Apply updates
    try:
        old_settings = manager.get_settings() if persist or validate_skyshield else None
        new_settings = manager.update_settings(updates)
        if validate_skyshield:
            ok, message, status = await _validate_skyshield_settings(new_settings)
            if not ok:
                if old_settings is not None:
                    manager.replace_settings(old_settings)
                return web.json_response(
                    {"error": message, "validation": "skyshield"}, status=status
                )
        backup_path = None
        config_path = None
        if persist:
            config_path = _get_config_path(request.app)
            try:
                backup_path, _ = _persist_settings_snapshot(
                    new_settings,
                    config_path,
                    create_backup=create_backup,
                )
            except Exception as exc:
                if old_settings is not None:
                    manager.replace_settings(old_settings)
                logger.error(f"Failed to persist settings: {exc}")
                return web.json_response(
                    {
                        "error": "Failed to persist settings",
                        "details": str(exc),
                        "rolled_back": True,
                    },
                    status=500,
                )
        response: dict[str, Any] = {
            "status": "updated",
            "updated_sections": [section],
            "settings": _settings_to_dict(new_settings, redact_passwords=True),
        }
        if persist:
            response["persisted"] = True
            response["config_path"] = str(config_path)
            if backup_path:
                response["backup_path"] = str(backup_path)
        return web.json_response(response)
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


async def get_available_cameras(request: web.Request) -> web.Response:
    """
    Fetch available cameras from SkyShield and local systems.
    
    This is used by the UI to auto-suggest camera sources.
    """
    manager: SettingsManager = request.app["settings_manager"]
    settings = manager.get_settings()
    
    # 1. Fetch from SkyShield
    skyshield_cameras = await fetch_camera_list(settings.skyshield.base_url)
    
    # 2. Local camera device scan (basic)
    # In a real environment, we'd use something more robust than just checking 0-5
    local_cameras = []
    import cv2
    for i in range(5):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            local_cameras.append(i)
            cap.release()

    return web.json_response({
        "success": True,
        "skyshield_cameras": [
            {
                "id": c.id,
                "name": f"Camera {c.id} ({c.ip_camera})",
                "ip": c.ip_camera,
                "rtsp_url": c.live_view
            } for c in skyshield_cameras
        ],
        "local_cameras": local_cameras,
        "current_config": {
            "visible": settings.visible_detection.camera.model_dump(),
            "thermal": settings.thermal_detection.camera.model_dump(),
            "secondary": settings.secondary_detection.camera.model_dump(),
        }
    })


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

    logger.info(f"Received persist settings request (backup={create_backup})")

    # Get current settings
    settings = manager.get_settings()

    config_path = _get_config_path(request.app)

    try:
        backup_path, _ = _persist_settings_snapshot(
            settings, config_path, create_backup=create_backup
        )
        response = {
            "status": "persisted",
            "config_path": str(config_path),
        }
        if backup_path:
            response["backup_path"] = str(backup_path)

        return web.json_response(response)

    except SettingsError as e:
        logger.error(f"Failed to persist settings: {e}")
        return web.json_response({"error": str(e)}, status=400)
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
        config_path = _get_config_path(request.app)
        new_settings = manager.reload_from_disk(config_path)

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


async def reload_session(request: web.Request) -> web.Response:
    """POST /settings/reload-session - Reload active session with current settings.

    This applies runtime changes to detection mode and camera settings
    without requiring a full service restart.

    Returns:
        JSON response with reload status for each active session
    """
    from src.api.session_manager import SessionManager
    
    settings_manager: SettingsManager = request.app["settings_manager"]
    session_manager: SessionManager = request.app["session_manager"]
    
    logger.info("Received session reload request")
    
    settings = settings_manager.get_settings()
    
    # Validate MediaMTX streams if WebRTC/SkyShield source
    sources_to_validate = []
    if settings.visible_detection.enabled:
        sources_to_validate.append(settings.visible_detection.camera)
    if settings.thermal_detection.enabled:
        sources_to_validate.append(settings.thermal_detection.camera)
    if settings.secondary_detection.enabled:
        sources_to_validate.append(settings.secondary_detection.camera)

    from src.stream_validator import validate_mediamtx_stream
    for cam_config in sources_to_validate:
        webrtc_url = None
        if cam_config.source == "webrtc":
            webrtc_url = cam_config.webrtc_url
        elif cam_config.source == "skyshield" and cam_config.skyshield_camera_id is not None:
             webrtc_url = f"{settings.skyshield.mediamtx_webrtc_base}/camera_{cam_config.skyshield_camera_id}/"
             
        if webrtc_url:
            is_valid, message = await validate_mediamtx_stream(webrtc_url)
            if not is_valid:
                return web.json_response(
                    {"error": f"Stream validation failed for {webrtc_url}", "details": message},
                    status=400
                )
    
    # Get all active sessions and reload them
    sessions_reloaded = []
    logger.info(f"Found {len(session_manager._sessions_by_id)} sessions in manager")
    for session_id, session in session_manager._sessions_by_id.items():
        if session.is_running():
            logger.info(f"Reloading active session: {session_id}")
            from src.detection_profiles import (
                resolve_profile,
                settings_for_profile,
            )  # noqa: PLC0415

            profile = resolve_profile(settings, session.camera_id)
            if profile is None:
                logger.warning(
                    "No active detection profile for camera_id={}, stopping session {}",
                    session.camera_id,
                    session_id,
                )
                session_manager.delete_session(session_id)
                sessions_reloaded.append(
                    {
                        "session_id": session_id,
                        "error": "No active detection profile for camera_id",
                    }
                )
                continue

            if profile.profile_id != session.detection_id:
                logger.info(
                    "Session {} switching detection_id from {} to {}",
                    session_id,
                    session.detection_id,
                    profile.profile_id,
                )
                session.detection_id = profile.profile_id

            result = session.reload_services(
                settings_for_profile(settings, profile.profile_id)
            )
            sessions_reloaded.append({
                "session_id": session_id,
                **result
            })
        else:
            logger.info(f"Session {session_id} is not running, skipping reload")
    
    return web.json_response({
        "status": "session_reload_complete",
        "sessions_reloaded": len(sessions_reloaded),
        "results": sessions_reloaded,
        "modes": {
            "visible": settings.visible_detection.enabled,
            "thermal": settings.thermal_detection.enabled,
            "secondary": settings.secondary_detection.enabled,
        }
    })
