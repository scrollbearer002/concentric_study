# Exhaustive PhD Master: Every Tool, Tip, and Trick in Concentric Study

This document is a single reference for **every tool, entry point, capability, and tip** in the project. Use it to find how to run something, what to set, and what tricks exist. Nothing here is invented; all anchors are to real files and commands.

---

## 1. Quick index (find fast)

| I want to… | Go to section |
|------------|----------------|
| Run the main agent / GUI test | §2.1, §2.2 |
| Run a live Safari / aim / path-follow task | §3, §4 |
| Use mission control / evidence gate | §3.1, §5 |
| See all CLI commands and scripts | §6 |
| See all agent actions (click, draw, etc.) | §7 |
| Check host/tool health | §8 |
| Use agent_infra (tracing, healing, skills, etc.) | §9 |
| Set env vars and flags | §10 |
| Apply tips (Safari focus, coordinates, calibration) | §11 |
| Run build/audit/calibration tools | §12 |
| Run tests (pytest + manual) | §13 |
| Use MCP / Cursor integration | §14 |
| Use Codex/Hammerspoon kernel | §15 |
| Understand perception / security / macOS permissions | §9 (perception), §18, §19 |
| Verification calibration (human agreement) | §12, §17 (SECTION_8) |
| Control room, Phoenix, Structurizr, artifacts | §6.2, §17, §20 |
| Other runnable scripts (drawing studies, tests as main) | §6.9 |
| Shell scripts (run_agent, verify_kernel, install reminders) | §6.10 |

---

## 2. Main agent and canonical test

### 2.1 Universal agent (any URL, any goal)

**File:** `operator/agent.py`

**Run:**
```bash
cd operator
./venv/bin/python agent.py --url https://excalidraw.com --goal "Draw 4 concentric black triangles"
./venv/bin/python agent.py --url https://kleki.com --goal "Draw a BMW E30 M3"
./venv/bin/python agent.py --goal "Navigate to Excalidraw and draw a red circle"
```

**Behavior:** Classifies mission, staffs capabilities, opens Safari (or uses existing), runs research/planning if needed, executes action plan with recovery and verification, writes trace and manifest. URL can be omitted if goal mentions excalidraw/kleki/magma (auto-filled).

### 2.2 Canonical benchmark test (Excalidraw concentric triangles)

**File:** `operator/cre/test_excalidraw_covt.py`

**Run:**
```bash
cd operator
CONCENTRIC_TRIANGLES_CLEAN=1 ./venv/bin/python cre/test_excalidraw_covt.py
```

**Env (optional):** `CONCENTRIC_TRIANGLES_CLEAN`, `CONCENTRIC_TRIANGLES`, `AGENT_GOAL`, `EXECUTION_LOG_PATH`, `PASS_LOG_PATH`, `DISABLE_COORD_CACHE`, `DISABLE_TRUST_TRACKER`, `DISABLE_ADAPTIVE_ROUTING`, `DISABLE_ACTION_ALLOWLIST`, `DYNAMIC_PLAN`, `ABLATION_CONDITION`. See §10.

**Tip:** Use venv; do not use system Python. Trace is at `operator/cre/runs/<run_id>/trace.jsonl`; when `manifest.json` appears, run is done. Read results with `DiagnosticReader("operator/cre/runs/<run_id>").full_diagnostic()`.

---

## 3. Live Safari stack (mandatory for visible browser tasks)

**When:** Any task that clicks or interacts in Safari (aim trainers, puzzle sites, canvas, forms). Rules: `LIVE_SAFARI_STACK_CHECKLIST.md`, `live-safari-stack.mdc`.

### 3.1 Mission Control

**File:** `operator/cre/project_understanding/tools/mission_control.py`

**Commands:**

| Command | Purpose |
|---------|---------|
| `mission_control.py up live [--open]` | Bring up live profile (Phoenix + Control Room). **Do this first** for Safari/aim/path tasks. |
| `mission_control.py up debug [--open]` | Same as live; use when you want runtime + drilldown focus. |
| `mission_control.py up architecture [--open]` | Control Room + Structurizr (no Phoenix). |
| `mission_control.py up full [--open]` | Phoenix + Control Room + Structurizr. |
| `mission_control.py down [profile]` | Stop a profile (profile optional). |
| `mission_control.py down --all` | Stop all managed services. |
| `mission_control.py open <profile>` | Open healthy service URLs for a profile. |
| `mission_control.py status` | Show managed and live service status. |
| `mission_control.py doctor` | Environment and stack health checks. |
| `mission_control.py evidence Safari [--require-frontmost] [--capture] [--strict]` | GUI evidence gate: frontmost check, optional screenshot. **Do not proceed** until `ready_for_visible_task` is true. |

**Tip:** Always pass `--json` for machine-readable output when scripting.

### 3.2 Evidence gate and focus (tips)

