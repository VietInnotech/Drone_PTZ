from __future__ import annotations

import asyncio
import contextlib
import json
from typing import Any
from urllib.parse import urlparse

from aiohttp import WSCloseCode, WSMsgType, web

from src.api.session_manager import SessionManager


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
    *,
    publish_hz: float = 10.0,
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
            response.headers["Access-Control-Allow-Methods"] = "GET,POST,DELETE,OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type,Authorization"
            )
            response.headers["Access-Control-Max-Age"] = "86400"

        return response

    app = web.Application(middlewares=[cors_middleware])
    app["session_manager"] = session_manager
    app["publish_hz"] = float(publish_hz)

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
        if camera_id not in manager.list_cameras():
            return _json_error(status=404, message=f"Unknown camera_id: {camera_id}")

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
        publish_interval_s = 1.0 / max(0.1, float(request.app["publish_hz"]))
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

    app.router.add_get("/healthz", healthz)
    app.router.add_get("/cameras", list_cameras)
    app.router.add_post("/sessions", create_session)
    app.router.add_get("/sessions/{session_id}", get_session)
    app.router.add_delete("/sessions/{session_id}", delete_session)
    app.router.add_get("/ws/sessions/{session_id}", ws_session)

    return app
