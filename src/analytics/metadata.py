from __future__ import annotations

import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from src.analytics.types import (
    CoordinateSpace,
    MetadataTick,
    NormalizedBBox,
    PtzCommand,
    PtzControlMode,
    PtzState,
    SchemaName,
    Track,
    TrackingPhaseValue,
)
from src.tracking.selector import parse_track_id
from src.tracking.state import TrackerStatus


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def _round6(value: float) -> float:
    return round(value, 6)


def _as_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        if hasattr(value, "item"):
            return float(value.item())
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        if hasattr(value, "item"):
            return int(value.item())
        return int(value)
    except (TypeError, ValueError):
        return None


def _xyxy_from_det(det: Any) -> tuple[float, float, float, float] | None:
    xyxy = getattr(det, "xyxy", None)
    if xyxy is None:
        return None
    try:
        row = xyxy[0]
        x1, y1, x2, y2 = row
        return (_as_float(x1), _as_float(y1), _as_float(x2), _as_float(y2))
    except Exception:
        return None


def normalize_bbox_xyxy(
    *,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    frame_w: int,
    frame_h: int,
) -> NormalizedBBox:
    if frame_w <= 0 or frame_h <= 0:
        msg = f"Invalid frame size w={frame_w} h={frame_h}"
        raise ValueError(msg)

    # Some paths may already provide normalized xyxy in [0..1].
    looks_normalized = all(0.0 <= v <= 1.0 for v in (x1, y1, x2, y2))
    if looks_normalized:
        x = x1
        y = y1
        w = x2 - x1
        h = y2 - y1
    else:
        x = x1 / frame_w
        y = y1 / frame_h
        w = (x2 - x1) / frame_w
        h = (y2 - y1) / frame_h

    x = _round6(_clamp(x, 0.0, 1.0))
    y = _round6(_clamp(y, 0.0, 1.0))
    w = _round6(_clamp(w, 0.0, 1.0))
    h = _round6(_clamp(h, 0.0, 1.0))
    return {"x": x, "y": y, "w": w, "h": h}


def _class_label(det: Any, class_names: Sequence[str]) -> str:
    cls = getattr(det, "cls", None)
    cls_i = _as_int(cls)
    if cls_i is None:
        return "unknown"
    if 0 <= cls_i < len(class_names):
        return str(class_names[cls_i])
    return str(cls_i)


def tracks_from_detections(
    tracked_boxes: Iterable[Any],
    *,
    class_names: Sequence[str],
    frame_w: int,
    frame_h: int,
) -> list[Track]:
    tracks: list[Track] = []
    for det in tracked_boxes:
        track_id = parse_track_id(det)
        if track_id is None:
            continue

        label = _class_label(det, class_names)
        conf = _round6(_clamp(_as_float(getattr(det, "conf", 0.0), 0.0), 0.0, 1.0))
        xyxy = _xyxy_from_det(det)
        if xyxy is None:
            continue
        x1, y1, x2, y2 = xyxy
        bbox = normalize_bbox_xyxy(
            x1=x1, y1=y1, x2=x2, y2=y2, frame_w=frame_w, frame_h=frame_h
        )
        tracks.append({"id": track_id, "label": label, "conf": conf, "bbox": bbox})
    return tracks


def _ptz_control_mode_from_obj(ptz: Any) -> PtzControlMode:
    mode = getattr(ptz, "control_mode", None)
    if mode in ("onvif", "octagon"):
        return mode
    # Best-effort fallback for the simulator.
    return "sim"


def _ptz_cmd_from_obj(ptz: Any) -> PtzCommand:
    # "cmd" refers to the last commanded velocity values when using continuous_move.
    # Clamp to avoid leaking absolute/degree position values when a backend sync overwrote them.
    pan = _clamp(_as_float(getattr(ptz, "last_pan", 0.0), 0.0), -1.0, 1.0)
    tilt = _clamp(_as_float(getattr(ptz, "last_tilt", 0.0), 0.0), -1.0, 1.0)
    zoom = _clamp(_as_float(getattr(ptz, "last_zoom", 0.0), 0.0), -1.0, 1.0)
    return {"pan": _round6(pan), "tilt": _round6(tilt), "zoom": _round6(zoom)}


def _ptz_state_from_obj(ptz: Any) -> PtzState:
    state: PtzState = {
        "control_mode": _ptz_control_mode_from_obj(ptz),
        "active": bool(getattr(ptz, "active", False)),
        "cmd": _ptz_cmd_from_obj(ptz),
    }

    return state


def _tracking_phase_value(tracker_status: TrackerStatus) -> TrackingPhaseValue:
    # TrackerStatus.phase is an Enum; use its `.value` strings (idle/searching/tracking/lost).
    phase = getattr(tracker_status, "phase", None)
    value = getattr(phase, "value", None)
    if value in ("idle", "searching", "tracking", "lost"):
        return value
    return "idle"


@dataclass(slots=True)
class MetadataBuilder:
    session_id: str
    camera_id: str
    space: CoordinateSpace = "source"
    schema: SchemaName = "drone-ptz-metadata/1"

    def build_tick(
        self,
        *,
        frame_index: int | None,
        frame_w: int,
        frame_h: int,
        tracks: list[Track],
        tracker_status: TrackerStatus,
        ptz: Any | None = None,
        ts_unix_ms: int | None = None,
        ts_mono_ms: int | None = None,
    ) -> MetadataTick:
        if ts_unix_ms is None:
            ts_unix_ms = int(time.time() * 1000)

        tick: MetadataTick = {
            "schema": self.schema,
            "type": "metadata_tick",
            "session_id": self.session_id,
            "camera_id": self.camera_id,
            "ts_unix_ms": int(ts_unix_ms),
            "space": self.space,
            "frame_size": {"w": int(frame_w), "h": int(frame_h)},
            "selected_target_id": tracker_status.target_id,
            "tracking_phase": _tracking_phase_value(tracker_status),
            "tracks": tracks,
        }

        if frame_index is not None:
            tick["frame_index"] = int(frame_index)

        if ts_mono_ms is not None:
            tick["ts_mono_ms"] = int(ts_mono_ms)

        if ptz is not None:
            tick["ptz"] = _ptz_state_from_obj(ptz)

        return tick

    def build_tick_from_detections(
        self,
        tracked_boxes: Iterable[Any],
        *,
        frame_index: int | None,
        frame_w: int,
        frame_h: int,
        class_names: Sequence[str],
        tracker_status: TrackerStatus,
        ptz: Any | None = None,
        ts_unix_ms: int | None = None,
        ts_mono_ms: int | None = None,
    ) -> MetadataTick:
        tracks = tracks_from_detections(
            tracked_boxes, class_names=class_names, frame_w=frame_w, frame_h=frame_h
        )
        return self.build_tick(
            frame_index=frame_index,
            frame_w=frame_w,
            frame_h=frame_h,
            tracks=tracks,
            tracker_status=tracker_status,
            ptz=ptz,
            ts_unix_ms=ts_unix_ms,
            ts_mono_ms=ts_mono_ms,
        )
