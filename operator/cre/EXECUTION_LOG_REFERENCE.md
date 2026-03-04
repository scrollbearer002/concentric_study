# Excalidraw CoVT Test: Full Execution Timeline (Run Start → Triangle Mouse-Up)

This document describes **every step** that occurs from the moment you run the test until the mouse button is released after drawing the triangle. Use it together with `execution_log.txt` (written each run) for exhaustive debugging.

---

## 1. Run bootstrap

| Step | What happens | Where |
|------|----------------|------|
| 1.1 | Script starts; `execution_log.txt` is created/truncated and `EXECUTION_LOG_PATH` is set so all modules append to it. | `test_excalidraw_covt.py` → start of `run_model_based_agent()` |
| 1.2 | Log line: `run_start \| test_excalidraw_covt.py` | |
| 1.3 | Mode chosen: Enterprise (if `GEMINI_API_KEY`/`OPENAI_API_KEY` set and `agent_core`/`visual_engine` load) or Legacy. | |
| 1.4 | Enterprise: `MacOSAgentCore()` and `VisualGroundingEngine(grid_size=12)` are constructed. Log: `init \| MacOSAgentCore + VisualGroundingEngine` | |
| 1.5 | Screen info read via `agent.get_screen_info()` (scale factor, logical size). | `agent_core.get_screen_info()` |

---

## 2. PHASE 1: Page load and initial observation

| Step | What happens | Where |
|------|----------------|------|
| 2.1 | Log: `phase \| PHASE 1: PAGE LOAD & INITIAL OBSERVATION` | |
| 2.2 | `subprocess.run(["open", "-a", "Safari", "https://excalidraw.com"])` runs. Log: `safari_open` then `safari_opened \| ok` (or error). | |
| 2.3 | 10-second countdown; each second no log, then `wait_start \| 10 seconds`, then `wait_complete \| ok`. | |
| 2.4 | Safari window maximized via AppleScript: `tell application "Safari" to set bounds of front window to {0, 22, W, H}`. Log: `safari_maximize \| ok` with `w`, `h`. | |
| 2.5 | `agent.enforce_app_focus("Safari")`: osascript activate (if needed), then NSWorkspace poll until `frontmostApplication().localizedName()` contains "Safari", then ~0.55s sleep. Log: `enforce_focus \| Safari` and frontmost app name. | `agent_core.enforce_app_focus()` |
| 2.6 | Full-screen screenshot: `screencapture -x current_state.png`. | |
| 2.7 | SoM overlay: `VisualGroundingEngine.generate_som_overlay(current_state.png)` → 12×12 grid, coordinate map, `som_overlay.png`. Log: `som_overlay` with zone count. | `visual_engine.generate_som_overlay()` |
| 2.8 | UI analysis: screenshot uploaded to Gemini File API, structured output (canvas_center_x, canvas_center_y, page_loaded). `ui_analysis["canvas_center"] = {x, y}` set. | `agent_core.analyze_ui()` |

---

## 3. PHASE 3: Action planning

| Step | What happens | Where |
|------|----------------|------|
| 3.1 | Log: `phase \| PHASE 3: ACTION PLANNING` with list of action descriptions. | |
| 3.2 | Plan generated: 5 actions (Select pen `p`, Draw triangle path, Open stroke color `S`, Click red swatch, Final verification). Triangle vertices in **screenshot pixels**: top `(center_x, center_y - 220)`, bottom-left `(center_x - 220, center_y + 220)`, bottom-right `(center_x + 220, center_y + 220)`, close `(center_x, center_y - 220)`. | `generate_action_plan()` |

---

## 4. PHASE 4: Execution (up to and including triangle draw)

| Step | What happens | Where |
|------|----------------|------|
| 4.1 | Log: `phase \| PHASE 4: EXECUTION`. | |
| 4.2 | **Move cursor to canvas center:** `agent.execute_move_mouse(cx, cy)` with `cx, cy` from `ui_analysis["canvas_center"]`. Log: `move_mouse` (from agent_core) then test log `move_cursor_to_canvas` with `cx`, `cy`. | `agent_core.execute_move_mouse()` |
| 4.3 | `time.sleep(0.2)`. | |

### Action 1: Select pen tool (p)

| Step | What happens | Where |
|------|----------------|------|
| 4.4 | Log: `action_start` with index 1, type `keystroke`, description. | |
| 4.5 | `agent.enforce_app_focus("Safari")` (again). | |
| 4.6 | Log: `action_keystroke` with `key: "p"`. | |
| 4.7 | `agent.execute_keystroke("p")`: keycode 35 (kVK_ANSI_P), log `keystroke_prep`, then JIT `enforce_app_focus("Safari")`, then `keystroke_post \| key_down`, CGEventPost key down, sleep 0.05s, CGEventPost key up, `keystroke_post \| key_up`. | `agent_core.execute_keystroke()` |
| 4.8 | `time.sleep(0.3)`. | |
| 4.9 | Visual assertion: screencapture, upload to File API, VLM asked "Is the Pen tool selected? YES or NO."; on NO, RuntimeError. | |
| 4.10 | Verification screenshot saved (e.g. `verify_2.png`). | |

