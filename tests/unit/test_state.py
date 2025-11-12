"""
Test suite for tracking state machine.

Tests cover phase transitions, state management, and grace period handling.
"""

import time

from src.tracking.state import (
    TrackerStatus,
    TrackingPhase,
)


class TestTrackingPhaseEnum:
    """Test TrackingPhase enum values."""

    def test_all_phases_defined(self):
        """Test that all expected phases are defined."""
        assert hasattr(TrackingPhase, "IDLE")
        assert hasattr(TrackingPhase, "SEARCHING")
        assert hasattr(TrackingPhase, "TRACKING")
        assert hasattr(TrackingPhase, "LOST")

    def test_phase_values(self):
        """Test that phase enum values are correct."""
        assert TrackingPhase.IDLE.value == "idle"
        assert TrackingPhase.SEARCHING.value == "searching"
        assert TrackingPhase.TRACKING.value == "tracking"
        assert TrackingPhase.LOST.value == "lost"


class TestTrackerStatusInitialization:
    """Test TrackerStatus initialization and defaults."""

    def test_default_initialization(self):
        """Test default TrackerStatus initialization."""
        status = TrackerStatus()

        assert status.phase == TrackingPhase.IDLE
        assert status.target_id is None
        assert status.loss_grace_s == 2.0
        assert isinstance(status.last_seen_ts, float)

    def test_custom_initialization(self):
        """Test TrackerStatus initialization with custom values."""
        now = time.time()
        status = TrackerStatus(
            phase=TrackingPhase.TRACKING,
            target_id=42,
            last_seen_ts=now,
            loss_grace_s=5.0,
        )

        assert status.phase == TrackingPhase.TRACKING
        assert status.target_id == 42
        assert status.last_seen_ts == now
        assert status.loss_grace_s == 5.0


class TestTrackerStatusMarkSeen:
    """Test mark_seen() method."""

    def test_mark_seen_with_explicit_time(self):
        """Test mark_seen updates last_seen_ts."""
        status = TrackerStatus()
        original_ts = status.last_seen_ts

        # Wait a small amount and mark seen
        time.sleep(0.01)
        now = time.time()
        status.mark_seen(now)

        assert status.last_seen_ts == now
        assert status.last_seen_ts > original_ts

    def test_mark_seen_without_time_uses_current(self):
        """Test mark_seen uses current time if not provided."""
        status = TrackerStatus()
        before = time.time()
        status.mark_seen()
        after = time.time()

        assert before <= status.last_seen_ts <= after

    def test_mark_seen_multiple_times(self):
        """Test mark_seen can be called multiple times."""
        status = TrackerStatus()
        timestamps = []

        for _ in range(3):
            time.sleep(0.01)
            ts = time.time()
            status.mark_seen(ts)
            timestamps.append(ts)

        # Each call should update to the most recent time
        assert status.last_seen_ts == timestamps[-1]


class TestTrackerStatusSetTarget:
    """Test set_target() method."""

    def test_set_target_with_id(self):
        """Test setting a target ID."""
        status = TrackerStatus()
        now = time.time()

        status.set_target(42, now)

        assert status.target_id == 42
        assert status.last_seen_ts == now

    def test_set_target_none_transitions_to_idle(self):
        """Test setting target to None transitions to IDLE."""
        status = TrackerStatus(
            phase=TrackingPhase.TRACKING,
            target_id=42,
        )

        status.set_target(None)

        assert status.target_id is None
        assert status.phase == TrackingPhase.IDLE

    def test_set_target_without_time_uses_current(self):
        """Test set_target uses current time if not provided."""
        status = TrackerStatus()
        before = time.time()
        status.set_target(99)
        after = time.time()

        assert status.target_id == 99
        assert before <= status.last_seen_ts <= after

    def test_set_target_overwrites_previous(self):
        """Test setting a new target ID overwrites previous."""
        status = TrackerStatus(target_id=42)
        now = time.time()

        status.set_target(99, now)

        assert status.target_id == 99
        assert status.last_seen_ts == now


class TestTrackerStatusClearTarget:
    """Test clear_target() method."""

    def test_clear_target_resets_to_idle(self):
        """Test clear_target resets state to IDLE."""
        status = TrackerStatus(
            phase=TrackingPhase.TRACKING,
            target_id=42,
        )

        status.clear_target()

        assert status.target_id is None
        assert status.phase == TrackingPhase.IDLE

    def test_clear_target_from_searching(self):
        """Test clear_target from SEARCHING phase."""
        status = TrackerStatus(
            phase=TrackingPhase.SEARCHING,
            target_id=42,
        )

        status.clear_target()

        assert status.target_id is None
        assert status.phase == TrackingPhase.IDLE

    def test_clear_target_idempotent(self):
        """Test clear_target can be called multiple times safely."""
        status = TrackerStatus(target_id=42, phase=TrackingPhase.TRACKING)

        status.clear_target()
        first_state = (status.target_id, status.phase)

        status.clear_target()
        second_state = (status.target_id, status.phase)

        assert first_state == second_state


