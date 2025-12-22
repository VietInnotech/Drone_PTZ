"""
Tests for PID servo controller.
"""

import time

import pytest

from src.ptz_servo import GAINS_BALANCED, GAINS_RESPONSIVE, GAINS_SMOOTH, PTZServo


def test_servo_initialization():
    """Test servo initialization with default gains."""
    servo = PTZServo()

    assert servo.gains is not None
    assert servo.last_error_x == 0.0
    assert servo.last_error_y == 0.0
    assert servo.integral_x == 0.0
    assert servo.integral_y == 0.0


def test_servo_custom_gains():
    """Test servo with custom gains."""
    servo = PTZServo(GAINS_RESPONSIVE)

    assert servo.gains.kp == 3.0
    assert servo.gains.ki == 0.2
    assert servo.gains.kd == 1.2


def test_servo_step_response():
    """Test PID response to step input (suddenly large error)."""
    servo = PTZServo(GAINS_BALANCED)

    # Large step input
    error_x = 0.5  # 50% error
    outputs = []

    # Collect outputs over multiple iterations
    for _ in range(10):
        x_speed, _ = servo.control(error_x, 0)
        outputs.append(x_speed)

    # Verify outputs are bounded
    assert all(-1.0 <= o <= 1.0 for o in outputs)

    # Verify outputs change smoothly (not step)
    diffs = [abs(outputs[i + 1] - outputs[i]) for i in range(len(outputs) - 1)]
    assert all(d < 0.3 for d in diffs), "Output should change smoothly"

    # Verify initial response is immediate
    assert outputs[0] > 0.1, "Should respond immediately"


def test_servo_zero_error():
    """Test servo output with zero error."""
    servo = PTZServo()

    x_speed, y_speed = servo.control(0, 0)

    assert x_speed == 0.0
    assert y_speed == 0.0


def test_servo_dead_band():
    """Test dead band prevents micro-movements."""
    servo = PTZServo(GAINS_BALANCED)

    # Error smaller than dead band
    small_error = 0.005  # Smaller than default dead_band of 0.01

    x_speed, _ = servo.control(small_error, 0)

    # Should be zero (dead band applied)
    assert x_speed == 0.0


def test_servo_integral_windup_protection():
    """Test anti-windup protection on integral term."""
    servo = PTZServo(GAINS_BALANCED)

    # Constant error over many iterations
    error = 0.3
    for _ in range(100):
        servo.control(error, 0)

    # Integral should be bounded
    assert servo.integral_x <= servo.gains.integral_limit
    assert servo.integral_x >= -servo.gains.integral_limit


def test_servo_reset():
    """Test servo reset functionality."""
    servo = PTZServo(GAINS_BALANCED)

    # Run servo to accumulate state with large error
    for _ in range(10):
        servo.control(5.0, 3.0)  # Larger error to accumulate integral

    # Verify state is accumulated
    assert servo.integral_x != 0.0 or servo.integral_y != 0.0

    # Reset
    servo.reset()

    # Verify state is cleared
    assert servo.last_error_x == 0.0
    assert servo.last_error_y == 0.0
    assert servo.integral_x == 0.0
    assert servo.integral_y == 0.0


def test_servo_saturation():
    """Test output is saturated to [-1, 1] range."""
    servo = PTZServo(GAINS_RESPONSIVE)  # High gains

    # Very large error
    x_speed, y_speed = servo.control(2.0, 2.0)

    # Verify saturation
    assert -1.0 <= x_speed <= 1.0
    assert -1.0 <= y_speed <= 1.0


def test_servo_different_gains():
    """Test servo behavior with different gain presets."""
    error_x = 0.2
    error_y = 0.1

    # Test all presets
    for gains in [GAINS_SMOOTH, GAINS_BALANCED, GAINS_RESPONSIVE]:
        servo = PTZServo(gains)
        x_speed, y_speed = servo.control(error_x, error_y)

        # Verify all are valid outputs
        assert -1.0 <= x_speed <= 1.0
        assert -1.0 <= y_speed <= 1.0

        # Reset for next iteration
        servo.reset()


def test_servo_steady_state():
    """Test servo behavior at steady state."""
    servo = PTZServo(GAINS_BALANCED)

    # Small constant error
    error = 0.05

    outputs = []
    for _ in range(50):
        x_speed, _ = servo.control(error, 0)
        outputs.append(x_speed)

    # After steady state, output should be relatively stable
    final_outputs = outputs[-10:]
    variance = max(final_outputs) - min(final_outputs)

    # Variance should be small at steady state
    assert variance < 0.1, "Output should stabilize at steady state"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
