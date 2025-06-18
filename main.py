import sys
import os
import time
import threading
import queue
from collections import deque
import cv2
from detection import DetectionService
from ptz_controller import PTZService
from config import Config, logger, setup_logging

# --- Logging configuration ---
# The logger is now configured in config.py by calling setup_logging().
# This ensures consistent logging across the application.


def calculate_coverage(x1, y1, x2, y2, frame_w, frame_h):
    """Calculate the coverage of a bounding box relative to the frame size."""
    box_w = max(1, x2 - x1)
    box_h = max(1, y2 - y1)
    width_cov = box_w / frame_w
    height_cov = box_h / frame_h
    return max(width_cov, height_cov)


def frame_grabber(frame_queue, stop_event):
    """Continuously grab frames from the camera and put the latest into the queue."""
    cap = cv2.VideoCapture(
        Config.CAMERA_INDEX,
        cv2.CAP_DSHOW,  
        # Use DirectShow for Windows compatibility.
        # MediaFoundation's DXVA slows down the camera probing process.
    )

    cap.set(cv2.CAP_PROP_FPS, Config.FPS)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, Config.RESOLUTION_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.RESOLUTION_HEIGHT)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc(*"MJPG"))
    if not cap.isOpened():
        logger.error("Camera or video source not found.")
        raise RuntimeError("Camera or video source not found.")
    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            logger.warning("Failed to read frame from camera.")
            break
        # Always keep only the latest frame
        if not frame_queue.empty():
            try:
                frame_queue.get_nowait()
            except queue.Empty:
                pass
        frame_queue.put(frame)
    cap.release()


def draw_overlay(
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
):
    """Draw bounding boxes and informational overlay on the frame."""
    frame_h, frame_w = frame.shape[:2]
    detection_count = len(tracked_boxes)
    tracking_ids = [
        int(det.id)
        for det in tracked_boxes
        if hasattr(det, "id") and det.id is not None
    ]

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

    detection_lines = [
        f"Detections: {detection_count}",
        f"Tracking IDs: {tracking_ids}",
        f"FPS: {fps:.2f}",
        f"Proc Time: {proc_time * 1000:.1f} ms",
        f"Confidence: {Config.CONFIDENCE_THRESHOLD}",
    ]
    ptz_lines = [
        f"PTZ Status: {'active' if ptz.active else 'idle'}",
        f"Last PTZ Cmd: {last_ptz_command}",
        f"Current Coverage: {coverage * 100:.1f}%",
        f"Target Coverage: {Config.ZOOM_TARGET_COVERAGE * 100:.1f}%",
    ]
    sys_lines = [
        f"Frame: {frame_index}",
        f"Model: {Config.MODEL_PATH}",
        f"Camera: {Config.CAMERA_INDEX}",
        f"Resolution: {Config.RESOLUTION_WIDTH}x{Config.RESOLUTION_HEIGHT}",
        f"Device: {'cuda' if hasattr(detection.model, 'device') and str(detection.model.device) == 'cuda:0' else 'cpu'}",
        f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}",
        f"ONVIF: {'connected' if hasattr(ptz, 'connected') and ptz.connected else 'unknown'}",
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


def main():
    """Main entry point for the PTZ tracking system."""
    ptz = PTZService()
    detection = DetectionService()
    class_names = detection.get_class_names()

    last_zoom_time = 0.0
    zoom_active = False
    last_ptz_command = "None"
    fps_window = deque(maxlen=30)

    last_detection_time = 0.0
    home_triggered = False

    frame_queue = queue.Queue(maxsize=1)
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
                ):
                    if conf > best_conf:
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
                    dx * Config.PTZ_PAN_GAIN
                    if abs(dx) > Config.PTZ_PAN_THRESHOLD
                    else 0
                )
                y_speed = (
                    -dy * Config.PTZ_TILT_GAIN
                    if abs(dy) > Config.PTZ_TILT_THRESHOLD
                    else 0
                )
                x_speed = max(-1.0, min(1.0, x_speed))
                y_speed = max(-1.0, min(1.0, y_speed))

                coverage = calculate_coverage(x1, y1, x2, y2, frame_w, frame_h)
                coverage_diff = Config.ZOOM_TARGET_COVERAGE - coverage

                # Calculate zoom velocity for continuous tracking
                zoom_velocity = 0.0
                if (
                    abs(coverage_diff) > 0.03
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
        grabber_thread.join()
        cv2.destroyAllWindows()
        logger.info("Application shut down cleanly.")


if __name__ == "__main__":
    main()
