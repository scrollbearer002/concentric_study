# What the Last Three Uploads Taught: PhD Exhaustive Synthesis

This document distills, in structured and citation-grounded form, what three major conversation arcs established: (1) the taxonomy of live vs near-live vs on-demand windows and the four-window Concentric sidecar stack; (2) building and PhD-validating the first Visual Control Room; (3) properly building v2 (viewpoints, coordinated views, evented updates, canonical model) and the research-backed ordering of external integrations (Phoenix first, then D2, Sourcegraph, Structurizr). No new design is introduced here; this is a synthesis of lessons already inferred in those uploads.

---

## 1. Epistemic and Methodological Lessons

### 1.1 Success signals are not interchangeable

- **Lesson:** Command success, AppleScript success, and DOM response do **not** imply that the cursor visibly clicked, that the page received the click, or that the human saw what was claimed.
- **Implication:** For live GUI work, only **visible-state proof** counts. Evidence must be captured (screenshot, frontmost check, coordinate chain) and logged; claims must be grounded in artifacts, not in “it ran without error.”
- **Where it appears:** Live Safari stack checklist, mouseaccuracy.com post-mortems, Human Benchmark vs mouseaccuracy.com contrast.

### 1.2 Frontmost state is a hard dependency for visible clicks

- **Lesson:** When Cursor remained frontmost, Safari received **zero** DOM mouse events from the Quartz path. After hiding Cursor and activating Safari, the same motor path produced real DOM events.
- **Implication:** Any visible browser task must **acquire focus** (e.g. hide Cursor, activate Safari) and **verify** readiness (evidence gate with `require_frontmost`) before issuing clicks. This is not optional.
- **Where it appears:** LIVE_SAFARI_STACK_CHECKLIST.md, live-safari-stack.mdc, mission-control evidence gate.

### 1.3 Coordinate spaces must be explicit and consistent

- **Lesson:** Window-relative screenshot pixels are **not** screen-global click coordinates. Retina scaling and window offset (e.g. Safari window top at y=31) cause systematic error if ignored.
- **Implication:** Always convert: DOM/client → viewport origin (or window bounds + content inset) → **screen-global**. Document the chain; log viewport_origin and representative conversions in run artifacts.
- **Where it appears:** Human Benchmark success formula (center_px/2 + offset), mouseaccuracy.com coordinate fixes, LIVE_SAFARI_STACK_CHECKLIST.md.

### 1.4 One supervisor, many specialized tools

- **Lesson:** The proper shape is a **control plane** (one CLI, explicit profiles) that starts the **right** services for the task type, not many ad hoc scripts or “everything on” by default.
- **Implication:** mission_control.py with profiles (live, debug, architecture, full) is the single entrypoint; each profile maps to a set of services (Phoenix, Control Room, Structurizr). Health-based reuse avoids duplicate processes and ports.
- **Where it appears:** Profile-based mission supervisor design, DEFAULT_PROFILES, MISSION_CONTROL_STACK_AND_PROFILES.md.

### 1.5 Live vs near-live vs on-demand is a design choice per window

- **Lesson:** Some tools are **truly live** (D2 watch, Phoenix, Sourcegraph local indexing, Structurizr Lite auto-refresh); some are **near-live** (Understand incremental, Import Linter on save/hook); some are **on-demand** (Excalidraw, manual refreshes). Forcing one refresh strategy on every view is wrong.
- **Implication:** Design each “window” (architecture map, code graph, runtime observatory, constitution monitor) with the appropriate refresh strategy. The system is **hybrid**: some views generated, some curated, some live.
- **Where it appears:** First upload (four-window setup, “map / street view / live traffic / constitutional police”), caution against one tool doing everything.

### 1.6 Multi-view power comes from coordination, not from panel count

- **Lesson:** The literature on multi-view sensemaking says the power is in **relationships between views** (selection in one view updates others), not in the mere existence of many panels.
- **Implication:** The control room must have a **canonical selection model** and **coordinated cross-view filtering** (e.g. click a station → diagram focus, run filter, conformance filter, legitimacy filter update together). This turns a dashboard into a cognitive instrument.
- **Where it appears:** Second and third uploads (coordinated views, Phase 2, “selection state in one place”).

