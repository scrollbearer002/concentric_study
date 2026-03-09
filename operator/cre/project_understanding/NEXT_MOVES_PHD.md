# Next Moves: PhD-Level Checklist from All Angles

This document is the single actionable checklist derived from the lessons (LESSONS_FROM_THREE_UPLOADS_PHD.md), the mission-control stack (MISSION_CONTROL_STACK_AND_PROFILES.md), and the Live Safari checklist (LIVE_SAFARI_STACK_CHECKLIST.md). It states what is **done**, what is **next**, and how to **verify**, from five angles: operational, control room, integration, documentation, and verification.

---

## Angle 1: Operational (Live Tasks, Safari, Harnesses)

### Done
- **Mission Control** with profiles (live, debug, architecture, full) and health-based reuse.
- **Live profile** brings up Phoenix + Control Room; Control Room started with `CONCENTRIC_OTEL_ENABLE=1` and Phoenix collector endpoint for live/debug/full.
- **Evidence gate:** `mission_control.py evidence Safari --require-frontmost --capture`; harnesses call `_ensure_safari_ready()` (hide Cursor, activate Safari, then evidence).
- **Live Safari checklist** and **live-safari-stack.mdc** rule: mission_control up live, focus, evidence gate, coordinate discipline, artifact logging.
- **Reference harnesses** (human_benchmark_suite.py, mouse_accuracy_suite.py) use full stack; xbitlabs_path_follow.py uses full stack by default (skip_evidence opt-in only).

### Next
- **Run a live Safari task** with full stack (e.g. Human Benchmark Aim Trainer or XBitLabs Path Follow) and confirm: (1) `up live` brings Phoenix + Control Room up, (2) evidence gate passes when Safari is frontmost, (3) run produces traces/artifacts and (when OTel enabled) appears in Phoenix.
- **Optional:** Add a single end-to-end test or script that: `mission_control up live`, `_ensure_safari_ready()`, open a known URL, one verified click, then tear down or leave stack up for inspection.

### Verify
- `python3 operator/cre/project_understanding/tools/mission_control.py doctor --json` → `overall_ok: true` (or document known gaps).
- `mission_control.py evidence Safari --require-frontmost --capture --json` with Safari frontmost → `ready_for_visible_task: true`.

---

## Angle 2: Control Room (Viewpoints, Coordinated Views, SSE)

### Done
- **Canonical entity/viewpoint model:** viewpoints, laws, stations, files, selection state in snapshot.
- **Coordinated multi-view selection:** click a station → diagram focus, metrics, latest-run trace view, conformance, legitimacy, tool-hook relevance update together.
- **SSE:** `/api/events` for server→browser push; frontend can subscribe for targeted refresh.
- **Selection-aware diagram** and **station-aware drilldown** (latest_trace_hits, latest_trace_steps per station).
- **As-built regeneration:** conformance, dynamic execution, calibration, latest-run tail from repo and runs.

### Next
- **Semantic zoom / drilldown:** station → file list → artifact; rule → affected stations/files; run → trace family → verification/calibration (Phase 4 in the research plan).
- **Viewpoint labeling:** make each panel explicitly answer a concern (Founder, Operator, Debugger, Governance, Evaluator) in the UI.
- **Deep links:** from control room to Phoenix trace, to Sourcegraph, to Structurizr, when those tools are available.

### Verify
- `python3 operator/cre/project_understanding/tools/control_room.py --print-snapshot` (or serve and GET /api/state) → snapshot contains viewpoints, laws, stations, selection, observability, metrics.
- GET /api/events → SSE stream.
- Click a station in the UI → multiple panels update (manual check or automated if test harness exists).

---

## Angle 3: Integration (Phoenix, D2, Sourcegraph, Structurizr)

### Done
- **Phoenix + OTel (control room):** For live/debug/full profiles, mission_control starts Phoenix and Control Room with `CONCENTRIC_OTEL_ENABLE=1` and `PHOENIX_COLLECTOR_ENDPOINT`. control_room.py uses `concentric_observability` (ensure_observability, span, status_payload); snapshot includes `observability.enabled` and project name. So the **control room** is already instrumented and can send spans to Phoenix when the live profile is up.
- **run_phoenix_control_room.py:** Standalone launcher for Phoenix + Control Room with OTel; bootstraps Phoenix sidecar venv and starts both processes.
- **Tool hooks in control room:** Detection of Phoenix, D2, Sourcegraph, Structurizr, Understand, Import Linter (availability and commands).

