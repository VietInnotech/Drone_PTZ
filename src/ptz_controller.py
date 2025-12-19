import requests
from loguru import logger

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


def get_onvif_camera():
    """Lazy import for ONVIFCamera to avoid heavy dependencies during testing."""
    from onvif import ONVIFCamera  # noqa: PLC0415 - Intentional lazy import for testing

    return ONVIFCamera


class PTZService:
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

            # Store credentials for Octagon API access (separate from ONVIF)
            self.octagon_ip = self.settings.octagon.ip
            self.octagon_user = self.settings.octagon.user
            self.octagon_pass = self.settings.octagon.password
            self.octagon_pantilt_id = self.settings.octagon_devices.pantilt_id
            self.octagon_visible_id = self.settings.octagon_devices.visible_id
            # Control path selection
            self.control_mode = getattr(self.settings.ptz, "control_mode", "onvif")
            # Use lazy import for ONVIFCamera
            onvif_camera_cls = get_onvif_camera()
            self.cam = onvif_camera_cls(ip, port, user, password)
            self.media = self.cam.create_media_service()
            self.ptz = self.cam.create_ptz_service()
            profiles = self.media.GetProfiles()
        except Exception as e:
            logger.error(f"PTZService connection failed: {e}")
            self.connected = False
            self.request = None  # Set to None on failure
            return

        if not profiles:
            logger.error("No media profiles found on camera")
            self.connected = False
            self.request = None
            return

        try:
            self.profile = profiles[0]
            logger.info(f"Selected profile: {self.profile}")
            logger.info(f"Profile token: {self.profile.token}")
            logger.info(f"Type of profile token: {type(self.profile.token)}")
            options = self.ptz.GetConfigurationOptions(
                {"ConfigurationToken": self.profile.PTZConfiguration.token}
            )

            if (
                options
                and hasattr(options, "Spaces")
                and options.Spaces
                and hasattr(options.Spaces, "ContinuousPanTiltVelocitySpace")
            ):
                self.xmax = options.Spaces.ContinuousPanTiltVelocitySpace[0].XRange.Max
                self.xmin = options.Spaces.ContinuousPanTiltVelocitySpace[0].XRange.Min
                self.ymax = options.Spaces.ContinuousPanTiltVelocitySpace[0].YRange.Max
                self.ymin = options.Spaces.ContinuousPanTiltVelocitySpace[0].YRange.Min
            else:
                self.xmax = 1.0
                self.xmin = -1.0
                self.ymax = 1.0
                self.ymin = -1.0
            abs_zoom_space = (
                getattr(options.Spaces, "AbsoluteZoomPositionSpace", None)
                if options and hasattr(options, "Spaces") and options.Spaces
                else None
            )
            if abs_zoom_space and len(abs_zoom_space) > 0:
                self.zmin = abs_zoom_space[0].XRange.Min
                self.zmax = abs_zoom_space[0].XRange.Max
            else:
                self.zmin = 0.0
                self.zmax = 1.0

            logger.info(
                f"PTZService initialized with IP: {ip}, Profile: {self.profile.Name}, "
                f"Pan/Tilt Range: ({self.xmin}, {self.xmax}), ({self.ymin}, {self.ymax}), "
                f"Zoom Range: ({self.zmin}, {self.zmax})"
            )

            # Manually construct the request as a dictionary, simplifying the Zoom structure.
            self.request = self.ptz.create_type("ContinuousMove")
            self.request.ProfileToken = self.profile.token

            # Create a velocity payload dictionary
            velocity_payload = {
                "PanTilt": {"x": 0.0, "y": 0.0},
                "Zoom": 0.0,  # Use a simple float for Zoom
            }

            # Assign velocity spaces if available
            if options and hasattr(options, "Spaces") and options.Spaces:
                pan_tilt_space = getattr(
                    options.Spaces, "ContinuousPanTiltVelocitySpace", None
                )
                if pan_tilt_space and pan_tilt_space[0]:
                    velocity_payload["PanTilt"]["space"] = pan_tilt_space[0].URI

                zoom_space = getattr(
                    options.Spaces, "ContinuousZoomVelocitySpace", None
                )
                if zoom_space and zoom_space[0]:
                    # The suds library might need the space attribute at this level
                    velocity_payload["Zoom"] = {"x": 0.0, "space": zoom_space[0].URI}

            self.request.Velocity = velocity_payload
            logger.info(
                f"Initialized ContinuousMove request with dictionary payload: {self.request}"
            )

            self.connected = True
        except Exception as e:
            logger.error(f"PTZService connection failed: {e}")
            self.connected = False
            self.request = None  # Set to None on failure

        self.zoom_level = 0.0

        # For smooth transitions (use settings value)
        self.last_pan = 0.0
        self.last_tilt = 0.0
        self.last_zoom = 0.0
        self.ramp_rate = self.settings.ptz.ptz_ramp_rate  # Max change per command

    def ramp(self, target: float, current: float) -> float:
        """Simple linear ramping for smooth transitions."""
        delta = target - current
        if abs(delta) > self.ramp_rate:
            return current + self.ramp_rate * (1 if delta > 0 else -1)
        return target

    def _octagon_move(self, pan: float, tilt: float) -> None:
        """Send Octagon API move command with direction and speeds.

        Maps signed pan/tilt velocities [-1, 1] to Octagon direction strings
        and per-axis speeds (0-100).
        """
        # Determine direction
        direction = None
        if pan > 0 and tilt == 0:
            direction = "right"
        elif pan < 0 and tilt == 0:
            direction = "left"
        elif tilt > 0 and pan == 0:
            direction = "up"
        elif tilt < 0 and pan == 0:
            direction = "down"
        elif pan > 0 and tilt > 0:
            direction = "upright"
        elif pan < 0 and tilt > 0:
            direction = "upleft"
        elif pan > 0 and tilt < 0:
            direction = "downright"
        elif pan < 0 and tilt < 0:
            direction = "downleft"

        if not direction:
            # No movement requested; issue stop
            url = f"http://{self.octagon_ip}/api/devices/{self.octagon_pantilt_id}?command=stop"
            requests.get(url, auth=(self.octagon_user, self.octagon_pass), timeout=2)
            return

        # Convert speeds to 0..100 percent
        pan_pct = max(0, min(100, round(abs(pan) * 100)))
        tilt_pct = max(0, min(100, round(abs(tilt) * 100)))

        url = (
            f"http://{self.octagon_ip}/api/devices/{self.octagon_pantilt_id}"
            f"?command=move&direction={direction}&panSpeed={pan_pct}&tiltSpeed={tilt_pct}"
        )
        requests.get(url, auth=(self.octagon_user, self.octagon_pass), timeout=2)

    def continuous_move(
        self, pan: float, tilt: float, zoom: float, threshold: float = 0.01
    ) -> None:
        """
        Move the camera continuously in pan, tilt, and zoom.

        Args:
            pan: Pan velocity, range [-1.0, 1.0]. Positive = right.
            tilt: Tilt velocity, range [-1.0, 1.0]. Positive = up.
            zoom: Zoom velocity. Positive = zoom in.
            threshold: Minimum change to send command (default 0.01).
        """
        if self.control_mode != "octagon" and (not self.connected or not self.request):
            return
        # Smooth transitions
        # Convert inputs to float before processing
        pan = float(pan)
        tilt = float(tilt)
        zoom = float(zoom)

        pan = round(self.ramp(pan, self.last_pan), 2)
        tilt = round(self.ramp(tilt, self.last_tilt), 2)
        # Clamp and round zoom to the valid range
        zoom = round(max(-self.zmax, min(self.zmax, zoom)), 2)

        # Only send if significant change
        if (
            abs(pan - self.last_pan) < threshold
            and abs(tilt - self.last_tilt) < threshold
            and abs(zoom - self.last_zoom) < threshold
        ):
            return

        # Octagon control: issue HTTP move and return
        if self.control_mode == "octagon":
            try:
                self._octagon_move(pan, tilt)
                self.active = pan != 0 or tilt != 0 or zoom != 0
                self.last_pan = pan
                self.last_tilt = tilt
                self.last_zoom = zoom
            except Exception as e:
                logger.error(f"Octagon move error: {e}")
            return

        self.request.Velocity["PanTilt"]["x"] = pan
        self.request.Velocity["PanTilt"]["y"] = tilt

        # Assign zoom value based on whether a space URI is present
        if (
            isinstance(self.request.Velocity["Zoom"], dict)
            and "space" in self.request.Velocity["Zoom"]
        ):
            self.request.Velocity["Zoom"]["x"] = zoom
        else:
            self.request.Velocity["Zoom"] = zoom

        try:
            # Log the request payload before sending
            logger.debug(f"Executing ContinuousMove with request: {self.request}")
            self.ptz.ContinuousMove(self.request)
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
        # Octagon control path: stop pantilt via API
        if getattr(self, "control_mode", "onvif") == "octagon":
            try:
                url = f"http://{self.octagon_ip}/api/devices/{self.octagon_pantilt_id}?command=stop"
                requests.get(
                    url, auth=(self.octagon_user, self.octagon_pass), timeout=2
                )
                self.active = False
                if pan:
                    self.last_pan = 0.0
                if tilt:
                    self.last_tilt = 0.0
                if zoom:
                    self.last_zoom = 0.0
            except Exception as e:
                logger.error(f"PTZ stop error (octagon): {e}")
            return

        # Only stop the axes that are requested
        try:
            stop_req = {"ProfileToken": self.profile.token}
            if not (pan and tilt and zoom):
                stop_req["PanTilt"] = pan or tilt
                stop_req["Zoom"] = zoom
            self.ptz.Stop(stop_req)
            self.active = False
            # Only reset the axes that are being stopped
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
            zoom_value: Zoom value to set (will be clamped to valid range).
        """
        # Clamp and move to absolute zoom
        try:
            zoom_value = max(self.zmin, min(self.zmax, float(zoom_value)))
            request = self.ptz.create_type("AbsoluteMove")
            request.ProfileToken = self.profile.token
            status = self.ptz.GetStatus({"ProfileToken": self.profile.token})
            if (
                status is not None
                and hasattr(status, "Position")
                and status.Position is not None
            ):
                request.Position = status.Position
            else:
                # Create a default Position object if status or Position is not available
                request.Position = self.ptz.create_type("PTZVector")
                request.Position.PanTilt = self.ptz.create_type("Vector2D")
                request.Position.PanTilt.x = 0.0
                request.Position.PanTilt.y = 0.0
                request.Position.Zoom = 0.0
            request.Position.Zoom = zoom_value
            self.ptz.AbsoluteMove(request)
            self.zoom_level = zoom_value
            self.last_zoom = zoom_value
        except Exception as e:
            logger.error(f"set_zoom_absolute error: {e}")

    def set_zoom_home(self) -> None:
        """Set zoom to the home (widest) position defined by self.zmin."""
        self.set_zoom_absolute(self.zmin)

    def set_home_position(self) -> None:
        """
        Move the camera to its home position using ONVIF GotoHomePosition or fallback methods.
        """
        # Octagon control path: use API home
        if getattr(self, "control_mode", "onvif") == "octagon":
            try:
                url = f"http://{self.octagon_ip}/api/devices/{self.octagon_pantilt_id}?command=home"
                requests.get(
                    url, auth=(self.octagon_user, self.octagon_pass), timeout=2
                )
                self.last_pan = 0.0
                self.last_tilt = 0.0
                self.last_zoom = self.zmin
                self.zoom_level = self.zmin
                logger.info("set_home_position: Using Octagon API home command")
            except Exception as e:
                logger.error(f"Octagon home error: {e}")
            return

        try:
            # First attempt: Use ONVIF standard GotoHomePosition command
            request = self.ptz.create_type("GotoHomePosition")
            request.ProfileToken = self.profile.token

            # Optional: Set speed for the movement
            try:
                request.Speed = self.ptz.create_type("PTZSpeed")
                request.Speed.PanTilt = self.ptz.create_type("Vector2D")
                request.Speed.PanTilt.x = 0.5  # Medium speed
                request.Speed.PanTilt.y = 0.5
                request.Speed.Zoom = 0.5
            except Exception:
                # Speed setting is optional, continue without it
                logger.debug("Speed setting not supported, continuing without it")

            self.ptz.GotoHomePosition(request)

            # Update internal state
            self.last_pan = 0.0
            self.last_tilt = 0.0
            self.last_zoom = self.zmin
            self.zoom_level = self.zmin

            logger.info("set_home_position: Using ONVIF GotoHomePosition command")

        except Exception as e:
            logger.error(f"GotoHomePosition failed: {e}")
            # Fallback: Use AbsoluteMove with explicit coordinates
            try:
                logger.info("Attempting AbsoluteMove fallback...")
                request = self.ptz.create_type("AbsoluteMove")
                request.ProfileToken = self.profile.token

                # Get current position and modify it
                current_status = self.ptz.GetStatus(
                    {"ProfileToken": self.profile.token}
                )
                if (
                    current_status is not None
                    and hasattr(current_status, "Position")
                    and current_status.Position is not None
                ):
                    request.Position = current_status.Position
                else:
                    # Create a default Position object if status or Position is not available
                    request.Position = self.ptz.create_type("PTZVector")
                    request.Position.PanTilt = self.ptz.create_type("Vector2D")
                    request.Position.PanTilt.x = 0.0
                    request.Position.PanTilt.y = 0.0
                    request.Position.Zoom = 0.0

                # Set pan/tilt to home (0,0)
                request.Position.PanTilt.x = 0.0
                request.Position.PanTilt.y = 0.0
                request.Position.Zoom = self.zmin

                self.ptz.AbsoluteMove(request)

                # Update internal state
                self.last_pan = 0.0
                self.last_tilt = 0.0
                self.last_zoom = self.zmin
                self.zoom_level = self.zmin

                logger.info("AbsoluteMove fallback completed")

            except Exception as abs_e:
                logger.error(f"AbsoluteMove fallback failed: {abs_e}")
                # Final fallback: Use continuous movement to stop and zoom home
                try:
                    logger.info("Attempting final fallback with continuous movement...")
                    self.continuous_move(0.0, 0.0, 0.0)  # Stop any current movement
                    self.set_zoom_home()  # Set zoom separately
                    logger.info("Final fallback completed")
                except Exception as fallback_e:
                    logger.error(f"All fallback methods failed: {fallback_e}")

    def set_zoom_relative(self, zoom_delta: float) -> None:
        """
        Set zoom relatively from current position.

        Args:
            zoom_delta: Amount to change zoom by.
        """
        # Relative zoom move
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
            Current zoom value, or zmin if unavailable.
        """
        try:
            status = self.ptz.GetStatus({"ProfileToken": self.profile.token})
            if (
                status is not None
                and hasattr(status, "Position")
                and status.Position is not None
            ):
                zoom_obj = getattr(status.Position, "Zoom", None)
                if zoom_obj is not None:
                    if hasattr(zoom_obj, "x"):
                        return float(zoom_obj.x)
                    return float(zoom_obj)
        except Exception:
            pass
        return self.zmin

    def get_position_from_octagon(self) -> tuple[float, float, float] | None:
        """
        Get current pan, tilt, and zoom position from Octagon API.

        This retrieves the actual camera position from the device via HTTP REST API
        instead of ONVIF status, providing more reliable position feedback.

        Returns:
            Tuple of (pan, tilt, zoom) in degrees/units, or None if unavailable.
        """
        try:
            url = f"http://{self.octagon_ip}/api/devices/{self.octagon_pantilt_id}/position"
            response = requests.get(
                url, auth=(self.octagon_user, self.octagon_pass), timeout=2
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "data" in data:
                    pos = data["data"]
                    pan = float(pos.get("panPosition", 0.0))
                    tilt = float(pos.get("tiltPosition", 0.0))
                    # Zoom is read separately if needed
                    zoom = float(pos.get("zoom", self.zoom_level))

                    logger.debug(
                        f"Octagon position: pan={pan:.3f}, tilt={tilt:.3f}, zoom={zoom:.3f}"
                    )
                    return (pan, tilt, zoom)
            else:
                logger.debug(
                    f"Octagon API position request failed with status {response.status_code}"
                )
        except requests.exceptions.RequestException as e:
            logger.debug(f"Octagon API position request error: {e}")
        except Exception as e:
            logger.debug(f"Error parsing Octagon position response: {e}")

        return None

    def get_visible_position_from_octagon(self) -> dict | None:
        """
        Get current visible lens position (e.g., zoom/focus) from Octagon API.

        Returns:
            Dict with keys like 'zoomPosition', 'focusPosition', etc., or None if unavailable.
        """
        try:
            url = f"http://{self.octagon_ip}/api/devices/{self.octagon_visible_id}/position"
            response = requests.get(
                url, auth=(self.octagon_user, self.octagon_pass), timeout=2
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "data" in data:
                    return data["data"]
            else:
                logger.debug(
                    f"Octagon API visible position request failed with status {response.status_code}"
                )
        except requests.exceptions.RequestException as e:
            logger.debug(f"Octagon API visible position request error: {e}")
        except Exception as e:
            logger.debug(f"Error parsing Octagon visible position response: {e}")
        return None

    def update_position_from_octagon(self) -> bool:
        """
        Update internal position tracking from Octagon API.

        This should be called periodically to sync the internal position state
        with the actual camera position from the Octagon API.

        Returns:
            True if position was successfully updated, False otherwise.
        """
        updated = False
        # Update pan/tilt
        pos = self.get_position_from_octagon()
        if pos:
            pan, tilt, _ = pos
            self.last_pan = pan
            self.last_tilt = tilt
            updated = True
        # Update zoom from visible lens position
        vis = self.get_visible_position_from_octagon()
        if vis:
            zoom_val = vis.get("zoomPosition") or vis.get("zoom")
            if zoom_val is not None:
                try:
                    zoom_f = float(zoom_val)
                    self.last_zoom = zoom_f
                    self.zoom_level = zoom_f
                    updated = True
                except Exception:
                    pass
        return updated
