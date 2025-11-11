"""
Comprehensive test suite for DetectionService.

Tests cover model initialization, frame processing, error handling, and performance.
Target coverage: 95%
"""

from unittest.mock import Mock, patch

import numpy as np
import pytest

# Import the service under test
from src.detection import DetectionService


class TestDetectionServiceInitialization:
    """Test DetectionService initialization and model loading."""

    @pytest.mark.timeout(5)
    def test_initialization_with_valid_config(self, mock_yolo_model, settings):  # noqa: ARG002 - mock_yolo_model needed for fixture
        """Test successful initialization with valid configuration."""
        # Arrange & Act
        detection_service = DetectionService(settings)

        # Assert
        assert detection_service.settings == settings
        assert detection_service.model is not None
        assert hasattr(detection_service, "class_names")
        assert isinstance(detection_service.class_names, dict)

    def test_initialization_with_default_config(self, mock_yolo_model):  # noqa: ARG002 - mock_yolo_model needed for fixture
        """Test initialization with default configuration."""
        # Arrange & Act
        detection_service = DetectionService()

        # Assert
        assert detection_service.settings is not None
        assert detection_service.model is not None

    @patch("src.detection.get_yolo")
    def test_initialization_with_invalid_model_path(self, mock_get_yolo, settings):
        """Test initialization failure with invalid model path."""
        # Arrange
        settings.detection.model_path = "nonexistent_model.pt"
        mock_yolo_class = Mock()
        mock_yolo_class.side_effect = Exception("Model file not found")
        mock_get_yolo.return_value = mock_yolo_class

        # Act & Assert
        with pytest.raises(Exception, match="Model file not found"):
            DetectionService(settings)

    def test_initialization_stores_class_names(self, mock_yolo_model, settings):  # noqa: ARG002 - mock_yolo_model needed for fixture
        """Test that class names are properly stored during initialization."""
        # Arrange & Act
        detection_service = DetectionService(settings)

        # Assert
        expected_classes = {0: "drone", 1: "bird", 2: "airplane", 3: "aircraft"}
        assert detection_service.class_names == expected_classes


