from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from src.api.app import create_app
from src.api.session import default_session_factory
from src.api.session_manager import SessionManager
from src.api.settings_manager import SettingsManager
from src.api import settings_routes
from src.settings import load_settings


class SettingsAPITestCase(AioHTTPTestCase):
    """Test suite for settings management API endpoints."""

    async def get_application(self) -> web.Application:
        """Create test application."""
        settings = load_settings()
        settings_manager = SettingsManager(settings)

        manager = SessionManager(
            cameras=["test_camera"],
            session_factory=default_session_factory,
            settings_manager=settings_manager,
        )

        app = create_app(manager, settings_manager, publish_hz=10.0)
        return app

    def setUp(self):
        """Reset rate limiters before each test."""
        super().setUp()
        # Reset global rate limiters for clean tests
        settings_routes._update_rate_limiter._requests.clear()
        settings_routes._persist_rate_limiter._requests.clear()

    @unittest_run_loop
    async def test_get_settings(self):
        """Test GET /settings endpoint."""
        resp = await self.client.request("GET", "/settings")
        assert resp.status == 200

        data = await resp.json()
        assert "ptz" in data
        assert "camera" in data
        assert "detection" in data
        assert "performance" in data
        assert "simulator" in data
        assert "logging" in data

    @unittest_run_loop
    async def test_get_settings_passwords_redacted(self):
        """Test that passwords are redacted in GET /settings."""
        resp = await self.client.request("GET", "/settings")
        assert resp.status == 200

        data = await resp.json()
        password = data["detection"]["camera_credentials"]["password"]
        assert password == "***REDACTED***"

    @unittest_run_loop
    async def test_get_settings_section_ptz(self):
        """Test GET /settings/ptz endpoint."""
        resp = await self.client.request("GET", "/settings/ptz")
        assert resp.status == 200

        data = await resp.json()
        assert "ptz_movement_gain" in data
        assert "zoom_target_coverage" in data
        assert "ptz_movement_threshold" in data

    @unittest_run_loop
    async def test_get_settings_section_camera(self):
        """Test GET /settings/camera endpoint."""
        resp = await self.client.request("GET", "/settings/camera")
        assert resp.status == 200

        data = await resp.json()
        assert "camera_index" in data
        assert "resolution_width" in data
        assert "resolution_height" in data
        assert "fps" in data

    @unittest_run_loop
    async def test_get_settings_section_detection(self):
        """Test GET /settings/detection endpoint."""
        resp = await self.client.request("GET", "/settings/detection")
        assert resp.status == 200

        data = await resp.json()
        assert "confidence_threshold" in data
        assert "model_path" in data
        assert "target_labels" in data
        # Password should be redacted in detection section too
        assert data["camera_credentials"]["password"] == "***REDACTED***"

    @unittest_run_loop
    async def test_get_settings_section_invalid(self):
        """Test GET /settings/{section} with invalid section."""
        resp = await self.client.request("GET", "/settings/invalid_section")
        assert resp.status == 404

        data = await resp.json()
        assert "error" in data
        assert "Unknown section" in data["error"]
        assert "valid_sections" in data

    @unittest_run_loop
    async def test_update_settings_single_field(self):
        """Test PATCH /settings with single field update."""
        updates = {"ptz": {"ptz_movement_gain": 2.5}}

        resp = await self.client.request("PATCH", "/settings", json=updates)
        assert resp.status == 200

        data = await resp.json()
        assert data["status"] == "updated"
        assert data["updated_sections"] == ["ptz"]
        assert data["settings"]["ptz"]["ptz_movement_gain"] == 2.5

    @unittest_run_loop
    async def test_update_settings_multiple_fields(self):
        """Test PATCH /settings with multiple field updates."""
        updates = {
            "ptz": {"ptz_movement_gain": 1.5, "zoom_target_coverage": 0.15},
            "detection": {"confidence_threshold": 0.5},
        }

        resp = await self.client.request("PATCH", "/settings", json=updates)
        assert resp.status == 200

        data = await resp.json()
        assert data["status"] == "updated"
        assert set(data["updated_sections"]) == {"ptz", "detection"}
        assert data["settings"]["ptz"]["ptz_movement_gain"] == 1.5
        assert data["settings"]["ptz"]["zoom_target_coverage"] == 0.15
        assert data["settings"]["detection"]["confidence_threshold"] == 0.5

    @unittest_run_loop
    async def test_update_settings_invalid_json(self):
        """Test PATCH /settings with invalid JSON."""
        resp = await self.client.request(
            "PATCH",
            "/settings",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status == 400

        data = await resp.json()
        assert "error" in data
        assert "Invalid JSON" in data["error"]

    @unittest_run_loop
    async def test_update_settings_validation_error(self):
        """Test PATCH /settings with invalid values."""
        updates = {"detection": {"confidence_threshold": 1.5}}

        resp = await self.client.request("PATCH", "/settings", json=updates)
        assert resp.status == 400

        data = await resp.json()
        assert data["error"] == "Validation failed"
        assert "validation_errors" in data
        assert len(data["validation_errors"]) > 0

    @unittest_run_loop
    async def test_update_settings_section(self):
        """Test PATCH /settings/{section} endpoint."""
        updates = {"ptz_movement_gain": 3.0, "zoom_target_coverage": 0.2}

        resp = await self.client.request("PATCH", "/settings/ptz", json=updates)
        assert resp.status == 200

        data = await resp.json()
        assert data["status"] == "updated"
        assert data["updated_sections"] == ["ptz"]
        assert data["settings"]["ptz"]["ptz_movement_gain"] == 3.0

    @unittest_run_loop
    async def test_update_settings_section_invalid(self):
        """Test PATCH /settings/{section} with invalid section."""
        updates = {"some_field": "value"}

        resp = await self.client.request(
            "PATCH", "/settings/invalid_section", json=updates
        )
        assert resp.status == 400

        data = await resp.json()
        assert "error" in data

    @unittest_run_loop
    async def test_validate_settings_valid(self):
        """Test POST /settings/validate with valid settings."""
        updates = {"ptz": {"ptz_movement_gain": 2.0}}

        resp = await self.client.request("POST", "/settings/validate", json=updates)
        assert resp.status == 200

        data = await resp.json()
        assert data["valid"] is True
        assert "message" in data

    @unittest_run_loop
    async def test_validate_settings_invalid(self):
        """Test POST /settings/validate with invalid settings."""
        updates = {"detection": {"confidence_threshold": 99.0}}

        resp = await self.client.request("POST", "/settings/validate", json=updates)
        assert resp.status == 200

        data = await resp.json()
        assert data["valid"] is False
        assert "validation_errors" in data
        assert len(data["validation_errors"]) > 0

    @unittest_run_loop
    async def test_validate_settings_does_not_apply(self):
        """Test that validate doesn't apply changes to runtime settings."""
        # First get current value
        get_resp = await self.client.request("GET", "/settings")
        original_gain = (await get_resp.json())["ptz"]["ptz_movement_gain"]

        # Validate a change
        updates = {"ptz": {"ptz_movement_gain": 5.0}}
        await self.client.request("POST", "/settings/validate", json=updates)

        # Check settings haven't changed
        get_resp = await self.client.request("GET", "/settings")
        current_gain = (await get_resp.json())["ptz"]["ptz_movement_gain"]
        assert current_gain == original_gain

    @unittest_run_loop
    async def test_reload_settings(self):
        """Test POST /settings/reload endpoint."""
        # First modify settings
        updates = {"ptz": {"ptz_movement_gain": 99.0}}
        await self.client.request("PATCH", "/settings", json=updates)

        # Verify change
        get_resp = await self.client.request("GET", "/settings")
        assert (await get_resp.json())["ptz"]["ptz_movement_gain"] == 99.0

        # Reload
        resp = await self.client.request("POST", "/settings/reload")
        assert resp.status == 200

        data = await resp.json()
        assert data["status"] == "reloaded"
        assert "config_path" in data
        assert "settings" in data

        # Value should be back to file value
        assert data["settings"]["ptz"]["ptz_movement_gain"] != 99.0

    @unittest_run_loop
    async def test_rate_limiting_updates(self):
        """Test rate limiting on PATCH /settings."""
        updates = {"ptz": {"ptz_movement_gain": 1.0}}

        # First request should succeed
        resp1 = await self.client.request("PATCH", "/settings", json=updates)
        assert resp1.status == 200

        # Second request immediately after should be rate limited
        resp2 = await self.client.request("PATCH", "/settings", json=updates)
        assert resp2.status == 429

        data = await resp2.json()
        assert "Rate limit exceeded" in data["error"]

    @unittest_run_loop
    async def test_update_nested_credentials(self):
        """Test updating nested camera credentials."""
        updates = {
            "detection": {
                "camera_credentials": {
                    "ip": "192.168.1.200",
                    "user": "testuser",
                }
            }
        }

        resp = await self.client.request("PATCH", "/settings", json=updates)
        assert resp.status == 200

        data = await resp.json()
        creds = data["settings"]["detection"]["camera_credentials"]
        assert creds["ip"] == "192.168.1.200"
        assert creds["user"] == "testuser"

    @unittest_run_loop
    async def test_multiple_sequential_updates(self):
        """Test multiple sequential updates."""
        # Update 1
        resp = await self.client.request(
            "PATCH", "/settings", json={"ptz": {"ptz_movement_gain": 1.5}}
        )
        assert resp.status == 200

        # Wait a bit for rate limiting window
        import asyncio

        await asyncio.sleep(1.1)

        # Update 2
        resp = await self.client.request(
            "PATCH", "/settings", json={"ptz": {"zoom_target_coverage": 0.18}}
        )
        assert resp.status == 200

        data = await resp.json()
        # First update should still be applied
        assert data["settings"]["ptz"]["ptz_movement_gain"] == 1.5
        # Second update should be applied too
        assert data["settings"]["ptz"]["zoom_target_coverage"] == 0.18

    @unittest_run_loop
    async def test_update_with_non_dict_body(self):
        """Test PATCH /settings with non-dict body."""
        resp = await self.client.request(
            "PATCH", "/settings", json=["not", "a", "dict"]
        )
        assert resp.status == 400

        data = await resp.json()
        assert "must be a JSON object" in data["error"]
