from __future__ import annotations

import argparse
import logging
import asyncio
from urllib.parse import urlparse

from aiohttp import web
from loguru import logger

from src.api.app import create_app
from src.api.session import default_session_factory
from src.api.session_manager import SessionManager
from src.api.settings_manager import SettingsManager
from src.detection_profiles import get_detection_profiles
from src.settings import load_settings


def _derive_camera_id_from_settings() -> str:
    settings = load_settings()
    # Use visible_detection camera as primary source for camera ID
    vis_cam = settings.visible_detection.camera
    if vis_cam.source == "webrtc" and vis_cam.webrtc_url:
        parsed = urlparse(vis_cam.webrtc_url)
        parts = [p for p in parsed.path.split("/") if p]
        if parts:
            return str(parts[-1])
    if vis_cam.source == "skyshield" and vis_cam.skyshield_camera_id:
        return f"camera_{vis_cam.skyshield_camera_id}"
    return "default"


def _derive_camera_ids_from_settings() -> list[str]:
    settings = load_settings()
    profiles = get_detection_profiles(settings)
    if profiles:
        return [profile.camera_id for profile in profiles]
    return [_derive_camera_id_from_settings()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Drone PTZ analytics API server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--publish-hz", type=float, default=10.0)
    parser.add_argument(
        "--auto-start",
        action="store_true",
        default=True,
        help="Automatically start WebRTC/camera connection on server startup (default: True)",
    )
    args = parser.parse_args()

    # aiohttp 3.13+ snapshots the access logger enabled state at handler init time.
    # If `aiohttp.access` is enabled later, aiohttp can attempt to log with a missing
    # start_time and raise `TypeError: float - NoneType`. Force it enabled up front.
    logging.getLogger("aiohttp.access").setLevel(logging.INFO)
    
    # Silence noisy aiortc/aioice logs unless at ERROR level
    logging.getLogger("aiortc").setLevel(logging.WARNING)
    logging.getLogger("aioice").setLevel(logging.WARNING)
    logging.getLogger("aiortc.codecs.h264").setLevel(logging.DEBUG)

    # Load initial settings and create manager
    settings = load_settings()
    settings_manager = SettingsManager(settings)

    camera_ids = _derive_camera_ids_from_settings()

    manager = SessionManager(
        cameras=camera_ids,
        session_factory=default_session_factory,
        settings_manager=settings_manager,
    )
    app = create_app(
        manager,
        settings_manager,
        publish_hz=args.publish_hz,
        auto_start_session=args.auto_start,
        camera_id=camera_ids[0] if camera_ids else None,
    )
    
    web.run_app(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
