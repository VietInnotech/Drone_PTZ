# Analytics Web Integration Guide (MediaMTX video + Drone_PTZ metadata)

This guide is for the web/web-server developer who will build the browser experience:

- play the live video stream (via MediaMTX)
- draw overlays using analytics metadata from this repo’s API (no overlay video)
- allow a user to select/clear a target track ID (autotrack only)

If you need background context, see `docs/ANALYTICS_BACKEND_PLAN.md`.

---

## System overview (two planes)

1. **Media plane (video)**

   - Source camera/encoder → **MediaMTX** → browser (WebRTC/WHEP recommended).
   - The analytics backend does **not** serve video.

2. **Data/control plane (metadata + commands)**
   - This repo runs an **aiohttp** server that:
     - starts/stops analytics sessions
     - broadcasts `metadata_tick` (latest overlay state) over WebSocket
     - emits `track_event` (lifecycle: `new|update|end`) over WebSocket
     - accepts only:
       - `set_target_id` (integer track id)
       - `clear_target`

Important contract assumption (v1):

- The backend and frontend use the **same MediaMTX stream** so metadata coordinate space stays
  consistent (`space="source"`).

---

## What you need to integrate

### A) Video playback (MediaMTX)

Your UI must play the same stream that the backend ingests. In practice you will have:

- Browser WHEP URL (example):
  - `http://<mediamtx-host>:8889/<stream>/whep`
- Backend ingest config (`config.yaml` in this repo), example:

```yaml
camera:
  source: "webrtc"
  webrtc_url: "http://<mediamtx-host>:8889/<stream>/"
```

Notes:

- Backend ingest uses the existing `src/webrtc_client.py` and tries WHEP `/<stream>/whep` first,
  then falls back to legacy `/<stream>/offer`.
- Frontend playback can use WHEP directly, or any other method, as long as the displayed video
  matches the backend’s decoded frames (same crop/aspect ratio).

### B) Analytics API (this repo)

Run the analytics API server:

```bash
pixi run python -m src.api.server --host 0.0.0.0 --port 8080 --publish-hz 10
```

Endpoints (v1):

- `GET /healthz` → `{ "status": "ok" }`
- `GET /cameras` → `{ "cameras": [{ "camera_id": "camera_1" }] }`
- `POST /sessions` body `{ "camera_id": "camera_1" }` (or `{}` to use default)
  - returns `201` when created, `200` when reused (one session per camera)
  - response includes `session_id` and `ws_path`
- `GET /sessions/{session_id}` → session status
- `DELETE /sessions/{session_id}` → stop session
- `GET /ws/sessions/{session_id}` → WebSocket:
  - server → client: `metadata_tick`, `track_event`
  - client → server: `set_target_id`, `clear_target`

### C) Settings Management API (runtime)

Use these endpoints to read, validate, update, persist, or reload settings without restarting the server. Passwords are redacted in read responses. Write endpoints are rate-limited to 1 request/sec per client.

Core endpoints:

- `GET /settings` → full runtime settings (passwords redacted)
- `GET /settings/{section}` → a single section (`logging|camera|detection|ptz|performance|simulator|tracking|octagon_credentials|octagon_devices`)
- `PATCH /settings` → partial update across any sections (deep merge + validation)
- `PATCH /settings/{section}` → partial update of one section
- `POST /settings/validate` → dry-run validation (no changes applied)
- `POST /settings/persist` → write current runtime settings to `config.yaml` (creates timestamped backup, atomic write)
- `POST /settings/reload` → reload from `config.yaml`, discarding runtime changes (affects new sessions only)

Quick examples:

