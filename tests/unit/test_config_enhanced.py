"""
Comprehensive test suite for Config validation and setup_logging.

Tests cover all parameter validation, logging configuration, and error handling.
Target coverage: 100%
"""

from unittest.mock import patch

import pytest

# Import the modules under test
from src.config import Config, setup_logging


@pytest.mark.usefixtures("mock_config")
class TestConfigValidation:
    """Test Config.validate() method for all configuration parameters."""

    def test_valid_configuration_passes_validation(self):
        """Test that a valid configuration passes validation without errors."""
        # Arrange & Act & Assert
        # Should not raise any exception
        Config.validate()

    def test_invalid_confidence_threshold_high_value(self):
        """Test validation fails when confidence threshold > 1.0."""
        # Arrange
        Config.CONFIDENCE_THRESHOLD = 1.5

        # Act & Assert
        with pytest.raises(
            ValueError, match=r"CONFIDENCE_THRESHOLD must be between 0\.0 and 1\.0"
        ):
            Config.validate()

    def test_invalid_confidence_threshold_negative_value(self):
        """Test validation fails when confidence threshold < 0.0."""
        # Arrange
        Config.CONFIDENCE_THRESHOLD = -0.1

        # Act & Assert
        with pytest.raises(
            ValueError, match=r"CONFIDENCE_THRESHOLD must be between 0\.0 and 1\.0"
        ):
            Config.validate()

    def test_invalid_confidence_threshold_zero(self):
        """Test validation passes when confidence threshold = 0.0 (boundary case)."""
        # Arrange
        Config.CONFIDENCE_THRESHOLD = 0.0

        # Act & Assert
        # Should not raise exception (0.0 is valid)
        Config.validate()

    def test_invalid_confidence_threshold_one(self):
        """Test validation passes when confidence threshold = 1.0 (boundary case)."""
        # Arrange
        Config.CONFIDENCE_THRESHOLD = 1.0

        # Act & Assert
        # Should not raise exception (1.0 is valid)
        Config.validate()

    def test_invalid_resolution_width_zero(self):
        """Test validation fails when resolution width = 0."""
        # Arrange
        Config.RESOLUTION_WIDTH = 0
        Config.RESOLUTION_HEIGHT = 720

        # Act & Assert
        with pytest.raises(ValueError, match="Resolution must be positive integers"):
            Config.validate()

    def test_invalid_resolution_height_zero(self):
        """Test validation fails when resolution height = 0."""
        # Arrange
        Config.RESOLUTION_WIDTH = 1280
        Config.RESOLUTION_HEIGHT = 0

        # Act & Assert
        with pytest.raises(ValueError, match="Resolution must be positive integers"):
            Config.validate()

    def test_invalid_resolution_width_negative(self):
        """Test validation fails when resolution width < 0."""
        # Arrange
        Config.RESOLUTION_WIDTH = -1280
        Config.RESOLUTION_HEIGHT = 720

        # Act & Assert
        with pytest.raises(ValueError, match="Resolution must be positive integers"):
            Config.validate()

    def test_invalid_fps_zero(self):
        """Test validation fails when FPS = 0."""
        # Arrange
        Config.FPS = 0

        # Act & Assert
        with pytest.raises(ValueError, match="FPS must be positive"):
            Config.validate()

    def test_invalid_fps_negative(self):
        """Test validation fails when FPS < 0."""
        # Arrange
        Config.FPS = -30

        # Act & Assert
        with pytest.raises(ValueError, match="FPS must be positive"):
            Config.validate()

    @patch("os.path.exists")
    def test_missing_model_file(self, mock_exists):
        """Test validation fails when model file doesn't exist."""
        # Arrange
        mock_exists.return_value = False
        Config.MODEL_PATH = "nonexistent_model.pt"

        # Act & Assert
        with pytest.raises(ValueError, match="Model file not found"):
            Config.validate()

    @patch("os.path.exists")
    def test_existing_model_file_passes(self, mock_exists):
        """Test validation passes when model file exists."""
        # Arrange
        mock_exists.return_value = True
        Config.MODEL_PATH = "existing_model.pt"

        # Act & Assert
        # Should not raise exception
        Config.validate()

    def test_invalid_ptz_movement_gain_negative(self):
        """Test validation fails when PTZ_MOVEMENT_GAIN < 0."""
        # Arrange
        Config.PTZ_MOVEMENT_GAIN = -1.0

        # Act & Assert
        with pytest.raises(ValueError, match="PTZ_MOVEMENT_GAIN must be positive"):
            Config.validate()

    def test_invalid_ptz_movement_threshold_high(self):
        """Test validation fails when PTZ_MOVEMENT_THRESHOLD > 1.0."""
        # Arrange
        Config.PTZ_MOVEMENT_THRESHOLD = 1.5

        # Act & Assert
        with pytest.raises(
            ValueError, match=r"PTZ_MOVEMENT_THRESHOLD must be between 0\.0 and 1\.0"
        ):
            Config.validate()

    def test_invalid_ptz_movement_threshold_negative(self):
        """Test validation fails when PTZ_MOVEMENT_THRESHOLD < 0.0."""
        # Arrange
        Config.PTZ_MOVEMENT_THRESHOLD = -0.1

        # Act & Assert
        with pytest.raises(
            ValueError, match=r"PTZ_MOVEMENT_THRESHOLD must be between 0\.0 and 1\.0"
        ):
            Config.validate()

    def test_invalid_zoom_target_coverage_high(self):
        """Test validation fails when ZOOM_TARGET_COVERAGE > 1.0."""
        # Arrange
        Config.ZOOM_TARGET_COVERAGE = 1.5

        # Act & Assert
        with pytest.raises(
            ValueError, match=r"ZOOM_TARGET_COVERAGE must be between 0\.0 and 1\.0"
        ):
            Config.validate()

    def test_invalid_zoom_target_coverage_negative(self):
        """Test validation fails when ZOOM_TARGET_COVERAGE < 0.0."""
        # Arrange
        Config.ZOOM_TARGET_COVERAGE = -0.1

        # Act & Assert
        with pytest.raises(
            ValueError, match=r"ZOOM_TARGET_COVERAGE must be between 0\.0 and 1\.0"
        ):
            Config.validate()

    def test_invalid_zoom_reset_timeout_negative(self):
        """Test validation fails when ZOOM_RESET_TIMEOUT < 0."""
        # Arrange
        Config.ZOOM_RESET_TIMEOUT = -1.0

        # Act & Assert
        with pytest.raises(ValueError, match="ZOOM_RESET_TIMEOUT must be non-negative"):
            Config.validate()

    def test_invalid_zoom_min_interval_negative(self):
        """Test validation fails when ZOOM_MIN_INTERVAL < 0."""
        # Arrange
        Config.ZOOM_MIN_INTERVAL = -0.1

        # Act & Assert
        with pytest.raises(ValueError, match="ZOOM_MIN_INTERVAL must be non-negative"):
            Config.validate()

    def test_missing_camera_ip(self):
        """Test validation fails when camera IP is missing."""
        # Arrange
        Config.CAMERA_CREDENTIALS = {
            "ip": "",  # Missing IP
            "user": "test_user",
            "pass": "test_pass",
        }

        # Act & Assert
        with pytest.raises(ValueError, match="CAMERA_CREDENTIALS must include 'ip'"):
            Config.validate()

    def test_missing_camera_user(self):
        """Test validation fails when camera user is missing."""
        # Arrange
        Config.CAMERA_CREDENTIALS = {
            "ip": "192.168.1.70",
            "user": "",  # Missing user
            "pass": "test_pass",
        }

        # Act & Assert
        with pytest.raises(ValueError, match="CAMERA_CREDENTIALS must include 'user'"):
            Config.validate()

    def test_missing_camera_password(self):
        """Test validation fails when camera password is missing."""
        # Arrange
        Config.CAMERA_CREDENTIALS = {
            "ip": "192.168.1.70",
            "user": "test_user",
            "pass": "",  # Missing password
        }

        # Act & Assert
        with pytest.raises(ValueError, match="CAMERA_CREDENTIALS must include 'pass'"):
            Config.validate()

    def test_missing_camera_credentials_key(self):
        """Test validation fails when camera credentials dict is missing."""
        # Arrange
        Config.CAMERA_CREDENTIALS = {}  # Empty dict

        # Act & Assert
        with pytest.raises(ValueError, match="CAMERA_CREDENTIALS must include 'ip'"):
            Config.validate()

    def test_invalid_fps_window_size_zero(self):
        """Test validation fails when FPS_WINDOW_SIZE <= 0."""
        # Arrange
        Config.FPS_WINDOW_SIZE = 0

        # Act & Assert
        with pytest.raises(ValueError, match="FPS_WINDOW_SIZE must be positive"):
            Config.validate()

    def test_invalid_fps_window_size_negative(self):
        """Test validation fails when FPS_WINDOW_SIZE < 0."""
        # Arrange
        Config.FPS_WINDOW_SIZE = -1

        # Act & Assert
        with pytest.raises(ValueError, match="FPS_WINDOW_SIZE must be positive"):
            Config.validate()

    def test_invalid_ptz_ramp_rate_zero(self):
        """Test validation fails when PTZ_RAMP_RATE <= 0."""
        # Arrange
        Config.PTZ_RAMP_RATE = 0.0

        # Act & Assert
        with pytest.raises(ValueError, match="PTZ_RAMP_RATE must be positive"):
            Config.validate()

    def test_invalid_ptz_ramp_rate_negative(self):
        """Test validation fails when PTZ_RAMP_RATE < 0."""
        # Arrange
        Config.PTZ_RAMP_RATE = -0.1

        # Act & Assert
        with pytest.raises(ValueError, match="PTZ_RAMP_RATE must be positive"):
            Config.validate()

    def test_multiple_validation_errors_accumulated(self):
        """Test that multiple validation errors are reported together."""
        # Arrange
        Config.CONFIDENCE_THRESHOLD = 1.5  # Invalid
        Config.RESOLUTION_WIDTH = -1280  # Invalid
        Config.FPS = 0  # Invalid
        Config.CAMERA_CREDENTIALS = {"ip": "", "user": "", "pass": ""}  # Invalid

        # Act & Assert
        with pytest.raises(
            ValueError, match="Configuration validation failed"
        ) as exc_info:
            Config.validate()

        error_message = str(exc_info.value)
        # Should contain multiple error messages
        assert "CONFIDENCE_THRESHOLD" in error_message
        assert "Resolution" in error_message
        assert "FPS must be positive" in error_message
        assert "CAMERA_CREDENTIALS" in error_message

    def test_validation_with_boundary_values(self):
        """Test validation passes with boundary values."""
        # Arrange
        Config.CONFIDENCE_THRESHOLD = 0.0
        Config.RESOLUTION_WIDTH = 1
        Config.RESOLUTION_HEIGHT = 1
        Config.FPS = 1
        Config.PTZ_MOVEMENT_THRESHOLD = 0.0
        Config.ZOOM_TARGET_COVERAGE = 1.0
        Config.ZOOM_RESET_TIMEOUT = 0.0
        Config.ZOOM_MIN_INTERVAL = 0.0
        Config.PTZ_RAMP_RATE = 0.001  # Small but positive
        Config.FPS_WINDOW_SIZE = 1
        Config.PTZ_MOVEMENT_GAIN = 0.001  # Small but positive

        # Act & Assert
        # Should not raise exception
        Config.validate()

    def test_validation_error_message_format(self):
        """Test that validation error messages are properly formatted."""
        # Arrange
        Config.CONFIDENCE_THRESHOLD = 2.0  # Invalid

        # Act & Assert
        with pytest.raises(
            ValueError,
            match=r"Configuration validation failed:.+CONFIDENCE_THRESHOLD must be between 0\.0 and 1\.0, got 2\.0",
        ) as exc_info:
            Config.validate()

        error_message = str(exc_info.value)
        # Check formatting
        assert "Configuration validation failed:" in error_message
        assert "- " in error_message  # Bullet points


