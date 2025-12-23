"""
Pytest configuration and shared fixtures for Drone PTZ tests.

This module provides pytest fixtures that mock hardware dependencies and provide
deterministic test data to ensure all tests run completely offline.
"""

import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock

import numpy as np
import pytest

from src.settings import (
    CameraSettings,
    DetectionSettings,
    LoggingSettings,
    PerformanceSettings,
    PTZSettings,
    Settings,
    SimulatorSettings,
    TrackingSettings,
)

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure pytest
pytest_plugins: list[str] = []


class MockYOLOResult:
    """Mock YOLO detection results for testing."""

    def __init__(self, boxes_data: list[dict] | None = None):
        self.boxes = MockBoxes(boxes_data or [])


class MockBoxes:
    """Mock YOLO boxes container."""

    def __init__(self, boxes_data: list[dict]):
        self.boxes_data = boxes_data

    def __iter__(self):
        return iter([MockBox(data) for data in self.boxes_data])

    def __len__(self):
        return len(self.boxes_data)

    def __getitem__(self, index):
        return MockBox(self.boxes_data[index])


class MockBox:
    """Mock single detection box."""

    def __init__(self, data: dict):
        self.cls = data.get("cls", 0)
        self.conf = data.get("conf", 0.9)
        self.xyxy = np.array([data.get("xyxy", [100, 100, 200, 200])])
        self.id = data.get("id", 1)


class MockYOLOModel:
    """Mock YOLO model for testing without hardware dependencies."""

    def __init__(self, _model_path: str):
        # names should be a dict for YOLO compatibility
        self.names = {0: "drone", 1: "bird", 2: "airplane", 3: "aircraft"}
        self.device = "cpu"

    def track(
        self,
        source: Any = None,
        frame: Any = None,
        persist: bool = True,
        tracker: str | None = None,
        conf: float = 0.5,
        verbose: bool = False,
    ) -> list[MockYOLOResult]:
        """Mock YOLO track method with deterministic results."""
        # Accept both source (keyword) and frame (positional/keyword) for compatibility
        data = source if source is not None else frame
        if data is None or (hasattr(data, "size") and data.size == 0):
            return [MockYOLOResult([])]

        # Return mock detections based on frame shape
        if hasattr(data, "shape"):
            height, width = data.shape[:2]
            # Create a drone detection in the center for standard frames
            return [
                MockYOLOResult(
                    [
                        {
                            "cls": 0,  # drone class
                            "conf": 0.85,
                            "xyxy": [
                                width // 4,
                                height // 4,
                                3 * width // 4,
                                3 * height // 4,
                            ],
                            "id": 1,
                        }
                    ]
                )
            ]

        return [MockYOLOResult([])]


class MockONVIFCamera:
    """Mock ONVIF camera for PTZ testing."""

    def __init__(self, ip: str, port: int, user: str, password: str):
        self.ip = ip
        self.port = port
        self.user = user
        self.password = password
        # Raise exception if credentials are missing to simulate real behavior
        if not ip or not user or not password:
            msg = "Invalid camera credentials"
            raise ConnectionError(msg)
        self.connected = True

    def create_media_service(self) -> "MockMediaService":
        return MockMediaService()

    def create_ptz_service(self) -> "MockPTZService":
        return MockPTZService()


class MockMediaService:
    """Mock ONVIF media service."""

    def get_profiles(self) -> list[Mock]:
        """Return mock media profiles."""
        mock_profile = Mock()
        mock_profile.token = "test_profile_token"
        mock_profile.Name = "TestProfile"
        mock_profile.PTZConfiguration = Mock()
        mock_profile.PTZConfiguration.token = "test_ptz_token"
        return [mock_profile]

    # Keep original name for ONVIF compatibility
    GetProfiles = get_profiles


