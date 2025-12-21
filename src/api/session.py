from __future__ import annotations

import contextlib
import queue
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any

import cv2
from loguru import logger

from src.analytics.engine import AnalyticsEngine
from src.analytics.metadata import MetadataBuilder
from src.detection import DetectionService
from src.ptz_controller import PTZService
from src.settings import Settings, load_settings
from src.tracking.state import TrackerStatus, TrackingPhase
from src.webrtc_client import start_webrtc_client


def _frame_grabber(
    frame_queue: queue.Queue[Any],
    stop_event: threading.Event,
    *,
    settings: Settings,
) -> None:
    """Continuously grab frames and keep only the latest."""
    video_source = settings.simulator.video_source
    camera_index = settings.camera.camera_index
    rtsp_url = settings.camera.rtsp_url
    fps_setting = settings.camera.fps
    resolution_width = settings.camera.resolution_width
    resolution_height = settings.camera.resolution_height
    video_loop = settings.simulator.video_loop

    if rtsp_url:
        cap = cv2.VideoCapture(rtsp_url)
        frame_delay = None
    elif video_source is not None:
        cap = cv2.VideoCapture(video_source)
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        frame_delay = 1.0 / video_fps if video_fps > 0 else (1.0 / 30.0)
    else:
        cap = cv2.VideoCapture(camera_index, cv2.CAP_ANY)
        cap.set(cv2.CAP_PROP_FPS, fps_setting)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution_height)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc(*"MJPG"))
        frame_delay = None

    if not cap.isOpened():
        logger.error(
            "Failed to open video source (rtsp={} source={})", rtsp_url, video_source
        )
        return

    last_frame_time = time.time()
    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            if video_source is not None and video_loop:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            break

        if frame_delay is not None:
            elapsed = time.time() - last_frame_time
            sleep_time = frame_delay - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
            last_frame_time = time.time()

        if not frame_queue.empty():
            with contextlib.suppress(queue.Empty):
                frame_queue.get_nowait()
        with contextlib.suppress(queue.Full):
            frame_queue.put_nowait(frame)

    cap.release()


def _calculate_coverage(
    x1: int, y1: int, x2: int, y2: int, *, frame_w: int, frame_h: int
) -> float:
    box_w = max(1, x2 - x1)
    box_h = max(1, y2 - y1)
    return max(box_w / frame_w, box_h / frame_h)


