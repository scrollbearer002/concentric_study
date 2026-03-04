# Last 3 Kleki Runs Line-by-Line Audit (PhD)

Audited runs: `2b70a9a006b0`, `f40e7d9ed9ab`, `9d28b35cf1b0`.

## Run Summaries

- `2b70a9a006b0`: outcome=`failure`, failure_step=`None`, claims_score=`0.46153846153846156`
- `f40e7d9ed9ab`: outcome=`failure`, failure_step=`2`, claims_score=`0.4117647058823529`
- `9d28b35cf1b0`: outcome=`failure`, failure_step=`3`, claims_score=`0.4117647058823529`

## Required Conclusions

- `9d28b35cf1b0` exposed the old color-setting contract defect and is now a historical regression case.
- `f40e7d9ed9ab` exposed a real recovery-policy bug: diagnosis succeeded but corrective action was `none` twice.
- `2b70a9a006b0` is the primary open-defect run because it crossed setup and failed on output quality at final verification.

## Open Quality Backlog from `2b70a9a006b0`

- composition coverage too small
- insufficient detail density
- weak subject recognizability
- poor facade structure
- broken one-point perspective
- linework reads as scribble/noise
- scatter noise contaminates shading

## Step Matrix

See `operator/cre/artifacts/last_3_kleki_step_matrix.csv` for the full row-level matrix.

### `2b70a9a006b0`

