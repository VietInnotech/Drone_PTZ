from loguru import logger

class Config:
    """
    Centralized configuration for all services, including logging.
    """

    # Logging Settings
    LOG_FILE: str = "logs/app.log"
    """Path to the log file."""

    LOG_LEVEL: str = "DEBUG"
    """Logging level (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')."""

    LOG_FORMAT: str = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    """Format string for log messages."""

    LOG_ROTATION: str = "5 MB"
    """Log rotation policy (e.g., '10 MB', '1 week')."""

    LOG_RETENTION: str = "30 days"
    """How long to retain old log files."""

    LOG_ENQUEUE: bool = True
    """Whether to use multiprocessing-safe log handling."""

    LOG_BACKTRACE: bool = True
    """Enable backtrace in loguru for better error context."""

    LOG_DIAGNOSE: bool = True
    """Enable loguru's diagnose feature for detailed exception info."""

    # Logging Control Options
    write_log_file: bool = True
    """If True, write logs to app.log file."""
    reset_log_on_start: bool = True
    """If True, truncate app.log at program start."""

    # Camera Settings
    CAMERA_INDEX: int = 0  # Camera device index (e.g., 0 for default webcam)
    RESOLUTION_WIDTH: int = 1280  # Frame width in pixels
    RESOLUTION_HEIGHT: int = 720  # Frame height in pixels
    FPS: int = 30  # Desired frames per second

    # Detection Settings
    CONFIDENCE_THRESHOLD: float = 0.5  # YOLO detection confidence threshold
    MODEL_PATH: str = "models/best5.pt"  # Path to YOLO model

    # PTZ Control Settings
    PTZ_PAN_GAIN: float = 2.0  # Gain for pan control (tuned for smoother movement)
    PTZ_TILT_GAIN: float = 2.0  # Gain for tilt control (tuned for smoother movement)
    PTZ_PAN_THRESHOLD: float = 0.05  # Minimum normalized error to trigger pan (increased for stability)
    PTZ_TILT_THRESHOLD: float = 0.05  # Minimum normalized error to trigger tilt (increased for stability)
    ZOOM_TARGET_COVERAGE: float = 0.3  # Target object coverage (fraction of frame)
    ZOOM_RATE_LIMIT: float = 0.5  # Max zoom change per command (reduced for finer control)
    ZOOM_RESET_TIMEOUT: float = 2.0  # Timeout (seconds) after which zoom resets if no object detected
    ZOOM_MIN_INTERVAL: float = 0.1  # Reduced for faster zoom response

    # Continuous Zoom Control
    ZOOM_VELOCITY_GAIN: float = 1.0  # Proportional gain for continuous zoom velocity
    ZOOM_RESET_VELOCITY: float = 0.5  # Velocity for zoom reset to home position

    # PID Controller Gains for Zoom (Tuned for stability)
    ZOOM_PID_KP: float = 0.2  # Reduced proportional gain to prevent overshooting
    ZOOM_PID_KI: float = 0.001 # Reduced integral gain to minimize lag
    ZOOM_PID_KD: float = 0.02 # Reduced derivative gain for smoother response

    # ONVIF Camera Settings
    CAMERA_IP: str = "192.168.1.70"  # Camera IP address
    CAMERA_USER: str = "admin"        # Camera username
    CAMERA_PASS: str = "admin@123"     # Camera password
    PTZ_SERVICE = None           # Optional: PTZ service path or identifier

    # Home timeout for no detection (seconds)
    NO_DETECTION_HOME_TIMEOUT: int = 5

import os
import sys

def setup_logging():
    """Configure the logger based on Config settings."""
    logger.remove()

    # If resetting, truncate the file before adding the handler
    if Config.reset_log_on_start and os.path.exists(Config.LOG_FILE):
        try:
            with open(Config.LOG_FILE, "w"):
                pass
        except Exception as e:
            # Use a print statement for critical config errors
            print(f"Error truncating log file: {e}", file=sys.stderr)

    if Config.write_log_file:
        try:
            logger.add(
                Config.LOG_FILE,
                rotation=Config.LOG_ROTATION,
                retention=Config.LOG_RETENTION,
                level=Config.LOG_LEVEL,
                format=Config.LOG_FORMAT,
                enqueue=Config.LOG_ENQUEUE,
                backtrace=Config.LOG_BACKTRACE,
                diagnose=Config.LOG_DIAGNOSE,
            )
        except Exception as e:
            print(f"Error setting up file logger: {e}", file=sys.stderr)

# Initial setup for the application
setup_logging()