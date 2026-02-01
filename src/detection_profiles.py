from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlparse

from src.settings import CameraSourceConfig, Settings

DetectionProfileId = Literal["visible", "thermal", "secondary"]


@dataclass(frozen=True, slots=True)
class DetectionProfile:
    profile_id: DetectionProfileId
    camera_id: str
    camera: CameraSourceConfig


def derive_camera_id(config: CameraSourceConfig) -> str:
    """Map a camera source config to the analytics camera_id used by the UI."""
    if config.source == "skyshield" and config.skyshield_camera_id is not None:
        return f"camera_{config.skyshield_camera_id}"

    if config.source == "webrtc" and config.webrtc_url:
        parsed = urlparse(config.webrtc_url)
        parts = [part for part in parsed.path.split("/") if part]
        if parts:
            return str(parts[-1])

    if config.source == "rtsp" and config.rtsp_url:
        return f"rtsp:{config.rtsp_url}"

    return f"local_{config.camera_index}"


def get_detection_profiles(settings: Settings) -> list[DetectionProfile]:
    profiles: list[DetectionProfile] = []
    if settings.visible_detection.enabled:
        profiles.append(
            DetectionProfile(
                profile_id="visible",
                camera_id=derive_camera_id(settings.visible_detection.camera),
                camera=settings.visible_detection.camera,
            )
        )
    if settings.thermal_detection.enabled:
        profiles.append(
            DetectionProfile(
                profile_id="thermal",
                camera_id=derive_camera_id(settings.thermal_detection.camera),
                camera=settings.thermal_detection.camera,
            )
        )
    if settings.secondary_detection.enabled:
        profiles.append(
            DetectionProfile(
                profile_id="secondary",
                camera_id=derive_camera_id(settings.secondary_detection.camera),
                camera=settings.secondary_detection.camera,
            )
        )
    return profiles


def resolve_profile(settings: Settings, camera_id: str) -> DetectionProfile | None:
    for profile in get_detection_profiles(settings):
        if profile.camera_id == camera_id:
            return profile
    return None


def settings_for_profile(settings: Settings, profile_id: DetectionProfileId) -> Settings:
    """Return a Settings copy that enables only the requested profile."""
    data = settings.model_dump(mode="python")
    for key in ("visible_detection", "thermal_detection", "secondary_detection"):
        if key in data:
            data[key]["enabled"] = False

    if profile_id == "visible":
        data["visible_detection"]["enabled"] = True
    elif profile_id == "thermal":
        data["thermal_detection"]["enabled"] = True
    elif profile_id == "secondary":
        data["secondary_detection"]["enabled"] = True
    else:
        raise ValueError(f"Unknown detection profile: {profile_id}")

    return Settings(**data)


def settings_without_detection(settings: Settings) -> Settings:
    """Return a Settings copy with all detection pipelines disabled."""
    data = settings.model_dump(mode="python")
    for key in ("visible_detection", "thermal_detection", "secondary_detection"):
        if key in data:
            data[key]["enabled"] = False
    return Settings(**data)
