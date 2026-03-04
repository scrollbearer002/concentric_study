# Concentric Triangles Hot Path: Three-Part Initialization Report

**Environment:** Clean-room study (extracted hot path)  
**Date:** 2026-02-21  
**Scope:** `cre/` folder as the universe for this task

---

## Part 1: Architectural Audit — Code → Visual Evidence Mapping

Map of the 12 steps in `study_concentric_logic.py` to the evidence report and screenshots.

### Truth Table: Code Lines → Visual Results

| Step | Code Location | Action Performed | Evidence Screenshot | Expected Visual State |
|------|---------------|------------------|---------------------|------------------------|
| **1** | Lines 188–189 | `execute_clear_canvas()` | `step_01.png` | Cmd+Backspace sent; dialog may appear |
| **2** | Lines 191–192 | `execute_keystroke(36)` (Enter) | `step_02.png` | Dialog confirmed; canvas cleared |
| **3** | Line 193 | `time.sleep(1.0)` | `step_03.png` | Pause; dialog closed, canvas empty |
| **4** | Lines 194–196 (commented) | Oracle: `assert_visual_state(…, "Is canvas empty?")` | `step_04.png` | Empty Excalidraw canvas |
| **5** | Line 197 | `time.sleep(0.5)` | `step_05.png` | Pause; canvas ready for drawing |
| **6** | Lines 200–202 | `get_screenshot_center()` → `execute_move_mouse(cx, cy)` | `step_06.png` | Cursor moved to center (1440, 900) |
| **7** | Line 203 | `time.sleep(0.5)` | `step_07.png` | Brief pause before pen |
| **8** | Lines 205–206 | `execute_keystroke("p")` | `step_08.png` | Pen tool selected |
| **9** | Lines 207–209 | `execute_keystroke("S")` | `step_09.png` | Stroke color picker open |
| **10** | Lines 211–212 (placeholder) | SoM + VLM + `execute_global_click` (black swatch) | `step_10.png` | Stroke set to black |
| **11** | Line 213 | `time.sleep(0.5)` | `step_11.png` | Pause before drawing |
| **12** | Lines 215–219 | `execute_draw_path_segments()` × 4 (sizes 220,160,100,50) | `step_12.png` | Four concentric black triangles |

### Evidence Folder

- **Path:** `cre/evidence_concentric_clean/`
- **Report:** `report.html` (generated 2026-02-21 09:31:31)
- **Screenshots:** `step_01.png` … `step_12.png` (referenced by report)

**Note:** In the clean-room extraction, the step screenshots may be absent. The pass log (`concentric_triangles_clean_pass_log.txt`) records center `(1440, 900)` and confirms the run completed successfully.

### Critical Code → Visual Links

| Code | Produces |
|------|----------|
| `execute_clear_canvas()` (lines 60–72) | Cmd+Backspace → Step 1 screenshot |
| `execute_keystroke(36)` (lines 75–87) | Enter → Step 2 screenshot |
| `get_screenshot_center()` (lines 18–25) | `(cx, cy) = (1440, 900)` for 2880×1800 |
| `execute_move_mouse(cx, cy)` (lines 104–110) | Cursor at screen center → Step 6 |
| `execute_keystroke("p")` | Pen selected → Step 8 |
| `execute_keystroke("S")` | Stroke picker → Step 9 |
| `execute_draw_path_segments(vertices, cx, cy)` (lines 114–146) | Four triangles → Step 12 |

---

## Part 2: Portability & Safety Check

### 2.1 Dependency Review (Post-Move)

`study_concentric_logic.py` depends on:

| Dependency | Purpose | Status in Clean Room |
|------------|---------|----------------------|
| **PIL (Pillow)** | `get_screenshot_center()` — read image dimensions | ❓ May need `pip install Pillow` |
| **pyobjc-framework-Quartz** | CGEvent keyboard/mouse posting | ❓ macOS-only; `pip install pyobjc-framework-Quartz` |
| **pyobjc-framework-Cocoa** | `NSScreen` for `backingScaleFactor()` | ❓ macOS-only; via `AppKit` |
| **google-genai** | `assert_visual_state()` — Gemini VLM oracle | ❓ `pip install google-genai` |
| **pydantic** | `VisualAssertionResult` schema for VLM | ❓ `pip install pydantic` |
| **json, os, time, pathlib** | stdlib | ✅ Built-in |

### Broken Dependencies

- **MacOSAgentCore** and **agent_core.py** are not in this folder. `study_concentric_logic.py` inlines the hot-path subset (Quartz events, `_pixel_to_global_quartz`). No import of `agent_core` in the study file.
- **current_state.png** is referenced at line 185 (`cre_dir / "current_state.png"`). The flow assumes this file exists from a prior `screencapture`. In a clean run, something must capture it first; the study flow does not.

### 2.2 Dry Run Mode Proposal for MacOSAgentCore

To observe the logic without taking over the mouse or posting Quartz events, introduce a `DRY_RUN` flag that short-circuits all system interaction:

