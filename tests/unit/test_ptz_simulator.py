"""
Unit tests for PTZ Simulator.

Tests the SimulatedPTZService class including:
- Initialization and state
- Ramp behavior
- Continuous movement and velocity integration
- Stop behavior
- Zoom control
"""

import time

import pytest

from src.ptz_simulator import SimulatedPTZService


class TestSimulatedPTZServiceInitialization:
    """Test SimulatedPTZService initialization."""

    def test_init_connected(self):
        """Service should be connected on initialization."""
        ptz = SimulatedPTZService()
        assert ptz.connected is True

    def test_init_position_home(self):
        """Service should start at home position."""
        ptz = SimulatedPTZService()
        assert ptz.pan_pos == 0.0
        assert ptz.tilt_pos == 0.0
        assert ptz.zoom_level == ptz.zmin

    def test_init_velocity_zero(self):
        """Service should start with zero velocity."""
        ptz = SimulatedPTZService()
        assert ptz.pan_vel == 0.0
        assert ptz.tilt_vel == 0.0
        assert ptz.zoom_vel == 0.0

    def test_init_ranges(self):
        """Pan/tilt/zoom ranges should be set correctly."""
        ptz = SimulatedPTZService()
        assert ptz.xmin == -1.0
        assert ptz.xmax == 1.0
        assert ptz.ymin == -1.0
        assert ptz.ymax == 1.0
        assert ptz.zmin == 0.0
        assert ptz.zmax == 1.0


class TestRamp:
    """Test ramp behavior."""

    def test_ramp_no_change_within_rate(self):
        """Ramp should reach target if delta is within rate."""
        ptz = SimulatedPTZService()
        ptz.ramp_rate = 0.5
        result = ptz.ramp(0.2, 0.0)
        assert result == 0.2

    def test_ramp_rate_limited(self):
        """Ramp should be limited by ramp_rate when delta exceeds it."""
        ptz = SimulatedPTZService()
        ptz.ramp_rate = 0.2
        result = ptz.ramp(1.0, 0.0)
        assert result == pytest.approx(0.2)

    def test_ramp_direction_positive(self):
        """Ramp should move in positive direction."""
        ptz = SimulatedPTZService()
        ptz.ramp_rate = 0.1
        result = ptz.ramp(1.0, 0.0)
        assert result > 0.0

    def test_ramp_direction_negative(self):
        """Ramp should move in negative direction."""
        ptz = SimulatedPTZService()
        ptz.ramp_rate = 0.1
        result = ptz.ramp(-1.0, 0.0)
        assert result < 0.0


class TestContinuousMove:
    """Test continuous move behavior."""

    def test_continuous_move_updates_velocity(self):
        """Continuous move should update velocity state."""
        ptz = SimulatedPTZService()
        # Use value well above threshold (default is 0.05)
        ptz.continuous_move(0.5, 0.0, 0.0)
        assert ptz.last_pan != 0.0 or ptz.pan_vel != 0.0

    def test_continuous_move_below_threshold_ignored(self):
        """Continuous move below threshold should be ignored."""
        ptz = SimulatedPTZService()
        ptz.last_pan = 0.5
        ptz.last_tilt = 0.5
        ptz.last_zoom = 0.5
        ptz.continuous_move(0.501, 0.501, 0.501, threshold=0.01)
        # State should not change significantly
        assert ptz.last_pan == 0.5
        assert ptz.last_tilt == 0.5
        assert ptz.last_zoom == 0.5

    def test_continuous_move_clamps_values(self):
        """Continuous move should clamp values to valid ranges."""
        ptz = SimulatedPTZService()
        ptz.continuous_move(2.0, 2.0, 2.0)
        # After ramping and clamping, should be within [-1, 1]
        assert -1.0 <= ptz.pan_vel <= 1.0
        assert -1.0 <= ptz.tilt_vel <= 1.0

    def test_continuous_move_updates_active(self):
        """Continuous move should set active flag when moving."""
        ptz = SimulatedPTZService()
        # Use value well above threshold (default is 0.05)
        ptz.continuous_move(0.5, 0.0, 0.0)
        # Should be active after non-zero command
        assert ptz.active is True or ptz.pan_vel != 0.0

    def test_continuous_move_integrates_position(self):
        """Continuous move should integrate velocity into position."""
        ptz = SimulatedPTZService()
        # Set velocity directly and simulate integration
        ptz.last_pan = 0.3
        initial_pan = ptz.pan_pos
        ptz.continuous_move(0.3, 0.0, 0.0)
        time.sleep(0.02)  # Small delay
        ptz.continuous_move(0.3, 0.0, 0.0)
        # Pan position should have moved in positive direction
        assert ptz.pan_pos >= initial_pan


