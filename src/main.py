import contextlib
import queue
import threading
import time
from collections import deque
from typing import Any

import cv2
import numpy as np
from loguru import logger

from src.detection import DetectionService
from src.ptz_controller import PTZService
from src.settings import load_settings

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
    camera_index = settings.camera.camera_index
    fps_setting = settings.camera.fps
    resolution_width = settings.camera.resolution_width
    resolution_height = settings.camera.resolution_height
    video_loop = settings.simulator.video_loop

    if video_source is not None:
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
        if video_source is not None:
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


def draw_detection_boxes(
    frame: np.ndarray, class_names: dict[int, str], tracked_boxes: Any
) -> list[int]:
    """
    Draw bounding boxes for all detections on the frame.

    Args:
        frame: Frame to draw on.
        class_names: List of class names from the model.
        tracked_boxes: Detected boxes from YOLO.

    Returns:
        List of tracking IDs.
    """
    frame_h, frame_w = frame.shape[:2]
    tracking_ids = []

    for det in tracked_boxes:
        cls_id = int(det.cls)
        conf = float(det.conf)
        label = class_names.get(cls_id, str(cls_id))
        color = (0, 255, 255) if label == "drone" else (255, 0, 0)
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
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        track_id = getattr(det, "id", None)
        label_text = f"{label} {conf:.2f}"
        if track_id is not None:
            # Convert tensor to int if necessary
            if hasattr(track_id, "item"):
                track_id = track_id.item()
            track_id_int = int(track_id)
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
    settings: Any = None,
) -> None:
    """Draw PTZ status information on the top-right of the frame."""
    _frame_h, frame_w = frame.shape[:2]

    # Get zoom_target_coverage from Settings
    zoom_target_coverage = settings.ptz.zoom_target_coverage

    ptz_lines = [
        f"PTZ Status: {'active' if ptz.active else 'idle'}",
        f"Last PTZ Cmd: {last_ptz_command}",
        f"Current Coverage: {coverage * 100:.1f}%",
        f"Target Coverage: {zoom_target_coverage * 100:.1f}%",
    ]
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

    sys_lines = [
        f"Frame: {frame_index}",
        f"Model: {model_path}",
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
    settings: Any = None,
) -> None:
    """Draw bounding boxes and informational overlay on the frame."""
    tracking_ids = draw_detection_boxes(frame, class_names, tracked_boxes)
    detection_count = len(tracked_boxes)

    draw_detection_info(frame, detection_count, tracking_ids, fps, proc_time, settings)
    draw_ptz_status(frame, ptz, last_ptz_command, coverage, settings)
    draw_system_info(frame, frame_index, detection, ptz, settings)


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

    detection = DetectionService(settings=settings)
    class_names = detection.get_class_names()

    last_zoom_time = 0.0
    zoom_active = False
    last_ptz_command = "None"
    fps_window = deque(maxlen=settings.performance.fps_window_size)

    last_detection_time = 0.0
    home_triggered = False

    frame_queue: queue.Queue = queue.Queue(
        maxsize=settings.performance.frame_queue_maxsize
    )
    stop_event = threading.Event()
    grabber_thread = threading.Thread(
        target=frame_grabber, args=(frame_queue, stop_event, settings), daemon=True
    )
    grabber_thread.start()

    frame_index = 0
    last_time = time.time()

    try:
        # Pre-load settings values for efficient access in the main loop
        confidence_threshold = settings.detection.confidence_threshold
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
        target_labels = settings.detection.target_labels

        while True:
            now = time.time()

            try:
                orig_frame = frame_queue.get(timeout=1)
            except queue.Empty:
                logger.warning("No frame received from frame queue. Exiting.")
                break

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

            tracked_boxes = detection.detect(frame)

            # Debug logging: frame-level PTZ state and detection count
            pan_pos = getattr(ptz, "pan_pos", 0.0)
            tilt_pos = getattr(ptz, "tilt_pos", 0.0)
            zoom_val = getattr(ptz, "zoom_level", getattr(ptz, "zoom", 0.0))
            logger.debug(
                f"Frame {frame_index}: detections={len(tracked_boxes)}, "
                f"zoom={zoom_val:.3f}, pan={pan_pos:.3f}, tilt={tilt_pos:.3f}"
            )

            best_det = None
            best_conf = 0
            best_label = ""
            # Inspect each detection for diagnostics and perform robust label check
            for det in tracked_boxes:
                cls_id = int(det.cls)
                conf = float(det.conf)
                det_id = getattr(det, "id", None)
                if det_id is not None and hasattr(det_id, "item"):
                    det_id = det_id.item()
                label = class_names.get(cls_id, str(cls_id))
                logger.debug(
                    f"  Detection: label={label} cls={cls_id} conf={conf:.3f} id={det_id}"
                )
                # Only accept specific labels; avoid incorrect `or "UAV"` truthiness bug
                if (
                    label in target_labels
                    and conf > confidence_threshold
                    and conf > best_conf
                ):
                    best_det = det
                    best_conf = conf
                    best_label = label

            if best_det is not None:
                best_det_id = getattr(best_det, "id", None)
                if best_det_id is not None and hasattr(best_det_id, "item"):
                    best_det_id = best_det_id.item()
                logger.info(
                    f"Selected best_det: class={best_label} conf={best_conf:.3f} id={best_det_id}"
                )
                # Log bounding box coordinates for diagnostic purposes
                try:
                    bb = best_det.xyxy[0]
                    logger.debug(
                        f"  best_det.xyxy: {bb}, sim_frame_size=({frame_w},{frame_h})"
                    )
                except Exception:
                    logger.debug("  best_det.xyxy: unable to read coordinates")

            coverage = 0.0
            if best_det is not None:
                last_detection_time = now
                home_triggered = False

                if frame_index % 30 == 0:
                    logger.info(f"Drone detected with confidence {best_conf:.2f}")

                x1, y1, x2, y2 = best_det.xyxy[0]
                if all(0 <= v <= 1.0 for v in [x1, y1, x2, y2]):
                    x1, y1, x2, y2 = (
                        int(x1 * frame_w),
                        int(y1 * frame_h),
                        int(x2 * frame_w),
                        int(y2 * frame_h),
                    )

                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)

                dx = (cx - frame_center[0]) / frame_w
                dy = (cy - frame_center[1]) / frame_h

                x_speed = (
                    dx * ptz_movement_gain if abs(dx) > ptz_movement_threshold else 0
                )
                y_speed = (
                    -dy * ptz_movement_gain if abs(dy) > ptz_movement_threshold else 0
                )
                x_speed = max(-1.0, min(1.0, x_speed))
                y_speed = max(-1.0, min(1.0, y_speed))

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
            else:
                if ptz.active:
                    ptz.stop()
                    last_ptz_command = "stop()"
                if zoom_active and (now - last_detection_time > zoom_reset_timeout):
                    # Smoothly reset zoom using continuous move to wide (negative velocity)
                    ptz.continuous_move(0, 0, -abs(zoom_reset_velocity))
                    last_ptz_command = "continuous_move(0, 0, -ZOOM_RESET_VELOCITY)"
                    zoom_active = False

                if (
                    not home_triggered
                    and (now - last_detection_time) > no_detection_home_timeout
                ):
                    ptz.set_home_position()
                    last_ptz_command = "set_home_position()"
                    home_triggered = True

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
            if key == ord("q"):
                logger.info("User pressed 'q', exiting...")
                break

            # Check if any window was closed
            if cv2.getWindowProperty("Detection", cv2.WND_PROP_VISIBLE) < 1:
                logger.info("Detection window closed, exiting...")
                break

            frame_index += 1
    finally:
        stop_event.set()
        grabber_thread.join(timeout=2.0)
        if grabber_thread.is_alive():
            logger.warning(
                "Frame grabber thread did not stop gracefully within timeout"
            )
        cv2.destroyAllWindows()
        logger.info("Application shut down cleanly.")


if __name__ == "__main__":
    main()
