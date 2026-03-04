# Section 5: Dynamic Execution Architecture

## 1. Purpose

Sections 1 through 4 established the static architecture, traceability, and
live conformance gate.

This section answers the next stronger question from
`operator/cre/project_understanding/PHD_PATH_REVALIDATION.md`:

**What runtime architecture is actually visible in the observed run corpus, and
where does that behavior differ from what static imports alone would suggest?**

## 2. Research Basis

- SEI's "Discovering Architectures from Running Systems" supports recovering an execution view from observed runtime behavior rather than only from source structure.
- Hofmeister, Nord, and Soni's "Dynamic Design Analysis to Support Architecture Design" supports deriving architectural insight from execution paths, not just module dependencies.
- Cornelissen et al.'s dynamic-analysis survey supports combining source evidence and runtime evidence for program comprehension.
- ISO/IEC/IEEE 42010 supports maintaining multiple corresponding views when one structural view is insufficient.

## 3. Evidence Base

- The generator analyzed 56 complete run directories under `operator/cre/runs/`.
- The current incomplete run directories are `070f6b51ff4a`, `3537e37f831e`, `7071c4ab92c2`, and `ablation_20260223_121639`.
- The live machine-readable outputs are:
  - `operator/cre/project_understanding/artifacts/dynamic_execution_architecture.json`
  - `operator/cre/project_understanding/artifacts/dynamic_transition_matrix.csv`
  - `operator/cre/project_understanding/artifacts/dynamic_execution_overview.mmd`
- Representative trace evidence used to validate the recovered view:
  - `operator/cre/runs/19dc71c8b483/trace.jsonl`
  - `operator/cre/runs/f967c6591f02/trace.jsonl`
  - `operator/cre/runs/b7dcf9ee41f5/trace.jsonl`
  - `operator/cre/runs/8d466eac548d/trace.jsonl`
  - `operator/cre/runs/15f87a8cc002/trace.jsonl`
  - `operator/cre/runs/a397b0a85d5e/trace.jsonl`
  - `operator/cre/runs/d07655943ebf/trace.jsonl`

## 4. Recovered Runtime Architecture

### 4.1 Runtime planes

The execution corpus resolves into seven runtime planes:

- `Observation Plane`: passive state capture via `a11y_passive_snapshot`
- `Bootstrap Plane`: URL/app/canvas initialization actions such as `go_to_url` and `magma_*`
- `Reset / Prepare Plane`: control-loop actions such as `clear_canvas`, `keystroke`, `sleep`, and `refresh_canvas_center`
- `Configure Plane`: tool and parameter setup such as `set_stroke_color` and some `click` actions
- `Production Plane`: artifact-producing actions such as `draw_concentric_triangles`, `draw_circle`, `draw_path`, `draw_eiffel_landscape`, and `bmw_*`
- `Verification Plane`: explicit `verify_success` plus encoded verification through oracle-backed `sleep`
- `Audit Plane`: terminal `metacognitive_audit`

The key methodological correction is that `sleep` is not always idle time.
In this corpus, 22 sleep steps are assertion-backed verification oracles and 3
additional sleep steps are trust-skipped verification checks.

### 4.2 Execution families

- `enterprise`: 42 runs. Dominant motif:
  `clear_canvas -> keystroke -> sleep -> sleep -> sleep -> refresh_canvas_center -> sleep -> keystroke`
- `universal`: 12 runs. Dominant motif:
  `a11y_passive_snapshot -> clear_canvas -> set_stroke_color -> draw_concentric_triangles`
- `magma_traced`: 1 run. Dominant motif:
  `magma_open_url -> magma_navigate_app -> magma_click_new_canvas -> magma_click_landscape -> magma_draw_bmw_e30`
- `iterative_art_study`: 1 run. Dominant motif:
  `bmw_skeleton -> bmw_form_blocking -> bmw_mechanical -> bmw_lighting -> bmw_final`

These families are visible in
`operator/cre/project_understanding/artifacts/dynamic_execution_architecture.json`
under `execution_family_profiles`.

### 4.3 Quantitative runtime structure

- Outcomes across the 56 complete runs:
  - 42 `success`
  - 12 `failure`
  - 2 `error`
- Raw manifest modes:
  - 42 `enterprise`
  - 12 `universal`
  - 1 `magma_traced`
  - 1 `unknown`
- Recovered execution families:
  - 42 `enterprise`
  - 12 `universal`
  - 1 `magma_traced`
  - 1 `iterative_art_study`
- Phase totals:
  - 272 `reset_prepare`
  - 54 `produce`
  - 48 `configure`
  - 36 `verify`
  - 12 `observe`
  - 5 `bootstrap`
  - 3 `audit`
