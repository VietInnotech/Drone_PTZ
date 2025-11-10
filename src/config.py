import contextlib
import typing
from pathlib import Path

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
    CAMERA_INDEX: int = 4  # Camera device index (e.g., 0 for default webcam)
    RESOLUTION_WIDTH: int = 1280  # Frame width in pixels
    RESOLUTION_HEIGHT: int = 720  # Frame height in pixels
    FPS: int = 30  # Desired frames per second

    # Detection Settings
    CONFIDENCE_THRESHOLD: float = 0.5  # YOLO detection confidence threshold
    MODEL_PATH: str = "assets/models/yolo/best5.pt"  # Path to YOLO model

    # PTZ Control Settings
    PTZ_MOVEMENT_GAIN: float = (
        2.0  # Gain for pan/tilt control (tuned for smoother movement)
    )
    PTZ_MOVEMENT_THRESHOLD: float = (
        0.05  # Minimum normalized error to trigger pan/tilt (increased for stability)
    )
    ZOOM_TARGET_COVERAGE: float = 0.3  # Target object coverage (fraction of frame)
    ZOOM_RESET_TIMEOUT: float = (
        2.0  # Timeout (seconds) after which zoom resets if no object detected
    )
    ZOOM_MIN_INTERVAL: float = 0.1  # Reduced for faster zoom response

    # Continuous Zoom Control
    ZOOM_VELOCITY_GAIN: float = 2.0  # Proportional gain for continuous zoom velocity
    ZOOM_RESET_VELOCITY: float = 0.5  # Velocity for zoom reset to home position

    # Performance Tuning
    FPS_WINDOW_SIZE: int = 30  # Number of frames for FPS calculation
    ZOOM_DEAD_ZONE: float = (
        0.03  # Minimum coverage difference to trigger zoom adjustment
    )
    PTZ_RAMP_RATE: float = (
        0.2  # Maximum speed change per PTZ command (for smooth transitions)
    )
    FRAME_QUEUE_MAXSIZE: int = 1  # Maximum frames to queue (1 = always latest frame)

    # ONVIF Camera Credentials
    CAMERA_CREDENTIALS: typing.ClassVar[dict[str, str]] = {
        "ip": "192.168.1.70",
        "user": "admin",
        "pass": "admin@123",
    }

    # Home timeout for no detection (seconds)
    NO_DETECTION_HOME_TIMEOUT: int = 5

    @classmethod
    def validate(cls):
        """
        Validate configuration values to ensure they are within acceptable ranges.

        Raises:
            ValueError: If any configuration value is invalid.
        """
        errors = []

        # Validate confidence threshold
        if not (0.0 <= cls.CONFIDENCE_THRESHOLD <= 1.0):
            errors.append(
                f"CONFIDENCE_THRESHOLD must be between 0.0 and 1.0, got {cls.CONFIDENCE_THRESHOLD}"
            )

        # Validate resolution
        if cls.RESOLUTION_WIDTH <= 0 or cls.RESOLUTION_HEIGHT <= 0:
            errors.append(
                f"Resolution must be positive integers, got {cls.RESOLUTION_WIDTH}x{cls.RESOLUTION_HEIGHT}"
            )

        # Validate FPS
        if cls.FPS <= 0:
            errors.append(f"FPS must be positive, got {cls.FPS}")

        # Validate model file exists
        model_path = Path(cls.MODEL_PATH)
        if not model_path.exists():
            errors.append(f"Model file not found: {cls.MODEL_PATH}")

        # Validate PTZ settings
        if cls.PTZ_MOVEMENT_GAIN < 0:
            errors.append(
                f"PTZ_MOVEMENT_GAIN must be positive, got {cls.PTZ_MOVEMENT_GAIN}"
            )

        if not (0.0 <= cls.PTZ_MOVEMENT_THRESHOLD <= 1.0):
            errors.append(
                f"PTZ_MOVEMENT_THRESHOLD must be between 0.0 and 1.0, got {cls.PTZ_MOVEMENT_THRESHOLD}"
            )

        # Validate zoom settings
        if not (0.0 <= cls.ZOOM_TARGET_COVERAGE <= 1.0):
            errors.append(
                f"ZOOM_TARGET_COVERAGE must be between 0.0 and 1.0, got {cls.ZOOM_TARGET_COVERAGE}"
            )

        if cls.ZOOM_RESET_TIMEOUT < 0:
            errors.append(
                f"ZOOM_RESET_TIMEOUT must be non-negative, got {cls.ZOOM_RESET_TIMEOUT}"
            )

        if cls.ZOOM_MIN_INTERVAL < 0:
            errors.append(
                f"ZOOM_MIN_INTERVAL must be non-negative, got {cls.ZOOM_MIN_INTERVAL}"
            )

        # Validate camera credentials
        if not cls.CAMERA_CREDENTIALS.get("ip"):
            errors.append("CAMERA_CREDENTIALS must include 'ip'")

        if not cls.CAMERA_CREDENTIALS.get("user"):
            errors.append("CAMERA_CREDENTIALS must include 'user'")

        if not cls.CAMERA_CREDENTIALS.get("pass"):
            errors.append("CAMERA_CREDENTIALS must include 'pass'")

        # Validate performance settings
        if cls.FPS_WINDOW_SIZE <= 0:
            errors.append(
                f"FPS_WINDOW_SIZE must be positive, got {cls.FPS_WINDOW_SIZE}"
            )

        if cls.PTZ_RAMP_RATE <= 0:
            errors.append(f"PTZ_RAMP_RATE must be positive, got {cls.PTZ_RAMP_RATE}")

        # If there are errors, raise ValueError with all error messages
        if errors:
            error_msg = "Configuration validation failed:\n  - " + "\n  - ".join(errors)
            raise ValueError(error_msg)

        logger.info("✓ Configuration validated successfully")


def setup_logging():
    """Configure the logger based on Config settings."""
    logger.remove()

    # If resetting, truncate the file before adding the handler
    log_path = Path(Config.LOG_FILE)
    if Config.reset_log_on_start and log_path.exists():
        with contextlib.suppress(Exception):
            log_path.write_text("")

    if Config.write_log_file:
        with contextlib.suppress(Exception):
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


# Initial setup for the application
setup_logging()

# Public API exports
__all__ = ["Config", "logger", "setup_logging"]