```bash
# Read everything
curl http://<api-host>:8080/settings

# Read one section
curl http://<api-host>:8080/settings/ptz

# Update and validate in one call (deep merge)
curl -X PATCH http://<api-host>:8080/settings \
  -H 'content-type: application/json' \
  -d '{"ptz":{"ptz_movement_gain":0.35},"detection":{"confidence_threshold":0.55}}'

# Dry-run validation only (no changes applied)
curl -X POST http://<api-host>:8080/settings/validate \
  -H 'content-type: application/json' \
  -d '{"detection":{"confidence_threshold":0.99}}'

# Persist current runtime settings to disk with backup
curl -X POST http://<api-host>:8080/settings/persist

# Reload from config.yaml (discard runtime overrides)
curl -X POST http://<api-host>:8080/settings/reload
```

---

## Message contract (v1)

### `metadata_tick` (server → client)

Reference examples:

- `docs/fixtures/metadata_tick.example.json`
- `docs/fixtures/metadata_tick.empty.example.json`
- `docs/fixtures/metadata_tick.edge_cases.example.json`

Key fields:

- `schema`: `"drone-ptz-metadata/1"`
- `type`: `"metadata_tick"`
- `session_id`, `camera_id`
- `ts_unix_ms` (+ optional `ts_mono_ms`)
- `space`: `"source"` (v1)
- `frame_size`: `{ "w": <int>, "h": <int> }`
- `tracks`: list of tracks (includes **all** active tracks so the user can choose)
  - `id`: integer (tracker-local, stable within session)
  - `label`: string
  - `conf`: float `[0..1]`
  - `bbox`: normalized `{ "x","y","w","h" }` in `[0..1]`, top-left origin
- `selected_target_id`: integer or `null`
- `tracking_phase`: `"idle" | "searching" | "tracking" | "lost"`
- `ptz.cmd`: last commanded velocity values (pan/tilt/zoom), clamped `[-1..1]`

### `track_event` (server → client)

Lifecycle messages suitable for timelines/notifications/persistence (as opposed to the
high-rate overlay tick).

Reference examples:

- `docs/fixtures/track_event.new.example.json`
- `docs/fixtures/track_event.update.example.json`
- `docs/fixtures/track_event.end.example.json`

Notes:

- `confirmed` indicates whether the backend considers the track “real” (used to reduce UI spam).
- `top_conf` is the best confidence seen so far for the track.
- `best_bbox` is the bbox corresponding to `top_conf` (normalized `x,y,w,h`).

### Commands (client → server)

Only these two commands exist in v1 (no manual PTZ override API):

```json
{ "type": "set_target_id", "target_id": 17 }
```

```json
{ "type": "clear_target" }
```

Server replies with an `ack` or an `error`:

```json
{ "type": "ack", "command": "set_target_id", "target_id": 17 }
```

```json
{ "type": "error", "error": "target_id_must_be_int" }
```

---

## Recommended browser flow (step-by-step)

1. Fetch cameras:

```bash
curl http://<api-host>:8080/cameras
```

2. Start session:

```bash
curl -X POST http://<api-host>:8080/sessions \
  -H 'content-type: application/json' \
  -d '{"camera_id":"camera_1"}'
```

3. Connect WebSocket:

- Use `ws://<api-host>:8080/ws/sessions/<session_id>` in dev
- Use `wss://...` in production (TLS)

4. Render overlay:

