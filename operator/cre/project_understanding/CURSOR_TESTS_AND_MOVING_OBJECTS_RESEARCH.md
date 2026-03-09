# Cursor Tests and Moving Objects: PhD Research Dive

This document catalogs how the Concentric Study project **tests cursor behavior and interacts with moving or dynamic targets**: aim trainers, reaction-time tests, spawning targets, path-following, and drag-and-drop. It ties each capability to specific files, data flows, and design choices.

---

## 1. Executive summary

The repo supports several distinct “cursor vs. moving or dynamic objects” scenarios:

| Scenario | What moves | How the agent tracks / reacts | Primary harness / backend |
|---------|------------|-------------------------------|----------------------------|
| **Aim Trainer (Human Benchmark)** | Target appears at new position each click | DOM query → target (cx, cy) → smooth move → click; repeat until 30 targets | `human_benchmark_suite.run_aim` |
| **Reaction Time (Human Benchmark)** | Box turns green at random time | Poll `query_reaction_state()` for `isGreen` → click box; repeat 5× | `human_benchmark_suite.run_reactiontime` |
| **Mouse Accuracy Classic** | Multiple DOM targets spawn over time | Query `targets[]` → per-target click with **aim correction** (cursor position vs intended → running offset) | `mouse_accuracy_suite.run_classic_game` |
| **Path Follow (XBitLabs)** | Cursor must stay on a fixed path (path doesn’t move) | Precomputed path points → smooth move along path; query progress/accuracy | `xbitlabs_path_follow.run` |
| **Moving-target vision loop (ultimate test)** | Target moves in view | Region screenshot → detect target → smooth_move_and_click; 10 FPS loop (designed, not fully wired) | `ULTIMATE_TESTS.md` Test 2 + `CodexClient` |
| **Drag-and-drop** | User drags object A to B | `CodexClient.drag(start_x, start_y, end_x, end_y)` → kernel: move, mouse down, Bezier drag, mouse up | `codex_kernel.lua` + `test_drag_drop.py` |

So: **moving objects** are handled by (1) **DOM/JS state queries** for target positions (aim trainer, reaction, mouse accuracy classic), (2) **precomputed paths** for path-follow, and (3) a **vision loop** (screenshot → detect → click) in the ultimate-test design. **Cursor motion** is either **Quartz** (harnesses using `_smooth_move` + `_click_here`) or **Hammerspoon kernel** (CodexClient: Bezier move, drag, draw_path).

---

## 2. Human Benchmark: Aim Trainer and Reaction Time

**Files:** `operator/cre/project_understanding/tools/human_benchmark_suite.py`

### 2.1 Aim Trainer (discrete moving targets)

- **Site:** `https://humanbenchmark.com/tests/aim`
- **Behavior:** A target appears; when you click it, the next target appears elsewhere. Goal: click 30 targets; score = average time per target.
- **Flow:**
  1. `_ensure_live_profile()` → `mission_control.py up live`; `_ensure_safari_ready()` (evidence gate, Safari frontmost).
  2. Navigate to aim URL; click center to start (e.g. `START_CLIENT_CENTER`).
  3. Loop: `query_aim_state()` (JavaScript in page) returns `remaining`, `target` (with `cx`, `cy` in viewport), `averageVisible` (results screen).
  4. For each target: `click_client_point(target["cx"], target["cy"], profile)` → `_global_from_client` (viewport → global) → `_smooth_move(gx, gy, duration, steps)` → `_click_here(gx, gy)`.
  5. `_smooth_move` uses **Quartz**: linear interpolate from current position (from `cliclick p`) to target in `steps` steps, posting `kCGEventMouseMoved` each step; then click is `kCGEventLeftMouseDown` / `kCGEventLeftMouseUp`.

So the “moving” aspect is **target position changes each click**; the agent gets new positions via **DOM/JS**, not by tracking pixels. Cursor motion is **smooth linear** (or could be wired to Bezier via CodexClient if kernel is used).

### 2.2 Reaction Time (green box at random time)

- **Site:** `https://humanbenchmark.com/tests/reactiontime`
- **Behavior:** Click to start; wait; box turns green at a random moment; click as fast as possible; repeat 5 times.
- **Flow:**
  1. Navigate, then click box once to start.
  2. Poll `query_reaction_state()` (JS) for `isGreen`. When true, `click_client_point(box["cx"], box["cy"], profile)`.
  3. Loop until 5 green clicks or timeout; optionally click “Save score”.