### Action 2: Draw triangle path

| Step | What happens | Where |
|------|----------------|------|
| 4.11 | Log: `action_start` with index 2, type `draw_path`, description. | |
| 4.12 | `agent.enforce_app_focus("Safari")`. | |
| 4.13 | Optional debug write to `debug-a16689.log` (after_enforce_before_draw_work, frontmost app). | |
| 4.14 | **Vertices:** From plan `vertices` (absolute pixel coords). **Relative path:** `(v[0]-cx, v[1]-cy)` for each vertex → e.g. `(0, -220), (-220, 220), (220, 220), (0, -220)`. Log: `action_draw_path` with `canvas_center`, `vertices_raw`, `relative_path`. | |
| 4.15 | **`agent.execute_draw_path(relative_path, cx, cy)`** — this is the full sequence from “start draw” to “release click”: | `agent_core.execute_draw_path()` |

#### Inside `execute_draw_path` (start to mouse-up)

| Step | What happens | Where |
|------|----------------|------|
| 4.15.1 | **Prep (before any focus):** For each `(px, py)` in `relative_path`, compute global Quartz coords: `_pixel_to_global_quartz(center_x + px, center_y + py)` (scale by `backingScaleFactor()`, add screen frame origin). Build list `global_points`. | `_pixel_to_global_quartz()` |
| 4.15.2 | Log: `draw_path_prep` with `center_x`, `center_y`, `relative_path`, `global_points` (rounded). | `_exec_log()` |
| 4.15.3 | **JIT focus:** `enforce_app_focus("Safari", timeout_seconds=2.0, poll_interval=0.05)`. | |
| 4.15.4 | Log: `draw_path_event \| mouse_down` with first point `(x, y)`. | |
| 4.15.5 | **Mouse down:** `CGPointMake(start_x, start_y)` → `CGEventCreateMouseEvent(..., kCGEventLeftMouseDown, ...)` → `CGEventPost(kCGHIDEventTap, event_down)`. | Quartz |
| 4.15.6 | `time.sleep(0.1)`. | |
| 4.15.7 | **For each subsequent point in `global_points`:** Log: `draw_path_event \| mouse_dragged` with index and `(x, y)`; create left-mouse-dragged event; `CGEventPost`; `time.sleep(0.02)`. | |
| 4.15.8 | Log: `draw_path_event \| mouse_up` with last point `(x, y)`. | |
| 4.15.9 | **Mouse up:** `CGEventCreateMouseEvent(..., kCGEventLeftMouseUp, last_point, ...)` → `CGEventPost(kCGHIDEventTap, event_up)`. **This is the moment the click is released.** | Quartz |
| 4.15.10 | `time.sleep(0.3)` (canvas commit). Log: `draw_path_done` with `points_posted`. | |

| Step | What happens | Where |
|------|----------------|------|
| 4.16 | Back in test script: `time.sleep(0.5)`. | |
| 4.17 | Visual assertion: "Is there a triangle shape drawn on the Excalidraw canvas? YES or NO." | |
| 4.18 | Verification screenshot (e.g. `verify_3.png`) saved. | |

Actions 3–5 (stroke color keystroke, red swatch click, final verification) continue after this; the **triangle drawing** is complete at step 4.15.9.

---

## 5. Where to find the logs

- **Session log (every run):** `operator/cre/execution_log.txt`  
  - Timestamped lines for: run_start, mode, init, phase, safari_open, wait, maximize, enforce_focus, som_overlay, action_start, action_keystroke / action_draw_path / action_click, and from agent_core: keystroke_prep/post, move_mouse, click_prep/post, draw_path_prep, draw_path_event (mouse_down, mouse_dragged, mouse_up), draw_path_done, run_complete.
- **Debug log (agent_core + test):** `operator/cre/debug-a16689.log`  
  - JSON lines: focus_verified, before_post_keystroke, before_post_draw_path, after_enforce_before_draw_work, etc.
- **Verification screenshots:** `operator/cre/verify_2.png`, `verify_3.png`, … (after each state-changing action).

---

## 6. Summary: from “run” to “release click”

1. Execution log and env set → mode and init.
2. Safari opened → 10s wait → Safari maximized → Safari focus enforced.
3. Screenshot → SoM overlay → UI analysis (canvas center).
4. Action plan: pen `p`, draw_path (triangle), stroke `S`, click red, verify.
5. Cursor moved to canvas center; then Action 1: focus → keystroke `p` (keycode 35, down then up) → assert Pen selected.
6. Action 2: focus → relative path from triangle vertices → **execute_draw_path**: all global points computed → focus again → **mouse_down** at first point → **mouse_dragged** for each middle point → **mouse_up** at last point → sleep 0.3s.

The **exact coordinates** (pixel and global) and **every mouse event** for the triangle are in `execution_log.txt` under `draw_path_prep`, `draw_path_event`, and `draw_path_done`.