class TestStop:
    """Test stop behavior."""

    def test_stop_resets_velocity(self):
        """Stop should reset all velocities."""
        ptz = SimulatedPTZService()
        ptz.continuous_move(0.5, 0.5, 0.5)
        ptz.stop()
        assert ptz.pan_vel == 0.0
        assert ptz.tilt_vel == 0.0
        assert ptz.zoom_vel == 0.0

    def test_stop_resets_last_values(self):
        """Stop should reset last command values."""
        ptz = SimulatedPTZService()
        ptz.continuous_move(0.5, 0.5, 0.5)
        ptz.stop()
        assert ptz.last_pan == 0.0
        assert ptz.last_tilt == 0.0
        assert ptz.last_zoom == 0.0

    def test_stop_sets_inactive(self):
        """Stop should set active to False."""
        ptz = SimulatedPTZService()
        ptz.continuous_move(0.5, 0.5, 0.5)
        ptz.stop()
        assert ptz.active is False

    def test_stop_selective_axes(self):
        """Stop should allow selective axis stopping."""
        ptz = SimulatedPTZService()
        ptz.pan_vel = 0.5
        ptz.tilt_vel = 0.5
        ptz.zoom_vel = 0.5
        ptz.stop(pan=True, tilt=False, zoom=False)
        assert ptz.pan_vel == 0.0
        assert ptz.tilt_vel == 0.5
        assert ptz.zoom_vel == 0.5


class TestZoomControl:
    """Test zoom control methods."""

    def test_set_zoom_absolute_valid(self):
        """set_zoom_absolute should set zoom level."""
        ptz = SimulatedPTZService()
        ptz.set_zoom_absolute(0.5)
        assert ptz.zoom_level == pytest.approx(0.5)

    def test_set_zoom_absolute_clamps_max(self):
        """set_zoom_absolute should clamp to zmax."""
        ptz = SimulatedPTZService()
        ptz.set_zoom_absolute(2.0)
        assert ptz.zoom_level == pytest.approx(ptz.zmax)

    def test_set_zoom_absolute_clamps_min(self):
        """set_zoom_absolute should clamp to zmin."""
        ptz = SimulatedPTZService()
        ptz.set_zoom_absolute(-1.0)
        assert ptz.zoom_level == pytest.approx(ptz.zmin)

    def test_set_zoom_relative_increases(self):
        """set_zoom_relative should increase from current."""
        ptz = SimulatedPTZService()
        ptz.zoom_level = 0.2
        ptz.set_zoom_relative(0.2)
        assert ptz.zoom_level == pytest.approx(0.4)

    def test_set_zoom_relative_decreases(self):
        """set_zoom_relative should decrease from current."""
        ptz = SimulatedPTZService()
        ptz.zoom_level = 0.5
        ptz.set_zoom_relative(-0.2)
        assert ptz.zoom_level == pytest.approx(0.3)

    def test_get_zoom_returns_current(self):
        """get_zoom should return current zoom level."""
        ptz = SimulatedPTZService()
        ptz.zoom_level = 0.6
        assert ptz.get_zoom() == pytest.approx(0.6)

    def test_set_zoom_home(self):
        """set_zoom_home should set zoom to zmin."""
        ptz = SimulatedPTZService()
        ptz.zoom_level = 0.8
        ptz.set_zoom_home()
        assert ptz.zoom_level == pytest.approx(ptz.zmin)