### 1.7 Architecture description should be organized by viewpoints and concerns

- **Lesson:** ISO/IEC/IEEE 42010 and multi-view architecture work say descriptions should be organized around **stakeholders, concerns, viewpoints, and views**, not ad hoc panels.
- **Implication:** Every control-room panel should answer a **specific concern** (e.g. Founder: system shape; Operator: what is happening now; Debugger: where failure entered; Governance: where the constitution is drifting; Evaluator: whether outcomes are trustworthy). Viewpoints should be explicit in the model.
- **Where it appears:** Third upload (viewpoint model, Phase 1), control room viewpoints/laws in snapshot.

### 1.8 As-built reconstruction plus live evidence beats decorative architecture

- **Lesson:** SEI reconstruction guidance and observability practice say: recover architecture from the **implemented** system and correlate with **runtime** evidence. Static structure alone is insufficient.
- **Implication:** The control room should **regenerate** conformance, dynamic execution artifacts, and calibration from the repo and from runs (manifest, trace tail). It must not be a static brochure.
- **Where it appears:** Second upload (PhD validation), “as-built architecture plus live evidence.”

### 1.9 Overview first, then zoom/filter, then details on demand

- **Lesson:** Shneiderman’s information-seeking mantra (overview first, zoom and filter, details on demand) is the right interaction spine for complex system comprehension.
- **Implication:** Top-level diagrams and metric cards are overview; stations, run summary, trace tail, conformance are first detail layer. The proper v2 adds **semantic zoom** (subsystem → file → artifact), **filter** (by station, run, failure type), and **relate** (how selected item connects to others).
- **Where it appears:** Second and third uploads (overview-first layout, Phase 3/4 drilldown).

### 1.10 Evented updates reduce latency and support coordinated refresh

- **Lesson:** Polling is acceptable for v1; the research-backed v2 uses **snapshot + event stream** (e.g. SSE) so the server can push changes (latest-run, conformance, calibration, diagram notices) and the client can do **targeted re-render** instead of full-page refresh.
- **Implication:** Backend exposes `/api/state` (full snapshot) and `/api/events` (SSE). Frontend subscribes to events and updates only the affected views. MDN SSE guidance supports this as the right transport for server→browser updates.
- **Where it appears:** Third upload (evented backend, SSE, MDN EventSource/SSE).

### 1.11 Canonical entity model precedes coordinated views

- **Lesson:** Coordinated-view systems break down if each panel invents its own schema. There must be **stable entity IDs** (run_id, station_id, trace_id, file_id, law_id, viewpoint_id) and a **single domain model** that views render from.
- **Implication:** Phase 1 is viewpoint and entity model; Phase 2 is coordinated-view frontend that consumes that model. Selection state is part of the model (e.g. selected_station_id) and drives all views.
- **Where it appears:** Third upload (canonical model, Phase 1 and 2 build order).

### 1.12 External integrations are specialized windows, not replacements for the shell

- **Lesson:** The control room should be the **orchestrating shell** that links external tools (Structurizr, D2, Phoenix, Sourcegraph, Import Linter), not a reimplementation of all of them.
- **Implication:** Control Room = command center; Phoenix = runtime truth; D2 = live architecture diagrams; Sourcegraph = semantic drilldown; Structurizr = canonical atlas; Import Linter = constitution monitor. Attach them in an order that maximizes marginal epistemic gain.
- **Where it appears:** All three uploads (four-window setup, tool hooks, “do not duplicate Phoenix/Structurizr inside the control room”).

### 1.13 Integration order should maximize new truth, not polish

- **Lesson:** The next external integration should add a **new truth layer** the system does not yet have. For Concentric, the biggest missing layer was **live span-level runtime observability**, not better diagramming.
- **Implication:** **Phoenix + OpenTelemetry first** (traces/spans/evals); then D2 (improve architecture view quality); then Sourcegraph (code drilldown); then Structurizr (canonical atlas once the model stabilizes). Import Linter is governance, not the first visual integration.
- **Where it appears:** Third upload (research-backed ranking: Phoenix first, then D2, Sourcegraph, Structurizr).

