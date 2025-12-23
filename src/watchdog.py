"""
Lightweight watchdog utility for detecting stalled loops.

Starts a background thread that triggers a callback if not fed within
`timeout_s`. Intended for guarding the main control loop.
"""

from __future__ import annotations

import threading
import time
from typing import Callable


class Watchdog:
    """Background watchdog timer.

    The watchdog runs in a daemon thread and invokes `on_timeout` if no feed
    occurs within `timeout_s`. Feeding updates the internal timer. Calling
    `stop()` terminates the thread gracefully.
    """

    def __init__(
        self,
        *,
        timeout_s: float,
        on_timeout: Callable[[], None],
        name: str = "watchdog",
        poll_interval_s: float | None = None,
    ) -> None:
        self.timeout_s = float(timeout_s)
        self.on_timeout = on_timeout
        self._poll_interval_s = poll_interval_s or max(0.05, timeout_s / 5)
        self._last_feed = time.monotonic()
        self._stop_event = threading.Event()
        self._triggered = threading.Event()
        self._thread = threading.Thread(target=self._run, name=name, daemon=True)

    def start(self) -> None:
        """Start watchdog monitoring."""
        if not self._thread.is_alive():
            self._thread.start()

    def feed(self) -> None:
        """Reset watchdog timer."""
        self._last_feed = time.monotonic()

    def stop(self, timeout: float | None = 1.0) -> None:
        """Stop watchdog and wait for thread to finish."""
        self._stop_event.set()
        if self._thread.is_alive():
            self._thread.join(timeout=timeout)

    @property
    def triggered(self) -> bool:
        """Return True if the watchdog has fired."""
        return self._triggered.is_set()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            now = time.monotonic()
            if (now - self._last_feed) >= self.timeout_s:
                # Fire once per timeout cycle
                if not self._triggered.is_set():
                    self._triggered.set()
                    try:
                        self.on_timeout()
                    finally:
                        # After firing once, continue monitoring unless stopped
                        self._last_feed = now
                # Avoid tight loop when triggered
                time.sleep(self._poll_interval_s)
                continue

            time.sleep(self._poll_interval_s)
