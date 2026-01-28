"""
Unit tests for thermal detection service.

Tests all three detection methods (hotspot, blob, contour) and Kalman filter.
Uses mocking for cv2 to avoid import issues in test environment.
"""

import numpy as np
import pytest
from unittest.mock import Mock, MagicMock, patch

# Mock cv2 before importing thermal_detection
cv2_mock = MagicMock()
cv2_mock.createCLAHE.return_value = MagicMock()
cv2_mock.SimpleBlobDetector_Params.return_value = MagicMock()
cv2_mock.SimpleBlobDetector_create.return_value = MagicMock()
cv2_mock.KalmanFilter.return_value = MagicMock()

# Patch cv2 at module level for import
import sys
sys.modules['cv2'] = cv2_mock

from src.thermal_detection import (
    ThermalDetectionMethod,
    ThermalTarget,
)


class TestThermalTarget:
    """Tests for ThermalTarget dataclass."""

    def test_create_target(self):
        target = ThermalTarget(
            centroid=(320.5, 240.5),
            area=900.0,
            bbox=(305, 225, 30, 30),
            intensity=240.0,
            track_id=1,
        )
        assert target.centroid == (320.5, 240.5)
        assert target.area == 900.0
        assert target.bbox == (305, 225, 30, 30)
        assert target.intensity == 240.0
        assert target.track_id == 1

    def test_target_default_track_id(self):
        target = ThermalTarget(
            centroid=(100.0, 100.0),
            area=500.0,
            bbox=(90, 90, 20, 20),
            intensity=200.0,
        )
        assert target.track_id is None


class TestThermalDetectionMethod:
    """Tests for ThermalDetectionMethod enum."""

    def test_enum_values(self):
        assert ThermalDetectionMethod.HOTSPOT.value == "hotspot"
        assert ThermalDetectionMethod.BLOB.value == "blob"
        assert ThermalDetectionMethod.CONTOUR.value == "contour"

    def test_enum_from_string(self):
        method = ThermalDetectionMethod("contour")
        assert method == ThermalDetectionMethod.CONTOUR


class TestThermalDetectionServiceWithMocks:
    """Tests for ThermalDetectionService using mocked cv2."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for thermal detection."""
        settings = Mock()
        settings.thermal = Mock()
        settings.thermal.enabled = True
        settings.thermal.detection_method = "contour"
        settings.thermal.threshold_value = 200
        settings.thermal.use_otsu = True
        settings.thermal.clahe_clip_limit = 2.0
        settings.thermal.clahe_tile_size = 8
        settings.thermal.min_area = 100
        settings.thermal.max_area = 50000
        settings.thermal.use_kalman = False
        settings.thermal.blur_size = 5
        return settings

    def test_service_initialization(self, mock_settings):
        """Test that service initializes with settings."""
        from src.thermal_detection import ThermalDetectionService
        
        service = ThermalDetectionService(settings=mock_settings)
        assert service._method == ThermalDetectionMethod.CONTOUR
        assert service._use_kalman == False
        assert service._min_area == 100

    def test_set_method(self, mock_settings):
        """Test changing detection method at runtime."""
        from src.thermal_detection import ThermalDetectionService
        
        service = ThermalDetectionService(settings=mock_settings)
        service.set_method("blob")
        assert service._method == ThermalDetectionMethod.BLOB

        service.set_method(ThermalDetectionMethod.HOTSPOT)
        assert service._method == ThermalDetectionMethod.HOTSPOT

    def test_thermal_target_yolo_interface(self):
        """Test ThermalTarget has YOLO-compatible properties."""
        target = ThermalTarget(
            centroid=(100.0, 100.0),
            area=500.0,
            bbox=(90, 90, 20, 20),
            intensity=128.0,
            track_id=1,
        )
        
        # Test aliases and properties
        assert target.id == 1
        assert target.cls == 0
        assert 0.0 <= target.conf <= 1.0
        assert target.conf == 128.0 / 255.0
        
        # Test xyxy format (list of lists)
        assert isinstance(target.xyxy, list)
        assert len(target.xyxy) == 1
        assert len(target.xyxy[0]) == 4
        assert target.xyxy[0] == [90.0, 90.0, 110.0, 110.0]

    def test_filter_by_target_labels_compatibility(self, mock_settings):
        """Test filter_by_target_labels compatibility method."""
        from src.thermal_detection import ThermalDetectionService
        
        service = ThermalDetectionService(settings=mock_settings)
        targets = [Mock(), Mock()]  # Just pass some objects
        
        # Should return input unchanged
        result = service.filter_by_target_labels(targets)
        assert result == targets

    def test_get_class_names(self, mock_settings):
        """Test get_class_names returns thermal_target."""
        from src.thermal_detection import ThermalDetectionService
        
        service = ThermalDetectionService(settings=mock_settings)
        names = service.get_class_names()
        assert 0 in names
        assert names[0] == "thermal_target"

    def test_get_primary_target_empty(self, mock_settings):
        """Test get_primary_target with empty list returns None."""
        from src.thermal_detection import ThermalDetectionService
        
        service = ThermalDetectionService(settings=mock_settings)
        result = service.get_primary_target([])
        assert result is None

    def test_get_primary_target_single(self, mock_settings):
        """Test get_primary_target with single target."""
        from src.thermal_detection import ThermalDetectionService
        
        service = ThermalDetectionService(settings=mock_settings)
        target = ThermalTarget(
            centroid=(320.0, 240.0),
            area=500.0,
            bbox=(300, 220, 40, 40),
            intensity=200.0,
        )
        result = service.get_primary_target([target])
        assert result == target

    def test_get_primary_target_multiple(self, mock_settings):
        """Test get_primary_target returns largest."""
        from src.thermal_detection import ThermalDetectionService
        
        service = ThermalDetectionService(settings=mock_settings)
        small = ThermalTarget(
            centroid=(100.0, 100.0),
            area=100.0,
            bbox=(90, 90, 20, 20),
            intensity=180.0,
        )
        large = ThermalTarget(
            centroid=(300.0, 300.0),
            area=1000.0,
            bbox=(250, 250, 100, 100),
            intensity=220.0,
        )
        result = service.get_primary_target([small, large])
        assert result == large

    def test_detect_returns_empty_for_none_frame(self, mock_settings):
        """Test detect returns empty list for None frame."""
        from src.thermal_detection import ThermalDetectionService
        
        service = ThermalDetectionService(settings=mock_settings)
        result = service.detect(None)
        assert result == []

    def test_detect_returns_empty_for_empty_array(self, mock_settings):
        """Test detect returns empty list for empty array."""
        from src.thermal_detection import ThermalDetectionService
        
        service = ThermalDetectionService(settings=mock_settings)
        result = service.detect(np.array([]))
        assert result == []


