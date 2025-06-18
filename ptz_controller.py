import sys
import os

# Ensure project root is on sys.path for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from onvif import ONVIFCamera
from config import Config, logger

class PTZService:
    @logger.catch
    def __init__(self, ip=None, port=80, user=None, password=None):
        self.connected = False
        self.active = False
        try:
            ip = ip or Config.CAMERA_IP
            user = user or Config.CAMERA_USER
            password = password or Config.CAMERA_PASS
            self.cam = ONVIFCamera(ip, port, user, password)
            self.media = self.cam.create_media_service()
            self.ptz = self.cam.create_ptz_service()
            profiles = self.media.GetProfiles()
            if not profiles:
                raise Exception("No media profiles found on camera.")
            self.profile = profiles[0]
            logger.info(f"Selected profile: {self.profile}")
            logger.info(f"Profile token: {self.profile.token}")
            logger.info(f"Type of profile token: {type(self.profile.token)}")
            options = self.ptz.GetConfigurationOptions({
                "ConfigurationToken": self.profile.PTZConfiguration.token
            })

            if options and hasattr(options, 'Spaces') and options.Spaces and hasattr(options.Spaces, 'ContinuousPanTiltVelocitySpace'):
                self.xmax = options.Spaces.ContinuousPanTiltVelocitySpace[0].XRange.Max
                self.xmin = options.Spaces.ContinuousPanTiltVelocitySpace[0].XRange.Min
                self.ymax = options.Spaces.ContinuousPanTiltVelocitySpace[0].YRange.Max
                self.ymin = options.Spaces.ContinuousPanTiltVelocitySpace[0].YRange.Min
            else:
                self.xmax = 1.0
                self.xmin = -1.0
                self.ymax = 1.0
                self.ymin = -1.0
            abs_zoom_space = getattr(options.Spaces, "AbsoluteZoomPositionSpace", None) if options and hasattr(options, 'Spaces') and options.Spaces else None
            if abs_zoom_space and len(abs_zoom_space) > 0:
                self.zmin = abs_zoom_space[0].XRange.Min
                self.zmax = abs_zoom_space[0].XRange.Max
            else:
                self.zmin = 0.0
                self.zmax = 1.0
            
            logger.info(f"PTZService initialized with IP: {ip}, Profile: {self.profile.Name}, "
                        f"Pan/Tilt Range: ({self.xmin}, {self.xmax}), ({self.ymin}, {self.ymax}), "
                        f"Zoom Range: ({self.zmin}, {self.zmax})")

            # Manually construct the request as a dictionary, simplifying the Zoom structure.
            self.request = self.ptz.create_type('ContinuousMove')
            self.request.ProfileToken = self.profile.token
            
            # Create a velocity payload dictionary
            velocity_payload = {
                'PanTilt': {'x': 0.0, 'y': 0.0},
                'Zoom': 0.0  # Use a simple float for Zoom
            }

            # Assign velocity spaces if available
            if options and hasattr(options, 'Spaces') and options.Spaces:
                pan_tilt_space = getattr(options.Spaces, 'ContinuousPanTiltVelocitySpace', None)
                if pan_tilt_space and pan_tilt_space[0]:
                    velocity_payload['PanTilt']['space'] = pan_tilt_space[0].URI

                zoom_space = getattr(options.Spaces, 'ContinuousZoomVelocitySpace', None)
                if zoom_space and zoom_space[0]:
                    # The suds library might need the space attribute at this level
                    velocity_payload['Zoom'] = {'x': 0.0, 'space': zoom_space[0].URI}

            self.request.Velocity = velocity_payload
            logger.info(f"Initialized ContinuousMove request with dictionary payload: {self.request}")
            
            self.connected = True
        except Exception as e:
            logger.error(f"PTZService connection failed: {e}")
            self.connected = False
            self.request = None # Set to None on failure

        self.zoom_level = 0.0

        # For smooth transitions
        self.last_pan = 0.0
        self.last_tilt = 0.0
        self.last_zoom = 0.0
        self.ramp_rate = 0.2  # Max change per command (tune as needed)

    def ramp(self, target, current):
        # Simple linear ramping
        delta = target - current
        if abs(delta) > self.ramp_rate:
            return current + self.ramp_rate * (1 if delta > 0 else -1)
        return target

    def continuous_move(self, pan, tilt, zoom, threshold=0.01):
        if not self.connected or not self.request:
            return
        # Smooth transitions
        # Convert inputs to float before processing
        pan = float(pan)
        tilt = float(tilt)
        zoom = float(zoom)

        pan = round(self.ramp(pan, self.last_pan), 1)
        tilt = round(self.ramp(tilt, self.last_tilt), 1)
        # Clamp and round zoom to the valid range
        zoom = round(max(self.zmin, min(self.zmax, zoom)), 1)

        # Only send if significant change
        if (
            abs(pan - self.last_pan) < threshold
            and abs(tilt - self.last_tilt) < threshold
            and abs(zoom - self.last_zoom) < threshold
        ):
            return

        self.request.Velocity['PanTilt']['x'] = pan
        self.request.Velocity['PanTilt']['y'] = tilt
        
        # Assign zoom value based on whether a space URI is present
        if isinstance(self.request.Velocity['Zoom'], dict) and 'space' in self.request.Velocity['Zoom']:
            self.request.Velocity['Zoom']['x'] = zoom
        else:
            self.request.Velocity['Zoom'] = zoom

        try:
            # Log the request payload before sending
            logger.debug(f"Executing ContinuousMove with request: {self.request}")
            self.ptz.ContinuousMove(self.request)
            self.active = (pan != 0 or tilt != 0 or zoom != 0)
            self.last_pan = pan
            self.last_tilt = tilt
            self.last_zoom = zoom
        except Exception as e:
            logger.error(f"PTZ continuous_move error: {e}", exc_info=True)

    def stop(self, pan=True, tilt=True, zoom=True):
        # Only stop the axes that are requested
        try:
            stop_req = {"ProfileToken": self.profile.token}
            if not (pan and tilt and zoom):
                stop_req["PanTilt"] = pan or tilt
                stop_req["Zoom"] = zoom
            self.ptz.Stop(stop_req)
            self.active = False
            self.last_pan = 0.0
            self.last_tilt = 0.0
            self.last_zoom = 0.0
        except Exception as e:
            logger.error(f"PTZ stop error: {e}")

    def set_zoom_absolute(self, zoom_value):
        # Clamp and move to absolute zoom
        try:
            zoom_value = max(self.zmin, min(self.zmax, float(zoom_value)))
            request = self.ptz.create_type("AbsoluteMove")
            request.ProfileToken = self.profile.token
            status = self.ptz.GetStatus({"ProfileToken": self.profile.token})
            if status is not None and hasattr(status, "Position") and status.Position is not None:
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
    def set_zoom_home(self):
        """Set zoom to the home (widest) position defined by self.zmin."""
        self.set_zoom_absolute(self.zmin)

    def set_home_position(self):
        """
        Move the camera to its home position using ONVIF GotoHomePosition or fallback methods.
        """
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
            except:
                # Speed setting is optional, continue without it
                pass
            
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
                current_status = self.ptz.GetStatus({"ProfileToken": self.profile.token})
                if current_status is not None and hasattr(current_status, "Position") and current_status.Position is not None:
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

    def set_zoom_relative(self, zoom_delta):
        # Relative zoom move
        try:
            current_zoom = self.get_zoom()
            new_zoom = max(self.zmin, min(self.zmax, current_zoom + zoom_delta))
            self.set_zoom_absolute(new_zoom)
        except Exception as e:
            logger.error(f"set_zoom_relative error: {e}")

    def get_zoom(self):
        try:
            status = self.ptz.GetStatus({"ProfileToken": self.profile.token})
            if status is not None and hasattr(status, "Position") and status.Position is not None:
                zoom_obj = getattr(status.Position, 'Zoom', None)
                if zoom_obj is not None:
                    if hasattr(zoom_obj, 'x'):
                        return float(zoom_obj.x)
                    return float(zoom_obj)
            return self.zmin
        except Exception:
            return self.zmin

