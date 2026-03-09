# Tools and Permissions: Deep Research Dive

This document catalogs **what in the codebase** enables “open Safari, go to a drawing site, and draw” — i.e. the tools and permissions the agent has, file by file, and how they chain together.

---

## 1. Executive summary

To drive Safari and draw on a canvas, the system uses:

| Layer | What it does | Primary files |
|-------|----------------|---------------|
| **Open Safari / navigate** | Launch Safari, set URL, activate window | `agent.py`, `action_handlers.py`, AppleScript |
| **Focus** | Make Safari frontmost so clicks land in the right app | `agent_core.py` (NSWorkspace + Quartz) |
| **Screenshot** | Capture what’s on screen (full or window) | `window_capture.py`, `screencapture` CLI, `agent_core.py` (Gemini File API) |
| **Perception** | See elements (a11y tree, visual SoM, fused map) | `a11y_engine.py`, `visual_engine.py`, `element_map.py` |
| **Click** | Post a single mouse click at global coordinates | `agent_core.execute_global_click` → Quartz |
| **Move mouse** | Move cursor without clicking | `agent_core.execute_move_mouse` → Quartz |
| **Draw (path)** | Mouse down → drag through points → mouse up | `agent_core.execute_draw_path` / `execute_draw_path_segments` → Quartz |
| **Keystroke** | Send key + modifiers (e.g. Cmd+Backspace, “p” for pen) | `agent_core.execute_keystroke` → Quartz |
| **High-level actions** | “click”, “draw_shape”, “go_to_url”, “type_text”, etc. | `action_handlers.py` → calls agent_core |
| **Health / permissions check** | Ensure Python, Quartz, screencapture, Safari, System Events are available | `host_tool_health.py`, `tool_health_catalog.json`, `gui_evidence.py` |

**Permissions the machine needs (macOS):**

- **Input (Quartz HID):** The process posting `CGEventPost(Quartz.kCGHIDEventTap, …)` must be allowed to **control the computer** (Accessibility / Input Monitoring). Otherwise clicks and keystrokes are ignored.
- **Automation (AppleScript / System Events):** For “tell application Safari to …” and “tell application System Events …”, the app (e.g. Terminal or Cursor) needs **Automation** permission for Safari and System Events. Denial shows as `-1743` / “not authorized to send apple events”.
- **Screen capture:** `screencapture` and any CGWindowListCopyWindowInfo usage need **Screen Recording** (and/or Accessibility, depending on OS). Without it, screenshots can fail or be restricted.
- **Accessibility (optional but used):** For a11y tree extraction (AXUIElement), the app may need **Accessibility** permission; the code falls back to AppleScript when a11y is denied.

There is no single “permission file” in the repo — the repo **uses** the OS APIs; macOS **enforces** the permissions via TCC (Transparency, Consent, and Control).

---

## 2. File-by-file tools and permissions

### 2.1 `operator/agent_core.py`

**Role:** State Machinery Depot — the layer that actually moves the mouse and keyboard and verifies focus.

**Dependencies (imports):**

- `Quartz` (pyobjc-framework-Quartz): `CGEventCreateMouseEvent`, `CGEventPost`, `kCGHIDEventTap`, `kCGEventLeftMouseDown`, `kCGEventLeftMouseDragged`, `kCGEventLeftMouseUp`, `kCGEventMouseMoved`, `CGPointMake`, keyboard events.
- `AppKit` (pyobjc-framework-Cocoa): `NSWorkspace`, `NSScreen`, `NSRunningApplication`, `NSApplicationActivateIgnoringOtherApps`, `NSApplicationActivateAllWindows`.
- `window_capture.get_frontmost_application_name` (for focus checks).

**Tools (methods) that enable “draw in Safari”:**

