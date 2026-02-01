Thermal Detection Tuning Guide (Rocket Launch Tracking)

Scope
- This guide is for thermal contour/blob detection when tracking a rocket launch.
- Assumes a single dominant hot target with transient exhaust flicker and hot ground clutter.

Baseline Rocket Profile (recommended starting point)
Set these in `Drone_PTZ/config.yaml` under `thermal_detection`:
- detection_method: contour
- use_otsu: false
- threshold_value: 225
- clahe_clip_limit: 1.0
- clahe_tile_size: 16
- blur_size: 9
- min_area: 600
- max_area: 15000

Why this profile works
- Fixed threshold avoids Otsu “chasing” large scene changes during ignition/plume growth.
- Higher blur reduces speckle noise and suppresses tiny hot fragments.
- Lower CLAHE contrast prevents background heat from being amplified into many small targets.
- Area gates keep the plume or hot ground from becoming a giant target.

Step‑by‑step tuning workflow
1) Confirm a clean baseline
   - Start with the profile above.
   - Ensure thermal input is stable (no automatic gain or palette changes mid‑scene).

2) Reduce false positives
   - Too many small targets: increase `min_area` (e.g., 600 → 900 → 1200).
   - Sparkly background: increase `blur_size` by +2 (odd values only).
   - Background still noisy: decrease `clahe_clip_limit` (e.g., 1.0 → 0.8).

3) Prevent the plume/ground from dominating
   - If the plume becomes the only target and covers too much: reduce `max_area`.
   - If the rocket itself disappears early: increase `max_area` slightly or lower `threshold_value`.

4) Recover missed detections
   - If the rocket is missed entirely: lower `threshold_value` (e.g., 225 → 210).
   - If the rocket is visible but fragmented: lower `min_area` slightly and/or reduce `blur_size`.

5) Handling ignition transition
   - Expect the plume to be very hot and large. Keep `use_otsu: false` for stability.
   - If ignition floods the frame, temporarily lower `max_area` to force tracking a smaller core.

Quick adjustments cheat‑sheet
- Too many targets: increase `min_area`, increase `blur_size`, lower `clahe_clip_limit`.
- No targets: lower `threshold_value`, lower `min_area`, reduce `blur_size`.
- One huge target (plume/ground): lower `max_area`, raise `threshold_value`.
- Flicker / jumping centroid: increase `blur_size`, keep `use_kalman: true`.

Notes
- Otsu (`use_otsu: true`) can be useful in stable scenes but often performs poorly during rapid thermal changes at ignition.
- Changes should be made one at a time; observe 3–5 seconds of footage after each change.
