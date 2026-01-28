import contextlib
import queue
import threading
import time
from collections import deque
from typing import Any
from urllib.parse import urlparse

import cv2
import numpy as np
from loguru import logger

from src.detection import DetectionService
from src.thermal_detection import ThermalDetectionService
from src.frame_buffer import FrameBuffer
from src.latency_monitor import LatencyMonitor
from src.metadata_manager import MetadataManager
from src.ptz_controller import PTZService
from src.ptz_servo import PIDGains, PTZServo
from src.settings import load_settings
from src.tracking.state import (
    TrackerStatus,
    TrackingPhase,
)
from src.watchdog import Watchdog

# Latest analytics metadata snapshot (Phase 1 extraction target).
# Intended to be read by a future API/WebSocket layer (Phase 2).
# Now using thread-safe MetadataManager instead of global variable.
metadata_manager = MetadataManager()

# --- Logging configuration ---
# The logger is now configured in config.py by calling setup_logging().
# This ensures consistent logging across the application.


def calculate_coverage(
    x1: int, y1: int, x2: int, y2: int, frame_w: int, frame_h: int
) -> float:
    """Calculate the coverage of a bounding box relative to the frame size."""
    box_w = max(1, x2 - x1)
    box_h = max(1, y2 - y1)
    width_cov = box_w / frame_w
    height_cov = box_h / frame_h
    return max(width_cov, height_cov)


def simulate_ptz_view(
    frame: np.ndarray, ptz: Any, settings: Any = None
) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    """
    Crop and resize frame to simulate PTZ viewport based on pan/tilt/zoom.

    Args:
        frame: Original input frame.
        ptz: PTZ service object with pan_pos, tilt_pos, zoom_level attributes.
        settings: Settings object (optional, for getting zoom_min_scale and resolution).

    Returns:
        Tuple of (simulated_frame, viewport_rect) where viewport_rect is (x1, y1, x2, y2)
        in original frame coordinates.
    """
    frame_h, frame_w = frame.shape[:2]

    # Map zoom_level to viewport scale
    if hasattr(ptz, "zmin") and hasattr(ptz, "zmax"):
        z_normalized = (ptz.zoom_level - ptz.zmin) / (ptz.zmax - ptz.zmin + 1e-6)
    else:
        z_normalized = 0.0
    z_normalized = max(0.0, min(1.0, z_normalized))

    # Get zoom_min_scale from Settings
    zoom_min_scale = settings.simulator.sim_zoom_min_scale

    scale = 1.0 - z_normalized * (1.0 - zoom_min_scale)

    crop_w = max(1, round(frame_w * scale))
    crop_h = max(1, round(frame_h * scale))

    # Map pan/tilt to viewport center
    pan_pos = getattr(ptz, "pan_pos", 0.0)
    tilt_pos = getattr(ptz, "tilt_pos", 0.0)
    cx = frame_w / 2 + pan_pos * (frame_w / 2 - crop_w / 2)
    cy = frame_h / 2 - tilt_pos * (frame_h / 2 - crop_h / 2)

    # Convert to top-left corner and clamp
    x1 = max(0, min(frame_w - crop_w, round(cx - crop_w / 2)))
    y1 = max(0, min(frame_h - crop_h, round(cy - crop_h / 2)))
    x2 = min(frame_w, x1 + crop_w)
    y2 = min(frame_h, y1 + crop_h)

    # Crop
    roi = frame[y1:y2, x1:x2] if x1 < x2 and y1 < y2 else frame

    # Get resolution from Settings
    resolution_width = settings.camera.resolution_width
    resolution_height = settings.camera.resolution_height

    # Resize to configured resolution
    sim_frame = cv2.resize(roi, (resolution_width, resolution_height))

    return sim_frame, (x1, y1, x2, y2)


