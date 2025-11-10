import contextlib
import queue
import sys
import threading
import time
from collections import deque
from typing import Any

import cv2
import numpy as np

from src.config import Config, logger
from src.detection import DetectionService
from src.ptz_controller import PTZService

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


def frame_grabber(frame_queue: queue.Queue, stop_event: threading.Event) -> None:
    """Continuously grab frames from the camera and put the latest into the queue."""
    cap = cv2.VideoCapture(Config.CAMERA_INDEX, cv2.CAP_ANY)
    cap.set(cv2.CAP_PROP_FPS, Config.FPS)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, Config.RESOLUTION_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.RESOLUTION_HEIGHT)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc(*"MJPG"))
    if not cap.isOpened():
        error_msg = (
            f"Failed to open camera at index {Config.CAMERA_INDEX}.\n"
            f"Troubleshooting:\n"
            f"  1. Check if camera is connected: ls /dev/video*\n"
            f"  2. Try different CAMERA_INDEX in config.py (try 0, 1, 2, etc.)\n"
            f"  3. Ensure camera permissions: sudo usermod -a -G video $USER\n"
            f"  4. Check if another application is using the camera"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            logger.warning("Failed to read frame from camera.")
            break
        # Always keep only the latest frame
        if not frame_queue.empty():
            with contextlib.suppress(queue.Empty):
                frame_queue.get_nowait()
        frame_queue.put(frame)
    cap.release()


def draw_detection_boxes(
    frame: np.ndarray, class_names: list[str], tracked_boxes: Any
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
        label = class_names[cls_id] if cls_id < len(class_names) else str(cls_id)
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
            label_text += f" ID:{track_id}"
            tracking_ids.append(int(track_id))
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
) -> None:
    """Draw detection statistics on the top-left of the frame."""
    detection_lines = [
        f"Detections: {detection_count}",
        f"Tracking IDs: {tracking_ids}",
        f"FPS: {fps:.2f}",
        f"Proc Time: {proc_time * 1000:.1f} ms",
        f"Confidence: {Config.CONFIDENCE_THRESHOLD}",
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
    frame: np.ndarray, ptz: PTZService, last_ptz_command: str, coverage: float
) -> None:
    """Draw PTZ status information on the top-right of the frame."""
    _frame_h, frame_w = frame.shape[:2]
    ptz_lines = [
        f"PTZ Status: {'active' if ptz.active else 'idle'}",
        f"Last PTZ Cmd: {last_ptz_command}",
        f"Current Coverage: {coverage * 100:.1f}%",
        f"Target Coverage: {Config.ZOOM_TARGET_COVERAGE * 100:.1f}%",
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
    frame: np.ndarray, frame_index: int, detection: DetectionService, ptz: PTZService
) -> None:
    """Draw system information on the bottom-left of the frame."""
    frame_h, _frame_w = frame.shape[:2]
    sys_lines = [
        f"Frame: {frame_index}",
        f"Model: {Config.MODEL_PATH}",
        f"Camera: {Config.CAMERA_INDEX}",
        f"Resolution: {Config.RESOLUTION_WIDTH}x{Config.RESOLUTION_HEIGHT}",
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
    class_names: list[str],
    tracked_boxes: Any,
    fps: float,
    proc_time: float,
    ptz: PTZService,
    last_ptz_command: str,
    coverage: float,
    frame_index: int,
    detection: DetectionService,
) -> None:
    """Draw bounding boxes and informational overlay on the frame."""
    tracking_ids = draw_detection_boxes(frame, class_names, tracked_boxes)
    detection_count = len(tracked_boxes)

    draw_detection_info(frame, detection_count, tracking_ids, fps, proc_time)
    draw_ptz_status(frame, ptz, last_ptz_command, coverage)
    draw_system_info(frame, frame_index, detection, ptz)


def main() -> None:
    """Main entry point for the PTZ tracking system."""
    # Validate configuration before starting
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Configuration validation failed:\n{e}")
        sys.exit(1)

    ptz = PTZService()
    detection = DetectionService()
    class_names = detection.get_class_names()

    last_zoom_time = 0.0
    zoom_active = False
    last_ptz_command = "None"
    fps_window = deque(maxlen=Config.FPS_WINDOW_SIZE)

    last_detection_time = 0.0
    home_triggered = False

    frame_queue = queue.Queue(maxsize=Config.FRAME_QUEUE_MAXSIZE)
    stop_event = threading.Event()
    grabber_thread = threading.Thread(
        target=frame_grabber, args=(frame_queue, stop_event), daemon=True
    )
    grabber_thread.start()

    frame_index = 0
    last_time = time.time()

    try:
        while True:
            now = time.time()

            try:
                frame = frame_queue.get(timeout=1)
            except queue.Empty:
                logger.warning("No frame received from frame queue. Exiting.")
                break

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

            best_det = None
            best_conf = 0
            for det in tracked_boxes:
                cls_id = int(det.cls)
                conf = float(det.conf)
                if (
                    class_names[cls_id] == "drone"
                    and conf > Config.CONFIDENCE_THRESHOLD
                ) and conf > best_conf:
                    best_det = det
                    best_conf = conf

            coverage = 0.0
            if best_det is not None:
                last_detection_time = now
                home_triggered = False

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
                    dx * Config.PTZ_MOVEMENT_GAIN
                    if abs(dx) > Config.PTZ_MOVEMENT_THRESHOLD
                    else 0
                )
                y_speed = (
                    -dy * Config.PTZ_MOVEMENT_GAIN
                    if abs(dy) > Config.PTZ_MOVEMENT_THRESHOLD
                    else 0
                )
                x_speed = max(-1.0, min(1.0, x_speed))
                y_speed = max(-1.0, min(1.0, y_speed))

                coverage = calculate_coverage(x1, y1, x2, y2, frame_w, frame_h)
                coverage_diff = Config.ZOOM_TARGET_COVERAGE - coverage

                # Calculate zoom velocity for continuous tracking
                zoom_velocity = 0.0
                if (
                    abs(coverage_diff) > Config.ZOOM_DEAD_ZONE
                    and (now - last_zoom_time) >= Config.ZOOM_MIN_INTERVAL
                ):
                    # Proportional ramping for zoom velocity
                    zoom_velocity = max(
                        -1.0, min(1.0, coverage_diff * Config.ZOOM_VELOCITY_GAIN)
                    )
                    if zoom_velocity != 0.0:
                        last_zoom_time = now
                        zoom_active = True

                if x_speed != 0 or y_speed != 0 or zoom_active:
                    ptz.continuous_move(x_speed, y_speed, zoom_velocity)
                    last_ptz_command = f"continuous_move({x_speed:.2f}, {y_speed:.2f}, {zoom_velocity:.2f})"
                else:
                    ptz.stop()
                    last_ptz_command = "stop()"
            else:
                if ptz.active:
                    ptz.stop()
                    last_ptz_command = "stop()"
                if zoom_active and (
                    now - last_detection_time > Config.ZOOM_RESET_TIMEOUT
                ):
                    # Smoothly reset zoom using continuous move to wide (negative velocity)
                    ptz.continuous_move(0, 0, -abs(Config.ZOOM_RESET_VELOCITY))
                    last_ptz_command = "continuous_move(0, 0, -ZOOM_RESET_VELOCITY)"
                    zoom_active = False

                if (
                    not home_triggered
                    and (now - last_detection_time) > Config.NO_DETECTION_HOME_TIMEOUT
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
            )

            cv2.imshow("Detection", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
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