- **Hide Cursor, then activate Safari** before any visible click. If Cursor stays frontmost, Safari can receive zero DOM events from Quartz.
- **Evidence before action:** `mission_control.py evidence Safari --require-frontmost --capture --json` (or in code `_ensure_safari_ready()`). Do not skip for “quick” runs when the task is visible.
- **Coordinates:** Convert DOM/client coords to **screen-global** using window bounds + content inset (or viewport origin). Do not use raw screenshot pixels as click coordinates (Retina and window offset break this). Use `_global_from_client(cx, cy, viewport_origin=...)` or equivalent.
- **Artifact logging:** Log evidence payload, viewport_origin, and per-step state so failures are diagnosable from logs.

**Ref:** `LIVE_SAFARI_STACK_CHECKLIST.md`, `QUICKSTART_LIVE_TASKS.md`, `MISSION_CONTROL_STACK_AND_PROFILES.md`.

---

## 4. Live harnesses (Safari aim / path / benchmarks)

All use the full stack (mission_control up, evidence gate, bounds+inset) unless `--skip-evidence` is set for a fast rerun.

### 4.1 Human Benchmark

**File:** `operator/cre/project_understanding/tools/human_benchmark_suite.py`

**Commands (from `operator/`):**
```bash
./venv/bin/python cre/project_understanding/tools/human_benchmark_suite.py aim [--name aim_manual] [--move-duration 0.05] [--move-steps 8] [--settle-sleep 0.2]
./venv/bin/python .../human_benchmark_suite.py sequence [--name sequence_manual] ...
./venv/bin/python .../human_benchmark_suite.py chimp ...
./venv/bin/python .../human_benchmark_suite.py typing ...
./venv/bin/python .../human_benchmark_suite.py reactiontime [--name reaction_manual] ...
./venv/bin/python .../human_benchmark_suite.py verbal-memory ...
./venv/bin/python .../human_benchmark_suite.py number-memory ...
./venv/bin/python .../human_benchmark_suite.py visual-memory ...
./venv/bin/python .../human_benchmark_suite.py suite [--from-test sequence|aim|...] [--no-save-score]
```

**Tip:** Uses `SAFARI_VERTICAL_OFFSET = 139` and `START_CLIENT_CENTER`; smooth move via Quartz (linear interpolation). Artifacts under `operator/cre/project_understanding/artifacts/human_benchmark/`.

### 4.2 Mouse Accuracy

**File:** `operator/cre/project_understanding/tools/mouse_accuracy_suite.py`

**Run:**
```bash
./venv/bin/python cre/project_understanding/tools/mouse_accuracy_suite.py [--name mouse_accuracy_classic] [--move-duration 0.005] [--move-steps 1] [--settle-sleep 0.001] [--skip-evidence] [--content-inset 108] [--aim-offset-y -6] [--speed slow|normal|fast|epic] [--size tiny|small|medium|large]
```

**Tip:** Classic has DOM targets and **per-click aim correction** (cursor position vs intended → `running_aim_x/y`). Use `--skip-evidence` only for fast reruns when Safari is already front.

### 4.3 XBitLabs Path Follow

**File:** `operator/cre/project_understanding/tools/xbitlabs_path_follow.py`

**Run:**
```bash
./venv/bin/python cre/project_understanding/tools/xbitlabs_path_follow.py [--skip-evidence] [--path-duration 4] [--path-steps 200]
# or run_all_stages
```

**Tip:** Path is precomputed; cursor moves along it (no moving target). Use same viewport/bounds discipline as other harnesses.

---

## 5. GUI evidence and readiness

**File:** `operator/cre/project_understanding/tools/gui_evidence.py`

**Run:**
```bash
python3 .../gui_evidence.py [--app Safari] [--require-frontmost] [--capture] [--strict] [--json]
```

**Purpose:** Frontmost check, Quartz window list, optional capture, blocker classification (automation_denied, accessibility_denied, etc.). Used by mission_control evidence and by harnesses via `_ensure_safari_ready()`.

**Tip:** If evidence fails, fix focus/permissions before clicking; do not retry blindly.

---

## 6. CLI entry points (full list)

Every script you can run as a main program. From repo root or `operator/` as noted.

### 6.1 Agent and outer loop

| Script | Purpose |
|--------|---------|
| `operator/agent.py` | Universal agent: `--url`, `--goal` |
| `operator/cre/test_excalidraw_covt.py` | Main Excalidraw test (env-driven) |
| `python -m agent_infra.outer_loop --task CONCENTRIC_TRIANGLES_CLEAN [--max-cycles 3] [--test-script path]` | Dual-agent loop: run → diagnose → retry/escalate |

### 6.2 Mission control and evidence

