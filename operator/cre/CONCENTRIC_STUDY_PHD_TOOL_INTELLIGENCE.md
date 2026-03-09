# Concentric Study PhD Tool Intelligence Pack

Date: `2026-03-05` (America/Los_Angeles)  
Scope: `concentric_study` only (not Cursor Intelligence side projects)

Related architecture synthesis:
- `operator/cre/project_understanding/MASTER_PHD_ARCHITECTURE_BRIEF.md`

Related whole-repo tool adoption memo:
- `operator/cre/DECISION_SUPPORT_TOOL_ADOPTION_PHD.md`

## 1. Research Question

What tools, infrastructure layers, and Cursor-facing integrations are currently present in `concentric_study`, and how should another high-capability agent reason about them without tool sprawl?

## 2. Method (Evidence-First)

Primary repo sources inspected:
- `AGENTS.md`
- `operator/agent_infra/__init__.py`
- `operator/cre/MASTER_TOOL_LIST_PHD.md`
- `operator/cre/artifacts/master_tool_list.json`
- `operator/agent_infra/tool_health_catalog.json`
- `operator/cre/PHD_DECISION_PRACTICE.md`
- `operator/cre/MISSED_TOOL_WORKFLOW_VALUE_PHD.md`
- `operator/cre/PHASE_1_ENVIRONMENT_BENEFITS_PHD.md`
- `operator/cre/TOOL_CHEAT_SHEET_PHD.md`
- `operator/cre/CURSOR_2_6_PROJECT_FIT_PHD.md`
- `operator/cre/CURSOR_2_6_OPERATING_PROTOCOL_PHD.md`
- `.cursor/mcp.json`
- `.cursor/rules/*.mdc`
- `.cursor/plans/*.md`
- `operator/cursor_integration/mcp/*.py`
- `operator/cre/artifacts/cursor_environment/latest_report.md`

Validation run:
- `cd operator && ./venv/bin/python -m pytest cursor_integration/tests -q`
- Result: `6 passed` (`0.25s`)

## 3. Environment Baseline (Local Facts)

- Cursor: `2.6.11` (stable)
- VS Code base: `1.105.1`
- Electron: `39.6.0`
- macOS: `26.3` build `25D125`
- Architecture: `arm64`
- Source: `operator/cre/artifacts/cursor_environment/latest_report.md`

Interpretation: 2.6-era Cursor surfaces are locally available, but repo policy still prioritizes local evidence and bounded integrations before broad external feature expansion.

### 3.1 Host Security Addendum (Read-Only Audit Context, 2026-03-05)

The current intelligence pack did not originally include the separate read-only Mac security report.  
For decision completeness, treat the following as in-scope host context:

- platform hardening appears intact (`Activation Lock`, `FileVault`, `SIP`, `Authenticated Root`, `Gatekeeper`)
- pending updates were reported (`macOS 26.3.1`, `Command Line Tools 26.3`)
- highest-impact exposure claim: `Chrome Remote Desktop` installed/enabled/running with screen/accessibility privileges
- lateral/local exposure claim: SMB public share with guest access reported
- credential hygiene risk claim: plaintext secrets in `~/.zshrc`
- privilege-amplification risk: broad TCC grants for automation-heavy tools (Cursor, Hammerspoon, Terminal/Docker)

Interpretation: no direct stealth-malware indicator was reported, but authorized remote-control + broad local privileges were identified as primary practical risk.

## 4. Tool Inventory State (Definitive Snapshot)

From `operator/cre/artifacts/master_tool_list.json`:
- Total tool entries: `67`
- `current`: `47`
- `optional`: `7`
- `legacy`: `8`
- `historical_reference`: `5`

Category distribution:
- `internal_module`: `35`
- `python_dependency`: `13`
- `system_tool`: `6`
- `operational_script`: `5`
- `legacy_runtime`: `3`
- `historical_reference`: `5`

Implication: this is a mature stack with a large first-party core; most value comes from exposing and orchestrating existing infrastructure, not adding new generic wrappers.

## 5. Current Architecture (Operationally Relevant)

### 5.1 Canonical shared infra (`operator/agent_infra`)

Exported components include:
- `TraceWriter`, `DiagnosticReader`, `HealingOrchestrator`
- `SkillLibrary`, `SemanticSkillIndex`
- `OuterLoop`, `ReflectionJournal`, `RulesStore`
- `ActionTrustTracker`, `Summarizer`
- `SiteKnowledge`, `ExplorationLoop`, `ToolAffordance`
- `HostToolHealth`, `VisualMonitor`
- `ResearchAgent`, `VerificationGate`
- `DecisionDependenceAnalyzer`, `BenchmarkEvaluator`

