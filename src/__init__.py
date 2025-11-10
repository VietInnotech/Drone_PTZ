"""
Drone PTZ - Pan-Tilt-Zoom tracking system for drone detection.

This package provides computer vision-based drone tracking with PTZ camera control.
"""

__version__ = "1.0.0"
__author__ = "Drone PTZ Team"

# Public API exports
from loguru import logger

from src.config import Config, setup_logging
from src.detection import DetectionService
from src.ptz_controller import PTZService

__all__ = [
    "Config",
    "DetectionService",
    "PTZService",
    "logger",
    "setup_logging",
]