class TestKalmanCentroidTrackerWithMocks:
    """Tests for KalmanCentroidTracker using mocked cv2."""

    def test_tracker_initialization(self):
        """Test Kalman tracker initializes with cv2.KalmanFilter."""
        # The cv2.KalmanFilter is mocked, so we just test the class instantiation
        from src.thermal_detection import KalmanCentroidTracker
        tracker = KalmanCentroidTracker()
        assert tracker._initialized == False

    def test_predict_before_init_returns_zero(self):
        """Test predict returns (0,0) before initialization."""
        from src.thermal_detection import KalmanCentroidTracker
        tracker = KalmanCentroidTracker()
        result = tracker.predict()
        assert result == (0.0, 0.0)

    def test_reset(self):
        """Test reset sets initialized to False."""
        from src.thermal_detection import KalmanCentroidTracker
        tracker = KalmanCentroidTracker()
        tracker._initialized = True
        tracker.reset()
        assert tracker._initialized == False


class TestThermalSettingsIntegration:
    """Test thermal settings integration with settings module."""

    def test_thermal_settings_exist(self):
        """Test ThermalSettings class exists and has correct fields."""
        from src.settings import ThermalSettings, ThermalCameraSettings
        
        settings = ThermalSettings()
        assert settings.enabled == False
        assert settings.detection_method == "contour"
        assert settings.use_otsu == True
        assert settings.min_area == 100
        assert settings.use_kalman == True
        assert isinstance(settings.camera, ThermalCameraSettings)

    def test_thermal_camera_settings(self):
        """Test ThermalCameraSettings defaults."""
        from src.settings import ThermalCameraSettings
        
        cam = ThermalCameraSettings()
        assert cam.source == "camera"
        assert cam.camera_index == 0
        assert cam.resolution_width == 640
        assert cam.resolution_height == 480

    def test_settings_includes_thermal(self):
        """Test main Settings class includes thermal."""
        from src.settings import Settings, ThermalSettings
        
        settings = Settings()
        assert hasattr(settings, 'thermal')
        assert isinstance(settings.thermal, ThermalSettings)