| Method | What it does | Permission / backend |
|--------|----------------|----------------------|
| `enforce_app_focus(app_name="Safari", ...)` | Brings Safari to front via `NSRunningApplication.activateWithOptions_`; falls back to `osascript -e 'tell application "Safari" to activate'`. Polls until `get_frontmost_application_name()` matches. | NSWorkspace + optional AppleScript → Automation for Safari. |
| `execute_global_click(local_pixel_x, local_pixel_y, app_focus="Safari", ...)` | Converts pixel to global Quartz coords, optionally enforces focus, then posts `kCGEventLeftMouseDown` and `kCGEventLeftMouseUp` at that point. | Quartz → **Input Monitoring / Accessibility** (control computer). |
| `execute_move_mouse(local_pixel_x, local_pixel_y, app_focus="Safari", ...)` | Same coordinate conversion and focus; posts `kCGEventMouseMoved` only. | Quartz → same as above. |
| `execute_draw_path(path_coordinates, center_x, center_y, app_focus="Safari", drag_delay=0.02, ...)` | Converts relative path to global points, enforces focus, then: mouse down at first point → sequence of `kCGEventLeftMouseDragged` at each point (with `drag_delay`) → mouse up at last point. | Quartz → same. |
| `execute_draw_path_segments(...)` | Per-segment draw: for each segment, mouse down at A → drag to B → mouse up at B. Used for polygons / multi-stroke shapes. | Quartz → same. |
| `execute_draw_path_with_modifier(..., modifier="shift")` | Same as draw path but holds Shift (e.g. for Kleki straight lines). | Quartz + keycode 56 + kCGEventFlagMaskShift. |
| `execute_keystroke(key, app_focus="Safari", modifiers=None)` | Maps key to macOS keycode, applies modifier flags, posts key down and key up. Used for tool shortcuts (e.g. “p” = pen), Cmd+Backspace, etc. | Quartz → same. |

**Coordinate conversion:** `_pixel_to_global_quartz` uses scale factor and capture origin (from window bounds or display) so that “pixel in screenshot” maps to “global Quartz point” where the event is posted. This depends on `window_capture` and/or NSScreen for geometry.

**Other capabilities:** `visually_extract_target`, `analyze_ui`, etc. use Gemini File API (upload screenshot, get structured response). No extra OS permission; needs network and API key.

---

### 2.2 `operator/window_capture.py`

**Role:** Window-scoped screenshot and frontmost-app/window metadata.

**Dependencies:**

- `Quartz`: `CGWindowListCopyWindowInfo`, `kCGWindowListOptionOnScreenOnly`, `kCGWindowBounds`, `kCGWindowOwnerName`, `kCGWindowNumber`, `kCGWindowLayer`, `kCGWindowAlpha`.
- `AppKit`: `NSWorkspace` (fallback for frontmost app).
- `subprocess`: runs `screencapture`.

**Tools:**

| Function | What it does | Permission / backend |
|----------|----------------|----------------------|
| `get_frontmost_application_name()` | Uses Quartz window list (z-order) for first eligible window owner; fallback NSWorkspace.frontmostApplication(). | Quartz/AppKit — may need Screen Recording or Accessibility for full fidelity. |
| `get_front_window_info(owner_name=None)` | Returns first eligible onscreen window’s owner, window_id, bounds (for Safari window). | Same. |
| `capture_front_window(path, owner_name=None, ...)` | If front window found: `screencapture -x -o -l <window_id> <path>`. Else: `screencapture -x <path>` (full display). | **Screen Recording** (and possibly Accessibility) for `screencapture` and CGWindowListCopyWindowInfo. |

So: **screenshots and “which window is in front”** come from this file; **posting click/drag/key** comes from `agent_core.py`.

---

### 2.3 `operator/agent.py`

**Role:** Executive — opens Safari, orchestrates flow, calls handlers and agent_core.

**Tools relevant to “Safari + drawing site”:**

| Symbol | What it does | Permission / backend |
|--------|----------------|----------------------|
| `_open_safari(url)` | `subprocess.run(["open", "-a", "Safari", url], ...)`. | None beyond run subprocess. |
| `_maximize_safari(agent=None)` | (Uses agent or other means to maximize; implementation may use AppleScript.) | Automation if AppleScript. |
| Later in flow | Calls `agent.enforce_app_focus("Safari")`, passes context to action_handlers which call `ctx.agent.execute_global_click`, `execute_draw_path`, etc. | As in agent_core + window_capture. |

So **opening Safari and sending it a URL** is done here; **actual input** is delegated to `agent_core` and **semantic actions** to `action_handlers`.

---

### 2.4 `operator/agent_infra/action_handlers.py`

**Role:** Ministry of Interior — maps legal action names (from `action_space`) to concrete operations, many of which end in agent_core.

**Tools relevant to drawing and Safari:**

| Handler / behavior | What it does | Permission / backend |
|--------------------|----------------|----------------------|
| `_handle_go_to_url(ctx, args)` | `osascript -e 'tell application "Safari" to set URL of current tab of front window to "..."'`. | **Automation** for Safari. |
| `_handle_click(ctx, args)` | Resolves label or (x,y); optionally preclick confirmation; then `ctx.agent.execute_global_click(pixel_x, pixel_y)`. | Quartz (via agent_core) + optional SoM/VLM. |
| `_handle_draw_shape(ctx, args)` | For rectangle/ellipse/diamond: computes bounding box, then `agent.execute_draw_path([top_left, bottom_right], cx, cy)`. | Quartz via agent_core. |
| `_handle_drag_shape` | Same idea: one drag from A to B via `execute_draw_path`. | Same. |
| Draw-path-style handlers | Call `ctx.agent.execute_draw_path_segments(vertices, ctx.cx, ctx.cy)` or `execute_draw_path(relative_path, ctx.cx, ctx.cy, ...)`. | Same. |
| `ctx.agent.enforce_app_focus("Safari")` | Called before many actions so clicks/keys go to Safari. | NSWorkspace + AppleScript as in agent_core. |
| Screenshot for SoM/color | `subprocess.run(["screencapture", "-x", path], ...)`. | Screen Recording. |