| Script | Purpose |
|--------|---------|
| `operator/cre/project_understanding/tools/mission_control.py` | up | down | open | status | doctor | evidence (§3.1) |
| `operator/cre/project_understanding/tools/gui_evidence.py` | Evidence gate CLI |
| `operator/cre/project_understanding/tools/run_phoenix_control_room.py` | Bring up Phoenix + Control Room (with optional --open) |
| `operator/cre/project_understanding/tools/control_room.py` | Control Room server (with --open-browser) |
| `operator/cre/project_understanding/tools/run_structurizr_atlas.py` | Launch Structurizr atlas (Docker) |

### 6.3 Live harnesses

| Script | Purpose |
|--------|---------|
| `operator/cre/project_understanding/tools/human_benchmark_suite.py` | aim | sequence | chimp | typing | reactiontime | verbal-memory | number-memory | visual-memory | suite |
| `operator/cre/project_understanding/tools/mouse_accuracy_suite.py` | Classic (and main) game |
| `operator/cre/project_understanding/tools/xbitlabs_path_follow.py` | Path Follow (and run_all_stages) |

### 6.4 Run scripts (site-specific mastery / demos)

| Script | Purpose |
|--------|---------|
| `operator/cre/run_browserbotics_safari_phd.py` | BrowserBotics sandbox in Safari (full stack) |
| `operator/cre/run_browserbotics_autonomous.py` | Autonomous BrowserBotics with self-verifying loop |
| `operator/cre/run_browserbotics_safari_paste.py` | Safari paste demo |
| `operator/cre/run_live_visual_control_demo.py` | Live visual control demo |
| `operator/cre/run_live_cursor_window_demo.py` | Live Cursor window demo |
| `operator/cre/run_qa_practice_safari_probe.py` | QA Practice site probe |
| `operator/cre/run_qa_practice_mastery.py` | QA Practice mastery |
| `operator/cre/run_the_internet_mastery.py` | The Internet site mastery |
| `operator/cre/run_expandtesting_mastery.py` | ExpandTesting mastery |
| `operator/cre/run_uitestingplayground_site5_mastery.py` | UI Testing Playground site 5 |
| `operator/cre/run_automationexercise_site4_mastery.py` | Automation Exercise site 4 |
| `operator/cre/run_automationexercise_auth_benchmark.py` | Auth benchmark |
| `operator/cre/run_wikipedia_universal_autonomy_holdout.py` | Wikipedia universal autonomy holdout |
| `operator/cre/run_universal_autonomy_blind_holdout_batch.py` | Universal autonomy blind holdout batch |
| `operator/cre/run_preclick_smoke.py` | Preclick smoke |
| `operator/cre/ablation_harness.py` | Ablation study: `--reps 5`, `--conditions A,B,C,D`, `--dry-run` (conditions A–D = cache/trust/routing/allowlist) |
| `operator/ai_jury.py` | AI jury: `--calibration-file`, `--screenshot-dir`, `--output-dir parliament/jury_records`; `--judges claude` or `--judges gpt4o` for single judge. Requires ANTHROPIC_API_KEY + OPENAI_API_KEY for default two-judge pool. |

### 6.5 Build, audit, calibration

| Script | Purpose |
|--------|---------|
| `operator/cre/project_understanding/tools/build_verification_calibration.py` | `--build-candidates`, `--write-review-packets`, `--dataset`, `--runs-dir`, `--packets-dir`, `--limit` |
| `operator/cre/project_understanding/tools/build_architecture_conformance.py` | `--check` or regenerate conformance artifacts |
| `operator/cre/project_understanding/tools/build_understanding_artifacts.py` | Regenerate understanding corpus artifacts |
| `operator/cre/project_understanding/tools/build_dynamic_execution_architecture.py` | Dynamic execution architecture from traces |
| `operator/cre/project_understanding/tools/build_entrypoint_duplication_audit.py` | Entrypoint duplication audit |
| `operator/cre/project_understanding/tools/build_traceability_matrix.py` | Traceability matrix |
| `operator/cre/project_understanding/tools/markdown_to_basic_pdf.py` | Markdown → PDF (no pandoc) |
| `operator/cre/tools/build_cre_doc_registry.py` | CRE doc registry |
| `operator/cre/tools/build_cursor_mcp_landscape.py` | Cursor MCP landscape |
| `operator/cre/tools/build_cursor_official_updates_2026.py` | Cursor official updates |
| `operator/cre/tools/build_whole_project_truth_audit.py` | Whole-project truth audit |
| `operator/cre/tools/build_last_3_kleki_audit.py` | Last 3 Kleki audit |
| `operator/cre/tools/cursor_environment_snapshot.py` | Cursor environment fingerprint |
| `operator/cre/tools/log_environment_compliance.py` | Log environment-justification compliance |
| `operator/cre/tools/review_environment_compliance.py` | Review environment compliance log |
| `operator/cre/tools/verification_packet_walkthrough_reminder.py` | Verification packet walkthrough reminder |
| `operator/cre/build_reference_board_artifact.py` | Build reference board artifact set |

### 6.6 Live validation campaign

**File:** `operator/cre/project_understanding/tools/live_validation_campaign.py`

