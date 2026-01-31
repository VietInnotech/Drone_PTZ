from __future__ import annotations

import aiohttp
from dataclasses import dataclass
from typing import Any
from loguru import logger


@dataclass(slots=True)
class SkyShieldCamera:
    id: int
    ip_camera: str
    live_view: str  # RTSP URL
    has_credentials: bool
    model_number: str | None = None


async def fetch_camera_list(base_url: str) -> list[SkyShieldCamera]:
    """
    Fetch the list of registered cameras from SkyShield server.
    
    Args:
        base_url: Base URL of the SkyShield server (e.g. http://localhost:3000)
        
    Returns:
        List of SkyShieldCamera objects.
    """
    url = f"{base_url.rstrip('/')}/db/camera/list"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5.0) as response:
                if response.status != 200:
                    logger.error(f"SkyShield API error: {response.status}")
                    return []
                
                payload = await response.json()
                if not payload.get("success"):
                    logger.error(f"SkyShield API returned success=False: {payload.get('message')}")
                    return []
                
                data = payload.get("data", [])
                cameras = []
                for item in data:
                    cameras.append(SkyShieldCamera(
                        id=item["id"],
                        ip_camera=item["ip_camera"],
                        live_view=item["live_view"],
                        has_credentials=item.get("has_credentials", False),
                        model_number=item.get("model_number")
                    ))
                return cameras
    except Exception as exc:
        logger.error(f"Failed to fetch camera list from SkyShield: {exc}")
        return []