- Keep the latest tick in memory.
- Handle `track_event` messages separately (append to a timeline, show toasts, etc.).
- On `requestAnimationFrame`, redraw the overlay canvas from the latest tick.
- Use normalized bbox math (see next section).
- **Implemented features:**
  - Color coding: green (#22c55e) for selected target, cyan (#38bdf8) for other tracks, orange (#f97316) when tracking phase is "lost"
  - Tracking phase badge: displays current phase badge in top-right corner with color coding
  - Confidence display: shown as percentage in bbox labels (e.g., "drone #17 83%")
  - Track timeline: displays recent lifecycle events (new/update/end) with auto-dismiss after 30 seconds

5. Target selection UI:

- Display `tracks[]` to user (id + label + conf).
- When user selects one, send `set_target_id`.
- Provide "clear" button that sends `clear_target`.
- **PTZ Autotracking:** When a target is selected via `set_target_id`, the Python backend automatically starts PTZ autotracking. The `ptz.active` field in `metadata_tick` indicates if autotracking is active. PTZ command velocities are shown in `ptz.cmd` (pan/tilt/zoom values in [-1..1] range).

---

## Overlay rendering details (the part that usually breaks)

### Coordinate mapping (normalized bbox → overlay pixels)

The backend emits bbox in normalized coordinates relative to the **source frame**:

- `x,y,w,h` all in `[0..1]`
- origin is top-left

If your `<video>` is displayed without cropping (recommended: `object-fit: contain`), compute the
actual displayed video content rect inside the element, then map bboxes into that rect.

Example (JS, `object-fit: contain`):

```js
function computeContainRect(videoEl) {
  const rect = videoEl.getBoundingClientRect();
  const vw = rect.width;
  const vh = rect.height;
  const sw = videoEl.videoWidth;
  const sh = videoEl.videoHeight;
  const scale = Math.min(vw / sw, vh / sh);
  const cw = sw * scale;
  const ch = sh * scale;
  return { x: (vw - cw) / 2, y: (vh - ch) / 2, w: cw, h: ch };
}

function bboxToPixels(bbox, containRect) {
  return {
    x: containRect.x + bbox.x * containRect.w,
    y: containRect.y + bbox.y * containRect.h,
    w: bbox.w * containRect.w,
    h: bbox.h * containRect.h,
  };
}
```

If you use `object-fit: cover` (cropping), the mapping is different (scale is `max(...)` and you
must subtract crop offsets). Prefer `contain` until everything works.

### Canvas sizing (handle DPR)

To keep overlays crisp on high-DPI displays:

- Set canvas CSS size to match the video element size (in CSS pixels).
- Set canvas width/height to CSS size \* `devicePixelRatio`.
- Scale the drawing context by `devicePixelRatio`.

---

## WebRTC/WHEP playback note (MediaMTX)

If you implement WHEP playback yourself, the basic pattern is:

1. Create `RTCPeerConnection`
2. Add a recv-only video transceiver
3. Create offer + setLocalDescription
4. POST offer SDP to the WHEP endpoint (`Content-Type: application/sdp`)
5. SetRemoteDescription from the response SDP answer

WHEP can require trickle ICE (PATCH to the returned session URL). If you see “connects but no
video”, check whether candidates need to be PATCHed.

References:

- `src/webrtc_client.py` (backend WHEP handshake logic)
- WHEP/WHIP references at end of `docs/ANALYTICS_BACKEND_PLAN.md`

---

## Validation checklist (Phase 3)

These checks prevent “boxes don’t line up” problems:

1. **Same stream**

   - Browser video URL points to the same MediaMTX stream the backend ingests.
   - No additional crop/letterbox in the media server path.

2. **Aspect ratio consistency**

   - Use `object-fit: contain` and validate mapping on multiple window sizes.

3. **Sanity overlay**

   - Render a known rectangle from the UI itself (e.g., center box at `x=0.4,y=0.4,w=0.2,h=0.2`)
     to validate mapping independent of backend.

4. **Backend tick inspection**
   - Log the latest tick and confirm:
     - `frame_size` matches `video.videoWidth/video.videoHeight` (or proportional)
     - `bbox` stays within `[0..1]`

---

## Error handling + reconnection

- The WebSocket publisher uses “latest-state semantics” and may close slow clients.
- If the WebSocket closes:
  - reconnect WS to the same `session_id` (session still running), or
  - call `POST /sessions` again (idempotent) and reconnect to returned `ws_path`.

## Operational notes (loop health)

- Tick cadence can vary slightly: the backend now uses a non-blocking frame buffer; under load it will drop older frames instead of stalling. Handle bursts/gaps gracefully (keep last tick and render until a new one arrives).
- Main loop is guarded by a watchdog (3s) and latency percentiles are logged every 120 frames. If the WS disconnects unexpectedly, assume the backend watchdog fired or the source stalled—recreate the session.
- `/healthz` remains the quickest probe; consider surfacing backend log warnings for frame drops/latency in ops dashboards (no protocol changes required for the UI).

---

## Deployment notes (recommended)

- Run MediaMTX and the analytics API behind the same reverse proxy/domain to avoid CORS and mixed
  content issues.
- Prefer TLS in production (`https` + `wss`).
- If you add auth later, treat it as **two** systems:
  - video plane auth (MediaMTX)
  - API plane auth (analytics backend)

---

## Frontend Implementation Details

### Environment Configuration

Create a `.env` file in the project root:

```env
VITE_ANALYTICS_API_URL=http://localhost:8080
```

The frontend will default to `http://${window.location.hostname}:8080` if this variable is not set.

### Track Event Handling

The `useAnalyticsSession` hook automatically handles both `metadata_tick` and `track_event` messages:

- `metadata_tick`: Used for real-time overlay rendering (high frequency, ~10 Hz)
- `track_event`: Used for lifecycle notifications (new/update/end events)

Track events are stored in a rolling buffer (last 50 events) and exposed via:

- `analyticsSession.trackEvents`: Array of recent track events
- `analyticsSession.latestEvent`: Most recent track event

### Overlay Features

**Color Coding:**

- Selected target: Green (#22c55e) with thicker stroke (3px)
- Other tracks: Cyan (#38bdf8) with standard stroke (2px)
- Lost phase: Orange (#f97316) when `tracking_phase === "lost"`

**Tracking Phase Badge:**

- Displays in top-right corner of video overlay
- Shows current phase: IDLE, SEARCHING, TRACKING, or LOST
- Color-coded: green for tracking, yellow for searching, orange for lost
- Only visible when phase is not "idle"

**Confidence Display:**

- Shown as percentage in bbox labels (e.g., "drone #17 83%")
- Automatically calculated from `track.conf` field

### Track Timeline Component

The `TrackTimeline` component displays recent track lifecycle events:

- Auto-filters events older than 30 seconds
- Shows last 20 visible events (most recent first)
- Color-coded event types: green (new), blue (update), gray (end)
- Displays track ID, label, confidence, zones, and event age
- Toggleable via checkbox in the sidebar (only visible when Object Info is enabled)

## Quick reference (copy/paste)

Start API server:

```bash
pixi run python -m src.api.server --port 8080
```

Start a session:

```bash
curl -X POST http://localhost:8080/sessions -H 'content-type: application/json' -d '{}'
```

Connect WS:

```text
ws://localhost:8080/ws/sessions/<session_id>
```

Send select target:

```json
{ "type": "set_target_id", "target_id": 17 }
```

Clear target:

```json
{ "type": "clear_target" }
```

## Testing Checklist

1. **Environment Setup:**

   - [ ] `.env` file created with `VITE_ANALYTICS_API_URL`
   - [ ] Python analytics API running on configured port
   - [ ] Frontend can connect to analytics API

2. **Overlay Rendering:**

   - [ ] Bounding boxes appear on video when tracks are detected
   - [ ] Selected target shows green color
   - [ ] Other tracks show cyan color
   - [ ] Orange color appears when tracking phase is "lost"
   - [ ] Confidence percentage displays in labels
   - [ ] Tracking phase badge appears in top-right corner

3. **Track Events:**

   - [ ] Track timeline shows new events when tracks appear
   - [ ] Update events appear when track confidence changes
   - [ ] End events appear when tracks disappear
   - [ ] Events auto-dismiss after 30 seconds
   - [ ] Timeline toggle works correctly

4. **Target Selection:**
   - [ ] Can select target from dropdown
   - [ ] Selected target changes color to green
   - [ ] Clear target button works
   - [ ] WebSocket commands send correctly
   - [ ] ACK/error messages handled properly
