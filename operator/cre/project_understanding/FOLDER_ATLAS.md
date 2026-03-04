# Folder Atlas

## Top-Level Structure

| Folder | Mission | Why it matters |
|---|---|---|
| `.` | Workspace root for repo-wide governance and architecture memos | Sets the rules and cross-cutting research framing |
| `.cursor/` | Editor/agent operating context | Holds mandatory project-specific rules |
| `operator/` | Main Python implementation tree | Contains runtime code, infrastructure, security, and experiments |
| `operator/agent_infra/` | Shared infrastructure package | Canonical source for tracing, diagnosis, recovery, learning, and benchmarking |
| `operator/security/` | Security controls | Input sanitization, credential vault, and HITL guard |
| `operator/cre/` | Experiment and evidence layer | Tests, docs, screenshots, scripts, state, and run history |
| `operator/cre/runs/` | Persistent run history | The best source of dynamic truth about actual executions |
| `operator/cre/project_understanding/` | This comprehension corpus | Converts the repo into a navigable knowledge system |

## Root

### `.`
- Primary contents: `AGENTS.md`, `DUAL_AGENT_LOOP_PLAN.md`, `POTENTIAL_CHANGES.md`, setup docs
- Role: repo governance and architecture-wide framing
- Read first when making non-trivial decisions

### `.cursor/`
- Primary contents: rule files for the editor/agent workflow
- Role: local operating policy, especially the PhD work standard
- Key file: `.cursor/rules/concentric-study.mdc`

## Implementation Tree

### `operator/`
- Mission: executable runtime code plus compatibility shims
- Key entrypoints: `operator/agent.py`, `operator/agent_core.py`
- Key support modules: `operator/action_space.py`, `operator/capability_router.py`,
  `operator/a11y_engine.py`, `operator/element_map.py`, `operator/web_primitives.py`,
  `operator/inference_router.py`, `operator/visual_engine.py`
- Important nuance: `operator/trace_writer.py`, `operator/diagnostic_reader.py`,
  `operator/healing_orchestrator.py`, `operator/outer_loop.py`, and
  `operator/skill_library.py` are shims

### `operator/agent_infra/`
- Mission: canonical infrastructure package
- Dependency pattern: mostly unidirectional from tracing to diagnosis to healing to outer-loop integration
- Highest-value files:
  - `trace_writer.py`
  - `diagnostic_reader.py`
  - `healing_orchestrator.py`
  - `outer_loop.py`
  - `recovery.py`
  - `action_handlers.py`
  - `skill_library.py`
  - `site_knowledge.py`
  - `verification_gate.py`
  - `benchmark_evaluator.py`
  - `decision_graph.py`
- Reading strategy: start with `__init__.py` to see the public package surface, then read the modules in the dependency order above

### `operator/security/`
- Mission: security hardening and human-control boundary
- Files:
  - `sanitizer.py`
  - `credential_vault.py`
- Why it matters: these modules define how the agent avoids prompt injection,
  credential leakage, and unsafe autonomy

## Experiment and Evidence Tree

### `operator/cre/`
- Mission: experimental harnesses, docs, evidence images, state files, and scripts
- This folder is structurally mixed; do not treat it as a single subsystem
- Sub-families inside it:
  - test harnesses: `test_*.py`
  - PhD docs: reports, analyses, memos, and validations
  - state stores: `skill_library.json`, `action_trust.json`, `routing_state.json`
  - site knowledge: `site_knowledge_*.json`
  - evidence images: `_checkpoint_*.png`, `diag_*.png`, `assert_after_*.png`, etc.
  - shell/Lua scripts: `run_agent.sh`, `run_ultimate_tests.sh`, `showcase.sh`, `verify_kernel.sh`, `codex_kernel.lua`

### `operator/cre/runs/`
- Mission: persistent run-history store
- Canonical artifacts:
  - `<run_id>/trace.jsonl`
  - `<run_id>/manifest.json`
  - `<run_id>/ESCALATION.md` when escalation occurs
  - `reflection_journal.jsonl`
  - `rules.jsonl` when rule extraction has happened
- Important nuance: some run directories can exist without `manifest.json` if a run crashes before finalization

### `operator/cre/evidence/`
- Mission: reserved evidence bucket
- Current state: sparse compared with the much larger evidence surface embedded directly in `operator/cre/`

### `operator/cre/evidence_concentric_clean/`
- Mission: task-specific evidence bundle for the concentric-triangles scenario
- Use this when you need curated artifacts rather than the raw full `runs/` history

## Reading Recommendations By Goal

### Understand the whole architecture
1. `operator/agent_infra/__init__.py`
2. `operator/cre/test_excalidraw_covt.py`
3. `operator/agent.py`
4. `operator/agent_infra/outer_loop.py`
5. `operator/agent_infra/recovery.py`
6. `operator/agent_infra/action_handlers.py`

### Understand persistent state and learning
1. `operator/cre/skill_library.json`
2. `operator/cre/action_trust.json`
3. `operator/cre/runs/reflection_journal.jsonl`
4. `operator/agent_infra/skill_library.py`
5. `operator/agent_infra/action_trust.py`
6. `operator/agent_infra/outer_loop.py`

### Understand evidence and failures
1. `operator/cre/runs/LAST_20_RUNS_EXHAUSTIVE.md`
2. `operator/cre/runs/<run_id>/manifest.json`
3. `operator/cre/runs/<run_id>/trace.jsonl`
4. `operator/agent_infra/diagnostic_reader.py`
5. `operator/agent_infra/healing_orchestrator.py`
6. `operator/agent_infra/decision_graph.py`