### Next
- **Runtime agent instrumentation:** Instrument the main agent path (operator/agent.py, agent_infra trace_writer/recovery/action_handlers) with OTel spans so that **run_id**, **station_id**, **phase**, verification, and recovery events appear in Phoenix, not only control-room HTTP/snapshot spans. This is the “see the republic move in real trace space” step.
- **Trace links in UI:** Add “Open in Phoenix” (or similar) from control room run/station views to the Phoenix trace view for the current run/session.
- **D2:** Wire a live architecture window (e.g. D2 watch mode) and link from control room or mission_control (e.g. `open_architecture_view`).
- **Sourcegraph:** Deep links from station/file to Sourcegraph search or code graph (already partially present via sourcegraph_base_url and tool hooks).
- **Structurizr:** Use for canonical atlas when the model is stable; mission_control already has architecture/full profiles that start Structurizr.
- **Import Linter:** Wire as governance guard (pre-commit or CI or periodic check); not necessarily a visual window.

### Verify
- `mission_control.py up live` → Phoenix healthy on 6006, Control Room healthy on 8765 with `observability_enabled: true` in /api/state.
- Load control room in browser, trigger a snapshot (e.g. refresh); in Phoenix UI, confirm spans for control_room.* (e.g. control_room.build_snapshot, control_room.http.state).

---

## Angle 4: Documentation and Governance

### Done
- **LIVE_SAFARI_STACK_CHECKLIST.md:** Mandatory steps for live Safari tasks; links to MISSION_CONTROL_STACK_AND_PROFILES.md.
- **MISSION_CONTROL_STACK_AND_PROFILES.md:** Profiles, tools, when to use each; how it fits the Live Safari checklist.
- **LESSONS_FROM_THREE_UPLOADS_PHD.md:** Exhaustive synthesis of epistemic, architectural, validation, and operational lessons; §7 “Finished” and “Next” summarized.
- **.cursor/rules/live-safari-stack.mdc:** Rule that enforces full stack for visible browser tasks and points to both checklists and the profiles doc.
- **README.md** (project_understanding): References mission_control, evidence, run_phoenix_control_room, and control room.

### Next
- **§7 of LESSONS** already points to this document as the single “next moves” checklist; keep cross-links consistent when editing any of the four docs.
- **QUICKSTART_LIVE_TASKS.md** added: up live, evidence Safari, run harness X (BrowserBotics example); README points to it.

### Verify
- Cross-links between LIVE_SAFARI_STACK_CHECKLIST.md, MISSION_CONTROL_STACK_AND_PROFILES.md, LESSONS_FROM_THREE_UPLOADS_PHD.md, and this file are consistent and accurate.

---

## Angle 5: Verification and Regression

### Done
- **test_mission_control.py** and **test_control_room.py** exist and are runnable.
- **mission_control doctor** checks venv, Phoenix sidecar, D2, Structurizr, Docker, Sourcegraph identity, control-room snapshot build.
- Control room snapshot is built from live repo state (conformance, dynamic execution, calibration, latest run).

### Next
- **Run doctor and status** as part of any “proceed from all angles” pass: `mission_control.py doctor --json`, `mission_control.py status --json`.
- **Optional:** Add a minimal “live stack smoke” test: up live (or use existing healthy services), GET /api/state from Control Room, assert observability_enabled when profile is live.

### Verify
- `cd operator && ./venv/bin/python -m pytest cre/project_understanding/tools/test_mission_control.py cre/project_understanding/tools/test_control_room.py -v --tb=short` (or equivalent) → tests pass.
- `mission_control.py doctor --json` → report shows which checks passed and which are not yet satisfied on this machine.

---

## Summary: One-Line Next Action per Angle

| Angle        | Next action |
|-------------|-------------|
| **Operational** | Run one full live Safari task with `up live` + evidence + harness; confirm observability and artifacts. |
| **Control room** | Add semantic drilldown (station→file→artifact) and explicit viewpoint labels in UI; add deep link to Phoenix. |
| **Integration** | Instrument runtime agent (agent.py, trace_writer, recovery) with OTel spans; add “Open in Phoenix” from control room. |
| **Documentation** | QUICKSTART_LIVE_TASKS.md added; keep cross-links consistent. |
| **Verification** | Run doctor and status; run tests; optionally add live-stack smoke test. |

---

## Research Basis

Same as in LESSONS_FROM_THREE_UPLOADS_PHD.md: ISO/IEC/IEEE 42010, SEI reconstruction, multi-view comprehension, Shneiderman, OpenTelemetry, Phoenix, MDN SSE, D2, Structurizr, Sourcegraph, Import Linter, 12-Factor, mission supervisor design. This checklist does not introduce new research claims; it turns the lessons and existing design into an actionable list from all angles.