---

## 2. Architectural and Design Lessons

### 2.1 Four persistent windows as a design template

- **Architecture Map:** D2 or Structurizr; generated from repo-aware inputs; auto-refresh on file change (D2 watch, Structurizr Lite). Best for “seeing the republic as a system.”
- **Code Graph / Dependency View:** Sourcegraph or Understand; local indexing / incremental analysis. Best for “what does this station touch?”
- **Runtime Observatory:** Phoenix; live dashboard while the agent runs. Best for traces, spans, failures, verification, recovery.
- **Constitution Monitor:** Import Linter plus conformance checks; run on save, pre-commit, or continuous. Best for boundary and rule violations.

Together they provide: **map** (structure), **street view** (code), **live traffic** (runtime), **constitutional police** (governance).

### 2.2 Repo-local command layer

- **Lesson:** The most powerful thing is a **repo-local command layer** that starts the right server, opens the right tab or app, and optionally watches the right files and regenerates artifacts when code changes.
- **Implication:** Commands like `mission_control.py up live --open`, and future shims like `open_architecture_view`, `open_runtime_view`, `open_code_graph`, `open_conformance_view`, give a single vocabulary for “bring up the republic map,” “open the live trace room,” “show me if the constitution broke.”

### 2.3 Profile-to-service mapping

- **live:** Phoenix + Control Room. Default for Safari, Mac navigation, app workflows, aim trainers, puzzle sites.
- **debug:** Phoenix + Control Room (explicit focus on runtime + drilldown).
- **architecture:** Control Room + Structurizr. Redesign, subsystem/repo mapping.
- **full:** Phoenix + Control Room + Structurizr. When both observability and atlas are needed.

Sourcegraph is used as a **bridge** from inside the Control Room when code-path debugging is needed; it is not a separate profile service.

### 2.4 Control room as shell, not mega-tool

- The control room **coordinates** runtime, conformance, calibration, Sourcegraph links, Structurizr links, and station focus. It does **not** duplicate Phoenix’s trace UI, Structurizr’s workspace model, or D2’s diagram engine. It holds the **canonical selection and viewpoint model** and drives **coordinated views** and **deep links** into external tools.

### 2.5 Hybrid view authorship

- **Generated:** Recovered from code or runs (e.g. conformance, dynamic execution diagram, latest-run tail).
- **Curated:** Human-maintained architecture views, ADRs, ministry descriptions.
- **Live:** Fed by real-time telemetry (Phoenix) or file watchers (D2, Sourcegraph indexing).

Do not force one tool to produce every view; do not try to make every view fully auto-generated from raw code on day one.

---

## 3. Validation and Verification Lessons

### 3.1 Verify against live repo and running server

- The control room was verified by: (1) tests (e.g. test_control_room.py), (2) live server GET / and GET /api/state, (3) live SSE /api/events, (4) snapshot content (viewpoints, laws, stations, conformance_passed, blocking_failures). So the build was checked **while building**, not only in theory.

### 3.2 PhD-level check means literature + implementation

- “PhD research on what you built” meant: (1) map the build to architecture and visualization literature (ISO/IEEE, SEI, multi-view, Shneiderman, OpenTelemetry, Phoenix, SSE), (2) state what is strong vs moderate vs early-stage, (3) state what should come next with a clear rationale and build order. The outcome was an honest v1 assessment and a phased v2 plan.

### 3.3 Next-step research before implementation

- Before “the next correct move,” research was run to rank external integrations (Phoenix vs D2 vs Sourcegraph vs Structurizr) by **marginal epistemic gain** and **orthogonality** to what the control room already has. That produced the order: Phoenix first, then D2, then Sourcegraph, then Structurizr.

---

## 4. Operational Lessons (Live Tasks + Stack)

### 4.1 Live Safari checklist is mandatory for visible browser tasks

- For any task that drives the cursor to click or interact in Safari: (1) mission_control up **live** (Phoenix + Control Room), (2) hide Cursor and activate Safari, (3) evidence gate with require_frontmost and optional capture, (4) coordinate discipline (viewport/bounds + inset → screen-global), (5) post-action proof when needed, (6) artifact logging. No default to `--skip-evidence`; no ad hoc scripts.