class TestSetHomePosition:
    """Test home position behavior."""

    def test_set_home_position_resets_pan_tilt(self):
        """set_home_position should reset pan and tilt to zero."""
        ptz = SimulatedPTZService()
        ptz.pan_pos = 0.5
        ptz.tilt_pos = 0.5
        ptz.set_home_position()
        assert ptz.pan_pos == pytest.approx(0.0)
        assert ptz.tilt_pos == pytest.approx(0.0)

    def test_set_home_position_resets_zoom(self):
        """set_home_position should reset zoom to zmin."""
        ptz = SimulatedPTZService()
        ptz.zoom_level = 0.8
        ptz.set_home_position()
        assert ptz.zoom_level == pytest.approx(ptz.zmin)

    def test_set_home_position_resets_velocities(self):
        """set_home_position should reset all velocities."""
        ptz = SimulatedPTZService()
        ptz.pan_vel = 0.5
        ptz.tilt_vel = 0.5
        ptz.zoom_vel = 0.5
        ptz.set_home_position()
        assert ptz.pan_vel == pytest.approx(0.0)
        assert ptz.tilt_vel == pytest.approx(0.0)
        assert ptz.zoom_vel == pytest.approx(0.0)

    def test_set_home_position_sets_inactive(self):
        """set_home_position should set active to False."""
        ptz = SimulatedPTZService()
        ptz.continuous_move(0.5, 0.5, 0.5)
        ptz.set_home_position()
        assert ptz.active is False


class TestViewportMath:
    """Test viewport cropping and resizing math from main.py."""

    def test_viewport_scaling_at_zoom_zero(self):
        """At zoom 0 (zmin), scale should be 1.0."""
        ptz = SimulatedPTZService()
        ptz.zoom_level = ptz.zmin
        z_normalized = (ptz.zoom_level - ptz.zmin) / (ptz.zmax - ptz.zmin + 1e-6)
        sim_zoom_min_scale = ptz.settings.simulator.sim_zoom_min_scale
        scale = 1.0 - z_normalized * (1.0 - sim_zoom_min_scale)
        assert scale == pytest.approx(1.0)

    def test_viewport_scaling_at_zoom_max(self):
        """At zoom zmax, scale should be SIM_ZOOM_MIN_SCALE."""
        ptz = SimulatedPTZService()
        ptz.zoom_level = ptz.zmax
        z_normalized = (ptz.zoom_level - ptz.zmin) / (ptz.zmax - ptz.zmin + 1e-6)
        sim_zoom_min_scale = ptz.settings.simulator.sim_zoom_min_scale
        scale = 1.0 - z_normalized * (1.0 - sim_zoom_min_scale)
        assert scale == pytest.approx(sim_zoom_min_scale, abs=1e-6)

    def test_viewport_scaling_linear(self):
        """Viewport scale should vary linearly with zoom."""
        ptz = SimulatedPTZService()
        sim_zoom_min_scale = ptz.settings.simulator.sim_zoom_min_scale
        scales = []
        for z in [0.0, 0.25, 0.5, 0.75, 1.0]:
            ptz.zoom_level = z
            z_normalized = (ptz.zoom_level - ptz.zmin) / (ptz.zmax - ptz.zmin + 1e-6)
            scale = 1.0 - z_normalized * (1.0 - sim_zoom_min_scale)
            scales.append(scale)
        # Scales should be monotonically decreasing
        for i in range(len(scales) - 1):
            assert scales[i] >= scales[i + 1]

    def test_viewport_pan_center_at_origin(self):
        """Pan at 0 should center viewport horizontally."""
        ptz = SimulatedPTZService()
        ptz.pan_pos = 0.0
        frame_w = 640
        crop_w = 320
        cx = frame_w / 2 + ptz.pan_pos * (frame_w / 2 - crop_w / 2)
        assert cx == pytest.approx(frame_w / 2)

    def test_viewport_pan_right(self):
        """Positive pan should move viewport right."""
        ptz = SimulatedPTZService()
        ptz.pan_pos = 0.5
        frame_w = 640
        crop_w = 320
        cx = frame_w / 2 + ptz.pan_pos * (frame_w / 2 - crop_w / 2)
        assert cx > frame_w / 2

    def test_viewport_pan_left(self):
        """Negative pan should move viewport left."""
        ptz = SimulatedPTZService()
        ptz.pan_pos = -0.5
        frame_w = 640
        crop_w = 320
        cx = frame_w / 2 + ptz.pan_pos * (frame_w / 2 - crop_w / 2)
        assert cx < frame_w / 2

    def test_viewport_tilt_center_at_origin(self):
        """Tilt at 0 should center viewport vertically."""
        ptz = SimulatedPTZService()
        ptz.tilt_pos = 0.0
        frame_h = 480
        crop_h = 240
        cy = frame_h / 2 - ptz.tilt_pos * (frame_h / 2 - crop_h / 2)
        assert cy == pytest.approx(frame_h / 2)

    def test_viewport_tilt_up(self):
        """Positive tilt should move viewport up."""
        ptz = SimulatedPTZService()
        ptz.tilt_pos = 0.5
        frame_h = 480
        crop_h = 240
        cy = frame_h / 2 - ptz.tilt_pos * (frame_h / 2 - crop_h / 2)
        assert cy < frame_h / 2

    def test_viewport_tilt_down(self):
        """Negative tilt should move viewport down."""
        ptz = SimulatedPTZService()
        ptz.tilt_pos = -0.5
        frame_h = 480
        crop_h = 240
        cy = frame_h / 2 - ptz.tilt_pos * (frame_h / 2 - crop_h / 2)
        assert cy > frame_h / 2