**Commands:** `start` | `resume` | `run` (single claim) | `run-family` | `status` | `report`

### 6.7 Host tool health

**File:** `operator/agent_infra/host_tool_health.py`

**Run:**
```bash
cd operator && ./venv/bin/python -m agent_infra.host_tool_health [--json] [--summary] [--has-url]
```

**Purpose:** Evaluate host-tool health (Python, Quartz, osascript, screencapture, Safari, etc.). Exit 0 only if all required classes are ready.

### 6.8 MCP servers (Cursor integration)

| Script | Purpose |
|--------|---------|
| `operator/cursor_integration/mcp/trace_server.py` | Concentric trace MCP server |
| `operator/cursor_integration/mcp/benchmark_server.py` | Concentric benchmark MCP server |
| `operator/cursor_integration/mcp/research_server.py` | Concentric research MCP server |
| `operator/cursor_integration/mcp/health_server.py` | Concentric health MCP server |

### 6.9 Other runnable scripts (drawing studies, canvas tests)

| Script | Purpose |
|--------|---------|
| `operator/cre/study_concentric_logic.py` | Study CONCENTRIC_TRIANGLES_CLEAN logic; use `CONCENTRIC_DRY_RUN=1` for no Quartz |
| `operator/cre/magma_open_canvas.py` | Open Magma canvas |
| `operator/cre/magma_draw_hand.py`, `magma_draw_realism_hand.py` | Magma hand-drawing runs |
| `operator/cre/magma_draw_bmw_e30.py`, `magma_bmw_e30_full_run.py` | Magma BMW E30 runs |
| `operator/cre/magma_draw_polo_bear_panther.py`, `magma_draw_tiger_rl_ironman.py` | Magma themed draws |
| `operator/cre/magma_traced_run.py` | Magma run with tracing |
| `operator/cre/jspaint_draw_polo_bear_panther.py`, `jspaint_draw_polo_bear_panther_enhanced.py` | JS Paint draws |
| `operator/cre/jspaint_draw_tiger_rl_ironman.py`, `_v2.py`, `_v3.py` | JS Paint tiger/ironman variants |
| `operator/cre/test_excalidraw_enterprise.py`, `test_excalidraw_autonomous.py` | Excalidraw enterprise/autonomous |
| `operator/cre/test_login_flow.py` | Login flow (LOGIN_DOMAIN, LOGIN_URL, HITL_APPROVE) |
| `operator/cre/test_canva_draw.py`, `test_canva_ai_image.py` | Canva draw / AI image |
| `operator/cre/test_kreska_statue.py`, `test_kleki_bmw.py` | Kreska/Kleki tests |
| `operator/cre/test_smooth_movement.py`, `test_dry_run_flow.py`, `test_coordinate_math.py` | Movement/dry-run/coords |
| `operator/cre/test_action_trust.py` | Action trust tracker |

### 6.10 Shell scripts (operator/cre/)

| Script | Purpose |
|--------|---------|
| `operator/cre/run_agent.sh` | Wrapper to run agent |
| `operator/cre/run_ultimate_tests.sh` | Run ultimate tests |
| `operator/cre/verify_kernel.sh` | Verify Codex kernel (Hammerspoon) |
| `operator/cre/showcase.sh` | Showcase run |
| `operator/cre/tools/install_verification_packet_walkthrough_daily_reminder.sh` | Install daily reminder for verification packet walkthrough |
| `operator/cre/tools/install_cursor_env_daily_check.sh` | Install Cursor env daily check |
| `operator/cre/tools/install_environment_compliance_daily_review.sh` | Install environment compliance daily review |

---

## 7. Action space (what the agent can do)

**File:** `operator/action_space.py`

Planner-visible actions (simplified). Full schema: `UnifiedActionSpace().to_planner_schema_list()` or `list_planner_names()`.

**Primitives:** `click`, `type`, `key`, `scroll`, `wait`  
**Perception:** `screenshot`, `assert_visual`, `a11y_snapshot`, `refresh_perception`  
**Drawing:** `draw_path`, `draw_segments`, `draw_shape`, `set_stroke_color`, `kleki_set_color`, `kleki_set_brush_size`, `kleki_set_opacity`, `kleki_set_scatter`, `kleki_set_stabilizer`, `kleki_select_tool`, `kleki_reset_render_state`  
**Navigation:** `go_to_url`, `go_back`, `browser_beforeunload_dialog`  
**Compound:** `clear_canvas`, `kleki_clear_canvas`, `draw_concentric_triangles`, `draw_eiffel_tower`, `draw_eiffel_landscape`; `login_flow` (planner_visible=False)  
**BMW:** `bmw_skeleton`, `bmw_details`, `bmw_shading`, `bmw_final`

**Conformance:** `test_action_space_conformance.py` asserts planner-visible actions have live handlers; `conformance_report(live_handler_keys)` returns missing/hidden lists.

