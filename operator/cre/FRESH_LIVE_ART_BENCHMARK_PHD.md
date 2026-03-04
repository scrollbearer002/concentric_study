# PhD Live Benchmark Report: Kleki Skyscraper

**Date:** February 28, 2026  
**Benchmark task:** `https://kleki.com`  
**Goal:** Draw a tall modern skyscraper in one-point perspective with exhaustive facade detail and profuse grayscale shading.

## 1. Primary run

- New live run: `operator/cre/runs/cd0862f1e3c4`
- Baseline failures:
  - `operator/cre/runs/0b64930f0c59`
  - `operator/cre/runs/9d28b35cf1b0`

Primary artifacts for the new run:

- `operator/cre/runs/cd0862f1e3c4/manifest.json`
- `operator/cre/runs/cd0862f1e3c4/trace.jsonl`
- `operator/cre/runs/cd0862f1e3c4/benchmark_result.json`
- `operator/cre/runs/cd0862f1e3c4/visual_monitor/status.json`
- `operator/cre/runs/cd0862f1e3c4/visual_monitor/timeline.json`
- `operator/cre/runs/cd0862f1e3c4/visual_monitor/checkpoints.json`
- `operator/cre/runs/cd0862f1e3c4/research_brief.json`

## 2. Outcome

The run failed, but it was materially stronger than the earlier Kleki art failures.

### Final outcome

- outcome: `failure`
- failure step: `15`
- duration: `404211 ms`
- steps recorded: `17`

Evidence:

- `operator/cre/runs/cd0862f1e3c4/manifest.json`

## 3. Comparison to the previous two art failures

| Run | Failure boundary | Steps recorded | Duration | Main defect |
|---|---:|---:|---:|---|
| `0b64930f0c59` | `7` | `9` | `152253 ms` | wrong site-specific verification and failed first visible draw |
| `9d28b35cf1b0` | `3` | `5` | `156960 ms` | failed `kleki_set_color` |
| `cd0862f1e3c4` | `15` | `17` | `404211 ms` | verifier saw Cursor/dark editor instead of Kleki during sustained drawing |

### Direct progress

The new run successfully crossed all of these earlier failure boundaries:

1. `kleki_clear_canvas`
2. `kleki_set_color`
3. `kleki_set_brush_size`
4. multiple verified `draw_path` steps for the skyscraper structure

That is real progress. The system moved from startup/color failure into sustained geometry execution.

## 4. What the new benchmark artifacts revealed

### 4.1 Benchmark result

`operator/cre/runs/cd0862f1e3c4/benchmark_result.json` reports:

- claims score: `0.4118`
- discovery precision: `0.9412`
- recovery rate: `1.0`
- plan optimality: `1.0`
- redundant actions: `10`

### 4.2 Monitor status

`operator/cre/runs/cd0862f1e3c4/visual_monitor/status.json` reports:

- total captures: `87`
- buffer size: `40`
- interval: `5.0s`

### 4.3 Recovery checkpoints

`operator/cre/runs/cd0862f1e3c4/visual_monitor/checkpoints.json` contains `9` labeled checkpoints.

Most important checkpoint findings:

- step `1`: recovery diagnosed a tiny residual black dot after clear-canvas verification
- step `15`: recovery twice diagnosed that the visible screen was a dark code editor / Cursor-like interface rather than the Kleki canvas

This is the strongest new evidence from the benchmark. Previous runs did not have this event-labeled temporal record.

## 5. Most important technical findings

### 5.1 The system is clearly stronger than before

The new run executed far more of the intended task:

- earlier failures stopped at initialization or color setup
- this run completed structural building strokes through the early facade phase

### 5.2 Recovery checkpoints exposed a new class of failure

The decisive failure was not color grounding.

It was **screen-routing / observation drift**:

- the verifier saw a dark code-editor interface
- focus enforcement still reported Safari as frontmost
- recovery_action remained `none`

That means the failure is now a higher-level runtime-state inconsistency, not the earlier low-level Kleki color-state inconsistency.

### 5.3 The current benchmark claims are too coarse

Backfilled with the same generic claim set, all three runs score the same `0.412` claims score:

- `0b64930f0c59`: `0.412`
- `9d28b35cf1b0`: `0.412`
- `cd0862f1e3c4`: `0.412`

Yet the new run is obviously stronger.

This is evidence that generic claims are insufficient for art tasks.

## 6. Research interpretation

### 6.1 Why the checkpoints mattered

Recent GUI-agent work argues that temporal context matters:

- `UI-Hawk` shows that screen-stream understanding is necessary because current-frame-only observation misses critical temporal information.
  - Source: https://aclanthology.org/2025.emnlp-main.920/
- `History-Aware Reasoning for GUI Agents` argues that long-horizon GUI tasks require explicit short-term historical context.
  - Source: https://arxiv.org/abs/2511.09127
- `GUI-KV` shows that long trajectories need selective retention of salient frames rather than uniform observation.
  - Source: https://arxiv.org/abs/2510.00536

**Inference from those sources:** the new labeled checkpoints are methodologically correct because they preserve salient recovery frames, not just periodic background images.

### 6.2 Why this benchmark is still valid despite failure

Modern agent evaluation work emphasizes:

- repeated, comparable task runs
- partial-credit diagnostics
- failure analysis from traces, not anecdote

Relevant sources:

- MCP-Atlas: claims-based scoring and diagnostic dimensions  
  https://arxiv.org/abs/2602.00933
- AutoGenBench: repeated evaluation because agent results are noisy  
  https://microsoft.github.io/autogen/0.2/blog/2024/01/25/AutoGenBench/
- SeeAct: live web agents succeed or fail at the grounding layer, not only the planning layer  
  https://arxiv.org/abs/2401.01614
- AppAgent: pre-execution research/exploration improves downstream execution on unfamiliar tools  
  https://arxiv.org/abs/2312.13771

## 7. Bottom line

The fresh live art benchmark did **not** succeed.

But it did show two important advances:

1. The agent now gets materially farther into the art task than the older Kleki failures.
2. The new runtime evidence layer makes the current failure mode much clearer.

The blocking problem has shifted from:

- color setup and early-site mismatch

to:

- sustained execution where visual verification can drift away from the intended Safari/Kleki surface while focus checks still claim Safari is frontmost

That is a more advanced, narrower, and more actionable failure.

## 8. Next steps

1. Add task-family-specific benchmark claims for art so the score reflects real visual-task progress.
2. Investigate why the verifier can observe Cursor/editor imagery while focus enforcement reports Safari.
3. Promote “wrong application / wrong visible surface” from `recovery_action: none` to a deterministic repair path.
