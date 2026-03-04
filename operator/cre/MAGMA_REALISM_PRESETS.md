# Magma — PhD-style realism presets & measurement protocol

**Purpose:** Single reference for exact sizes, zoom workflow, and minor details needed to produce PhD-level realistic art on Magma. Fill in measured values after one exploration run.

---

## 1. Zoom on canvas (how)

- **Zoom In:** Click **Zoom In** (magnifier +) in the **top toolbar**. Repeat to step in further.
- **Zoom Out:** Click **Zoom Out** (magnifier −) in the **top toolbar**.
- **Readout:** Bottom-left shows current zoom (e.g. **Q 13%**). 100% = 1:1; higher = zoomed in.
- **Pan after zoom:** Select **Hand** (left toolbar), drag on canvas to reposition; then select **Brush** again to draw.
- **Shortcuts (if available):** Try `+` / `-` or scroll with modifier; document here if they work: ___________

---

## 2. Canvas size (fill after measurement)

| Preset            | Width (px) | Height (px) | Notes |
|-------------------|------------|-------------|--------|
| Landscape drawing | _________  | _________   | Default landscape. |
| High-res          | _________  | _________   | If different from Landscape. |
| Vertical          | _________  | _________   | Portrait. |

**How to measure:** On canvas page, use browser dev tools (inspect canvas element or full viewport) or SoM overlay + known reference; or read from Magma UI if displayed.

---

## 3. Brush settings for PhD realism (fill after measurement)

| Use case       | Size (px or slider value) | Opacity (%) | Hardness (if any) | Notes |
|----------------|----------------------------|-------------|-------------------|--------|
| Outline / line | _________                  | 100         | _________         | Crisp edges. |
| Soft shadow    | _________                  | 30–50       | _________         | Larger, softer. |
| Fill / block   | _________                  | 80–100      | _________         | Solid areas. |

**How to measure:** Open Brush Settings (right panel), note min/max and step for size and opacity; record values that look correct for outline vs shadow on a test stroke.

---

## 4. Colors (hex or HSV)

| Role           | Hex or value | Notes |
|----------------|--------------|--------|
| Outline black  | #1a1a1a or ___ | Slightly soft black. |
| Shadow gray    | #4a4a4a or ___ | Mid gray for shading. |
| Body highlight | #e0e0e0 or ___ | Optional. |

---

## 5. UI element coordinates (for automation)

**Resolution used:** _________ (e.g. 2880×1800 Retina).  
**Coordinate system:** Pixel, origin top-left, y down.

| Element        | x    | y    | Notes |
|----------------|------|------|--------|
| Brush (left)   | ____ | ____ | Paintbrush icon. |
| Color Palette  | ____ | ____ | Right panel, swatch. |
| Brush Settings | ____ | ____ | Right panel, 3 lines. |
| Zoom In        | ____ | ____ | Top toolbar. |
| Zoom Out       | ____ | ____ | Top toolbar. |
| Add Layer (+)  | ____ | ____ | Bottom left. |
| Canvas center  | ____ | ____ | For draw_path origin. |

**How to measure:** Run SoM overlay on a Magma canvas screenshot; use VLM or button-mapping to get pixel coords; or click and log with a small script that reports cursor position.

---

## 6. PhD-style workflow (checklist)

1. [ ] Navigate to `magma.com/app` → My artworks.
2. [ ] New canvas → **Landscape drawing** (or High-res if measured).
3. [ ] Click **Zoom In** until readout is suitable (e.g. 50–100% for detail).
4. [ ] Optional: **Hand** → drag to center subject area.
5. [ ] Click **Brush** (left toolbar).
6. [ ] Set **Color** (Color Palette) — e.g. outline black.
7. [ ] Open **Brush Settings** — set size for outline, opacity 100%.
8. [ ] Draw outline (e.g. car body, wheels) with `draw_path`.
9. [ ] Optional: **Add Layer** (+), set gray, lower opacity, Brush Settings larger — shade.
10. [ ] Optional: **Zoom Out** to see full composition; **Save**.

---

## 7. Measurement protocol (one-time)

**Run once and fill this doc:**

1. Open Magma canvas (Landscape drawing). Screenshot full window.
2. Inspect or measure canvas element → Section 2 (canvas size).
3. Open Brush Settings; note slider ranges and a good outline/shadow pair → Section 3.
4. Set a black and a gray in Color Palette; note hex if visible → Section 4.
5. Run SoM + button mapping (or manual click-log) on same screenshot → Section 5.
6. Test zoom: click Zoom In 3×, note readout; click Hand, drag; click Brush → confirm zoom + pan + draw. Document any shortcut (+, −, scroll) → Section 1.

After that, this file is the exhaustive minor-detail spec for PhD realism art on Magma.