---

## 8. Host tool health (tool classes and backends)

**File:** `operator/agent_infra/tool_health_catalog.json` + `operator/agent_infra/host_tool_health.py`

**Required for URL/browser tasks:**  
`runtime_python_selected`, `macos_ui_automation`, `native_event_backend`, `screen_capture`, `browser_target`

**Tool classes:**  
runtime_python_selected (operator_venv_python), macos_ui_automation (osascript_system_events), native_event_backend (pyobjc_native_stack), screen_capture (screencapture_cli), browser_target (safari_bundle), credential_backend (security_cli), site_capture_windowed (window_capture_stack), a11y_semantic_backend (macapptree_backend | pyax_backend), semantic_skill_embeddings (sentence_transformers_backend), legacy_openai_path (legacy_openai_backend).

**Tip:** Run `host_tool_health --has-url` before a live browser task to ensure all required backends are satisfied.

---

## 9. Agent infrastructure (imports and usage)

**Package:** `operator/agent_infra/` (import as `from agent_infra import ...`)

| Export | Purpose |
|--------|---------|
| TraceWriter, TraceStep | Per-run trace JSONL and step schema |
| DiagnosticReader | Read traces with progressive disclosure (3 levels) |
| HealingOrchestrator, FailureClassification | Classify failures, recommend actions |
| SkillLibrary, SkillRecord, SkillMaturity, SemanticSkillIndex | Verified successes, maturity gating, semantic retrieval |
| OuterLoop, OuterLoopResult, ReflectionJournal, RulesStore, TASK_ENV_MAP | Dual-agent loop, reflection journal, rules |
| ActionTrustTracker | Adaptive verification skip (Beta-Binomial) |
| Summarizer | Trajectory summarizer (500-token budget) |
| SiteKnowledge, ExplorationLoop, ToolAffordance, InteractionRule, ButtonMapEntry | Site affordances and exploration |
| HostToolHealth | Host-tool health evaluation |
| VisualMonitor, Snapshot, ComparisonResult | Background screenshot monitor, compare to reference |
| ResearchAgent, ResearchBrief | 4-phase research pipeline (subject, method, tools, equation) |
| VerificationGate, VerificationGateResult, Constraint | Post-execution verification (constraint decomposition, judge) |
| DecisionDependenceAnalyzer, DDGNode, DDGEdge, AnomalyReport | Causal trace analysis (MindGuard-style) |
| BenchmarkEvaluator, BenchmarkResult, TaskClaim | Claims-based benchmark evaluation (MCP-Atlas-style) |

**Tip:** Use `DiagnosticReader(run_dir).full_diagnostic()` to read results; use `HealingOrchestrator(runs_dir).get_diagnostic_for_code_agent(run_dir)` for failure classification; use `SkillLibrary(cre_dir).ingest_from_trace(run_dir)` to ingest a successful run.

**Perception stack (operator/, not in agent_infra):** SoM (visual_engine.py), A11y (a11y_engine.py), Unified Element Map (element_map.py), Parallel Scout Dispatch (4× Gemini Flash). web_primitives.py: click_element, type_into, scroll_to, etc. inference_router.py: Flash/Pro/Local routing.

**DDG (trace analysis):** `HealingOrchestrator(...).analyze_run_with_ddg(run_dir)`; anomaly types: orphaned_action, state_discontinuity, repeated_failure_chain, thought_action_divergence.

**BenchmarkEvaluator:** `register_claims(task_id, [TaskClaim(...)]), register_optimal_steps(task_id, n), evaluate_run(run_dir)`; metrics: claims score, discovery precision, error recovery rate, plan optimality, NRP.

**Semantic skill retrieval:** `SkillLibrary(cre_dir).retrieve_by_similarity("draw nested triangles")` — dense (sentence-transformers) or TF-IDF fallback.

---

## 10. Environment variables and flags

| Variable | Where / effect |
|----------|----------------|
| `GEMINI_API_KEY` or `OPENAI_API_KEY` | Agent/VLM; required for enterprise mode |
| `CONCENTRIC_TRIANGLES_CLEAN` | Enables canonical clean-triangles test path and pass logging |
| `CONCENTRIC_TRIANGLES` | Alternate Excalidraw task |
| `AGENT_GOAL` | Override goal in test_excalidraw_covt |
| `EXECUTION_LOG_PATH` | Append execution log lines (agent, action_handlers, recovery) |
| `PASS_LOG_PATH` | Pass-log path for CONCENTRIC_TRIANGLES_CLEAN |
| `CONCENTRIC_DRY_RUN` | 1 = no Quartz events (study_concentric_logic) |
| `DISABLE_COORD_CACHE` | Disable coordinate cache in test |
| `DISABLE_TRUST_TRACKER` | Disable action trust tracker |
| `DISABLE_ADAPTIVE_ROUTING` | Disable adaptive inference routing |
| `DISABLE_ACTION_ALLOWLIST` | Disable action allowlist in test |
| `DISABLE_VISUAL_MONITOR` | Disable visual monitor in agent |
| `CONCENTRIC_VISUAL_MONITOR_INTERVAL_S` | Visual monitor interval (default 5) |
| `CONCENTRIC_VISUAL_MONITOR_BUFFER_SIZE` | Ring buffer size (default 40) |
| `DYNAMIC_PLAN` or custom goal | Use dynamic plan in test |
| `ABLATION_CONDITION` | Ablation harness |
| `GRADED_ASSERTIONS` | Use graded assertions in recovery |
| `CONCENTRIC_OTEL_ENABLE` | Enable OpenTelemetry (e.g. Phoenix) |
| `CONCENTRIC_LIVE_VALIDATION_VENV` | Use venv in live validation campaign |
| `LOGIN_DOMAIN`, `LOGIN_URL`, `HITL_APPROVE` | Login flow test |
| `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` | AI jury two-judge pool (or use `--judges claude` / `--judges gpt4o` for single judge) |

