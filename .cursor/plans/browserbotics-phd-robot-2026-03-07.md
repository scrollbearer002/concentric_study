# PhD-Level Robot on BrowserBotics Sandbox — Plan

**Objective:** Build an original, research-grounded robot controller in the BrowserBotics sandbox, with no plagiarism. All interaction via Safari.

## Research basis (citations only; implementation is original)

- **Formal methods in robotics:** Formal verification of control systems (e.g. UAV feedback controls; White Rose eTheses). We adopt the *idea* of discrete abstraction + invariants, not any specific code.
- **Temporal logic specifications:** LTL/STL for robot behavior (e.g. “always eventually reach goal”, “never enter forbidden set”). We implement a minimal state machine that *satisfies* a simple safety + liveness condition.
- **Controller synthesis with safety:** Reachability and barrier functions (e.g. TUM work on safety-critical systems). Our controller maintains a *safe set* (joint limits, workspace bounds) by construction.
- **PyBullet-inspired API:** BrowserBotics API reference and quickstart only; no copying of third-party robot code.

## Design (original)

1. **Abstraction:** Discrete mode set `{INIT, TRACK, HOLD}` and a continuous state (joint positions, time).
2. **Specification (our wording):**
   - **Safety:** Joint positions remain within prescribed limits at all times.
   - **Liveness:** The arm eventually reaches a target configuration and holds for a prescribed duration.
3. **Implementation:** 
   - Use `stepSimulation(dt)` in a loop with `setRealtime(False)` for deterministic stepping.
   - At each step: read joint positions, compute clamped target from a trajectory that respects limits, apply `setJointMotorControl`.
   - Mode transitions: INIT → TRACK when simulation started; TRACK → HOLD when within tolerance of goal; optional return to TRACK for a second goal.
4. **No copied code:** All logic written from API reference and the above specification only.

## Deliverables

- This plan (`.cursor/plans/browserbotics-phd-robot-2026-03-07.md`).
- **Single source of truth for site + PhD building:** `operator/cre/project_understanding/BROWSERBOTICS_PHD_SITE_AND_ROBOT_BUILDER.md` — complete URL/layout/API/specs and PhD robot builder checklist.
- Single Python file for sandbox: `operator/cre/project_understanding/tools/browserbotics_phd_robot.py` (pasted into sandbox via harness).
- **Full-stack Safari runner:** `operator/cre/run_browserbotics_safari_phd.py` — mission_control evidence gate, Safari focus, bounds+inset coordinates, paste robot code, click Run. Compliant with LIVE_SAFARI_STACK_CHECKLIST.md.
- Safari: open https://browserbotics.com/sandbox (harness opens it if not already open), then run the harness to paste and execute.

## Verification

- Code runs in sandbox without external dependencies beyond `browserbotics`.
- Joint targets are clamped to safe limits; mode machine is explicit.
- Comments cite research areas only; no verbatim material from papers or others’ code.
