"""Tests for LatencyMonitor utility."""

from src.latency_monitor import LatencyMonitor


def test_latency_snapshot_empty():
    monitor = LatencyMonitor()
    snap = monitor.snapshot()

    assert snap.count == 0
    assert snap.p50_ms == 0.0
    assert snap.p95_ms == 0.0
    assert snap.p99_ms == 0.0
    assert snap.max_ms == 0.0


def test_latency_snapshot_percentiles():
    monitor = LatencyMonitor(window_size=10)
    monitor.extend([0.001, 0.002, 0.003, 0.004, 0.005])  # seconds

    snap = monitor.snapshot()

    assert snap.count == 5
    # Percentiles in ms
    assert 2.0 <= snap.p50_ms <= 3.5
    assert snap.p95_ms >= snap.p50_ms
    assert snap.max_ms == 5.0


def test_latency_window_sliding():
    monitor = LatencyMonitor(window_size=3)
    monitor.extend([0.001, 0.002, 0.003])
    snap1 = monitor.snapshot()

    monitor.record(0.010)  # pushes out oldest
    snap2 = monitor.snapshot()

    assert snap1.count == 3
    assert snap2.count == 3
    assert snap2.max_ms == 10.0
