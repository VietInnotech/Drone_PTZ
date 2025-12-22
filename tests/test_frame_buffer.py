"""
Tests for non-blocking frame buffer.
"""

import numpy as np
import pytest

from src.frame_buffer import FrameBuffer


def test_frame_buffer_put_get():
    """Test basic put and get operations."""
    buffer = FrameBuffer(max_size=2)

    # Create test frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Initially empty
    assert buffer.get_nowait() is None

    # Add frame
    buffer.put(frame)

    # Should have frame now
    retrieved = buffer.get_nowait()
    assert retrieved is not None
    assert retrieved.shape == (480, 640, 3)


def test_frame_buffer_returns_copy():
    """Verify that get_nowait returns a copy."""
    buffer = FrameBuffer()

    frame = np.ones((480, 640, 3), dtype=np.uint8)
    buffer.put(frame)

    retrieved = buffer.get_nowait()
    assert retrieved is not None

    # Modify retrieved frame
    retrieved[0, 0] = [255, 255, 255]

    # Get another copy - should not be affected
    retrieved2 = buffer.get_nowait()
    assert retrieved2 is not None
    assert retrieved2[0, 0, 0] != 255


def test_frame_buffer_non_blocking():
    """Verify get_nowait never blocks."""
    buffer = FrameBuffer()

    # Getting from empty buffer should not block
    import time

    start = time.time()
    result = buffer.get_nowait()
    elapsed = time.time() - start

    assert result is None
    assert elapsed < 0.01, "Should be instant (< 10ms)"


def test_frame_buffer_circular():
    """Test circular buffer behavior (oldest replaced when full)."""
    buffer = FrameBuffer(max_size=2)

    # Add 3 frames to buffer with max size 2
    frame1 = np.ones((480, 640, 3), dtype=np.uint8) * 1
    frame2 = np.ones((480, 640, 3), dtype=np.uint8) * 2
    frame3 = np.ones((480, 640, 3), dtype=np.uint8) * 3

    buffer.put(frame1)
    buffer.put(frame2)

    # Should have dropped first frame
    stats = buffer.get_stats()
    assert stats.frames_dropped == 0  # Not dropped yet, buffer not full
    assert stats.frames_captured == 2

    # Add third frame
    buffer.put(frame3)

    # Now first frame should be dropped
    stats = buffer.get_stats()
    assert stats.frames_dropped == 1  # First frame replaced

    # Latest frame should be frame3
    latest = buffer.get_nowait()
    assert latest is not None
    assert np.all(latest == 3)


def test_frame_buffer_statistics():
    """Test statistics tracking."""
    buffer = FrameBuffer(max_size=1)

    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Add 5 frames
    for i in range(5):
        buffer.put(frame)

    # Get stats
    stats = buffer.get_stats()

    assert stats.frames_captured == 5
    assert stats.frames_dropped == 4  # 4 frames replaced
    # Drop rate = dropped / (dropped + processed) = 4 / (4 + 1) ≈ 44.44%
    assert abs(stats.drop_rate() - 44.44) < 1.0


def test_frame_buffer_size():
    """Test size tracking."""
    buffer = FrameBuffer(max_size=3)

    assert buffer.size() == 0

    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    buffer.put(frame)
    assert buffer.size() == 1

    buffer.put(frame)
    assert buffer.size() == 2

    buffer.put(frame)
    assert buffer.size() == 3


def test_frame_buffer_is_empty():
    """Test is_empty check."""
    buffer = FrameBuffer()

    assert buffer.is_empty()

    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    buffer.put(frame)

    assert not buffer.is_empty()


def test_frame_buffer_reset_stats():
    """Test statistics reset."""
    buffer = FrameBuffer(max_size=1)

    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # Generate some stats
    for _ in range(10):
        buffer.put(frame)
        buffer.get_nowait()

    # Verify stats are non-zero
    stats = buffer.get_stats()
    assert stats.frames_captured > 0

    # Reset
    buffer.reset_stats()

    # Verify reset
    stats = buffer.get_stats()
    assert stats.frames_captured == 0
    assert stats.frames_dropped == 0
    assert stats.frames_processed == 0


def test_frame_buffer_concurrent_access():
    """Test concurrent put/get operations."""
    import threading

    buffer = FrameBuffer(max_size=10)
    errors = []

    def writer():
        try:
            for i in range(100):
                frame = np.ones((480, 640, 3), dtype=np.uint8) * (i % 256)
                buffer.put(frame)
        except Exception as e:
            errors.append(e)

    def reader():
        try:
            for _ in range(50):
                frame = buffer.get_nowait()
                if frame is not None:
                    # Verify frame integrity
                    assert frame.shape == (480, 640, 3)
        except Exception as e:
            errors.append(e)

    # Start threads
    threads = []
    threads.append(threading.Thread(target=writer))
    for _ in range(3):
        threads.append(threading.Thread(target=reader))

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # Verify no errors
    assert len(errors) == 0, f"Errors occurred: {errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