So the “moving” aspect is **temporal** (when the box turns green), not spatial. The agent reacts by **polling DOM state** at ~30 Hz (`time.sleep(0.03)`), then issuing one smooth move + click.

### 2.3 Motion profile and coordinate system

- **MotionProfile:** `name`, `move_duration`, `move_steps`, `settle_sleep`. Tunes speed and steps of `_smooth_move` and sleep after click.
- **Coordinates:** Viewport (client) coords from JS `getBoundingClientRect()`; converted to global via `_global_from_client` using `SAFARI_VERTICAL_OFFSET` (139) or Safari window bounds + content inset so **Quartz events land in the right place** (see LIVE_SAFARI_STACK_CHECKLIST and LESSONS_FROM_THREE_UPLOADS_PHD).

---

## 3. Mouse Accuracy Classic: Spawning targets and aim correction

**Files:** `operator/cre/project_understanding/tools/mouse_accuracy_suite.py`

### 3.1 Classic game (multiple simultaneous / spawning targets)

- **Site:** `https://mouseaccuracy.com/classic/`
- **Behavior:** After “Start”, multiple circular targets appear (DOM); they can spawn and disappear over time. Speed/size configurable (Slow/Normal/Fast/Epic; Tiny/Small/Medium/Large).
- **Flow:**
  1. Mission control + evidence; navigate to Classic URL; optional JS click for speed/size; JS click “Start”.
  2. Wait until `_query_classic_state()` returns `targets` (list of `{ cx, cy }`).
  3. **Viewport origin:** From page `screenX`/`screenY` or Safari window bounds + content inset (so client coords map to global).
  4. **Per-click aim correction:** For each target `t`, intended click = `(t["cx"] + running_aim_x, t["cy"] + running_aim_y)`. Call `click_client_point(intended_cx, intended_cy, profile, viewport_origin=..., position_errors=position_errors)`.
  5. **Position error feedback:** Before posting the click, `click_client_point` does `_smooth_move` to `(gx, gy)`, then reads **actual cursor position** via `_get_cursor_position()` (cliclick `p`). It appends `(actual_x - gx, actual_y - gy)` to `position_errors`. The harness then updates `running_aim_x`, `running_aim_y` by subtracting this error (clamped to `AIM_OFFSET_X_MIN/MAX`, `AIM_OFFSET_Y_MIN/MAX`), so the **next** click is biased to correct for systematic drift.
  6. **Clear-rate heuristic:** If many targets were present and few cleared, `running_aim_y` is decreased (step `AIM_ADJUST_STEP`); if most cleared, it may increase. So the agent **adapts aim over the round** using both per-click cursor error and clear rate.

So “moving objects” here means **target list changes over time** (spawn/disappear). The agent does **not** predict target motion; it **queries current targets**, clicks one or more, then re-queries. The distinctive part is **closed-loop aim correction** using measured cursor position vs intended click and clear rate.

### 3.2 Main game (canvas-only, no DOM targets)

- **Site:** `https://mouseaccuracy.com/game`
- **Behavior:** Canvas-based; no DOM target list. The harness may wait for countdown then either (a) get DOM targets if the game exposes them, or (b) wait for round end and look for result text (“canvas_only_no_dom_targets” path). So for **canvas-only moving targets**, the repo currently has no pixel-based tracker; it falls back to “wait and see results” or future vision loop.

---

## 4. XBitLabs Path Follow: Cursor along a fixed path

**Files:** `operator/cre/project_understanding/tools/xbitlabs_path_follow.py`

### 4.1 Path Follow (cursor moves; path is static)

- **Site:** `https://www.xbitlabs.com/mouse-accuracy-test/` (Path Follow tab, Easy).
- **Behavior:** User clicks green start; a path (e.g. curve) is shown; cursor must stay on the path while moving. The path itself doesn’t move; **cursor motion** is what’s under test.
- **Flow:**
  1. Mission control + evidence (or `--skip-evidence`); navigate; set viewport origin from `screenX`/`screenY` or window bounds.
  2. Click “Path Follow” tab, “Easy”, then green start (with retries/offsets if needed).
  3. **Precomputed path:** A list of (x, y) viewport points from left to right (e.g. `x_start` to `x_end`, `y_mid` constant, with margin). For each point, `_global_from_client(px, py, viewport_origin)` → `_smooth_move(gx, gy, path_duration/path_steps, 3)` (no click). So the cursor **smoothly moves along the path**.
  4. Periodically `_query_xbitlabs_state()` (JS) for `accuracy`, `deviation`, `progress`. If `progress >= 100` break. Pass = e.g. accuracy ≥ 50% or progress 100%.

