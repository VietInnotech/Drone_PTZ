from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from loguru import logger

from src.detection import DetectionService
from src.thermal_detection import ThermalDetectionService
from src.settings import Settings, CameraSourceConfig
from src.webrtc_client import start_webrtc_client
import cv2


class DetectionMode(StrEnum):
    VISIBLE = "visible"
    THERMAL = "thermal"
    SECONDARY = "secondary"


@dataclass
class DetectionResult:
    """Detection with source tracking."""
    mode: DetectionMode
    boxes: list[Any]  # YOLO boxes or ThermalTargets
    frame: Any
    frame_shape: tuple[int, int]
    timestamp: float


def _frame_grabber(
    frame_queue: queue.Queue[Any],
    stop_event: threading.Event,
    camera_config: CameraSourceConfig,
    debug_name: str = "Camera",
) -> None:
    """Continuously grab frames for a specific camera configuration."""
    source = camera_config.source
    
    if source == "skyshield":
        # Derived WebRTC URL for SkyShield cameras
        # In a real impl, we'd use skyshield_client to get the base URL if not in settings
        # For now we use the derivation logic from the plan
        # Note: We'll need to pass the full URL here or derive it
        # Assuming URL is handled by the caller or passed in camera_config for runtime
        pass 

    rtsp_url = camera_config.rtsp_url
    camera_index = camera_config.camera_index
    fps_setting = camera_config.fps
    resolution_width = camera_config.resolution_width
    resolution_height = camera_config.resolution_height

    if rtsp_url:
        cap = cv2.VideoCapture(rtsp_url)
    else:
        cap = cv2.VideoCapture(camera_index, cv2.CAP_ANY)
        cap.set(cv2.CAP_PROP_FPS, fps_setting)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution_height)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc(*"MJPG"))

    if not cap.isOpened():
        logger.error(f"{debug_name}: Failed to open video source (index={camera_index} rtsp={rtsp_url})")
        return

    logger.info(f"{debug_name}: Started frame grabber")
    
    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            logger.warning(f"{debug_name}: Failed to read frame, retrying...")
            time.sleep(0.1)
            continue

        if not frame_queue.empty():
            try:
                frame_queue.get_nowait()
            except queue.Empty:
                pass
        try:
            frame_queue.put_nowait(frame)
        except queue.Full:
            pass

    cap.release()
    logger.info(f"{debug_name}: Stopped frame grabber")


