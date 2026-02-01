from __future__ import annotations

import asyncio
import contextlib
import json
from typing import Any
from urllib.parse import urlparse

from aiohttp import WSCloseCode, WSMsgType, web
from loguru import logger

from src.api.session_manager import SessionManager
from src.api.settings_routes import (
    get_settings,
    get_settings_section,
    persist_settings,
    reload_session,
    reload_settings,
    update_settings,
    update_settings_section,
    validate_settings,
    get_available_cameras,
)
from src.api.model_routes import (
    activate_model,
    delete_model,
    get_model,
    list_models,
    reset_model,
    upload_model,
)


def _json_error(*, status: int, message: str) -> web.Response:
    return web.json_response({"error": message}, status=status)


def _session_view(session: Any, *, created: bool | None = None) -> dict[str, Any]:
    status = session.get_status()
    payload: dict[str, Any] = {
        "session_id": session.session_id,
        "camera_id": session.camera_id,
        "ws_path": f"/ws/sessions/{session.session_id}",
        **status,
    }
    if created is not None:
        payload["created"] = created
    return payload


def _is_allowed_origin(origin: str) -> bool:
    parsed = urlparse(origin)
    if parsed.scheme not in {"http", "https"}:
        return False
    if parsed.port is None:
        return False
    return parsed.port == 5173