- Most common phase transitions:
  - `reset_prepare -> reset_prepare`: 164
  - `reset_prepare -> configure`: 41
  - `reset_prepare -> produce`: 38
  - `configure -> reset_prepare`: 33
  - `reset_prepare -> verify`: 25
  - `verify -> reset_prepare`: 25

## 5. Main Findings

### 5.1 Enterprise runs are control-loop heavy

Enterprise is not just a drawing family. It is a control-dominant runtime
architecture with repeated reset, confirm, pause, recenter, configure, and
verify loops.

Evidence:
- `operator/cre/runs/19dc71c8b483/trace.jsonl`
- `operator/cre/runs/f967c6591f02/trace.jsonl`
- `operator/cre/project_understanding/artifacts/dynamic_transition_matrix.csv`

### 5.2 Verification is partly implicit, not only explicit

The runtime does not reserve verification solely for `verify_success`.
It also encodes verification inside oracle-backed `sleep` steps.

Evidence:
- 11 explicit `verify_success` steps
- 22 assertion-backed verification sleeps
- 3 trust-skipped verification sleeps
- `operator/cre/runs/f967c6591f02/trace.jsonl`
- `operator/cre/runs/b7dcf9ee41f5/trace.jsonl`

Consequence:
- any later runtime conformance gate must treat some `sleep` steps as semantic verification, not timing noise

### 5.3 Universal runs add observation and terminal audit semantics

Universal runs expose a materially different runtime architecture from the
enterprise Excalidraw path:

- explicit initial observation via `a11y_passive_snapshot`
- optional bootstrap via `go_to_url`
- terminal explanation audit at step `998`

Evidence:
- `operator/cre/runs/15f87a8cc002/trace.jsonl`
- `operator/cre/runs/8d466eac548d/trace.jsonl`
- `operator/cre/runs/6b1f2014145b/trace.jsonl`

### 5.4 Manifest outcome is not sufficient runtime truth

The run corpus contains semantic mismatches that matter architecturally:

- 8 runs terminate as `failure` or `error` without a failed trace step, meaning the run can fail at the manifest level outside ordinary action-step failure semantics
- 3 runs report `success` while containing failed trace steps, meaning success is sometimes judged at a larger scenario level than per-step success

Examples:
- terminal failure without failed trace step:
  - `operator/cre/runs/075a6e459eb2/manifest.json`
  - `operator/cre/runs/8d466eac548d/manifest.json`
- success with failed trace steps:
  - `operator/cre/runs/a397b0a85d5e/trace.jsonl`
  - `operator/cre/runs/d07655943ebf/trace.jsonl`
  - `operator/cre/runs/ff9cbb3fb684/trace.jsonl`

Consequence:
- architecture evaluation must read both manifest and trace semantics
- future scenario-based evaluation should distinguish run outcome, step outcome, and task-level acceptability

### 5.5 Outliers distort family-level averages

The universal family has a median duration of about 72.69 seconds, but its
average is about 2721.15 seconds because `operator/cre/runs/6b1f2014145b`
contains a 31,584-second timeout outlier.

Consequence:
- later performance or cost claims should use medians or capped summaries, not only arithmetic means

## 6. Implementation

Code added:

- `operator/cre/project_understanding/tools/build_dynamic_execution_architecture.py`
- `operator/cre/test_dynamic_execution_architecture.py`

Generated artifacts:

- `operator/cre/project_understanding/artifacts/dynamic_execution_architecture.json`
- `operator/cre/project_understanding/artifacts/dynamic_transition_matrix.csv`
- `operator/cre/project_understanding/artifacts/dynamic_execution_overview.mmd`

## 7. Usage

From the repo root:

```bash
python3 operator/cre/project_understanding/tools/build_dynamic_execution_architecture.py
```

For the live regression check:

```bash
cd operator
./venv/bin/python -m pytest cre/test_dynamic_execution_architecture.py -v --tb=short
```

## 8. What This Section Changes In The Overall Corpus

- The project-understanding corpus now has both static structure and recovered runtime structure.
- The next architecture step should no longer be another structural inventory pass.
- The strongest remaining step is scenario-based architecture evaluation over the now-visible runtime families.

## 9. Next Step

The next strongest section is scenario-based architecture evaluation:

- recoverability under GUI obstruction or modal interruption
- observability of root cause across manifest, trace, and evidence artifacts
- changeability of duplicated orchestration helpers
- security and HITL clarity during credential-sensitive workflows
- verification-cost tradeoffs in trust-skipped versus asserted paths
