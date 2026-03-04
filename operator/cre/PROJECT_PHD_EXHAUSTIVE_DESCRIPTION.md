# Concentric Study: Exhaustive PhD-Level Project Description

**Document type:** Definitive project description with research framing, tool inventory, and academic references  
**Audience:** Researchers, reviewers, and maintainers who need a single source of truth for what the project is, what each component does, and why it exists.

**Validation tier note:** This document mixes (1) directly implemented and tested
mechanisms, (2) analogical research support, and (3) intended architecture. For
live repo-health claims, check the current test surface and architecture
conformance tests rather than treating all present-tense prose as universally
enforced.

---

# Part I — What This Project Is

## 1.1 One-sentence definition

**Concentric Study** is a **trace-centric, self-healing, dual-agent GUI automation framework** for macOS that drives browser-based drawing applications (primarily Excalidraw) via vision–language models (VLMs) and native Quartz HID control, producing structured execution traces for post-hoc diagnosis, automated recovery, skill learning, and escalation to a code-repair agent when the execution agent cannot recover on its own.

## 1.2 Research framing

The project sits at the intersection of several active research threads:

- **GUI agents and robustness.** GUI automation agents are brittle: pop-ups, tool-state drift, resolution changes, and distribution shift cause failures that static benchmarks miss. Benchmarks like **GUI-Robust** (arXiv:2506.14477, 2025) and **D-GARA** (arXiv:2511.16590) show substantial performance degradation under real-world anomalies; the project explicitly targets **observability** and **recovery** so that failures are visible and, when possible, corrected without human intervention.

- **Self-healing and reflection.** The execution loop implements the **Reflexion** pattern (Shinn et al., NeurIPS 2023, arXiv:2303.11366): after failures, a VLM diagnoses the cause and the system attempts recovery (e.g. dismiss dialogs), then verifies postconditions. Episodic memory (**ReflectionJournal**) and rule injection (**ExpeL**, Zhao et al., AAAI 2024, arXiv:2308.10144) prevent blind retries. This aligns with **VIGIL** (Cruz, 2025, arXiv:2512.07094)—stage-gated supervision and structured logs—and **SHML** (Rauba et al., NeurIPS 2024, arXiv:2411.00186): **Monitor → Diagnose → Adapt → Test** as the loop that closes the gap between an execution agent and a repair agent.

- **Trace-centric observability.** Every traced run produces a **run directory** with `trace.jsonl` (per-step JSON lines) and `manifest.json` (outcome, failure step, timing). There is no “black box”: the system is built for **program-comprehension-style** analysis (entry-point identification, call-graph and data-flow tracing, PDG-style dependence reasoning; Ferrante et al., TOPLAS 1987; Cornelissen et al., TSE 2009). The **DiagnosticReader** supports progressive disclosure (Level 1 summary → Level 2 failure window → Level 3 full detail); the **HealingOrchestrator** classifies failures and recommends actions; the **Decision Dependence Graph** (MindGuard, arXiv:2508.20412) adds causal-chain analysis for root-cause attribution.

- **Skill learning and reuse.** Successful runs are ingested into a **SkillLibrary** with **maturity gating** (candidate → proven → master), following the skill-library pattern from **VOYAGER** (Wang et al., NeurIPS 2023) and **ASG-SI** (arXiv:2512.23760). Master-tier skills store **resolved_coords**, enabling coordinate-cache replay that skips expensive visual grounding and VLM calls for known actions. **Semantic retrieval** (RAG-MCP, arXiv:2505.03275; Sentence-BERT, EMNLP 2019) allows retrieval by task meaning, not just lexical match.

- **Dual-agent orchestration.** The **OuterLoop** does not execute GUI actions itself. It invokes the test script (e.g. `test_excalidraw_covt.py`) as a subprocess, reads the resulting trace and manifest, and then: on **success**, ingests the run into the skill library and records a reflection; on **failure**, classifies via HealingOrchestrator (optionally with DDG), then **retries** with adjusted env, **escalates** to the code agent by writing **ESCALATION.md** (Level 1/2/3 diagnostic + reflection context), or **aborts**. This is the “dual-agent” design: one agent runs the GUI task, the other (human or code agent) repairs the system when the loop cannot recover.

