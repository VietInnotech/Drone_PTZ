# NanoTrack Integration Plan

This document outlines a concrete, step‑by‑step plan to integrate NanoTrack
single‑object tracking (SOT) into the Drone PTZ Tracking System. The design keeps
the current YOLO + ByteTrack multi‑object detection/ID pipeline intact while adding
an optional, lightweight SOT path that improves target continuity and reduces
compute once a target is locked.

## Summary

- Goal: Add a NanoTrack‑powered SOT mode that takes over after a user selects a
  target ID, using the current detection to seed the tracker and then updating the
  target box every frame without requiring YOLO on every frame.
- Approach: Use OpenCV’s `TrackerNano` (ONNX) backend for runtime tracking
  (no custom ops build), with periodic or event‑driven re‑detection via YOLO for
  re‑acquisition and drift control.
- Scope: New tracking adapter (`src/tracking/nanotracker.py`), minimal changes to
  `src/main.py`, additional config in `config.yaml` + typed settings in
  `src/settings.py`, optional test coverage.
- Default behavior remains unchanged unless explicitly enabled via config.

## Research Notes (MCP)

- NanoTrack project (PyTorch + NCNN demos) and docs:

  - GitHub: HonglinChu/NanoTrack — mobile/embedded demos (ncnn)
    https://github.com/HonglinChu/NanoTrack
  - PyTorch code and models under SiamTrackers/NanoTrack
    https://github.com/HonglinChu/SiamTrackers/tree/master/NanoTrack
  - README (models V1/V2/V3):
    https://raw.githubusercontent.com/HonglinChu/SiamTrackers/master/NanoTrack/README.md

- OpenCV `TrackerNano` (DNN‑based tracker; uses NanoTrack ONNX models):
  - API: https://docs.opencv.org/4.x/d8/d69/classcv_1_1TrackerNano.html
  - Sample (Python): https://raw.githubusercontent.com/opencv/opencv/4.x/samples/python/tracker.py
  - Required model files (example paths from sample; V2 recommended):
    - `nanotrack_backbone_sim.onnx`
    - `nanotrack_head_sim.onnx`

Why choose OpenCV TrackerNano

- Pros: No custom build steps; small ONNX models (~1–2 MB each); runs fast on CPU;
  already a dependency (`opencv` via Pixi).
- Cons: Pure SOT (single target); requires seeding from a detection; no ID output.

Alternative options considered (deprioritized for now)

- Integrate PyTorch NanoTrack from `SiamTrackers` directly: requires `setup.py
build_ext --inplace`, heavier integration and training/test data structures.
- Use third‑party `nanotrack` PyPI package: not the official NanoTrack model; API
  maturity unknown compared to OpenCV’s upstream integration.

## Current Architecture Fit

Today, `main()` runs YOLO+ByteTrack every frame and uses `TrackerStatus` (IDLE,
SEARCHING, TRACKING, LOST) to drive PTZ with an ID‑locked target.

NanoTrack integration slots in as follows:

1. Initial detection and ID selection remain unchanged (YOLO+ByteTrack).
2. When entering `TRACKING` with a selected ID, the current detection’s bbox seeds
   a NanoTrack SOT instance.
3. While SOT is active, the SOT bbox is used to drive PTZ; YOLO can run at a lower
   duty cycle (periodic or on events) for drift checks and re‑acquisition.
4. If the SOT update fails or drift exceeds thresholds, fall back to YOLO for
   re‑seeding (SEARCHING/LOST behavior remains consistent with `TrackerStatus`).

## Deliverables

- New module: `src/tracking/nanotracker.py`
  - Thin wrapper around OpenCV’s `TrackerNano` with a small, testable API.
- Settings additions (typed + config.yaml)
  - Enable/disable NanoTrack SOT; ONNX model paths; tuning knobs.
- `main.py` integration
  - Seed/own the lifecycle of a single active SOT instance when TRACKING.
  - Use SOT box for PTZ servoing; run YOLO with reduced cadence.
- Documentation
  - How to enable, where to place ONNX files, and operational notes.
- Optional tests
  - Light unit tests with mocks for `cv2.TrackerNano` to validate control flow.

## Dependencies and Assets

Environment

- OpenCV ≥ 4.7 provides `TrackerNano`; repo pins `opencv` via Pixi (4.11 is
  sufficient).
- No additional runtime dependency needed (OpenCV DNN reads ONNX directly).

