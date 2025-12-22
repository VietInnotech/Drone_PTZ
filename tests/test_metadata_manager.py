"""
Tests for metadata manager thread-safe access.
"""

import threading
import time

import pytest

from src.metadata_manager import MetadataManager


def test_metadata_manager_basic():
    """Test basic metadata storage and retrieval."""
    mgr = MetadataManager()

    # Initially empty
    assert mgr.get() is None

    # Store metadata
    metadata = {"frame": 1, "detection_count": 5}
    mgr.update(metadata)

    # Retrieve and verify
    retrieved = mgr.get()
    assert retrieved is not None
    assert retrieved["frame"] == 1
    assert retrieved["detection_count"] == 5


def test_metadata_manager_returns_copy():
    """Verify that get() returns a copy, not reference."""
    mgr = MetadataManager()
    metadata = {"frame": 1, "value": 100}
    mgr.update(metadata)

    # Get first copy
    copy1 = mgr.get()
    assert copy1 is not None

    # Modify the copy
    copy1["value"] = 999

    # Get second copy - should not be affected
    copy2 = mgr.get()
    assert copy2 is not None
    assert copy2["value"] == 100


def test_metadata_manager_concurrent_access():
    """Test thread-safe concurrent access."""
    mgr = MetadataManager()
    results = []
    errors = []

    def writer():
        """Writer thread."""
        try:
            for i in range(100):
                metadata = {"frame": i, "data": list(range(10))}
                mgr.update(metadata)
                time.sleep(0.001)
        except Exception as e:
            errors.append(e)

    def reader():
        """Reader thread."""
        try:
            for _ in range(100):
                data = mgr.get()
                if data:
                    results.append(data["frame"])
                time.sleep(0.001)
        except Exception as e:
            errors.append(e)

    # Start multiple readers and writers
    threads = []
    threads.append(threading.Thread(target=writer))
    for _ in range(3):
        threads.append(threading.Thread(target=reader))

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # Verify no errors occurred
    assert len(errors) == 0, f"Errors occurred: {errors}"
    assert len(results) > 0, "Should have processed some data"


def test_metadata_manager_get_value():
    """Test get_value for single key access."""
    mgr = MetadataManager()

    # Empty manager returns default
    assert mgr.get_value("missing", "default") == "default"

    # Store and retrieve
    mgr.update({"coverage": 0.45, "detections": 10})
    assert mgr.get_value("coverage") == 0.45
    assert mgr.get_value("detections") == 10
    assert mgr.get_value("missing", 999) == 999


def test_metadata_manager_none_update():
    """Test handling of None updates."""
    mgr = MetadataManager()

    # Store data
    mgr.update({"frame": 1})
    assert mgr.get() is not None

    # Update to None
    mgr.update(None)
    assert mgr.get() is None

    # get_value should return default
    assert mgr.get_value("anything", "default") == "default"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
