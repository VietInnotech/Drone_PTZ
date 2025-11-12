"""
Simulated PTZ service for testing and development without a physical camera.

Provides a drop-in replacement for PTZService that simulates pan/tilt/zoom
behavior using a simple, smooth motion model.
"""

import time

from loguru import logger

from src.settings import Settings, load_settings


class SimulatedPTZService:
    """
    Simulated PTZ backend with the same public API as PTZService.

    The simulator models smooth pan/tilt/zoom motion with velocity ramping
    and position integration. All motion is purely simulated; no ONVIF commands
    are sent.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """
        Initialize the simulated PTZ service.

        Args:
            settings: Settings object containing PTZ configuration. If None, defaults are used.
        """
        # Create default settings if not provided
        if settings is None:
            settings = load_settings()

        self.settings = settings
        self.connected = True
        self.active = False  # Pan/tilt ranges (normalized to [-1, 1])
        self.xmin = -1.0
        self.xmax = 1.0
        self.ymin = -1.0
        self.ymax = 1.0

        # Zoom range (normalized to [0, 1])
        self.zmin = 0.0
        self.zmax = 1.0

        # Current absolute positions
        self.pan_pos = 0.0
        self.tilt_pos = 0.0
        self.zoom_level = self.zmin

        # Current velocities
        self.pan_vel = 0.0
        self.tilt_vel = 0.0
        self.zoom_vel = 0.0

        # Last command values for ramping
        self.last_pan = 0.0
        self.last_tilt = 0.0
        self.last_zoom = 0.0

        # Ramp rate from settings
        self.ramp_rate = self.settings.ptz.ptz_ramp_rate

        # Motion parameters
        self.sim_accel = 0.5  # acceleration limit (units/sec^2)
        self.sim_pan_rate = (
            2.0  # max pan speed (units/sec at full command) - increased from 1.0
        )
        self.sim_tilt_rate = (
            2.0  # max tilt speed (units/sec at full command) - increased from 1.0
        )
        self.sim_zoom_rate = (
            1.0  # max zoom speed (units/sec at full command) - increased from 0.5
        )

        # Timestamp for dt calculation
        self._last_update = time.time()

        logger.info(
            f"SimulatedPTZService initialized: pan=[{self.xmin}, {self.xmax}], "
            f"tilt=[{self.ymin}, {self.ymax}], zoom=[{self.zmin}, {self.zmax}]"
        )

    def ramp(self, target: float, current: float) -> float:
        """
        Simple linear ramping for smooth transitions.

        Args:
            target: Target value.
            current: Current value.

        Returns:
            Ramped value that approaches target at rate limited by ramp_rate.
        """
        delta = target - current
        if abs(delta) > self.ramp_rate:
            return current + self.ramp_rate * (1 if delta > 0 else -1)
        return target

    def continuous_move(
        self, pan: float, tilt: float, zoom: float, threshold: float = 0.01
    ) -> None:
        """
        Move the camera continuously in pan, tilt, and zoom.

        Smoothly ramps velocities toward desired values and integrates positions
        with clamping at bounds.

        Args:
            pan: Pan velocity, range [-1.0, 1.0]. Positive = right.
            tilt: Tilt velocity, range [-1.0, 1.0]. Positive = up.
            zoom: Zoom velocity. Positive = zoom in.
            threshold: Minimum change to send command (default 0.01).
        """
        # Convert inputs to float
        pan = float(pan)
        tilt = float(tilt)
        zoom = float(zoom)

        # Apply ramp for smooth transitions
        pan = round(self.ramp(pan, self.last_pan), 2)
        tilt = round(self.ramp(tilt, self.last_tilt), 2)
        zoom = round(max(-self.zmax, min(self.zmax, zoom)), 2)

        # Only update if significant change
        if (
            abs(pan - self.last_pan) < threshold
            and abs(tilt - self.last_tilt) < threshold
            and abs(zoom - self.last_zoom) < threshold
        ):
            return

        # Update last values
        self.last_pan = pan
        self.last_tilt = tilt
        self.last_zoom = zoom

        # Calculate time delta for integration
        now = time.time()
        dt = now - self._last_update
        self._last_update = now

        if dt <= 0:
            dt = 0.016  # fallback to ~60 FPS if dt is 0

        # Cap dt to prevent large jumps during processing delays or frame drops
        # This ensures smooth motion even if frame processing is slow
        max_dt = 0.5  # ~30fps - prevents viewport jumping when ID is selected
        dt = min(dt, max_dt)

        # Ramp velocities toward desired values using acceleration limit
        accel_limit = self.sim_accel * dt
        self.pan_vel = max(
            -1.0,
            min(
                1.0,
                self.pan_vel + accel_limit * (1 if pan > self.pan_vel else -1)
                if abs(pan - self.pan_vel) > accel_limit
                else pan,
            ),
        )
        self.tilt_vel = max(
            -1.0,
            min(
                1.0,
                self.tilt_vel + accel_limit * (1 if tilt > self.tilt_vel else -1)
                if abs(tilt - self.tilt_vel) > accel_limit
                else tilt,
            ),
        )
        self.zoom_vel = max(
            -1.0,
            min(
                1.0,
                self.zoom_vel + accel_limit * (1 if zoom > self.zoom_vel else -1)
                if abs(zoom - self.zoom_vel) > accel_limit
                else zoom,
            ),
        )

        # Integrate positions with velocity
        self.pan_pos = max(
            self.xmin,
            min(self.xmax, self.pan_pos + self.pan_vel * self.sim_pan_rate * dt),
        )
        self.tilt_pos = max(
            self.ymin,
            min(
                self.ymax,
                self.tilt_pos + self.tilt_vel * self.sim_tilt_rate * dt,
            ),
        )
        self.zoom_level = max(
            self.zmin,
            min(
                self.zmax,
                self.zoom_level + self.zoom_vel * self.sim_zoom_rate * dt,
            ),
        )

        # Update active status
        self.active = pan != 0 or tilt != 0 or zoom != 0

        logger.debug(
            f"continuous_move: pan_vel={self.pan_vel:.2f}, tilt_vel={self.tilt_vel:.2f}, "
            f"zoom_vel={self.zoom_vel:.2f} | pan_pos={self.pan_pos:.3f}, "
            f"tilt_pos={self.tilt_pos:.3f}, zoom_level={self.zoom_level:.3f}"
        )

    def stop(self, pan: bool = True, tilt: bool = True, zoom: bool = True) -> None:
        """
        Stop PTZ movement on specified axes.

        Args:
            pan: Stop pan movement (default True).
            tilt: Stop tilt movement (default True).
            zoom: Stop zoom movement (default True).
        """
        if pan:
            self.pan_vel = 0.0
        if tilt:
            self.tilt_vel = 0.0
        if zoom:
            self.zoom_vel = 0.0

        self.active = False
        self.last_pan = 0.0
        self.last_tilt = 0.0
        self.last_zoom = 0.0

        logger.debug(f"stop called: pan={pan}, tilt={tilt}, zoom={zoom}")

    def set_zoom_absolute(self, zoom_value: float) -> None:
        """
        Set absolute zoom position.

        Args:
            zoom_value: Zoom value to set (will be clamped to valid range).
        """
        zoom_value = max(self.zmin, min(self.zmax, float(zoom_value)))
        self.zoom_level = zoom_value
        self.last_zoom = zoom_value
        logger.debug(f"set_zoom_absolute: {zoom_value:.3f}")

    def set_zoom_relative(self, zoom_delta: float) -> None:
        """
        Set zoom relatively from current position.

        Args:
            zoom_delta: Amount to change zoom by.
        """
        current_zoom = self.get_zoom()
        new_zoom = max(self.zmin, min(self.zmax, current_zoom + zoom_delta))
        self.set_zoom_absolute(new_zoom)

    def set_zoom_home(self) -> None:
        """Set zoom to the home (widest) position defined by zmin."""
        self.set_zoom_absolute(self.zmin)

    def set_home_position(self) -> None:
        """Reset pan/tilt/zoom to home position (0, 0, zmin)."""
        self.pan_pos = 0.0
        self.tilt_pos = 0.0
        self.pan_vel = 0.0
        self.tilt_vel = 0.0
        self.zoom_vel = 0.0
        self.last_pan = 0.0
        self.last_tilt = 0.0
        self.last_zoom = self.zmin
        self.zoom_level = self.zmin
        self.active = False
        logger.debug("set_home_position: pan=0, tilt=0, zoom=zmin")

    def get_zoom(self) -> float:
        """
        Get current zoom position.

        Returns:
            Current zoom value.
        """
        return self.zoom_level