def draw_viewport_on_original(
    frame: np.ndarray, rect: tuple[int, int, int, int]
) -> None:
    """
    Draw viewport rectangle on the original frame for reference.

    Args:
        frame: Frame to draw on.
        rect: Viewport rectangle (x1, y1, x2, y2) in frame coordinates.
    """
    x1, y1, x2, y2 = rect
    # Use contrasting color (cyan)
    color = (255, 255, 0)
    thickness = 2
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
    cv2.putText(
        frame,
        "Viewport",
        (x1 + 5, max(y1 - 5, 15)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        color,
        1,
        cv2.LINE_AA,
    )


def frame_grabber(
    frame_queue: queue.Queue, stop_event: threading.Event, settings: Any = None
) -> None:
    """Continuously grab frames from the camera or video file and put the latest into the queue."""
    # Get video source from Settings
    video_source = settings.simulator.video_source
    
    # Check for thermal mode override
    use_thermal = getattr(settings, "thermal", None) and settings.thermal.enabled
    
    if use_thermal:
        # Use thermal camera settings
        cam_settings = settings.thermal.camera
        camera_index = cam_settings.camera_index
        rtsp_url = cam_settings.rtsp_url
        fps_setting = cam_settings.fps
        resolution_width = cam_settings.resolution_width
        resolution_height = cam_settings.resolution_height
        logger.info(f"Using THERMAL camera input: index={camera_index}, rtsp={rtsp_url}")
    else:
        # Use standard camera settings
        camera_index = settings.camera.camera_index
        rtsp_url = settings.camera.rtsp_url
        fps_setting = settings.camera.fps
        resolution_width = settings.camera.resolution_width
        resolution_height = settings.camera.resolution_height

    video_loop = settings.simulator.video_loop

    # Priority: RTSP URL > video_source > camera_index
    if rtsp_url:
        cap = cv2.VideoCapture(rtsp_url)
        logger.info(f"Opening RTSP stream: {rtsp_url}")
        frame_delay = None  # No delay for live RTSP stream
    elif video_source is not None:
        cap = cv2.VideoCapture(video_source)
        logger.info(f"Opening video source: {video_source}")
        # Get the video's original FPS for timing
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        if video_fps > 0:
            frame_delay = 1.0 / video_fps
            logger.info(
                f"Video FPS: {video_fps:.2f}, frame delay: {frame_delay * 1000:.1f}ms"
            )
        else:
            frame_delay = 1.0 / 30.0  # Default to 30 FPS if unable to detect
            logger.warning("Unable to detect video FPS, defaulting to 30 FPS")
    else:
        cap = cv2.VideoCapture(camera_index, cv2.CAP_ANY)
        cap.set(cv2.CAP_PROP_FPS, fps_setting)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution_height)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc(*"MJPG"))
        logger.info(f"Opening camera at index: {camera_index}")
        frame_delay = None  # No delay for live camera

    if not cap.isOpened():
        if rtsp_url:
            error_msg = (
                f"Failed to open RTSP stream: {rtsp_url}\n"
                f"Troubleshooting:\n"
                f"  1. Check if the RTSP URL is correct\n"
                f"  2. Verify network connectivity to the camera\n"
                f"  3. Ensure credentials are correct (username/password)\n"
                f"  4. Check if the camera supports RTSP protocol\n"
                f"  5. Try accessing the stream with VLC or ffplay to verify"
            )
        elif video_source is not None:
            error_msg = f"Failed to open video file: {video_source}"
        else:
            error_msg = (
                f"Failed to open camera at index {camera_index}.\n"
                f"Troubleshooting:\n"
                f"  1. Check if camera is connected: ls /dev/video*\n"
                f"  2. Try different CAMERA_INDEX in config.py (try 0, 1, 2, etc.)\n"
                f"  3. Ensure camera permissions: sudo usermod -a -G video $USER\n"
                f"  4. Check if another application is using the camera"
            )
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    last_frame_time = time.time()
    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            # Handle EOF for video files
            if video_source is not None:
                if video_loop:
                    logger.debug("End of video file, rewinding to start")
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                logger.info("End of video file reached, exiting")
                break
            logger.warning("Failed to read frame from camera.")
            break

        # For video files, respect the original frame rate
        if frame_delay is not None:
            elapsed = time.time() - last_frame_time
            sleep_time = frame_delay - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
            last_frame_time = time.time()

        # Always keep only the latest frame
        if not frame_queue.empty():
            with contextlib.suppress(queue.Empty):
                frame_queue.get_nowait()
        frame_queue.put(frame)

    cap.release()


def _derive_camera_id(settings: Any) -> str:
    """Best-effort camera_id derivation for analytics metadata."""
    try:
        if settings.camera.source == "webrtc" and settings.camera.webrtc_url:
            parsed = urlparse(settings.camera.webrtc_url)
            parts = [p for p in parsed.path.split("/") if p]
            if parts:
                return str(parts[-1])
    except Exception:
        pass
    return "default"


