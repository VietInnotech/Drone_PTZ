from pathlib import Path

from src.api.session import ThreadedAnalyticsSession
from src.settings import load_settings


def test_threaded_analytics_session_initializes(tmp_path: Path) -> None:
    settings = load_settings(tmp_path / "missing.yaml")

    session = ThreadedAnalyticsSession(
        session_id="sess_01",
        camera_id="cam_01",
        settings=settings,
    )

    assert session.is_running() is False
    assert session.get_latest_tick() is None
    assert session.get_status() == {
        "running": False,
        "selected_target_id": None,
        "tracking_phase": "idle",
        "last_tick_ts_unix_ms": None,
    }