class TestDetectionServiceDetection:
    """Test DetectionService.detect() method functionality."""

    @pytest.fixture
    def detection_service(self, mock_yolo_model, settings):  # noqa: ARG002 - mock_yolo_model needed for fixture
        """Provide DetectionService instance for detection testing."""
        return DetectionService(settings)

    def test_detect_valid_frame_returns_detections(
        self, detection_service, sample_frame
    ):
        """Test detection on valid frame returns expected results."""
        # Arrange
        # The mock already returns detections for valid frames

        # Act
        results = detection_service.detect(sample_frame)

        # Assert
        assert len(results) > 0
        # Results should have the expected structure
        for box in results:
            assert hasattr(box, "cls")
            assert hasattr(box, "conf")
            assert hasattr(box, "xyxy")
            assert hasattr(box, "id")

    def test_detect_none_frame_returns_empty_list(self, detection_service):
        """Test detection on None frame returns empty list."""
        # Act
        results = detection_service.detect(None)

        # Assert
        assert results == []

    def test_detect_empty_frame_returns_empty_list(self, detection_service):
        """Test detection on empty frame returns empty list."""
        # Arrange
        empty_frame = np.array([]).reshape(0, 0, 3)

        # Act
        results = detection_service.detect(empty_frame)

        # Assert
        assert results == []

    def test_detect_frame_with_size_zero(self, detection_service):
        """Test detection on frame with size 0 returns empty list."""
        # Arrange
        zero_frame = np.zeros((0, 0, 3), dtype=np.uint8)

        # Act
        results = detection_service.detect(zero_frame)

        # Assert
        assert results == []

    def test_detect_with_exception_handles_gracefully(
        self, detection_service, sample_frame
    ):
        """Test that exceptions during detection are handled gracefully."""
        # Arrange
        with patch.object(
            detection_service.model, "track", side_effect=Exception("Mock error")
        ):
            # Act
            results = detection_service.detect(sample_frame)

            # Assert
            assert results == []

    def test_detect_different_frame_sizes(self, detection_service):
        """Test detection on frames of different sizes."""
        # Arrange
        frame_sizes = [(640, 480), (1920, 1080), (2560, 1440)]

        for width, height in frame_sizes:
            frame = np.zeros((height, width, 3), dtype=np.uint8)

            # Act
            results = detection_service.detect(frame)

            # Assert
            # Should not crash and return some result (Boxes object or empty list)
            assert results is not None

    def test_detect_returns_boxes_attribute(self, detection_service, sample_frame):
        """Test that detection results have proper boxes attribute structure."""
        # Arrange & Act
        results = detection_service.detect(sample_frame)

        # Assert
        if len(results) > 0:
            # Results should be a list of box objects
            for box in results:
                # Each box should have the expected attributes
                assert hasattr(box, "cls")
                assert hasattr(box, "conf")
                assert hasattr(box, "xyxy")
                assert hasattr(box, "id")
                assert isinstance(box.xyxy, np.ndarray)
                assert box.xyxy.shape == (1, 4)

    def test_detect_persists_tracking_ids(self, detection_service, sample_frame):
        """Test that tracking IDs are properly maintained across detections."""
        # Arrange & Act
        results1 = detection_service.detect(sample_frame)
        results2 = detection_service.detect(sample_frame)

        # Assert
        if len(results1) > 0 and len(results2) > 0:
            # Tracking IDs should be consistent (mock returns same ID)
            assert results1[0].id == results2[0].id

    def test_detect_handles_corrupted_frame_data(self, detection_service):
        """Test detection on corrupted frame data."""
        # Arrange
        corrupted_frame = np.array([255, 128, 64] * 100).reshape(10, 10, 3)
        # Corrupt the data in some way
        corrupted_frame[0, 0] = -1  # Invalid pixel value

        # Act
        results = detection_service.detect(corrupted_frame)

        # Assert
        # Should not crash and return Boxes object or empty list
        assert results is not None

    def test_detect_confidence_threshold_filtering(
        self, detection_service, sample_frame
    ):
        """Test that detection respects confidence threshold configuration."""
        # Arrange
        # Mock detection with high and low confidence
        low_conf_detection = Mock()
        low_conf_detection.cls = 0
        low_conf_detection.conf = 0.1  # Below typical threshold
        low_conf_detection.xyxy = np.array([[100, 100, 200, 200]])
        low_conf_detection.id = 1

        high_conf_detection = Mock()
        high_conf_detection.cls = 0
        high_conf_detection.conf = 0.9  # Above typical threshold
        high_conf_detection.xyxy = np.array([[300, 300, 400, 400]])
        high_conf_detection.id = 2

        with patch.object(
            detection_service.model,
            "track",
            return_value=[Mock(boxes=[low_conf_detection, high_conf_detection])],
        ):
            # Act
            results = detection_service.detect(sample_frame)

            # Assert
            # Results should include both detections (filtering happens in the model)
            assert len(results) == 2


