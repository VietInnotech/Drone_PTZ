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
        self.names = ["drone", "bird", "airplane", "aircraft"]
        self.device = "cpu"

    def track(
        self,
        frame: Any,
        _persist: bool = True,
        _tracker: str | None = None,
        _conf: float = 0.5,
        _verbose: bool = False,
    ) -> list[MockYOLOResult]:
        """Mock YOLO track method with deterministic results."""
        if frame is None or (hasattr(frame, "size") and frame.size == 0):
            return [MockYOLOResult([])]

        # Return mock detections based on frame shape
        if hasattr(frame, "shape"):
            height, width = frame.shape[:2]
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
        self.connected = bool(ip and user and password)

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

    def continuous_move(self, request: dict):
        """Record continuous movement command."""
        self.movements.append(request)

    def stop(self, request: dict):
        """Record stop command."""
        self.stops.append(request)

    def absolute_move(self, request: dict):
        """Record absolute move command."""
        self.absolute_moves.append(request)

    def goto_home_position(self, request: dict):
        """Record home position command."""
        self.home_moves.append(request)

    def get_status(self, _request: dict) -> Mock:
        """Return mock PTZ status."""
        mock_status = Mock()
        mock_status.Position = Mock()
        mock_status.Position.PanTilt = Mock()
        mock_status.Position.PanTilt.x = 0.0
        mock_status.Position.PanTilt.y = 0.0
        mock_status.Position.Zoom = Mock()
        mock_status.Position.Zoom.x = 0.5
        return mock_status

    def get_configuration_options(self, _request: dict) -> Mock:
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

    # Keep original ONVIF-compatible method names as aliases
    ContinuousMove = continuous_move
    Stop = stop
    AbsoluteMove = absolute_move
    GotoHomePosition = goto_home_position
    GetStatus = get_status
    GetConfigurationOptions = get_configuration_options

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
    monkeypatch.setattr("detection.YOLO", MockYOLOModel)

    # Also mock torch.no_grad context manager
    torch_no_grad_mock = MagicMock()
    torch_no_grad_mock.__enter__ = MagicMock(return_value=None)
    torch_no_grad_mock.__exit__ = MagicMock(return_value=None)
    monkeypatch.setattr("torch.no_grad", lambda: torch_no_grad_mock)

    return MockYOLOModel("test_model.pt")


@pytest.fixture
def mock_onvif_camera(monkeypatch):
    """Provide mock ONVIF camera for PTZ testing."""
    monkeypatch.setattr("ptz_controller.ONVIFCamera", MockONVIFCamera)
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
def mock_config():
    """Provide configuration override for testing."""
    from src.config import Config  # noqa: PLC0415 - Import here for test isolation

    # Store original values
    original_values = {}
    for attr in [
        "CONFIDENCE_THRESHOLD",
        "MODEL_PATH",
        "CAMERA_CREDENTIALS",
        "FPS",
        "RESOLUTION_WIDTH",
        "RESOLUTION_HEIGHT",
    ]:
        if hasattr(Config, attr):
            original_values[attr] = getattr(Config, attr)

    # Set test values
    Config.CONFIDENCE_THRESHOLD = 0.5
    Config.MODEL_PATH = "tests/fixtures/mock_model.pt"
    Config.CAMERA_CREDENTIALS = {
        "ip": "192.168.1.70",
        "user": "test_user",
        "pass": "test_pass",
    }
    Config.FPS = 30
    Config.RESOLUTION_WIDTH = 1280
    Config.RESOLUTION_HEIGHT = 720

    yield Config

    # Restore original values
    for attr, value in original_values.items():
        setattr(Config, attr, value)


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
        "CONFIDENCE_THRESHOLD": 0.5,
        "MODEL_PATH": "tests/fixtures/mock_model.pt",
        "CAMERA_CREDENTIALS": {
            "ip": "192.168.1.70",
            "user": "test_user",
            "pass": "test_pass",
        },
        "RESOLUTION_WIDTH": 1280,
        "RESOLUTION_HEIGHT": 720,
        "FPS": 30,
    }


@pytest.fixture
def invalid_configs():
    """Provide various invalid configuration scenarios."""
    return {
        "high_confidence": {
            "CONFIDENCE_THRESHOLD": 1.5,
            "MODEL_PATH": "tests/fixtures/mock_model.pt",
            "CAMERA_CREDENTIALS": {
                "ip": "192.168.1.70",
                "user": "test_user",
                "pass": "test_pass",
            },
        },
        "missing_model": {
            "CONFIDENCE_THRESHOLD": 0.5,
            "MODEL_PATH": "nonexistent_model.pt",
            "CAMERA_CREDENTIALS": {
                "ip": "192.168.1.70",
                "user": "test_user",
                "pass": "test_pass",
            },
        },
        "missing_credentials": {
            "CONFIDENCE_THRESHOLD": 0.5,
            "MODEL_PATH": "tests/fixtures/mock_model.pt",
            "CAMERA_CREDENTIALS": {"ip": "", "user": "test_user", "pass": "test_pass"},
        },
        "invalid_resolution": {
            "CONFIDENCE_THRESHOLD": 0.5,
            "MODEL_PATH": "tests/fixtures/mock_model.pt",
            "CAMERA_CREDENTIALS": {
                "ip": "192.168.1.70",
                "user": "test_user",
                "pass": "test_pass",
            },
            "RESOLUTION_WIDTH": -1,
            "RESOLUTION_HEIGHT": 720,
        },
    }


# Configure pytest-timeout for tests that might hang
def pytest_configure(config):
    """Configure pytest plugins and markers."""
    config.addinivalue_line("markers", "timeout: mark test with individual timeout")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "performance: mark test as performance test")


def pytest_collection_modifyitems(_config, items):
    """Add timeout marker to all tests."""
    for item in items:
        # Add timeout to all tests (will be overridden by specific markers)
        item.add_marker(pytest.mark.timeout(10))