class MockPTZService:
    """Mock ONVIF PTZ service for movement testing."""

    def __init__(self):
        self.movements = []
        self.stops = []
        self.absolute_moves = []
        self.home_moves = []
        # Create Mock objects for methods so tests can spy on them
        self.continuous_move = Mock(side_effect=self._record_continuous_move)
        self.stop = Mock(side_effect=self._record_stop)
        self.absolute_move = Mock(side_effect=self._record_absolute_move)
        self.goto_home_position = Mock(side_effect=self._record_goto_home)
        self.get_status = Mock(side_effect=self._get_status)
        self.get_configuration_options = Mock(
            side_effect=self._get_configuration_options
        )

    def _record_continuous_move(self, request: dict):
        """Record continuous movement command."""
        self.movements.append(request)

    def _record_stop(self, request: dict):
        """Record stop command."""
        self.stops.append(request)

    def _record_absolute_move(self, request: dict):
        """Record absolute move command."""
        self.absolute_moves.append(request)

    def _record_goto_home(self, request: dict):
        """Record home position command."""
        self.home_moves.append(request)

    def _get_status(self, _request: dict) -> Mock:
        """Return mock PTZ status."""
        mock_status = Mock()
        mock_status.Position = Mock()
        mock_status.Position.PanTilt = Mock()
        mock_status.Position.PanTilt.x = 0.0
        mock_status.Position.PanTilt.y = 0.0
        mock_status.Position.Zoom = Mock()
        mock_status.Position.Zoom.x = 0.5
        return mock_status

    def _get_configuration_options(self, _request: dict) -> Mock:
        """Return mock PTZ configuration options."""
        mock_options = Mock()

        # Pan/Tilt velocity space
        mock_options.Spaces = Mock()
        mock_options.Spaces.ContinuousPanTiltVelocitySpace = [Mock()]
        mock_options.Spaces.ContinuousPanTiltVelocitySpace[0].XRange = Mock()
        mock_options.Spaces.ContinuousPanTiltVelocitySpace[0].XRange.Max = 1.0
        mock_options.Spaces.ContinuousPanTiltVelocitySpace[0].XRange.Min = -1.0
        mock_options.Spaces.ContinuousPanTiltVelocitySpace[0].YRange = Mock()
        mock_options.Spaces.ContinuousPanTiltVelocitySpace[0].YRange.Max = 1.0
        mock_options.Spaces.ContinuousPanTiltVelocitySpace[0].YRange.Min = -1.0

        # Absolute zoom position space
        mock_options.Spaces.AbsoluteZoomPositionSpace = [Mock()]
        mock_options.Spaces.AbsoluteZoomPositionSpace[0].XRange = Mock()
        mock_options.Spaces.AbsoluteZoomPositionSpace[0].XRange.Min = 0.0
        mock_options.Spaces.AbsoluteZoomPositionSpace[0].XRange.Max = 1.0

        # Continuous zoom velocity space
        mock_options.Spaces.ContinuousZoomVelocitySpace = [Mock()]
        mock_options.Spaces.ContinuousZoomVelocitySpace[
            0
        ].URI = "http://www.onvif.org/ver10/tptz/Zoom/VelocitySpace"

        return mock_options

    def create_type(self, request_type: str) -> Mock:
        """Create mock request objects."""
        mock_request = Mock()

        if request_type == "ContinuousMove":
            mock_request.ProfileToken = "test_profile_token"
            mock_request.Velocity = {
                "PanTilt": {"x": 0.0, "y": 0.0, "space": "test_space"},
                "Zoom": {"x": 0.0, "space": "test_zoom_space"},
            }
        elif request_type == "AbsoluteMove":
            mock_request.ProfileToken = "test_profile_token"
            mock_request.Position = Mock()
            mock_request.Position.PanTilt = Mock()
            mock_request.Position.PanTilt.x = 0.0
            mock_request.Position.PanTilt.y = 0.0
            mock_request.Position.Zoom = 0.5
        elif request_type == "GotoHomePosition":
            mock_request.ProfileToken = "test_profile_token"
            mock_request.Speed = Mock()
            mock_request.Speed.PanTilt = Mock()
            mock_request.Speed.PanTilt.x = 0.5
            mock_request.Speed.PanTilt.y = 0.5
            mock_request.Speed.Zoom = 0.5

        return mock_request

    def __getattr__(self, name: str):
        """Provide ONVIF-compatible method name aliases."""
        # Map PascalCase ONVIF names to lowercase mock method names
        aliases = {
            "ContinuousMove": "continuous_move",
            "Stop": "stop",
            "AbsoluteMove": "absolute_move",
            "GotoHomePosition": "goto_home_position",
            "GetStatus": "get_status",
            "GetConfigurationOptions": "get_configuration_options",
        }
        if name in aliases:
            return getattr(self, aliases[name])
        msg = f"'{type(self).__name__}' object has no attribute '{name}'"
        raise AttributeError(msg)


@pytest.fixture
def deterministic_environment(monkeypatch):
    """Ensure deterministic test environment with fixed random seeds."""
    # Fix random seeds for reproducibility
    import random  # noqa: PLC0415 - Import here to avoid side effects

    monkeypatch.setattr(random, "seed", lambda x: None)  # noqa: ARG005 - Mock signature

    # Mock numpy random seed if available
    try:
        import numpy as np  # noqa: PLC0415 - Conditional import

        monkeypatch.setattr(np.random, "seed", lambda x: None)  # noqa: ARG005 - Mock signature
    except ImportError:
        pass

    # Set deterministic environment variable
    monkeypatch.setenv("TEST_MODE", "true")

    yield

    # Cleanup
    monkeypatch.delenv("TEST_MODE", raising=False)


@pytest.fixture
def offline_network(monkeypatch):
    """Block all network access to ensure offline testing."""

    def mock_socket(*_args, **_kwargs):
        msg = "Network access disabled in tests"
        raise ConnectionError(msg)

    monkeypatch.setattr("socket.socket", mock_socket)

    # Cleanup is automatic due to monkeypatch scope


@pytest.fixture
def mock_yolo_model(monkeypatch):
    """Provide mock YOLO model for detection testing."""
    # Mock the lazy import helper functions instead of module-level attributes
    monkeypatch.setattr("src.detection.get_yolo", lambda: MockYOLOModel)

    # Mock torch helper
    class MockTorch:
        @staticmethod
        def no_grad():
            """Mock torch.no_grad context manager."""
            torch_no_grad_mock = MagicMock()
            torch_no_grad_mock.__enter__ = MagicMock(return_value=None)
            torch_no_grad_mock.__exit__ = MagicMock(return_value=None)
            return torch_no_grad_mock

    monkeypatch.setattr("src.detection.get_torch", lambda: MockTorch())

    return MockYOLOModel("test_model.pt")