So **high-level “click”, “draw_shape”, “go_to_url”** are implemented here; they all ultimately rely on **agent_core (Quartz)** and **screencapture / AppleScript** with the permissions above.

---

### 2.5 `operator/a11y_engine.py`

**Role:** Survey Office — accessibility tree extraction for semantic elements and, when available, coordinates.

**Dependencies:**

- Prefers `macapptree`, then `pyax`, then AppleScript (`tell application "System Events" to tell process "Safari" ...`).

**Tools:**

- `A11yEngine.extract(app_name="Safari")`: returns list of `A11yElement` (role, label, position, size, etc.). Used by element_map and handlers to resolve “click the Submit button” to coordinates.

**Permission:** Using **System Events** and process "Safari" requires **Automation** (and often **Accessibility**). The code treats “accessibility_denied” / “automation_denied” as blockers in `gui_evidence.py`.

---

### 2.6 `operator/visual_engine.py`, `operator/element_map.py`

**Role:** Visual grounding (Set-of-Mark) and fusion of a11y + visual into one map.

- **visual_engine:** Uses screenshots and VLM/SoM to get box IDs and coordinates for “click here”.
- **element_map:** Merges a11y elements and visual boxes so handlers can resolve by label or box.

They don’t post events themselves; they produce **coordinates and labels** that `action_handlers` turns into `execute_global_click` / `execute_draw_path` in agent_core.

---

### 2.7 `operator/agent_infra/host_tool_health.py` + `operator/agent_infra/tool_health_catalog.json`

**Role:** Before running a live task, the stack can check that required tools exist and are usable.

**Required classes for URL/browser tasks (from catalog):**

- `runtime_python_selected`: operator venv Python, version, core imports.
- `macos_ui_automation`: `osascript` exists and `tell application "System Events" to return true` succeeds → **System Events Automation**.
- `native_event_backend`: Python can `import AppKit, Quartz` → **PyObjC** (Quartz for posting events).
- `screen_capture`: `screencapture` command exists.
- `browser_target`: Safari app bundle exists (path from catalog).

So the **tools** the repo checks are: Python + PyObjC (Quartz/AppKit), osascript + System Events, screencapture, Safari. The **permissions** (Input Monitoring, Automation, Screen Recording) are not explicitly checked in code; they are implied by “does the probe succeed?”. If System Events returns “not authorized”, the probe fails and the catalog reports that.

---

### 2.8 `operator/cre/project_understanding/tools/gui_evidence.py`

**Role:** Evidence gate for live GUI tasks — run AppleScript probes and interpret failures as permission blockers.

**Relevant logic:**

- Runs osascript scripts (e.g. “tell application System Events” / “tell process Safari”).
- Classifies stderr: `automation_denied` (“not authorized to send apple events”, “-1743”), `accessibility_denied` (“assistive access”, “accessibility”), `not_running`, etc.
- Documents that **Apple Events and System Events may be blocked by TCC** and must be treated as hard blockers.

So this file **surfaces** permission failures; it doesn’t grant permissions — macOS does that in System Settings (Privacy & Security → Accessibility, Screen Recording, Automation).

---

### 2.9 `operator/cre/project_understanding/tools/live_validation_harnesses.py`

**Role:** Harnesses that run live checks (e.g. Safari visible, click fixture). Call `_make_agent_core().enforce_app_focus(app_name)` and use Quartz for frontmost; note that Safari’s accessibility tree may not expose every UI element (e.g. canvas).

---

### 2.10 Optional: `operator/cre/codex_kernel.lua` (Hammerspoon)

**Role:** Alternative backend for click/drag/keystroke via Hammerspoon (listens on localhost, receives JSON, calls `hs.eventtap`, `hs.mouse`). Not required for the main agent_core path; agent_core uses **Quartz (PyObjC)** directly. If used, Hammerspoon itself needs **Accessibility** (and possibly Automation) to inject events.

---

## 3. Permission matrix (what the OS must allow)

