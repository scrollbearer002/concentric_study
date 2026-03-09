# Live Visual Control Demo (2026-03-05)

## 1) Objective and Constraints

- objective:
  - execute a live visible automation sequence so the operator can watch cursor movement, clicks, and typing in real time
- hard constraints:
  - use a safe target app with no destructive side effects
  - keep the demo local-only (no credential entry, no account actions)
  - produce a durable evidence artifact after execution
- soft constraints:
  - keep the sequence human-legible (smooth moves + paced typing)
- out of scope:
  - website login flows
  - sensitive profile changes

## 2) Evidence Used

- repo files:
  - `operator/agent_core.py`
  - `operator/cre/test_canva_ai_image.py`
  - `operator/cre/run_qa_practice_safari_probe.py`
- runtime/environment checks:
  - selected backend class for `native_event_backend` is `pyobjc_native_stack`
  - selected automation provider includes `osascript_system_events`
- external sources (if required):
  - none

## 3) Plan and Checkpoints

1. checkpoint: prepare live script
   - expected outcome:
     - script uses native Quartz mouse/keyboard events and AppleScript app activation
   - pass condition:
     - script runs without import/runtime errors
   - fail condition:
     - PyObjC, accessibility, or script runtime failure
2. checkpoint: execute visible sequence
   - expected outcome:
     - operator can watch pointer move, click into document, and type text
   - pass condition:
     - final text appears in target document and completion screenshot is captured
   - fail condition:
     - pointer events or typing does not land on target surface
3. checkpoint: record evidence
   - expected outcome:
     - durable JSON artifact with action timeline and screenshot path
   - pass condition:
     - artifact file written and valid JSON
   - fail condition:
     - missing or malformed evidence artifact

## 4) Risk and Stop Conditions

- stop if:
  - target app cannot be focused reliably
  - accessibility events are blocked
- rollback trigger:
  - unintended interaction with non-target app/window
- downgrade path:
  - switch to dry-run trace without posting events

## 5) Execution Log

- step:
  - change:
    - added `operator/cre/run_live_visual_control_demo.py` (native Quartz + System Events demo driver)
  - rationale:
    - provide an operator-visible proof of real mouse movement, clicks, and typing
- step:
  - change:
    - first run failed with TextEdit AppleEvent timeout (`-1712`)
    - captured failure in `operator/cre/artifacts/live_visual_control_demo_2026-03-05.json`
  - rationale:
    - failure class isolated to direct TextEdit AppleEvent path
- step:
  - change:
    - patched script to use robust activation path:
      - `open -a TextEdit`
      - System Events `frontmost` + `Cmd+N`
      - main-display bounds for deterministic pointer path
  - rationale:
    - remove direct TextEdit document AppleEvent dependency
- step:
  - change:
    - reran demo successfully with full visible sequence and screenshot capture
  - rationale:
    - satisfy live operator-observable control objective

## 6) Verification

- commands/artifacts:
  - `cd operator && ./venv/bin/python cre/run_live_visual_control_demo.py`
  - `operator/cre/artifacts/live_visual_control_demo_2026-03-05.json`
- `operator/cre/artifacts/live_visual_control_demo_2026-03-05.png`
- results:
  - live run completed (`success: true`) with timestamped action timeline:
    - activate app
    - five smooth pointer path points
    - center click
    - typed multiline payload
    - screenshot captured
  - artifact validation:
    - `python3 -m json.tool ...` -> `OK`
    - screenshot exists (`~1.0M`)
- unresolved issues:
  - no blocking issues for safe local control demo
  - Cursor-surface specific demo is still pending (this pass intentionally used safe TextEdit target)

## 7) Next Best Action

- immediate next action:
  - adapt the same live control script to a Cursor-surface sequence:
    - activate Cursor
    - open a scratch tab
    - perform visible pointer move + click + typed non-destructive payload
- deferred action:
  - add traced run manifest integration to the live demo flow for stronger post-run forensics
