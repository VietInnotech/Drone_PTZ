# Analytics-Only Backend Plan (Metadata + Control; Frontend Draws Overlays)

This document proposes a best-practice architecture for evolving this repo into an
analytics/controls backend that outputs **object/track metadata** (not rendered video),
while a web frontend renders the overlay on top of an existing live video stream.

It also outlines an incremental implementation plan that fits the current codebase
(`src/main.py` orchestration, `DetectionService`, `TrackerStatus`, PTZ services, typed
`Settings`).

## Executive Summary

- Split responsibilities into two planes:
  - **Media plane**: deliver video to the browser (typically WebRTC).
  - **Control + data plane**: deliver analytics metadata and accept commands (REST +
    WebSocket).
- This repo should primarily output:
  - stable track IDs, labels, confidences, bounding boxes, and system/PTZ state.
  - an API to set/clear the selected target ID (replacing the current keyboard input).
- Prefer sending **normalized bounding boxes** and rendering overlays in the browser:
  - lower backend bandwidth and CPU than “burned-in overlay video”
  - easy to change overlay look/UX without touching backend
  - works with any video transport

## Current Repo Fit (What You Already Have)

Key strengths that map well to an analytics backend:

- Deterministic processing loop with a low-latency “latest frame” queue:
  - `settings.performance.frame_queue_maxsize` defaults to 1
  - producer thread drops stale frames instead of accumulating lag
- Multiple ingest paths already exist:
  - camera index / RTSP via OpenCV (`cv2.VideoCapture`)
  - file playback (simulator video source)
  - WebRTC ingest via `src/webrtc_client.py` (aiortc + aiohttp)
- Analytics core already exists:
  - `src/detection.py`: YOLO detection + Ultralytics tracking (ByteTrack / BoTSORT)
  - `src/tracking/state.py`: `TrackerStatus` state machine
  - `src/tracking/selector.py`: `select_by_id`
- PTZ integration exists (real + simulator):
  - `src/ptz_controller.py` (ONVIF / Octagon)
  - `src/ptz_simulator.py`

What to remove from the “backend” path (keep for local debugging only):

- UI rendering (`cv2.imshow`) and keyboard-driven state changes (`cv2.waitKey`).
  Those become frontend responsibilities + API calls.

## Recommended Target Architecture

### Two-Plane Design (Best Practice)

1. **Media plane (video to browser)**
   - Camera/encoder → media server → browser player.
   - For interactive PTZ and “feels live” use cases, this is commonly WebRTC.

2. **Control + data plane (metadata and commands)**
   - Backend produces object/track metadata and accepts control commands:
     - select target ID
     - clear target
     - optional PTZ overrides/modes (manual vs auto)
   - Browser draws the overlay from metadata on top of the video element.

This separation is common in real-time computer vision systems because video and
metadata have different throughput/latency requirements and failure modes.

### Reference Implementation Pattern

- **Video**:
  - use an existing streaming server (e.g., MediaMTX) for camera ingest + WebRTC egress
    to the browser.
- **Backend**:
  - subscribe to the same camera source for inference (RTSP ingest is typical).
  - publish metadata to clients via WebSocket; accept commands via WebSocket/REST.

## Media Plane Options (Tradeoffs)

You can support multiple delivery modes, but it helps to pick one “primary” path.

### WebRTC (recommended for interactive control)

- Pros:
  - lowest practical end-to-end latency in browsers
  - widely supported by modern browsers
- Cons:
  - more moving parts than HLS (ICE, NAT traversal, TURN if needed)
  - needs a signaling mechanism (WHEP/WHIP simplify this a lot)

If you use MediaMTX:

- For reading in browsers without a custom web page, consider WHEP (HTTP-based egress
  signaling layer on top of WebRTC).
- For ingesting WebRTC into a server, consider WHIP.

### HLS / LL-HLS

- Pros:
  - simple to serve and cache; good for wide distribution
  - robust playback
- Cons:
  - latency is typically higher than WebRTC; can feel sluggish for PTZ

### MJPEG

- Pros:
  - simplest possible implementation
  - good for internal debugging / MVP
- Cons:
  - inefficient bandwidth (JPEG per frame)
  - limited scalability compared to WebRTC/HLS