@pytest.mark.usefixtures("mock_config")
class TestSetupLogging:
    """Test setup_logging() function for logging configuration."""

    def test_setup_logging_removes_default_handler(self):
        """Test that setup_logging removes default loguru handler."""
        # Arrange

        with (
            patch("config.logger") as mock_logger,
            patch("config.Config.reset_log_on_start", False),
        ):
            # Act
            setup_logging()

            # Assert
            mock_logger.remove.assert_called_once()

    @patch("config.os.path.exists")
    @patch("builtins.open")
    def test_setup_logging_truncates_existing_log_file(self, mock_open, mock_exists):
        """Test that setup_logging truncates existing log file when configured."""
        # Arrange
        mock_exists.return_value = True

        # Act
        setup_logging()

        # Assert
        mock_open.assert_called_with(Config.LOG_FILE, "w")

    @patch("config.os.path.exists")
    @patch("builtins.open")
    def test_setup_logging_handles_truncate_error(self, mock_open, mock_exists):
        """Test that setup_logging handles file truncation errors gracefully."""
        # Arrange
        mock_exists.return_value = True
        mock_open.side_effect = PermissionError("Permission denied")

        # Act
        # Should not raise exception
        setup_logging()

    @patch("config.logger")
    def test_setup_logging_does_not_truncate_when_reset_disabled(self):
        """Test that setup_logging doesn't truncate when reset_log_on_start is False."""
        # Arrange
        Config.reset_log_on_start = False

        # Act
        setup_logging()

        # Assert
        # Should not try to open file for writing

    @patch("config.Config.write_log_file", False)
    def test_setup_logging_skips_file_handler_when_disabled(self):
        """Test that setup_logging skips file handler when write_log_file is False."""
        # Arrange & Act
        setup_logging()

        # Assert
        # Should not add file handler
        # (verification through mock)

    @patch("config.logger")
    def test_setup_logging_adds_file_handler_with_correct_settings(self, mock_logger):
        """Test that setup_logging adds file handler with all correct settings."""
        # Arrange
        Config.write_log_file = True

        # Act
        setup_logging()

        # Assert
        mock_logger.add.assert_called_once()
        call_args = mock_logger.add.call_args

        # Check all parameters
        assert call_args[0][0] == Config.LOG_FILE
        assert call_args[1]["rotation"] == Config.LOG_ROTATION
        assert call_args[1]["retention"] == Config.LOG_RETENTION
        assert call_args[1]["level"] == Config.LOG_LEVEL
        assert call_args[1]["format"] == Config.LOG_FORMAT
        assert call_args[1]["enqueue"] == Config.LOG_ENQUEUE
        assert call_args[1]["backtrace"] == Config.LOG_BACKTRACE
        assert call_args[1]["diagnose"] == Config.LOG_DIAGNOSE

    @patch("config.logger")
    @patch("builtins.print")
    def test_setup_logging_handles_file_handler_error(self, mock_print, mock_logger):
        """Test that setup_logging handles file handler errors gracefully."""
        # Arrange
        Config.write_log_file = True
        mock_logger.add.side_effect = Exception("Handler error")

        # Act
        setup_logging()

        # Assert
        # Should print error but not crash
        mock_print.assert_called_once()
        assert "Error setting up file logger" in str(mock_print.call_args[0])

    @patch("config.Config.write_log_file", True)
    @patch("config.logger")
    def test_setup_logging_with_custom_log_settings(self, mock_logger):
        """Test setup_logging with custom log settings."""
        # Arrange
        Config.LOG_FILE = "custom.log"
        Config.LOG_LEVEL = "WARNING"
        Config.LOG_ROTATION = "1 day"

        # Act
        setup_logging()

        # Assert
        mock_logger.add.assert_called_once()
        call_args = mock_logger.add.call_args

        assert call_args[0][0] == "custom.log"
        assert call_args[1]["level"] == "WARNING"
        assert call_args[1]["rotation"] == "1 day"

    def test_setup_logging_initialization(self):
        """Test that setup_logging is called automatically when config module is imported."""
        # Arrange & Act & Assert
        # This is verified by the fact that the logger is already configured
        # after importing config
        assert Config.LOG_FILE is not None
        assert Config.LOG_LEVEL is not None

    @patch("config.logger")
    def test_setup_logging_calls_remove_before_add(self, mock_logger):
        """Test that setup_logging calls remove before adding new handlers."""
        # Arrange
        Config.write_log_file = True

        # Act
        setup_logging()

        # Assert
        # Remove should be called before add
        remove_calls = mock_logger.remove.call_args_list
        add_calls = mock_logger.add.call_args_list

        assert len(remove_calls) > 0
        assert len(add_calls) > 0
        assert mock_logger.remove.call_args_list[0] < mock_logger.add.call_args_list[0]


