# Exhaustive Report: How Our Code Is Built to Run

**Document type:** PhD-level deep dive  
**Scope:** Rigorous code-analysis methodology + full application to the concentric_study codebase  
**Output:** How the system is built and how it runs — entry points, dependencies, control flow, data flow, and execution paths.

---

# Part I — Rigorous Code Analysis Methodology

This section summarizes established methodologies for going through code rigorously, as a lens for the subsequent analysis.

## 1.1 Program comprehension and systematic navigation

- **Entry-point and execution-path analysis:** Fix entry points (e.g. `if __name__ == "__main__"`, test runners, CLI hooks), then follow call graphs and data flow to identify which code runs under which scenario. Dynamic baselines (fixed entry + input corpus) validate static call graphs and reveal real execution paths (e.g. TotalRecall/ISSTA’24-style evaluation).
- **Call-graph and hierarchical abstraction:** Static call graphs are central to understanding large systems. Multilevel clustering and hierarchical abstraction of execution traces preserve structure while reducing cognitive load (e.g. CodEx-style clustering). Both static (source) and dynamic (traces) views are used.
- **Unified representation:** Semantic-enhanced code-property graphs can sit across source and binary, supporting design recovery and multiple abstraction levels with programmatic and natural-language interfaces (e.g. UFPC-style frameworks).

## 1.2 Dependence and data flow

- **Program dependence graphs (PDGs):** Control and data dependencies make dataflow and security analysis tractable (e.g. exploring/enforcing guarantees via PDGs). Trace-level analogues (state-flow dependencies) support causal analysis without source-level PDG construction.
- **Modular reasoning:** Encapsulating risky operations behind safe abstractions and using compositional reasoning localizes verification; the rest is checked by types and composition (e.g. Safe Coding patterns). The same idea applies to our infra: TraceWriter has no infra imports; readers and orchestrators depend on it unidirectionally.

## 1.3 Static analysis and review discipline

- **Diff-aware and incremental analysis:** Focus on changed code and dependencies for speed and relevance (e.g. CI-integrated static analysis). Our “what runs” analysis is incremental in the sense that we identify distinct entry points and trace from them.
- **Review roles and baselines:** Maintainers with deep codebase knowledge perform review; baselines (tests, execution logs) define “correct” behavior. Our execution log and trace act as runtime baselines.

## 1.4 Methodology applied here

For this report we:

1. **Identified entry points** — `test_excalidraw_covt.py` (main GUI test), `outer_loop.py` (dual-agent loop), pytest for `cre/test_*.py`, and optional `agent.py`.
2. **Mapped the dependency graph** — especially `agent_infra/` (TraceWriter → DiagnosticReader → HealingOrchestrator; TraceWriter/SkillLibrary; all consumed by OuterLoop) and the test’s imports and dependency injection.
3. **Traced control flow** — from process start through init, plan generation, execution loop, recovery, and trace finalization.
4. **Traced data flow** — run directory creation, JSONL append, manifest write, and consumption by DiagnosticReader, HealingOrchestrator, SkillLibrary, ReflectionJournal.
5. **Captured execution paths** — “traced run” path (with TraceWriter, EXECUTION_LOG_PATH, recovery) vs “ad-hoc” path (no trace, no run dir).

---

# Part II — Dependency and Architecture Overview

## 2.1 Repository layout (operator-centric)

```
operator/
├── agent_infra/           # Shared infrastructure package
│   ├── __init__.py        # Re-exports all public types
│   ├── trace_writer.py    # Phase 1: TraceStep, TraceWriter
│   ├── diagnostic_reader.py
│   ├── healing_orchestrator.py
│   ├── skill_library.py
│   ├── action_trust.py
│   ├── outer_loop.py
│   ├── summarizer.py
│   ├── action_handlers.py # Handlers called by test (injected)
│   ├── recovery.py        # _execute_action_with_recovery (injected)
│   ├── startup.py         # _launch_safari_and_capture, _init_agent (injected)
│   ├── site_knowledge.py
│   ├── visual_monitor.py
│   ├── research_agent.py
│   ├── verification_gate.py
│   ├── decision_graph.py
│   └── benchmark_evaluator.py
├── cre/
│   ├── test_excalidraw_covt.py   # Main traced GUI test
│   ├── test_*.py                 # Other tests (some use infra)
│   ├── runs/                      # output: run_id/trace.jsonl, manifest.json
│   ├── skill_library.json
│   ├── action_trust.json
│   └── ...
├── agent_core.py          # MacOSAgentCore (Quartz, Gemini, focus)
├── visual_engine.py       # Set-of-Mark grounding
├── vlm_coordinator.py     # Legacy VLM path
├── codex_client.py        # Hammerspoon/legacy client
├── trace_writer.py        # Shim -> agent_infra
├── diagnostic_reader.py   # Shim -> agent_infra
├── healing_orchestrator.py
├── skill_library.py
└── ...
```

