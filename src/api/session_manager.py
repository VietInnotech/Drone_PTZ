from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol


class Session(Protocol):
    session_id: str
    camera_id: str

    def start(self) -> None: ...

    def stop(self) -> None: ...

    def is_running(self) -> bool: ...

    def set_target_id(self, target_id: int) -> None: ...

    def clear_target(self) -> None: ...

    def get_latest_tick(self) -> dict[str, Any] | None: ...

    def get_events_since(
        self, last_seq: int | None
    ) -> tuple[int | None, list[dict[str, Any]]]: ...

    def get_status(self) -> dict[str, Any]: ...


@dataclass(frozen=True, slots=True)
class CreateSessionResult:
    session: Session
    created: bool


class SessionManager:
    def __init__(
        self,
        *,
        cameras: list[str],
        session_factory: Callable[[str, str, Any], Session],
        settings_manager: Any,
    ) -> None:
        self._cameras = list(cameras)
        self._session_factory = session_factory
        self._settings_manager = settings_manager
        self._lock = threading.Lock()
        self._sessions_by_id: dict[str, Session] = {}
        self._session_id_by_camera: dict[str, str] = {}

    def list_cameras(self) -> list[str]:
        return list(self._cameras)

    def get_session(self, session_id: str) -> Session | None:
        with self._lock:
            return self._sessions_by_id.get(session_id)

    def get_or_create_session(self, *, camera_id: str) -> CreateSessionResult:
        with self._lock:
            existing_id = self._session_id_by_camera.get(camera_id)
            if existing_id is not None:
                session = self._sessions_by_id[existing_id]
                return CreateSessionResult(session=session, created=False)

            session_id = f"session-{camera_id}-{int(time.time())}"
            session = self._session_factory(
                session_id, camera_id, self._settings_manager
            )
            self._sessions_by_id[session_id] = session
            self._session_id_by_camera[camera_id] = session_id
            return CreateSessionResult(session=session, created=True)

    def delete_session(self, session_id: str) -> bool:
        with self._lock:
            session = self._sessions_by_id.pop(session_id, None)
            if session is None:
                return False
            camera_id = session.camera_id
            if self._session_id_by_camera.get(camera_id) == session_id:
                self._session_id_by_camera.pop(camera_id, None)

        session.stop()
        return True
