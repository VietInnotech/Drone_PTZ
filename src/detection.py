from typing import Any

from loguru import logger

from src.settings import Settings


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

    def __init__(self, settings: Settings | None = None):
        """
        Initialize the detection service with Settings configuration.

        Args:
            settings: Settings object containing detection configuration.
                     If None, defaults are loaded.
        """
        if settings is None:
            from src.settings import load_settings  # noqa: PLC0415 - Lazy import

            settings = load_settings()

        self.settings = settings

        # Use lazy import for YOLO model
        yolo_class = get_yolo()

        # Get model path from Settings
        model_path = self.settings.detection.model_path

        # Log Ultralytics version and model path to validate runtime configuration
        try:
            import ultralytics  # noqa: PLC0415

            logger.info(
                "Initializing DetectionService with Ultralytics %s, model_path=%s, tracker_type=%s",
                getattr(ultralytics, "__version__", "unknown"),
                model_path,
                self.settings.tracking.tracker_type,
            )
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning(
                "Ultralytics not importable while initializing DetectionService: %s",
                exc,
            )

        self.model = yolo_class(model_path)
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

            # Get confidence threshold from Settings
            conf_threshold = self.settings.detection.confidence_threshold

            # Use lazy import for torch context manager
            torch = get_torch()
            tracker_yaml = f"config/trackers/{self.settings.tracking.tracker_type}.yaml"

            # Log the exact arguments we pass into YOLO.track() for validation
            logger.debug(
                "Calling YOLO.track with source=frame, persist=True, tracker=%s, conf=%s, verbose=False",
                tracker_yaml,
                conf_threshold,
            )

            with torch.no_grad():
                results = self.model.track(
                    source=frame,
                    persist=True,
                    tracker=tracker_yaml,
                    conf=conf_threshold,
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
        Returns a copy to prevent external mutation.
        """
        return dict(self.class_names)