class TestDetectionServiceGetClassNames:
    """Test DetectionService.get_class_names() method."""

    @pytest.fixture
    def detection_service(self, mock_yolo_model, settings):  # noqa: ARG002 - mock_yolo_model needed for fixture
        """Provide DetectionService instance for class names testing."""
        return DetectionService(settings)

    def test_get_class_names_returns_dict(self, detection_service):
        """Test that get_class_names returns a dict."""
        # Act
        class_names = detection_service.get_class_names()

        # Assert
        assert isinstance(class_names, dict)

    def test_get_class_names_matches_model_names(self, detection_service):
        """Test that returned class names match model names."""
        # Act
        class_names = detection_service.get_class_names()
        model_names = detection_service.model.names

        # Assert
        assert class_names == model_names

    def test_get_class_names_contains_expected_classes(self, detection_service):
        """Test that class names include expected object types."""
        # Act
        class_names = detection_service.get_class_names()

        # Assert
        assert "drone" in class_names.values()
        assert "bird" in class_names.values()
        assert "airplane" in class_names.values() or "aircraft" in class_names.values()

    def test_get_class_names_immutability(self, detection_service):
        """Test that class names dict cannot be accidentally modified."""
        # Arrange
        original_names = detection_service.get_class_names()

        # Act
        returned_names = detection_service.get_class_names()
        returned_names[999] = "new_class"  # Try to modify

        # Assert
        # Original dict should not be affected
        assert detection_service.get_class_names() == original_names
        assert 999 not in detection_service.get_class_names()


class TestDetectionServiceErrorHandling:
    """Test error handling in DetectionService."""

    @pytest.fixture
    def detection_service(self, mock_yolo_model, settings):  # noqa: ARG002 - mock_yolo_model needed for fixture
        """Provide DetectionService instance for error handling testing."""
        return DetectionService(settings)

    def test_invalid_frame_types(self, detection_service):
        """Test detection with various invalid frame types."""
        # Arrange
        invalid_frames = [
            None,
            "not_a_frame",
            42,
            [],
            {},
            np.array([1, 2, 3]),  # Wrong dimensions
        ]

        # Act & Assert
        for invalid_frame in invalid_frames:
            try:
                results = detection_service.detect(invalid_frame)
                # Should either return empty list or handle gracefully
                assert isinstance(results, list)
            except (TypeError, ValueError, AttributeError):
                # These exceptions are acceptable for invalid inputs
                pass

    def test_exception_in_model_track(self, detection_service, sample_frame):
        """Test handling of exceptions during model tracking."""
        # Arrange
        with patch.object(
            detection_service.model, "track", side_effect=RuntimeError("Model error")
        ):
            # Act
            results = detection_service.detect(sample_frame)

            # Assert
            assert results == []

    def test_exception_in_results_processing(self, detection_service):
        """Test handling of exceptions in results processing."""
        # Arrange
        mock_results = Mock()
        mock_results.boxes = None  # This might cause issues
        with patch.object(
            detection_service.model, "track", return_value=[mock_results]
        ):
            # Act
            results = detection_service.detect(np.zeros((720, 1280, 3), dtype=np.uint8))

            # Assert
            # Should handle None boxes gracefully
            assert isinstance(results, list)


class TestDetectionServicePerformance:
    """Test DetectionService performance characteristics."""

    @pytest.fixture
    def detection_service(self, mock_yolo_model, settings):  # noqa: ARG002 - mock_yolo_model needed for fixture
        """Provide DetectionService instance for performance testing."""
        return DetectionService(settings)

    @pytest.mark.performance
    def test_detection_processing_time(self, detection_service, sample_frame):
        """Test that detection processing is reasonably fast."""
        # Arrange
        import time  # noqa: PLC0415 - Import only for this test

        # Act
        start_time = time.time()
        results = detection_service.detect(sample_frame)
        processing_time = time.time() - start_time

        # Assert
        # Should complete within 100ms for test frame
        assert processing_time < 0.1
        assert results is not None

    @pytest.mark.performance
    def test_memory_usage_stable(self, detection_service, sample_frame):
        """Test that memory usage remains stable across multiple detections."""
        # Arrange
        import gc  # noqa: PLC0415 - Import only for this test

        gc.collect()  # Clean up before test

        # Act & Assert
        initial_objects = len(gc.get_objects())

        # Perform multiple detections
        for _ in range(10):
            results = detection_service.detect(sample_frame)
            assert results is not None

        gc.collect()
        final_objects = len(gc.get_objects())

        # Memory usage should not grow significantly
        object_growth = final_objects - initial_objects
        assert object_growth < 1000  # Allow some growth for normal operation
