from __future__ import annotations

from src.analytics.events import TrackLifecycle


def test_track_event_lifecycle_confirm_update_end() -> None:
    lifecycle = TrackLifecycle(
        session_id="sess_01",
        camera_id="cam_01",
        confirm_after=2,
        end_after_ms=0,
    )

    # First sighting: not confirmed yet -> no event.
    events = lifecycle.update(
        tracks=[
            {
                "id": 17,
                "label": "drone",
                "conf": 0.5,
                "bbox": {"x": 0.1, "y": 0.2, "w": 0.1, "h": 0.1},
            }
        ],
        ts_unix_ms=1000,
    )
    assert events == []

    # Second sighting: becomes confirmed -> emits "new".
    events = lifecycle.update(
        tracks=[
            {
                "id": 17,
                "label": "drone",
                "conf": 0.6,
                "bbox": {"x": 0.1, "y": 0.2, "w": 0.1, "h": 0.1},
            }
        ],
        ts_unix_ms=1100,
    )
    assert len(events) == 1
    assert events[0]["type"] == "track_event"
    assert events[0]["event"] == "new"
    assert events[0]["before"] is None
    assert events[0]["after"]["id"] == 17
    assert events[0]["after"]["confirmed"] is True
    assert events[0]["after"]["start_ts_unix_ms"] == 1000
    assert events[0]["after"]["end_ts_unix_ms"] is None
    assert events[0]["after"]["top_conf"] == 0.6

    # Confidence increases: emits "update" with before/after top_conf.
    events = lifecycle.update(
        tracks=[
            {
                "id": 17,
                "label": "drone",
                "conf": 0.9,
                "bbox": {"x": 0.2, "y": 0.2, "w": 0.1, "h": 0.1},
            }
        ],
        ts_unix_ms=1200,
    )
    assert len(events) == 1
    assert events[0]["event"] == "update"
    assert events[0]["before"] is not None
    assert events[0]["before"]["top_conf"] == 0.6
    assert events[0]["after"]["top_conf"] == 0.9

    # Track disappears: with end_after_ms=0 it ends immediately -> emits "end".
    events = lifecycle.update(tracks=[], ts_unix_ms=1300)
    assert len(events) == 1
    assert events[0]["event"] == "end"
    assert events[0]["before"] is not None
    assert events[0]["before"]["end_ts_unix_ms"] is None
    assert events[0]["after"]["end_ts_unix_ms"] == 1300