| Step | Action | Root Cause | Status | Required Fix |
|---|---|---|---|---|
| 0 | `a11y_passive_snapshot` | `historical_only` | `historical_resolved` | None beyond preserving current behavior. |
| 1 | `click` | `historical_only` | `historical_resolved` | None beyond preserving current behavior. |
| 2 | `kleki_clear_canvas` | `historical_only` | `historical_resolved` | None beyond preserving current behavior. |
| 3 | `kleki_set_color` | `historical_only` | `historical_resolved` | None beyond preserving current behavior. |
| 4 | `kleki_set_brush_size` | `historical_only` | `historical_resolved` | None beyond preserving current behavior. |
| 5 | `draw_path` | `geometry_primitive` | `still_open` | Expose a first-class draw_segments structural action and route silhouette, mullions, roof edges, and final outline through it. |
| 6 | `draw_path` | `geometry_primitive` | `still_open` | Expose a first-class draw_segments structural action and route silhouette, mullions, roof edges, and final outline through it. |
| 7 | `draw_path` | `geometry_primitive` | `still_open` | Expose a first-class draw_segments structural action and route silhouette, mullions, roof edges, and final outline through it. |
| 8 | `draw_path` | `geometry_primitive` | `still_open` | Expose a first-class draw_segments structural action and route silhouette, mullions, roof edges, and final outline through it. |
| 10 | `draw_path` | `plan_synthesis` | `still_open` | Enforce one-point scaffold rules in planning and normalization: front horizontals horizontal, verticals vertical, depth lines coherent. |
| 11 | `draw_path` | `plan_synthesis` | `still_open` | Enforce one-point scaffold rules in planning and normalization: front horizontals horizontal, verticals vertical, depth lines coherent. |
| 12 | `kleki_set_brush_size` | `historical_only` | `historical_resolved` | None beyond preserving current behavior. |
| 13 | `draw_path` | `geometry_primitive` | `still_open` | Expose a first-class draw_segments structural action and route silhouette, mullions, roof edges, and final outline through it. |
| 14 | `draw_path` | `geometry_primitive` | `still_open` | Expose a first-class draw_segments structural action and route silhouette, mullions, roof edges, and final outline through it. |
| 15 | `draw_path` | `geometry_primitive` | `still_open` | Expose a first-class draw_segments structural action and route silhouette, mullions, roof edges, and final outline through it. |
| 16 | `draw_path` | `geometry_primitive` | `still_open` | Expose a first-class draw_segments structural action and route silhouette, mullions, roof edges, and final outline through it. |
| 17 | `draw_path` | `geometry_primitive` | `still_open` | Expose a first-class draw_segments structural action and route silhouette, mullions, roof edges, and final outline through it. |
| 18 | `draw_path` | `geometry_primitive` | `still_open` | Expose a first-class draw_segments structural action and route silhouette, mullions, roof edges, and final outline through it. |
| 19 | `draw_path` | `plan_synthesis` | `still_open` | Enforce one-point scaffold rules in planning and normalization: front horizontals horizontal, verticals vertical, depth lines coherent. |
| 20 | `draw_path` | `plan_synthesis` | `still_open` | Enforce one-point scaffold rules in planning and normalization: front horizontals horizontal, verticals vertical, depth lines coherent. |
| 21 | `draw_path` | `plan_synthesis` | `still_open` | Enforce one-point scaffold rules in planning and normalization: front horizontals horizontal, verticals vertical, depth lines coherent. |
| 22 | `draw_path` | `plan_synthesis` | `still_open` | Enforce one-point scaffold rules in planning and normalization: front horizontals horizontal, verticals vertical, depth lines coherent. |
| 23 | `draw_path` | `plan_synthesis` | `still_open` | Enforce one-point scaffold rules in planning and normalization: front horizontals horizontal, verticals vertical, depth lines coherent. |
| 25 | `kleki_set_color` | `render_state` | `still_open` | Add explicit Kleki render-state normalization: tool, scatter, stabilizer, opacity, and brush-size actions with contracts. |
| 26 | `kleki_set_brush_size` | `render_state` | `still_open` | Add explicit Kleki render-state normalization: tool, scatter, stabilizer, opacity, and brush-size actions with contracts. |
| 27 | `kleki_set_opacity` | `render_state` | `still_open` | Add explicit Kleki render-state normalization: tool, scatter, stabilizer, opacity, and brush-size actions with contracts. |
| 28 | `draw_path` | `open_quality_gap` | `still_open` | Use broader, controlled tonal band segmentation and mid-run art assertions for shading quality and composition coverage. |
| 29 | `draw_path` | `open_quality_gap` | `still_open` | Use broader, controlled tonal band segmentation and mid-run art assertions for shading quality and composition coverage. |
| 30 | `kleki_set_color` | `render_state` | `still_open` | Add explicit Kleki render-state normalization: tool, scatter, stabilizer, opacity, and brush-size actions with contracts. |
| 31 | `draw_path` | `open_quality_gap` | `still_open` | Use broader, controlled tonal band segmentation and mid-run art assertions for shading quality and composition coverage. |
| 32 | `draw_path` | `open_quality_gap` | `still_open` | Use broader, controlled tonal band segmentation and mid-run art assertions for shading quality and composition coverage. |
| 33 | `kleki_set_color` | `render_state` | `still_open` | Add explicit Kleki render-state normalization: tool, scatter, stabilizer, opacity, and brush-size actions with contracts. |
| 34 | `kleki_set_brush_size` | `render_state` | `still_open` | Add explicit Kleki render-state normalization: tool, scatter, stabilizer, opacity, and brush-size actions with contracts. |
| 35 | `kleki_set_opacity` | `render_state` | `still_open` | Add explicit Kleki render-state normalization: tool, scatter, stabilizer, opacity, and brush-size actions with contracts. |
| 36 | `draw_path` | `open_quality_gap` | `still_open` | Use broader, controlled tonal band segmentation and mid-run art assertions for shading quality and composition coverage. |
| 38 | `kleki_set_color` | `render_state` | `still_open` | Add explicit Kleki render-state normalization: tool, scatter, stabilizer, opacity, and brush-size actions with contracts. |
| 39 | `kleki_set_brush_size` | `render_state` | `still_open` | Add explicit Kleki render-state normalization: tool, scatter, stabilizer, opacity, and brush-size actions with contracts. |
| 40 | `kleki_set_opacity` | `render_state` | `still_open` | Add explicit Kleki render-state normalization: tool, scatter, stabilizer, opacity, and brush-size actions with contracts. |
| 41 | `draw_path` | `geometry_primitive` | `still_open` | Expose a first-class draw_segments structural action and route silhouette, mullions, roof edges, and final outline through it. |
| 997 | `final_verification_gate` | `verification_granularity` | `still_open` | Add mandatory mid-run art visual assertions after scaffold, facade, shading, and final outline completion. |
| 996 | `visual_monitor_summary` | `benchmark_claim_design` | `still_open` | Add claims for composition coverage, recognizability, perspective coherence, facade legibility, detail density, and render-state normalization. |
| 998 | `metacognitive_audit` | `historical_only` | `historical_resolved` | None beyond preserving current behavior. |

