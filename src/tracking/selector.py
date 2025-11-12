"""
Target selection utilities for ID-based tracking.

Provides functions for parsing track IDs and selecting targets by ID.
"""

from typing import Any


def parse_track_id(det: Any) -> int | None:
    """
    Parse tracking ID from a detection object.

    Handles:
    - PyTorch tensors (converts via .item())
    - Integer values
    - None values
    - Objects with .id attribute

    Args:
        det: Detection object from YOLO (has .id attribute).

    Returns:
        Integer track ID or None if not found.
    """
    if det is None:
        return None

    try:
        track_id = getattr(det, "id", None)
        if track_id is None:
            return None

        # Handle torch tensor
        if hasattr(track_id, "item"):
            return int(track_id.item())

        # Handle integer
        return int(track_id)
    except (ValueError, TypeError, AttributeError):
        return None


def select_by_id(tracked_boxes: list[Any], target_id: int | None) -> Any | None:
    """
    Select a detection matching the target ID.

    Args:
        tracked_boxes: List of detection boxes from YOLO.
        target_id: ID to match, or None.

    Returns:
        Detection box if found, None otherwise. Label-based filtering is NOT applied.
    """
    if target_id is None or not tracked_boxes:
        return None

    for det in tracked_boxes:
        det_id = parse_track_id(det)
        if det_id == target_id:
            return det

    return None


def get_available_ids(tracked_boxes: list[Any]) -> list[int]:
    """
    Get a sorted list of all available tracking IDs in current detections.

    Args:
        tracked_boxes: List of detection boxes from YOLO.

    Returns:
        Sorted list of unique tracking IDs.
    """
    ids = set()
    for det in tracked_boxes:
        track_id = parse_track_id(det)
        if track_id is not None:
            ids.add(track_id)

    return sorted(ids)