## 2.2 Unidirectional dependency chain (agent_infra)

Documented in `.cursor/rules/concentric-study.mdc` and enforced by imports:

- **trace_writer.py** — No imports from other agent_infra modules. Defines `TraceStep` and `TraceWriter`; writes `trace.jsonl` and `manifest.json`.
- **diagnostic_reader.py** — Reads trace files only (no agent_infra imports). Builds Level 1/2/3 diagnostic text from manifest + trace.
- **healing_orchestrator.py** — Imports `DiagnosticReader`. Classifies failures from manifest/trace; optionally uses `DecisionDependenceAnalyzer`.
- **skill_library.py** — Reads trace files (and optional semantic index); no imports from other infra. Ingests successful runs; exposes retrieve/ingest API.
- **action_trust.py** — Standalone; no infra imports. Tracks consecutive successes per action key for verification skip.
- **outer_loop.py** — Imports `DiagnosticReader`, `HealingOrchestrator`, `SkillLibrary`. Top-level integration: invokes test subprocess, reads run dir, classifies, adapts, writes ESCALATION.md when escalating.

So: **TraceWriter** and **SkillLibrary** are leaves (no infra deps). **DiagnosticReader** consumes traces. **HealingOrchestrator** depends on DiagnosticReader. **OuterLoop** depends on DiagnosticReader, HealingOrchestrator, and SkillLibrary. No cycles.

## 2.3 Test and execution layer dependencies

- **test_excalidraw_covt.py** imports:
  - `agent_infra`: TraceWriter, SkillLibrary, ActionTrustTracker, Summarizer, SiteKnowledge, ExplorationLoop; action_handlers (ACTION_HANDLERS, inject_dependencies); recovery (_execute_action_with_recovery, inject_dependencies); startup (_init_agent, _launch_safari_and_capture, inject_dependencies).
  - **agent_core** (MacOSAgentCore), **visual_engine** (VisualGroundingEngine) when ENTERPRISE_AVAILABLE; else **vlm_coordinator** (VLMCoordinator), **codex_client** (CodexClient).
- **Dependency injection:** Action handlers, recovery, and startup receive trace/exec_log/pass_log, cache validation, and center/phash helpers via `inject_dependencies(...)`. No global infra singletons; the test owns the context and passes a `_Ctx` into the execution loop.

---

# Part III — How the Code Is Built to Run

## 3.1 Entry points

| Entry point | Invocation | Purpose |
|-------------|------------|---------|
| **Main GUI test** | `./venv/bin/python cre/test_excalidraw_covt.py` or `CONCENTRIC_TRIANGLES_CLEAN=1 ./venv/bin/python cre/test_excalidraw_covt.py` | Runs the full traced Excalidraw flow: init agent, launch Safari, capture UI, build plan, execute with recovery, write trace and manifest. |
| **Outer loop** | `./venv/bin/python -m agent_infra.outer_loop --task CONCENTRIC_TRIANGLES_CLEAN` (or programmatic `OuterLoop(...).run()`) | Runs Monitor→Diagnose→Adapt→Test: invokes test script as subprocess, reads latest run dir, classifies failure, retries or escalates. |
| **Pytest** | `./venv/bin/python -m pytest cre/test_*.py -v --tb=short` | Runs all tests under `cre/`; some (e.g. test_diagnostic_reader, test_action_trust) use agent_infra; test_excalidraw_covt is typically run standalone for GUI. |
| **Agent (optional)** | `agent.py` if present | Alternative orchestration entry; not the primary path for the documented “run” in this report. |

The **canonical “run”** that produces `cre/runs/<run_id>/` is: execute `test_excalidraw_covt.py` (directly or via outer_loop). Runs that do not use this test (e.g. ad-hoc Magma script) do not create a run dir or trace.

## 3.2 Execution flow: test_excalidraw_covt.py (traced run)

High-level control flow:

