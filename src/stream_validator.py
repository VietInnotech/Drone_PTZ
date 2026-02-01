"""
Stream validation utilities for MediaMTX and other RTSP/WebRTC streams.

Provides proactive validation to catch stream availability issues before
attempting connection, improving error messages and user experience.
"""

from __future__ import annotations

import asyncio
from urllib.parse import urlparse
from typing import Tuple

import aiohttp
from loguru import logger


async def validate_mediamtx_stream(url: str, timeout: float = 5.0) -> Tuple[bool, str]:
    """Validate that a MediaMTX WebRTC stream is accessible.
    
    Args:
        url: MediaMTX stream URL (e.g., http://localhost:8889/camera_1/)
        timeout: Connection timeout in seconds
        
    Returns:
        Tuple of (is_valid, message) where message explains the result
    """
    if not url:
        return False, "No URL provided"
        
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False, f"Invalid URL format: {url}"
            
        # MediaMTX exposes a health/status endpoint
        # Try to reach the WHEP endpoint which is used for WebRTC
        whep_url = url.rstrip("/") + "/whep"
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            # First check if the base URL is reachable
            try:
                async with session.options(whep_url) as response:
                    # OPTIONS request to WHEP should return 200 or 204
                    if response.status in (200, 204, 405):  # 405 means endpoint exists but OPTIONS not allowed
                        return True, f"Stream accessible at {url}"
            except aiohttp.ClientError:
                pass
                
            # Fallback: check if the MediaMTX API reports the path exists
            api_base = f"{parsed.scheme}://{parsed.netloc}"
            paths_url = f"{api_base}/v3/paths/list"
            
            try:
                async with session.get(paths_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Extract stream name from URL path
                        stream_name = parsed.path.strip("/").split("/")[0] if parsed.path else None
                        if stream_name and "items" in data:
                            for item in data.get("items", []):
                                if item.get("name") == stream_name:
                                    return True, f"Stream '{stream_name}' found in MediaMTX"
                            return False, f"Stream '{stream_name}' not found in MediaMTX. Available: {[i.get('name') for i in data.get('items', [])]}"
                        return True, "MediaMTX API accessible"
            except aiohttp.ClientError:
                pass
                
            # Final fallback: just check if the host is reachable
            try:
                async with session.head(url) as response:
                    if response.status < 500:
                        return True, f"Host reachable at {parsed.netloc}"
            except aiohttp.ClientError as e:
                return False, f"Cannot reach host: {e}"
                    
        return False, f"Stream validation failed for {url}"
        
    except Exception as e:
        logger.warning(f"Stream validation error for {url}: {e}")
        return False, f"Validation error: {str(e)}"


async def validate_rtsp_stream(url: str, timeout: float = 5.0) -> Tuple[bool, str]:
    """Validate that an RTSP stream URL is properly formatted.
    
    Note: Full RTSP validation would require an RTSP client.
    This performs basic URL format validation.
    
    Args:
        url: RTSP URL (e.g., rtsp://192.168.1.80:554/stream1)
        timeout: Not used for format validation
        
    Returns:
        Tuple of (is_valid, message)
    """
    if not url:
        return False, "No URL provided"
        
    try:
        parsed = urlparse(url)
        
        if parsed.scheme not in ("rtsp", "rtsps"):
            return False, f"Invalid scheme '{parsed.scheme}', expected 'rtsp' or 'rtsps'"
            
        if not parsed.netloc:
            return False, "Missing host in RTSP URL"
            
        # Check for common port
        port = parsed.port or 554
        if port < 1 or port > 65535:
            return False, f"Invalid port: {port}"
            
        return True, f"RTSP URL format valid: {parsed.netloc}"
        
    except Exception as e:
        return False, f"URL parse error: {str(e)}"


def get_stream_name_from_url(url: str) -> str | None:
    """Extract stream name from MediaMTX URL.
    
    Args:
        url: MediaMTX URL like http://localhost:8889/camera_1/
        
    Returns:
        Stream name like 'camera_1' or None if not extractable
    """
    try:
        parsed = urlparse(url)
        # Must have a valid HTTP scheme for MediaMTX URLs
        if not parsed.scheme or parsed.scheme not in ("http", "https"):
            return None
        if not parsed.netloc:
            return None
        parts = [p for p in parsed.path.split("/") if p]
        return parts[0] if parts else None
    except Exception:
        return None
