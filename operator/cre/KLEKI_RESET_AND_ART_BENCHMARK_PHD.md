# Kleki Reset And Art Benchmark PhD Memo

Date: February 28, 2026

## What changed

1. Window-scoped capture was already switched in the prior pass so verification and recovery observe the Safari/Kleki window rather than the full desktop.
2. `kleki_clear_canvas` now follows Kleki's documented clear-layer contract (`Delete` / `Backspace`) instead of using Excalidraw-style selection semantics.
3. Kleki clear-canvas recovery now has an explicit action contract repair path when diagnosis says the canvas still contains marks.
4. Benchmark evaluation now adds art-task-specific claims derived from the repo's own `final_verification_gate` constraints.
5. Planner-emitted `visual_assert` steps now have an executor handler, removing a planner/executor interface gap for future runs.

## Primary evidence

### Live run

- Run: `operator/cre/runs/2b70a9a006b0`
- Manifest: `operator/cre/runs/2b70a9a006b0/manifest.json`
- Benchmark: `operator/cre/runs/2b70a9a006b0/benchmark_result.json`
- Final screenshot: `operator/cre/runs/2b70a9a006b0/verification/verify_01.png`

### Result

- `kleki_clear_canvas` succeeded and was visually verified.
- The run progressed through 42 traced steps and reached final verification.
- Outcome remained `failure`, but it failed for quality reasons, not startup/reset reasons.

This is a significant shift in the failure frontier:
- before: mixed-desktop verification contamination, stale canvas state, early-site setup failure
- now: the system can execute the intended action family end-to-end, but the produced drawing still fails the requested architectural quality bar

## What the final screenshot shows

The output has:
- some grayscale tonal variation
- some repeated line structure
- non-empty canvas with sustained execution evidence

But it still fails on:
- recognizable skyscraper identity
- coherent one-point perspective
- facade subdivision quality
- exhaustive architectural detail
- clean line discipline

A concrete newly exposed defect is visible in the final screenshot:
- `Scatter` is non-zero, so shading and highlight passes become dotted noise instead of controlled tonal massing

## Research basis

### Official product / platform basis

- Kleki help documents `Delete` / `Backspace` for clearing a layer and describes browser-storage recovery behavior.
  - https://kleki.com/help/
- macOS `screencapture(1)` supports window-scoped capture via `-l <windowid>`.

### GUI-agent methodology basis

- SeeAct: semantic plans need grounded environment-specific execution.
  - https://arxiv.org/abs/2401.01614
- OSWorld: GUI agents mostly fail on grounding and operational knowledge, not only planning.
  - https://arxiv.org/abs/2404.07972
- UI-Hawk: correct temporal/visual observation stream matters for GUI understanding.
  - https://aclanthology.org/2025.emnlp-main.920/
- MCP-Atlas: claims-based evaluation is stronger than binary pass/fail, but claims must match task family.
  - https://arxiv.org/abs/2602.00933
- CRAFT and VisionDirector support decomposed visual verification rather than holistic success guesses.
  - https://arxiv.org/abs/2512.20362
  - https://arxiv.org/abs/2512.19243

## PhD-level conclusion

The latest repo state is methodologically better than the earlier one in two important ways:

1. The runtime now fails on the true task-quality problem instead of a contaminated observation pipeline.
2. The benchmark now reports partial progress for art tasks (`claims_score = 0.4615` on `2b70a9a006b0`) instead of collapsing all failed art runs into the same generic score.

The next highest-value technical issue exposed by the evidence is brush-state normalization, especially scatter, followed by geometric plan quality.
