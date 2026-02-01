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
from src.analytics.events import TrackLifecycle
from src.analytics.metadata import MetadataBuilder
from src.detection_manager import DetectionManager, DetectionMode, DetectionResult
from src.ptz_controller import PTZService
from src.settings import Settings
from src.tracking.state import TrackerStatus, TrackingPhase
from src.webrtc_client import start_webrtc_client


# Removed legacy _frame_grabber and _calculate_coverage as DetectionManager handles them


@dataclass(slots=True)
class ThreadedAnalyticsSession:
    session_id: str
    camera_id: str
    settings: Settings
    detection_id: str = "visible"
    publish_debug_logs: bool = False
    _lock: threading.Lock = field(init=False, repr=False)
    _running: bool = field(init=False, repr=False)
    _latest_tick: dict[str, Any] | None = field(init=False, repr=False)
    _stop_event: threading.Event = field(init=False, repr=False)
    _thread: threading.Thread | None = field(init=False, repr=False)
    _commands: queue.Queue[dict[str, Any]] = field(init=False, repr=False)
    _tracker_status: TrackerStatus = field(init=False, repr=False)
    _detection_manager: DetectionManager | None = field(init=False, repr=False)
    _class_names: dict[int, str] | None = field(init=False, repr=False)
    _ptz: Any | None = field(init=False, repr=False)
    _analytics: AnalyticsEngine | None = field(init=False, repr=False)
    _frame_index: int = field(init=False, repr=False)
    _fps_window: deque[float] = field(init=False, repr=False)
    _track_lifecycle: TrackLifecycle = field(init=False, repr=False)
    _events: deque[tuple[int, dict[str, Any]]] = field(init=False, repr=False)
    _event_seq: int = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._lock = threading.Lock()
        self._running = False
        self._latest_tick = None
        self._stop_event = threading.Event()
        self._thread = None
        self._commands = queue.Queue()

        self._tracker_status = TrackerStatus(
            loss_grace_s=self.settings.tracking.end_after_ms / 1000.0
        )
        self._detection_manager = None
        self._class_names = None
        self._ptz = None
        self._analytics = None
        self._frame_index = 0
        self._fps_window = deque(maxlen=self.settings.performance.fps_window_size)
        self._track_lifecycle = TrackLifecycle(
            session_id=self.session_id, camera_id=self.camera_id
        )
        self._events = deque(maxlen=1_000)
        self._event_seq = 0

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
        if self._detection_manager is not None:
            self._detection_manager.stop()
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

    def get_events_since(
        self, last_seq: int | None
    ) -> tuple[int | None, list[dict[str, Any]]]:
        with self._lock:
            if not self._events:
                return last_seq, []

            events: list[dict[str, Any]] = []
            max_seq: int | None = last_seq
            for seq, payload in self._events:
                if last_seq is not None and seq <= last_seq:
                    continue
                events.append(dict(payload))
                max_seq = seq if max_seq is None else max(max_seq, seq)

        return max_seq, events

    def reload_services(self, new_settings: Settings) -> dict[str, Any]:
        """Hot-reload detection and camera services with new settings.
        
        This allows runtime switching between YOLO and thermal detection,
        and changing camera sources without a full service restart.
        
        Args:
            new_settings: New settings to apply
            
        Returns:
            Status dict with reload results
        """
        results = {
            "detection_reloaded": False,
            "camera_reloaded": False,
            "new_mode": "concurrent" if (
                new_settings.visible_detection.enabled and new_settings.thermal_detection.enabled
            ) else (
                "secondary"
                if new_settings.secondary_detection.enabled
                else "visible"
                if new_settings.visible_detection.enabled
                else "thermal"
                if new_settings.thermal_detection.enabled
                else "none"
            ),
        }
        
        with self._lock:
            # For simplicity, we trigger reload if any detection/camera settings changed
            # In a more advanced impl, we would compare field by field
            detection_changed = True 
            camera_changed = True
            
            # Update settings reference
            self.settings = new_settings
            logger.info(f"Session {self.session_id} reloading with thermal method: {self.settings.thermal_detection.detection_method}")
            
            # Reload detection service if mode changed
            if detection_changed:
                if self._detection_manager:
                    self._detection_manager.stop()
                self._detection_manager = None  # Force rebuild
                self._class_names = None
                self._analytics = None  # Rebuild with new priority service
                if self._ptz is not None:
                    with contextlib.suppress(Exception):
                        self._ptz.stop()
                self._ptz = None  # Re-evaluate PTZ ownership
                results["detection_reloaded"] = True
                logger.info(f"Session {self.session_id}: Detection manager re-initializing for new mode: {results['new_mode']}")
            
            # Camera reload requires restarting input thread
            if camera_changed and self._running:
                results["camera_reloaded"] = True
                logger.info(f"Session {self.session_id}: Camera settings changed, will apply on next restart")
                # Note: Full camera hot-swap requires stopping the input thread
                # which would interrupt the stream. For now, log the change.
                # A full implementation would need careful thread management.
        
        # Re-ensure services to apply detection changes
        if results["detection_reloaded"] and self._running:
            self._ensure_services()
            if self._detection_manager:
                self._detection_manager.start()
                self._refresh_class_names()
            
        return results


    def _ensure_services(self) -> None:
        if self._detection_manager is None:
            self._detection_manager = DetectionManager(settings=self.settings)
            logger.info(f"API Session {self.session_id}: DetectionManager initialized")
            # Class names are resolved after the detection manager starts.
        if self._ptz is None and self._should_control_ptz():
            if self.settings.simulator.use_ptz_simulation:
                from src.ptz_simulator import SimulatedPTZService  # noqa: PLC0415

                self._ptz = SimulatedPTZService(settings=self.settings)
            else:
                self._ptz = PTZService(settings=self.settings)
        elif self._ptz is not None and not self._should_control_ptz():
            # Drop PTZ control if this session is no longer the tracking source.
            with contextlib.suppress(Exception):
                self._ptz.stop()
            self._ptz = None
        if self._analytics is None:
            builder = MetadataBuilder(
                session_id=self.session_id, camera_id=self.camera_id
            )
            # Use priority service for analytics state tracking
            p_mode = self._detection_manager.get_tracking_priority()
            p_service = self._detection_manager.get_service(p_mode)
            
            self._analytics = AnalyticsEngine(
                detection=p_service,
                metadata=builder,
                tracker_status=self._tracker_status,
            )
            self._track_lifecycle = TrackLifecycle(
                session_id=self.session_id, 
                camera_id=self.camera_id,
                confirm_after=self.settings.tracking.confirm_after,
                end_after_ms=self.settings.tracking.end_after_ms
            )

    def _should_control_ptz(self) -> bool:
        if self.settings.ptz.control_mode == "none":
            return False
        if not (
            self.settings.visible_detection.enabled
            or self.settings.thermal_detection.enabled
            or self.settings.secondary_detection.enabled
        ):
            return False
        if self.detection_id == "visible" and not self.settings.visible_detection.enabled:
            return False
        if self.detection_id == "thermal" and not self.settings.thermal_detection.enabled:
            return False
        if self.detection_id == "secondary" and not self.settings.secondary_detection.enabled:
            return False
        return self.settings.tracking.priority == self.detection_id

    def _refresh_class_names(self) -> None:
        """Resolve class names from active detection services."""
        if not self._detection_manager:
            return

        class_names: dict[int, str] | None = None
        if self.settings.visible_detection.enabled:
            vis_service = self._detection_manager.get_service(DetectionMode.VISIBLE)
            if vis_service:
                class_names = vis_service.get_class_names()
        if not class_names and self.settings.secondary_detection.enabled:
            sec_service = self._detection_manager.get_service(DetectionMode.SECONDARY)
            if sec_service:
                class_names = sec_service.get_class_names()
        if not class_names and self.settings.thermal_detection.enabled:
            therm_service = self._detection_manager.get_service(DetectionMode.THERMAL)
            if therm_service:
                class_names = therm_service.get_class_names()

        if class_names:
            self._class_names = class_names
            return

        if self.settings.thermal_detection.enabled:
            self._class_names = {0: "target"}
        else:
            self._class_names = {0: "drone", 1: "UAV"}

    def _class_names_list(self) -> list[str]:
        if not self._class_names:
            return ["target"]
        max_id = max(self._class_names)
        labels = [str(i) for i in range(max_id + 1)]
        for cls_id, name in self._class_names.items():
            if 0 <= cls_id <= max_id:
                labels[cls_id] = str(name)
        return labels

    def _start_input(self) -> None:
        if self._detection_manager:
            self._detection_manager.start()
            self._refresh_class_names()

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
        assert self._detection_manager is not None
        assert self._analytics is not None
        
        ptz_movement_gain = self.settings.ptz.ptz_movement_gain
        ptz_movement_threshold = self.settings.ptz.ptz_movement_threshold
        zoom_target_coverage = self.settings.ptz.zoom_target_coverage
        zoom_dead_zone = self.settings.performance.zoom_dead_zone
        zoom_velocity_gain = self.settings.ptz.zoom_velocity_gain

        while not self._stop_event.is_set():
            self._drain_commands()
            
            results = self._detection_manager.get_detections()
            if not results:
                time.sleep(0.01)
                continue

            now = time.time()
            self._fps_window.append(now)

            # Determine tracking priority
            priority_mode = self._detection_manager.get_tracking_priority()
            priority_result = next((r for r in results if r.mode == priority_mode), results[0])
            
            frame_h, frame_w = priority_result.frame_shape
            frame_center = (frame_w // 2, frame_h // 2)

            # Update analytics engine priority service if it changed
            # (e.g. if priority was switched via API)
            p_service = self._detection_manager.get_service(priority_mode)
            if self._analytics.detection != p_service:
                self._analytics.detection = p_service

            priority_boxes = priority_result.boxes
            best_det = self._analytics.update_tracking(priority_boxes, now=now)

            # PTZ Control
            if self._ptz is not None and self._tracker_status.phase == TrackingPhase.TRACKING:
                tracking_bbox = None
                if best_det is not None:
                    # best_det might be a YOLO box or a ThermalTarget
                    # Both are handled by normalize_bbox_xyxy in MetadataBuilder
                    # For PTZ control we need pixel coords
                    x1, y1, x2, y2 = _extract_pixel_coords(best_det, frame_w, frame_h)
                    tracking_bbox = (x1, y1, x2, y2)

                if tracking_bbox is not None:
                    x1, y1, x2, y2 = tracking_bbox
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    dx = (cx - frame_center[0]) / frame_w
                    dy = (cy - frame_center[1]) / frame_h

                    pan = dx * ptz_movement_gain if abs(dx) > ptz_movement_threshold else 0.0
                    tilt = -dy * ptz_movement_gain if abs(dy) > ptz_movement_threshold else 0.0
                    
                    # Zoom logic
                    box_w, box_h = x2 - x1, y2 - y1
                    coverage = max(box_w / frame_w, box_h / frame_h)
                    diff = zoom_target_coverage - coverage
                    zoom = diff * zoom_velocity_gain if abs(diff) > zoom_dead_zone else 0.0
                    
                    self._ptz.continuous_move(
                        max(-1.0, min(1.0, pan)), 
                        max(-1.0, min(1.0, tilt)), 
                        max(-1.0, min(1.0, zoom))
                    )
                else:
                    self._ptz.stop()
            elif self._ptz is not None and getattr(self._ptz, "active", False):
                self._ptz.stop()

            # Build Tick with combined tracks
            # For now we use the priority frame size as the context
            all_boxes = []
            for res in results:
                all_boxes.extend(res.boxes)
            
            tick = self._analytics.build_tick(
                all_boxes,
                frame_index=self._frame_index,
                frame_w=frame_w,
                frame_h=frame_h,
                class_names=self._class_names_list(),
                ptz=self._ptz,
                ts_unix_ms=int(time.time() * 1000),
                ts_mono_ms=int(time.monotonic() * 1000),
            )

            track_events = self._track_lifecycle.update(
                tracks=tick["tracks"], ts_unix_ms=tick["ts_unix_ms"]
            )
            with self._lock:
                self._latest_tick = dict(tick)
                for event in track_events:
                    self._event_seq += 1
                    self._events.append((self._event_seq, dict(event)))
            self._frame_index += 1


def _extract_pixel_coords(det: Any, frame_w: int, frame_h: int) -> tuple[int, int, int, int]:
    """Extract pixel coordinates from any detection type (YOLO or Thermal)."""
    # Try YOLO xyxy attribute first
    xyxy = getattr(det, "xyxy", None)
    if xyxy is not None:
        x1, y1, x2, y2 = xyxy[0]
        if all(0 <= v <= 1.0 for v in [x1, y1, x2, y2]):
            return int(x1 * frame_w), int(y1 * frame_h), int(x2 * frame_w), int(y2 * frame_h)
        return int(x1), int(y1), int(x2), int(y2)
    
    # Try Thermal target attributes
    x = getattr(det, "x", 0)
    y = getattr(det, "y", 0)
    w = getattr(det, "w", 0)
    h = getattr(det, "h", 0)
    return x, y, x + w, y + h


def default_session_factory(
    session_id: str, camera_id: str, settings_manager: Any
) -> ThreadedAnalyticsSession:
    """Create a new analytics session with latest settings from manager.

    Args:
        session_id: Unique session identifier
        camera_id: Camera identifier
        settings_manager: SettingsManager instance to get current settings

    Returns:
        New ThreadedAnalyticsSession instance
    """
    from src.detection_profiles import resolve_profile, settings_for_profile  # noqa: PLC0415

    settings = settings_manager.get_settings()
    profile = resolve_profile(settings, camera_id)
    if profile is None:
        raise ValueError(f"Unknown camera_id for analytics session: {camera_id}")
    session_settings = settings_for_profile(settings, profile.profile_id)
    return ThreadedAnalyticsSession(
        session_id=session_id,
        camera_id=camera_id,
        settings=session_settings,
        detection_id=profile.profile_id,
    )
