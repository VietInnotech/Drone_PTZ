import json
from dataclasses import dataclass
from pathlib import Path

from src.analytics.metadata import MetadataBuilder, tracks_from_detections
from src.tracking.state import TrackerStatus, TrackingPhase


@dataclass(slots=True)
class DummyDet:
    id: int
    cls: int
    conf: float
    xyxy: list[list[float]]


@dataclass(slots=True)
class DummyPtz:
    control_mode: str = "onvif"
    active: bool = True
    last_pan: float = 0.12
    last_tilt: float = -0.03
    last_zoom: float = 0.44


def _load_fixture(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


class TestTracksFromDetections:
    def test_rounding_from_normalized_xyxy(self) -> None:
        det = DummyDet(
            id=17,
            cls=0,
            conf=0.83,
            # x2-x1 and y2-y1 would otherwise produce float noise without rounding.
            xyxy=[[0.42, 0.31, 0.5, 0.37]],
        )

        tracks = tracks_from_detections(
            [det], class_names=["drone"], frame_w=1280, frame_h=720
        )

        assert tracks == [
            {
                "id": 17,
                "label": "drone",
                "conf": 0.83,
                "bbox": {"x": 0.42, "y": 0.31, "w": 0.08, "h": 0.06},
            }
        ]


class TestMetadataBuilderFixtures:
    def test_metadata_tick_example_fixture(self) -> None:
        expected = _load_fixture("docs/fixtures/metadata_tick.example.json")

        det = DummyDet(id=17, cls=0, conf=0.83, xyxy=[[0.42, 0.31, 0.5, 0.37]])
        tracker_status = TrackerStatus(phase=TrackingPhase.TRACKING, target_id=17)

        builder = MetadataBuilder(
            session_id=expected["session_id"],
            camera_id=expected["camera_id"],
            space=expected["space"],
        )

        tick = builder.build_tick_from_detections(
            [det],
            frame_index=expected["frame_index"],
            frame_w=expected["frame_size"]["w"],
            frame_h=expected["frame_size"]["h"],
            class_names=["drone"],
            tracker_status=tracker_status,
            ptz=DummyPtz(),
            ts_unix_ms=expected["ts_unix_ms"],
            ts_mono_ms=expected["ts_mono_ms"],
        )

        assert tick == expected

    def test_metadata_tick_empty_fixture(self) -> None:
        expected = _load_fixture("docs/fixtures/metadata_tick.empty.example.json")

        tracker_status = TrackerStatus(phase=TrackingPhase.IDLE, target_id=None)

        builder = MetadataBuilder(
            session_id=expected["session_id"],
            camera_id=expected["camera_id"],
            space=expected["space"],
        )

        tick = builder.build_tick_from_detections(
            [],
            frame_index=expected["frame_index"],
            frame_w=expected["frame_size"]["w"],
            frame_h=expected["frame_size"]["h"],
            class_names=["drone"],
            tracker_status=tracker_status,
            ptz=DummyPtz(active=False, last_pan=0.0, last_tilt=0.0, last_zoom=0.0),
            ts_unix_ms=expected["ts_unix_ms"],
            ts_mono_ms=expected["ts_mono_ms"],
        )

        assert tick == expected