| Capability | macOS permission / requirement | Where it’s used in repo |
|------------|--------------------------------|---------------------------|
| Post mouse/key events (click, drag, keystroke) | **Accessibility** and/or **Input Monitoring** (control the computer) | `agent_core.py` — all `CGEventPost(Quartz.kCGHIDEventTap, …)` |
| Bring app to front (Safari) | NSWorkspace (often allowed for same-user apps) + optional **Automation** if fallback osascript is used | `agent_core.enforce_app_focus` |
| “Tell application Safari” / “tell application System Events” | **Automation** (Safari, System Events) | `action_handlers._handle_go_to_url`, `a11y_engine` AppleScript fallback, various scripts |
| Screenshot (screencapture, CGWindowListCopyWindowInfo) | **Screen Recording** (and sometimes Accessibility) | `window_capture.capture_front_window`, `action_handlers` screencapture, `agent_core` if using local screenshot path |
| Read accessibility tree (AXUIElement or System Events UI) | **Accessibility** (and Automation for System Events) | `a11y_engine.py`, `gui_evidence.py` probes |

So: **the IDE (or terminal) process that runs the agent** must be granted these permissions in System Settings. The repo does not “have” permissions; it **uses** APIs that macOS protects.

---

## 4. Chain from “draw a Picasso in Safari” to hardware

1. **agent.py** (or a CRE runner): Decides to open a drawing site; calls `_open_safari(url)` or a handler that does `go_to_url`.
2. **action_handlers._handle_go_to_url**: Runs AppleScript to set Safari’s current tab URL → **Automation**.
3. **agent_core.enforce_app_focus("Safari")**: Brings Safari to front → **NSWorkspace / Automation**.
4. **Perception:** Screenshot (window_capture or screencapture) → **Screen Recording**. Optional: a11y_engine (→ **Accessibility/Automation**), visual_engine/element_map for canvas center and tool positions.
5. **Planning:** research_agent / action_space produce actions like `draw_shape`, `click`, `draw_path` with coordinates or tool keys.
6. **action_handlers._handle_draw_shape / _handle_click / draw_path**: Resolve to center (cx, cy) and relative path or bbox; call:
   - `ctx.agent.execute_global_click(x, y)` for clicks, or
   - `ctx.agent.execute_draw_path(...)` / `execute_draw_path_segments(...)` for strokes.
7. **agent_core**: For each call, converts pixel → global Quartz, enforces Safari focus again if needed, then posts:
   - `kCGEventLeftMouseDown` → `kCGEventLeftMouseDragged` (×N) → `kCGEventLeftMouseUp` for drawing;
   - or single down+up for click.
8. **Quartz** delivers events to the window server → Safari receives them as if the user had drawn. This requires the process to be allowed to **control the computer** (Input Monitoring / Accessibility).

So: **every file above contributes one link**; the **permissions** are the OS gate on step 2 (Automation), step 4 (Screen Recording / Accessibility), and step 8 (Input Monitoring / Accessibility).

---

## 5. Summary table: files → tools → permissions

| File | Tools provided | Permissions / dependencies |
|------|----------------|----------------------------|
| **agent_core.py** | enforce_app_focus, execute_global_click, execute_move_mouse, execute_draw_path, execute_draw_path_segments, execute_draw_path_with_modifier, execute_keystroke | Quartz + AppKit (PyObjC). Input Monitoring / Accessibility. Optional AppleScript for focus → Automation. |
| **window_capture.py** | get_frontmost_application_name, get_front_window_info, capture_front_window | Quartz (window list), subprocess(screencapture). Screen Recording. |
| **agent.py** | _open_safari, _maximize_safari, orchestration → agent_core + action_handlers | subprocess(open), Automation if AppleScript. |
| **action_handlers.py** | _handle_go_to_url, _handle_click, _handle_draw_shape, _handle_drag_shape, draw_path handlers | AppleScript (Safari URL) → Automation. agent_core (click/draw) → Quartz. screencapture → Screen Recording. |
| **a11y_engine.py** | A11yEngine.extract (tree + coordinates) | macapptree/pyax or AppleScript System Events → Accessibility + Automation. |
| **visual_engine.py** | SoM / VLM coordinate extraction | Screenshot + API; no extra OS permission. |
| **element_map.py** | Fused map (a11y + visual) | Depends on a11y + screenshot. |
| **host_tool_health.py** + **tool_health_catalog.json** | Checks: Python, Quartz/AppKit, osascript+System Events, screencapture, Safari bundle | Probes for tool presence and Automation success; does not grant permissions. |
| **gui_evidence.py** | Classifies Automation/Accessibility denial from osascript | Surfaces TCC blockers; does not grant permissions. |

This is the full set of **tools and permissions** that let the agent open Safari, go to a drawing site, and draw — and where in the repo each part lives.