class TestTrackerStatusComputePhase:
    """Test compute_phase() phase transition logic."""

    def test_no_target_stays_idle(self):
        """Test that with no target_id, phase stays IDLE."""
        status = TrackerStatus(target_id=None)

        phase = status.compute_phase(found=True)

        assert phase == TrackingPhase.IDLE

    def test_target_found_transitions_to_tracking(self):
        """Test that finding a target transitions to TRACKING."""
        now = time.time()
        status = TrackerStatus(target_id=42, phase=TrackingPhase.SEARCHING)

        phase = status.compute_phase(found=True, now=now)

        assert phase == TrackingPhase.TRACKING
        assert status.last_seen_ts == now

    def test_target_missing_within_grace_period_searches(self):
        """Test that missing target within grace period searches."""
        now = time.time()
        status = TrackerStatus(
            target_id=42,
            last_seen_ts=now - 0.5,  # Seen 0.5s ago
            loss_grace_s=2.0,
        )

        phase = status.compute_phase(found=False, now=now)

        assert phase == TrackingPhase.SEARCHING

    def test_target_missing_beyond_grace_period_lost(self):
        """Test that missing target beyond grace period is LOST."""
        now = time.time()
        status = TrackerStatus(
            target_id=42,
            last_seen_ts=now - 3.0,  # Seen 3s ago
            loss_grace_s=2.0,
        )

        phase = status.compute_phase(found=False, now=now)

        assert phase == TrackingPhase.LOST

    def test_lost_to_tracking_reacquire(self):
        """Test transitioning from LOST back to TRACKING on reacquisition."""
        now = time.time()
        status = TrackerStatus(
            target_id=42,
            phase=TrackingPhase.LOST,
            last_seen_ts=now - 5.0,
        )

        phase = status.compute_phase(found=True, now=now)

        assert phase == TrackingPhase.TRACKING
        assert status.last_seen_ts == now

    def test_full_state_machine_cycle(self):
        """Test a complete cycle: IDLE → TRACKING → SEARCHING → LOST → TRACKING."""
        base_time = time.time()
        status = TrackerStatus(loss_grace_s=1.0)

        status.set_target(42, base_time)

        # IDLE → TRACKING (target found immediately)
        phase = status.compute_phase(found=True, now=base_time)
        assert phase == TrackingPhase.TRACKING

        # TRACKING → SEARCHING (0.5s missing, within grace period)
        phase = status.compute_phase(found=False, now=base_time + 0.5)
        assert phase == TrackingPhase.SEARCHING

        # SEARCHING → LOST (1.5s missing, beyond grace period)
        phase = status.compute_phase(found=False, now=base_time + 1.5)
        assert phase == TrackingPhase.LOST

        # LOST → TRACKING (target reacquired)
        phase = status.compute_phase(found=True, now=base_time + 2.0)
        assert phase == TrackingPhase.TRACKING


class TestTrackerStatusEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_grace_period_exact_boundary(self):
        """Test behavior at grace period boundary."""
        base_time = time.time()
        status = TrackerStatus(
            target_id=42,
            last_seen_ts=base_time - 2.0,
            loss_grace_s=2.0,
        )

        # Slightly before boundary: should be SEARCHING
        phase = status.compute_phase(found=False, now=base_time - 0.001)
        assert phase == TrackingPhase.SEARCHING

        # Slightly past boundary: should be LOST
        phase = status.compute_phase(found=False, now=base_time + 0.001)
        assert phase == TrackingPhase.LOST

    def test_zero_grace_period(self):
        """Test with grace period set to zero."""
        base_time = time.time()
        status = TrackerStatus(
            target_id=42,
            last_seen_ts=base_time,
            loss_grace_s=0.0,
        )

        # Any time in future should be LOST
        phase = status.compute_phase(found=False, now=base_time + 0.001)
        assert phase == TrackingPhase.LOST

    def test_very_large_grace_period(self):
        """Test with very large grace period."""
        base_time = time.time()
        status = TrackerStatus(
            target_id=42,
            last_seen_ts=base_time,
            loss_grace_s=1000.0,
        )

        # Even 100s later should still be SEARCHING
        phase = status.compute_phase(found=False, now=base_time + 100.0)
        assert phase == TrackingPhase.SEARCHING

    def test_compute_phase_without_explicit_time_uses_current(self):
        """Test compute_phase uses current time if not provided."""
        status = TrackerStatus(
            target_id=42,
            last_seen_ts=time.time() - 0.5,
            loss_grace_s=2.0,
        )

        phase = status.compute_phase(found=False)
        # Should be SEARCHING since not enough time has passed
        assert phase == TrackingPhase.SEARCHING


class TestTrackerStatusMarkMissing:
    """Test mark_missing() method."""

    def test_mark_missing_no_op(self):
        """Test that mark_missing does not change state."""
        now = time.time()
        status = TrackerStatus(
            target_id=42,
            last_seen_ts=now,
            phase=TrackingPhase.TRACKING,
        )

        status.mark_missing()

        # State should remain unchanged
        assert status.target_id == 42
        assert status.last_seen_ts == now
        assert status.phase == TrackingPhase.TRACKING