Models (to be stored in repo assets)

- Place model files under:
  - `assets/models/nanotrack/nanotrack_backbone_sim.onnx`
  - `assets/models/nanotrack/nanotrack_head_sim.onnx`
- Source references (for download):
  - Backbone ONNX (V2):
    https://github.com/HonglinChu/SiamTrackers/blob/master/NanoTrack/models/nanotrackv2/nanotrack_backbone_sim.onnx
  - Head ONNX (V2):
    https://github.com/HonglinChu/SiamTrackers/blob/master/NanoTrack/models/nanotrackv2/nanotrack_head_sim.onnx

## Config and Settings Changes

config.yaml additions (example)

```yaml
tracking:
  use_nanotrack: false
  nanotrack_backbone_path: assets/models/nanotrack/nanotrack_backbone_sim.onnx
  nanotrack_head_path: assets/models/nanotrack/nanotrack_head_sim.onnx
  # How often to re-run YOLO while SOT is active (frames)
  reacquire_interval_frames: 10
  # Max allowed center drift (fraction of frame width/height) before forcing re-detect
  max_center_drift: 0.15
  # SOT failure retry budget before releasing tracker
  max_failed_updates: 5
  # OpenCV DNN backend/target; leave defaults unless you know your hardware
  dnn_backend: default # default|opencv|cuda|vulkan|openvino|halide
  dnn_target: cpu # cpu|cuda|cuda_fp16|opencl|opencl_fp16|vulkan
```

Typed settings in `src/settings.py`

- Add `TrackingSettings` dataclass with the above fields.
- Add to top‑level `Settings` as `tracking: TrackingSettings`.
- Parse/validate in `load_settings()` with sane defaults.

## Code Changes

1. New tracker adapter `src/tracking/nanotracker.py`

```python
# Minimal, dependency-light wrapper
import cv2
from dataclasses import dataclass
from typing import Tuple

@dataclass
class NanoParams:
    backbone: str
    head: str
    backend: int | None = None
    target: int | None = None

class NanoSOT:
    def __init__(self, params: NanoParams) -> None:
        self._params = params
        self._tracker = None
        self._active = False

    def init(self, frame, bbox_xyxy: Tuple[int, int, int, int]) -> bool:
        x1, y1, x2, y2 = bbox_xyxy
        w, h = max(1, x2 - x1), max(1, y2 - y1)
        params = cv2.TrackerNano_Params()
        params.backbone = self._params.backbone
        params.neckhead = self._params.head
        if self._params.backend is not None:
            params.backend = self._params.backend
        if self._params.target is not None:
            params.target = self._params.target
        self._tracker = cv2.TrackerNano_create(params)
        self._active = self._tracker.init(frame, (x1, y1, w, h))
        return bool(self._active)

    def update(self, frame) -> tuple[bool, Tuple[int, int, int, int]]:
        if not self._active or self._tracker is None:
            return False, (0, 0, 0, 0)
        ok, (x, y, w, h) = self._tracker.update(frame)
        return bool(ok), (int(x), int(y), int(x + w), int(y + h))

    def release(self) -> None:
        self._tracker = None
        self._active = False
```

2. `main.py` lifecycle integration (high‑level)

- Add a `NanoSOT` instance variable `active_sot = None` and book‑keeping:
  - `last_reacquire_frame`, `failed_updates`, `last_sot_bbox`.
- Seed SOT when `TrackerStatus` transitions into `TRACKING` and `target_id` is set:
  - Use the selected detection’s bbox as seed: `active_sot.init(frame, det.xyxy)`.
- While SOT is active:
  - Prefer `sot_bbox` for PTZ steering (dx/dy, coverage, zoom logic unchanged).
  - Every `reacquire_interval_frames`, run YOLO once to refresh overlay and validate.
  - If SOT `update()` fails or exceeds `max_failed_updates`/drift thresholds:
    - `active_sot.release()` and fall back to YOLO for re‑seeding.
- When `target_id` cleared or phase changes to `IDLE`:
  - Release SOT immediately.

Minimal pseudo‑diff for decision point

