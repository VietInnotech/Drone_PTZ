from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from types import SimpleNamespace

import yaml
import pytest

from src.api.settings_manager import SettingsManager
from src.api import settings_routes
from src.api.settings_routes import persist_settings, update_settings_section
from src.settings import Settings


class DummyTransport:
    def get_extra_info(self, name: str) -> Any:
        if name == "peername":
            return ("127.0.0.1", 12345)
        return None


class DummyRequest:
    def __init__(
        self,
        app: dict[str, Any],
        *,
        json_body: dict[str, Any] | None = None,
        query: dict[str, str] | None = None,
        match_info: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.app = app
        self._json = json_body
        self.query = query or {}
        self.match_info = match_info or {}
        self.headers = headers or {"X-Forwarded-For": "127.0.0.1"}
        self.transport = DummyTransport()
        self.can_read_body = json_body is not None

    async def json(self) -> dict[str, Any]:
        return self._json or {}


def _build_app_state(tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    settings = Settings()
    settings_manager = SettingsManager(settings)
    config_path = tmp_path / "config.yaml"
    app_state: dict[str, Any] = {
        "settings_manager": settings_manager,
        "config_path": str(config_path),
    }
    return config_path, app_state


def test_quick_control_patch_autopersist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    async def _run() -> None:
        config_path, app_state = _build_app_state(tmp_path)
        async def _fake_fetch_camera_list(_base_url: str) -> list[Any]:
            return [SimpleNamespace(id=6)]

        monkeypatch.setattr(settings_routes, "fetch_camera_list", _fake_fetch_camera_list)

        request = DummyRequest(
            app_state,
            json_body={
                "enabled": True,
                "camera": {
                    "source": "skyshield",
                    "skyshield_camera_id": 6,
                },
            },
            query={"persist": "true"},
            match_info={"section": "visible_detection"},
            headers={"X-Forwarded-For": "127.0.0.10"},
        )
        response = await update_settings_section(request)
        assert response.status == 200
        payload = json.loads(response.text)
        assert payload.get("persisted") is True

        assert config_path.exists()
        saved = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert saved["visible_detection"]["enabled"] is True
        assert saved["visible_detection"]["camera"]["source"] == "skyshield"
        assert saved["visible_detection"]["camera"]["skyshield_camera_id"] == 6

    import asyncio
    asyncio.run(_run())


def test_settings_page_save_apply(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    async def _run() -> None:
        config_path, app_state = _build_app_state(tmp_path)
        async def _fake_fetch_camera_list(_base_url: str) -> list[Any]:
            return [SimpleNamespace(id=6)]

        monkeypatch.setattr(settings_routes, "fetch_camera_list", _fake_fetch_camera_list)

        update_request = DummyRequest(
            app_state,
            json_body={"enabled": True},
            match_info={"section": "visible_detection"},
            headers={"X-Forwarded-For": "127.0.0.20"},
        )
        response = await update_settings_section(update_request)
        assert response.status == 200
        assert not config_path.exists()

        persist_request = DummyRequest(
            app_state,
            json_body={"create_backup": False},
            headers={"X-Forwarded-For": "127.0.0.21"},
        )
        response = await persist_settings(persist_request)
        assert response.status == 200

        assert config_path.exists()
        saved = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert saved["visible_detection"]["enabled"] is True

    import asyncio
    asyncio.run(_run())


def test_quick_control_rejects_unknown_skyshield_camera(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _run() -> None:
        config_path, app_state = _build_app_state(tmp_path)

        async def _fake_fetch_camera_list(_base_url: str) -> list[Any]:
            return [SimpleNamespace(id=1)]

        monkeypatch.setattr(settings_routes, "fetch_camera_list", _fake_fetch_camera_list)

        request = DummyRequest(
            app_state,
            json_body={
                "enabled": True,
                "camera": {
                    "source": "skyshield",
                    "skyshield_camera_id": 6,
                },
            },
            query={"persist": "true"},
            match_info={"section": "visible_detection"},
            headers={"X-Forwarded-For": "127.0.0.30"},
        )
        response = await update_settings_section(request)
        assert response.status == 400
        payload = json.loads(response.text)
        assert "Unknown SkyShield camera id" in payload.get("error", "")
        assert not config_path.exists()

        settings_manager = app_state["settings_manager"]
        assert settings_manager.get_settings().visible_detection.enabled is False

    import asyncio
    asyncio.run(_run())
