from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.analytics.metadata import MetadataBuilder
from src.analytics.types import MetadataTick
from src.detection import DetectionService
from src.tracking.selector import select_by_id
from src.tracking.state import TrackerStatus, TrackingPhase


@dataclass(slots=True)
class AnalyticsEngine:
    """Analytics-only engine: frame in -> detections + structured metadata out.

    This class is intentionally side-effect free: it does not do UI, networking, or PTZ control.
    """

    detection: DetectionService
    metadata: MetadataBuilder
    tracker_status: TrackerStatus

    def infer(self, frame: Any) -> list[Any]:
        tracked_boxes = self.detection.detect(frame)
        return self.detection.filter_by_target_labels(tracked_boxes)

    def update_tracking(self, tracked_boxes: list[Any], *, now: float) -> Any | None:
        if self.tracker_status.target_id is None:
            self.tracker_status.phase = TrackingPhase.IDLE
            return None

        best_det = select_by_id(tracked_boxes, self.tracker_status.target_id)
        self.tracker_status.compute_phase(best_det is not None, now)
        return best_det

    def build_tick(
        self,
        tracked_boxes: list[Any],
        *,
        frame_index: int,
        frame_w: int,
        frame_h: int,
        class_names: list[str],
        ptz: Any | None,
        ts_unix_ms: int,
        ts_mono_ms: int | None = None,
    ) -> MetadataTick:
        return self.metadata.build_tick_from_detections(
            tracked_boxes,
            frame_index=frame_index,
            frame_w=frame_w,
            frame_h=frame_h,
            class_names=class_names,
            tracker_status=self.tracker_status,
            ptz=ptz,
            ts_unix_ms=ts_unix_ms,
            ts_mono_ms=ts_mono_ms,
        )