So this is **cursor test on a static path** (moving the cursor, not tracking a moving target). Motion is again **Quartz** (`_smooth_move`), linear interpolation step-by-step. No drag; no Bezier in this harness (Bezier is in CodexClient/kernel).

### 4.2 Run all stages

- `run_all_stages` runs Path Follow for multiple stages (e.g. 1/5–5/5), recomputing green start from canvas rect each time and adapting path or parameters. Same idea: **cursor follows a planned path**; success is read from page state (accuracy, deviation, progress).

---

## 5. Ultimate Tests: Moving targets and drag-and-drop (design and kernel)

**Files:** `operator/cre/ULTIMATE_TESTS.md`, `operator/codex_client.py`, `operator/cre/codex_kernel.lua`

### 5.1 Test 2: Real-time reaction – moving target (vision loop)

- **Objective:** Track and click **moving** targets in an aim trainer or slider puzzle.
- **Claim:** Old `screencapture` has ~294 ms disk I/O → too slow; in-memory/region capture + fast loop can track dynamic elements.
- **Designed loop (ULTIMATE_TESTS.md):**
  - Continuously capture a **region** (e.g. center 800×600) via `client.screenshot({'x': 320, 'y': 150, 'w': 800, 'h': 600})`.
  - `detect_target(img)` (OCR or color detection – not implemented in repo; placeholder).
  - If target found: `client.smooth_move_and_click(target_x, target_y, steps=15, duration=0.2)`.
  - `time.sleep(0.1)` → ~10 FPS vision loop.
- **CodexClient:** `smooth_move_and_click` gets current position from kernel `get_mouse_position`, builds a **cubic Bezier** path (control points 25% and 75% with small randomness), then streams `move_mouse` for each step. So **cursor** motion is Bezier; **target** position would come from vision (not implemented in repo). Status: “Ready to test – needs aim trainer URL and coordinate detection.”

### 5.2 Test 3: Drag-and-drop (moving an object by dragging)

- **Objective:** Locate objects (e.g. blue icons on desktop), then **drag** them to a drop zone (e.g. Finder).
- **Flow (design):** Capture region → detect icon positions → get drop zone → for each icon `client.drag(icon_x, icon_y, finder_x, finder_y)`.
- **CodexClient.drag(start_x, start_y, end_x, end_y):** Sends `drag` command to kernel with start/end. No cursor “test” in the sense of scoring; it’s **execution** of a drag.
- **codex_kernel.lua `commands.drag`:**
  - Move to start; 50 ms; post leftMouseDown at start.
  - **Smooth drag:** 20 steps along a **cubic Bezier** from start to end (control points 25% and 75%); each step `hs.mouse.setAbsolutePosition` + 10 ms.
  - Post leftMouseUp at end.
- **test_drag_drop.py:** Calls `client.drag(100, 100, 800, 600)` after 3 s delay; no visual detection, just kernel drag. So **cursor test on moving objects** for drag = “did the kernel perform a smooth drag?” not “did we track a moving target.”

---

## 6. Smooth motion: Quartz vs Hammerspoon kernel

| Location | Method | How motion is generated |
|----------|--------|---------------------------|
| **human_benchmark_suite** | `_smooth_move(x, y, duration, steps)` | Linear interpolation; current pos from `cliclick p`; each step Quartz `CGEventCreateMouseEvent(MouseMoved)` + sleep. |
| **mouse_accuracy_suite** | Same `_smooth_move` (import/cliclick) | Same: linear, Quartz. |
| **xbitlabs_path_follow** | Same pattern | Same: linear, Quartz. |
| **CodexClient** | `smooth_move_and_click`, `move_mouse` | **Cubic Bezier** (control points 25%, 75% + jitter); requests to Hammerspoon kernel; kernel uses `hs.mouse.setAbsolutePosition` and/or eventtap. |
| **codex_kernel.lua** | `commands.drag`, `commands.move_mouse` | Bezier for drag; `move_mouse` = single absolute position. |

So: **Harnesses (Human Benchmark, Mouse Accuracy, XBitLabs)** use **Quartz + cliclick** for position and linear interpolation. **CodexClient + kernel** use **Bezier** and are intended for human-like motion and drag; they are used in ultimate-test **design** and in `test_drag_drop`, but the main **agent_core** drawing path uses **Quartz** (`execute_draw_path`), not the kernel.

