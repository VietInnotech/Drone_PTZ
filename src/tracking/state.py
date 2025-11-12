"""
Tracking state machine for ID-based target selection.

Manages tracking phases (IDLE, SEARCHING, TRACKING, LOST) and phase transitions.
"""

from dataclasses import dataclass, field
from enum import Enum
from time import time


class TrackingPhase(Enum):
    """Tracking phases for the state machine."""

    IDLE = "idle"
    SEARCHING = "searching"
    TRACKING = "tracking"
    LOST = "lost"


@dataclass
class TrackerStatus:
    """
    Tracking status and state machine.

    Attributes:
        phase: Current tracking phase.
        target_id: Currently locked target ID (None if idle).
        last_seen_ts: Timestamp when target was last seen.
        loss_grace_s: Grace period (seconds) before transitioning to LOST.
    """

    phase: TrackingPhase = TrackingPhase.IDLE
    target_id: int | None = None
    last_seen_ts: float = field(default_factory=time)
    loss_grace_s: float = 2.0

    def mark_seen(self, now: float | None = None) -> None:
        """Mark target as seen at the given timestamp."""
        if now is None:
            now = time()
        self.last_seen_ts = now

    def mark_missing(self) -> None:
        """Mark target as missing (no update to last_seen_ts)."""
        # No-op: we rely on time delta to detect missing targets

    def set_target(self, target_id: int | None, now: float | None = None) -> None:
        """Set a new target ID and initialize tracking."""
        if now is None:
            now = time()
        self.target_id = target_id
        if target_id is not None:
            self.last_seen_ts = now
        else:
            self.phase = TrackingPhase.IDLE

    def clear_target(self) -> None:
        """Clear the current target and return to IDLE."""
        self.target_id = None
        self.phase = TrackingPhase.IDLE

    def compute_phase(self, found: bool, now: float | None = None) -> TrackingPhase:
        """
        Compute the next phase based on current state and detection.

        Args:
            found: True if target_id is found in this frame's detections.
            now: Current timestamp. If None, uses current time.

        Returns:
            The computed phase.
        """
        if now is None:
            now = time()

        # If no target is locked, stay IDLE
        if self.target_id is None:
            self.phase = TrackingPhase.IDLE
            return self.phase

        # If target is found, we are TRACKING
        if found:
            self.last_seen_ts = now
            self.phase = TrackingPhase.TRACKING
            return self.phase

        # Target not found; check grace period
        time_missing = now - self.last_seen_ts
        if time_missing < self.loss_grace_s:
            self.phase = TrackingPhase.SEARCHING
        else:
            self.phase = TrackingPhase.LOST

        return self.phase