class DetectionManager:
    """Manages concurrent visible and thermal detection pipelines."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._visible_service: DetectionService | None = None
        self._thermal_service: ThermalDetectionService | None = None
        self._secondary_service: DetectionService | None = None
        
        self._visible_frame_queue = queue.Queue(maxsize=1)
        self._thermal_frame_queue = queue.Queue(maxsize=1)
        self._secondary_frame_queue = queue.Queue(maxsize=1)
        
        self._visible_input_thread: threading.Thread | None = None
        self._thermal_input_thread: threading.Thread | None = None
        self._secondary_input_thread: threading.Thread | None = None
        self._visible_webrtc_stop: threading.Event | None = None
        self._thermal_webrtc_stop: threading.Event | None = None
        self._secondary_webrtc_stop: threading.Event | None = None
        
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def _get_skyshield_webrtc_url(self, camera_id: int) -> str:
        base = self.settings.skyshield.mediamtx_webrtc_base
        return f"{base}/camera_{camera_id}/"

    def _start_source(
        self, 
        config: CameraSourceConfig, 
        frame_queue: queue.Queue, 
        debug_name: str
    ) -> tuple[threading.Thread | None, threading.Event | None]:
        if config.source == "webrtc" or (config.source == "skyshield" and config.skyshield_camera_id is not None):
            url = config.webrtc_url
            if config.source == "skyshield":
                url = self._get_skyshield_webrtc_url(config.skyshield_camera_id)
            
            stop_event = threading.Event()
            thread = start_webrtc_client(
                frame_queue,
                stop_event,
                url=url,
                width=config.resolution_width,
                height=config.resolution_height,
                fps=config.fps,
            )
            return thread, stop_event
        else:
            thread = threading.Thread(
                target=_frame_grabber,
                args=(frame_queue, self._stop_event, config, debug_name),
                daemon=True,
            )
            thread.start()
            return thread, None

    def start(self) -> None:
        """Start enabled detection services and their camera inputs."""
        logger.info(f"DetectionManager starting with thermal method: {self.settings.thermal_detection.detection_method}")
        with self._lock:
            self._stop_event.clear()
            
            # Start Visible Detection
            if self.settings.visible_detection.enabled:
                logger.info("Starting VISIBLE detection pipeline")
                self._visible_service = DetectionService(settings=self.settings)
                self._visible_input_thread, self._visible_webrtc_stop = self._start_source(
                    self.settings.visible_detection.camera,
                    self._visible_frame_queue,
                    "Visible Camera"
                )
            else:
                logger.info("VISIBLE detection pipeline is DISABLED")
                
            # Start Thermal Detection
            if self.settings.thermal_detection.enabled:
                logger.info("Starting THERMAL detection pipeline")
                self._thermal_service = ThermalDetectionService(settings=self.settings)
                self._thermal_input_thread, self._thermal_webrtc_stop = self._start_source(
                    self.settings.thermal_detection.camera,
                    self._thermal_frame_queue,
                    "Thermal Camera"
                )
            else:
                logger.info("THERMAL detection pipeline is DISABLED")

            # Start Secondary YOLO Detection
            if self.settings.secondary_detection.enabled:
                logger.info("Starting SECONDARY detection pipeline")
                self._secondary_service = DetectionService(
                    settings=self.settings,
                    detection_config=self.settings.secondary_detection,
                    config_label="secondary",
                )
                self._secondary_input_thread, self._secondary_webrtc_stop = self._start_source(
                    self.settings.secondary_detection.camera,
                    self._secondary_frame_queue,
                    "Secondary Camera"
                )
            else:
                logger.info("SECONDARY detection pipeline is DISABLED")

    def stop(self) -> None:
        """Stop all services and input threads."""
        self._stop_event.set()
        if self._visible_webrtc_stop:
            self._visible_webrtc_stop.set()
        if self._thermal_webrtc_stop:
            self._thermal_webrtc_stop.set()
        if self._secondary_webrtc_stop:
            self._secondary_webrtc_stop.set()
            
        if self._visible_input_thread:
            self._visible_input_thread.join(timeout=2)
        if self._thermal_input_thread:
            self._thermal_input_thread.join(timeout=2)
        if self._secondary_input_thread:
            self._secondary_input_thread.join(timeout=2)
            
        with self._lock:
            self._visible_service = None
            self._thermal_service = None
            self._secondary_service = None
            self._visible_input_thread = None
            self._thermal_input_thread = None
            self._secondary_input_thread = None

    def get_detections(self) -> list[DetectionResult]:
        """Run inference on both pipelines and return combined results."""
        results = []
        now = time.time()
        
        # Visible Inference
        if self._visible_service:
            try:
                frame = self._visible_frame_queue.get_nowait()
                boxes = self._visible_service.detect(frame)
                results.append(DetectionResult(
                    mode=DetectionMode.VISIBLE,
                    boxes=boxes,
                    frame=frame,
                    frame_shape=frame.shape[:2],
                    timestamp=now
                ))
            except queue.Empty:
                pass
                
        # Thermal Inference
        if self._thermal_service:
            try:
                frame = self._thermal_frame_queue.get_nowait()
                targets = self._thermal_service.detect(frame)
                results.append(DetectionResult(
                    mode=DetectionMode.THERMAL,
                    boxes=targets,
                    frame=frame,
                    frame_shape=frame.shape[:2],
                    timestamp=now
                ))
            except queue.Empty:
                pass

        # Secondary YOLO Inference
        if self._secondary_service:
            try:
                frame = self._secondary_frame_queue.get_nowait()
                boxes = self._secondary_service.detect(frame)
                results.append(DetectionResult(
                    mode=DetectionMode.SECONDARY,
                    boxes=boxes,
                    frame=frame,
                    frame_shape=frame.shape[:2],
                    timestamp=now
                ))
            except queue.Empty:
                pass
                
        return results

    def get_service(self, mode: DetectionMode):
        """Get the detection service instance for a specific mode."""
        if mode == DetectionMode.VISIBLE:
            return self._visible_service
        if mode == DetectionMode.THERMAL:
            return self._thermal_service
        if mode == DetectionMode.SECONDARY:
            return self._secondary_service
        return None

    def get_tracking_priority(self) -> DetectionMode:
        """Return which mode should drive PTZ tracking (configurable)."""
        priority = self.settings.tracking.priority
        if priority == "thermal" and self.settings.thermal_detection.enabled:
            return DetectionMode.THERMAL
        if priority == "visible" and self.settings.visible_detection.enabled:
            return DetectionMode.VISIBLE
        if priority == "secondary" and self.settings.secondary_detection.enabled:
            return DetectionMode.SECONDARY
            
        # Fallback
        if self.settings.secondary_detection.enabled:
            return DetectionMode.SECONDARY
        if self.settings.thermal_detection.enabled:
            return DetectionMode.THERMAL
        return DetectionMode.VISIBLE
