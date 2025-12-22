import asyncio
from dataclasses import dataclass
from typing import Any

from aiohttp.test_utils import TestClient, TestServer

from src.api.app import create_app
from src.api.session_manager import SessionManager
from src.api.settings_manager import SettingsManager
from src.settings import load_settings


@dataclass
class FakeSession:
    session_id: str
    camera_id: str

    def __post_init__(self) -> None:
        self._running = False
        self.selected_target_id: int | None = None
        self._latest_tick: dict[str, Any] | None = None
        self._events: list[tuple[int, dict[str, Any]]] = []

    def start(self) -> None:
        self._running = True
        self._latest_tick = {
            "schema": "drone-ptz-metadata/1",
            "type": "metadata_tick",
            "session_id": self.session_id,
            "camera_id": self.camera_id,
            "ts_unix_ms": 1700000000000,
            "ts_mono_ms": 123,
            "space": "source",
            "frame_size": {"w": 1280, "h": 720},
            "selected_target_id": self.selected_target_id,
            "tracking_phase": "idle",
            "tracks": [],
        }
        self._events = [
            (
                1,
                {
                    "schema": "drone-ptz-metadata/1",
                    "type": "track_event",
                    "event": "new",
                    "session_id": self.session_id,
                    "camera_id": self.camera_id,
                    "ts_unix_ms": 1700000000000,
                    "before": None,
                    "after": {
                        "track_id": f"{self.camera_id}/7",
                        "id": 7,
                        "label": "drone",
                        "top_conf": 0.9,
                        "confirmed": True,
                        "start_ts_unix_ms": 1700000000000,
                        "end_ts_unix_ms": None,
                        "best_bbox": {"x": 0.1, "y": 0.2, "w": 0.1, "h": 0.1},
                    },
                },
            )
        ]

    def stop(self) -> None:
        self._running = False

    def is_running(self) -> bool:
        return self._running

    def set_target_id(self, target_id: int) -> None:
        self.selected_target_id = int(target_id)

    def clear_target(self) -> None:
        self.selected_target_id = None

    def get_latest_tick(self) -> dict[str, Any] | None:
        return self._latest_tick

    def get_events_since(
        self, last_seq: int | None
    ) -> tuple[int | None, list[dict[str, Any]]]:
        events = []
        max_seq = last_seq
        for seq, payload in self._events:
            if last_seq is not None and seq <= last_seq:
                continue
            events.append(payload)
            max_seq = seq if max_seq is None else max(max_seq, seq)
        return max_seq, events

    def get_status(self) -> dict[str, Any]:
        return {
            "running": self._running,
            "selected_target_id": self.selected_target_id,
            "tracking_phase": "idle",
            "last_tick_ts_unix_ms": self._latest_tick.get("ts_unix_ms")
            if self._latest_tick
            else None,
        }


def test_api_session_lifecycle() -> None:
    async def _run() -> None:
        def factory(
            session_id: str, camera_id: str, settings_manager: Any
        ) -> FakeSession:
            return FakeSession(session_id=session_id, camera_id=camera_id)

        settings = load_settings()
        settings_manager = SettingsManager(settings)
        manager = SessionManager(
            cameras=["cam_01"],
            session_factory=factory,
            settings_manager=settings_manager,
        )
        app = create_app(manager, settings_manager, publish_hz=50.0)

        async with TestServer(app) as server, TestClient(server) as client:
            resp = await client.get("/cameras")
            assert resp.status == 200
            cameras = await resp.json()
            assert cameras == {"cameras": [{"camera_id": "cam_01"}]}

            resp = await client.post("/sessions", json={})
            assert resp.status == 201
            created = await resp.json()
            session_id = created["session_id"]
            assert created["camera_id"] == "cam_01"
            assert created["created"] is True

            resp = await client.post("/sessions", json={"camera_id": "cam_01"})
            assert resp.status == 200
            reused = await resp.json()
            assert reused["created"] is False
            assert reused["session_id"] == session_id

            resp = await client.get(f"/sessions/{session_id}")
            assert resp.status == 200

            resp = await client.delete(f"/sessions/{session_id}")
            assert resp.status == 200
            deleted = await resp.json()
            assert deleted == {"deleted": True, "session_id": session_id}

            resp = await client.get(f"/sessions/{session_id}")
            assert resp.status == 404

    asyncio.run(_run())


def test_ws_sends_tick_and_accepts_commands() -> None:
    async def _run() -> None:
        def factory(
            session_id: str, camera_id: str, settings_manager: Any
        ) -> FakeSession:
            return FakeSession(session_id=session_id, camera_id=camera_id)

        settings = load_settings()
        settings_manager = SettingsManager(settings)
        manager = SessionManager(
            cameras=["cam_01"],
            session_factory=factory,
            settings_manager=settings_manager,
        )
        app = create_app(manager, settings_manager, publish_hz=100.0)

        async with TestServer(app) as server, TestClient(server) as client:
            resp = await client.post("/sessions", json={"camera_id": "cam_01"})
            session = await resp.json()
            session_id = session["session_id"]

            ws = await client.ws_connect(f"/ws/sessions/{session_id}")
            try:
                tick = await ws.receive_json(timeout=1)
                assert tick["type"] == "metadata_tick"
                assert tick["session_id"] == session_id

                event = await ws.receive_json(timeout=1)
                assert event["type"] == "track_event"
                assert event["event"] == "new"

                await ws.send_json({"type": "set_target_id", "target_id": 7})
                ack = await ws.receive_json(timeout=1)
                assert ack == {
                    "type": "ack",
                    "command": "set_target_id",
                    "target_id": 7,
                }
                sess = manager.get_session(session_id)
                assert isinstance(sess, FakeSession)
                assert sess.selected_target_id == 7

                await ws.send_json({"type": "clear_target"})
                ack = await ws.receive_json(timeout=1)
                assert ack == {"type": "ack", "command": "clear_target"}
                assert sess.selected_target_id is None
            finally:
                await ws.close()

    asyncio.run(_run())
