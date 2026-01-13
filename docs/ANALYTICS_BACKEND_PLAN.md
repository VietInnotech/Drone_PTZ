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
  - APIs for runtime configuration:
    - Target selection: set/clear the selected target ID.
    - Settings: read, update, persist, and reload runtime settings.
    - Model management: list, upload, delete, and activate detection models.
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
   - Browser draws the overlay from metadata on top of the video element.

This separation is common in real-time computer vision systems because video and
metadata have different throughput/latency requirements and failure modes.

### Reference Implementation Pattern

- **Video**:
  - use an existing streaming server (e.g., MediaMTX) for camera ingest + WebRTC egress
    to the browser.
- **Backend**:
  - ingest from the existing MediaMTX deployment (recommended and already supported by
    this repo):
    - **WebRTC ingest (current path)**: `camera.source="webrtc"` + `camera.webrtc_url` and
      use `src/webrtc_client.py` (tries WHEP `/<stream>/whep` first, then legacy `/<stream>/offer`)
    - **RTSP ingest (optional alternative)**: point `camera.rtsp_url` at MediaMTX
      (e.g., `rtsp://<mediamtx-host>:8554/<stream>`) when you want simpler decoding / less
      WebRTC overhead
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
  "type": "metadata_tick",
  "session_id": "session-cam_01-2025-12-20T12:00:00Z",
  "camera_id": "cam_01",
  "ts_unix_ms": 1730000000123,
  "ts_mono_ms": 123456789,
  "frame_index": 9321,
  "space": "source",
  "frame_size": {"w": 1280, "h": 720},
  "selected_target_id": 17,
  "tracking_phase": "tracking",
  "ptz": {
    "control_mode": "onvif",
    "active": true,
    "cmd": {"pan": 0.12, "tilt": -0.03, "zoom": 0.44}
  },
  "tracks": [
    {
      "id": 17,
      "label": "drone",
      "conf": 0.83,
      "bbox": {"x": 0.42, "y": 0.31, "w": 0.08, "h": 0.06}
    }
  ]
}
```

Notes:

- Include both `ts_unix_ms` (log correlation) and `ts_mono_ms` (ordering / drift-safe).
- `velocity` is optional; it helps frontend smoothing/prediction (can be added later).
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

## Proven Patterns to Copy (Frigate-Inspired, Adapted to Analytics-Only)

Frigate is a mature, production-proven reference for “video + metadata + PTZ control” systems.
Even though this repo should remain **analytics-only** (no recording/clip storage required), a
few patterns are worth copying because they reduce noise, improve UX, and scale well.

### 1) Separate “detect” stream from “view” stream

Frigate encourages using different inputs/roles per camera: a low-res stream for detection and
another (often higher-res) stream for recording/viewing. The key takeaway for this repo:

- inference ingest should be optimized for detection/tracking (resolution, FPS, codec)
- the browser stream can remain independent (WebRTC/HLS) and tuned for UX

In practice:

- keep **media plane** in a dedicated media server (MediaMTX / go2rtc / etc.)
- let the backend subscribe to a **detection-optimized** RTSP feed (or decoded frames) that is
  consistent and cheap to process

Example config shape (Frigate-style roles, adapted):

```yaml
cameras:
  cam_01:
    enabled: true
    inputs:
      - path: rtsp://<mediamtx-host>:8554/stream_sub
        roles: [detect] # backend ingest
      - path: rtsp://<mediamtx-host>:8554/stream_main
        roles: [view]   # media plane (browser), not required by this repo
    detect:
      width: 1280
      height: 720
      fps: 10
    ptz:
      onvif:
        host: 10.0.0.10
        port: 8000
        user: admin
        password: ${ONVIF_PASSWORD}
      autotrack:
        enabled: true
        required_zones: [sky]
        return_preset: home
