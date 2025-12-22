from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final, Literal

from src.analytics.types import NormalizedBBox, Track, TrackEvent, TrackSummary


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def _round6(value: float) -> float:
    return round(value, 6)


@dataclass(slots=True)
class _TrackState:
    track_id: int
    label: str
    start_ts_unix_ms: int
    last_seen_ts_unix_ms: int
    seen_count: int = 0
    confirmed: bool = False
    top_conf: float = 0.0
    best_bbox: NormalizedBBox | None = None
    end_ts_unix_ms: int | None = None


@dataclass(slots=True)
class TrackLifecycle:
    """Build Frigate-inspired track lifecycle events (new/update/end).

    This is intentionally independent of networking: callers can publish returned events
    over WebSocket, persist them, etc.
    """

    session_id: str
    camera_id: str
    confirm_after: int = 2
    end_after_ms: int = 1_000
    schema: Final[str] = "drone-ptz-metadata/1"
    _tracks: dict[int, _TrackState] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.confirm_after <= 0:
            msg = f"confirm_after must be > 0, got {self.confirm_after}"
            raise ValueError(msg)
        if self.end_after_ms < 0:
            msg = f"end_after_ms must be >= 0, got {self.end_after_ms}"
            raise ValueError(msg)

        self._tracks = {}

    def _summary(self, state: _TrackState) -> TrackSummary:
        summary: TrackSummary = {
            "track_id": f"{self.camera_id}/{state.track_id}",
            "id": int(state.track_id),
            "label": str(state.label),
            "top_conf": _round6(_clamp(float(state.top_conf), 0.0, 1.0)),
            "confirmed": bool(state.confirmed),
            "start_ts_unix_ms": int(state.start_ts_unix_ms),
            "end_ts_unix_ms": int(state.end_ts_unix_ms)
            if state.end_ts_unix_ms is not None
            else None,
        }
        if state.best_bbox is not None:
            summary["best_bbox"] = dict(state.best_bbox)
        return summary

    def _event(
        self,
        *,
        event: Literal["new", "update", "end"],
        ts_unix_ms: int,
        before: TrackSummary | None,
        after: TrackSummary,
    ) -> TrackEvent:
        payload: TrackEvent = {
            "schema": self.schema,
            "type": "track_event",
            "event": event,
            "session_id": self.session_id,
            "camera_id": self.camera_id,
            "ts_unix_ms": int(ts_unix_ms),
            "before": before,
            "after": after,
        }
        return payload

    def update(self, *, tracks: list[Track], ts_unix_ms: int) -> list[TrackEvent]:
        """Update lifecycle state from the current active tracks and emit any events."""
        events: list[TrackEvent] = []

        current_by_id: dict[int, Track] = {int(t["id"]): t for t in tracks}

        for track_id in sorted(current_by_id):
            track = current_by_id[track_id]
            conf = float(track["conf"])
            bbox = track["bbox"]
            label = str(track["label"])

            state = self._tracks.get(track_id)
            if state is None:
                state = _TrackState(
                    track_id=track_id,
                    label=label,
                    start_ts_unix_ms=int(ts_unix_ms),
                    last_seen_ts_unix_ms=int(ts_unix_ms),
                )
                self._tracks[track_id] = state

            state.label = label
            state.last_seen_ts_unix_ms = int(ts_unix_ms)
            state.seen_count += 1

            prev_confirmed = state.confirmed
            prev_top_conf = state.top_conf
            prev_best_bbox = state.best_bbox

            if conf > state.top_conf:
                state.top_conf = conf
                state.best_bbox = dict(bbox)

            if not state.confirmed and state.seen_count >= self.confirm_after:
                state.confirmed = True
                after = self._summary(state)
                events.append(
                    self._event(
                        event="new",
                        ts_unix_ms=int(ts_unix_ms),
                        before=None,
                        after=after,
                    )
                )
                continue

            if prev_confirmed and state.top_conf > prev_top_conf:
                before_state = _TrackState(
                    track_id=state.track_id,
                    label=state.label,
                    start_ts_unix_ms=state.start_ts_unix_ms,
                    last_seen_ts_unix_ms=state.last_seen_ts_unix_ms,
                    seen_count=state.seen_count,
                    confirmed=True,
                    top_conf=prev_top_conf,
                    best_bbox=prev_best_bbox,
                    end_ts_unix_ms=None,
                )
                events.append(
                    self._event(
                        event="update",
                        ts_unix_ms=int(ts_unix_ms),
                        before=self._summary(before_state),
                        after=self._summary(state),
                    )
                )

        for track_id in sorted(self._tracks):
            state = self._tracks.get(track_id)
            if state is None:
                continue
            if track_id in current_by_id:
                continue
            if state.end_ts_unix_ms is not None:
                continue
            if not state.confirmed:
                self._tracks.pop(track_id, None)
                continue

            if int(ts_unix_ms) - int(state.last_seen_ts_unix_ms) < self.end_after_ms:
                continue

            before_summary = self._summary(state)
            state.end_ts_unix_ms = int(ts_unix_ms)
            after_summary = self._summary(state)
            events.append(
                self._event(
                    event="end",
                    ts_unix_ms=int(ts_unix_ms),
                    before=before_summary,
                    after=after_summary,
                )
            )
            self._tracks.pop(track_id, None)

        return events
