"""Tests for Watchdog utility."""

import time

from src.watchdog import Watchdog


def test_watchdog_triggers_on_timeout():
    fired = []

    def on_timeout():
        fired.append(True)

    wd = Watchdog(timeout_s=0.1, on_timeout=on_timeout, poll_interval_s=0.02)
    wd.start()
    time.sleep(0.15)  # exceed timeout
    wd.stop()

    assert fired, "Watchdog should trigger when not fed"
    assert wd.triggered


def test_watchdog_feed_prevents_timeout():
    fired = []

    def on_timeout():
        fired.append(True)

    wd = Watchdog(timeout_s=0.2, on_timeout=on_timeout, poll_interval_s=0.02)
    wd.start()

    # Feed repeatedly to prevent timeout
    for _ in range(5):
        wd.feed()
        time.sleep(0.05)

    wd.stop()

    assert not fired, "Watchdog should not trigger when fed in time"
    assert not wd.triggered


def test_watchdog_stop_is_idempotent():
    fired = []

    def on_timeout():
        fired.append(True)

    wd = Watchdog(timeout_s=0.1, on_timeout=on_timeout, poll_interval_s=0.02)
    wd.start()
    wd.stop()
    wd.stop()  # calling stop twice should be safe

    assert not fired, "Watchdog should not fire after immediate stop"
    assert not wd.triggered