---

## 11. Tips and tricks (curated)

- **Safari focus:** Hide Cursor (Cmd+H), then activate Safari. Evidence gate must pass before clicks.
- **Coordinates:** Always convert client/viewport to screen-global (bounds + inset or viewport origin). Do not use screenshot pixels as click coords.
- **Evidence before action:** For any visible Safari task, run evidence (or `_ensure_safari_ready()`) and do not proceed until `ready_for_visible_task` is true.
- **Aim correction (Mouse Accuracy):** Use `position_errors` and `running_aim_x/y`; clamp to AIM_OFFSET_*; adjust from clear rate when many/few targets cleared.
- **Calibration offsets:** Human Benchmark uses `SAFARI_VERTICAL_OFFSET = 139` and `START_CLIENT_CENTER`; Mouse Accuracy and XBitLabs use content inset (e.g. 90–139) and optional `--content-inset`, `--aim-offset-y`.
- **Dry run:** Set `CONCENTRIC_DRY_RUN=1` to observe logic without posting Quartz events (study_concentric_logic).
- **Trace monitoring:** Read `operator/cre/runs/<run_id>/trace.jsonl` as it is written; when `manifest.json` appears, run is complete. Do not use sleep+grep to monitor.
- **Conformance:** Run `test_action_space_conformance.py` to ensure planner-visible actions have live handlers.
- **Verification calibration:** Use `build_verification_calibration.py --build-candidates`, `--write-review-packets`, then human review; see SECTION_8_VERIFICATION_GATE_CALIBRATION.md.
- **Motion profile (harnesses):** `move_duration`, `move_steps`, `settle_sleep` tune smooth move and post-click wait (Human Benchmark, Mouse Accuracy, XBitLabs).
- **Canvas-only mouse accuracy:** `mouseaccuracy.com/game` is canvas-based with no DOM target list; harness may wait for results or future vision loop (CURSOR_TESTS_AND_MOVING_OBJECTS_RESEARCH.md).
- **ULTIMATE_TESTS vision loop (design):** Region capture → detect_target (placeholder) → smooth_move_and_click; ~10 FPS; CodexClient Bezier motion (not implemented in repo).

---

## 12. Build and calibration tools (short ref)

