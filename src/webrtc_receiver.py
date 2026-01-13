"""Simple WebRTC receiver that accepts an incoming browser WebRTC video stream
and injects frames into the application's frame queue.

Usage:
    from src.webrtc_receiver import start_webrtc_server
    start_webrtc_server(frame_queue, stop_event, host='0.0.0.0', port=8889, path='/camera_1')

Client (browser) will connect to `http://host:port/camera_1/` and POST an SDP offer
to `/camera_1/offer`. The server replies with an SDP answer and then receives
video frames which are converted to BGR numpy arrays and put into `frame_queue`.
"""

from __future__ import annotations

import asyncio
import logging
import threading

try:
    import av  # type: ignore
    from aiortc import RTCPeerConnection, RTCSessionDescription  # type: ignore

    _HAS_MEDIA_LIBS = True
except Exception:  # pragma: no cover - best-effort import handling
    av = None  # type: ignore
    RTCPeerConnection = None  # type: ignore
    RTCSessionDescription = None  # type: ignore
    _HAS_MEDIA_LIBS = False

from aiohttp import web
import time

logger = logging.getLogger(__name__)

# Simple HTML client that receives a remote video track via WebRTC.
HTML_PAGE = """<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Camera 1 - WebRTC Receive</title>
  </head>
  <body>
    <h1>WebRTC Output: Receive server video</h1>
    <video id="remote" autoplay playsinline controls style="width:640px;height:360px;"></video>
    <p>
      <button id="start">Start</button>
      <button id="stop">Stop</button>
    </p>
    <script>
      let pc;
      document.getElementById('start').onclick = async () => {
        pc = new RTCPeerConnection();
        pc.ontrack = (event) => {
          const [stream] = event.streams;
          document.getElementById('remote').srcObject = stream;
        };
        // Ask to receive video
        pc.addTransceiver('video', { direction: 'recvonly' });
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        const resp = await fetch(window.location.pathname + 'offer', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ sdp: offer.sdp, type: offer.type })
        });
        const answer = await resp.json();
        await pc.setRemoteDescription({ sdp: answer.sdp, type: answer.type });
        pc.onconnectionstatechange = () => console.log('pc state', pc.connectionState);
      };
      document.getElementById('stop').onclick = () => {
        if (pc) { pc.close(); pc = null; }
        document.getElementById('remote').srcObject = null;
      };
    </script>
  </body>
</html>
"""


from aiortc import VideoStreamTrack


class QueueVideoTrack(VideoStreamTrack):
    """Video track that pulls frames from a thread-safe queue (OpenCV BGR numpy arrays)."""

    def __init__(
        self, frame_queue: "queue.Queue", width: int, height: int, fps: int = 30
    ):
        super().__init__()  # don't forget to call the parent constructor
        self.queue = frame_queue
        self.width = width
        self.height = height
        self.fps = max(1, int(fps))
        self._frame_time = 1.0 / self.fps
        self._last_pts = 0

    async def recv(self):
        # Wait for next frame from the blocking queue in a thread pool
        loop = asyncio.get_event_loop()
        try:
            img = await loop.run_in_executor(None, self.queue.get)
        except Exception:
            # if queue get fails for any reason, wait a bit and raise
            await asyncio.sleep(self._frame_time)
            raise

        # Convert numpy bgr to av.VideoFrame
        try:
            video_frame = av.VideoFrame.from_ndarray(img, format="bgr24")
        except Exception:
            # fallback: small blank frame
            video_frame = av.VideoFrame(
                width=self.width, height=self.height, format="bgr24"
            )

        # Reformat to yuv420p for better browser compatibility
        video_frame = video_frame.reformat(self.width, self.height, format="yuv420p")

        # PTS and time_base
        self._last_pts += 1
        video_frame.pts = self._last_pts
        video_frame.time_base = av.Rational(1, self.fps)

        return video_frame


def _make_app(
    frame_queue: "queue.Queue",
    path: str = "/camera_1/",
    width: int = 1280,
    height: int = 720,
    fps: int = 30,
) -> web.Application:
    app = web.Application()

    async def index(request: web.Request) -> web.Response:
        return web.Response(text=HTML_PAGE, content_type="text/html")

    async def offer(request: web.Request) -> web.Response:
        """Handle incoming SDP offer from browser and reply with answer (server sends video)."""
        params = await request.json()
        sdp = params.get("sdp")
        typ = params.get("type")
        if not sdp or not typ:
            return web.Response(status=400, text="Missing sdp/type")

        if not _HAS_MEDIA_LIBS:
            return web.Response(
                status=503, text="Server missing aiortc/av dependencies"
            )

        pc = RTCPeerConnection()
        pcs = request.app.setdefault("pcs", set())
        pcs.add(pc)

        # Add outbound video track backed by our frame queue
        track = QueueVideoTrack(frame_queue, width=width, height=height, fps=fps)
        pc.addTrack(track)

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            logger.info("PC connection state: %s", pc.connectionState)
            if pc.connectionState in ("failed", "closed", "disconnected"):
                await pc.close()
                pcs.discard(pc)

        # Apply remote description
        offer = RTCSessionDescription(sdp=sdp, type=typ)
        await pc.setRemoteDescription(offer)

        # Create answer
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        return web.json_response(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        )

    app.router.add_get(path, index)
    app.router.add_post(path + "offer", offer)
    return app


def _run_app(
    loop: asyncio.AbstractEventLoop, app: web.Application, host: str, port: int
) -> None:
    asyncio.set_event_loop(loop)

    async def runner():
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host=host, port=port)
        await site.start()

        # keep running until loop is stopped
        while True:
            await asyncio.sleep(3600)

    loop.run_until_complete(runner())


def start_webrtc_server(
    frame_queue: "queue.Queue",
    stop_event: threading.Event,
    host: str = "0.0.0.0",
    port: int = 8889,
    path: str = "/camera_1/",
) -> threading.Thread:
    """Start the aiohttp + aiortc WebRTC receiver in a background thread.

    Returns the Thread object so the caller can join/stop if needed.
    """
    loop = asyncio.new_event_loop()
    app = _make_app(frame_queue, path=path)

    t = threading.Thread(target=_run_app, args=(loop, app, host, port), daemon=True)
    t.start()
    logger.info("WebRTC server started at http://%s:%s%s", host, port, path)

    # stop_event currently not wired to gracefully shutdown the aiohttp loop;
    # caller may stop process to terminate. For a more graceful shutdown, we
    # could set up loop.call_soon_threadsafe to cancel tasks when stop_event is set.
    return t


if __name__ == "__main__":
    import queue

    q = queue.Queue(maxsize=1)
    ev = threading.Event()
    start_webrtc_server(q, ev)
    print("Server running, press Ctrl+C to stop")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass
