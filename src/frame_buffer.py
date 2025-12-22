"""
Non-blocking frame buffer with statistics tracking.

Replaces blocking queue.Queue with circular buffer that:
- Never blocks the main control loop
- Tracks frame drops and queue fullness
- Provides statistics for diagnostics
"""

import threading
from collections import deque
from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class FrameStats:
    """Statistics for frame buffer performance."""

    frames_captured: int = 0
    frames_dropped: int = 0
    frames_processed: int = 0
    avg_queue_size: float = 0.0

    def drop_rate(self) -> float:
        """Calculate frame drop rate (%)."""
        total = self.frames_captured + self.frames_dropped
        if total == 0:
            return 0.0
        return 100.0 * self.frames_dropped / total


class FrameBuffer:
    """Non-blocking circular frame buffer for video capture."""

    def __init__(self, max_size: int = 2) -> None:
        """
        Initialize frame buffer.

        Args:
            max_size: Maximum frames to buffer (default 2 = latest + previous).
        """
        self.max_size = max_size
        self._frames: deque = deque(maxlen=max_size)
        self._lock = threading.RLock()
        self._has_frame_event = threading.Event()

        # Statistics
        self._stats = FrameStats()
        self._queue_sizes = deque(maxlen=1000)  # Track for averaging

    def put(self, frame: np.ndarray) -> None:
        """
        Add a frame to the buffer (non-blocking).

        If buffer is full, replaces oldest frame.

        Args:
            frame: Frame to add.
        """
        with self._lock:
            # Check if buffer was full (would drop)
            if len(self._frames) == self.max_size:
                self._stats.frames_dropped += 1

            self._frames.append(frame)
            self._stats.frames_captured += 1
            self._queue_sizes.append(len(self._frames))
            self._has_frame_event.set()

    def get_nowait(self) -> Optional[np.ndarray]:
        """
        Get latest frame without blocking.

        Returns:
            Latest frame, or None if buffer is empty.
        """
        with self._lock:
            if not self._frames:
                return None
            frame = self._frames[-1]
            self._stats.frames_processed += 1
            return frame.copy()  # Return copy to prevent external mutation

    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        with self._lock:
            return len(self._frames) == 0

    def size(self) -> int:
        """Get current number of frames in buffer."""
        with self._lock:
            return len(self._frames)

    def get_stats(self) -> FrameStats:
        """Get current statistics."""
        with self._lock:
            stats = FrameStats(
                frames_captured=self._stats.frames_captured,
                frames_dropped=self._stats.frames_dropped,
                frames_processed=self._stats.frames_processed,
                avg_queue_size=(
                    float(np.mean(list(self._queue_sizes)))
                    if self._queue_sizes
                    else 0.0
                ),
            )
            return stats

    def reset_stats(self) -> None:
        """Reset statistics counters."""
        with self._lock:
            self._stats = FrameStats()
            self._queue_sizes.clear()