## Metadata Contract (What This Repo Emits)

### Design goals

- **Browser-friendly**: JSON is fine initially.
- **Transport-agnostic**: metadata works regardless of video transport.
- **Stable coordinate space**: define what `bbox` refers to (critical).
- **Extensible**: include versioning and room for new fields.

### Recommended coordinate strategy

Always emit bounding boxes in one of these spaces (be explicit):

1. `space="source"`: coordinates refer to the original camera frame.
2. `space="processed"`: coordinates refer to the frame as processed by the model
   (e.g., resized, cropped, PTZ-sim viewport).

In this repo, if simulation crops/resizes frames, you must choose and document it.
For frontend overlays, `space="source"` is usually easiest if the browser video shows
the source frame. If the browser video shows a cropped PTZ view, `space="processed"`
may match better.

### Recommended bbox format

Use normalized floats to avoid frontend pixel math mismatches:

- `x`, `y`, `w`, `h` all in `[0.0..1.0]`
- `(x, y)` is top-left
- `w`, `h` are width/height

### Example: WebSocket “tick” message

```json
{
  "schema": "drone-ptz-metadata/1",
  "session_id": "cam-01",
  "ts_unix_ms": 1730000000123,
  "ts_mono_ms": 123456789,
  "frame_index": 9321,
  "space": "source",
  "frame_size": {"w": 1280, "h": 720},
  "selected_target_id": 17,
  "tracking_phase": "TRACKING",
  "ptz": {"pan": 0.12, "tilt": -0.03, "zoom": 0.44},
  "tracks": [
    {
      "id": 17,
      "label": "drone",
      "conf": 0.83,
      "bbox": {"x": 0.42, "y": 0.31, "w": 0.08, "h": 0.06},
      "velocity": {"x": 0.001, "y": -0.002}
    }
  ]
}
```

Notes:

- Include both `ts_unix_ms` (log correlation) and `ts_mono_ms` (ordering / drift-safe).
- `velocity` is optional; it helps frontend smoothing/prediction.
- If you want to reduce bandwidth: send at 10–15 Hz, and/or send deltas.

## Control Plane API (What the Frontend Calls)

### Session lifecycle (REST)

- `GET /cameras`
  - list known cameras/sources (static config or dynamic discovery)
- `POST /sessions`
  - start analytics for a specific `camera_id` and return a `session_id`
- `GET /sessions/{session_id}`
  - health/status: FPS, processing latency, last frame timestamp
- `DELETE /sessions/{session_id}`
  - stop analytics

### Realtime metadata + commands (WebSocket)

Use one WebSocket per session:

- `GET /ws/sessions/{session_id}`
  - server → client: `metadata_tick` messages
  - client → server: commands

Example command messages:

```json
{"type": "set_target_id", "target_id": 17}
```

```json
{"type": "clear_target"}
```

```json
{"type": "set_mode", "mode": "auto"}  // or "manual"
```

Why WebSocket:

- metadata is server-push, low-latency
- commands are bidirectional
- single connection for the session simplifies browser integration

Alternative (when you only need server → client):

- SSE can be simpler than WebSocket for one-way telemetry, but it won’t cover commands
  unless you add separate REST endpoints.

## Frontend Overlay Rendering (Recommended Approach)

Typical browser approach:

- Play the video in a `<video>` element.
- Render overlays in a `<canvas>` layered on top (absolute positioning).
- Subscribe to metadata via WebSocket.
- On each animation frame:
  - draw boxes/labels using the latest metadata message
  - map normalized bbox → pixel coordinates using the canvas size

Important details:

- canvas size must match the displayed video size (handle DPR / resizing)
- define what “frame” the metadata corresponds to (source vs processed)
- for best UX, interpolate/smooth between ticks if you send metadata < video FPS

## Synchronization: Video vs Metadata

Perfect A/V sync is hard across separate transports; “good enough” is usually fine:

- emit timestamps with each metadata tick
- the frontend uses the latest tick <= current render time

If you need tighter sync:

- embed capture timestamps in the video pipeline (when possible)
- or send metadata over a WebRTC DataChannel and correlate it with the PeerConnection
  (more complex; usually not needed for overlays)

## Performance and Scaling Best Practices

### Don’t block on clients