1. **run_model_based_agent()** (main orchestrator)
   - **Logging:** `_init_logging(cre_dir)` creates `execution_log.txt`, sets `EXECUTION_LOG_PATH`; if CONCENTRIC_TRIANGLES_CLEAN, sets `PASS_LOG_PATH` for pass log.
   - **Agent init:** `_init_agent()` → returns (use_enterprise, agent, vision_engine, client, vlm). Uses MacOSAgentCore + VisualGroundingEngine when available; else VLMCoordinator + CodexClient.
   - **Task id:** `_resolve_task_id()` from env (CONCENTRIC_TRIANGLES_CLEAN, CONCENTRIC_TRIANGLES, or AGENT_GOAL).
   - **TraceWriter:** `_init_trace_writer(cre_dir, task_id, task_description, use_enterprise)` → creates `cre/runs/<run_id>/`, opens `trace.jsonl`, prepares manifest path.
   - **Trust tracker:** Optional `ActionTrustTracker(persist_path=cre/action_trust.json)` unless DISABLE_TRUST_TRACKER.
   - **Launch and capture:** `_launch_safari_and_capture(...)` → Safari, capture initial UI, optional enterprise readiness poll; sets `ui_analysis`, `current_state_path`.
   - **Optional a11y/element map:** If enterprise, can build UnifiedElementMap and WebPrimitives from A11yEngine.
   - **Episodic memory:** `_load_episodic_memory(cre_dir, task_id)` → ReflectionJournal + RulesStore for past lessons/rules.
   - **Summarizer:** Optional `Summarizer(token_budget=500)` for context.
   - **Site knowledge:** Optional SiteKnowledge + ExplorationLoop for Excalidraw tool inventory.
   - **Action plan:** `generate_action_plan(ui_analysis, goal)` (or `generate_dynamic_plan(...)` if DYNAMIC_PLAN/AGENT_GOAL) → list of `{action, args, description, verify?}`.
   - **Coord cache:** `_load_coord_cache(cre_dir, task_id)` from SkillLibrary MASTER skill `resolved_coords` when not DISABLE_COORD_CACHE.
   - **Context:** Build `_Ctx(...)` with all of the above (agent, vision_engine, trace_writer, coord_cache, trust_tracker, summarizer, etc.).
   - **Execute:** `_execute_plan(ctx, action_plan)` (see below). Outcome stored in `run_outcome` ("success" or "failure").
   - **Finalize:** `_finalize_run(trace_writer, run_outcome, action_plan, evidence_entries, agent)` → write evidence report, pHash audit step if applicable, `trace_writer.finalize(outcome=run_outcome)` → write `manifest.json`, print stats.

2. **_execute_plan(ctx, action_plan)**
   - For each action in plan: calls **`_execute_action_with_recovery(ctx, action_item, step_index)`** (recovery module). No per-step TraceWriter calls inside this summary; recovery and handlers are responsible for updating trace and exec log.
   - For steps with `verify=True`, takes verification screenshot and optionally runs visual assert.
   - If CONCENTRIC_TRIANGLES_CLEAN and enterprise, captures evidence screenshots and appends to evidence_entries.

3. **_execute_action_with_recovery** (agent_infra/recovery.py)
   - Dispatches to the appropriate **ACTION_HANDLERS** entry for `action_item["action"]`.
   - Wraps execution in try/except; on failure, can run diagnosis (`_diagnose_failure`), recovery (`_execute_recovery`), and retry. Records failure in TraceWriter when used (via ctx.trace_writer).
   - Per-step trace writing is done by the recovery layer (begin_step/end_step/record_failure) so that each action is one or more trace steps with pre_state, thought, action, action_result, post_state.

4. **Action handlers** (agent_infra/action_handlers.py)
   - Each handler receives `(ctx, args)` and performs one logical action: keystroke, click, set_stroke_color, draw_path, draw_concentric_triangles, clear_canvas, refresh_canvas_center, verify_success, etc.
   - Handlers use `ctx.agent` (MacOSAgentCore) for focus, click, keystroke, draw; `ctx.vision_engine` for SoM/grounding when needed; `ctx.coord_cache` and pHash validation for cached coordinates; `ctx.trust_tracker` for verification skip.
   - Enterprise path: high-res screenshots (Gemini File API), Quartz global coordinates, SoM overlay for clicks when cache misses or is invalid.

So: **one process** runs the test; that process creates **one run directory** per invocation, appends to **one trace.jsonl**, and writes **one manifest.json** at the end. Execution log and pass log (when set) are process-global via env vars.

## 3.3 Data flow: run directory and trace

- **Producer (TraceWriter):**
  - **Constructor:** `TraceWriter(output_dir, task_id, task_description, agent_config)` creates `output_dir/runs/<run_id>/`, `screenshots/`, and empty `trace.jsonl`.
  - **Per step:** `begin_step(i)` → TraceStep; caller sets pre_state, thought, action, action_result, post_state, evaluation; `end_step(step)` → step.finalize(), append one JSON line to `trace.jsonl`.
  - **On failure:** `record_failure(step_index, category, error_summary)` stores failure pointer (at most once per run).
  - **Finalize:** `finalize(outcome)` writes `manifest.json` (run_id, task_id, outcome, failure_step, failure_category, error_summary, steps_summary, timing, environment).