```

### 2) Track lifecycle events, not just per-frame “ticks”

Frigate’s MQTT `frigate/events` feed is built around **object lifecycle** updates:
`new` → repeated `update` → `end`, and it only starts publishing once the object is no longer
considered a false positive.

Copy the idea (not necessarily the exact payload):

- a **tick** message for the current overlay state (fast, latest-state semantics)
- a **track_event** message for lifecycle changes (new/update/end) suitable for persistence,
  notifications, and UX timelines
- “false positive / confirmed” gating to avoid spamming the UI with flickery tracks

Suggested WebSocket `track_event` shape (Frigate-inspired):

```json
{
  "schema": "drone-ptz-metadata/1",
  "type": "track_event",
  "event": "new",
  "session_id": "session-cam_01-2025-12-20T12:00:00Z",
  "camera_id": "cam_01",
  "ts_unix_ms": 1730000000123,
  "before": null,
  "after": {
    "track_id": "cam_01/17",
    "id": 17,
    "label": "drone",
    "top_conf": 0.93,
    "confirmed": true,
    "start_ts_unix_ms": 1730000000123,
    "end_ts_unix_ms": null,
    "zones": ["sky"],
    "best_bbox": {"x": 0.42, "y": 0.31, "w": 0.08, "h": 0.06}
  }
}
```

### 3) Topic-based pub/sub over WebSocket (optional, but scales well)

Frigate’s UI updates behave like a pub/sub bus: clients subscribe to “topics” and receive
updates, with some topics effectively “retained” so the UI can bootstrap quickly.

For this repo, you can start with one WebSocket per session, but consider a topic model early:

- `sessions/<id>/tick` (retained latest)
- `sessions/<id>/tracks` (event stream)
- `sessions/<id>/ptz/state` (retained latest)
- `stats` (retained latest)

This makes it easy to add optional MQTT bridging later because the message model matches.

### 4) PTZ autotracking guardrails

Frigate’s autotracking docs are a good checklist of real-world PTZ issues. Ideas to adopt:

- **required zone(s)** before autotracking begins (reduces “track the wrong thing” failures)
- **return preset** when tracking ends (predictable operator UX)
- **timeout scan** after lost tracking (try to reacquire near last known position)
- **calibration/movement weights** to handle estimating object position after camera motion
- publish autotracker state (enabled/active) separately from PTZ position telemetry

### 5) Stats endpoint and periodic telemetry publish

Frigate exposes `/api/stats` and also publishes similar data periodically (e.g., via MQTT).
Copy the pattern:

- `GET /stats` (or `GET /sessions/{id}/stats`): per-camera FPS, inference latency, dropped
  frames, PTZ command rates, etc.
- optionally publish the same payload on WebSocket (and later MQTT) at a low rate (1–5 Hz)

### 6) Optional persistence + retention (analytics-only)

Frigate persists “events” in SQLite and exposes rich query APIs (filter by camera/label/time,
score, in-progress, etc.). For this repo:

- persist **track summaries** and **low-rate samples** (not video) to support timelines,
  debugging, and “what happened?” queries
- add retention/cleanup jobs (time-based + “retain indefinitely” escape hatch)

## Implementation Roadmap (Incremental)

### Phase 0: Contract + schemas (foundation)

**Goal:** make backend/frontend integration deterministic before writing server code.

#### Proposed contract v1 (ready to implement)

These defaults match the current codebase (ByteTrack IDs, WebSocket control) and the current
MediaMTX ingest setup.

**MediaMTX + sessions**

- `camera_id`: stable identifier from config (e.g., `cam_01`).
- `session_id`: generated by the backend on session start; unique per analytics run.
- Confirmed (and required for v1 overlay correctness): the frontend and backend consume the same
  MediaMTX stream (same aspect ratio, no cropping/letterboxing differences).

**Coordinate space (`space`)**

- `space="source"` means: coordinates refer to the decoded frame from the analytics ingest
  (recommended to be the same stream the browser displays).
- `space="processed"` is reserved for cases where the backend runs inference on a cropped/resized
  image and cannot trivially map back; avoid in production unless you also ship a transform.

**Bounding boxes (`bbox`)**

- `bbox` is normalized floats: `x`, `y`, `w`, `h` in `[0.0..1.0]`, top-left origin.
- Backend clamps values into `[0.0..1.0]` (no negatives; no >1), so the frontend can render
  without special-casing out-of-range math.

**Transform rules (processed → source)**

Avoid this in production by having the backend ingest the same stream the browser renders. If
you must run inference on a cropped/resized viewport (e.g., PTZ simulation), convert bboxes back
to `space="source"` using the viewport rectangle from the original frame:

- Given:
  - source frame size `(W, H)`
  - viewport rect `(x1, y1, x2, y2)` in source pixel coordinates
  - bbox in processed normalized coords `(xp, yp, wp, hp)`
- Compute:
  - `roi_w = x2 - x1`, `roi_h = y2 - y1`
  - `x_src = (x1 + xp * roi_w) / W`
  - `y_src = (y1 + yp * roi_h) / H`
  - `w_src = (wp * roi_w) / W`
  - `h_src = (hp * roi_h) / H`

**Rates + ordering**

- Inference runs as fast as available input + hardware allows.
- Publish `metadata_tick` at a configurable rate (default target: 10 Hz).
- Emit `track_event` immediately on lifecycle changes (`new|update|end`).
- Include both `ts_unix_ms` and `ts_mono_ms` when possible.

**IDs**

- Track `id` is the tracker-local integer ID (ByteTrack/BoTSORT). It is stable only within a
  session and can change across restarts.
- `selected_target_id` refers to this integer ID (v1 keeps compatibility with `select_by_id`).
- `tracking_phase` uses the `TrackingPhase.value` strings: `idle`, `searching`, `tracking`, `lost`.

**Message types (server → client)**

- `metadata_tick`: latest-state overlay payload (includes all active tracks so the user can pick an ID).
- `track_event`: lifecycle updates (`new|update|end`), Frigate-inspired (recommended for confirmed
  tracks only to avoid spam; the UI can still render all tracks from `metadata_tick`).
- (optional) `stats`: low-rate health/telemetry snapshot (1–5 Hz).

**Commands (client → server)**

- `set_target_id` and `clear_target` are required for the first UI.
- No manual PTZ control/override API in v1.
- PTZ telemetry stays simple: expose “last commanded velocity” in `metadata_tick.ptz.cmd`, not
  absolute camera position.

#### Contract artifacts (schemas + fixtures)

- Schemas:
  - `docs/schemas/metadata_tick.schema.json`
  - `docs/schemas/track_event.schema.json`
  - `docs/schemas/command.schema.json`
- Fixtures:
  - `docs/fixtures/metadata_tick.example.json`
  - `docs/fixtures/metadata_tick.edge_cases.example.json`
  - `docs/fixtures/metadata_tick.empty.example.json`
  - `docs/fixtures/track_event.new.example.json`
  - `docs/fixtures/track_event.update.example.json`
  - `docs/fixtures/track_event.end.example.json`
  - `docs/fixtures/command.set_target_id.example.json`
  - `docs/fixtures/command.clear_target.example.json`

#### Decisions confirmed (Phase 0)

1. Frontend and backend use the same MediaMTX stream (so `space="source"` stays consistent).
2. `metadata_tick.tracks` includes all tracks (so the user can choose a target ID).
3. Target selection stays integer-based (`set_target_id.target_id` is the tracker-local int).
4. No manual PTZ control/override API (autotrack only).
5. PTZ telemetry stays simple (no absolute position; “last commanded velocity” is enough).

**Definition of done:**

- frontend can render overlays from fixtures without running the backend

### Phase 1: Analytics engine extraction (no UI, no network)

**Goal:** isolate “compute metadata from frames” into a testable module.

**Status:** implemented for `metadata_tick` generation (no transport yet).

Implemented:

- New analytics modules:
  - `src/analytics/types.py` (typed contract)
  - `src/analytics/metadata.py` (`MetadataBuilder`)
  - `src/analytics/engine.py` (`AnalyticsEngine`)
- `src/main.py` now builds and stores `LATEST_METADATA_TICK` each frame (future Phase 2 API can
  read/broadcast it).
- Fixtures-backed tests:
  - `tests/unit/test_analytics_metadata.py` validates ticks match `docs/fixtures/metadata_tick*.json`

Notes / findings:

- `bbox` is emitted as normalized `x,y,w,h` in `[0..1]` and rounded (6 decimals) to reduce float
  noise.
- `ptz.cmd` emits only “last commanded velocity” (clamped to `[-1, 1]`); no absolute PTZ
  position/telemetry is emitted in v1.
- Track `velocity` is not emitted yet (kept optional in the schema for future smoothing).

Deferred (next):

- A per-session state container to fully decouple the engine from `src/main.py`’s UI/debug loop.

**Definition of done:**

- deterministic tests can drive the engine with synthetic inputs and validate emitted metadata (done
  for `metadata_tick` and `track_event`)

### Phase 2: API server + realtime bus (sessions + WebSocket)

**Goal:** ship a minimal backend that browsers can connect to for metadata + control.

**Status:** implemented (REST + WebSocket + in-process session runner).

Implemented:

- Session + state:
  - `src/api/session_manager.py` enforces one session per camera (idempotent `POST /sessions`).
  - `src/api/session.py` runs a background `ThreadedAnalyticsSession` that ingests frames (including
    `camera.source="webrtc"` via the existing MediaMTX/WebRTC client) and updates a latest
    `metadata_tick`.
- HTTP + WebSocket:
  - `src/api/app.py` exposes:
    - `GET /healthz`
    - `GET /cameras`
    - `POST /sessions`, `GET /sessions/{id}`, `DELETE /sessions/{id}`
    - `GET /ws/sessions/{id}` (server → client `metadata_tick` + `track_event`; client → server commands)
    - **Settings management**: `GET /settings`, `PATCH /settings`, `POST /settings/persist`, `POST /settings/reload`
    - **Model management**: `GET /models`, `POST /models/upload`, `DELETE /models/{name}`, `POST /models/{name}/activate`
- `src/api/server.py` runs the aiohttp app (example: `pixi run api`).
  - Override via `API_HOST`, `API_PORT`, `API_PUBLISH_HZ` (e.g. `API_PORT=8080 pixi run api`).
- Tests:
  - `tests/unit/test_api_server.py` covers session lifecycle + WebSocket command handling.
  - `tests/integration/test_settings_api.py` and `test_model_api.py` cover management.

Notes / findings:

- WebSocket publishing uses “latest-state semantics” and closes slow clients (send timeout) to avoid
  impacting inference.
- Only v1 commands are supported: `set_target_id` (integer) and `clear_target` (no manual override).

**Definition of done:**

- two browser clients can subscribe concurrently without slowing inference

### Phase 3: Media plane integration + coordinate validation

**Goal:** align what the user sees (video) with what the backend reports (metadata).

- Standardize on the existing MediaMTX deployment as the ingest hub (current repo path):
  - browser plays the MediaMTX stream (WebRTC egress via WHEP)
  - backend ingests the same stream via `camera.source="webrtc"` + `camera.webrtc_url`
    (WHEP preferred; legacy `/offer` fallback via `src/webrtc_client.py`)
  - optionally switch backend ingest to RTSP-from-MediaMTX for lower overhead if needed
- Document the concrete endpoints used by your deployment:
  - WebRTC/WHEP: `http://<mediamtx-host>:8889/<stream>/whep` (or `/<stream>/` base, depending on setup)
  - RTSP: `rtsp://<mediamtx-host>:8554/<stream>`
