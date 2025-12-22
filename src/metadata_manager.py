"""
Thread-safe manager for latest metadata tick.

Solves race condition issue where main thread and API threads
access LATEST_METADATA_TICK without synchronization.
"""

import threading
from typing import Any


class MetadataManager:
    """Thread-safe manager for latest metadata tick."""

    def __init__(self) -> None:
        """Initialize metadata manager with thread-safe storage."""
        self._lock = threading.RLock()
        self._latest_tick: dict[str, Any] | None = None

    def update(self, tick: dict[str, Any] | None) -> None:
        """
        Update metadata tick (called from main thread).

        Args:
            tick: Metadata dictionary to store.
        """
        with self._lock:
            self._latest_tick = tick

    def get(self) -> dict[str, Any] | None:
        """
        Get current metadata tick safely (safe for API threads).

        Returns a copy to prevent external mutation.

        Returns:
            Copy of latest metadata tick, or None if not available.
        """
        with self._lock:
            # Return a copy to prevent external mutation
            return dict(self._latest_tick) if self._latest_tick else None

    def get_value(self, key: str, default: Any = None) -> Any:
        """
        Get a single value from metadata safely.

        Args:
            key: Key to retrieve.
            default: Default value if key not found.

        Returns:
            Value associated with key, or default if not found.
        """
        with self._lock:
            if self._latest_tick is None:
                return default
            return self._latest_tick.get(key, default)