def draw_detection_boxes(
    frame: np.ndarray,
    class_names: dict[int, str],
    tracked_boxes: Any,
    highlight_id: int | None = None,
) -> list[int]:
    """
    Draw bounding boxes for all detections on the frame.

    Args:
        frame: Frame to draw on.
        class_names: List of class names from the model.
        tracked_boxes: Detected boxes from YOLO.
        highlight_id: ID to highlight with green color and thicker border, or None.

    Returns:
        List of tracking IDs.
    """
    frame_h, frame_w = frame.shape[:2]
    tracking_ids = []

    for det in tracked_boxes:
        cls_id = int(det.cls)
        conf = float(det.conf)
        label = class_names.get(cls_id, str(cls_id))
        x1, y1, x2, y2 = det.xyxy[0]
        if all(0 <= v <= 1.0 for v in [x1, y1, x2, y2]):
            x1, y1, x2, y2 = (
                int(x1 * frame_w),
                int(y1 * frame_h),
                int(x2 * frame_w),
                int(y2 * frame_h),
            )
        else:
            x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])

        track_id = getattr(det, "id", None)
        if track_id is not None and hasattr(track_id, "item"):
            track_id = track_id.item()
        track_id_int = int(track_id) if track_id is not None else None

        # Determine color and thickness based on highlight
        if highlight_id is not None and track_id_int == highlight_id:
            color = (0, 255, 0)  # Green for highlighted target
            thickness = 3
        else:
            color = (0, 255, 255) if label == "drone" else (255, 0, 0)
            thickness = 2

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

        label_text = f"{label} {conf:.2f}"
        if track_id_int is not None:
            label_text += f" ID:{track_id_int}"
            tracking_ids.append(track_id_int)

        cv2.putText(
            frame,
            label_text,
            (x1, max(y1 - 10, 0)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2,
            cv2.LINE_AA,
        )

    return tracking_ids


def draw_detection_info(
    frame: np.ndarray,
    detection_count: int,
    tracking_ids: list[int],
    fps: float,
    proc_time: float,
    settings: Any = None,
) -> None:
    """Draw detection statistics on the top-left of the frame."""
    # Get confidence threshold from Settings
    confidence_threshold = settings.detection.confidence_threshold

    detection_lines = [
        f"Detections: {detection_count}",
        f"Tracking IDs: {tracking_ids}",
        f"FPS: {fps:.2f}",
        f"Proc Time: {proc_time * 1000:.1f} ms",
        f"Confidence: {confidence_threshold}",
    ]
    y0, dy = 30, 25
    for i, line in enumerate(detection_lines):
        cv2.putText(
            frame,
            line,
            (10, y0 + i * dy),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )


def draw_ptz_status(
    frame: np.ndarray,
    ptz: Any,
    last_ptz_command: str,
    coverage: float,
    tracker_status: Any = None,
    settings: Any = None,
) -> None:
    """
    Draw PTZ status information on the top-right of the frame.

    Args:
        frame: Frame to draw on.
        ptz: PTZ service instance.
        last_ptz_command: Last PTZ command issued.
        coverage: Current target coverage.
        tracker_status: Optional TrackerStatus instance for target info.
        settings: Settings object.
    """
    _frame_h, frame_w = frame.shape[:2]

    zoom_target_coverage = settings.ptz.zoom_target_coverage

    ptz_lines = [
        f"PTZ Status: {'active' if ptz.active else 'idle'}",
        f"Last PTZ Cmd: {last_ptz_command}",
        f"Current Coverage: {coverage * 100:.1f}%",
        f"Target Coverage: {zoom_target_coverage * 100:.1f}%",
    ]

    # Add tracker status if provided
    if tracker_status is not None:
        if tracker_status.target_id is not None:
            ptz_lines.append(
                f"Target: ID={tracker_status.target_id} ({tracker_status.phase.value})"
            )
        else:
            ptz_lines.append("Target: cleared (idle)")

    y0, dy = 30, 25
    for i, line in enumerate(ptz_lines):
        textsize = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        x = frame_w - textsize[0] - 10
        y = y0 + i * dy
        cv2.putText(
            frame,
            line,
            (x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 128, 0),
            2,
            cv2.LINE_AA,
        )


def draw_system_info(
    frame: np.ndarray,
    frame_index: int,
    detection: DetectionService,
    ptz: Any,
    settings: Any = None,
) -> None:
    """Draw system information on the bottom-left of the frame."""
    frame_h, _frame_w = frame.shape[:2]

    # Get config values from Settings
    model_path = settings.detection.model_path
    camera_index = settings.camera.camera_index
    resolution_width = settings.camera.resolution_width
    resolution_height = settings.camera.resolution_height

    detection_mode = "THERMAL" if getattr(settings, "thermal", None) and settings.thermal.enabled else "YOLO"
    
    sys_lines = [
        f"Frame: {frame_index}",
        f"Mode: {detection_mode}",
        f"Model: {model_path if detection_mode == 'YOLO' else settings.thermal.detection_method}",
        f"Camera: {camera_index}",
        f"Resolution: {resolution_width}x{resolution_height}",
        f"Device: {'cuda' if hasattr(detection.model, 'device') and str(detection.model.device) == 'cuda:0' else 'cpu'}",
        f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}",
        f"ONVIF: {'connected' if hasattr(ptz, 'connected') and ptz.connected else 'unknown'}",
    ]
    dy = 25
    y_bl = frame_h - dy * len(sys_lines) - 10
    for i, line in enumerate(sys_lines):
        cv2.putText(
            frame,
            line,
            (10, y_bl + i * dy),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 128, 255),
            2,
            cv2.LINE_AA,
        )