```python
# Add at top of study_concentric_logic.py
DRY_RUN = os.environ.get("CONCENTRIC_DRY_RUN", "0").lower() in ("1", "true", "yes")

def _dry_run_guard(action: str, *args, **kwargs):
    """Log what would happen; do not post events."""
    if DRY_RUN:
        print(f"[DRY_RUN] {action} args={args} kwargs={kwargs}")
        return True
    return False

# Wrap each executor:
def execute_clear_canvas(app_focus: str = "Safari"):
    if _dry_run_guard("execute_clear_canvas", app_focus=app_focus):
        return
    # ... existing Quartz code ...

def execute_keystroke(key: int | str, app_focus: str = "Safari"):
    if _dry_run_guard("execute_keystroke", key=key, app_focus=app_focus):
        return
    # ...

def execute_move_mouse(px: int, py: int):
    gx, gy = _pixel_to_global_quartz(float(px), float(py))
    if _dry_run_guard("execute_move_mouse", px=px, py=py, gx=gx, gy=gy):
        return
    # ...

def execute_global_click(px: int, py: int):
    gx, gy = _pixel_to_global_quartz(float(px), float(py))
    if _dry_run_guard("execute_global_click", px=px, py=py, gx=gx, gy=gy):
        return
    # ...

def execute_draw_path_segments(...):
    if _dry_run_guard("execute_draw_path_segments", n_points=len(path_coordinates), center=(center_x, center_y)):
        return
    # ...
```

**Usage (macOS):**

```bash
CONCENTRIC_DRY_RUN=1 python cre/study_concentric_logic.py
```

- All `time.sleep()` calls remain; timing can still be observed.
- `_pixel_to_global_quartz()` still runs, so coordinate math is exercised.
- No `CGEventPost`; mouse and keyboard are untouched.

---

## Part 3: Mathematical Deep Dive — Coordinate Translation

### 3.1 Two Coordinate Systems

| System | Origin | Y Direction | Units |
|--------|--------|-------------|-------|
| **Image pixel** | Top-left (0,0) | Down = +Y | Pixels (1:1 with screenshot) |
| **Quartz global** | Bottom-left (0,0) | Up = +Y | Display pixels |

### 3.2 The Conversion Function

```python
def _pixel_to_global_quartz(px: float, py: float) -> tuple[float, float]:
    primary = NSScreen.mainScreen()
    scale = primary.backingScaleFactor() if primary else 2.0
    screen_height = primary.frame().size.height * scale if primary else 900 * scale
    gx = px
    gy = screen_height - py
    return (gx, gy)
```

### 3.3 Walkthrough: Center of 2880×1800 Screenshot → Quartz

**Input:** Pixel at center of a 2880×1800 screenshot.

1. **Screenshot center (image pixels):**
   - `px = 2880 / 2 = 1440`
   - `py = 1800 / 2 = 900`

2. **Screen frame (points):**
   - `NSScreen.mainScreen().frame()` returns the frame in Cocoa *points*.
   - For a 2880×1800 Retina display: frame ≈ 1440×900 points.

3. **Backing scale:**
   - `scale = primary.backingScaleFactor()` → typically `2.0` for Retina.

4. **Pixel height:**
   - `screen_height = frame.height * scale = 900 * 2 = 1800` (display pixels).

5. **X:**
   - `gx = px = 1440` — X is unchanged.

6. **Y flip:**
   - Image: top-left origin, Y increases downward.
   - Quartz: bottom-left origin, Y increases upward.
   - `gy = screen_height - py = 1800 - 900 = 900`.

7. **Output:**
   - `(gx, gy) = (1440, 900)` — Quartz global coordinates.

### 3.4 Why This Works

- `screencapture` on a full-screen Retina display yields 2880×1800 pixels, matching the display’s backing store.
- Image pixels map 1:1 to display pixels.
- `frame().height * backingScaleFactor()` gives the height in display pixels.
- `gy = screen_height - py` performs the Y flip for the bottom-left origin.

### 3.5 Triangle Vertices Example

For size 220, center (1440, 900):

```
triangle_vertices(220) → [(0, -220), (-220, 220), (220, 220)]
```

Each vertex `(vx, vy)` is converted to image pixel `(center_x + vx, center_y + vy)`:

| Vertex | Relative | Image pixel | Quartz (gx, gy) |
|--------|----------|-------------|-----------------|
| Top | (0, -220) | (1440, 680) | (1440, 1120) |
| Bottom-left | (-220, 220) | (1220, 1120) | (1220, 680) |
| Bottom-right | (220, 220) | (1660, 1120) | (1660, 680) |

`execute_draw_path_segments` uses these Quartz coordinates for `mouse_down`, `mouse_dragged`, and `mouse_up` events.

### 3.6 Edge Cases

- **primary is None:** Uses `scale = 2.0`, `screen_height = 1800`.
- **Multi-monitor:** Assumes primary screen; frame origin is not added. For non-primary displays, you’d add `frame().origin.x * scale` to `gx` and `frame().origin.y * scale` to `gy` (respecting Quartz’s coordinate system).

---

## Summary

| Part | Outcome |
|------|---------|
| **Architectural Audit** | 12 steps in `study_concentric_logic.py` mapped to evidence report and screenshots in `evidence_concentric_clean/`; pass log confirms center (1440, 900). |
| **Portability & Safety** | Dependencies: Pillow, pyobjc (Quartz/Cocoa), google-genai, pydantic. Dry Run via `CONCENTRIC_DRY_RUN=1` to observe logic without Quartz posting. |
| **Mathematical Deep Dive** | `_pixel_to_global_quartz`: gx=px, gy=screen_height−py; for 2880×1800 center → (1440, 900) in both spaces; Y flip handles origin difference. |
