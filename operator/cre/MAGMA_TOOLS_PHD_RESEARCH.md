# Magma.com — PhD-Level Tool & Interface Research

**Source:** High-resolution screenshot of Magma drawing application (Safari, macOS).  
**Purpose:** Exhaustive catalog of every UI tool and control so the agent can use the **actual** Magma interface instead of bypassing it (e.g. raw Quartz strokes with no tool selection).  
**Key insight:** "Look how easy it can be" — the UI exposes Brush, Brush Settings, Color, and Layers; using them is the path to realistic drawing.

---

## 1. Interface Topology

- **Top:** Safari chrome (tabs, address bar). Tab title e.g. "New Drawing | Magma" when on canvas.
- **Below chrome:** Magma **top horizontal toolbar** (file/doc, zoom, undo/redo, share).
- **Left edge:** Magma **left vertical toolbar** — main **drawing tools** (Move, Selection, Lasso, Magic Wand, **Brush**, Pencil, Eraser, Fill, Eyedropper, Hand, Undo/Redo, more).
- **Right edge:** Magma **right vertical toolbar** — **Color**, **Brush Settings**, **Layers**, Reference, Settings.
- **Center:** White **canvas** (drawing surface). Small crosshair/cursor near center when ready to draw.
- **Bottom left:** Zoom (e.g. "Q 13%"), stroke/level info ("0/150 lvl 1"), **layer thumbnail** ("New Drawing"), **+ (add layer)**.

---

## 2. Left Vertical Toolbar — Drawing Tools (by order, top → bottom)

| # | Icon / name       | Tool name (agent ID) | Interaction mode | Description | Agent action / notes |
|---|-------------------|----------------------|------------------|-------------|----------------------|
| 1 | Crosshair         | **Move**             | click_drag / path_trace | Move selections or canvas. | click to select; drag to move. Use when you need to reposition content. |
| 2 | Dotted rectangle  | **Selection**        | bounding_box     | Rectangular selection. Drag to define box. | click + drag on canvas. |
| 3 | Lasso shape       | **Lasso**           | path_trace       | Freehand selection. | draw a closed path to select. |
| 4 | Magic wand        | **Magic Wand**      | click_place      | Select areas of similar color. | click on canvas; tolerance may be in panel. |
| 5 | **Paintbrush**    | **Brush**           | **path_trace**   | **Primary drawing tool.** Renders strokes with current color and brush settings. | **Select first for realistic drawing.** Then set color (right panel), then Brush Settings (size, opacity, hardness). |
| 6 | Pencil            | **Pencil**         | path_trace       | Pencil/pen — often harder edge, thinner. | Alternative to Brush for linework. |
| 7 | Eraser            | **Eraser**         | path_trace       | Makes pixels transparent. Like a brush that erases. | Use to correct or soften edges. |
| 8 | Paint bucket      | **Paint Bucket**    | click_place      | Fills contiguous area of similar color with current color. | Click inside closed region. Set color first. |
| 9 | Eyedropper        | **Eyedropper**     | click_place      | Picks color from canvas → sets as current color. | Click on canvas pixel. |
|10 | Hand              | **Hand**            | click_drag       | Pan canvas without drawing. | Hold and drag to move view. |
|11 | Curved arrow ←    | **Undo**           | click_place      | Revert last action. | Click or use shortcut. |
|12 | Curved arrow →    | **Redo**           | click_place      | Re-apply last undone action. | Click or use shortcut. |
|13 | Three dots        | **More tools**      | toggle / select  | May reveal additional tools or options. | Click to expand. |

**Critical for realistic car drawing:** **Brush** (or Pencil) must be **active** before drawing. Then **Brush Settings** (right panel) control size, opacity, hardness — essential for soft shadows and crisp outlines.

---

## 3. Top Horizontal Toolbar

| Section   | Element          | Agent ID / label   | Interaction | Description |
|-----------|------------------|--------------------|-------------|-------------|
| Left      | Sheet + plus     | **New Document**   | click_place | New document/canvas. May open dialog (size, orientation). |
|           | Folder           | **Open/Folder**    | click_place | Open or import. |
|           | Floppy disk      | **Save**           | click_place | Save current work. |
|           | Eraser icon      | **Eraser (top)**   | click_place | Same as left-toolbar Eraser. |
|           | Magnifier +      | **Zoom In**        | click_place | Zoom in. |
|           | Magnifier −      | **Zoom Out**       | click_place | Zoom out. |
|           | ?                | **Help**           | click_place | Help / tutorials. |
|           | Wrench           | **Settings**       | click_place | App preferences. |
| Middle    | Curved arrow ←   | **Undo**           | click_place | Undo. |
|           | Curved arrow →   | **Redo**           | click_place | Redo. |
| Right     | Share            | **Share**          | click_place | Share/collaboration. |
|           | "1" person       | **Collaborators**  | click_place | Collaborator count / invite. |
|           | Purple octopus   | (brand/extension)  | —           | Likely Magma brand or extension. |
|           | Star             | **Favorite / star**| click_place | May favorite or highlight. |

---

## 4. Right Vertical Toolbar — Color, Brush, Layers