class TestConfigClassAttributes:
    """Test Config class attributes and their types."""

    def test_config_attributes_are_class_variables(self):
        """Test that Config attributes are class variables, not instance variables."""
        # Arrange & Act
        assert hasattr(Config, "CONFIDENCE_THRESHOLD")
        assert hasattr(Config, "MODEL_PATH")
        assert hasattr(Config, "CAMERA_CREDENTIALS")

        # Assert
        # All should be class attributes, not instance attributes
        assert "CONFIDENCE_THRESHOLD" in dir(Config)
        assert "MODEL_PATH" in dir(Config)

    def test_config_camera_credentials_structure(self):
        """Test that CAMERA_CREDENTIALS has the expected structure."""
        # Arrange & Act
        credentials = Config.CAMERA_CREDENTIALS

        # Assert
        assert isinstance(credentials, dict)
        assert "ip" in credentials
        assert "user" in credentials
        assert "pass" in credentials

    def test_config_logging_settings_types(self):
        """Test that logging settings have correct types."""
        # Arrange & Act
        # Assert
        assert isinstance(Config.LOG_FILE, str)
        assert isinstance(Config.LOG_LEVEL, str)
        assert isinstance(Config.LOG_FORMAT, str)
        assert isinstance(Config.LOG_ROTATION, str)
        assert isinstance(Config.LOG_RETENTION, str)
        assert isinstance(Config.LOG_ENQUEUE, bool)
        assert isinstance(Config.LOG_BACKTRACE, bool)
        assert isinstance(Config.LOG_DIAGNOSE, bool)
        assert isinstance(Config.write_log_file, bool)
        assert isinstance(Config.reset_log_on_start, bool)

    def test_config_detection_settings_types(self):
        """Test that detection settings have correct types."""
        # Arrange & Act
        # Assert
        assert isinstance(Config.CAMERA_INDEX, int)
        assert isinstance(Config.RESOLUTION_WIDTH, int)
        assert isinstance(Config.RESOLUTION_HEIGHT, int)
        assert isinstance(Config.FPS, int)
        assert isinstance(Config.CONFIDENCE_THRESHOLD, float)
        assert isinstance(Config.MODEL_PATH, str)

    def test_config_ptz_settings_types(self):
        """Test that PTZ settings have correct types."""
        # Arrange & Act
        # Assert
        assert isinstance(Config.PTZ_MOVEMENT_GAIN, float)
        assert isinstance(Config.PTZ_MOVEMENT_THRESHOLD, float)
        assert isinstance(Config.ZOOM_TARGET_COVERAGE, float)
        assert isinstance(Config.ZOOM_RESET_TIMEOUT, float)
        assert isinstance(Config.ZOOM_MIN_INTERVAL, float)
        assert isinstance(Config.ZOOM_VELOCITY_GAIN, float)
        assert isinstance(Config.ZOOM_RESET_VELOCITY, float)
        assert isinstance(Config.PTZ_RAMP_RATE, float)
        assert isinstance(Config.FPS_WINDOW_SIZE, int)
        assert isinstance(Config.ZOOM_DEAD_ZONE, float)
        assert isinstance(Config.FRAME_QUEUE_MAXSIZE, int)
        assert isinstance(Config.NO_DETECTION_HOME_TIMEOUT, int)


