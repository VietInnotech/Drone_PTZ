import sys
import os

# Ensure project root is on sys.path for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import cv2
import torch
from ultralytics import YOLO
from config import Config, setup_logging
from loguru import logger
from typing import Any, Callable, Generator, List, Optional, Tuple


class DetectionService:
    """
    Service for running YOLO-based object detection.
    """

    def __init__(self, config: Optional[Any] = None):
        """
        Initialize the detection service with a given configuration.
        """
        self.config = config or Config
        self.model = YOLO(self.config.MODEL_PATH)
        self.model.to(
            "cuda" if torch.cuda.is_available() else "cpu"  # Use GPU if available
        )
        self.class_names = self.model.names

    def detect(self, frame: Any) -> Any:
        """
        Run detection on a single frame.
        """
        with torch.no_grad():
            results = self.model.track(
                frame,
                persist=True,
                tracker="botsort.yaml",
                conf=self.config.CONFIDENCE_THRESHOLD,
                verbose=False,
            )[0]
        return results.boxes

    def get_class_names(self) -> List[str]:
        """
        Get the list of class names from the model.
        """
        return self.class_names


def tracker(
    video_source: Optional[Any] = None,
    config: Optional[Any] = None,
    callback: Optional[Callable[[Any, Any, int], None]] = None,
    display: bool = False,
    max_frames: Optional[int] = None,
    frame_skip: int = 0,
) -> Generator[Tuple[int, Any, Any, List[str]], None, None]:
    """
    Generator for YOLO-based multi-object tracking.
    Yields: (frame_index, frame, tracked_boxes, labels)
    """
    cfg = config or Config
    detection_service = DetectionService(cfg)
    class_names = detection_service.get_class_names()

    if video_source is None:
        video_source = cfg.CAMERA_INDEX
    cap = cv2.VideoCapture(video_source, cv2.CAP_ANY)
    cap.set(cv2.CAP_PROP_FPS, cfg.FPS)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cfg.RESOLUTION_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.RESOLUTION_HEIGHT)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))

    if not cap.isOpened():
        logger.error("Camera or video source not found.")
        raise RuntimeError("Camera or video source not found.")

    frame_index = 0
    last_detections = []
    last_labels = []

    while True:
        # Skip frames at the capture stage to reduce decoding overhead
        if frame_skip and frame_skip > 0:
            for _ in range(frame_skip):
                grabbed = cap.grab()
                frame_index += 1
                if not grabbed:
                    break

        ret, frame = cap.read()
        if not ret:
            break

        tracked_boxes = detection_service.detect(frame)
        last_detections = tracked_boxes
        last_labels = []
        for i, det in enumerate(tracked_boxes):
            cls_id = int(det.cls)
            conf = float(det.conf)
            track_id = (
                int(det.id) if hasattr(det, "id") and det.id is not None else None
            )
            label = f"{class_names[cls_id]} {conf:.2f}"
            if track_id is not None:
                label += f" ID:{track_id}"
            last_labels.append(label)
        if callback:
            callback(frame, tracked_boxes, frame_index)

        yield (frame_index, frame, last_detections, last_labels)

        frame_index += 1
        if max_frames is not None and frame_index >= max_frames:
            break

    cap.release()
    if display:
        cv2.destroyAllWindows()
