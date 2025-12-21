"""Analytics domain modules (metadata-first backend).

Phase 1 extracts testable, side-effect-free builders for the metadata contract so the
runtime loop can emit structured messages (WebSocket/MQTT later) without being coupled to UI.
"""

from __future__ import annotations

from src.analytics.engine import AnalyticsEngine
from src.analytics.metadata import MetadataBuilder

__all__ = [
    "AnalyticsEngine",
    "MetadataBuilder",
]