---

## 7. Where “cursor test” and “moving objects” appear in the repo

| Concept | Where it appears |
|---------|-------------------|
| **Aim trainer (discrete new target per click)** | `human_benchmark_suite.run_aim`; `query_aim_state` → target → `click_client_point`. |
| **Reaction time (green at random time)** | `human_benchmark_suite.run_reactiontime`; poll `isGreen` → click box. |
| **Spawning / multiple DOM targets** | `mouse_accuracy_suite.run_classic_game`; `_query_classic_state().targets`; per-target click + aim correction. |
| **Aim correction (cursor vs intended)** | `mouse_accuracy_suite`: `click_client_point(..., position_errors=...)`; `_get_cursor_position()` (cliclick `p`); `running_aim_x/y` updated from error and clear rate. |
| **Path follow (cursor along path)** | `xbitlabs_path_follow.run`: precomputed path points → `_smooth_move` along path; progress/accuracy from JS. |
| **Moving target (vision loop)** | `ULTIMATE_TESTS.md` Test 2; `CodexClient.screenshot` + `smooth_move_and_click`; `detect_target` not in repo. |
| **Drag (move object A→B)** | `codex_kernel.lua` `commands.drag`; `CodexClient.drag`; `test_drag_drop.py`. |
| **Live stack / evidence** | All Safari harnesses: `mission_control.py up live`, `_ensure_safari_ready()`, viewport from bounds + inset (LIVE_SAFARI_STACK_CHECKLIST, LESSONS_FROM_THREE_UPLOADS_PHD). |

---

## 8. Design choices and tradeoffs

- **State from DOM/JS vs pixels:** Aim trainer, reaction, mouse accuracy classic use **in-page JS** to get target positions and timing. That avoids image-based detection and is fast and precise when the site exposes state. Canvas-only games (e.g. mouseaccuracy.com main game) don’t expose targets → either wait for results or need a **vision** loop (ULTIMATE_TESTS Test 2).
- **Aim correction:** Only **mouse_accuracy_suite** classic implements **closed-loop** correction (cursor position error + clear rate). Human Benchmark aim trainer does not; it assumes viewport→global mapping is good (calibrated offset).
- **Smooth motion:** Linear (Quartz) in harnesses; Bezier in CodexClient/kernel. Ultimate tests and academic notes (e.g. SapiAgent, IEEE Access 2021) favor Bezier for human-like motion; harnesses keep Quartz for simplicity and no kernel dependency.
- **Kernel dependency:** CodexClient + codex_kernel.lua require Hammerspoon on port 9999. The main agent (agent_core, action_handlers) does **not** use the kernel; it uses Quartz only. So **cursor tests on moving objects** that use **Bezier and drag** are in the **Codex/harness** layer; the **constitutional** agent path uses Quartz draw_path/click.

---

## 9. Summary table: file → cursor/moving-object role

| File | Role for cursor tests / moving objects |
|------|----------------------------------------|
| **human_benchmark_suite.py** | Aim trainer (discrete moving targets via DOM); reaction time (temporal “moving” green); smooth move + click via Quartz; MotionProfile. |
| **mouse_accuracy_suite.py** | Classic: spawning DOM targets; per-click aim correction (cursor position error + clear rate); viewport origin; main game: canvas fallback (no target list). |
| **xbitlabs_path_follow.py** | Path Follow: cursor along fixed path; precomputed points; smooth move (no click along path); progress/accuracy from JS. |
| **codex_client.py** | Bezier smooth_move_and_click; drag(start, end); get_mouse_position; screenshot (region); for ultimate-test vision loop and test_drag_drop. |
| **codex_kernel.lua** | drag (Bezier); move_mouse; get_mouse_position; click; draw_path (continuous stroke). |
| **ULTIMATE_TESTS.md** | Spec for Test 2 (moving target vision loop) and Test 3 (drag-and-drop); status and required kernel commands. |
| **test_drag_drop.py** | Integration test: CodexClient.drag(100,100,800,600). |
| **agent_core.py** | execute_move_mouse, execute_global_click, execute_draw_path (Quartz); used by main agent, not by Human Benchmark / Mouse Accuracy / XBitLabs harnesses (they use their own _smooth_move/_click_here). |

This is the full research map for **cursor tests and moving objects** in the project: what exists, where it lives, and how it works.
