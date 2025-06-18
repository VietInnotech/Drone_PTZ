import cv2

def draw_info_overlay(
    frame,
    model_path,
    camera_index,
    resolution,
    device,
    confidence,
    fps,
    detection_count,
    tracking_ids,
    frame_num,
    proc_time,
    frame_skip,
    target_coverage,
    timestamp
):
    """
    Overlay system, stats, and configuration info on the frame for visualization.

    Args:
        frame: The image frame (numpy array).
        model_path: Path to the model used.
        camera_index: Index of the camera.
        resolution: Tuple (width, height) of the frame.
        device: Device string (e.g., 'cpu', 'cuda').
        confidence: Detection confidence threshold.
        fps: Frames per second.
        detection_count: Number of detections in the frame.
        tracking_ids: List of tracking IDs.
        frame_num: Current frame number.
        proc_time: Processing time per frame.
        frame_skip: Number of skipped frames.
        target_coverage: Target object coverage (fraction).
        timestamp: Timestamp string.
    Returns:
        Frame with overlay drawn.
    """
    overlay = frame.copy()
    h, w = frame.shape[:2]
    font = cv2.FONT_HERSHEY_SIMPLEX

    # Colors
    color_sys = (40, 180, 255)      # Orange for system info
    color_stats = (0, 200, 0)       # Green for stats
    color_conf = (255, 140, 0)      # Blue/Orange for config
    color_bg = (30, 30, 30)
    alpha = 0.7

    # --- Top-left: System Info ---
    sys_lines = [
        f"Model: {model_path}",
        f"Camera: Index {camera_index} ({resolution[0]}x{resolution[1]})",
        f"Device: {device}",
        f"Confidence: {confidence:.2f}"
    ]
    x0, y0 = 10, 10
    line_h = 28
    box_w = max([cv2.getTextSize(line, font, 0.7, 2)[0][0] for line in sys_lines]) + 20
    box_h = line_h * len(sys_lines) + 10
    cv2.rectangle(overlay, (x0-5, y0-5), (x0+box_w, y0+box_h), color_bg, -1)
    for i, line in enumerate(sys_lines):
        cv2.putText(overlay, line, (x0, y0 + line_h * (i+1) - 10), font, 0.7, color_sys, 2)

    # --- Top-right: Real-time Stats ---
    stats_lines = [
        f"FPS: {fps:.2f}",
        f"Detections: {detection_count}",
        f"Tracking: {tracking_ids}",
        f"Frame: {frame_num}",
        f"Proc: {proc_time:.1f}ms"
    ]
    box_w2 = max([cv2.getTextSize(line, font, 0.7, 2)[0][0] for line in stats_lines]) + 20
    x1 = w - box_w2 - 10
    y1 = 10
    box_h2 = line_h * len(stats_lines) + 10
    cv2.rectangle(overlay, (x1-5, y1-5), (x1+box_w2, y1+box_h2), color_bg, -1)
    for i, line in enumerate(stats_lines):
        cv2.putText(overlay, line, (x1, y1 + line_h * (i+1) - 10), font, 0.7, color_stats, 2)

    # --- Bottom: Config ---
    conf_line = f"Frame Skip: {frame_skip} | Target Coverage: {int(target_coverage*100)}% | {timestamp}"
    box_w3 = cv2.getTextSize(conf_line, font, 0.8, 2)[0][0] + 20
    box_h3 = 38
    x2 = 10
    y2 = h - box_h3 - 10
    cv2.rectangle(overlay, (x2-5, y2-5), (x2+box_w3, y2+box_h3), color_bg, -1)
    cv2.putText(overlay, conf_line, (x2, y2 + box_h3 - 18), font, 0.8, color_conf, 2)

    # --- Bottom-right: Quit hint ---
    quit_line = "Press 'q' to quit"
    box_w4 = cv2.getTextSize(quit_line, font, 0.7, 2)[0][0] + 20
    x3 = w - box_w4 - 10
    y3 = h - box_h3 - 10
    cv2.rectangle(overlay, (x3-5, y3-5), (x3+box_w4, y3+box_h3), color_bg, -1)
    cv2.putText(overlay, quit_line, (x3, y3 + box_h3 - 18), font, 0.7, (200, 200, 200), 2)

    # Blend overlay
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    return frame