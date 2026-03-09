# Maze Report — Understand the Maze Game

**Center:** This chat (the starting point).  
**Goal:** Understand the maze (the laptop as experienced from this chat — workspace, tools, MCPs).  
**Finished:** When this report exists and the agent has reported back once.

---

## 1. Structural Map (regions and entry points)

### Workspace root (`concentric_study/`)
- **.cursor/** — Rules and plans: `rules/` (6 .mdc files), `plans/` (6 plans + README), `mcp.json` (MCP server config).
- **.git/** — Version history.
- **.tmp_video/** — Video-related artifacts (e.g. transcripts, cleaned text); side region.
- **.tmp_video_env/** — Isolated env for video tooling (e.g. yt-dlp).
- **operator/** — Main body: agent code, infra, CRE, security, venv.
- **Root docs:** AGENTS.md, DUAL_AGENT_LOOP_PLAN.md, POTENTIAL_CHANGES.md, SETUP.md, SETUP_STATUS.md, COMPLEXITY_ANALYSIS_REPORT.md, verify_setup.py, injection_test.log.

### Operator (`operator/`)
- **agent_infra/** — Shared infrastructure package (24 modules): trace_writer, diagnostic_reader, healing_orchestrator, skill_library, outer_loop, action_trust, summarizer, site_knowledge, host_tool_health, visual_monitor, research_agent, verification_gate, decision_graph, benchmark_evaluator, action_allowlist, action_contracts, action_handlers, recovery, startup, tool_health_catalog.json.
- **cre/** — Continuous run environment: **runs/** (many run dirs, each with trace.jsonl, manifest.json; reflection_journal.jsonl, rules.jsonl at runs level), **skill_library.json**, **action_trust.json**, **tools/**, **artifacts/**, **project_understanding/**, **reddit_research_demo/**, **transcripts/**, many test_*.py and run_*.py scripts, site_knowledge_*.json files.
- **cursor_integration/** — Cursor-facing layer: **mcp/** (health_server, trace_server, benchmark_server, research_server, base), **apps/**, **plugin/**, **tests/**.
- **security/** — sanitizer, credential_vault.
- **venv/** — Python virtual environment.
- **Root-level .py:** a11y_engine, action_space, agent, agent_core, capability_router, codex_client, element_map, inference_router, screenshot_preprocessor, visual_engine, vlm_coordinator, web_primitives, window_capture; shims: diagnostic_reader, healing_orchestrator, outer_loop, skill_library, trace_writer (point into agent_infra).

### .cursor/
- **rules:** browser-debug-evidence, concentric-study, context7-docs, mcp-governance, plan-artifact-discipline, runtime-debug-discipline.
- **plans:** browser-task-triage, research-before-runtime, add-internal-mcp, debug-runtime-regression, context7-pilot, README.
- **mcp.json:** context7 (external URL), concentric-health (local zsh/python), concentric-trace (local zsh/python).

---

## 2. Semantic Map (purpose of regions and spine)

| Region | Purpose |
|--------|--------|
| **agent_infra** | Shared foundation: tracing, diagnostics, self-healing, skills, outer loop, research, verification, DDG, benchmark evaluation; unidirectional dependency chain. |
| **cre** | Where the agent runs and learns: runs dir (traces, manifests), skill_library.json, action_trust.json, reflection_journal.jsonl, rules.jsonl; tests and run scripts. |
| **cursor_integration** | Read-only MCP servers exposing repo-local health and trace forensics to Cursor. |
| **operator (root .py)** | Perception and action: a11y, element_map, web_primitives, agent_core, agent, inference_router, security; shims for backward compat. |
| **.cursor** | Governance: rules (how to behave), plans (durable workflows), MCP config. |
| **.tmp_video / .tmp_video_env** | Video/download side branch; not part of agent spine. |

**Spine (dependency order):**
- **TraceWriter** (Phase 1) → writes trace.jsonl + manifest per run.
- **DiagnosticReader** (Phase 2) → reads traces with progressive disclosure (3 levels).
- **HealingOrchestrator** (Phase 3) → classifies failures, recommends actions; uses DiagnosticReader.
- **SkillLibrary** (Phase 5) → ingests successful traces; reads trace data.
- **OuterLoop** (Phase A) → Monitor → Diagnose → Adapt → Test; uses DiagnosticReader, HealingOrchestrator, SkillLibrary.

Standalone / no infra imports: ActionTrustTracker, Summarizer, DecisionDependenceAnalyzer, BenchmarkEvaluator, HostToolHealth, VisualMonitor, ResearchAgent, VerificationGate, SiteKnowledge.

---

## 3. Behavioral Map (run → trace → diagnose → heal/skill)

- **Run:** A test or run script (e.g. test_excalidraw_covt.py, run_qa_practice_mastery.py) executes under operator/venv; it uses TraceWriter to open a run dir under `operator/cre/runs/<run_id>/`.
- **Trace:** Each step is written as a JSONL line (trace.jsonl); at end, manifest.json is written (run_id, task_id, outcome, duration, steps_summary, error_summary, etc.).
- **Diagnose:** DiagnosticReader(run_dir) reads trace + manifest; full_diagnostic() gives Level 1–3 disclosure. HealingOrchestrator(get_diagnostic_for_code_agent) classifies failure and returns recommended actions; can use DecisionDependenceAnalyzer for causal chain.
- **Skill / escalate:** On success, SkillLibrary.ingest_from_trace(run_dir) can store a skill (candidate → proven → master). OuterLoop runs the test, reads trace, classifies via HealingOrchestrator, then retries or writes ESCALATION.md for the code agent; it also appends to reflection_journal.jsonl and can update rules.jsonl.
- **Persistent state:** reflection_journal.jsonl (episodic lessons), rules.jsonl (ExpeL-style rules), skill_library.json (verified skills), action_trust.json (per-action success counts for verification skip).

---

## 4. Boundary Map (tool inventory and what each reveals)

| Tool | What it reveals |
|------|------------------|
| **Read** | Static content of any file in the maze (docs, code, config, manifests). |
| **Glob** | File/directory layout by pattern; reachable paths. |
| **Grep** | Where symbols or strings appear; dependency and usage. |
| **SemanticSearch** | “How does X work?” / “Where is Y?” once structure is roughly known. |
| **Shell** (read-only) | Filesystem listing, line counts, process visibility within sandbox. |
| **TodoWrite** | Progress through phases (optional). |
| **call_mcp_tool** | Live queries to MCP servers (concentric-health: environment readiness; concentric-trace: run forensics). In this session the concentric-health and concentric-trace tools were not found / servers had errored; tool surface is documented from codebase. |
| **fetch_mcp_resource** | MCP resources (e.g. status, docs) if exposed. |
| **mcp_task** (subagent) | Broad exploration or shell tasks; use when a targeted read/search is not enough. |

**What I cannot do from this chat:** See other chats; modify files or run tests (unless explicitly allowed); access full disk outside workspace; assume MCP servers are up without checking.

---

## 5. MCP Wing

**concentric-health** (operator, via cursor_integration.mcp.health_server):
- **health_summary** — HostToolHealth readiness and selected providers (has_url optional).
- **check_tool_class** — Availability and selected provider for one tool class.
- **compare_environment_baselines** — Diff two Cursor environment snapshot JSONs.
- **cursor_environment_snapshot** — Live read-only environment snapshot vs latest baseline.

**concentric-trace** (operator, via cursor_integration.mcp.trace_server):
- **list_recent_runs** — Recent traced runs under operator/cre/runs (limit 1–50).
- **get_run_manifest** — manifest.json for a run_id.
- **get_run_summary** — DiagnosticReader summary for a run (detail_level 1–3).
- **summarize_failure_chain** — DDG-aware healing summary for a run.
- **list_run_artifacts** — Files under a run directory.

**Observed in this session:** MCP tool calls for concentric-health and concentric-trace returned “tool not found” / server metadata indicates server had errored. Run forensics was instead observed by reading from the filesystem: e.g. `operator/cre/runs/096e149c220f/manifest.json` (task_id, outcome, duration, steps_summary, failure_category) and `operator/cre/runs/reflection_journal.jsonl` (episodic lessons). So the MCP wing *design* is: health = environment readiness on this laptop; trace = run listing and per-run manifest/summary/failure chain.

---

## 6. Summary

- **Center:** This chat.  
- **Goal:** Understand the maze (the laptop as experienced from here: workspace, operator, agent_infra, cre, cursor_integration, .cursor, and the tools/MCPs available).  
- **Finished:** This report is the deliverable; the agent reports back once with “Game finished.” and this report (or its path).