@dataclass(slots=True)
class ThreadedAnalyticsSession:
    session_id: str
    camera_id: str
    settings: Settings
    publish_debug_logs: bool = False
    _lock: threading.Lock = field(init=False, repr=False)
    _running: bool = field(init=False, repr=False)
    _latest_tick: dict[str, Any] | None = field(init=False, repr=False)
    _stop_event: threading.Event = field(init=False, repr=False)
    _thread: threading.Thread | None = field(init=False, repr=False)
    _frame_queue: queue.Queue[Any] = field(init=False, repr=False)
    _input_thread: threading.Thread | None = field(init=False, repr=False)
    _commands: queue.Queue[dict[str, Any]] = field(init=False, repr=False)
    _tracker_status: TrackerStatus = field(init=False, repr=False)
    _detection: DetectionService | None = field(init=False, repr=False)
    _class_names: dict[int, str] | None = field(init=False, repr=False)
    _ptz: Any | None = field(init=False, repr=False)
    _analytics: AnalyticsEngine | None = field(init=False, repr=False)
    _frame_index: int = field(init=False, repr=False)
    _fps_window: deque[float] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._lock = threading.Lock()
        self._running = False
        self._latest_tick: dict[str, Any] | None = None
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._frame_queue: queue.Queue[Any] = queue.Queue(
            maxsize=self.settings.performance.frame_queue_maxsize
        )
        self._input_thread: threading.Thread | None = None
        self._commands: queue.Queue[dict[str, Any]] = queue.Queue()

        self._tracker_status = TrackerStatus(loss_grace_s=2.0)
        self._detection: DetectionService | None = None
        self._class_names: dict[int, str] | None = None
        self._ptz: Any | None = None
        self._analytics: AnalyticsEngine | None = None
        self._frame_index = 0
        self._fps_window = deque(maxlen=self.settings.performance.fps_window_size)

    def is_running(self) -> bool:
        with self._lock:
            return self._running

    def start(self) -> None:
        with self._lock:
            if self._running:
                return
            self._running = True
            self._stop_event.clear()

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._input_thread is not None:
            self._input_thread.join(timeout=2)
        if self._thread is not None:
            self._thread.join(timeout=5)
        with self._lock:
            self._running = False

    def set_target_id(self, target_id: int) -> None:
        self._commands.put({"type": "set_target_id", "target_id": int(target_id)})

    def clear_target(self) -> None:
        self._commands.put({"type": "clear_target"})

    def get_latest_tick(self) -> dict[str, Any] | None:
        with self._lock:
            if self._latest_tick is None:
                return None
            return dict(self._latest_tick)

    def get_status(self) -> dict[str, Any]:
        with self._lock:
            tick = self._latest_tick
            last_ts = tick.get("ts_unix_ms") if tick else None
            phase = getattr(self._tracker_status.phase, "value", "idle")
            target_id = self._tracker_status.target_id

        return {
            "running": self.is_running(),
            "selected_target_id": target_id,
            "tracking_phase": phase,
            "last_tick_ts_unix_ms": last_ts,
        }

    def _ensure_services(self) -> None:
        if self._detection is None:
            self._detection = DetectionService(settings=self.settings)
            self._class_names = self._detection.get_class_names()
        if self._ptz is None:
            if self.settings.simulator.use_ptz_simulation:
                from src.ptz_simulator import SimulatedPTZService  # noqa: PLC0415

                self._ptz = SimulatedPTZService(settings=self.settings)
            else:
                self._ptz = PTZService(settings=self.settings)
        if self._analytics is None:
            builder = MetadataBuilder(
                session_id=self.session_id, camera_id=self.camera_id
            )
            self._analytics = AnalyticsEngine(
                detection=self._detection,
                metadata=builder,
                tracker_status=self._tracker_status,
            )

    def _start_input(self) -> None:
        if self.settings.camera.source == "webrtc":
            self._input_thread = start_webrtc_client(
                self._frame_queue,
                self._stop_event,
                url=self.settings.camera.webrtc_url,
                width=self.settings.camera.resolution_width,
                height=self.settings.camera.resolution_height,
                fps=self.settings.camera.fps,
            )
            return

        self._input_thread = threading.Thread(
            target=_frame_grabber,
            args=(self._frame_queue, self._stop_event),
            kwargs={"settings": self.settings},
            daemon=True,
        )
        self._input_thread.start()

    def _drain_commands(self) -> None:
        while True:
            with contextlib.suppress(queue.Empty):
                cmd = self._commands.get_nowait()
                if cmd.get("type") == "set_target_id":
                    self._tracker_status.set_target(
                        int(cmd["target_id"]), now=time.time()
                    )
                elif cmd.get("type") == "clear_target":
                    self._tracker_status.clear_target()
                continue
            break

    def _run(self) -> None:
        try:
            self._ensure_services()
            self._start_input()
            self._loop()
        except Exception as exc:  # pragma: no cover - best-effort error isolation
            logger.exception("Session {} crashed: {}", self.session_id, exc)
        finally:
            self._stop_event.set()
            with self._lock:
                self._running = False

    def _loop(self) -> None:
        assert self._analytics is not None
        assert self._class_names is not None

        ptz_movement_gain = self.settings.ptz.ptz_movement_gain
        ptz_movement_threshold = self.settings.ptz.ptz_movement_threshold
        zoom_target_coverage = self.settings.ptz.zoom_target_coverage
        zoom_dead_zone = self.settings.performance.zoom_dead_zone
        zoom_velocity_gain = self.settings.ptz.zoom_velocity_gain

        while not self._stop_event.is_set():
            self._drain_commands()
            try:
                frame = self._frame_queue.get(timeout=1)
            except queue.Empty:
                continue

            now = time.time()
            self._fps_window.append(now)

            frame_h, frame_w = frame.shape[:2]
            frame_center = (frame_w // 2, frame_h // 2)

            tracked_boxes = self._analytics.infer(frame)
            best_det = self._analytics.update_tracking(tracked_boxes, now=now)

            if (
                self._ptz is not None
                and self._tracker_status.phase == TrackingPhase.TRACKING
            ):
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

                if tracking_bbox is not None:
                    x1, y1, x2, y2 = tracking_bbox
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)

                    dx = (cx - frame_center[0]) / frame_w
                    dy = (cy - frame_center[1]) / frame_h

                    pan = (
                        dx * ptz_movement_gain
                        if abs(dx) > ptz_movement_threshold
                        else 0.0
                    )
                    tilt = (
                        -dy * ptz_movement_gain
                        if abs(dy) > ptz_movement_threshold
                        else 0.0
                    )
                    pan = max(-1.0, min(1.0, pan))
                    tilt = max(-1.0, min(1.0, tilt))

                    coverage = _calculate_coverage(
                        x1, y1, x2, y2, frame_w=frame_w, frame_h=frame_h
                    )
                    coverage_diff = zoom_target_coverage - coverage
                    zoom = 0.0
                    if abs(coverage_diff) > zoom_dead_zone:
                        zoom = max(-1.0, min(1.0, coverage_diff * zoom_velocity_gain))

                    self._ptz.continuous_move(pan, tilt, zoom)
                else:
                    self._ptz.stop()
            elif self._ptz is not None and getattr(self._ptz, "active", False):
                self._ptz.stop()

            tick = self._analytics.build_tick(
                tracked_boxes,
                frame_index=self._frame_index,
                frame_w=frame_w,
                frame_h=frame_h,
                class_names=list(self._class_names.values()),
                ptz=self._ptz,
                ts_unix_ms=int(time.time() * 1000),
                ts_mono_ms=int(time.monotonic() * 1000),
            )

            with self._lock:
                self._latest_tick = dict(tick)
            self._frame_index += 1


def default_session_factory(
    session_id: str, camera_id: str
) -> ThreadedAnalyticsSession:
    settings = load_settings()
    return ThreadedAnalyticsSession(
        session_id=session_id, camera_id=camera_id, settings=settings
    )