- **Consumers:**
  - **DiagnosticReader(run_dir):** Reads `manifest.json` and `trace.jsonl`; exposes `level1_summary()`, `level2_failure_window()`, `full_diagnostic()`, etc., for progressive disclosure.
  - **HealingOrchestrator.analyze_run(run_dir):** Uses DiagnosticReader to load manifest; if outcome != "success", gets failure step data and classifies via `_classify_failure`; returns FailureClassification (category, confidence, action, details) or None.
  - **HealingOrchestrator.analyze_run_with_ddg(run_dir):** Same as above, plus builds DecisionDependenceAnalyzer from trace steps, gets causal chain and failure context, appends DDG notes to classification details.
  - **SkillLibrary.ingest_from_trace(run_dir):** Called by OuterLoop on success; reads trace/manifest, creates/updates skill record with maturity (candidate/proven/master) and optional resolved_coords; persists to `skill_library.json`.
  - **ReflectionJournal / RulesStore:** OuterLoop records reflections and rules under `runs/reflection_journal.jsonl` and `runs/rules.jsonl`; these are not inside a specific run_id dir but alongside runs.

So: **single producer (TraceWriter)** during the test process; **multiple consumers** after the run (DiagnosticReader, HealingOrchestrator, SkillLibrary, and optionally DDG/BenchmarkEvaluator).

## 3.4 Execution flow: outer_loop

- **OuterLoop.run():**
  - Loop over cycles (1..max_cycles):
    - **MONITOR:** `_invoke_test()` → subprocess.run([python, test_script], env with TASK_ENV_MAP for task_id). Waits for process exit; then locates latest run dir under runs_dir (by manifest mtime or run_id listing). Returns that run_dir or None (timeout/error).
    - **Read manifest** from run_dir; if missing, return aborted.
    - **SUCCESS:** If manifest["outcome"] == "success", call `skill_lib.ingest_from_trace(run_dir)`, record success in ReflectionJournal, return OuterLoopResult(outcome="success", ...).
    - **DIAGNOSE:** `healer.analyze_run(run_dir)` → FailureClassification.
    - **ADAPT:** If classification.action == "abort", record and return aborted. If "escalate_to_code_agent", write ESCALATION.md (Level 1/2/3 diagnostic + reflection context), return escalated. If "retry" or "adjust_parameters", set env for next cycle and continue loop.
  - If max_cycles exhausted without success, return max_retries_exhausted.

So the **outer loop does not execute actions itself**; it only runs the test script, reads the trace/manifest, classifies failure, and either retries with env tweaks or escalates. All GUI execution is inside the test subprocess.

## 3.5 Agent core and low-level execution

- **MacOSAgentCore** (agent_core.py):
  - **Focus:** `enforce_app_focus(app_name)` via NSWorkspace/Cocoa.
  - **Screenshots:** Can use Gemini File API (upload path, model sees image) or local path for VLM.
  - **Coordinates:** `_pixel_to_global_quartz(pixel_x, pixel_y)` using NSScreen backing scale and frame; screenshot pixels → global Quartz for CGEvent.
  - **Click:** `execute_global_click(pixel_x, pixel_y)` → focus Safari, then CGEvent left mouse down/up at converted point.
  - **Move:** `execute_move_mouse(pixel_x, pixel_y)`.
  - **Keystroke:** `execute_keystroke(key)` with keycode map (e.g. pen tool "p", stroke "S").
  - **Draw path:** `execute_draw_path_segments(center, vertices)` for polygon strokes.
  - **Visual assert:** `assert_visual_state(image_path, question)` via VLM (e.g. Gemini Flash); used by recovery for verify steps.
  - **Logging:** `_exec_log` only when EXECUTION_LOG_PATH is set; `_trace` writes to a debug log path.

So: **execution is synchronous** within the test process; each action blocks until done. Recovery and handlers call into agent_core; no separate “execution server” in the main design.

## 3.6 Paths that do not produce a trace

- **Ad-hoc scripts** (e.g. Magma drawing) that only use agent_core or Quartz directly: no TraceWriter, no run dir, no manifest, no execution log (unless the script sets EXECUTION_LOG_PATH).
- **Tests that don’t call TraceWriter** (e.g. unit tests for DiagnosticReader that only read existing runs): they consume traces but don’t create new ones.
- **Outer loop** itself doesn’t write trace; it only invokes the test and reads the result.