These define a full monitor-diagnose-adapt-verify-evaluate lifecycle, not just one-shot execution.

### 5.2 Health and substrate gating

`operator/agent_infra/tool_health_catalog.json` defines `10` tool classes.
Required classes (`4`):
- `runtime_python_selected`
- `macos_ui_automation`
- `native_event_backend`
- `screen_capture`

Default preferred providers include:
- `operator_venv_python`
- `osascript_system_events`
- `pyobjc_native_stack`
- `screencapture_cli`

Implication: host-tool readiness is first-class and fail-closed for required substrate classes.

### 5.3 Security and trust model

Core defensive layers referenced in `AGENTS.md`:
- input sanitization (`InputSanitizer`) with MCP poisoning defenses
- credential isolation (`CredentialVault`)
- human approval for sensitive actions (`HITLGuard`)
- post-execution verification (`VerificationGate`)
- probabilistic skip controls (`ActionTrustTracker`)

## 6. Cursor Integration State (Repo-Local)

### 6.1 Active MCP config (`.cursor/mcp.json`)

Active entries:
- `context7` (external docs MCP, key via `CONTEXT7_API_KEY`)
- `concentric-health` (local read-only server)
- `concentric-trace` (local read-only server)

### 6.2 Implemented internal servers (all read-only)

`concentric-health` tools:
- `health_summary`
- `check_tool_class`
- `compare_environment_baselines`
- `cursor_environment_snapshot`

`concentric-trace` tools:
- `list_recent_runs`
- `get_run_manifest`
- `get_run_summary`
- `summarize_failure_chain`
- `list_run_artifacts`

`concentric-benchmark` tools (implemented, not active by default):
- `evaluate_run`
- `compare_runs`
- `latest_benchmark_summary`

`concentric-research` tools (implemented, not active by default):
- `get_research_brief`
- `search_research_notes`
- `method_tool_map`

## 7. Cursor Operating Layer (Already Added)

Rules present in `.cursor/rules/`:
- `concentric-study.mdc`
- `cursor-intelligence-charter.mdc`
- `context7-docs.mdc`
- `plan-artifact-discipline.mdc`
- `browser-debug-evidence.mdc`
- `mcp-governance.mdc`
- `runtime-debug-discipline.mdc`

Plans present in `.cursor/plans/`:
- `context7-pilot.md`
- `debug-runtime-regression.md`
- `add-internal-mcp.md`
- `research-before-runtime.md`
- `browser-task-triage.md`
- `cursor-intelligence-bootstrap.md`
- `evidence-gated-task-template.md`
- `maze_report.md`

Protocol documents:
- `operator/cre/CURSOR_2_6_PROJECT_FIT_PHD.md`
- `operator/cre/CURSOR_2_6_OPERATING_PROTOCOL_PHD.md`

## 8. What Actually Improves Workflow (Evidence-Based)

From `operator/cre/MISSED_TOOL_WORKFLOW_VALUE_PHD.md`:

High-value enhancers:
- `ResearchAgent`
- semantic repository retrieval (`SemanticSkillIndex`/codebase semantic search)
- lint/static-diagnostic reads
- `VisualMonitor`
- `BenchmarkEvaluator`

Conditional:
- bounded subagent exploration for targeted evidence gathering

Low net-new in this environment:
- shell/file/edit wrappers already covered by existing tool surfaces

## 9. Practical Decision Rule For New Work

If task is non-trivial:
1. verify host substrate (`HostToolHealth`/`concentric-health`)
2. do research pass (`ResearchAgent`/saved briefs)
3. execute with trace and verification enabled
4. diagnose with `DiagnosticReader` + DDG-aware chain analysis
5. benchmark and compare runs before claiming improvement

This follows repository policy from `operator/cre/PHD_DECISION_PRACTICE.md`.

## 10. Copy-Paste Prompt For Another Project (Concentric Context Injection)

Use the block below as the exact bootstrap prompt when you want another agent to reason with `concentric_study` context:

