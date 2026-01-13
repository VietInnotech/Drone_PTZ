from __future__ import annotations

import io
import os
import shutil
from pathlib import Path

import pytest
from aiohttp import web, FormData
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from src.api.app import create_app
from src.api.session import default_session_factory
from src.api.session_manager import SessionManager
from src.api.settings_manager import SettingsManager
from src.api import settings_routes
from src.settings import load_settings


class ModelAPITestCase(AioHTTPTestCase):
    """Test suite for model management API endpoints."""

    async def get_application(self) -> web.Application:
        """Create test application."""
        self.root_dir = Path(__file__).parent.parent.parent
        self.models_dir = self.root_dir / "assets" / "models" / "yolo"
        self.models_dir.mkdir(parents=True, exist_ok=True)

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
        super().setUp()
        self.test_files = []

    def tearDown(self):
        for f in self.test_files:
            if os.path.exists(f):
                os.remove(f)
        super().tearDown()

    @unittest_run_loop
    async def test_list_models(self):
        """Test GET /models endpoint."""
        resp = await self.client.request("GET", "/models")
        assert resp.status == 200
        data = await resp.json()
        assert "models" in data
        assert isinstance(data["models"], list)

    @unittest_run_loop
    async def test_upload_and_get_model(self):
        """Test POST /models/upload and GET /models/{name}."""
        filename = "test_test_test.pt"
        content = b"fake model content"
        
        data = FormData()
        data.add_field("file", content, filename=filename, content_type="application/octet-stream")

        resp = await self.client.request("POST", "/models/upload", data=data)
        assert resp.status == 201
        
        test_data = await resp.json()
        assert test_data["status"] == "uploaded"
        assert test_data["model"]["name"] == filename
        
        self.test_files.append(self.models_dir / filename)

        # GET detail
        resp = await self.client.request("GET", f"/models/{filename}")
        assert resp.status == 200
        data = await resp.json()
        assert data["name"] == filename

    @unittest_run_loop
    async def test_upload_invalid_extension(self):
        """Test uploading file with invalid extension."""
        data = FormData()
        data.add_field("file", b"fake content", filename="test.txt")

        resp = await self.client.request("POST", "/models/upload", data=data)
        assert resp.status == 400
        data = await resp.json()
        assert "Only .pt and .onnx are allowed" in data["error"]

    @unittest_run_loop
    async def test_get_model_not_found(self):
        """Test GET /models/non_existent.pt."""
        resp = await self.client.request("GET", "/models/non_existent_12345.pt")
        assert resp.status == 404

    @unittest_run_loop
    async def test_activate_model(self):
        """Test POST /models/{name}/activate."""
        filename = "test_activate.pt"
        content = b"fake content"
        (self.models_dir / filename).write_bytes(content)
        self.test_files.append(self.models_dir / filename)

        resp = await self.client.request("POST", f"/models/{filename}/activate")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "activated"
        assert data["model_name"] == filename

        # Verify in settings
        resp = await self.client.request("GET", "/settings/detection")
        settings_data = await resp.json()
        assert settings_data["model_path"].endswith(filename)

    @unittest_run_loop
    async def test_delete_model(self):
        """Test DELETE /models/{name}."""
        filename = "test_delete.pt"
        content = b"fake content"
        (self.models_dir / filename).write_bytes(content)
        
        resp = await self.client.request("DELETE", f"/models/{filename}")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "deleted"
        assert not (self.models_dir / filename).exists()

    @unittest_run_loop
    async def test_delete_active_model_blocked(self):
        """Test that deleting the active model is blocked."""
        # 1. Get current active model
        resp = await self.client.request("GET", "/settings/detection")
        curr_settings = await resp.json()
        active_path = Path(curr_settings["model_path"])
        active_name = active_path.name
        
        # Ensure it exists (it should in assets/models/yolo/)
        if not (self.models_dir / active_name).exists():
             (self.models_dir / active_name).write_bytes(b"temp")
             self.test_files.append(self.models_dir / active_name)

        resp = await self.client.request("DELETE", f"/models/{active_name}")
        assert resp.status == 403
        data = await resp.json()
        assert "Cannot delete the currently active model" in data["error"]

    @unittest_run_loop
    async def test_upload_too_large(self):
        """Test file size limit."""
        filename = "large.pt"
        # 201 MB
        large_content = b"x" * (201 * 1024 * 1024)
        
        data = FormData()
        data.add_field("file", large_content, filename=filename)

        resp = await self.client.request("POST", "/models/upload", data=data)
        assert resp.status == 413
        data = await resp.json()
        assert "File too large" in data["error"]
