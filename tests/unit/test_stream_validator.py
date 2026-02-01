"""
Unit tests for stream_validator module.
"""

import asyncio
import pytest
from src.stream_validator import (
    get_stream_name_from_url,
    validate_rtsp_stream,
)


class TestGetStreamNameFromUrl:
    """Tests for get_stream_name_from_url function."""

    def test_basic_mediamtx_url(self):
        """Test extracting stream name from standard MediaMTX URL."""
        url = "http://localhost:8889/camera_1/"
        assert get_stream_name_from_url(url) == "camera_1"

    def test_mediamtx_url_without_trailing_slash(self):
        """Test URL without trailing slash."""
        url = "http://localhost:8889/camera_2"
        assert get_stream_name_from_url(url) == "camera_2"

    def test_mediamtx_url_with_subpath(self):
        """Test URL with subpath."""
        url = "http://localhost:8889/stream/whep"
        assert get_stream_name_from_url(url) == "stream"

    def test_empty_path(self):
        """Test URL with empty path."""
        url = "http://localhost:8889/"
        assert get_stream_name_from_url(url) is None

    def test_invalid_url(self):
        """Test invalid URL returns None."""
        assert get_stream_name_from_url("not a url") is None


class TestValidateRtspStream:
    """Tests for validate_rtsp_stream function."""

    def test_valid_rtsp_url(self):
        """Test valid RTSP URL."""
        is_valid, message = asyncio.get_event_loop().run_until_complete(
            validate_rtsp_stream("rtsp://192.168.1.80:554/stream1")
        )
        assert is_valid is True
        assert "valid" in message.lower()

    def test_invalid_scheme(self):
        """Test URL with invalid scheme."""
        is_valid, message = asyncio.get_event_loop().run_until_complete(
            validate_rtsp_stream("http://192.168.1.80:554/stream1")
        )
        assert is_valid is False
        assert "scheme" in message.lower()

    def test_missing_host(self):
        """Test URL with missing host."""
        is_valid, message = asyncio.get_event_loop().run_until_complete(
            validate_rtsp_stream("rtsp://")
        )
        assert is_valid is False

    def test_empty_url(self):
        """Test empty URL."""
        is_valid, message = asyncio.get_event_loop().run_until_complete(
            validate_rtsp_stream("")
        )
        assert is_valid is False

    def test_rtsps_scheme(self):
        """Test RTSPS scheme is valid."""
        is_valid, message = asyncio.get_event_loop().run_until_complete(
            validate_rtsp_stream("rtsps://192.168.1.80:554/stream1")
        )
        assert is_valid is True