### `f40e7d9ed9ab`

| Step | Action | Root Cause | Status | Required Fix |
|---|---|---|---|---|
| 0 | `a11y_passive_snapshot` | `historical_only` | `historical_resolved` | None beyond preserving current behavior. |
| 1 | `click` | `historical_only` | `historical_resolved` | None beyond preserving current behavior. |
| 2 | `kleki_clear_canvas` | `recovery_policy` | `historical_resolved` | Preserve explicit clear-canvas contract repair and forbid none when diagnosis says canvas still contains marks. |
| 996 | `visual_monitor_summary` | `historical_only` | `historical_resolved` | None beyond preserving current behavior. |
| 998 | `metacognitive_audit` | `historical_only` | `historical_resolved` | None beyond preserving current behavior. |

### `9d28b35cf1b0`

| Step | Action | Root Cause | Status | Required Fix |
|---|---|---|---|---|
| 0 | `a11y_passive_snapshot` | `historical_only` | `historical_resolved` | None beyond preserving current behavior. |
| 1 | `click` | `historical_only` | `historical_resolved` | None beyond preserving current behavior. |
| 2 | `kleki_clear_canvas` | `historical_only` | `historical_resolved` | None beyond preserving current behavior. |
| 3 | `kleki_set_color` | `color_grounding` | `historical_resolved` | Preserve the grayscale-anchor selection path and the color-effect contract; do not regress to generic panel clicks. |
| 998 | `metacognitive_audit` | `historical_only` | `historical_resolved` | None beyond preserving current behavior. |

## Research Basis

- [Kleki Help](https://kleki.com/help/): Documents Delete/Backspace clear-layer behavior, Shift drawing, shape tool shortcut, and browser recovery behavior.
- [OSWorld](https://arxiv.org/abs/2404.07972): Primary benchmark showing GUI-agent failures cluster around grounding and operational control.
- [UI-Hawk](https://aclanthology.org/2025.emnlp-main.920/): Supports temporal GUI evidence and screen-history-aware diagnostics.
- [ShowUI](https://arxiv.org/abs/2411.17465): Supports tighter visual-action coupling for GUI tasks.
- [ShowUI-pi](https://showlab.github.io/showui-pi): Supports continuous GUI dexterity primitives for line- and stroke-like operations.
- [MCP-Atlas](https://arxiv.org/abs/2602.00933): Justifies claims-based partial-credit evaluation, but only when claims match task semantics.
- [CRAFT](https://arxiv.org/abs/2512.20362): Supports decomposed multimodal verification instead of holistic pass/fail.
- [University of Missouri One-Point Perspective](https://arch.missouri.edu/architectural-studies-studio-student-work/drafting/project-one-point-perspective/): Line quality, scale, and perspective accuracy are first-class acceptance criteria in architectural drawing.
- [Julianna Kunstler One-Point Perspective](https://juliannakunstler.com/1pt-perspective): Codifies the relevant construction rules: verticals vertical, front horizontals horizontal, depth lines to one vanishing point.
