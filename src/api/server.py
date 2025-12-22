from __future__ import annotations

import argparse
import logging
from urllib.parse import urlparse

from aiohttp import web

from src.api.app import create_app
from src.api.session import default_session_factory
from src.api.session_manager import SessionManager
from src.settings import load_settings


def _derive_camera_id_from_settings() -> str:
    settings = load_settings()
    if settings.camera.source == "webrtc" and settings.camera.webrtc_url:
        parsed = urlparse(settings.camera.webrtc_url)
        parts = [p for p in parsed.path.split("/") if p]
        if parts:
            return str(parts[-1])
    return "default"


def main() -> None:
    parser = argparse.ArgumentParser(description="Drone PTZ analytics API server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--publish-hz", type=float, default=10.0)
    args = parser.parse_args()

    # aiohttp 3.13+ snapshots the access logger enabled state at handler init time.
    # If `aiohttp.access` is enabled later, aiohttp can attempt to log with a missing
    # start_time and raise `TypeError: float - NoneType`. Force it enabled up front.
    logging.getLogger("aiohttp.access").setLevel(logging.INFO)

    camera_id = _derive_camera_id_from_settings()

    manager = SessionManager(
        cameras=[camera_id], session_factory=default_session_factory
    )
    app = create_app(manager, publish_hz=args.publish_hz)
    web.run_app(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