- **Cost and verification efficiency.** **ActionTrustTracker** (action_trust.py) uses a Beta-Binomial posterior per action key and skips visual verification only when the lower credible bound exceeds a configured reliability threshold at the configured confidence level; any failure resets the record. The **Summarizer** compresses execution history into a fixed token budget (default 500) for VLM context injection, following trajectory folding (OpAgent, arXiv:2602.13559; MemoBrain, arXiv:2601.08079; Context-Folding, arXiv:2510.11967). **InferenceRouter** supports Flash/Pro/local model selection for difficulty-aware routing (ICoT, arXiv:2512.14048).

- **Security and human-in-the-loop.** **InputSanitizer** defends against prompt injection and MCP-specific threats (OWASP MCP Top 10; MSB, arXiv:2510.15994, ICLR 2026). **CredentialVault** uses macOS Keychain; **HITLGuard** requires human approval for sensitive actions (passwords, form submissions, unknown domains). The project explicitly avoids putting credentials in logs or VLM prompts.

## 1.3 What it is *not*

- It is **not** an Excalidraw fork or extension: there is no Excalidraw front-end code in the repo. The system **automates** Excalidraw (and other sites) in Safari via OS-level control.
- It is **not** a generic “AI assistant”: it is a **GUI automation agent** with a defined loop (plan → execute → trace → diagnose → recover or escalate) and a clear separation between execution and repair.
- It is **not** stateless: traces, skill library, reflection journal, rules, and trust tracker are **persistent** and drive future runs.

---

# Part II — The Whole Point of the Project

## 2.1 Primary goal

**Build, test, and evolve a reliable, self-healing AI agent** that can perform complex drawing/diagramming tasks (and, by design, generalize to other web tasks) via natural-language-like goals and model-based execution, while:

1. **Producing rich execution traces** so every run is inspectable and classifiable.
2. **Recovering automatically** from common UI failures (dialogs, overlays, tool state) using VLM-based diagnosis and a fixed set of recovery actions (escape, enter, click_away).
3. **Learning from success** by ingesting successful traces into a skill library with maturity gating and optional coordinate caching.
4. **Learning from failure** by recording reflections and rules and escalating to a code agent when recovery is exhausted, with a structured escalation document (ESCALATION.md) that a human or code agent can act on.
5. **Controlling cost and latency** via trust-based verification skipping, trajectory summarization, and inference routing.

## 2.2 Secondary goals

- **Generalize beyond a single site:** Excalidraw is the primary target; Kleki, Canva, login flows, and generic URLs (via `agent.py`) are supported so the architecture is not tied to one app.
- **Support research and benchmarking:** Trace format, manifest, and run directory are designed for integration with benchmarks (e.g. GUI-Robust-style evaluation) and with research components (DDG, BenchmarkEvaluator, VerificationGate, ResearchAgent).
- **Preserve security and human oversight:** Sanitization, credential vault, and HITL ensure the agent can be used in sensitive or production-like settings without exposing secrets or taking destructive actions without approval.

## 2.3 Success criteria (implicit)

- **Traced runs complete** with a clear outcome (success/failure) and a manifest.
- **Failures are classified** and either recovered in-loop or escalated with actionable context.
- **Skills accumulate** and mature so that repeated tasks can reuse proven/master skills and, when applicable, resolved coordinates.
- **Outer loop** can run unattended for multiple cycles and either succeed or escalate with a readable ESCALATION.md.

---

# Part III — Tools and Components: Exhaustive Inventory

The following tables and descriptions list **every major tool** (module or subsystem) and **what it is in charge of**. Dependencies are unidirectional where stated; no component is “miscellaneous”—each has a defined responsibility.

## 3.1 Agent infrastructure (`operator/agent_infra/`)