- analytics loop should never wait on slow WebSocket clients
- use a publish/subscribe fanout:
  - per-session ring buffer of latest metadata
  - background broadcaster task writes to clients with timeouts

### Prefer “latest-state” semantics

- for low-latency dashboards, clients usually want the latest state, not every frame
- this matches your current “frame_queue_maxsize=1” approach

### Rate control

- consider output caps:
  - e.g., run inference at max available FPS but publish metadata at 10–15 Hz
  - or publish at inference FPS but with delta encoding

### Multi-session concurrency

- start with one process and N sessions using threads/async IO
- if you add multiple cameras and heavy inference:
  - consider one process per camera session (or a worker pool)
  - pin CPU affinity or use GPU scheduling as needed

## Security and Secrets

Immediate items to align with best practice:

- do not keep camera credentials in `config.yaml` in production
  - use environment variables or a secrets manager
- add authentication and authorization:
  - viewer vs controller roles
  - per-session access control
- rate limit PTZ commands and validate payloads (avoid “command spam”)
- consider CORS explicitly if you expose the API to browsers

## Observability

- add `/healthz` and `/readyz` endpoints
- emit metrics:
  - inference FPS, end-to-end processing time, dropped frames, active sessions
- structured logging with correlation IDs:
  - `session_id`, `camera_id`, request IDs

## Testing Strategy (TDD-friendly)

Keep tests deterministic (no real cameras, no network):

- unit tests:
  - bbox normalization, coordinate mapping rules (source vs processed)
  - message schema validation (pydantic/dataclasses)
  - selection logic (`select_by_id`) and tracking phase transitions
- integration tests:
  - feed synthetic frames to the pipeline and assert stable metadata output
  - mock PTZ backends to assert command issuance without real ONVIF/HTTP

## Implementation Roadmap (Incremental)

### Phase 0: Define the contract

- decide:
  - coordinate `space` emitted (`source` vs `processed`)
  - metadata tick rate target
  - what fields are required vs optional
- publish this contract for the frontend team (this doc + JSON schema file).

### Phase 1: Extract analytics core (no UI)

- refactor `src/main.py` into:
  - an “analytics engine” that accepts frames and emits structured metadata
  - a session state object (`selected_target_id`, `tracking_phase`, etc.)
- keep `cv2.imshow` only under a local debug flag/tool.

### Phase 2: Add backend API (sessions + WebSocket)

- implement:
  - session lifecycle endpoints
  - WebSocket for metadata + commands
- ensure:
  - analytics loop is never blocked by network IO
  - clean shutdown and resource cleanup per session

### Phase 3: Integrate with media server (recommended)

- standardize video distribution via a media server (e.g., MediaMTX):
  - browser uses WebRTC egress (WHEP)
  - backend ingests RTSP (or subscribes to the same source)
- ensure consistent coordinate space between browser video and backend metadata.

### Phase 4: Hardening

- authentication/authorization
- backpressure and rate limiting
- metrics and dashboards
- load testing with multiple sessions and multiple browser clients

## Online References (Best Practices and Examples)

Media plane (WebRTC signaling simplification):

- WHIP (WebRTC-HTTP Ingestion Protocol) RFC: https://www.rfc-editor.org/rfc/rfc9725
- WHEP (WebRTC-HTTP Egress Protocol) IETF draft: https://datatracker.ietf.org/doc/draft-ietf-wish-whep

Media server integration (practical docs):

- MediaMTX “Read a stream” docs (includes WebRTC/WHEP notes): https://mediamtx.org/docs/usage/read
- MediaMTX repository: https://github.com/bluenviron/mediamtx

Browser overlay rendering:

- MDN: manipulating video using canvas (video + canvas pipeline):\
  https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Manipulating_video_using_canvas

WebRTC advanced capabilities (optional):

- WebRTC Insertable Streams (overview): https://webrtc.org/getting-started/insertable-streams
- MDN: `RTCPeerConnection.insertableStreams`:\
  https://developer.mozilla.org/en-US/docs/Web/API/RTCPeerConnection/insertableStreams

Realtime protocol choice (metadata transport):

- SSE vs WebSockets comparison (overview):\
  https://www.freecodecamp.org/news/server-sent-events-vs-websockets

