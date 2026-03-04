# Canonical Runtime Baseline (PhD)

## Executive Summary
`concentric_study` now has an explicit host-tool health layer. The next Phase 1
hardening step is to define a single named runtime baseline for this repo so
startup, recovery, and future exploration all target the same known-good state.

For this environment, the correct baseline is **two-layered**, not a direct copy
of the parent `~/rust` Cursor-layout baseline:

1. **Global runtime baseline**
2. **Task-surface baseline**

That split fits the current system-of-interest:
- macOS `26.3`, `arm64`
- Cursor `2.5.26`
- Safari-based visual web agent
- `operator/venv` Python runtime

## Environment Basis
System of interest:
- `concentric_study`

Local environment:
- macOS `26.3`, build `25D125`, `arm64`
- Cursor `2.5.26`
- Safari installed at `/Applications/Safari.app`
- repo runtime: `./operator/venv/bin/python`

Repo-local evidence:
- `operator/agent.py`
- `operator/agent_infra/startup.py`
- `operator/agent_infra/recovery.py`
- `operator/agent_infra/host_tool_health.py`
- `operator/window_capture.py`
- `operator/cre/HOST_TOOL_HEALTH_DISCOVERY_PHD.md`
- `operator/cre/PHASE_1_ENVIRONMENT_BENEFITS_PHD.md`

Parent-environment evidence:
- `~/rust/CANONICAL_OPERATOR_STATE.md`
- `~/rust/cursor-nav/verify_nav_baseline.sh`
- `~/rust/operator/reset_cursor_baseline.sh`

## Why A Two-Layer Baseline Is Correct Here
The parent project baseline is application-layout-specific:
- Cursor must be fullscreen
- primary sidebar on
- secondary sidebar off
- panel off

That is appropriate for `~/rust`, whose system-of-interest is Cursor operator
control.

`concentric_study` is different. The critical substrate is:
- selected Python runtime
- native macOS UI automation
- screenshot/capture path
- browser target viability
- front-window capture viability
- site/task surface usability once a page is open

So one monolithic baseline would be too coarse. It would either:
- overfit a single app/site layout, or
- become too vague to enforce.

## Layer 1: Global Runtime Baseline
This is the baseline for the machine substrate itself.

### Formal invariant
Before task execution begins, the repo must be able to prove that the current
machine/runtime substrate is healthy enough to support the selected task class.

### Current baseline elements
1. selected runtime is `./operator/venv/bin/python`
2. `AppKit` and `Quartz` imports succeed
3. `osascript` + `System Events` are callable
4. `screencapture` is callable
5. Safari is present for URL-bearing tasks
6. optional augmentation backends are classified as optional, not required

### Current implementation status
Implemented:
- `operator/agent_infra/host_tool_health.py`
- `operator/agent_infra/tool_health_catalog.json`
- integration in `operator/agent.py`
- tests in `operator/cre/test_host_tool_health.py`

This means the **global runtime baseline** is now materially present as a
host-health gate, though not yet named as part of a unified baseline doctrine in
the runtime docs.

## Layer 2: Task-Surface Baseline
This is the baseline for the active task surface after the runtime substrate is
healthy.

### Formal invariant
Before task-specific execution begins, the active site/app surface must be in a
known-good usable state for the task family.

### Expected baseline elements
1. target app/browser is frontmost and usable
2. no blocking dialogs or stale overlays are present
3. the visible surface matches the intended task context
4. site-specific reset contracts can restore the surface if drift occurs

### Current implementation status
Partially present, but distributed:
- startup checks in `operator/agent_infra/startup.py`
- recovery checks in `operator/agent_infra/recovery.py`
- site-specific reset logic in action handlers and contracts

Not yet present:
- one named task-surface baseline contract
- one canonical verification entrypoint
- one canonical reset entrypoint for the whole runtime

## Correct Phase 1 Interpretation
Phase 1 should now be read as:

1. **Host-tool health discovery and backend selection**
   - now implemented
2. **Canonical runtime baseline and reset doctrine**
   - next hardening branch
   - should unify:
     - global runtime baseline
     - task-surface baseline

## Non-Goals
This baseline doctrine should not:
- encode one site-specific page layout as universal truth
- override `ResearchAgent`, `SiteKnowledge`, or `WebPrimitives`
- run heavy verification before every action
- replace task-level verification or recovery

It is a preflight/recovery anchor, not a planner.

## Acceptance Criteria For The Next Implementation Branch
The baseline/reset branch is complete only when:
1. the repo names one global runtime baseline
2. the repo names one task-surface baseline contract
3. both can be checked independently of task execution
4. both can be restored independently of task execution
5. failures can distinguish:
   - host substrate not ready
   - task surface drifted
6. this is integrated without degrading the current web-learning/runtime path

## Evidence Level
- **Direct support:** the current host-health gate and local startup/recovery code
- **Supported inference:** the two-layer baseline design derived from the mismatch
  between parent Cursor-layout control and current Safari/site-runtime control
- **Not yet implemented:** unified runtime baseline module and reset entrypoints
