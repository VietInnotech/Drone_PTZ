from typing import Any

from loguru import logger

from src.config import Config


def get_cv2():
    """Lazy import for cv2 to avoid heavy dependencies during testing."""
    import cv2  # noqa: PLC0415 - Intentional lazy import for testing

    return cv2


def get_torch():
    """Lazy import for torch to avoid heavy dependencies during testing."""
    import torch  # noqa: PLC0415 - Intentional lazy import for testing

    return torch


def get_yolo():
    """Lazy import for YOLO to avoid heavy dependencies during testing."""
    from ultralytics import YOLO  # noqa: PLC0415 - Intentional lazy import for testing

    return YOLO


class DetectionService:
    """
    Service for running YOLO-based object detection.
    """

    def __init__(self, config: Any | None = None):
        """
        Initialize the detection service with a given configuration.
        """
        self.config = config or Config
        # Use lazy import for YOLO model
        yolo_class = get_yolo()
        self.model = yolo_class(self.config.MODEL_PATH)
        self.class_names = self.model.names

    def detect(self, frame: Any) -> Any:
        """
        Run detection on a single frame.

        Args:
            frame: Input frame to detect objects in.

        Returns:
            Boxes object from YOLO results, or empty list if detection fails.
        """
        try:
            if frame is None or frame.size == 0:
                logger.warning("Invalid frame provided to detect()")
                return []

            # Use lazy import for torch context manager
            torch = get_torch()
            with torch.no_grad():
                results = self.model.track(
                    frame,
                    persist=True,
                    tracker="botsort.yaml",
                    conf=self.config.CONFIDENCE_THRESHOLD,
                    verbose=False,
                )[0]
        except Exception as e:
            logger.error(f"Detection failed: {e}")
            return []
        else:
            return results.boxes if results.boxes is not None else []

    def get_class_names(self) -> dict[int, str]:
        """
        Get the dict of class names from the model.
        """
        return self.class_names
