"""
Test suite for tracking selector utilities.

Tests cover ID parsing, target selection, and available ID listing.
"""

from unittest.mock import Mock

from src.tracking.selector import (
    get_available_ids,
    parse_track_id,
    select_by_id,
)


class TestParseTrackId:
    """Test parse_track_id utility function."""

    def test_parse_integer_id(self):
        """Test parsing integer track ID."""
        det = Mock()
        det.id = 42

        result = parse_track_id(det)

        assert result == 42

    def test_parse_tensor_id(self):
        """Test parsing PyTorch tensor track ID."""
        det = Mock()
        tensor_mock = Mock()
        tensor_mock.item.return_value = 99
        det.id = tensor_mock

        result = parse_track_id(det)

        assert result == 99

    def test_parse_none_id(self):
        """Test parsing None track ID."""
        det = Mock()
        det.id = None

        result = parse_track_id(det)

        assert result is None

    def test_parse_none_detection(self):
        """Test parsing None detection."""
        result = parse_track_id(None)

        assert result is None

    def test_parse_missing_id_attribute(self):
        """Test detection without id attribute."""
        det = Mock(spec=[])  # No 'id' attribute

        result = parse_track_id(det)

        assert result is None

    def test_parse_invalid_id_type(self):
        """Test parsing invalid ID type."""
        det = Mock()
        det.id = "invalid_string"

        result = parse_track_id(det)

        # Should raise ValueError caught and return None
        assert result is None

    def test_parse_zero_id(self):
        """Test parsing ID of zero."""
        det = Mock()
        det.id = 0

        result = parse_track_id(det)

        assert result == 0

    def test_parse_negative_id(self):
        """Test parsing negative ID."""
        det = Mock()
        det.id = -1

        result = parse_track_id(det)

        assert result == -1

    def test_parse_large_id(self):
        """Test parsing very large ID."""
        det = Mock()
        det.id = 999999999

        result = parse_track_id(det)

        assert result == 999999999


class TestSelectById:
    """Test select_by_id target selection function."""

    def test_select_existing_id(self):
        """Test selecting detection with matching ID."""
        det1 = Mock()
        det1.id = 1
        det2 = Mock()
        det2.id = 42
        det3 = Mock()
        det3.id = 3

        result = select_by_id([det1, det2, det3], 42)

        assert result is det2

    def test_select_missing_id_returns_none(self):
        """Test selecting non-existent ID returns None."""
        det1 = Mock()
        det1.id = 1
        det2 = Mock()
        det2.id = 2

        result = select_by_id([det1, det2], 99)

        assert result is None

    def test_select_with_none_target_id(self):
        """Test selecting with target_id=None returns None."""
        det1 = Mock()
        det1.id = 1

        result = select_by_id([det1], None)

        assert result is None

    def test_select_from_empty_boxes(self):
        """Test selecting from empty boxes list."""
        result = select_by_id([], 42)

        assert result is None

    def test_select_first_matching_id(self):
        """Test selecting returns first match when duplicates exist."""
        det1 = Mock()
        det1.id = 42
        det1.conf = 0.8
        det2 = Mock()
        det2.id = 42
        det2.conf = 0.9

        result = select_by_id([det1, det2], 42)

        # Should return the first match
        assert result is det1

    def test_select_with_tensor_id(self):
        """Test selection with tensor IDs."""
        det1 = Mock()
        tensor_mock = Mock()
        tensor_mock.item.return_value = 42
        det1.id = tensor_mock

        result = select_by_id([det1], 42)

        assert result is det1

    def test_select_with_none_boxes(self):
        """Test selection with None in boxes list (gracefully skip)."""
        det1 = Mock()
        det1.id = 1
        det2 = Mock()
        det2.id = 42

        result = select_by_id([det1, det2], 42)

        assert result is det2

    def test_select_zero_id(self):
        """Test selecting ID of zero."""
        det = Mock()
        det.id = 0

        result = select_by_id([det], 0)

        assert result is det


class TestGetAvailableIds:
    """Test get_available_ids utility function."""

    def test_get_ids_from_detections(self):
        """Test getting all available IDs from detections."""
        det1 = Mock()
        det1.id = 1
        det2 = Mock()
        det2.id = 42
        det3 = Mock()
        det3.id = 3

        result = get_available_ids([det1, det2, det3])

        assert result == [1, 3, 42]  # Sorted

    def test_get_ids_empty_list(self):
        """Test getting IDs from empty list."""
        result = get_available_ids([])

        assert result == []

    def test_get_ids_duplicates_removed(self):
        """Test that duplicate IDs are removed."""
        det1 = Mock()
        det1.id = 1
        det2 = Mock()
        det2.id = 1
        det3 = Mock()
        det3.id = 1

        result = get_available_ids([det1, det2, det3])

        assert result == [1]

    def test_get_ids_sorted(self):
        """Test that returned IDs are sorted."""
        det1 = Mock()
        det1.id = 99
        det2 = Mock()
        det2.id = 1
        det3 = Mock()
        det3.id = 50

        result = get_available_ids([det1, det2, det3])

        assert result == [1, 50, 99]

    def test_get_ids_with_none_ids(self):
        """Test that None IDs are filtered out."""
        det1 = Mock()
        det1.id = 1
        det2 = Mock()
        det2.id = None
        det3 = Mock()
        det3.id = 3

        result = get_available_ids([det1, det2, det3])

        assert result == [1, 3]

    def test_get_ids_with_tensor_ids(self):
        """Test getting IDs from tensor-based detections."""
        det1 = Mock()
        tensor1 = Mock()
        tensor1.item.return_value = 1
        det1.id = tensor1

        det2 = Mock()
        tensor2 = Mock()
        tensor2.item.return_value = 42
        det2.id = tensor2

        result = get_available_ids([det1, det2])

        assert result == [1, 42]

    def test_get_ids_with_zero_id(self):
        """Test getting IDs when zero ID is present."""
        det1 = Mock()
        det1.id = 0
        det2 = Mock()
        det2.id = 1

        result = get_available_ids([det1, det2])

        assert result == [0, 1]

    def test_get_ids_large_dataset(self):
        """Test getting IDs from large detection set."""
        detections = []
        expected_ids = []
        for i in range(100, 110):
            det = Mock()
            det.id = i
            detections.append(det)
            expected_ids.append(i)

        result = get_available_ids(detections)

        assert result == expected_ids
