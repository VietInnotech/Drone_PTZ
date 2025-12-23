"""
PID servo controller for smooth PTZ motion.

Replaces simple proportional control with full PID for:
- P: Immediate response to error
- I: Eliminating steady-state error
- D: Damping overshoot
"""

import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class PIDGains:
    """PID tuning parameters."""

    kp: float = 2.0  # Proportional gain
    ki: float = 0.15  # Integral gain
    kd: float = 0.8  # Derivative gain

    # Anti-windup: limit integral accumulation
    integral_limit: float = 1.0

    # Dead band: ignore errors smaller than this
    dead_band: float = 0.01


class PTZServo:
    """PID servo controller for PTZ pan/tilt axes."""

    def __init__(self, gains: Optional[PIDGains] = None) -> None:
        """
        Initialize servo controller.

        Args:
            gains: PID tuning parameters. Defaults are well-tuned for typical
                   camera servo responses.
        """
        self.gains = gains or PIDGains()

        # State tracking
        self.last_error_x = 0.0
        self.last_error_y = 0.0
        self.integral_x = 0.0
        self.integral_y = 0.0
        self.last_time = time.time()

    def control(self, error_x: float, error_y: float) -> tuple[float, float]:
        """
        Calculate servo output for pan/tilt errors.

        Args:
            error_x: Horizontal error (frame center coords).
            error_y: Vertical error.

        Returns:
            Tuple of (pan_velocity, tilt_velocity) in range [-1.0, 1.0].
        """
        # Calculate time delta
        now = time.time()
        dt = now - self.last_time
        self.last_time = now

        # Avoid division by zero and limit dt to reasonable values
        if dt < 0.001:
            dt = 0.016  # Assume ~60 FPS
        dt = min(dt, 0.1)  # Cap at 100ms to prevent large jumps

        # Apply dead band (ignore tiny errors)
        if abs(error_x) < self.gains.dead_band:
            error_x = 0.0
        if abs(error_y) < self.gains.dead_band:
            error_y = 0.0

        # PAN (X axis) control
        pan_velocity, self.integral_x = self._pid_update(
            error_x, self.last_error_x, self.integral_x, dt, axis="pan"
        )
        self.last_error_x = error_x

        # TILT (Y axis) control
        tilt_velocity, self.integral_y = self._pid_update(
            error_y, self.last_error_y, self.integral_y, dt, axis="tilt"
        )
        self.last_error_y = error_y

        return (pan_velocity, tilt_velocity)

    def _pid_update(
        self,
        error: float,
        last_error: float,
        integral: float,
        dt: float,
        axis: str,
    ) -> tuple[float, float]:
        """
        Calculate PID output for a single axis.

        Args:
            error: Current error value.
            last_error: Previous error (for derivative).
            integral: Accumulated integral.
            dt: Time delta.
            axis: "pan" or "tilt" (for logging).

        Returns:
            Tuple of (control_output, updated_integral) where output is in
            range [-1.0, 1.0] and integral is the updated accumulated error.
        """
        # P term: Proportional to error
        p_term = self.gains.kp * error

        # I term: Accumulated error with anti-windup
        integral += error * dt
        integral = max(
            -self.gains.integral_limit, min(self.gains.integral_limit, integral)
        )
        i_term = self.gains.ki * integral

        # D term: Rate of error change (dampening)
        if dt > 0:
            d_term = self.gains.kd * (error - last_error) / dt
        else:
            d_term = 0.0

        # Sum and saturate output
        output = p_term + i_term + d_term
        output = max(-1.0, min(1.0, output))

        return output, integral

    def reset(self) -> None:
        """Reset servo state (e.g., when target is lost)."""
        self.last_error_x = 0.0
        self.last_error_y = 0.0
        self.integral_x = 0.0
        self.integral_y = 0.0
        self.last_time = time.time()


# Presets for different scenarios
GAINS_RESPONSIVE = PIDGains(kp=3.0, ki=0.2, kd=1.2)  # Fast, aggressive
GAINS_BALANCED = PIDGains(kp=2.0, ki=0.15, kd=0.8)  # Default, smooth
GAINS_SMOOTH = PIDGains(kp=1.2, ki=0.1, kd=0.5)  # Slow, very smooth