```python
# inside TRACKING phase
if settings.tracking.use_nanotrack:
    if active_sot is None and best_det is not None:
        seed_bbox = to_xyxy(best_det, frame_w, frame_h)
        active_sot = NanoSOT(params)
        active_sot.init(frame, seed_bbox)
    if active_sot is not None:
        ok, sot_bbox = active_sot.update(frame)
        if ok:
            drive_ptz_from_bbox(sot_bbox)
        else:
            failed_updates += 1
            if failed_updates >= settings.tracking.max_failed_updates:
                active_sot.release(); active_sot = None
                # fall back to YOLO until next seed
else:
    # current behavior using YOLO+ByteTrack bbox
    drive_ptz_from_bbox(best_det.xyxy)
```

3. Overlays and diagnostics

- When SOT is active, draw an additional rectangle (e.g., magenta) for the SOT box.
- Continue drawing YOLO boxes for situational awareness when available.
- Extend `draw_ptz_status` to add `SOT: active/idle` and last update status.

## Testing Strategy

Unit tests (fast)

- Mock `cv2.TrackerNano_Params` and `cv2.TrackerNano_create` to validate
  `NanoSOT.init()`, `update()`, and `release()` control flow.
- Add tests for `settings` parsing of new `tracking` section.

Integration test (simulation)

- Use PTZ simulator video (`assets/videos/...`).
- Enable `tracking.use_nanotrack: true` and verify:
  - Program runs; SOT transitions occur when a target ID is selected; no crashes.
  - PTZ responds to SOT bbox and overlay shows SOT activity.

CI/coverage

- Keep tests deterministic; no external downloads in tests.
- Maintain current coverage thresholds.

## Operational Notes

- Seeding SOT from detection: the selected detection’s `xyxy` is converted to
  `(x, y, w, h)` for SOT initialization.
- Re‑acquisition: For robustness, run YOLO every N frames or on apparent drift
  (SOT center vs. last known detection center), whichever occurs first.
- Performance: On CPU, NanoTrack ONNX typically runs near real‑time at 720p; expect
  a net speedup since YOLO is skipped most frames while tracking.
- Backends/targets: Stick with OpenCV DNN default unless there’s a tested reason to
  select CUDA/Vulkan/OpenCL (documented in config).

## Migration & Backward Compatibility

- Defaults keep current behavior (NanoTrack disabled).
- Enabling SOT requires placing ONNX files under `assets/models/nanotrack/` and
  updating `config.yaml` paths.
- No changes required for ONVIF PTZ or simulator APIs.

## Risks & Mitigations

- Model availability: Pin to the V2 ONNX files in assets; provide a helper script
  to fetch them; verify integrity on startup (size/hash).
- Tracker drift: Use periodic YOLO refresh and drift thresholds to trigger
  re‑seeding; expose knobs in config.
- Version compatibility: Ensure `opencv` version supports `TrackerNano` (≥ 4.7).
  Repo currently pins `opencv` via Pixi; if needed, bump minor within constraints.

## Work Breakdown (TDD‑friendly)

1. Settings & config schema

   - Add `TrackingSettings` dataclass + parsing/validation.
   - Extend `config.yaml` with `tracking` section and defaults.
   - Unit tests for settings parsing.

2. NanoTrack adapter

   - Implement `src/tracking/nanotracker.py` wrapper.
   - Unit tests with cv2 mocks to validate lifecycle.

3. `main.py` integration

   - Seed/update/release SOT in `TRACKING` phase.
   - Add periodic YOLO re‑acquisition logic.
   - Draw SOT overlay + status line.

4. Assets & scripts

   - Add `assets/models/nanotrack/` placeholders.
   - Optional: `scripts/download_nanotrack_models.py` + Pixi task.

5. Docs & validation
   - Update README/ARCHITECTURE with SOT mode.
   - Run sim video to smoke‑test; adjust defaults.

## Acceptance Criteria

- With `tracking.use_nanotrack: true` and valid ONNX paths:
  - Selecting a target ID seeds NanoTrack and activates SOT.
  - PTZ control uses SOT updates with smooth pan/tilt/zoom behavior.
  - YOLO runs periodically for re‑acquisition; SOT recovers on temporary losses.
  - Disabling NanoTrack restores current behavior with no regressions.

## Next Steps

- Confirm OpenCV build exposes `cv2.TrackerNano_*` symbols in the Pixi environment.
- Download/commit the ONNX models into `assets/models/nanotrack/` (or add fetch task).
- Implement the settings + adapter + main loop changes per the work breakdown.
- Validate in simulator; iterate on `reacquire_interval_frames` and drift thresholds.