| Module | In charge of | Key APIs / behavior | Research basis |
|--------|----------------|----------------------|----------------|
| **trace_writer.py** | Creating the run directory, appending one JSON line per step to `trace.jsonl`, writing `manifest.json` on finalize. No imports from other agent_infra modules. | `TraceWriter(output_dir, task_id, ...)`, `begin_step(i)`, `end_step(step)`, `record_failure(...)`, `finalize(outcome)` | Phase 1 tracing; foundation for all consumers |
| **diagnostic_reader.py** | Reading a run directory: loading manifest and trace, exposing Level 1 (summary), Level 2 (failure window), Level 3 (full diagnostic). No agent_infra imports. | `DiagnosticReader(run_dir)`, `level1_summary()`, `level2_failure_window()`, `full_diagnostic()` | Progressive disclosure; program-comprehension baselines |
| **healing_orchestrator.py** | Classifying failures from manifest (and optionally trace/DDG); recommending action: retry, adjust_parameters, escalate_to_code_agent, abort. Consumes DiagnosticReader. | `analyze_run(run_dir)`, `analyze_run_with_ddg(run_dir)` → `FailureClassification` | ConceptAgent, MindGuard, AgentArmor, TraceCoder, APR survey (arXiv:2506.23749) |
| **skill_library.py** | Ingesting successful runs from trace/manifest; storing skills with maturity (candidate/proven/master); persisting to `skill_library.json`; retrieving by task_id or by semantic similarity. No agent_infra imports. | `ingest_from_trace(run_dir)`, `retrieve_proven(task_id)`, `retrieve_by_similarity(query)`, `get_summary()` | VOYAGER, ASG-SI, RAG-MCP, security-inspired provenance discipline, ViReSkill |
| **outer_loop.py** | Orchestrating the dual-agent loop: invoke test subprocess, find latest run dir, read manifest; on success ingest and return; on failure classify, then retry with env, escalate (write ESCALATION.md + reflection), or abort. Hosts ReflectionJournal and RulesStore. | `OuterLoop(task_id, test_script, runs_dir).run()` → `OuterLoopResult`; `ReflectionJournal`, `RulesStore` | SHML, VIGIL, TraceCoder, Reflexion, COCO, RepairAgent, AOrchestra |
| **action_trust.py** | Tracking per-action success/failure evidence and deciding whether to run visual verification (`should_verify(key)`) via a Beta-Binomial posterior lower bound; persisting to `action_trust.json`. Standalone, no agent_infra imports. | `ActionTrustTracker(persist_path)`, `should_verify(key)`, `record_success(key)`, `record_failure(key)` | Beta-posterior style reliability; FrugalGPT-style cost control |
| **summarizer.py** | Incrementally ingesting trace steps and maintaining a compressed “context so far” under a token budget (default 500) for injection into VLM prompts (e.g. diagnosis). | `Summarizer(token_budget=500)`, `ingest_step(step_dict)`, `get_context()` | OpAgent, MemoBrain, Context-Folding |
| **recovery.py** | Executing a single action with recovery: pre-action sanity check (`_ensure_canvas_clear`, skippable via trust), run handler, on failure call VLM diagnosis (`_diagnose_failure`), run recovery actions (escape/enter/click_center), verify postcondition. Writes trace steps via ctx.trace_writer. | `_execute_action_with_recovery(ctx, action_item, step_index)`; `_diagnose_failure`, `_execute_recovery`, `_ensure_canvas_clear` | Reflexion, STRIPS verification; VIGIL, ExpeL (rules injection) |
| **action_handlers.py** | Implementing one handler per action type (keystroke, set_stroke_color, draw_concentric_triangles, clear_canvas, etc.). Uses ctx.agent (MacOSAgentCore), ctx.vision_engine (SoM), ctx.coord_cache, ctx.trust_tracker. Injected with trace/exec_log/cache/center/phash. | `ACTION_HANDLERS[action_type](ctx, args)`; `inject_dependencies(...)` | Excalidraw/Kleki-specific UI logic; SoM and coord cache integration |
| **startup.py** | Initializing the agent (_init_agent: MacOSAgentCore or legacy VLMCoordinator), launching Safari and capturing initial UI (_launch_safari_and_capture). Injected with exec_log, pass_log, get_screenshot_center. | `_init_agent()`, `_launch_safari_and_capture(...)` | Single place for browser + agent bootstrap |
| **site_knowledge.py** | Representing site-specific tool affordances, interaction rules, and button maps (SiteKnowledge, ExplorationLoop, ToolAffordance, InteractionRule, ButtonMapEntry). Used for plan generation and exploration. | SiteKnowledge, ExplorationLoop, ToolAffordance, etc. | GUI-explorer transition-aware knowledge; SeeAct documentation grounding |
| **decision_graph.py** | Building a Decision Dependence Graph from trace steps (state-flow dependencies); detecting anomalies (orphaned actions, state discontinuities, repeated failure chains); extracting causal chain for a failure step. Consumed by HealingOrchestrator.analyze_run_with_ddg. | `DecisionDependenceAnalyzer()`, `build_from_trace(steps)`, `get_failure_context(step_index)`, `detect_anomalies()` | MindGuard, AgentArmor, IPIGuard, Ferrante et al. PDG |
| **benchmark_evaluator.py** | Evaluating a run against registered task claims (MCP-Atlas-style), computing claims score, discovery precision, error recovery rate, plan optimality, NRP. | `BenchmarkEvaluator()`, `register_claims(task_id, claims)`, `evaluate_run(run_dir)` → `BenchmarkResult` | MCP-Atlas, MCP-Bench, MCPToolBench++, MSB |
| **research_agent.py** | Running a pre-execution research pipeline in the universal-agent path: study subject (reference images), study method (tutorials), study tools (platform inventory), solve equation (map method to tools → plan). Outputs ResearchBrief. | `ResearchAgent(output_dir).research(task, site_url)` → `ResearchBrief` | AppAgent Phase 1, SeeAct, GUI-explorer, PG-Agent |
| **visual_monitor.py** | Background screenshot capture at fixed intervals; ring buffer; pixel-diff comparison against a reference image (no VLM). Integrated in the universal-agent path and selected demos/tests. | `VisualMonitor(interval_seconds, buffer_size, output_dir)`, `start()`, `compare(reference_path)`, `timeline(last_n)` | Peekaboo MCP, ScreenAgent, MIRA |
| **verification_gate.py** | Post-execution verification layer used in the universal-agent path and selected demos/tests: decompose task into constraints, capture screenshot, judge each constraint (VLM or heuristic), return pass/fail and deficiencies. | `VerificationGate(task_description, output_dir)`, `verify()` → `VerificationResult`, `verify_loop(fix_fn, max_iterations)` | CRAFT, GUI-Shepherd, VISCO, Maestro, VisionDirector |

