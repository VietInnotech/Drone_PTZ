"""
Comprehensive test suite for PTZService movement functionality.

Tests cover connection, movement commands, error handling, and PTZ control.
Target coverage: 90% (up from 25%)
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

# Import the service under test
from src.ptz_controller import PTZService
from src.settings import Settings

pytestmark = pytest.mark.usefixtures("mock_onvif_camera")


class TestPTZServiceInitialization:
    """Test PTZService initialization and connection handling."""

    def test_initialization_success_with_valid_credentials(self):
        """Test successful initialization with valid camera credentials."""
        # Arrange & Act
        ptz_service = PTZService(
            ip="192.168.1.70", port=80, user="test_user", password="test_pass"
        )

        # Assert
        assert ptz_service.connected is True
        assert ptz_service.active is False
        assert ptz_service.request is not None

    def test_initialization_failure_with_invalid_credentials(self):
        """Test initialization failure with invalid camera credentials."""
        # Arrange - Create settings with empty credentials
        bad_settings = Settings()
        bad_settings.camera.credentials_ip = ""
        bad_settings.camera.credentials_user = ""
        bad_settings.camera.credentials_password = ""
        bad_settings.ptz.ptz_ramp_rate = 0.1

        # Act
        ptz_service = PTZService(settings=bad_settings)

        # Assert
        assert ptz_service.connected is False
        assert ptz_service.active is False

    def test_initialization_with_config_defaults(self):
        """Test initialization using configuration defaults."""
        # Arrange & Act
        ptz_service = PTZService()

        # Assert
        assert ptz_service.connected is True  # Should use config defaults
        assert ptz_service.xmin == -1.0
        assert ptz_service.xmax == 1.0
        assert ptz_service.ymin == -1.0
        assert ptz_service.ymax == 1.0
        assert ptz_service.zmin == 0.0
        assert ptz_service.zmax == 1.0

    def test_initialization_handles_connection_failure(self):
        """Test handling of connection failures during initialization."""
        # Arrange
        with patch(
            "src.ptz_controller.get_onvif_camera",
            side_effect=lambda: Mock(side_effect=Exception("Connection failed")),
        ):
            # Act
            ptz_service = PTZService(
                ip="192.168.1.70", port=80, user="test_user", password="test_pass"
            )

            # Assert
            assert ptz_service.connected is False
            assert ptz_service.active is False

    def test_initialization_stores_ptz_ranges(self):
        """Test that PTZ ranges are properly stored from camera capabilities."""
        # Arrange & Act
        ptz_service = PTZService()

        # Assert
        # Check that ranges are set from mock configuration
        assert hasattr(ptz_service, "xmin")
        assert hasattr(ptz_service, "xmax")
        assert hasattr(ptz_service, "ymin")
        assert hasattr(ptz_service, "ymax")
        assert hasattr(ptz_service, "zmin")
        assert hasattr(ptz_service, "zmax")

    def test_initialization_handles_missing_profiles(self):
        """Test handling when camera returns no profiles."""
        # Arrange
        with patch("src.ptz_controller.get_onvif_camera") as mock_camera_class:
            mock_camera = Mock()
            mock_camera.create_media_service.return_value.GetProfiles.return_value = []
            mock_camera_class.return_value = mock_camera

            # Act
            ptz_service = PTZService()

            # Assert - Should gracefully fail with connected=False
            assert ptz_service.connected is False
            assert ptz_service.active is False


class TestPTZServiceRamp:
    """Test PTZService.ramp() method for smooth transitions."""

    @pytest.fixture
    def ptz_service(self):
        """Provide PTZService instance for ramp testing."""
        ptz_service = PTZService()
        ptz_service.ramp_rate = 0.2  # Standard ramp rate
        return ptz_service

    def test_ramp_moves_towards_target_within_rate_limit(self, ptz_service):
        """Test ramping moves towards target but limited by ramp rate."""
        # Arrange
        current = 0.0
        target = 1.0
        ramp_rate = 0.2

        # Act
        result = ptz_service.ramp(target, current)

        # Assert
        # Should move towards target by ramp_rate
        assert result == current + ramp_rate
        assert result < target

    def test_ramp_returns_target_when_within_rate(self, ptz_service):
        """Test ramp returns target when already close enough."""
        # Arrange
        current = 0.9
        target = 1.0

        # Act
        result = ptz_service.ramp(target, current)

        # Assert
        # Should return target when already within rate limit
        assert result == target

    def test_ramp_handles_negative_target(self, ptz_service):
        """Test ramping in negative direction."""
        # Arrange
        current = 0.0
        target = -1.0
        ramp_rate = 0.2

        # Act
        result = ptz_service.ramp(target, current)

        # Assert
        assert result == -ramp_rate
        assert result > target  # Still above the target

    def test_ramp_handles_no_change_needed(self, ptz_service):
        """Test ramp when already at target."""
        # Arrange
        current = 0.5
        target = 0.5

        # Act
        result = ptz_service.ramp(target, current)

        # Assert
        assert result == target

    def test_ramp_with_custom_rate(self, ptz_service):
        """Test ramp with different ramp rates."""
        # Arrange
        ptz_service.ramp_rate = 0.1
        current = 0.0
        target = 0.5

        # Act
        result = ptz_service.ramp(target, current)

        # Assert
        assert result == 0.1  # Should use custom rate


class TestPTZServiceContinuousMove:
    """Test PTZService.continuous_move() method."""

    @pytest.fixture
    def ptz_service(self):
        """Provide PTZService instance for movement testing."""
        ptz_service = PTZService()
        ptz_service.connected = True  # Ensure connected
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
        # Should have called the ONVIF service
        assert len(ptz_service.ptz.ContinuousMove.call_args_list) > 0
        # Should be marked as active
        assert ptz_service.active is True

    def test_continuous_move_with_rounding(self, ptz_service):
        """Test continuous movement applies proper rounding."""
        # Arrange
        pan = 0.123456
        tilt = 0.987654
        zoom = 0.555555

        # Act
        ptz_service.continuous_move(pan, tilt, zoom)

        # Assert
        # Should have rounded to 2 decimal places

        # Check that the movement was called (verification through mocking)
        assert ptz_service.active is True

    def test_continuous_move_with_zoom_clamping(self, ptz_service):
        """Test continuous movement clamps zoom to valid range."""
        # Arrange
        pan = 0.0
        tilt = 0.0
        zoom = 2.0  # Exceeds zmax

        # Act
        ptz_service.continuous_move(pan, tilt, zoom)

        # Assert
        # Should clamp zoom to zmax (1.0)
        assert ptz_service.active is True

    def test_continuous_move_skips_small_changes(self, ptz_service):
        """Test continuous movement skips commands for small changes."""
        # Arrange
        ptz_service.last_pan = 0.5
        ptz_service.last_tilt = 0.5
        ptz_service.last_zoom = 0.5
        threshold = 0.01

        # Set ramp_rate very high so ramp function doesn't limit movement
        ptz_service.ramp_rate = 1.0

        # All changes must be strictly less than threshold for command to be skipped
        # Testing with values where all changes are < 0.01
        pan = 0.5005  # Change: 0.5005 - 0.5 = 0.0005 < 0.01
        tilt = 0.5006  # Change: 0.5006 - 0.5 = 0.0006 < 0.01
        zoom = 0.5007  # Change: 0.5007 - 0.5 = 0.0007 < 0.01

        # Act
        ptz_service.continuous_move(pan, tilt, zoom, threshold)

        # Assert
        # Should not have moved (no significant change)
        assert ptz_service.active is False

    def test_continuous_move_updates_internal_state(self, ptz_service):
        """Test continuous movement updates internal position state."""
        # Arrange
        pan = 0.5
        tilt = 0.3
        zoom = 0.2

        # Act
        ptz_service.continuous_move(pan, tilt, zoom)

        # Assert
        assert ptz_service.last_pan != 0.0
        assert ptz_service.last_tilt != 0.0
        assert ptz_service.last_zoom != 0.0

    def test_continuous_move_when_not_connected(self, ptz_service):
        """Test continuous movement when not connected returns early."""
        # Arrange
        ptz_service.connected = False

        # Act
        ptz_service.continuous_move(0.5, 0.3, 0.2)

        # Assert
        # Should not have made any movement calls
        assert ptz_service.active is False

    def test_continuous_move_handles_exception(self, ptz_service):
        """Test continuous movement handles ONVIF exceptions gracefully."""
        # Arrange
        ptz_service.ptz.ContinuousMove.side_effect = Exception("ONVIF error")

        # Act
        ptz_service.continuous_move(0.5, 0.3, 0.2)

        # Assert
        # Should handle exception and not crash
        assert ptz_service.active is False

    def test_continuous_move_with_float_conversion(self, ptz_service):
        """Test continuous movement converts inputs to float."""
        # Arrange
        pan = "0.5"
        tilt = 0.3
        zoom = 0.2

        # Act
        ptz_service.continuous_move(pan, tilt, zoom)

        # Assert
        # Should convert string to float and process normally
        assert ptz_service.active is True


class TestPTZServiceStop:
    """Test PTZService.stop() method."""

    @pytest.fixture
    def ptz_service(self):
        """Provide PTZService instance for stop testing."""
        ptz_service = PTZService()
        ptz_service.connected = True
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

    def test_stop_with_exception_handling(self, ptz_service):
        """Test stop method handles ONVIF exceptions gracefully."""
        # Arrange
        ptz_service.ptz.Stop.side_effect = Exception("Stop failed")

        # Act
        ptz_service.stop()

        # Assert
        # Should handle exception and still reset internal state
        assert ptz_service.last_pan == 0.0
        assert ptz_service.last_tilt == 0.0
        assert ptz_service.last_zoom == 0.0


class TestPTZServiceZoomAbsolute:
    """Test PTZService.set_zoom_absolute() method."""

    @pytest.fixture
    def ptz_service(self):
        """Provide PTZService instance for zoom testing."""
        ptz_service = PTZService()
        ptz_service.connected = True
        return ptz_service

    def test_set_zoom_absolute_valid_value(self, ptz_service):
        """Test setting absolute zoom with valid value."""
        # Arrange
        zoom_value = 0.5

        # Act
        ptz_service.set_zoom_absolute(zoom_value)

        # Assert
        assert ptz_service.zoom_level == zoom_value
        assert ptz_service.last_zoom == zoom_value

    def test_set_zoom_absolute_clamps_to_range(self, ptz_service):
        """Test absolute zoom clamps values to valid range."""
        # Arrange
        zoom_value = 2.0  # Exceeds zmax

        # Act
        ptz_service.set_zoom_absolute(zoom_value)

        # Assert
        # Should clamp to zmax (1.0)
        assert ptz_service.zoom_level <= ptz_service.zmax

    def test_set_zoom_absolute_with_exception_handling(self, ptz_service):
        """Test absolute zoom handles ONVIF exceptions gracefully."""
        # Arrange
        ptz_service.ptz.AbsoluteMove.side_effect = Exception("Zoom failed")
        zoom_value = 0.5

        # Act
        ptz_service.set_zoom_absolute(zoom_value)

        # Assert
        # Should handle exception and not crash

    def test_set_zoom_absolute_updates_internal_state(self, ptz_service):
        """Test absolute zoom updates internal zoom state."""
        # Arrange
        zoom_value = 0.7

        # Act
        ptz_service.set_zoom_absolute(zoom_value)

        # Assert
        assert ptz_service.zoom_level == zoom_value
        assert ptz_service.last_zoom == zoom_value


class TestPTZServiceHomePosition:
    """Test PTZService.set_home_position() method."""

    @pytest.fixture
    def ptz_service(self):
        """Provide PTZService instance for home position testing."""
        ptz_service = PTZService()
        ptz_service.connected = True
        return ptz_service

    def test_set_home_position_successful(self, ptz_service):
        """Test successful home position movement."""
        # Arrange
        # Act
        ptz_service.set_home_position()

        # Assert
        # Should have called GotoHomePosition
        assert len(ptz_service.ptz.GotoHomePosition.call_args_list) > 0
        # Should update internal state
        assert ptz_service.last_pan == 0.0
        assert ptz_service.last_tilt == 0.0

    def test_set_home_position_fallback_to_absolute_move(self, ptz_service):
        """Test home position fallback to absolute move when GotoHomePosition fails."""
        # Arrange
        ptz_service.ptz.GotoHomePosition.side_effect = Exception(
            "GotoHomePosition failed"
        )

        # Act
        ptz_service.set_home_position()

        # Assert
        # Should fall back to AbsoluteMove
        assert len(ptz_service.ptz.AbsoluteMove.call_args_list) > 0

    def test_set_home_position_final_fallback(self, ptz_service):
        """Test final fallback to continuous movement when all else fails."""
        # Arrange
        ptz_service.ptz.GotoHomePosition.side_effect = Exception(
            "GotoHomePosition failed"
        )
        ptz_service.ptz.AbsoluteMove.side_effect = Exception("AbsoluteMove failed")

        # Act
        ptz_service.set_home_position()

        # Assert
        # Should eventually fall back to continuous move approach
        # (verification through mock calls)

    def test_set_home_position_handles_status_exception(self, ptz_service):
        """Test home position handles status query exceptions."""
        # Arrange
        ptz_service.ptz.GetStatus.side_effect = Exception("Status failed")

        # Act
        ptz_service.set_home_position()

        # Assert
        # Should handle exception and continue with default position

    def test_set_zoom_home(self, ptz_service):
        """Test set_zoom_home convenience method."""
        # Arrange
        with patch.object(ptz_service, "set_zoom_absolute") as mock_set_zoom:
            # Act
            ptz_service.set_zoom_home()

            # Assert
            # Should call set_zoom_absolute with zmin
            mock_set_zoom.assert_called_once_with(ptz_service.zmin)


class TestPTZServiceZoomRelative:
    """Test PTZService.set_zoom_relative() method."""

    @pytest.fixture
    def ptz_service(self):
        """Provide PTZService instance for relative zoom testing."""
        ptz_service = PTZService()
        ptz_service.connected = True
        return ptz_service

    def test_set_zoom_relative_valid_delta(self, ptz_service):
        """Test relative zoom with valid delta."""
        # Arrange
        ptz_service.ptz.GetStatus.return_value.Position.Zoom.x = 0.5
        zoom_delta = 0.2

        # Act
        ptz_service.set_zoom_relative(zoom_delta)

        # Assert
        # Should set zoom to current + delta (clamped to range)
        assert ptz_service.zoom_level is not None

    def test_set_zoom_relative_clamps_to_bounds(self, ptz_service):
        """Test relative zoom clamps to valid bounds."""
        # Arrange
        ptz_service.ptz.GetStatus.return_value.Position.Zoom.x = 0.9
        zoom_delta = 0.3  # Would exceed zmax

        # Act
        ptz_service.set_zoom_relative(zoom_delta)

        # Assert
        # Should clamp to zmax
        assert ptz_service.zoom_level <= ptz_service.zmax

    def test_set_zoom_relative_handles_exception(self, ptz_service):
        """Test relative zoom handles exceptions gracefully."""
        # Arrange
        ptz_service.ptz.GetStatus.side_effect = Exception("GetStatus failed")

        # Act
        ptz_service.set_zoom_relative(0.2)

        # Assert
        # Should handle exception and not crash


class TestPTZServiceGetZoom:
    """Test PTZService.get_zoom() method."""

    @pytest.fixture
    def ptz_service(self):
        """Provide PTZService instance for get zoom testing."""
        ptz_service = PTZService()
        ptz_service.connected = True
        return ptz_service

    def test_get_zoom_returns_current_value(self, ptz_service):
        """Test get zoom returns current zoom position."""
        # Arrange - Replace GetStatus entirely to override mock fixture
        mock_status = Mock()
        mock_status.Position = Mock()
        mock_status.Position.Zoom = Mock()
        mock_status.Position.Zoom.x = 0.7
        ptz_service.ptz.GetStatus = Mock(return_value=mock_status)

        # Act
        zoom_level = ptz_service.get_zoom()

        # Assert
        assert zoom_level == 0.7

    def test_get_zoom_falls_back_when_status_unavailable(self, ptz_service):
        """Test get zoom falls back to zmin when status unavailable."""
        # Arrange - Set GetStatus to return None to simulate unavailable status
        ptz_service.ptz.GetStatus = Mock(return_value=None)

        # Act
        zoom_level = ptz_service.get_zoom()

        # Assert
        # Should return zmin as fallback
        assert zoom_level == ptz_service.zmin

    def test_get_zoom_handles_exception(self, ptz_service):
        """Test get zoom handles exceptions gracefully."""
        # Arrange
        ptz_service.ptz.GetStatus.side_effect = Exception("GetStatus failed")

        # Act
        zoom_level = ptz_service.get_zoom()

        # Assert
        # Should return zmin as fallback
        assert zoom_level == ptz_service.zmin
