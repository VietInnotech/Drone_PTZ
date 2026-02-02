"""WebRTC client that connects to an existing WebRTC *server* endpoint
(e.g. http://localhost:8889/camera_1/offer), receives the remote video track
and pushes frames into the application's frame queue for OpenCV processing.

Usage:
    from src.webrtc_client import start_webrtc_client
    start_webrtc_client(frame_queue, stop_event, url='http://localhost:8889/camera_1/offer')
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
from typing import Optional

import aiohttp
from aiortc import RTCPeerConnection, RTCSessionDescription

logger = logging.getLogger(__name__)


class H264InitializationFilter(logging.Filter):
    """Suppress expected H264 decoder errors during stream initialization.
    
    When a WebRTC client connects mid-stream, the H264 decoder receives frames
    before getting SPS/PPS (Sequence/Picture Parameter Sets) from a keyframe.
    This causes "Invalid data found when processing input" errors that are
    cosmetic and resolve automatically once a keyframe arrives (typically 1-2s).
    
    This filter suppresses these warnings during the initialization window to
    prevent log spam while preserving visibility of genuine decoding errors.
    """
    
    def __init__(self):
        super().__init__()
        self.connection_start_time = None
        self.initialization_window = 10.0  # Suppress warnings for first 10 seconds
        self.got_first_successful_frame = False
    
    def reset_for_new_connection(self):
        """Call when starting a new WebRTC connection."""
        self.connection_start_time = time.time()
        self.got_first_successful_frame = False
    
    def mark_successful_frame(self):
        """Call when first frame decodes successfully."""
        self.got_first_successful_frame = True
    
    def filter(self, record):
        """Return False to suppress the log record, True to allow it."""
        # Only filter H264 decoder warnings
        if (record.levelno == logging.WARNING and 
            "H264Decoder() failed to decode" in record.getMessage() and
            "Invalid data found when processing input" in record.getMessage()):
            
            # If we're in initialization window, suppress the warning
            if self.connection_start_time is not None:
                elapsed = time.time() - self.connection_start_time
                if elapsed < self.initialization_window and not self.got_first_successful_frame:
                    # Suppress during initialization
                    return False
        
        # Allow all other log messages
        return True


# Install filter on aiortc's H264 codec logger
_h264_filter = H264InitializationFilter()
logging.getLogger("aiortc.codecs.h264").addFilter(_h264_filter)

logger = logging.getLogger(__name__)


async def _single_session(
    frame_queue,
    url: str,
    stop_event: threading.Event,
    width: int,
    height: int,
    fps: int,
) -> None:
    """Create a single RTC session and receive remote video frames into the queue."""
    # Reset filter for this new connection
    _h264_filter.reset_for_new_connection()
    
    pc = RTCPeerConnection()

    # add a recv-only transceiver for video
    pc.addTransceiver("video", direction="recvonly")

    # parse helper to extract offer data (ice ufrag/pwd and media lines)
    def _parse_offer(sdp: str) -> dict:
        od = {"iceUfrag": "", "icePwd": "", "medias": []}
        for line in sdp.split("\r\n"):
            if line.startswith("m="):
                od["medias"].append(line[2:])
            elif od["iceUfrag"] == "" and line.startswith("a=ice-ufrag:"):
                od["iceUfrag"] = line.split(":", 1)[1]
            elif od["icePwd"] == "" and line.startswith("a=ice-pwd:"):
                od["icePwd"] = line.split(":", 1)[1]
        return od

    def _generate_sdp_fragment(od: dict, candidates: list) -> str:
        candidates_by_media = {}
        for c in candidates:
            mid = getattr(c, "sdpMLineIndex", None)
            if mid is None:
                mid = 0
            candidates_by_media.setdefault(mid, []).append(c)

        frag = (
            f"a=ice-ufrag:{od.get('iceUfrag', '')}\r\n"
            + f"a=ice-pwd:{od.get('icePwd', '')}\r\n"
        )
        mid = 0
        for media in od.get("medias", []):
            if mid in candidates_by_media:
                frag += f"m={media}\r\n" + f"a=mid:{mid}\r\n"
                for cand in candidates_by_media[mid]:
                    frag += f"a={cand.candidate}\r\n"
            mid += 1
        return frag

    queued_candidates = []
    session_url_ref = {"url": None}

    @pc.on("icecandidate")
    def on_ice(event):
        cand = event.candidate
        if cand is None:
            return
        logger.debug("Local ICE candidate generated: %s", cand)
        queued_candidates.append(cand)

        # if session_url is available, send immediately
        if session_url_ref["url"] is not None:

            async def _send():
                try:
                    frag = _generate_sdp_fragment(offer_data, queued_candidates)
                    queued_candidates.clear()
                    headers = {
                        "Content-Type": "application/trickle-ice-sdpfrag",
                        "If-Match": "*",
                    }
                    async with aiohttp.ClientSession() as sess:
                        async with sess.patch(
                            session_url_ref["url"], data=frag, headers=headers
                        ) as presp:
                            logger.info(
                                "PATCH %s -> %s", session_url_ref["url"], presp.status
                            )
                except Exception as exc:
                    logger.debug("Failed to send candidates: %s", exc)

            asyncio.ensure_future(_send())

    @pc.on("track")
    def on_track(track):
        logger.info("Remote track received: kind=%s", track.kind)

        if track.kind != "video":
            return

        async def recv_loop() -> None:
            """Receive frames from the track and push to queue.
            
            Note: H264 decoding happens at the aiortc codec layer before track.recv().
            Frames that fail codec-level decode due to missing SPS/PPS will not reach
            this code - they're filtered out by the decoder. The H264InitializationFilter
            suppresses these expected warnings during the initialization period.
            """
            while True:
                try:
                    frame = await track.recv()  # av.VideoFrame (already decoded)
                except Exception as exc:
                    logger.info("Track receive ended: %s", exc)
                    break

                try:
                    # Convert frame to numpy array for OpenCV
                    try:
                        img = frame.to_ndarray(format="bgr24")
                        # Mark that we successfully decoded a frame
                        if not _h264_filter.got_first_successful_frame:
                            _h264_filter.mark_successful_frame()
                            logger.info("First frame decoded successfully, H264 decoder initialized")
                    except Exception as nd_exc:
                        logger.warning(f"Frame to ndarray failed: {nd_exc}")
                        # Fallback conversion
                        img = frame.to_image().convert("RGB")
                        import numpy as np
                        img = np.array(img)[:, :, ::-1].copy()  # Convert RGB to BGR

                    # Best-effort non-blocking queue put (replace old frame if queue full)
                    try:
                        frame_queue.get_nowait()
                    except Exception:
                        pass
                    
                    frame_queue.put_nowait(img)
                    
                except Exception as frame_exc:
                    logger.error(f"Error processing frame: {frame_exc}")
                    continue

        asyncio.ensure_future(recv_loop())

    try:
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)
        # parse offer data for candidate fragments
        offer_data = _parse_offer(pc.localDescription.sdp)

        # If the url ends with '/', try to append 'offer'
        post_url = url
        if post_url.endswith("/"):
            post_url = post_url + "offer"

        logger.info("Posting SDP offer to %s (WHEP or /offer fallback)", url)
        data = None
        session_url: Optional[str] = None
        async with aiohttp.ClientSession() as sess:
            # First, try WHEP-style POST to the base url with Content-Type: application/sdp
            try:
                # Common MediaMTX pattern: POST to <stream>/whep
                candidates_whep = [
                    url.rstrip("/") + "/whep",
                    url.rstrip("/") + "/whep/",
                ]
                for wh_url in candidates_whep:
                    try:
                        logger.debug("Attempting WHEP POST to %s", wh_url)
                        async with sess.post(
                            wh_url,
                            data=pc.localDescription.sdp,
                            headers={"Content-Type": "application/sdp"},
                        ) as resp:
                            text = await resp.text()
                            logger.info(
                                "WHEP POST %s -> status=%s len=%d",
                                wh_url,
                                resp.status,
                                len(text) if text is not None else 0,
                            )
                            if resp.status == 201:
                                session_url = resp.headers.get("location")
                                data = {"sdp": text, "type": "answer"}
                                break
                    except Exception as exc:
                        logger.debug("WHEP POST to %s failed: %s", wh_url, exc)
                # if not found, try posting to the base URL as a fallback
                if data is None:
                    wh_url = url.rstrip("/")
                    logger.debug("Attempting WHEP POST to base %s", wh_url)
                    async with sess.post(
                        wh_url,
                        data=pc.localDescription.sdp,
                        headers={"Content-Type": "application/sdp"},
                    ) as resp:
                        text = await resp.text()
                        logger.info(
                            "WHEP POST %s -> status=%s len=%d",
                            wh_url,
                            resp.status,
                            len(text) if text is not None else 0,
                        )
                        if resp.status == 201:
                            session_url = resp.headers.get("location")
                            data = {"sdp": text, "type": "answer"}
            except Exception as exc:
                logger.debug("WHEP POST failed: %s", exc)

            # If WHEP didn't succeed, try legacy /offer JSON endpoints as fallback
            if data is None:
                tried = []
                for candidate in (
                    post_url,
                    url.rstrip("/") + "/offer",
                    url + "offer",
                    url.rstrip("/"),
                ):
                    if candidate in tried:
                        continue
                    tried.append(candidate)
                    try:
                        logger.debug("Attempting JSON POST to %s", candidate)
                        async with sess.post(
                            candidate,
                            json={
                                "sdp": pc.localDescription.sdp,
                                "type": pc.localDescription.type,
                            },
                        ) as resp:
                            text = await resp.text()
                            logger.info(
                                "JSON POST %s -> status=%s len=%d",
                                candidate,
                                resp.status,
                                len(text) if text is not None else 0,
                            )
                            if resp.status == 200:
                                try:
                                    data = json.loads(text)
                                except Exception:
                                    data = await resp.json()
                                break
                            else:
                                continue
                    except Exception as exc:
                        logger.debug("POST to %s failed: %s", candidate, exc)
                        continue
                else:
                    raise RuntimeError(
                        f"Failed to POST offer to any candidate URLs: {tried}"
                    )

        if "sdp" not in data or "type" not in data:
            raise RuntimeError(f"Invalid answer from server: {data}")

        # If WHEP created a session, convert relative Location to absolute
        if session_url is not None:
            from urllib.parse import urljoin

            session_url_abs = urljoin(url, session_url)
            session_url_ref["url"] = session_url_abs
            logger.info("WHEP session established: %s", session_url_abs)

            # send any queued candidates immediately
            if queued_candidates:
                try:
                    frag = _generate_sdp_fragment(offer_data, queued_candidates)
                    queued_candidates.clear()
                    headers = {
                        "Content-Type": "application/trickle-ice-sdpfrag",
                        "If-Match": "*",
                    }
                    async with aiohttp.ClientSession() as sess:
                        async with sess.patch(
                            session_url_ref["url"], data=frag, headers=headers
                        ) as presp:
                            logger.info(
                                "Initial PATCH %s -> %s",
                                session_url_ref["url"],
                                presp.status,
                            )
                except Exception as exc:
                    logger.debug("Failed to send initial candidates: %s", exc)

        answer = RTCSessionDescription(sdp=data["sdp"], type=data["type"])
        logger.debug("Server SDP Answer: %s", answer.sdp)
        logger.info("Setting remote description from server answer")
        await pc.setRemoteDescription(answer)

        @pc.on("connectionstatechange")
        def _on_statechange():
            logger.info("PeerConnection state changed: %s", pc.connectionState)

        # Wait until stop_event is set or connection closes
        idle_since = time.time()
        while not stop_event.is_set():
            if pc.connectionState in ("failed", "closed", "disconnected"):
                logger.info("PC connection state changed to %s", pc.connectionState)
                break
            # If no frames arrive for a while, log an info message (helps debugging)
            if time.time() - idle_since > 5.0:
                logger.debug("No frames received yet (still waiting)...")
                idle_since = time.time()
            await asyncio.sleep(0.5)

    finally:
        try:
            await pc.close()
        except Exception:
            pass


async def _run_client_loop(
    frame_queue,
    stop_event: threading.Event,
    url: str,
    width: int,
    height: int,
    fps: int,
):
    """Persistent runner that reconnects on failures until stop_event is set."""
    backoff = 1.0
    while not stop_event.is_set():
        try:
            await _single_session(frame_queue, url, stop_event, width, height, fps)
            backoff = 1.0
        except Exception as exc:  # pragma: no cover - best-effort runtime behaviour
            logger.exception("WebRTC client session failed: %s", exc)
            # exponential backoff with cap
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30.0)


def _run_thread(
    frame_queue,
    stop_event: threading.Event,
    url: str,
    width: int,
    height: int,
    fps: int,
) -> None:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(
            _run_client_loop(frame_queue, stop_event, url, width, height, fps)
        )
    finally:
        # close pending tasks
        tasks = [t for t in asyncio.all_tasks(loop) if not t.done()]
        for t in tasks:
            t.cancel()
        
        # Wait a bit for cancellations to propagate
        if tasks:
            try:
                loop.run_until_complete(asyncio.wait(tasks, timeout=1.0))
            except Exception:
                pass
                
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
        logger.info("WebRTC client event loop closed")


def start_webrtc_client(
    frame_queue,
    stop_event: threading.Event,
    url: str = "http://localhost:8889/camera_1/",
    width: int = 1280,
    height: int = 720,
    fps: int = 30,
) -> threading.Thread:
    """Start the WebRTC client runner in a background thread.

    The provided `url` should point to the server-side page or directly to its
    offer endpoint. If the url ends with '/', this function will POST to
    `url + 'offer'` automatically.
    """
    t = threading.Thread(
        target=_run_thread,
        args=(frame_queue, stop_event, url, width, height, fps),
        daemon=True,
    )
    t.start()
    logger.info("WebRTC client started connecting to %s", url)
    return t


if __name__ == "__main__":
    import queue

    q = queue.Queue(maxsize=1)
    ev = threading.Event()
    start_webrtc_client(q, ev)
    print("Client running, press Ctrl+C to stop")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        ev.set()
        print("Stopping...")