@pytest.fixture
def mock_onvif_camera(monkeypatch):
    """Provide mock ONVIF camera for PTZ testing."""
    # Mock the lazy import helper function
    monkeypatch.setattr("src.ptz_controller.get_onvif_camera", lambda: MockONVIFCamera)
    return MockONVIFCamera


@pytest.fixture
def mock_cv2(monkeypatch):
    """Mock OpenCV functions to avoid GUI dependencies."""
    # Mock cv2.VideoCapture
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (True, create_test_frame())
    mock_cap.release.return_value = None
    monkeypatch.setattr("cv2.VideoCapture", lambda *_args: mock_cap)

    # Mock cv2.VideoWriter
    monkeypatch.setattr("cv2.VideoWriter", MagicMock())
    monkeypatch.setattr("cv2.VideoWriter.fourcc", lambda *_args: "MJPG")

    # Mock cv2 drawing functions
    monkeypatch.setattr("cv2.rectangle", MagicMock())
    monkeypatch.setattr("cv2.putText", MagicMock())
    monkeypatch.setattr("cv2.imshow", MagicMock())
    monkeypatch.setattr("cv2.waitKey", lambda _x: ord("q"))
    monkeypatch.setattr("cv2.destroyAllWindows", MagicMock())
    monkeypatch.setattr("cv2.getTextSize", lambda *_args: ((100, 20), 2))

    return mock_cap


@pytest.fixture
def sample_frame():
    """Provide a deterministic test frame for detection testing."""
    return create_test_frame()


def create_test_frame(width: int = 1280, height: int = 720) -> np.ndarray:
    """Create a deterministic test frame with known content."""
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    # Add a white rectangle in the center (simulating a drone)
    center_x, center_y = width // 2, height // 2
    size = min(width, height) // 4
    frame[center_y - size : center_y + size, center_x - size : center_x + size] = [
        255,
        255,
        255,
    ]
    return frame


@pytest.fixture
def test_detections():
    """Provide mock detections for testing."""
    return [
        {
            "cls": 0,  # drone
            "conf": 0.85,
            "xyxy": [320, 180, 960, 540],  # center region
            "id": 1,
        }
    ]


@pytest.fixture
def valid_config_data():
    """Provide valid configuration data for testing."""
    return {
        "detection": {
            "confidence_threshold": 0.5,
            "model_path": "assets/models/yolo/best5.pt",
        },
        "camera": {
            "credentials_ip": "192.168.1.70",
            "credentials_user": "test_user",
            "credentials_password": "test_pass",
            "resolution_width": 1280,
            "resolution_height": 720,
            "fps": 30,
        },
    }


@pytest.fixture
def invalid_configs():
    """Provide various invalid configuration scenarios."""
    return {
        "high_confidence": {
            "detection": {
                "confidence_threshold": 1.5,
                "model_path": "assets/models/yolo/best5.pt",
            }
        },
        "missing_model": {
            "detection": {
                "confidence_threshold": 0.5,
                "model_path": "nonexistent_model.pt",
            },
        },
        "missing_credentials": {
            "camera": {
                "credentials_ip": "",
                "credentials_user": "test_user",
                "credentials_password": "test_pass",
            }
        },
        "invalid_resolution": {
            "camera": {
                "resolution_width": -1,
                "resolution_height": 720,
            }
        },
    }


# Configure pytest-timeout for tests that might hang
@pytest.fixture
def settings():
    """Provide default test Settings."""
    return Settings(
        logging=LoggingSettings(
            log_file="test.log",
            log_level="INFO",
            write_log_file=False,
            reset_log_on_start=False,
        ),
        camera=CameraSettings(
            camera_index=0,
            resolution_width=640,
            resolution_height=480,
            fps=30,
            credentials_ip="192.168.1.70",
            credentials_user="test_user",
            credentials_password="test_pass",
        ),
        detection=DetectionSettings(
            confidence_threshold=0.5,
            model_path="assets/models/yolo/best5.pt",
        ),
        ptz=PTZSettings(
            ptz_ramp_rate=0.1,
            zoom_target_coverage=0.3,
        ),
        performance=PerformanceSettings(),
        simulator=SimulatorSettings(
            use_ptz_simulation=True,
            video_source=None,
            video_loop=False,
        ),
        tracking=TrackingSettings(
            tracker_type="botsort",
        ),
    )


def pytest_configure(config):
    """Configure pytest plugins and markers."""
    config.addinivalue_line("markers", "timeout: mark test with individual timeout")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "performance: mark test as performance test")


def pytest_collection_modifyitems(config: Any, items):  # noqa: ARG001 - Required by pytest API
    """Add timeout marker to all tests."""
    for item in items:
        # Add timeout to all tests (will be overridden by specific markers)
        item.add_marker(pytest.mark.timeout(10))
