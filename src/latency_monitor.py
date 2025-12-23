"""
Latency monitoring utilities for the control loop.

Keeps a sliding window of recent durations and computes percentiles for
observability.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass
class LatencySnapshot:
    count: int
    p50_ms: float
    p95_ms: float
    p99_ms: float
    max_ms: float


class LatencyMonitor:
    """Tracks loop latency and exposes percentile metrics."""

    def __init__(self, window_size: int = 512) -> None:
        self.window_size = window_size
        self._samples = deque(maxlen=window_size)

    def record(self, duration_s: float) -> None:
        """Record a new latency sample in seconds."""
        self._samples.append(max(0.0, float(duration_s)))

    def snapshot(self) -> LatencySnapshot:
        """Return percentile snapshot (ms)."""
        samples = np.array(self._samples, dtype=float)
        if samples.size == 0:
            return LatencySnapshot(0, 0.0, 0.0, 0.0, 0.0)

        percentiles = np.percentile(samples, [50, 95, 99]) * 1000.0
        return LatencySnapshot(
            count=int(samples.size),
            p50_ms=float(percentiles[0]),
            p95_ms=float(percentiles[1]),
            p99_ms=float(percentiles[2]),
            max_ms=float(samples.max() * 1000.0),
        )

    def extend(self, durations_s: Iterable[float]) -> None:
        """Bulk insert multiple duration samples (seconds)."""
        for value in durations_s:
            self.record(value)