def draw_sot_bbox(
    frame: np.ndarray,
    sot_bbox: tuple[int, int, int, int],
) -> None:
    """
    Draw SOT bounding box on the frame with distinct magenta color.

    Args:
        frame: Frame to draw on.
        sot_bbox: SOT bounding box (x1, y1, x2, y2).
    """
    x1, y1, x2, y2 = sot_bbox
    color = (255, 0, 255)  # Magenta for SOT
    thickness = 3

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
    cv2.putText(
        frame,
        "SOT",
        (x1, max(y1 - 10, 15)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        color,
        2,
        cv2.LINE_AA,
    )


def draw_input_mode_overlay(frame: np.ndarray, input_buf: str) -> None:
    """
    Draw input mode overlay prompting for ID entry.

    Args:
        frame: Frame to draw on.
        input_buf: Current input buffer (digits typed).
    """
    frame_h, frame_w = frame.shape[:2]

    # Display at top-center, below detection/PTZ info
    y = 170
    font_scale = 1.2
    color = (0, 255, 255)  # Yellow
    bg_color = (0, 0, 0)  # Black for semi-transparent background

    text = f"Enter ID: {input_buf}_"  # Underscore shows cursor

    # Get text size for background
    textsize, baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)
    text_w, text_h = textsize

    # Draw semi-transparent background
    padding = 10
    x_center = frame_w // 2
    x1 = max(0, x_center - text_w // 2 - padding)
    y1 = max(0, y - text_h - padding)
    x2 = min(frame_w, x_center + text_w // 2 + padding)
    y2 = min(frame_h, y + baseline + padding)

    # Draw filled rectangle with transparency
    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), bg_color, -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    # Draw text centered
    text_x = x_center - text_w // 2
    cv2.putText(
        frame,
        text,
        (text_x, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        color,
        3,
        cv2.LINE_AA,
    )


def draw_overlay(
    frame: np.ndarray,
    class_names: dict[int, str],
    tracked_boxes: Any,
    fps: float,
    proc_time: float,
    ptz: Any,
    last_ptz_command: str,
    coverage: float,
    frame_index: int,
    detection: DetectionService,
    tracker_status: Any = None,
    input_mode: bool = False,
    input_buf: str = "",
    settings: Any = None,
) -> None:
    """
    Draw bounding boxes and informational overlay on the frame.

    Args:
        frame: Frame to draw on.
        class_names: Model class names.
        tracked_boxes: Detected boxes.
        fps: Frames per second.
        proc_time: Processing time for frame.
        ptz: PTZ controller.
        last_ptz_command: Last PTZ command.
        coverage: Current target coverage.
        frame_index: Current frame index.
        detection: Detection service.
        tracker_status: Optional TrackerStatus for target tracking info.
        input_mode: Whether in ID input mode.
        input_buf: Current input buffer.
        settings: Settings object.
    """
    # Determine highlight_id based on tracking phase
    highlight_id = None
    if tracker_status is not None and tracker_status.phase == TrackingPhase.TRACKING:
        highlight_id = tracker_status.target_id

    tracking_ids = draw_detection_boxes(
        frame, class_names, tracked_boxes, highlight_id=highlight_id
    )
    detection_count = len(tracked_boxes)

    draw_detection_info(frame, detection_count, tracking_ids, fps, proc_time, settings)
    draw_ptz_status(frame, ptz, last_ptz_command, coverage, tracker_status, settings)
    draw_system_info(frame, frame_index, detection, ptz, settings)

    # Draw input mode overlay if active
    if input_mode:
        draw_input_mode_overlay(frame, input_buf)


def main() -> None:
    """Main entry point for the PTZ tracking system."""
    # Load Settings from config.yaml
    settings = load_settings()

    # Select PTZ service implementation
    if settings.simulator.use_ptz_simulation:
        from src.ptz_simulator import SimulatedPTZService  # noqa: PLC0415

        ptz = SimulatedPTZService(settings=settings)
        logger.info("Using SimulatedPTZService (PTZ_SIMULATION enabled)")
    else:
        ptz = PTZService(settings=settings)
        logger.info("Using real PTZService (connecting to ONVIF camera)")

    # Initialize detection service (YOLO or Thermal)
    if settings.thermal.enabled:
        detection = ThermalDetectionService(settings=settings)
        logger.info("Thermal detection ENABLED (YOLO disabled)")
    else:
        detection = DetectionService(settings=settings)
        logger.info("YOLO object detection ENABLED")
        
    class_names = detection.get_class_names()

    # Initialize tracker status for ID-based targeting
    tracker_status = TrackerStatus(loss_grace_s=2.0)

    # Phase 1: analytics metadata builder/engine (no network, no UI coupling).
    from src.analytics.engine import AnalyticsEngine  # noqa: PLC0415
    from src.analytics.metadata import MetadataBuilder  # noqa: PLC0415

    camera_id = _derive_camera_id(settings)
    session_id = f"session-{camera_id}-{int(time.time())}"
    metadata_builder = MetadataBuilder(session_id=session_id, camera_id=camera_id)
    analytics_engine = AnalyticsEngine(
        detection=detection,
        metadata=metadata_builder,
        tracker_status=tracker_status,
    )

    # Input mode state
    input_mode = False
    input_buf = ""

    # Homing guards (separate flags to prevent duplicate calls)
    idle_home_triggered = True  # Will home immediately on startup
    detection_loss_home_triggered = False

    last_zoom_time = 0.0
    zoom_active = False
    last_ptz_command = "None"
    fps_window = deque(maxlen=settings.performance.fps_window_size)

    last_detection_time = 0.0

    frame_queue: queue.Queue = queue.Queue(
        maxsize=settings.performance.frame_queue_maxsize
    )
    stop_event = threading.Event()

    # Initialize new control modules for critical fixes
    pid_gains = PIDGains(
        kp=settings.ptz.pid_kp,
        ki=settings.ptz.pid_ki,
        kd=settings.ptz.pid_kd,
        integral_limit=settings.ptz.pid_integral_limit,
        dead_band=settings.ptz.pid_dead_band,
    )
    ptz_servo = PTZServo(pid_gains)
    frame_buffer = FrameBuffer(max_size=2)  # Minimal buffer for non-blocking behavior
    latency_monitor = LatencyMonitor(window_size=256)

    watchdog_timeout_s = 15.0
    watchdog_fired = threading.Event()

    def _on_watchdog_timeout() -> None:
        logger.critical(
            "Watchdog: no main-loop heartbeat for %.1fs; requesting shutdown",
            watchdog_timeout_s,
        )
        watchdog_fired.set()
        stop_event.set()

    watchdog = Watchdog(
        timeout_s=watchdog_timeout_s,
        on_timeout=_on_watchdog_timeout,
        name="main-loop-watchdog",
    )
    watchdog.start()

    grabber_thread: threading.Thread | None = None
    webrtc_thread: threading.Thread | None = None

    if settings.camera.source == "webrtc":
        try:
            from src.webrtc_client import start_webrtc_client  # noqa: PLC0415

            webrtc_thread = start_webrtc_client(
                frame_queue,
                stop_event,
                url=settings.camera.webrtc_url,
                width=settings.camera.resolution_width,
                height=settings.camera.resolution_height,
                fps=settings.camera.fps,
            )
            logger.info(
                "WebRTC client started to fetch stream from %s",
                settings.camera.webrtc_url,
            )
        except Exception as exc:  # pragma: no cover - best-effort error handling
            logger.exception("Failed to start WebRTC client: %s", exc)
            raise
    else:
        grabber_thread = threading.Thread(
            target=frame_grabber, args=(frame_queue, stop_event, settings), daemon=True
        )
        grabber_thread.start()

    frame_index = 0
    last_time = time.time()

    # Allow longer to receive the first frame for RTSP/WebRTC
    if settings.camera.source == "webrtc":
        frame_get_timeout = 10
    elif settings.camera.rtsp_url:
        frame_get_timeout = 5
    else:
        frame_get_timeout = 1
    first_frame_received = False

    try:
        # Pre-load settings values for efficient access in the main loop
        ptz_movement_gain = settings.ptz.ptz_movement_gain
        ptz_movement_threshold = settings.ptz.ptz_movement_threshold
        zoom_target_coverage = settings.ptz.zoom_target_coverage
        zoom_dead_zone = settings.performance.zoom_dead_zone
        zoom_min_interval = settings.ptz.zoom_min_interval
        zoom_velocity_gain = settings.ptz.zoom_velocity_gain
        zoom_reset_timeout = settings.ptz.zoom_reset_timeout
        zoom_reset_velocity = settings.ptz.zoom_reset_velocity
        no_detection_home_timeout = settings.ptz.no_detection_home_timeout
        use_ptz_simulation = settings.simulator.use_ptz_simulation
        sim_viewport = settings.simulator.sim_viewport
        sim_draw_original_viewport_box = (
            settings.simulator.sim_draw_original_viewport_box
        )
        resolution_width = settings.camera.resolution_width
        resolution_height = settings.camera.resolution_height
        
        # New PTZ control parameters
        invert_pan = settings.ptz.invert_pan
        invert_tilt = settings.ptz.invert_tilt
        enable_zoom_compensation = settings.ptz.enable_zoom_compensation
        zoom_max_mag = settings.ptz.zoom_max_magnification

        while True:
            loop_start = time.perf_counter()
            now = time.time()

            if not first_frame_received:
                try:
                    orig_frame = frame_queue.get(timeout=frame_get_timeout)
                    frame_buffer.put(orig_frame)
                    first_frame_received = True
                    frame_get_timeout = 1
                    if settings.camera.source == "webrtc":
                        logger.info("First frame received from WebRTC input")
                except queue.Empty:
                    logger.debug("No frame received from frame queue. Continuing...")
                    time.sleep(0.01)
                    continue
            else:
                # Drain any queued frames into the non-blocking buffer
                while True:
                    try:
                        new_frame = frame_queue.get_nowait()
                        frame_buffer.put(new_frame)
                    except queue.Empty:
                        break

            frame = frame_buffer.get_nowait()
            if frame is None:
                logger.debug("Frame buffer empty; waiting for frames")
                time.sleep(0.01)
                continue

            orig_frame = frame

            # Apply PTZ simulation if enabled
            if use_ptz_simulation and sim_viewport:
                frame, viewport_rect = simulate_ptz_view(orig_frame, ptz, settings)
                # Detection runs on simulated viewport
            else:
                frame = orig_frame
                viewport_rect = None

            fps_window.append(now)
            fps = (
                len(fps_window) / (fps_window[-1] - fps_window[0] + 1e-6)
                if len(fps_window) > 1
                else 0.0
            )
            proc_time = now - last_time
            last_time = now

            frame_h, frame_w = frame.shape[:2]
            frame_center = (frame_w // 2, frame_h // 2)

            tracked_boxes = analytics_engine.infer(frame)

            # Periodically sync position from camera (every 10 frames)
            # Uses ONVIF GetStatus or Octagon API depending on position_mode
            if frame_index % 10 == 0 and hasattr(ptz, "update_position"):
                ptz.update_position()

            # Debug logging: frame-level PTZ state and detection count
            pan_pos = getattr(ptz, "pan_pos", getattr(ptz, "last_pan", 0.0))
            tilt_pos = getattr(ptz, "tilt_pos", getattr(ptz, "last_tilt", 0.0))
            zoom_val = getattr(ptz, "zoom_level", getattr(ptz, "last_zoom", 0.0))
            logger.debug(
                f"Frame {frame_index}: detections={len(tracked_boxes)}, "
                f"zoom={zoom_val:.3f}, pan={pan_pos:.3f}, tilt={tilt_pos:.3f}"
            )

            # ===== Target Selection: ID-locked or label-based =====
            best_det = None
            old_phase = tracker_status.phase
            old_target_id = tracker_status.target_id

            if tracker_status.target_id is not None:
                # ID-lock mode: find the target by ID only
                best_det = analytics_engine.update_tracking(tracked_boxes, now=now)
                target_found = best_det is not None

                if target_found:
                    logger.debug(
                        f"Target ID {tracker_status.target_id} found in frame "
                        f"{frame_index} (phase: {tracker_status.phase.value})"
                    )
                else:
                    logger.debug(
                        f"Target ID {tracker_status.target_id} not found in frame "
                        f"{frame_index} (phase: {tracker_status.phase.value})"
                    )
            else:
                # IDLE mode: no label-based auto selection
                tracker_status.phase = TrackingPhase.IDLE
                logger.debug(
                    f"Frame {frame_index}: IDLE mode (no target locked), "
                    f"{len(tracked_boxes)} detections available"
                )

            # Reset PID servo on phase or target transitions to prevent state leakage and "wind-up"
            if tracker_status.phase != old_phase or tracker_status.target_id != old_target_id:
                logger.info(
                    f"Transition: phase({old_phase.value}->{tracker_status.phase.value}), "
                    f"target({old_target_id}->{tracker_status.target_id}). "
                    "Resetting PID servo state."
                )
                ptz_servo.reset()

            # Emit a structured metadata snapshot for this frame (Phase 1).
            # This is not sent anywhere yet; it enables a Phase 2 API/WebSocket layer.
            tick_data = analytics_engine.build_tick(
                tracked_boxes,
                frame_index=frame_index,
                frame_w=frame_w,
                frame_h=frame_h,
                class_names=class_names,
                ptz=ptz,
                ts_unix_ms=int(time.time() * 1000),
                ts_mono_ms=int(time.monotonic() * 1000),
            )
            # Use thread-safe metadata manager instead of global variable
            metadata_manager.update(tick_data)

            coverage = 0.0

            # ===== Phase-aware PTZ behavior =====
            if tracker_status.phase == TrackingPhase.IDLE:
                # IDLE: home once on entry, suppress detection-based homing
                if not idle_home_triggered:
                    ptz.set_home_position()
                    last_ptz_command = "set_home_position()"
                    idle_home_triggered = True
                    logger.info("IDLE phase: homing to default position")
                elif ptz.active:
                    ptz.stop()
                    last_ptz_command = "stop()"
                # Don't execute detection loss home while IDLE

            elif tracker_status.phase == TrackingPhase.TRACKING:
                # TRACKING: Drive PTZ based on target using YOLO detection
                last_detection_time = now
                idle_home_triggered = False
                detection_loss_home_triggered = False

                if frame_index % 30 == 0:
                    logger.info(f"TRACKING phase: target ID={tracker_status.target_id}")

                # Get tracking bbox from YOLO detection
                tracking_bbox: tuple[int, int, int, int] | None = None
                if best_det is not None:
                    x1, y1, x2, y2 = best_det.xyxy[0]
                    if all(0 <= v <= 1.0 for v in [x1, y1, x2, y2]):
                        x1, y1, x2, y2 = (
                            int(x1 * frame_w),
                            int(y1 * frame_h),
                            int(x2 * frame_w),
                            int(y2 * frame_h),
                        )
                    else:
                        x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                    tracking_bbox = (x1, y1, x2, y2)

                # Drive PTZ using tracking bbox from YOLO
                if tracking_bbox is not None:
                    x1, y1, x2, y2 = tracking_bbox

                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)

                    dx = (cx - frame_center[0]) / frame_w
                    dy = (cy - frame_center[1]) / frame_h

                    # Calculate current magnification for zoom compensation
                    zoom_factor = 1.0
                    if enable_zoom_compensation:
                        z_range = ptz.zmax - ptz.zmin
                        if z_range > 0:
                            z_norm = (ptz.zoom_level - ptz.zmin) / z_range
                            zoom_factor = 1.0 + z_norm * (zoom_max_mag - 1.0)
                    
                    # Apply zoom compensation and inversion to gains
                    # Pan: dx > 0 (Right) -> positive speed (Right)
                    # Tilt: dy > 0 (Down) -> negative speed (Down)
                    # Compensation reduces speed at high zoom to maintain visual stability
                    effective_gain = ptz_movement_gain / zoom_factor
                    
                    err_x = dx * effective_gain
                    err_y = -dy * effective_gain
                    
                    if invert_pan:
                        err_x = -err_x
                    if invert_tilt:
                        err_y = -err_y

                    # Use PID servo for smooth tracking instead of P-only control
                    # Servo automatically handles P, I, D terms for smooth convergence
                    x_speed, y_speed = ptz_servo.control(
                        error_x=err_x, error_y=err_y
                    )

                    coverage = calculate_coverage(x1, y1, x2, y2, frame_w, frame_h)
                    coverage_diff = zoom_target_coverage - coverage

                    # Calculate zoom velocity for continuous tracking
                    zoom_velocity = 0.0
                    if (
                        abs(coverage_diff) > zoom_dead_zone
                        and (now - last_zoom_time) >= zoom_min_interval
                    ):
                        # Proportional ramping for zoom velocity
                        zoom_velocity = max(
                            -1.0, min(1.0, coverage_diff * zoom_velocity_gain)
                        )
                        if zoom_velocity != 0.0:
                            last_zoom_time = now
                            zoom_active = True
                    else:
                        # Coverage is within dead zone, stop zooming
                        zoom_active = False

                    if x_speed != 0 or y_speed != 0 or zoom_velocity != 0:
                        ptz.continuous_move(x_speed, y_speed, zoom_velocity)
                        last_ptz_command = f"continuous_move({x_speed:.2f}, {y_speed:.2f}, {zoom_velocity:.2f})"
                        if frame_index % 30 == 0:
                            logger.info(
                                f"PTZ command: pan={x_speed:.2f}, tilt={y_speed:.2f}, "
                                f"zoom_vel={zoom_velocity:.2f}, coverage={coverage:.3f}"
                            )
                    else:
                        ptz.stop()
                        last_ptz_command = "stop()"
                elif ptz.active:
                    # No tracking bbox available
                    ptz.stop()
                    last_ptz_command = "stop()"

            else:
                # SEARCHING or LOST phase, or no detection
                if ptz.active:
                    ptz.stop()
                    last_ptz_command = "stop()"

                # Zoom reset logic (if no detection for a while)
                if zoom_active and (now - last_detection_time > zoom_reset_timeout):
                    ptz.continuous_move(0, 0, -abs(zoom_reset_velocity))
                    last_ptz_command = "continuous_move(0, 0, -ZOOM_RESET_VELOCITY)"
                    zoom_active = False

                # Detection loss homing (with guard to prevent duplicates)
                if (
                    not detection_loss_home_triggered
                    and (now - last_detection_time) > no_detection_home_timeout
                    and tracker_status.phase != TrackingPhase.IDLE
                ):
                    ptz.set_home_position()
                    last_ptz_command = "set_home_position()"
                    detection_loss_home_triggered = True
                    logger.warning(
                        f"No detection for {now - last_detection_time:.1f}s, "
                        f"homing (phase: {tracker_status.phase.value})"
                    )

            draw_overlay(
                frame,
                class_names,
                tracked_boxes,
                fps,
                proc_time,
                ptz,
                last_ptz_command,
                coverage,
                frame_index,
                detection,
                tracker_status,
                input_mode,
                input_buf,
                settings,
            )

            cv2.imshow("Detection", frame)

            # Display original frame with viewport rectangle if simulation is enabled
            if use_ptz_simulation and viewport_rect is not None:
                orig_display = orig_frame.copy()
                if sim_draw_original_viewport_box:
                    draw_viewport_on_original(orig_display, viewport_rect)
                # If we have a best detection in simulated frame, map its bbox back to original for debugging
                try:
                    if best_det is not None:
                        # best_det coordinates are in the simulated frame (resolution_width x resolution_height)
                        bx1, by1, bx2, by2 = best_det.xyxy[0]
                        # Convert normalized coords if necessary
                        if all(0 <= v <= 1.0 for v in [bx1, by1, bx2, by2]):
                            bx1, by1, bx2, by2 = (
                                int(bx1 * resolution_width),
                                int(by1 * resolution_height),
                                int(bx2 * resolution_width),
                                int(by2 * resolution_height),
                            )
                        else:
                            bx1, by1, bx2, by2 = map(int, [bx1, by1, bx2, by2])
                        vx1, vy1, vx2, vy2 = viewport_rect
                        crop_w = max(1, vx2 - vx1)
                        crop_h = max(1, vy2 - vy1)
                        scale_x = crop_w / resolution_width
                        scale_y = crop_h / resolution_height

                        orig_bx1 = int(vx1 + bx1 * scale_x)
                        orig_by1 = int(vy1 + by1 * scale_y)
                        orig_bx2 = int(vx1 + bx2 * scale_x)
                        orig_by2 = int(vy1 + by2 * scale_y)

                        # Draw mapped bbox on original for visual verification (magenta)
                        cv2.rectangle(
                            orig_display,
                            (orig_bx1, orig_by1),
                            (orig_bx2, orig_by2),
                            (255, 0, 255),
                            2,
                        )
                except Exception:
                    # Ignore mapping errors in hot path
                    pass

                cv2.imshow("Original", orig_display)

            # Check for 'q' key press or window close
            key = cv2.waitKey(1) & 0xFF

            # ===== Keyboard input handling =====
            if key != 0xFF:
                if input_mode:
                    # In input mode: collect digits, Backspace to delete, Enter to confirm, Esc to cancel
                    if key in (
                        ord("0"),
                        ord("1"),
                        ord("2"),
                        ord("3"),
                        ord("4"),
                        ord("5"),
                        ord("6"),
                        ord("7"),
                        ord("8"),
                        ord("9"),
                    ):
                        input_buf += chr(key)
                        logger.debug(f"Input buffer: {input_buf}")
                    elif key in (8, 127):
                        # Backspace: delete last character
                        if input_buf:
                            input_buf = input_buf[:-1]
                            logger.debug(f"Input buffer after backspace: {input_buf}")
                    elif key == ord("\r"):
                        # Enter: commit ID
                        if input_buf:
                            try:
                                target_id = int(input_buf)
                                tracker_status.set_target(target_id, now)
                                idle_home_triggered = False
                                input_mode = False
                                input_buf = ""
                                logger.info(
                                    f"Target ID set to {target_id}, "
                                    f"phase: {tracker_status.phase.value}"
                                )
                            except ValueError:
                                logger.warning(f"Invalid ID: {input_buf}")
                                input_buf = ""
                        else:
                            input_mode = False
                            input_buf = ""
                    elif key == 27:
                        # Esc: cancel input mode
                        input_mode = False
                        input_buf = ""
                        logger.info("Input mode cancelled")
                elif key == ord("i"):
                    # 'i': enter ID input mode
                    input_mode = True
                    input_buf = ""
                    logger.info(
                        "Entering ID input mode... (press Enter to confirm, Esc to cancel)"
                    )
                elif key == ord("c"):
                    # 'c': clear target and trigger home
                    tracker_status.clear_target()
                    detection_loss_home_triggered = True
                    logger.info("Target cleared, will home after timeout")
                elif key == ord("q"):
                    logger.info("User pressed 'q', exiting...")
                    break

            # Check if any window was closed
            if cv2.getWindowProperty("Detection", cv2.WND_PROP_VISIBLE) < 1:
                logger.info("Detection window closed, exiting...")
                break

            latency_monitor.record(time.perf_counter() - loop_start)

            if frame_index > 0 and frame_index % 120 == 0:
                snap = latency_monitor.snapshot()
                logger.info(
                    "Loop latency (n=%d): p50=%.1fms p95=%.1fms p99=%.1fms max=%.1fms",
                    snap.count,
                    snap.p50_ms,
                    snap.p95_ms,
                    snap.p99_ms,
                    snap.max_ms,
                )

            watchdog.feed()
            if watchdog_fired.is_set():
                logger.error("Watchdog fired; breaking main loop")
                break

            frame_index += 1
    finally:
        stop_event.set()
        if grabber_thread is not None:
            grabber_thread.join(timeout=2.0)
            if grabber_thread.is_alive():
                logger.warning(
                    "Frame grabber thread did not stop gracefully within timeout"
                )
        if webrtc_thread is not None:
            # The WebRTC thread runs aiohttp loop; we attempt a short join
            webrtc_thread.join(timeout=2.0)
            if webrtc_thread.is_alive():
                logger.warning("WebRTC thread did not stop gracefully within timeout")
        watchdog.stop()
        cv2.destroyAllWindows()
        logger.info("Application shut down cleanly.")


if __name__ == "__main__":
    main()