def create_app(
    session_manager: SessionManager,
    settings_manager: Any,
    *,
    publish_hz: float = 10.0,
    auto_start_session: bool = True,
    camera_id: str | None = None,
) -> web.Application:
    @web.middleware
    async def cors_middleware(
        request: web.Request, handler: web.Handler
    ) -> web.StreamResponse:
        if request.method == "OPTIONS":
            response = web.Response(status=204)
        else:
            response = await handler(request)

        origin = request.headers.get("Origin")
        if origin and _is_allowed_origin(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
            response.headers["Access-Control-Allow-Methods"] = (
                "GET,POST,DELETE,PATCH,OPTIONS"
            )
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type,Authorization"
            )
            response.headers["Access-Control-Max-Age"] = "86400"

        return response

    app = web.Application(middlewares=[cors_middleware])
    app["session_manager"] = session_manager
    app["settings_manager"] = settings_manager
    app["publish_hz"] = float(publish_hz)
    app["auto_start_enabled"] = auto_start_session
    app["auto_start_camera_id"] = camera_id or "default"

    async def startup_handler(app: web.Application) -> None:
        """Auto-start WebRTC/camera connection on server startup if enabled."""
        if app.get("auto_start_enabled", False):
            camera_id_to_use = app.get("auto_start_camera_id", "default")
            logger.info(
                "Auto-starting WebRTC/camera connection for camera_id=%s",
                camera_id_to_use,
            )
            try:
                manager: SessionManager = app["session_manager"]
                result = manager.get_or_create_session(camera_id=camera_id_to_use)
                if result.created:
                    result.session.start()
                    logger.info(
                        "Auto-started session: session_id=%s, camera_id=%s",
                        result.session.session_id,
                        camera_id_to_use,
                    )
                else:
                    logger.info(
                        "Session already running: session_id=%s, camera_id=%s",
                        result.session.session_id,
                        camera_id_to_use,
                    )
                app["auto_start_session"] = result.session
            except Exception as exc:  # pragma: no cover
                logger.error("Failed to auto-start session: %s", exc)

    app.on_startup.append(startup_handler)

    async def healthz(_request: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    async def list_cameras(request: web.Request) -> web.Response:
        manager: SessionManager = request.app["session_manager"]
        return web.json_response(
            {"cameras": [{"camera_id": cid} for cid in manager.list_cameras()]}
        )

    async def create_session(request: web.Request) -> web.Response:
        manager: SessionManager = request.app["session_manager"]

        body: dict[str, Any] = {}
        if request.can_read_body:
            try:
                body = await request.json()
            except Exception:
                body = {}

        camera_id = body.get("camera_id")
        if camera_id is None:
            cameras = manager.list_cameras()
            if not cameras:
                return _json_error(status=404, message="No cameras configured")
            camera_id = cameras[0]

        if not isinstance(camera_id, str) or not camera_id:
            return _json_error(
                status=400, message="camera_id must be a non-empty string"
            )
        # Allow any camera ID to support dynamic selection from UI without config.yaml edits
        # if camera_id not in manager.list_cameras():
        #    return _json_error(status=404, message=f"Unknown camera_id: {camera_id}")

        result = manager.get_or_create_session(camera_id=camera_id)
        if result.created:
            result.session.start()
            return web.json_response(
                _session_view(result.session, created=True), status=201
            )
        return web.json_response(
            _session_view(result.session, created=False), status=200
        )

    async def get_session(request: web.Request) -> web.Response:
        manager: SessionManager = request.app["session_manager"]
        session_id = request.match_info["session_id"]
        session = manager.get_session(session_id)
        if session is None:
            return _json_error(status=404, message="Unknown session")
        return web.json_response(_session_view(session))

    async def delete_session(request: web.Request) -> web.Response:
        manager: SessionManager = request.app["session_manager"]
        session_id = request.match_info["session_id"]
        deleted = manager.delete_session(session_id)
        if not deleted:
            return _json_error(status=404, message="Unknown session")
        return web.json_response({"deleted": True, "session_id": session_id})

    async def ws_session(request: web.Request) -> web.StreamResponse:
        manager: SessionManager = request.app["session_manager"]
        settings_manager = request.app["settings_manager"]
        
        # Prefer settings from manager, fall back to app-wide constant from CLI
        settings = settings_manager.get_settings()
        hz = getattr(settings.performance, "publish_hz", float(request.app["publish_hz"]))
        publish_interval_s = 1.0 / max(0.1, hz)
        session_id = request.match_info["session_id"]
        session = manager.get_session(session_id)
        if session is None:
            return _json_error(status=404, message="Unknown session")

        ws = web.WebSocketResponse(heartbeat=30.0)
        await ws.prepare(request)

        async def publisher() -> None:
            last_sent_key: int | None = None
            last_event_seq: int | None = None
            while True:
                if ws.closed:
                    return

                tick = session.get_latest_tick()
                if tick is not None:
                    key = tick.get("ts_mono_ms") or tick.get("ts_unix_ms")
                    try:
                        key_i = int(key) if key is not None else None
                    except (TypeError, ValueError):
                        key_i = None

                    if key_i is None or key_i != last_sent_key:
                        try:
                            await asyncio.wait_for(ws.send_json(tick), timeout=1.0)
                        except TimeoutError:
                            await ws.close(
                                code=WSCloseCode.GOING_AWAY,
                                message=b"client too slow",
                            )
                            return
                        last_sent_key = key_i

                if hasattr(session, "get_events_since"):
                    last_event_seq, events = session.get_events_since(last_event_seq)
                    for event in events:
                        try:
                            await asyncio.wait_for(ws.send_json(event), timeout=1.0)
                        except TimeoutError:
                            await ws.close(
                                code=WSCloseCode.GOING_AWAY,
                                message=b"client too slow",
                            )
                            return

                await asyncio.sleep(publish_interval_s)

        pub_task = asyncio.create_task(publisher())
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        payload = json.loads(msg.data)
                    except json.JSONDecodeError:
                        await ws.send_json({"type": "error", "error": "invalid_json"})
                        continue

                    cmd_type = payload.get("type")
                    if cmd_type == "set_target_id":
                        target_id = payload.get("target_id")
                        if not isinstance(target_id, int):
                            await ws.send_json(
                                {"type": "error", "error": "target_id_must_be_int"}
                            )
                            continue
                        session.set_target_id(target_id)
                        await ws.send_json(
                            {
                                "type": "ack",
                                "command": "set_target_id",
                                "target_id": target_id,
                            }
                        )
                    elif cmd_type == "clear_target":
                        session.clear_target()
                        await ws.send_json({"type": "ack", "command": "clear_target"})
                    else:
                        await ws.send_json(
                            {"type": "error", "error": "unknown_command"}
                        )

                elif msg.type == WSMsgType.ERROR:
                    break
        finally:
            pub_task.cancel()
            with contextlib.suppress(Exception):
                await pub_task

        return ws

    async def get_global_tick(request: web.Request) -> web.Response:
        """Debug endpoint to get the latest tick from the first active session."""
        manager: SessionManager = request.app["session_manager"]
        # Find the first running session
        # We access the internal dictionary carefully
        if not manager._sessions_by_id:
             return _json_error(status=404, message="No active sessions")
        
        # Taking the most recently created one or just the first
        session = list(manager._sessions_by_id.values())[-1]
        tick = session.get_latest_tick()
        if tick is None:
             return web.json_response({"status": "no_tick_data", "camera_id": session.camera_id})
        
        return web.json_response(tick)

    app.router.add_get("/healthz", healthz)
    app.router.add_get("/cameras", list_cameras)
    app.router.add_post("/sessions", create_session)
    app.router.add_get("/sessions/{session_id}", get_session)
    app.router.add_delete("/sessions/{session_id}", delete_session)
    app.router.add_get("/ws/sessions/{session_id}", ws_session)

    # Debug routes
    app.router.add_get("/tick", get_global_tick)

    # Settings management routes
    app.router.add_get("/settings", get_settings)
    app.router.add_get("/settings/{section}", get_settings_section)
    app.router.add_patch("/settings", update_settings)
    app.router.add_patch("/settings/{section}", update_settings_section)
    app.router.add_post("/settings/validate", validate_settings)
    app.router.add_post("/settings/persist", persist_settings)
    app.router.add_post("/settings/reload", reload_settings)
    app.router.add_post("/settings/reload-session", reload_session)
    app.router.add_get("/settings/cameras", get_available_cameras)

    # Model management routes
    app.router.add_get("/models", list_models)
    app.router.add_get("/models/{model_name}", get_model)
    app.router.add_post("/models/upload", upload_model)
    app.router.add_delete("/models/{model_name}", delete_model)
    app.router.add_post("/models/{model_name}/activate", activate_model)
    app.router.add_post("/models/reset", reset_model)

    # ==============================================================================
    # OCTAGON COMPATIBILITY ROUTES
    # ==============================================================================
    async def get_visible_config(request: web.Request) -> web.Response:
        settings = settings_manager.get_settings()
        return web.json_response({"success": True, "data": settings.visible_detection.dict()})

    async def update_visible_config(request: web.Request) -> web.Response:
        data = await request.json()
        # Map Octagon config keys to internal settings if necessary, 
        # or just assume SkyShield sends matching keys because it was built for this.
        # SkyShield sends: { enabled: boolean, ... } which matches visible_detection.
        
        # We need to wrap it because update_settings_section expects just the fields
        try:
             # If SkyShield sends "data" wrapper, unwrap it (though usually client.ts sends body directly)
             payload = data
             settings_manager.update_section("visible_detection", payload)
             updated = settings_manager.get_settings().visible_detection.dict()
             return web.json_response({"success": True, "data": updated})
        except Exception as e:
             return _json_error(status=500, message=str(e))

    async def get_thermal_config(request: web.Request) -> web.Response:
        settings = settings_manager.get_settings()
        return web.json_response({"success": True, "data": settings.thermal_detection.dict()})

    async def update_thermal_config(request: web.Request) -> web.Response:
        data = await request.json()
        try:
             settings_manager.update_section("thermal_detection", data)
             updated = settings_manager.get_settings().thermal_detection.dict()
             return web.json_response({"success": True, "data": updated})
        except Exception as e:
             return _json_error(status=500, message=str(e))

    async def test_ptz_connection(request: web.Request) -> web.Response:
        data = await request.json()
        ip = data.get("ip")
        user = data.get("user")
        password = data.get("password")
        port = int(data.get("port", 80))

        if not ip or not user:
            return _json_error(status=400, message="Missing ip or user")

        # Logic copied from PTZService to handle WSDL path
        import sys
        from pathlib import Path
        try:
            from src.ptz_controller import get_onvif_camera
            onvif_camera_cls = get_onvif_camera()
            
            wsdl_dir = None
            if getattr(sys, "frozen", False):
                wsdl_dir = Path(sys._MEIPASS) / "wsdl"
            else:
                import onvif
                onvif_path = Path(onvif.__file__).parent
                if not (onvif_path / "wsdl").exists():
                    possible_wsdl = onvif_path.parent / "wsdl"
                    if possible_wsdl.exists():
                        wsdl_dir = possible_wsdl
            
            # Attempt connection
            cam = onvif_camera_cls(ip, port, user, password, wsdl_dir=str(wsdl_dir) if wsdl_dir else None)
            
            # Verify by creating media service and getting profiles
            await asyncio.to_thread(cam.update_xaddrs)
            # Creating ptz service doesn't guarantee connection, need a call
            # devicemgmt is created by default.
            
            # Simple check: get device information
            # resp = await asyncio.to_thread(cam.devicemgmt.GetDeviceInformation)
            # Actually update_xaddrs does GetCapabilities which is a good check.

            return web.json_response({"success": True, "message": "Connection successful"})
            
        except Exception as e:
            logger.error(f"Test PTZ connection failed: {e}")
            return _json_error(status=500, message=str(e))

    # Register routes
    app.router.add_post("/settings/test-ptz", test_ptz_connection)

    # Register compatibility routes
    # SkyShield client uses prefix defined in settingsStore.ts, default /api/devices
    
    # Visible
    app.router.add_get("/api/devices/visible/config", get_visible_config)
    app.router.add_post("/api/devices/visible/config", update_visible_config)
    app.router.add_get("/api/devices/visible", get_visible_config)

    # Alias for visible1 (SkyShield default)
    app.router.add_get("/api/devices/visible1/config", get_visible_config)
    app.router.add_post("/api/devices/visible1/config", update_visible_config)
    app.router.add_get("/api/devices/visible1", get_visible_config)

    # Thermal
    app.router.add_get("/api/devices/thermal/config", get_thermal_config)
    app.router.add_post("/api/devices/thermal/config", update_thermal_config)
    app.router.add_get("/api/devices/thermal", get_thermal_config)

    return app