- Add a coordinate validation tool:
  - render a test pattern or known calibration markers
  - verify bbox mapping between backend “source” coordinates and frontend overlay pixels

**Definition of done:**

- overlays line up reliably across resizing/DPR changes and common camera aspect ratios

### Phase 4: Persistence + query API (optional but high-value)

**Goal:** make analytics explainable and debuggable over time (without storing video).

- Add storage (start with SQLite for simplicity):
  - `tracks` table (summary fields: start/end/top score/zones/selected/confirmed)
  - `track_samples` table (downsampled bbox/score/velocity every N ms)
  - `ptz_commands` table (issued commands + results for audit/debug)
- Add retention:
  - time-based cleanup
  - optional `retain_indefinitely` flag (Frigate-inspired)
- Add query endpoints:
  - `GET /tracks?camera_id=&label=&after=&before=&min_score=&in_progress=`
  - `GET /tracks/{track_id}`

**Definition of done:**

- you can answer “what did the tracker think happened?” for a time range

### Phase 5: Hardening + integrations

**Goal:** make it production-ready and easy to integrate with other systems.

- AuthN/AuthZ:
  - viewer vs controller roles
  - per-session tokens and CORS policy
- Backpressure + rate limiting:
  - PTZ command rate limits + validation
  - publish throttles per client/topic
- Metrics:
  - `/metrics` (Prometheus) + `/healthz`/`/readyz`
  - expose inference FPS, dropped frames, PTZ command counts, queue depths
- Optional MQTT bridge (Frigate-style):
  - publish stats + track events under `drone_ptz/...`
  - accept limited commands (enable/disable autotrack, select target)

**Definition of done:**

- system stays stable with multiple sessions + multiple clients under load

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

Frigate (proven reference architecture and message patterns):

- Frigate camera config (separate detect vs view/record streams):\
  https://docs.frigate.video/configuration/cameras/
- Frigate PTZ autotracking considerations and guardrails:\
  https://docs.frigate.video/configuration/autotracking/
- Frigate MQTT event/lifecycle message pattern (`new|update|end`):\
  https://docs.frigate.video/integrations/mqtt/
- Frigate events query API (filters by camera/label/time/score/etc.):\
  https://docs.frigate.video/integrations/api/events-events-get/
- Frigate stats endpoint (example of consolidated health/telemetry payload):\
  https://docs.frigate.video/integrations/api/stats-stats-get/