| # | Icon / description      | Agent ID           | Interaction | Description | Relevance for realistic drawing |
|---|-------------------------|--------------------|-------------|-------------|----------------------------------|
| 1 | Color swatch + brush    | **Color Palette**  | select      | Choose current drawing color (saturation/value + hue). | **Essential.** Set dark gray/black for outlines, mid-tones for shading. |
| 2 | Three lines / sliders   | **Brush Settings** | select      | **Brush size, opacity, hardness,** etc. | **Critical.** Thin size for lines; larger + lower opacity for soft shadows. |
| 3 | Stacked squares        | **Layers**         | select      | Layer list; add/delete/visibility/order. | **Essential for complex art.** Outline on one layer, shading on another. |
| 4 | Book / stacked papers  | **Reference/View** | click_place | Reference images or view options. | Can load a reference photo (e.g. BMW E30) for tracing or visual guide. |
| 5 | Gear                   | **Settings**       | click_place | Application settings. | General prefs. |

**Operation rules:**

- **Color before drawing:** Select color from Color Palette, then draw with Brush/Pencil.
- **Brush Settings before drawing:** Open Brush Settings; set size (e.g. small for outlines, larger for fill); set opacity (e.g. 100% for lines, 30–50% for shading); then draw.
- **Layers:** Use at least one layer for linework and optionally a second for shading so corrections don’t destroy outline.

---

## 5. Bottom Panel

| Element        | Description |
|----------------|-------------|
| **Zoom**       | e.g. "Q 13%" — current zoom level. |
| **0/150 lvl 1** | Likely stroke count or history index (e.g. 0 of 150 undo steps), level/layer. |
| **Layer thumbnail** | "New Drawing" — current layer preview. |
| **+**          | **Add layer** — creates a new layer. |

---

## 5b. Zoom on canvas (exhaustive)

**How to zoom in / out on the canvas:**

1. **Toolbar (always works):** Click **Zoom In** (magnifier with +) or **Zoom Out** (magnifier with −) in the **top horizontal toolbar**. Each click steps zoom in or out. Center of zoom is typically the canvas center or the last cursor position depending on app behavior.
2. **Readout:** Current zoom level is shown in the **bottom-left** of the Magma UI (e.g. **"Q 13%"**). Use this to know current zoom (e.g. 13% = zoomed out; 100% = 1:1; higher = zoomed in).
3. **Shortcuts (common in drawing apps):** Many apps use **+ / −** (with or without Cmd) or **scroll wheel** (with Alt/Option or with Hand active) to zoom. If Magma supports them, use for faster workflow; otherwise rely on toolbar clicks.
4. **Pan after zoom:** After zooming in, use **Hand** tool (left toolbar) to click-drag and pan so the area you want to draw is visible. Sequence: Zoom In (multiple clicks if needed) → Hand → drag canvas → select Brush again → draw.

**Agent workflow for “zoom in on canvas then draw”:**  
Click **Zoom In** (top toolbar) one or more times; optionally click **Hand** and drag to reposition; click **Brush** again; then draw. Current zoom is visible in bottom-left (e.g. "Q 50%").

---

## 6. Agent Action Mapping (summary)

For **realistic 1991 BMW M3 E30** on Magma:

1. **Navigate:** `go_to_url` → `https://magma.com/app` (redirects to My artworks).
2. **Open canvas:** Click "New canvas" (or use JS from MAGMA_LAST_RUN_RESEARCH.md), then click "Landscape drawing".
3. **Select Brush:** Click **Brush** tool in left toolbar (paintbrush icon).
4. **Set color:** Click **Color Palette** on right; choose black or dark gray (e.g. click in saturation box + hue slider).
5. **Brush Settings:** Click **Brush Settings** (three lines/sliders); set **size** (small for outlines); set **opacity** (e.g. 100% for lines).
6. **Draw outline:** Use `draw_path` with vertices for car body side profile (hood, roof, trunk, sill, wheel arches). Or multiple `draw_path` steps for front fender, door, rear fender, windows.
7. **Wheels:** Same brush; two circles or ellipses (front and rear wheel).
8. **Details:** Door line, window frames, headlight/taillight; optionally lower opacity + larger brush for shadows under car or in wheel wells.
9. **Optional:** Add layer via **+**, set color to mid-gray, reduce opacity, shade one side of car.

**What was missing before:** The agent drove Quartz strokes without ever **clicking Brush**, **Color**, or **Brush Settings**. So the app may have been in Move or Selection mode, default color, default brush — producing a single crude stroke instead of a composed drawing.

---

## 7. Interaction Modes (for SiteKnowledge / VLM)

| Mode          | Meaning | Example tools |
|---------------|---------|----------------|
| path_trace    | User draws by dragging through points; stroke follows path. | Brush, Pencil, Eraser, Lasso. |
| bounding_box  | User drags to define a rectangle (selection or shape). | Selection. |
| click_place   | Single click to place or activate (e.g. fill, eyedropper, button). | Magic Wand, Paint Bucket, Eyedropper, all toolbar buttons. |
| toggle        | Click toggles state on/off. | More tools (…), possibly layer visibility. |
| select        | Click selects from options (e.g. color, layer, preset). | Color Palette, Brush Settings, Layers. |
| click_drag    | Click and drag for pan/move. | Move, Hand. |

---

## 8. References

- **MAGMA_LAST_RUN_RESEARCH.md:** Proven path to canvas: `magma.com/app` → My artworks → JS "New canvas" → JS "Landscape drawing" → canvas at `magma.com/d/<id>`.
- **Screenshot:** `Screenshot_2026-02-27_at_12.04.39_AM-...png` — full Magma UI on high-resolution "paper" (canvas).
- **site_knowledge_magma.json:** Machine-readable tool affordances, rules, and shortcuts for planner injection.

This document is the single source of truth for "what all these tools are" and how the agent should use them to produce a realistic car drawing on Magma.
