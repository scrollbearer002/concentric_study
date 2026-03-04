# JSPaint Draw Failure Forensics

## Environment Basis
- Repo: `concentric_study`
- Machine/runtime: local macOS + Safari + Quartz draw path
- Failed artifact: `operator/cre/jspaint_polo_bear_panther_canvas.png`
- Source script: `operator/cre/jspaint_draw_polo_bear_panther.py`

## Local Evidence
- Real canvas size from live DOM:
  - `683 x 384`
- Planned stroke box before normalization:
  - `x: 185.5..497.5`
  - `y: 53.52..683.52`
- Actual rendered non-white pixel box:
  - `x: 189..493`
  - `y: 53..383`

The drawing plan exceeded the live canvas height by about `299.52` pixels. The
lower body and boots were therefore clipped by construction before any cursor
timing issue or stroke-quality issue is considered.

## Diagnosis
This was primarily a **geometry-control failure**, not a pointer-control
failure.

The script did use live canvas discovery via `getBoundingClientRect()`, but it
did **not** use the discovered canvas size to fit the planned figure to the
available drawing area. It treated the canvas dimensions as a coordinate frame
but not as a hard containment constraint.

That produced two concrete failures:
1. the figure was too tall for the actual canvas
2. the saved screenshot/canvas export was not used as a post-draw fit check

## Correction
An isolated geometry helper now normalizes the stroke plan to the live canvas
before drawing:
- `operator/cre/art_geometry.py`

The JSPaint script now scales and recenters the stroke set with explicit
margins before sending Quartz events.

## Additional Live Finding After the First Fix
The fit-to-canvas correction addressed the first root cause, but a maximized
replay exposed a second one:

- Safari bounds during replay: `(0, 31, 1440, 813)`
- Script-reported `canvas_bbox_px`: `(122, 1422, 1488, 2190)`

Those `y` values are physically impossible inside a window whose bottom edge is
at `813` points. That means the screenshot-derived `_detect_canvas_top_px()`
heuristic is not stable across layout changes and can overwrite correct DOM
geometry with a bogus chrome offset.

So the full failure stack is:
1. no fit-to-canvas normalization
2. unstable screenshot-based canvas-top inference

The first is now fixed. The second still needs replacement with a deterministic
viewport-to-screen mapping method.

## Why This Fix Is Scientifically Sound
- `getBoundingClientRect()` returns viewport-relative element geometry and is
  the correct ground truth for the visible drawing region:
  <https://developer.mozilla.org/en-US/docs/Web/API/Element/getBoundingClientRect>
- `<canvas>` has a logical drawing size that can differ from CSS/display
  layout, so containment must be computed explicitly:
  <https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement>
  <https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial/Basic_usage>
- GUI-agent literature supports closed-loop, state-aware interaction over
  open-loop coordinate guessing:
  - OSWorld: <https://arxiv.org/abs/2404.07972>
  - UI-Hawk: <https://aclanthology.org/2025.emnlp-main.920/>
  - ShowUI: <https://arxiv.org/abs/2411.17465>

## Practical Lesson
For art tasks in this repo:
1. inspect live canvas geometry
2. compute planned stroke bbox
3. normalize art to fit the canvas
4. map viewport geometry to screen coordinates with a deterministic method
5. draw
6. verify the actual canvas bitmap, not just the page screenshot