```text
You are entering with Concentric Study context. This is a macOS visual web-agent research stack, not a generic IDE helper.

Mission:
- Operate evidence-first and fail-closed.
- Prioritize repo-native infrastructure before adding external dependencies.
- Treat environment substrate and verification as first-class.

Authoritative tool baseline (from concentric_study):
1) Shared infra (`operator/agent_infra`):
   - TraceWriter, DiagnosticReader, HealingOrchestrator
   - SkillLibrary + SemanticSkillIndex
   - OuterLoop + ReflectionJournal + RulesStore
   - ActionTrustTracker, Summarizer
   - SiteKnowledge/ExplorationLoop/ToolAffordance
   - HostToolHealth, VisualMonitor
   - ResearchAgent, VerificationGate
   - DecisionDependenceAnalyzer, BenchmarkEvaluator
2) Health model:
   - Required substrate classes: runtime_python_selected, macos_ui_automation, native_event_backend, screen_capture.
   - Default preferred providers: operator_venv_python, osascript_system_events, pyobjc_native_stack, screencapture_cli.
3) Cursor MCP (read-only first wave):
   - Active: context7, concentric-health, concentric-trace.
   - Implemented but usually inactive until needed: concentric-benchmark, concentric-research.
   - Health MCP tools: health_summary, check_tool_class, compare_environment_baselines, cursor_environment_snapshot.
   - Trace MCP tools: list_recent_runs, get_run_manifest, get_run_summary, summarize_failure_chain, list_run_artifacts.
   - Benchmark MCP tools: evaluate_run, compare_runs, latest_benchmark_summary.
   - Research MCP tools: get_research_brief, search_research_notes, method_tool_map.

Operating protocol:
- `/plan` for non-trivial work; `/ask` for read-only exploration.
- Keep MCP set minimal; name MCP explicitly when ambiguity exists.
- For failures capture Request ID + screenshot/state evidence and classify failure source:
  repo code vs MCP routing vs sandbox/network vs Cursor product behavior.
- For UI work, collect state evidence before action.

Workflow priorities:
- Highest value: ResearchAgent, semantic retrieval, VisualMonitor, BenchmarkEvaluator.
- Avoid redundant wrapper tooling if equivalent capability already exists.

Decision method:
- Facts first -> decision second -> consequences third.
- No non-trivial implementation without explicit evidence context.
```

## 11. Bottom Line

`concentric_study` already has a strong systems-grade tool stack. The highest-leverage move is disciplined orchestration of existing components (health -> research -> execution -> verification -> forensic diagnosis -> benchmark comparison), with internal read-only MCP exposure used as the Cursor bridge.

## 12. Cursor Intelligence Bootstrap (Operational Start Point)

Start order:
1. load charter rule: `.cursor/rules/cursor-intelligence-charter.mdc`
2. open bootstrap plan: `.cursor/plans/cursor-intelligence-bootstrap.md`
3. copy template for current objective: `.cursor/plans/evidence-gated-task-template.md`
4. execute only after pass/fail checkpoints and stop conditions are explicit

This keeps Cursor behavior deterministic, evidence-backed, and bounded.

## 13. Activation Snapshot (Executed)

Activation artifacts:
- plan: `.cursor/plans/cursor-intelligence-activation-2026-03-05.md`
- machine-readable snapshot: `operator/cre/artifacts/cursor_intelligence_activation_2026-03-05.json`

Executed verification:
- `cd operator && ./venv/bin/python -m pytest cursor_integration/tests -q` -> `6 passed`
- `cd operator && ./venv/bin/python -m pytest cre/test_cre_doc_registry.py -q` -> `5 passed`

Host readiness during activation:
- `all_required_ready = true`
- selected providers include:
  - `operator_venv_python`
  - `osascript_system_events`
  - `pyobjc_native_stack`
  - `screencapture_cli`
  - `safari_bundle`

## 14. Live Human-Visible Control Proof (Executed)

Executed script:
- `operator/cre/run_live_visual_control_demo.py`

Evidence artifacts:
- `operator/cre/artifacts/live_visual_control_demo_2026-03-05.json`
- `operator/cre/artifacts/live_visual_control_demo_2026-03-05.png`
- plan log: `.cursor/plans/live-visual-control-demo-2026-03-05.md`

Observed sequence:
- app activation (`TextEdit`)
- smooth pointer movement across 5 path points
- center click
- paced multiline typing via native keyboard events
- completion screenshot capture

Interpretation:
- the current local substrate supports live, operator-visible native control
  (mouse + click + typing) using the same Quartz/System Events foundation used
  by the main Concentric agent path.

Additional Cursor-surface proof:
- script: `operator/cre/run_live_cursor_window_demo.py`
- artifacts:
  - `operator/cre/artifacts/live_cursor_window_demo_2026-03-05.json`
  - `operator/cre/artifacts/live_cursor_window_demo_2026-03-05.png`
- observed sequence:
  - activate Cursor
  - `Cmd+N` (new scratch tab)
  - visible 5-point mouse path
  - click into editor region
  - type payload by native key events