- **Verification calibration:** `build_verification_calibration.py --build-candidates [--write-review-packets]` → candidates in `artifacts/verification_calibration_candidates.jsonl`; blind packets in `artifacts/verification_review_packets/blind/`, adjudication in `.../adjudication/`. After human labels: `--dataset path/to/candidates.jsonl` → `artifacts/verification_calibration_report.json` (agreement, kappa, confusion matrix). Review states: unlabeled, single_rater, multi_rater_consensus, pending_adjudication, adjudicated. Test: `test_verification_calibration.py`.
- **AI jury:** `operator/ai_jury.py`. From `operator/`: `./venv/bin/python ai_jury.py --calibration-file cre/project_understanding/artifacts/verification_calibration_candidates.jsonl --screenshot-dir cre/runs --output-dir parliament/jury_records`. Env: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` (or single judge: `--judges claude` | `--judges gpt4o`). Deps: `pip install anthropic openai`. First run with few packets → `insufficient_data` for Kappa (expected); use verdicts to bootstrap trust. See SECTION_8 §5.1.
- **Parliament:** `operator/parliament.py` — knowledge health, staleness, pre/post-mission review, census sweep. Ready to drop in.
- **Jury interface (human fallback):** `jury.html` — seed calibration with your own judgments. Place in repo per project layout.
- **Host capabilities:** `.cursor/rules/host-capabilities.mdc` — canonical brief so every model knows what it can do.
- **Architecture conformance:** `build_architecture_conformance.py [--check]` or `--regen-graph --write-artifacts` (from project_understanding/tools). Writes `artifacts/architecture_conformance.json`, `.csv`.
- **Understanding artifacts:** `build_understanding_artifacts.py` regenerates repo_inventory.json, file_catalog.csv, import_graph.json, subsystem_dependency_report.json, architecture_overview.mmd, entrypoint_duplication_audit, traceability_matrix, dynamic_execution_architecture, folder_records, artifact_flow_matrix, inventory_summary, bibliography_seed. Conformance is separate (build_architecture_conformance.py).
- **PDF from Markdown:** `markdown_to_basic_pdf.py` (no pandoc)

---

## 13. Tests (pytest and manual)

**Run all cre tests:**
```bash
cd operator && ./venv/bin/python -m pytest cre/test_*.py -v --tb=short
```

**Notable tests:**  
`test_excalidraw_covt.py` (main GUI), `test_action_space_conformance.py` (conformance court), `test_trace_writer.py`, `test_diagnostic_reader.py`, `test_healing_orchestrator.py`, `test_outer_loop.py`, `test_phase3_equation_solver.py`, `test_drag_drop.py` (CodexClient drag), `test_verification_calibration.py`, plus many other test_*.py under cre/.

---

## 14. MCP (Cursor)

Repo references **concentric-health**, **concentric-trace**, **cursor-ide-browser** in rules. MCP tool descriptors live under `.cursor/projects/.../mcps/<server>/tools/`. Use smallest active MCP set; prefer repo-local and read-only MCPs for environment and forensics. See `.cursor/rules/mcp-governance.mdc`, `context7-docs.mdc`.

---

## 15. Codex / Hammerspoon kernel

**File:** `operator/cre/codex_kernel.lua` (Hammerspoon); **client:** `operator/codex_client.py`

**When:** Optional backend for click, drag, smooth move (Bezier), draw_path. Not used by main agent_core path (which uses Quartz directly).

**CodexClient:** `ping()`, `click(x,y)`, `keystroke(key)`, `get_mouse_position()`, `get_screen_info()`, `convert_pixel_to_logical()`, `move_mouse(x,y)`, `smooth_move_and_click(...)`, `drag(start_x, start_y, end_x, end_y)`, `screenshot(...)`, `draw_path(path)`. Requires kernel on port 9999.

**Tip:** Human Benchmark, Mouse Accuracy, XBitLabs use Quartz + cliclick in harnesses, not CodexClient. Use CodexClient for ultimate-test-style loops or test_drag_drop.

---

## 16. External binaries and deps

- **osascript** — Safari/System Events automation; required (macos_ui_automation).
- **screencapture** — Screenshots; required (screen_capture).
- **cliclick** — Used by some harnesses for current mouse position (`p`) and optionally clicks; not required by agent_core.
- **Python venv** — `operator/venv`; use `./venv/bin/python` for all runs.
- **PyObjC** — AppKit, Quartz (native_event_backend); required.
- **Optional:** macapptree or pyax (a11y), sentence_transformers (semantic skills), Hammerspoon (Codex kernel).

---

## 17. Where to read more (section 17 deep ref)

Use these when you need narrative, method, or next-move guidance. Paths relative to repo root or `operator/cre/project_understanding/` as stated.

| Doc | Path | Use when you need |
|-----|------|-------------------|
| **AGENTS.md** | repo root | Infrastructure table, running tests, skill library, outer loop, security, Research Agent, VerificationGate, DDG, BenchmarkEvaluator, semantic retrieval, perception stack, architecture-critical files, two protocols (Facts Before Decision, Research-First Implementation). |
| **README (corpus)** | `operator/cre/project_understanding/README.md` | Corpus reading order (1–32), generated artifacts list, "How to use this corpus" (which doc for runtime, architecture, traceability, conformance, calibration, control room, mission control, live validation, BrowserBotics PhD, evidence gate). |
| **LIVE_SAFARI_STACK_CHECKLIST.md** | same dir | Mandatory steps for visible Safari tasks; tools table; reference harnesses. |
| **MISSION_CONTROL_STACK_AND_PROFILES.md** | same dir | Profiles (live, debug, architecture, full), what each tool does (Control Room, Phoenix, Structurizr, D2, Sourcegraph), commands quick reference. |
| **QUICKSTART_LIVE_TASKS.md** | same dir | Minimal sequence: up live → evidence Safari → run harness. |
| **TOOLS_AND_PERMISSIONS_RESEARCH.md** | same dir | File-by-file tools (agent_core, window_capture, agent, action_handlers, a11y, host_tool_health, gui_evidence), permission matrix, chain from "draw in Safari" to hardware. |
| **CURSOR_TESTS_AND_MOVING_OBJECTS_RESEARCH.md** | same dir | Aim trainer, reaction time, Mouse Accuracy classic (aim correction), Path Follow, ULTIMATE_TESTS vision loop, drag-and-drop, motion profile, coordinate system. |
| **SECTION_8_VERIFICATION_GATE_CALIBRATION.md** | same dir | Purpose, research basis, candidate export, blind/adjudication packets, agreement scoring, workflow (build-candidates → human label → --dataset score), review states, local test test_verification_calibration.py. |
| **MASTER_DIAGRAM_CHAPTER.md** | same dir | System overview, ministry chain, law-to-ministry matrix, feedback-loop map, legitimacy-loop map. |
| **SECTION_9_MASTER_SYSTEMS_DIAGRAM.md** | same dir | End-to-end inputs, ministries, laws, outputs, feedback, legitimacy loop. |
| **BROWSERBOTICS_PHD_SITE_AND_ROBOT_BUILDER.md** | same dir | URLs, layout, API, supported robots, PhD builder checklist; use with `run_browserbotics_safari_phd.py`. |
| **NEXT_MOVES_PHD.md**, **NEXT_BEST_MOVE_PHD.md**, **POST_CONFORMANCE_NEXT_MOVE_PHD.md** | same dir / cre | Done vs next; strongest next move; post-conformance next move. |
| **PHD_DECISION_PRACTICE.md** | `operator/cre/` | Facts-before-decision, research-first implementation (Triage → Analyze → Strategize → Execute → Reflect), Rule 12/13. |
| **RUNTIME_FLOWS.md** | project_understanding | Canonical runtime path. |
| **EVIDENCE_AND_RUN_ARTIFACTS.md** | project_understanding | Old screenshots, run directories. |
| **BIBLIOGRAPHY.md** | project_understanding | Related work, thesis refs. |

---

## 18. macOS permissions (what the OS must allow)

The process that runs the agent (Terminal/Cursor) must have these in **System Settings → Privacy & Security**. The repo does not grant them; it uses APIs that macOS protects. **gui_evidence.py** surfaces denial (automation_denied, accessibility_denied); fix in TCC, not in code.

| Capability | Permission / requirement | Where used |
|------------|---------------------------|------------|
| Post mouse/key events (click, drag, keystroke) | **Input Monitoring** / **Accessibility** (control the computer) | agent_core.py — CGEventPost(Quartz.kCGHIDEventTap, …) |
| Bring Safari to front | NSWorkspace + optional **Automation** (osascript fallback) | agent_core.enforce_app_focus |
| "Tell application Safari" / "Tell application System Events" | **Automation** (Safari, System Events) | action_handlers._handle_go_to_url, a11y_engine AppleScript, gui_evidence |
| Screenshot (screencapture, CGWindowListCopyWindowInfo) | **Screen Recording** (and sometimes Accessibility) | window_capture.capture_front_window, action_handlers, agent_core |
| Read accessibility tree (AXUIElement / System Events UI) | **Accessibility** (+ Automation for System Events) | a11y_engine.py, gui_evidence probes |

Ref: TOOLS_AND_PERMISSIONS_RESEARCH.md §3, §5.

---

## 19. Security (operator/security and agent path)

- **InputSanitizer** (`operator/security/sanitizer.py`): Prompt injection, credential phishing, hidden instructions; MCP tool poisoning (8 patterns, OWASP MCP Top 10). `sanitize_tool_description()`, `sanitize_tool_response()`, `verify_schema_integrity()` (rug-pull, CVE-2025-54136).
- **CredentialVault** (`operator/security/credential_vault.py`): macOS Keychain; credentials not in logs or VLM prompts.
- **HITLGuard**: Pauses for human approval on password fields, form submissions, unknown domains.

Ref: AGENTS.md § Security.

---

## 20. Control room, Phoenix, Structurizr, and generated artifacts

- **Control Room:** `python3 operator/cre/project_understanding/tools/control_room.py --open-browser`. Live browser over architecture, runtime, conformance, calibration; ministry/viewpoint selection; SSE push; D2/SVG under `artifacts/control_room_generated/d2/` if d2 installed; Sourcegraph panel for code drilldown.
- **Phoenix + Control Room:** `python3 operator/cre/project_understanding/tools/run_phoenix_control_room.py [--open]`. Phoenix on `http://127.0.0.1:6006/`; first run bootstraps `operator/cre/local_ops/phoenix_sidecar/venv`.
- **Structurizr atlas:** `python3 operator/cre/project_understanding/tools/run_structurizr_atlas.py [--open-browser]`. Atlas under `artifacts/control_room_generated/structurizr/` (workspace.dsl, docs, ADRs, JSON, static export).
- **Mission control state:** `artifacts/control_room_generated/mission_control/state.json` (profile membership, health, logs, PIDs).
- **Live validation artifacts:** Campaign registry in `live_validation_registry.py` (CLAIMS); run artifacts and reports under `artifacts/live_validation/`. Commands: `live_validation_campaign.py start | resume | run <claim-id> | run-family | status | report`.

Ref: project_understanding/README.md "How To Use This Corpus".

---

This master is the single exhaustive reference for tools, entry points, and tips in the project. Add new sections here when you add new tools or conventions.
