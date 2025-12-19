"""
PTZ Controller using Octagon HTTP API.

This module provides PTZ (Pan-Tilt-Zoom) camera control via the Infiniti
Octagon platform HTTP API. It replaces the previous ONVIF-based implementation.
"""

import time
from typing import Any

import requests
from loguru import logger
from requests.auth import HTTPBasicAuth

from src.settings import Settings


class PTZError(Exception):
    """Base exception for PTZ service errors."""


class PTZConnectionError(PTZError):
    """Exception raised when PTZ camera connection fails."""


class PTZCommandError(PTZError):
    """Exception raised when a PTZ command fails."""


class PTZProfileError(PTZError):
    """Exception raised when no media profiles are found on camera."""

    def __init__(self) -> None:
        super().__init__("No media profiles found on camera.")


class OctagonAPIClient:
    """
    HTTP client for Octagon Platform API communication.

    Handles authentication, request construction, and response parsing
    for the Infiniti Octagon platform.
    """

    def __init__(
        self,
        base_url: str,
        username: str = "admin",
        password: str = "!Inf",
        timeout: float = 5.0,
    ) -> None:
        """
        Initialize Octagon API client.

        Args:
            base_url: Base URL of the Octagon platform (e.g., "http://192.168.1.21")
            username: API username (default: admin)
            password: API password (default: !Inf)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.auth = HTTPBasicAuth(username, password)
        self.timeout = timeout
        self.session = requests.Session()
        self.session.auth = self.auth

    def get(self, endpoint: str, params: dict | None = None) -> dict[str, Any]:
        """
        Execute GET request to Octagon API.

        Args:
            endpoint: API endpoint (e.g., "/api/devices/pantilt/position")
            params: Optional query parameters

        Returns:
            Response data dict

        Raises:
            PTZConnectionError: If connection fails
            PTZCommandError: If API returns an error
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            if not data.get("success", True):
                error = data.get("error", {})
                raise PTZCommandError(
                    f"API error: {error.get('message', 'Unknown error')}"
                )

            return data.get("data", data)
        except requests.exceptions.ConnectionError as e:
            raise PTZConnectionError(f"Connection failed to {url}: {e}") from e
        except requests.exceptions.Timeout as e:
            raise PTZConnectionError(f"Request timeout to {url}: {e}") from e
        except requests.exceptions.RequestException as e:
            raise PTZCommandError(f"Request failed: {e}") from e

    def post(
        self, endpoint: str, data: dict | None = None, params: dict | None = None
    ) -> dict[str, Any]:
        """
        Execute POST request to Octagon API.

        Args:
            endpoint: API endpoint
            data: JSON body data
            params: Optional query parameters

        Returns:
            Response data dict

        Raises:
            PTZConnectionError: If connection fails
            PTZCommandError: If API returns an error
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.post(
                url, json=data, params=params, timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()

            if not result.get("success", True):
                error = result.get("error", {})
                raise PTZCommandError(
                    f"API error: {error.get('message', 'Unknown error')}"
                )

            return result.get("data", result)
        except requests.exceptions.ConnectionError as e:
            raise PTZConnectionError(f"Connection failed to {url}: {e}") from e
        except requests.exceptions.Timeout as e:
            raise PTZConnectionError(f"Request timeout to {url}: {e}") from e
        except requests.exceptions.RequestException as e:
            raise PTZCommandError(f"Request failed: {e}") from e

    def test_connection(self) -> bool:
        """
        Test connection to the Octagon API.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.get("/api")
            return True
        except (PTZConnectionError, PTZCommandError):
            return False