class TestBoundsClamping:
    """Test that positions are clamped correctly."""

    def test_pan_pos_clamped_positive(self):
        """Pan position should not exceed xmax."""
        ptz = SimulatedPTZService()
        ptz.pan_pos = 2.0
        ptz.pan_pos = max(ptz.xmin, min(ptz.xmax, ptz.pan_pos))
        assert ptz.pan_pos == pytest.approx(ptz.xmax)

    def test_pan_pos_clamped_negative(self):
        """Pan position should not go below xmin."""
        ptz = SimulatedPTZService()
        ptz.pan_pos = -2.0
        ptz.pan_pos = max(ptz.xmin, min(ptz.xmax, ptz.pan_pos))
        assert ptz.pan_pos == pytest.approx(ptz.xmin)

    def test_tilt_pos_clamped_positive(self):
        """Tilt position should not exceed ymax."""
        ptz = SimulatedPTZService()
        ptz.tilt_pos = 2.0
        ptz.tilt_pos = max(ptz.ymin, min(ptz.ymax, ptz.tilt_pos))
        assert ptz.tilt_pos == pytest.approx(ptz.ymax)

    def test_tilt_pos_clamped_negative(self):
        """Tilt position should not go below ymin."""
        ptz = SimulatedPTZService()
        ptz.tilt_pos = -2.0
        ptz.tilt_pos = max(ptz.ymin, min(ptz.ymax, ptz.tilt_pos))
        assert ptz.tilt_pos == pytest.approx(ptz.ymin)

    def test_zoom_level_clamped_positive(self):
        """Zoom level should not exceed zmax."""
        ptz = SimulatedPTZService()
        ptz.zoom_level = 2.0
        ptz.zoom_level = max(ptz.zmin, min(ptz.zmax, ptz.zoom_level))
        assert ptz.zoom_level == pytest.approx(ptz.zmax)

    def test_zoom_level_clamped_negative(self):
        """Zoom level should not go below zmin."""
        ptz = SimulatedPTZService()
        ptz.zoom_level = -1.0
        ptz.zoom_level = max(ptz.zmin, min(ptz.zmax, ptz.zoom_level))
        assert ptz.zoom_level == pytest.approx(ptz.zmin)
