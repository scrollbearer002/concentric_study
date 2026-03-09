# Section 7: Outcome Semantics Unification

## 1. Purpose

Section 6 identified the top-ranked risk theme in `concentric_study` as
fragmented outcome semantics:

- step-level success lived in `action_result.success`
- run-level success lived in manifest `outcome`
- final verification lived in a trace step or side artifact

This section records the implementation that turns those three signals into one
explicit contract.

## 2. Problem

Before this change, the repo could exhibit all of the following:

- `manifest.json` rejected a run without a canonical failure step
- accepted runs still contained failed trace steps from meta actions
- final verification failure was visible in trace data but not normalized in the
  manifest itself
- downstream consumers had to infer whether a run was rejected because of:
  - execution failure
  - verification failure
  - meta-step failure

That made diagnosis, benchmark interpretation, and calibration weaker than they
needed to be.

## 3. Implementation

The canonical implementation is now in:

- `operator/agent_infra/trace_writer.py`
- `operator/agent_infra/diagnostic_reader.py`
- `operator/agent_infra/benchmark_evaluator.py`

### 3.1 New manifest contract

`TraceWriter.finalize()` now writes `manifest["outcome_semantics"]` with:

- `task_result`
- `execution_result`
- `acceptance_basis`
- `final_verification`
- `step_outcomes`
- `consistency`

This makes the correspondence explicit:

- task acceptance/rejection
- raw execution outcome
- final verification pass/fail/not-run
- productive vs. meta failed steps

### 3.2 Canonical failure inference

If a run is rejected and no failure step was explicitly recorded, the trace
writer now infers canonical failure metadata from:

1. failed final verification
2. otherwise, the first failed step

This repairs the earlier case where final verification rejection could produce a
failed run with no canonical failure step in the manifest.

### 3.3 Diagnostic reader support

`DiagnosticReader` now surfaces the normalized contract directly in the level-1
summary and exposes `get_outcome_semantics()`.

### 3.4 Benchmark evaluator support

`BenchmarkEvaluator.check_success` now prefers normalized `task_result` when it
is available instead of depending only on raw manifest `outcome`.

## 4. What Changed Semantically

The repo now distinguishes:

- `execution_result`: what the runtime reported overall
- `task_result`: whether the task is accepted or rejected
- `final_verification.status`: whether the verification gate passed, failed, or
  did not run
- `step_outcomes.productive_failed` vs. `step_outcomes.meta_failed`

This is the key correction.

It means the architecture can now represent cases like:

- accepted run with failed meta audit
- rejected run due to final verification failure
- rejected run due to execution failure before final verification

without forcing all of them into the same ambiguous interpretation.

## 5. Local Verification

Focused local validation passed after the implementation:

- `23 passed` across:
  - `cre/test_trace_writer.py`
  - `cre/test_diagnostic_reader.py`
  - `cre/test_trace_integration.py`
  - `cre/test_runtime_tool_integration.py`
- `3 passed` in `cre/test_kleki_art_quality.py`
- `42 passed` across the broader regression slice:
  - `cre/test_action_space_conformance.py`
  - `cre/test_phase3_equation_solver.py`
  - `cre/test_research_guided_planning.py`
  - `test_router_dryrun.py`
  - `cre/test_browser_dialog_controls.py`
  - `cre/test_architecture_conformance.py`

The architecture conformance gate also remained green.

## 6. Effect On The Research Agenda

This change closes the specific Section 6 recommendation to unify outcome
semantics.

The strongest next empirical move is now:

- calibrate `VerificationGate` and related effect checks against human judgment

Why:

- the repo now has a clearer truth surface for accepted vs. rejected runs
- that makes verification calibration and benchmark-validity work much more
  interpretable

## 7. Usage

Use this section when you need to know:

- what the normalized manifest contract means
- how final verification now maps into canonical run failure semantics
- why accepted runs can still contain failed meta steps without architectural
  ambiguity