## 3.2 Operator-layer modules (`operator/`)

| Module | In charge of | Key APIs / behavior |
|--------|----------------|----------------------|
| **agent_core.py** | macOS interaction: focus (NSWorkspace), screenshots (screencapture / Gemini File API), pixel→Quartz coordinate conversion (NSScreen), global click/keystroke/draw (CGEvent), VLM-based visual assertions. | `MacOSAgentCore(router=...)`, `enforce_app_focus(app_name)`, `execute_global_click(pixel_x, pixel_y)`, `execute_keystroke(key)`, `execute_draw_path_segments(center, vertices)`, `assert_visual_state(image_path, question)` |
| **visual_engine.py** | Set-of-Mark (SoM) visual grounding: grid overlay, VLM-based element identification, coordinate resolution for clicks. | VisualGroundingEngine(grid_size, output_dir); used by action handlers when coord cache misses |
| **inference_router.py** | Choosing which model (Flash/Pro/local) to use for a given task type; persisting routing state; optional EMA-based adaptation. | InferenceRouter(persist_path), route(task_type, ...), record_outcome(...) |
| **a11y_engine.py** | Extracting the macOS accessibility tree (macapptree/pyax/AppleScript backends) for semantic labels. | Used when building UnifiedElementMap |
| **element_map.py** | Fusing SoM visual zones with a11y tree data into a unified element map for hybrid perception. | UnifiedElementMap, WebPrimitives integration |
| **web_primitives.py** | Site-agnostic primitives: click_element, type_into, scroll_to, etc., for navigation beyond a single canvas. | Used by login flow and generic navigation |
| **security/sanitizer.py** | Detecting prompt injection, credential phishing, hidden instructions; MCP tool description/response sanitization; schema integrity checks. | InputSanitizer, MCP-specific patterns (OWASP MCP Top 10, MSB) |
| **security/credential_vault.py** | Storing/retrieving credentials from macOS Keychain; HITLGuard for human approval on sensitive actions. | CredentialVault, HITLGuard |

## 3.3 Entry points and test layer (`operator/cre/` and `operator/`)

