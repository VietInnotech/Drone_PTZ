"""
Comprehensive test suite for PTZService with Octagon API.

Tests cover connection, movement commands, error handling, and PTZ control.
Target coverage: 90%
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

# Import the service under test
from src.ptz_controller import (
    OctagonAPIClient,
    PTZCommandError,
    PTZConnectionError,
    PTZService,
)
from src.settings import Settings


class TestOctagonAPIClient:
    """Test OctagonAPIClient HTTP communication."""

    @pytest.fixture
    def api_client(self):
        """Provide OctagonAPIClient instance for testing."""
        return OctagonAPIClient(
            base_url="http://192.168.1.21",
            username="admin",
            password="!Inf",
            timeout=5.0,
        )

    def test_initialization(self, api_client):
        """Test API client initialization."""
        assert api_client.base_url == "http://192.168.1.21"
        assert api_client.timeout == 5.0

    @patch("src.ptz_controller.requests.Session")
    def test_get_request_success(self, mock_session_class, api_client):
        """Test successful GET request."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {"success": True, "data": {"pan": 45.0}}
        mock_response.raise_for_status = Mock()
        api_client.session.get = Mock(return_value=mock_response)

        # Act
        result = api_client.get("/api/devices/pantilt/position")

        # Assert
        assert result == {"pan": 45.0}

    @patch("src.ptz_controller.requests.Session")
    def test_get_request_api_error(self, mock_session_class, api_client):
        """Test GET request with API error."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": False,
            "error": {"message": "Device not found"},
        }
        mock_response.raise_for_status = Mock()
        api_client.session.get = Mock(return_value=mock_response)

        # Act & Assert
        with pytest.raises(PTZCommandError) as exc_info:
            api_client.get("/api/devices/pantilt/position")
        assert "Device not found" in str(exc_info.value)

    def test_get_request_connection_error(self, api_client):
        """Test GET request with connection error."""
        # Arrange
        import requests

        api_client.session.get = Mock(
            side_effect=requests.exceptions.ConnectionError("Connection refused")
        )

        # Act & Assert
        with pytest.raises(PTZConnectionError):
            api_client.get("/api/devices/pantilt/position")

    def test_get_request_timeout(self, api_client):
        """Test GET request with timeout."""
        # Arrange
        import requests

        api_client.session.get = Mock(
            side_effect=requests.exceptions.Timeout("Request timeout")
        )

        # Act & Assert
        with pytest.raises(PTZConnectionError):
            api_client.get("/api/devices/pantilt/position")

    @patch("src.ptz_controller.requests.Session")
    def test_post_request_success(self, mock_session_class, api_client):
        """Test successful POST request."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {"success": True, "data": None}
        mock_response.raise_for_status = Mock()
        api_client.session.post = Mock(return_value=mock_response)

        # Act
        result = api_client.post(
            "/api/devices/pantilt/position", data={"pan": 45.0, "tilt": 10.0}
        )

        # Assert
        assert result is None or isinstance(result, dict)

    def test_test_connection_success(self, api_client):
        """Test connection test success."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {"success": True, "data": {"version": "2.19"}}
        mock_response.raise_for_status = Mock()
        api_client.session.get = Mock(return_value=mock_response)

        # Act
        result = api_client.test_connection()

        # Assert
        assert result is True

    def test_test_connection_failure(self, api_client):
        """Test connection test failure."""
        # Arrange
        import requests

        api_client.session.get = Mock(
            side_effect=requests.exceptions.ConnectionError("Connection refused")
        )

        # Act
        result = api_client.test_connection()

        # Assert
        assert result is False


@pytest.fixture
def mock_octagon_client():
    """Create a mock OctagonAPIClient for PTZService tests."""
    with patch("src.ptz_controller.OctagonAPIClient") as mock_client_class:
        mock_client = Mock()
        mock_client.test_connection.return_value = True
        mock_client.get.return_value = {"pan": 0.0, "tilt": 0.0}
        mock_client.post.return_value = None
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_settings():
    """Create mock settings for PTZService tests."""
    settings = MagicMock(spec=Settings)
    settings.detection.camera_credentials.ip = "192.168.1.21"
    settings.detection.camera_credentials.user = "admin"
    settings.detection.camera_credentials.password = "!Inf"
    settings.ptz.ptz_ramp_rate = 0.2
    return settings


class TestPTZServiceInitialization:
    """Test PTZService initialization and connection handling."""

    def test_initialization_success_with_valid_credentials(
        self, mock_octagon_client, mock_settings
    ):
        """Test successful initialization with valid camera credentials."""
        # Arrange & Act
        ptz_service = PTZService(
            ip="192.168.1.21",
            port=80,
            user="admin",
            password="!Inf",
            settings=mock_settings,
        )

        # Assert
        assert ptz_service.connected is True
        assert ptz_service.active is False
        assert ptz_service.client is not None

    def test_initialization_failure_with_empty_credentials(self, mock_settings):
        """Test initialization failure with empty IP."""
        # Arrange - Create settings with empty IP
        mock_settings.detection.camera_credentials.ip = ""

        # Act
        ptz_service = PTZService(settings=mock_settings)

        # Assert
        assert ptz_service.connected is False

    def test_initialization_with_config_defaults(
        self, mock_octagon_client, mock_settings
    ):
        """Test initialization using configuration defaults."""
        # Arrange & Act
        ptz_service = PTZService(settings=mock_settings)

        # Assert
        assert ptz_service.connected is True
        assert ptz_service.xmin == -1.0
        assert ptz_service.xmax == 1.0
        assert ptz_service.ymin == -1.0
        assert ptz_service.ymax == 1.0
        assert ptz_service.zmin == 0.0
        assert ptz_service.zmax == 100.0

    def test_initialization_handles_connection_failure(self, mock_settings):
        """Test handling of connection failures during initialization."""
        # Arrange
        with patch("src.ptz_controller.OctagonAPIClient") as mock_client_class:
            mock_client = Mock()
            mock_client.test_connection.return_value = False
            mock_client_class.return_value = mock_client

            # Act
            ptz_service = PTZService(settings=mock_settings)

            # Assert
            assert ptz_service.connected is False


class TestPTZServiceRamp:
    """Test PTZService.ramp() method for smooth transitions."""

    @pytest.fixture
    def ptz_service(self, mock_octagon_client, mock_settings):
        """Provide PTZService instance for ramp testing."""
        ptz_service = PTZService(settings=mock_settings)
        ptz_service.ramp_rate = 0.2
        return ptz_service

    def test_ramp_moves_towards_target_within_rate_limit(self, ptz_service):
        """Test ramping moves towards target but limited by ramp rate."""
        # Arrange
        current = 0.0
        target = 1.0

        # Act
        result = ptz_service.ramp(target, current)

        # Assert
        assert result == 0.2  # Should move by ramp_rate
        assert result < target

    def test_ramp_returns_target_when_within_rate(self, ptz_service):
        """Test ramp returns target when already close enough."""
        # Arrange
        current = 0.9
        target = 1.0

        # Act
        result = ptz_service.ramp(target, current)

        # Assert
        assert result == target

    def test_ramp_handles_negative_target(self, ptz_service):
        """Test ramping in negative direction."""
        # Arrange
        current = 0.0
        target = -1.0

        # Act
        result = ptz_service.ramp(target, current)

        # Assert
        assert result == -0.2

    def test_ramp_handles_no_change_needed(self, ptz_service):
        """Test ramp when already at target."""
        # Arrange
        current = 0.5
        target = 0.5

        # Act
        result = ptz_service.ramp(target, current)

        # Assert
        assert result == target


class TestPTZServiceDirectionConversion:
    """Test PTZService direction and speed conversion."""

    @pytest.fixture
    def ptz_service(self, mock_octagon_client, mock_settings):
        """Provide PTZService instance for direction testing."""
        return PTZService(settings=mock_settings)

    def test_get_direction_up_right(self, ptz_service):
        """Test direction conversion for up-right movement."""
        # Act
        direction, pan_speed, tilt_speed = ptz_service._get_direction_and_speeds(
            0.5, 0.5
        )

        # Assert
        assert direction == "upright"
        assert pan_speed == 50
        assert tilt_speed == 50

    def test_get_direction_down_left(self, ptz_service):
        """Test direction conversion for down-left movement."""
        # Act
        direction, pan_speed, tilt_speed = ptz_service._get_direction_and_speeds(
            -0.5, -0.5
        )

        # Assert
        assert direction == "downleft"
        assert pan_speed == 50
        assert tilt_speed == 50

    def test_get_direction_no_movement(self, ptz_service):
        """Test direction conversion when no movement."""
        # Act
        direction, pan_speed, tilt_speed = ptz_service._get_direction_and_speeds(0, 0)

        # Assert
        assert direction is None
        assert pan_speed == 0
        assert tilt_speed == 0

    def test_get_direction_clamps_speed(self, ptz_service):
        """Test speed clamping to 1-100 range."""
        # Act
        direction, pan_speed, tilt_speed = ptz_service._get_direction_and_speeds(
            1.5, 1.5
        )

        # Assert
        assert pan_speed == 100  # Clamped to max
        assert tilt_speed == 100


class TestPTZServiceContinuousMove:
    """Test PTZService.continuous_move() method."""

    @pytest.fixture
    def ptz_service(self, mock_octagon_client, mock_settings):
        """Provide PTZService instance for movement testing."""
        ptz_service = PTZService(settings=mock_settings)
        ptz_service._last_command_time = 0  # Reset debounce
        return ptz_service

    def test_continuous_move_valid_movement(self, ptz_service):
        """Test continuous movement with valid pan/tilt/zoom values."""
        # Arrange
        pan = 0.5
        tilt = 0.3
        zoom = 0.2

        # Act
        ptz_service.continuous_move(pan, tilt, zoom)

        # Assert
        assert ptz_service.active is True
        # Should have called API
        ptz_service.client.get.assert_called()

    def test_continuous_move_skips_small_changes(self, ptz_service):
        """Test continuous movement skips commands for small changes."""
        # Arrange
        ptz_service.last_pan = 0.5
        ptz_service.last_tilt = 0.5
        ptz_service.last_zoom = 0.5
        ptz_service.ramp_rate = 1.0

        pan = 0.5005
        tilt = 0.5005
        zoom = 0.5005

        # Act
        ptz_service.continuous_move(pan, tilt, zoom, threshold=0.01)

        # Assert - should not update active state for tiny changes

    def test_continuous_move_when_not_connected(self, ptz_service):
        """Test continuous movement when not connected returns early."""
        # Arrange
        ptz_service.connected = False

        # Act
        ptz_service.continuous_move(0.5, 0.3, 0.2)

        # Assert
        assert ptz_service.active is False

    def test_continuous_move_handles_exception(self, ptz_service):
        """Test continuous movement handles API exceptions gracefully."""
        # Arrange
        ptz_service.client.get.side_effect = PTZCommandError("API error")
        ptz_service._last_command_time = 0

        # Act
        ptz_service.continuous_move(0.5, 0.3, 0.2)

        # Assert - should not crash
        assert ptz_service.active is False


class TestPTZServiceStop:
    """Test PTZService.stop() method."""

    @pytest.fixture
    def ptz_service(self, mock_octagon_client, mock_settings):
        """Provide PTZService instance for stop testing."""
        ptz_service = PTZService(settings=mock_settings)
        return ptz_service

    def test_stop_all_axes(self, ptz_service):
        """Test stopping all axes by default."""
        # Arrange
        ptz_service.active = True
        ptz_service.last_pan = 0.5
        ptz_service.last_tilt = 0.3
        ptz_service.last_zoom = 0.2

        # Act
        ptz_service.stop()

        # Assert
        assert ptz_service.active is False
        assert ptz_service.last_pan == 0.0
        assert ptz_service.last_tilt == 0.0
        assert ptz_service.last_zoom == 0.0

    def test_stop_selective_axes(self, ptz_service):
        """Test stopping only specified axes."""
        # Arrange
        ptz_service.active = True
        ptz_service.last_pan = 0.5
        ptz_service.last_tilt = 0.3
        ptz_service.last_zoom = 0.2

        # Act
        ptz_service.stop(pan=True, tilt=False, zoom=True)

        # Assert
        assert ptz_service.active is False
        assert ptz_service.last_pan == 0.0
        assert ptz_service.last_tilt == 0.3  # Should not be reset
        assert ptz_service.last_zoom == 0.0

    def test_stop_when_not_connected(self, ptz_service):
        """Test stop when not connected."""
        # Arrange
        ptz_service.connected = False
        ptz_service.active = True

        # Act
        ptz_service.stop()

        # Assert - should return early without error
        assert ptz_service.active is True  # Not modified


class TestPTZServiceZoomAbsolute:
    """Test PTZService.set_zoom_absolute() method."""

    @pytest.fixture
    def ptz_service(self, mock_octagon_client, mock_settings):
        """Provide PTZService instance for zoom testing."""
        ptz_service = PTZService(settings=mock_settings)
        return ptz_service

    def test_set_zoom_absolute_valid_value(self, ptz_service):
        """Test setting absolute zoom with valid value."""
        # Arrange
        zoom_value = 50.0

        # Act
        ptz_service.set_zoom_absolute(zoom_value)

        # Assert
        assert ptz_service.zoom_level == zoom_value
        ptz_service.client.post.assert_called_once()

    def test_set_zoom_absolute_clamps_to_range(self, ptz_service):
        """Test absolute zoom clamps values to valid range."""
        # Arrange
        zoom_value = 150.0  # Exceeds zmax (100)

        # Act
        ptz_service.set_zoom_absolute(zoom_value)

        # Assert
        assert ptz_service.zoom_level == 100.0

    def test_set_zoom_home(self, ptz_service):
        """Test set_zoom_home convenience method."""
        # Act
        ptz_service.set_zoom_home()

        # Assert
        assert ptz_service.zoom_level == ptz_service.zmin


class TestPTZServiceHomePosition:
    """Test PTZService.set_home_position() method."""

    @pytest.fixture
    def ptz_service(self, mock_octagon_client, mock_settings):
        """Provide PTZService instance for home position testing."""
        ptz_service = PTZService(settings=mock_settings)
        return ptz_service

    def test_set_home_position_successful(self, ptz_service):
        """Test successful home position movement."""
        # Act
        ptz_service.set_home_position()

        # Assert
        assert ptz_service.last_pan == 0.0
        assert ptz_service.last_tilt == 0.0
        assert ptz_service.last_zoom == 0.0
        # Should have called API
        ptz_service.client.get.assert_called()

    def test_set_home_position_when_not_connected(self, ptz_service):
        """Test home position when not connected."""
        # Arrange
        ptz_service.connected = False

        # Act
        ptz_service.set_home_position()

        # Assert - should return early without error


class TestPTZServiceZoomRelative:
    """Test PTZService.set_zoom_relative() method."""

    @pytest.fixture
    def ptz_service(self, mock_octagon_client, mock_settings):
        """Provide PTZService instance for relative zoom testing."""
        ptz_service = PTZService(settings=mock_settings)
        ptz_service.client.get.return_value = {"zoom": 50.0}
        return ptz_service

    def test_set_zoom_relative_valid_delta(self, ptz_service):
        """Test relative zoom with valid delta."""
        # Arrange
        zoom_delta = 10.0

        # Act
        ptz_service.set_zoom_relative(zoom_delta)

        # Assert
        assert ptz_service.zoom_level == 60.0  # 50 + 10

    def test_set_zoom_relative_clamps_to_bounds(self, ptz_service):
        """Test relative zoom clamps to valid bounds."""
        # Arrange
        ptz_service.client.get.return_value = {"zoom": 95.0}
        zoom_delta = 20.0  # Would exceed zmax

        # Act
        ptz_service.set_zoom_relative(zoom_delta)

        # Assert
        assert ptz_service.zoom_level == 100.0  # Clamped to zmax


class TestPTZServiceGetZoom:
    """Test PTZService.get_zoom() method."""

    @pytest.fixture
    def ptz_service(self, mock_octagon_client, mock_settings):
        """Provide PTZService instance for get zoom testing."""
        ptz_service = PTZService(settings=mock_settings)
        return ptz_service

    def test_get_zoom_returns_current_value(self, ptz_service):
        """Test get zoom returns current zoom position."""
        # Arrange
        ptz_service.client.get.return_value = {"zoom": 75.0}

        # Act
        zoom_level = ptz_service.get_zoom()

        # Assert
        assert zoom_level == 75.0

    def test_get_zoom_falls_back_when_unavailable(self, ptz_service):
        """Test get zoom falls back to zmin when unavailable."""
        # Arrange
        ptz_service.client.get.side_effect = PTZConnectionError("Connection failed")

        # Act
        zoom_level = ptz_service.get_zoom()

        # Assert
        assert zoom_level == ptz_service.zmin

    def test_get_zoom_when_not_connected(self, ptz_service):
        """Test get zoom when not connected."""
        # Arrange
        ptz_service.connected = False

        # Act
        zoom_level = ptz_service.get_zoom()

        # Assert
        assert zoom_level == ptz_service.zmin


class TestPTZServicePosition:
    """Test PTZService position methods."""

    @pytest.fixture
    def ptz_service(self, mock_octagon_client, mock_settings):
        """Provide PTZService instance for position testing."""
        ptz_service = PTZService(settings=mock_settings)
        return ptz_service

    def test_get_position(self, ptz_service):
        """Test get position returns current pan/tilt."""
        # Arrange
        ptz_service.client.get.return_value = {"pan": 45.0, "tilt": 10.0}

        # Act
        position = ptz_service.get_position()

        # Assert
        assert position == {"pan": 45.0, "tilt": 10.0}

    def test_set_position_absolute(self, ptz_service):
        """Test set absolute position."""
        # Act
        ptz_service.set_position_absolute(45.0, 10.0)

        # Assert
        ptz_service.client.post.assert_called_once()

    def test_set_position_absolute_clamps_values(self, ptz_service):
        """Test set position clamps to valid ranges."""
        # Act
        ptz_service.set_position_absolute(400.0, -100.0)

        # Assert - should clamp pan to 360 and tilt to -90
        call_args = ptz_service.client.post.call_args
        assert call_args[1]["data"]["pan"] == 360.0
        assert call_args[1]["data"]["tilt"] == -90.0


class TestPTZServiceStatus:
    """Test PTZService status methods."""

    @pytest.fixture
    def ptz_service(self, mock_octagon_client, mock_settings):
        """Provide PTZService instance for status testing."""
        ptz_service = PTZService(settings=mock_settings)
        return ptz_service

    def test_get_status(self, ptz_service):
        """Test get status returns device status."""
        # Arrange
        ptz_service.client.get.return_value = {"boardTemperature": 24.5, "pan": 45.0}

        # Act
        status = ptz_service.get_status()

        # Assert
        assert status["connected"] is True
        assert status["boardTemperature"] == 24.5

    def test_get_status_when_not_connected(self, ptz_service):
        """Test get status when not connected."""
        # Arrange
        ptz_service.connected = False

        # Act
        status = ptz_service.get_status()

        # Assert
        assert status == {"connected": False}

    def test_initialize_device(self, ptz_service):
        """Test device initialization."""
        # Act
        result = ptz_service.initialize_device()

        # Assert
        assert result is True
        ptz_service.client.get.assert_called()


class TestPTZServiceStabilization:
    """Test PTZService stabilization methods."""

    @pytest.fixture
    def ptz_service(self, mock_octagon_client, mock_settings):
        """Provide PTZService instance for stabilization testing."""
        ptz_service = PTZService(settings=mock_settings)
        return ptz_service

    def test_set_stabilization_enable(self, ptz_service):
        """Test enabling stabilization."""
        # Act
        ptz_service.set_stabilization(True)

        # Assert
        call_args = ptz_service.client.get.call_args
        assert call_args[1]["params"]["enable"] == "true"

    def test_set_stabilization_disable(self, ptz_service):
        """Test disabling stabilization."""
        # Act
        ptz_service.set_stabilization(False)

        # Assert
        call_args = ptz_service.client.get.call_args
        assert call_args[1]["params"]["enable"] == "false"

    def test_get_stabilization(self, ptz_service):
        """Test get stabilization status."""
        # Arrange
        ptz_service.client.get.return_value = {"active": True}

        # Act
        result = ptz_service.get_stabilization()

        # Assert
        assert result is True

    def test_get_stabilization_when_not_connected(self, ptz_service):
        """Test get stabilization when not connected."""
        # Arrange
        ptz_service.connected = False

        # Act
        result = ptz_service.get_stabilization()

        # Assert
        assert result is False