So “how the code is built to run” has **two main modes**: (1) **traced run** — test_excalidraw_covt (or similar) with TraceWriter and recovery producing `runs/<run_id>/`; (2) **outer-loop run** — same test invoked by outer_loop with task env, then diagnose/adapt. All other entry points (pytest for non-GUI tests, one-off scripts) are secondary and may or may not produce traces.

---

# Part IV — Summary Tables

## 4.1 Entry points and what they produce

| Entry point | Run dir | trace.jsonl | manifest.json | Execution log |
|-------------|--------|-------------|---------------|----------------|
| test_excalidraw_covt.py (direct) | Yes (cre/runs/<run_id>/) | Yes | Yes | Yes (if cre_dir/execution_log.txt set) |
| outer_loop (invokes test) | Yes (same) | Yes | Yes | Yes (same) |
| pytest cre/test_*.py | Depends on test | Only if test uses TraceWriter | Only if test uses TraceWriter | Only if test sets EXECUTION_LOG_PATH |
| Ad-hoc script (e.g. Magma) | No | No | No | No (unless script sets it) |

## 4.2 Key file roles

| File / dir | Role |
|------------|------|
| agent_infra/trace_writer.py | Creates run dir, writes trace.jsonl and manifest.json; no infra deps |
| agent_infra/diagnostic_reader.py | Reads run dir; Level 1/2/3 diagnostics |
| agent_infra/healing_orchestrator.py | Classifies failure from manifest/trace; optional DDG |
| agent_infra/skill_library.py | Ingests successful runs; maturity; resolved_coords |
| agent_infra/outer_loop.py | Runs test subprocess; diagnose; adapt; escalate |
| agent_infra/action_handlers.py | Implements action types; called from recovery with ctx |
| agent_infra/recovery.py | _execute_action_with_recovery; diagnose + retry; trace steps |
| agent_infra/startup.py | _init_agent, _launch_safari_and_capture |
| cre/test_excalidraw_covt.py | Main GUI test; orchestrator; injects deps; builds plan; runs _execute_plan |
| agent_core.py | MacOSAgentCore: focus, screenshot, Quartz click/keystroke/draw, VLM assert |
| cre/runs/ | Output directory for run_id subdirs, reflection_journal.jsonl, rules.jsonl |

## 4.3 Control flow summary (traced run)

```
run_model_based_agent()
  → _init_logging(cre_dir)                    # EXECUTION_LOG_PATH, PASS_LOG_PATH
  → _init_agent()                             # enterprise or legacy agent/vlm
  → _init_trace_writer(...)                   # creates runs/<run_id>/, trace.jsonl
  → ActionTrustTracker(...)                   # optional
  → _launch_safari_and_capture(...)           # Safari, screenshot, ui_analysis
  → [optional] a11y, element_map, primitives
  → _load_episodic_memory(...)                # ReflectionJournal, RulesStore
  → Summarizer(), SiteKnowledge, ExplorationLoop  # optional
  → generate_action_plan(...)                 # or generate_dynamic_plan
  → _load_coord_cache(...)                   # from SkillLibrary master skill
  → _Ctx(...)
  → _execute_plan(ctx, action_plan)
       for each action:
         _execute_action_with_recovery(ctx, action_item, i)
           → ACTION_HANDLERS[action_type](ctx, args)   # may use agent, vision_engine, cache
           → on failure: _diagnose_failure, _execute_recovery, retry
           → trace step end_step / record_failure
  → _finalize_run(...)                        # manifest, evidence, pHash step
  → return 0
```

## 4.4 Data flow summary

- **Write path:** TraceWriter.begin_step → caller fills TraceStep → end_step → append to trace.jsonl; record_failure on first failure; finalize → manifest.json.
- **Read path (same run):** DiagnosticReader(run_dir) → _load_manifest(), _load_steps() → level1_summary(), level2_failure_window(), full_diagnostic().
- **Read path (outer loop):** OuterLoop.run() → _invoke_test() → subprocess runs test (writes run dir) → after exit, read run_dir → DiagnosticReader → HealingOrchestrator.analyze_run(run_dir) → classification → adapt or ingest_from_trace (on success).

---

This report is the exhaustive description of how the code is built to run: methodology (Part I), dependency and architecture (Part II), and full execution and data flow (Part III–IV). For file-by-file edits, respect the unidirectional infra chain and the fact that only the test (and whatever it calls) produces traces; the outer loop and other tools only consume them.