| Entry point | In charge of |
|-------------|----------------|
| **test_excalidraw_covt.py** | The main traced GUI test: _init_logging (EXECUTION_LOG_PATH, PASS_LOG_PATH), _init_agent, _init_trace_writer, _launch_safari_and_capture, generate_action_plan / generate_dynamic_plan, _load_coord_cache, build _Ctx, _execute_plan (which calls _execute_action_with_recovery for each action), _finalize_run. Produces cre/runs/<run_id>/ with trace.jsonl, manifest.json, execution_log.txt. |
| **test_kleki_bmw.py** | Secondary traced integration test for Kleki; same pattern (TraceWriter, recovery, execution log). |
| **agent.py** | Standalone universal orchestrator: URL + goal; can load master skill and replay action plan; uses TraceWriter when configured. Generalizes beyond Excalidraw. |
| **test_login_flow.py** | Login flow E2E test with TraceWriter (run dir, trace, manifest) and CredentialVault/HITLGuard; does not set EXECUTION_LOG_PATH. |
| **Outer loop CLI** | `python -m agent_infra.outer_loop --task CONCENTRIC_TRIANGLES_CLEAN`: runs the dual-agent loop (subprocess test → read run → ingest or diagnose → retry/escalate/abort). |

## 3.4 Data artifacts (what each tool reads or writes)

| Artifact | Written by | Read by |
|----------|------------|---------|
| **cre/runs/<run_id>/trace.jsonl** | TraceWriter (per step from recovery/plan execution) | DiagnosticReader, HealingOrchestrator, SkillLibrary, DecisionDependenceAnalyzer, BenchmarkEvaluator |
| **cre/runs/<run_id>/manifest.json** | TraceWriter.finalize() | DiagnosticReader, HealingOrchestrator, OuterLoop (outcome), SkillLibrary |
| **cre/runs/<run_id>/ESCALATION.md** | OuterLoop (on escalate) | Code agent / human |
| **cre/runs/reflection_journal.jsonl** | OuterLoop (ReflectionJournal) | recovery._diagnose_failure (injected into VLM prompt), OuterLoop on next cycle |
| **cre/runs/rules.jsonl** | OuterLoop (RulesStore) | recovery._diagnose_failure (ExpeL-style rules block) |
| **cre/skill_library.json** | SkillLibrary | SkillLibrary (retrieve), test/agent (coord cache load from master skill) |
| **cre/action_trust.json** | ActionTrustTracker | ActionTrustTracker |
| **execution_log.txt** | agent_core._exec_log (when EXECUTION_LOG_PATH set) | Humans / debugging |
| **concentric_triangles_clean_pass_log.txt** | Pass-log callback (when CONCENTRIC_TRIANGLES_CLEAN and PASS_LOG_PATH set) | Humans / evidence |

---

# Part IV — Control and Data Flow (Canonical Traced Run)

1. **Init:** _init_logging(cre_dir) sets EXECUTION_LOG_PATH (and optionally PASS_LOG_PATH). _init_agent() creates MacOSAgentCore (or legacy path). _init_trace_writer(...) creates cre/runs/<run_id>/, opens trace.jsonl. Optional ActionTrustTracker(persist_path=cre/action_trust.json).
2. **Launch:** _launch_safari_and_capture(...) opens Safari to https://excalidraw.com (or configured URL), captures initial UI, optional enterprise poll.
3. **Plan:** generate_action_plan(ui_analysis, goal) or generate_dynamic_plan(...) produces a list of {action, args, description, verify?}. Optional _load_coord_cache from SkillLibrary master skill. Optional episodic memory (ReflectionJournal, RulesStore) and Summarizer.
4. **Context:** Build _Ctx(agent, vision_engine, trace_writer, coord_cache, trust_tracker, summarizer, cre_dir, journal, rules, ...).
5. **Execute:** _execute_plan(ctx, action_plan). For each action: _execute_action_with_recovery(ctx, action_item, index). Inside recovery: trace_writer.begin_step(index); optionally _ensure_canvas_clear(ctx); handler(ctx, args); on exception, _diagnose_failure → _execute_recovery → verify postcondition; trace_writer.end_step(trace_step). Per-step verification may be skipped by trust tracker.
6. **Finalize:** _finalize_run(trace_writer, outcome, action_plan, evidence) → trace_writer.finalize(outcome) writes manifest.json.