### 4.2 Mission Control up = live profile for live tasks

- “Bring up the stack” for a live browser task means **up live**, which starts Phoenix and Control Room. That gives both (a) the evidence pipeline and capture and (b) **observability** (traces, runtime state). Evidence and observability are tied to the same profile.

### 4.3 Harnesses must use the full stack by default

- Reference harnesses (human_benchmark_suite.py, mouse_accuracy_suite.py) use mission_control up, _ensure_safari_ready(), viewport origin, and artifact logging. New harnesses (e.g. xbitlabs_path_follow.py) must use the same stack by default; `--skip-evidence` is opt-in for fast reruns only.

---

## 5. Sources and Provenance

The lessons above are grounded in the following (as cited in the three uploads):

- **Architecture and viewpoints:** ISO/IEC/IEEE 42010 (conceptual model, applying the standard), SEI Architecture Reconstruction Guidelines, Hilliard on multiple architecture views.
- **Visualization and interaction:** Shneiderman (overview, zoom, filter, details on demand), multi-view software comprehension (e.g. arXiv:1902.00526), software-city and trace visualization.
- **Observability and telemetry:** OpenTelemetry (signals, deployment), Phoenix (tracing, tutorial, OTel API), MDN Server-Sent Events and EventSource.
- **Tools:** D2 (watch mode, tour), Structurizr (workspaces, Lite usage, perspectives, static export), Sourcegraph (local indexing, reindex on change), Import Linter (usage, caching).
- **Operational:** 12-Factor admin processes, Typer/CLI design, psutil, launchd (optional persistence).

---

## 6. Summary Table: What Each Upload Taught

| Upload | Main lesson | Concrete outcome |
|--------|-------------|------------------|
| **1. Live vs near-live; four windows** | Not all windows update the same way; the best Concentric setup is a sidecar with four roles (map, street view, live traffic, constitution), repo-local commands, and hybrid view authorship. | Taxonomy of tools (truly live / near-live / on-demand), four-window template, “map + street view + live traffic + constitutional police,” caution against one-tool-does-all. |
| **2. Build Control Room; PhD-validate it** | Multi-view, as-built reconstruction, and overview-first are research-valid; the build is strong on reconstruction/overview/repo-local and moderate on interaction/runtime; coordinated views and real telemetry are the right next steps. | First control room (control_room.py, index.html, app.js, tests), explicit assessment of strengths and gaps, and a phased v2 plan (viewpoints, coordinated views, SSE, drilldown, external integrations). |
| **3. Properly build v2; order external integrations** | Proper v2 = viewpoints + canonical model + coordinated selection + evented updates + drilldown; external integrations should be ordered by marginal epistemic gain (Phoenix first, then D2, Sourcegraph, Structurizr). | Implemented: canonical entity/viewpoint model, coordinated multi-view selection, SSE, selection-aware diagram, station-aware drilldown. Research verdict: Phoenix + OTel first, then D2, Sourcegraph, Structurizr. |

---

## 7. What This Means for “Finished” and “Next”

- **Finished (as of the third upload):** The **in-repo** control-room sequence: canonical model, coordinated views, SSE, selection-aware diagram, station-aware drilldown. The **optional** external-tool phases (Phoenix, D2, Sourcegraph, Structurizr) are **not** finished; they are the next phases.
- **Next correct moves (from the uploads):** (1) First external integration: **Phoenix + OpenTelemetry** (instrument stations/phases as spans, run Phoenix locally, add trace links from the control room, correlate run_id/station_id/phase/verification/recovery). (2) Then D2 for live architecture window. (3) Then Sourcegraph for semantic drilldown. (4) Then Structurizr for canonical atlas when the model is stable. (5) Import Linter as governance guard (save/commit or continuous), not necessarily a “window.”

**Single actionable checklist from all angles (operational, control room, integration, documentation, verification):** see **NEXT_MOVES_PHD.md** in this directory. That document states what is done vs next per angle and how to verify; update it when advancing on any of these fronts.

This document is the PhD-exhaustive synthesis of what the last three uploads taught; it does not add new design theses beyond what those arcs already established.
