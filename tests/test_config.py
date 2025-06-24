import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure the main project directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config
from ptz_controller import PTZService

class TestConfigAndPTZIntegration(unittest.TestCase):
    """
    Test suite for configuration loading and its integration with the PTZService.
    It uses a mock ONVIFCamera to avoid dependency on a physical camera.
    """

    @patch('ptz_controller.ONVIFCamera')
    def test_ptz_service_initialization_with_config(self, mock_onvif_camera):
        """
        Verify that PTZService correctly initializes using settings from the Config class.
        """
        # Arrange: Mock the ONVIFCamera and its dependent services
        mock_camera_instance = MagicMock()
        mock_onvif_camera.return_value = mock_camera_instance

        # Mock media and PTZ services
        mock_media_service = MagicMock()
        mock_ptz_service = MagicMock()
        mock_camera_instance.create_media_service.return_value = mock_media_service
        mock_camera_instance.create_ptz_service.return_value = mock_ptz_service

        # Mock profile and PTZ configuration options
        mock_profile = MagicMock()
        mock_profile.token = "profile_token_123"
        mock_profile.Name = "TestProfile"
        mock_profile.PTZConfiguration.token = "ptz_config_token_456"
        mock_media_service.GetProfiles.return_value = [mock_profile]

        mock_options = MagicMock()
        mock_options.Spaces.ContinuousPanTiltVelocitySpace[0].XRange.Max = 1.0
        mock_options.Spaces.ContinuousPanTiltVelocitySpace[0].XRange.Min = -1.0
        mock_options.Spaces.ContinuousPanTiltVelocitySpace[0].YRange.Max = 1.0
        mock_options.Spaces.ContinuousPanTiltVelocitySpace[0].YRange.Min = -1.0
        mock_options.Spaces.AbsoluteZoomPositionSpace[0].XRange.Min = 0.0
        mock_options.Spaces.AbsoluteZoomPositionSpace[0].XRange.Max = 1.0
        mock_ptz_service.GetConfigurationOptions.return_value = mock_options
        
        # Mock the create_type method for ContinuousMove
        mock_continuous_move_request = MagicMock()
        mock_ptz_service.create_type.return_value = mock_continuous_move_request

        # Act: Initialize PTZService
        ptz_service = PTZService()

        # Assert: Check that ONVIFCamera was called with credentials from Config
        mock_onvif_camera.assert_called_once_with(
            Config.CAMERA_CREDENTIALS["ip"],
            80,
            Config.CAMERA_CREDENTIALS["user"],
            Config.CAMERA_CREDENTIALS["pass"]
        )

        # Assert: Verify that the service is marked as connected
        self.assertTrue(ptz_service.connected)

        # Assert: Check if the correct profile was used
        self.assertEqual(ptz_service.profile.token, "profile_token_123")

        # Assert: Check if PTZ ranges are set correctly from mock options
        self.assertEqual(ptz_service.xmax, 1.0)
        self.assertEqual(ptz_service.xmin, -1.0)
        self.assertEqual(ptz_service.ymax, 1.0)
        self.assertEqual(ptz_service.ymin, -1.0)
        self.assertEqual(ptz_service.zmin, 0.0)
        self.assertEqual(ptz_service.zmax, 1.0)

        # Assert: Ensure the continuous move request was created
        mock_ptz_service.create_type.assert_called_with('ContinuousMove')
        self.assertIsNotNone(ptz_service.request)

if __name__ == '__main__':
    unittest.main()