class PTZService:
    """
    PTZ camera control service using Octagon HTTP API.

    Provides pan, tilt, zoom control with smooth ramping transitions.
    """

    # Direction mappings for Octagon API
    DIRECTION_MAP = {
        "up": "up",
        "down": "down",
        "left": "left",
        "right": "right",
        "up_right": "upright",
        "up_left": "upleft",
        "down_right": "downright",
        "down_left": "downleft",
    }

    @logger.catch
    def __init__(
        self,
        ip: str | None = None,
        port: int = 80,
        user: str | None = None,
        password: str | None = None,
        settings: Settings | None = None,
    ) -> None:
        """
        Initialize the PTZ service with Settings configuration.

        Args:
            ip: Optional IP address (overrides settings).
            port: Optional port (default 80).
            user: Optional user (overrides settings).
            password: Optional password (overrides settings).
            settings: Settings object containing camera credentials and PTZ configuration.
                     If None, defaults are loaded.
        """
        if settings is None:
            from src.settings import load_settings  # noqa: PLC0415 - Lazy import

            settings = load_settings()

        self.settings = settings
        self.connected = False
        self.active = False
        self.client: OctagonAPIClient | None = None

        try:
            # Get credentials from Settings
            creds = {
                "ip": self.settings.detection.camera_credentials.ip,
                "user": self.settings.detection.camera_credentials.user,
                "pass": self.settings.detection.camera_credentials.password,
            }

            ip = ip or creds["ip"]
            user = user or creds["user"]
            password = password or creds["pass"]

            if not ip:
                logger.error("PTZService: No IP address provided")
                self.connected = False
                return

            # Build base URL
            base_url = f"http://{ip}:{port}"

            # Initialize Octagon API client
            self.client = OctagonAPIClient(
                base_url=base_url,
                username=user or "admin",
                password=password or "!Inf",
            )

            # Test connection
            if not self.client.test_connection():
                logger.error(f"PTZService: Failed to connect to Octagon API at {ip}")
                self.connected = False
                return

            logger.info(f"PTZService: Connected to Octagon API at {base_url}")

            # Initialize pan/tilt velocity ranges (Octagon uses 0-100 speed percentage)
            self.xmin = -1.0
            self.xmax = 1.0
            self.ymin = -1.0
            self.ymax = 1.0

            # Zoom is 0-100 percentage in Octagon API
            self.zmin = 0.0
            self.zmax = 100.0

            self.connected = True

        except Exception as e:
            logger.error(f"PTZService connection failed: {e}")
            self.connected = False
            return

        self.zoom_level = 0.0

        # For smooth transitions (use settings value)
        self.last_pan = 0.0
        self.last_tilt = 0.0
        self.last_zoom = 0.0
        self.ramp_rate = self.settings.ptz.ptz_ramp_rate

        # Track last movement command time for debouncing
        self._last_command_time = 0.0
        self._min_command_interval = 0.05  # 50ms minimum between commands

    def ramp(self, target: float, current: float) -> float:
        """Simple linear ramping for smooth transitions."""
        delta = target - current
        if abs(delta) > self.ramp_rate:
            return current + self.ramp_rate * (1 if delta > 0 else -1)
        return target

    def _get_direction_and_speeds(
        self, pan: float, tilt: float
    ) -> tuple[str | None, int, int]:
        """
        Convert pan/tilt velocities to Octagon direction and speeds.

        Args:
            pan: Pan velocity [-1.0, 1.0]. Positive = right.
            tilt: Tilt velocity [-1.0, 1.0]. Positive = up.

        Returns:
            Tuple of (direction, pan_speed, tilt_speed)
            direction is None if no movement needed
        """
        # Determine direction based on velocity signs
        direction_parts = []

        if tilt > 0.01:
            direction_parts.append("up")
        elif tilt < -0.01:
            direction_parts.append("down")

        if pan > 0.01:
            direction_parts.append("right")
        elif pan < -0.01:
            direction_parts.append("left")

        if not direction_parts:
            return None, 0, 0

        direction = "".join(direction_parts)

        # Convert velocity magnitude to speed percentage (0-100)
        pan_speed = int(abs(pan) * 100)
        tilt_speed = int(abs(tilt) * 100)

        # Clamp speeds to valid range
        pan_speed = max(1, min(100, pan_speed))
        tilt_speed = max(1, min(100, tilt_speed))

        return direction, pan_speed, tilt_speed

    def continuous_move(
        self, pan: float, tilt: float, zoom: float, threshold: float = 0.01
    ) -> None:
        """
        Move the camera continuously in pan, tilt, and zoom.

        Uses Octagon API's relative move command for pan/tilt and
        visible lens zoom commands.

        Args:
            pan: Pan velocity, range [-1.0, 1.0]. Positive = right.
            tilt: Tilt velocity, range [-1.0, 1.0]. Positive = up.
            zoom: Zoom velocity. Positive = zoom in (tele), negative = zoom out (wide).
            threshold: Minimum change to send command (default 0.01).
        """
        if not self.connected or not self.client:
            return

        # Debounce commands
        current_time = time.time()
        if current_time - self._last_command_time < self._min_command_interval:
            return
        self._last_command_time = current_time

        # Convert inputs to float before processing
        pan = float(pan)
        tilt = float(tilt)
        zoom = float(zoom)

        # Smooth transitions
        pan = round(self.ramp(pan, self.last_pan), 2)
        tilt = round(self.ramp(tilt, self.last_tilt), 2)
        zoom = round(max(-1.0, min(1.0, zoom)), 2)

        # Only send if significant change
        if (
            abs(pan - self.last_pan) < threshold
            and abs(tilt - self.last_tilt) < threshold
            and abs(zoom - self.last_zoom) < threshold
        ):
            return

        try:
            # Handle pan/tilt movement
            direction, pan_speed, tilt_speed = self._get_direction_and_speeds(pan, tilt)

            if direction:
                # API 3.28: Move Pan-Tilt Relative
                # GET /api/devices/pantilt?command=move&direction=<DIRECTION>&panSpeed=<SPEED>&tiltSpeed=<SPEED>
                self.client.get(
                    "/api/devices/pantilt",
                    params={
                        "command": "move",
                        "direction": direction,
                        "panSpeed": pan_speed,
                        "tiltSpeed": tilt_speed,
                    },
                )
                logger.debug(
                    f"PTZ move: direction={direction}, panSpeed={pan_speed}, "
                    f"tiltSpeed={tilt_speed}"
                )
            elif self.last_pan != 0 or self.last_tilt != 0:
                # Stop pan/tilt movement if we were moving before
                self.client.get("/api/devices/pantilt", params={"command": "stop"})
                logger.debug("PTZ pan/tilt stopped")

            # Handle zoom movement
            if abs(zoom) > threshold:
                zoom_command = "zoomTele" if zoom > 0 else "zoomWide"
                # API 3.45: Move Visible Lens
                self.client.get("/api/devices/visible1", params={"command": zoom_command})
                logger.debug(f"Zoom: {zoom_command}")
            elif abs(self.last_zoom) > threshold and abs(zoom) <= threshold:
                # Stop zoom if we were zooming before
                # API 3.46: Stop Visible Lens
                self.client.get("/api/devices/visible1", params={"command": "stop"})
                logger.debug("Zoom stopped")

            self.active = pan != 0 or tilt != 0 or zoom != 0
            self.last_pan = pan
            self.last_tilt = tilt
            self.last_zoom = zoom

        except Exception as e:
            logger.error(f"PTZ continuous_move error: {e}", exc_info=True)

    def stop(self, pan: bool = True, tilt: bool = True, zoom: bool = True) -> None:
        """
        Stop PTZ movement on specified axes.

        Args:
            pan: Stop pan movement (default True).
            tilt: Stop tilt movement (default True).
            zoom: Stop zoom movement (default True).
        """
        if not self.connected or not self.client:
            return

        try:
            if pan or tilt:
                # API 3.29: Stop Pan-Tilt
                self.client.get("/api/devices/pantilt", params={"command": "stop"})
                logger.debug("Pan/tilt stopped")

            if zoom:
                # API 3.46: Stop Visible Lens
                self.client.get("/api/devices/visible1", params={"command": "stop"})
                logger.debug("Zoom stopped")

            self.active = False

            # Reset the axes that are being stopped
            if pan:
                self.last_pan = 0.0
            if tilt:
                self.last_tilt = 0.0
            if zoom:
                self.last_zoom = 0.0

        except Exception as e:
            logger.error(f"PTZ stop error: {e}")

    def set_zoom_absolute(self, zoom_value: float) -> None:
        """
        Set absolute zoom position.

        Args:
            zoom_value: Zoom value to set (0-100 percentage).
        """
        if not self.connected or not self.client:
            return

        try:
            # Clamp zoom to valid range (0-100)
            zoom_value = max(self.zmin, min(self.zmax, float(zoom_value)))

            # API 3.40: Set Visible Lens Position (visible1 device)
            self.client.post(
                "/api/devices/visible1/position",
                data={"zoom": zoom_value},
            )
            self.zoom_level = zoom_value
            self.last_zoom = 0.0  # Reset velocity

            logger.debug(f"Set zoom to {zoom_value}%")

        except Exception as e:
            logger.error(f"set_zoom_absolute error: {e}")

    def set_zoom_home(self) -> None:
        """Set zoom to the home (widest) position defined by self.zmin."""
        self.set_zoom_absolute(self.zmin)

    def set_home_position(self) -> None:
        """
        Move the camera to its home position using Octagon home command.
        """
        if not self.connected or not self.client:
            return

        try:
            # Use Octagon pantilt home command
            # GET /api/devices/pantilt?command=home
            self.client.get("/api/devices/pantilt", params={"command": "home"})

            # Also reset zoom to minimum
            self.set_zoom_home()

            # Update internal state
            self.last_pan = 0.0
            self.last_tilt = 0.0
            self.last_zoom = 0.0
            self.zoom_level = self.zmin

            logger.info("PTZ moved to home position")

        except Exception as e:
            logger.error(f"set_home_position error: {e}")

    def set_zoom_relative(self, zoom_delta: float) -> None:
        """
        Set zoom relatively from current position.

        Args:
            zoom_delta: Amount to change zoom by (percentage).
        """
        if not self.connected or not self.client:
            return

        try:
            current_zoom = self.get_zoom()
            new_zoom = max(self.zmin, min(self.zmax, current_zoom + zoom_delta))
            self.set_zoom_absolute(new_zoom)
        except Exception as e:
            logger.error(f"set_zoom_relative error: {e}")

    def get_zoom(self) -> float:
        """
        Get current zoom position.

        Returns:
            Current zoom value (0-100 percentage), or zmin if unavailable.
        """
        if not self.connected or not self.client:
            return self.zmin

        try:
            # GET /api/devices/visible/position
            data = self.client.get("/api/devices/visible/position")
            return float(data.get("zoom", self.zmin))
        except Exception:
            return self.zmin

    def get_position(self) -> dict[str, float]:
        """
        Get current pan/tilt position.

        Returns:
            Dict with 'pan' and 'tilt' keys in degrees.
        """
        if not self.connected or not self.client:
            return {"pan": 0.0, "tilt": 0.0}

        try:
            # GET /api/devices/pantilt/position
            data = self.client.get("/api/devices/pantilt/position")
            return {
                "pan": float(data.get("pan", 0.0)),
                "tilt": float(data.get("tilt", 0.0)),
            }
        except Exception:
            return {"pan": 0.0, "tilt": 0.0}

    def set_position_absolute(self, pan: float, tilt: float) -> None:
        """
        Set absolute pan/tilt position in degrees.

        Args:
            pan: Pan angle (0-360 degrees)
            tilt: Tilt angle (-90 to 90 degrees)
        """
        if not self.connected or not self.client:
            return

        try:
            # Clamp values to valid ranges
            pan = max(0, min(360, float(pan)))
            tilt = max(-90, min(90, float(tilt)))

            # POST /api/devices/pantilt/position
            self.client.post(
                "/api/devices/pantilt/position",
                data={"pan": pan, "tilt": tilt},
            )

            logger.debug(f"Set position to pan={pan}, tilt={tilt}")

        except Exception as e:
            logger.error(f"set_position_absolute error: {e}")

    def get_status(self) -> dict[str, Any]:
        """
        Get detailed PTZ status.

        Returns:
            Status dict from Octagon API.
        """
        if not self.connected or not self.client:
            return {"connected": False}

        try:
            # GET /api/devices/pantilt/status
            status = self.client.get("/api/devices/pantilt/status")
            status["connected"] = True
            return status
        except Exception:
            return {"connected": False}

    def initialize_device(self) -> bool:
        """
        Initialize/reinitialize the PTZ device.

        Returns:
            True if successful, False otherwise.
        """
        if not self.client:
            return False

        try:
            # GET /api/devices/pantilt?command=initialize
            self.client.get("/api/devices/pantilt", params={"command": "initialize"})
            logger.info("PTZ device initialized")
            return True
        except Exception as e:
            logger.error(f"initialize_device error: {e}")
            return False

    def set_stabilization(self, enable: bool) -> None:
        """
        Enable or disable gyro stabilization.

        Args:
            enable: True to enable, False to disable.
        """
        if not self.connected or not self.client:
            return

        try:
            # GET /api/devices/pantilt/gyro?enable=<true OR false>
            self.client.get(
                "/api/devices/pantilt/gyro",
                params={"enable": str(enable).lower()},
            )
            logger.info(f"Stabilization {'enabled' if enable else 'disabled'}")
        except Exception as e:
            logger.error(f"set_stabilization error: {e}")

    def get_stabilization(self) -> bool:
        """
        Get current stabilization status.

        Returns:
            True if stabilization is active, False otherwise.
        """
        if not self.connected or not self.client:
            return False

        try:
            # GET /api/devices/pantilt/gyro
            data = self.client.get("/api/devices/pantilt/gyro")
            return data.get("active", False)
        except Exception:
            return False

    def update_position_from_octagon(self) -> bool:
        """Best-effort sync of current PTZ position from the Octagon API.

        This updates `pan_pos` / `tilt_pos` (degrees) and `zoom_level` (0-100) when
        available. It does not mutate the last commanded velocities used for ramping.
        """
        if not self.connected or not self.client:
            return False

        try:
            pos = self.get_position()
            self.pan_pos = float(pos.get("pan", 0.0))
            self.tilt_pos = float(pos.get("tilt", 0.0))
            self.zoom_level = float(self.get_zoom())
        except Exception:
            return False

        return True