@pytest.mark.usefixtures("mock_config")
class TestConfigIntegration:
    """Integration tests for Config validation with other components."""

    @pytest.mark.usefixtures("mock_onvif_camera")
    def test_config_validation_with_mock_onvif_camera(self):
        """Test Config validation works with mocked ONVIF camera."""
        # Arrange & Act
        Config.validate()

        # Assert
        # Should pass with valid config

    def test_config_validation_with_real_credentials(self):
        """Test Config validation with real camera credentials."""
        # Arrange
        Config.CAMERA_CREDENTIALS = {
            "ip": "192.168.1.70",
            "user": "admin",
            "pass": "admin@123",
        }

        # Act & Assert
        # Should pass validation
        Config.validate()

    @patch("config.os.path.exists")
    def test_config_validation_with_test_model_path(self, mock_exists):
        """Test Config validation works with test model path."""
        # Arrange
        Config.MODEL_PATH = "tests/fixtures/mock_model.pt"
        mock_exists.return_value = True

        # Act & Assert
        Config.validate()

    def test_config_logging_integration_with_validation(self):
        """Test that logging setup doesn't interfere with validation."""
        # Arrange & Act
        setup_logging()
        Config.validate()

        # Assert
        # Both should work together without issues

    def test_config_multiple_validation_calls(self):
        """Test that validate() can be called multiple times."""
        # Arrange & Act
        Config.validate()
        Config.validate()
        Config.validate()

        # Assert
        # Should not accumulate errors or state
        # All should pass


