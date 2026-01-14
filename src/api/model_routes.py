from __future__ import annotations

import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from aiohttp import web
from loguru import logger

from src.api.settings_manager import SettingsManager


def _get_models_dir() -> Path:
    """Get the models directory relative to project root."""
    root_dir = Path(__file__).parent.parent.parent
    models_dir = root_dir / "assets" / "models" / "yolo"
    return models_dir


def _get_model_metadata(path: Path) -> dict[str, Any]:
    """Extract metadata from a model file."""
    stat = path.stat()
    return {
        "name": path.name,
        "size_bytes": stat.st_size,
        "size_human": _human_size(stat.st_size),
        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "type": path.suffix.lower().lstrip("."),
    }


def _human_size(num: float, suffix: str = "B") -> str:
    """Convert bytes to human readable string."""
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


async def list_models(request: web.Request) -> web.Response:
    """GET /models - List available model files."""
    models_dir = _get_models_dir()
    if not models_dir.exists():
        return web.json_response({"models": [], "active_model": None})

    # Get active model path from settings
    settings_manager: SettingsManager = request.app["settings_manager"]
    settings = settings_manager.get_settings()
    active_model_path = Path(settings.detection.model_path).resolve()

    models = []
    active_model_name = None

    # Support both .pt and .onnx
    for ext in ("*.pt", "*.onnx"):
        for path in models_dir.glob(ext):
            if path.is_file():
                metadata = _get_model_metadata(path)
                # Mark if this is the active model
                if path.resolve() == active_model_path:
                    metadata["is_active"] = True
                    active_model_name = path.name
                else:
                    metadata["is_active"] = False
                models.append(metadata)

    # Sort by name
    models.sort(key=lambda x: x["name"])
    return web.json_response({"models": models, "active_model": active_model_name})


async def get_model(request: web.Request) -> web.Response:
    """GET /models/{model_name} - Get details for a specific model."""
    model_name = request.match_info["model_name"]
    models_dir = _get_models_dir()
    model_path = models_dir / model_name

    # Basic path traversal protection
    if not str(model_path.resolve()).startswith(str(models_dir.resolve())):
        return web.json_response({"error": "Invalid model name"}, status=400)

    if not model_path.exists() or not model_path.is_file():
        return web.json_response(
            {"error": f"Model not found: {model_name}"}, status=404
        )

    return web.json_response(_get_model_metadata(model_path))


async def upload_model(request: web.Request) -> web.Response:
    """POST /models/upload - Upload a new model file."""
    # Read multipart reader
    reader = await request.multipart()
    field = await reader.next()

    if field is None or field.name != "file":
        return web.json_response({"error": "No file field in request"}, status=400)

    filename = field.filename
    if not filename:
        return web.json_response({"error": "No filename provided"}, status=400)

    # Validate extension
    ext = Path(filename).suffix.lower()
    if ext not in (".pt", ".onnx"):
        return web.json_response(
            {"error": "Invalid file type. Only .pt and .onnx are allowed."}, status=400
        )

    # Sanitize filename (basic)
    filename = Path(filename).name
    models_dir = _get_models_dir()
    models_dir.mkdir(parents=True, exist_ok=True)
    temp_path = models_dir / f"{filename}.tmp"
    final_path = models_dir / filename

    try:
        size = 0
        with open(temp_path, "wb") as f:
            while True:
                chunk = await field.read_chunk()
                if not chunk:
                    break
                size += len(chunk)
                # Limit size to 200MB
                if size > 200 * 1024 * 1024:
                    f.close()
                    os.remove(temp_path)
                    return web.json_response(
                        {"error": "File too large (max 200MB)"}, status=413
                    )
                f.write(chunk)

        # Atomic move
        if temp_path.exists():
            temp_path.replace(final_path)

        logger.info(f"Model uploaded: {filename} ({size} bytes)")
        return web.json_response(
            {
                "status": "uploaded",
                "model": _get_model_metadata(final_path),
            },
            status=201,
        )

    except Exception as e:
        logger.error(f"Failed to upload model: {e}")
        if temp_path.exists():
            os.remove(temp_path)
        return web.json_response(
            {"error": "Internal server error during upload"}, status=500
        )


async def delete_model(request: web.Request) -> web.Response:
    """DELETE /models/{model_name} - Delete a model file."""
    model_name = request.match_info["model_name"]
    models_dir = _get_models_dir()
    model_path = models_dir / model_name

    # Basic path traversal protection
    if not str(model_path.resolve()).startswith(str(models_dir.resolve())):
        return web.json_response({"error": "Invalid model name"}, status=400)

    if not model_path.exists() or not model_path.is_file():
        return web.json_response(
            {"error": f"Model not found: {model_name}"}, status=404
        )

    # Check if this is the active model
    settings_manager: SettingsManager = request.app["settings_manager"]
    settings = settings_manager.get_settings()
    active_model_path = Path(settings.detection.model_path)

    if model_path.resolve() == active_model_path.resolve():
        return web.json_response(
            {"error": "Cannot delete the currently active model"}, status=403
        )

    try:
        os.remove(model_path)
        logger.info(f"Model deleted: {model_name}")
        return web.json_response({"status": "deleted", "model_name": model_name})
    except Exception as e:
        logger.error(f"Failed to delete model {model_name}: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def activate_model(request: web.Request) -> web.Response:
    """POST /models/{model_name}/activate - Set a model as the active detection model."""
    model_name = request.match_info["model_name"]
    models_dir = _get_models_dir()
    model_path = models_dir / model_name

    # Basic path traversal protection
    if not str(model_path.resolve()).startswith(str(models_dir.resolve())):
        return web.json_response({"error": "Invalid model name"}, status=400)

    if not model_path.exists() or not model_path.is_file():
        return web.json_response(
            {"error": f"Model not found: {model_name}"}, status=404
        )

    # Update settings
    settings_manager: SettingsManager = request.app["settings_manager"]
    relative_path = os.path.relpath(model_path, Path(__file__).parent.parent.parent)

    try:
        settings_manager.update_settings({"detection": {"model_path": relative_path}})
        logger.info(f"Model activated: {relative_path}")
        return web.json_response(
            {
                "status": "activated",
                "model_path": relative_path,
                "model_name": model_name,
            }
        )
    except Exception as e:
        logger.error(f"Failed to activate model {model_name}: {e}")
        return web.json_response({"error": str(e)}, status=400)


async def reset_model(request: web.Request) -> web.Response:
    """POST /models/reset - Reset detection settings to default."""
    settings_manager: SettingsManager = request.app["settings_manager"]
    
    # Default detection settings
    default_settings = {
        "detection": {
            "confidence_threshold": 0.3,
            "model_path": "assets/models/yolo/best5.pt",
            "target_labels": ["drone", "UAV"],
        }
    }

    try:
        settings_manager.update_settings(default_settings)
        logger.info("Detection settings reset to defaults")
        return web.json_response(
            {
                "status": "reset",
                "settings": default_settings["detection"],
                "message": "Detection settings reset to defaults",
            }
        )
    except Exception as e:
        logger.error(f"Failed to reset detection settings: {e}")
        return web.json_response({"error": str(e)}, status=400)