**Outer loop (separate process):** _invoke_test() runs test script in subprocess; after exit, find latest run dir; read manifest. If outcome == "success", skill_lib.ingest_from_trace(run_dir), record reflection, return success. Else healer.analyze_run(run_dir) → classification; if escalate, write ESCALATION.md, record reflection; if retry, set env and loop again.

---

# Part V — Academic References (Cited in Codebase or Docs)

The following references are explicitly cited in the project for methodology, architecture, or evaluation. This list is for attribution and further reading; it is not exhaustive of all influences.

- **Ferrante, J., Ottenstein, K., & Warren, J. (1987).** The Program Dependence Graph and Its Use in Optimization. *ACM TOPLAS*, 9(3), 319–349. (PDG; trace-level dependence analysis.)
- **Cornelissen, B., et al. (2009).** A Systematic Survey of Program Comprehension through Dynamic Analysis. *IEEE TSE*, 35(5), 684–702. (Program comprehension methodology.)
- **Fikes, R. E., & Nilsson, N. J. (1971).** STRIPS: A new approach to the application of theorem proving to problem solving. *Artificial Intelligence*, 2(3–4), 189–208. (Postcondition verification.)
- **Shinn, N., et al. (2023).** Reflexion: Language agents with verbal reinforcement learning. *NeurIPS*. arXiv:2303.11366. (Self-reflection and episodic memory.)
- **Zhao, W., et al. (2024).** ExpeL: LLM Agents Are Experiential Learners. *AAAI*. arXiv:2308.10144. (Rules from experience; injection into diagnosis.)
- **Rauba, B., et al. (2024).** SHML: Self-Healing Machine Learning. *NeurIPS*. arXiv:2411.00186. (Monitor → Diagnose → Adapt → Test.)
- **Cruz, C. (2025).** VIGIL. arXiv:2512.07094. (Stage-gated supervision; structured logs.)
- **TraceCoder (ICSE 2026).** arXiv:2602.06875. (Observe-Analyze-Repair; Historical Lesson Learning.)
- **MindGuard (2025).** arXiv:2508.20412. (Decision Dependence Graph; causal analysis.)
- **AgentArmor (2025).** arXiv:2508.01249. (Trace → PDG; security.)
- **IPIGuard (EMNLP 2025).** arXiv:2508.15310. (Tool dependency graph.)
- **GUI-Robust (2025).** arXiv:2506.14477. (Benchmark for GUI agent robustness under anomalies.)
- **MCP-Atlas (2026).** arXiv:2602.00933. (Claims-based evaluation.)
- **RAG-MCP (2025).** arXiv:2505.03275. (Semantic retrieval for tools/skills.)
- **VOYAGER (NeurIPS 2023).** (Skill library pattern.)
- **OpenHands SDK, AGENT KB, CRADLE, AgentHub.** (Modular agent infrastructure; see agent_infra/__init__.py.)
- **CRAFT, VISCO, Maestro, VisionDirector, AppAgent, SeeAct, MIRA, GUI-explorer, PG-Agent.** (Verification, exploration, and grounding; see AGENTS.md and verification_gate, research_agent, visual_monitor.)
- **OWASP MCP Top 10, MSB (ICLR 2026).** (MCP security; see security/sanitizer.py.)

---

# Part VI — Summary

- **What it is:** A trace-centric, self-healing, dual-agent GUI automation framework for macOS that uses VLMs and Quartz to drive Excalidraw (and other sites), with full observability, recovery, skill learning, and escalation.
- **Whole point:** Reliable, evolvable automation with rich traces, automatic recovery where possible, learning from success (skills) and failure (reflection/rules/escalation), and controlled cost via trust and summarization.
- **Tools:** Every component has a single responsibility; the intended dependency chain is unidirectional (TraceWriter → DiagnosticReader → HealingOrchestrator; TraceWriter → SkillLibrary; all consumed by OuterLoop), though live architecture-conformance tests should be treated as the source of truth for current drift. Execution is in the test/agent entry points, orchestration and repair in the outer loop and code agent.
- **References:** The project is explicitly grounded in Reflexion, ExpeL, SHML, VIGIL, PDG-based analysis, GUI-Robust-style benchmarking, and MCP/skill/verification literature; all citations above appear in the codebase or docs.

This document is the exhaustive PhD-level description of the Concentric Study project. For runnable commands and file locations, see AGENTS.md and .cursor/rules/concentric-study.mdc.
