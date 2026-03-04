# Pre-Click Confirmation Research

## Environment basis
This memo is specific to the live `concentric_study` repo on this Mac:

- macOS arm64
- Safari as the live browser surface
- `operator/window_capture.py` for front-window capture
- `operator/agent_core.py` for Gemini structured visual judgments
- `operator/agent_infra/action_handlers.py` for centralized click execution

The system-of-interest is the current Safari/macOS visual web-agent runtime, not a generic browser bot.

## Research question
Should this project add a screenshot-backed confirmation step before risky clicks, and if so, how should it fit the existing architecture without degrading the strong current path?

## Local evidence
The repo already has the right substrate for a bounded risky-click gate:

- cursor movement:
  - `operator/agent_core.py`
- structured Gemini visual assertions:
  - `operator/agent_core.py`
- front-window capture:
  - `operator/window_capture.py`
- click execution concentrated in one handler:
  - `operator/agent_infra/action_handlers.py`
- recovery and monitor layers already treat screenshots as operational evidence:
  - `operator/agent_infra/recovery.py`
  - `operator/agent_infra/visual_monitor.py`

The recurring failure modes in this repo have not mainly been “mouse click failed.” They have been:

- wrong visible surface
- popup or overlay interference
- stale layout assumptions
- clicking before confirming the current state

That makes a pre-click confirmation layer a good fit.

## What the strongest external sources support

### 1. GUI agents benefit from closed-loop confirmation
- OSWorld: real GUI-agent failures are dominated by grounding and operational mismatch  
  <https://arxiv.org/abs/2404.07972>
- SeeAct: semantic intent should be grounded through explicit visual actions, not vague step text  
  <https://arxiv.org/abs/2401.01614>
- ShowUI: stronger visual-action coupling matters for GUI control  
  <https://arxiv.org/abs/2411.17465>
- UI-Hawk: temporal/screen context matters; current frame alone can be misleading  
  <https://aclanthology.org/2025.emnlp-main.920/>

These sources support a screenshot-backed confirmation layer before risky actions.

### 2. Prompt quality and structured outputs matter
- Google Gemini image understanding docs  
  <https://ai.google.dev/gemini-api/docs/image-understanding>
- Google Gemini structured output docs  
  <https://ai.google.dev/gemini-api/docs/structured-output>

These sources support asking Gemini Flash a constrained go/no-go question over a cursor-visible screenshot instead of relying on free-form prose.

### 3. Verification should stay bounded and non-destructive
- This repo already uses post-action verification and structured recovery rather than blind retries.
- A pre-click gate should preserve that discipline:
  - confirm first for risky clicks
  - do not globally slow down every click

## Best architecture for this repo

The correct shape is:

1. **Move cursor first**
2. **Capture the front Safari window with the cursor visible**
3. **Ask Gemini Flash for a structured judgment**
4. **Click only if approved**

This should live:

- above the raw Quartz click substrate
- below planning/site-learning
- inside the click handler path

This should **not** become:

- a global before-every-click policy
- a replacement for the current runtime
- a planner rewrite

## Correct bounded scope
Recommended initial scope:

- direct coordinate clicks
- risky labeled clicks
- dialog buttons
- submit/continue buttons
- tool-changing clicks on unfamiliar websites

Not for:

- every draw-path point
- every drag segment
- every already-proven low-risk click

## Implementation contract

### New structured judgment
`confirm_click_target(...)`

Required fields:

- `approved`
- `target_under_cursor`
- `blockers_present`
- `expected_effect_likely`
- `confidence`
- `rationale`
- `suggested_action`

### Capture requirement
Use cursor-visible capture:

- `capture_front_window(..., include_cursor=True)`

### Click integration rule
Only block when:

- confirmation mode is explicitly requested, or
- repo/user policy later promotes it to a stronger default for specific action families

## Why this improves the project without degrading it

Directly supported by the local code:

- the strong click/runtime path remains intact when confirmation is off
- the new layer is opt-in
- the new layer reuses existing screenshot and Gemini infrastructure
- it improves exactly the failure class this repo has struggled with

That makes it a **core enhancement with non-regression evidence**, not a risky rewrite.

## Current implementation status
Implemented in this repo:

- cursor-visible front-window capture
- structured pre-click judgment in `agent_core`
- opt-in click gating in `action_handlers`
- focused tests

## References
- OSWorld: <https://arxiv.org/abs/2404.07972>
- SeeAct: <https://arxiv.org/abs/2401.01614>
- ShowUI: <https://arxiv.org/abs/2411.17465>
- UI-Hawk: <https://aclanthology.org/2025.emnlp-main.920/>
- Gemini image understanding: <https://ai.google.dev/gemini-api/docs/image-understanding>
- Gemini structured output: <https://ai.google.dev/gemini-api/docs/structured-output>