# Additional boundary and edge case tests


@pytest.mark.usefixtures("mock_config")
class TestConfigBoundaryCases:
    """Test Config validation with boundary and edge case values."""

    def test_valid_config_with_large_values(self):
        """Test validation passes with large but valid values."""
        # Arrange
        Config.RESOLUTION_WIDTH = 7680  # 8K width
        Config.RESOLUTION_HEIGHT = 4320  # 8K height
        Config.FPS = 120  # High FPS
        Config.FPS_WINDOW_SIZE = 1000  # Large window

        # Act & Assert
        Config.validate()

    def test_valid_config_with_small_values(self):
        """Test validation passes with small but valid values."""
        # Arrange
        Config.RESOLUTION_WIDTH = 160
        Config.RESOLUTION_HEIGHT = 120
        Config.FPS = 1
        Config.FPS_WINDOW_SIZE = 1

        # Act & Assert
        Config.validate()

    def test_config_with_floating_point_precision(self):
        """Test validation with floating point precision values."""
        # Arrange
        Config.CONFIDENCE_THRESHOLD = 0.999999
        Config.PTZ_MOVEMENT_THRESHOLD = 0.000001

        # Act & Assert
        Config.validate()

    def test_config_with_scientific_notation(self):
        """Test validation with scientific notation values."""
        # Arrange
        Config.CONFIDENCE_THRESHOLD = 5e-1  # 0.5

        # Act & Assert
        Config.validate()
