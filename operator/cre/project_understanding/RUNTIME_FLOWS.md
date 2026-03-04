# Runtime Flows

## Flow 1: Main Traced Excalidraw Execution

**Primary files:** `operator/cre/test_excalidraw_covt.py`, `operator/agent_infra/startup.py`, `operator/agent_infra/recovery.py`, `operator/agent_infra/action_handlers.py`, `operator/agent_infra/trace_writer.py`

1. `operator/cre/test_excalidraw_covt.py` initializes logging, task identity, trace writer, agent, episodic memory, and optional coordinate cache.
2. `operator/agent_infra/startup.py` launches Safari and captures the initial state.
3. The harness creates a context object carrying the agent, vision engine, trace writer, trust tracker, summarizer, and caches.
4. The harness generates a plan through `generate_action_plan()` or `generate_dynamic_plan()`.
5. `_execute_plan()` iterates action items and delegates each step to `operator/agent_infra/recovery.py`.
6. `operator/agent_infra/recovery.py` begins the trace step, performs optional pre-action sanity checks, calls the relevant action handler, and decides whether to verify, skip, retry, or recover.
7. `operator/agent_infra/action_handlers.py` executes the site-level action.
8. `operator/agent_infra/trace_writer.py` closes the step and finally writes `manifest.json`.

This is the canonical inner loop for the flagship Excalidraw task.

## Flow 2: Universal Multi-Site Orchestration

**Primary files:** `operator/agent.py`, `operator/capability_router.py`, `operator/action_space.py`, `operator/agent_infra/site_knowledge.py`, `operator/agent_infra/skill_library.py`

1. `operator/agent.py` accepts a URL and goal.
2. `operator/capability_router.py` decides which capabilities are needed for the task.
3. `operator/action_space.py` exposes a typed action schema for planning and execution.
4. `operator/agent.py` builds perception, retrieves subject/context knowledge, and asks the planner for a task-specific action plan.
5. The runtime optionally loads master-skill coordinates from `operator/cre/skill_library.json`.
6. Execution proceeds through the same recovery and trace machinery used by the Excalidraw harness.
7. The manifest for universal runs records a capability list, which is one of the clearest signals that this path differs from the main traced test harness.

## Flow 3: Diagnose, Heal, Escalate

**Primary files:** `operator/agent_infra/diagnostic_reader.py`, `operator/agent_infra/healing_orchestrator.py`, `operator/agent_infra/decision_graph.py`, `operator/agent_infra/outer_loop.py`

1. `operator/agent_infra/diagnostic_reader.py` loads `manifest.json` and `trace.jsonl` from a completed or partially completed run.
2. `operator/agent_infra/healing_orchestrator.py` classifies the failure into retry, adjust, escalate, or abort.
3. `operator/agent_infra/decision_graph.py` can build a causal graph from the trace and surface anomaly patterns.
4. `operator/agent_infra/outer_loop.py` decides the next cycle action.
5. If escalation is required, `operator/agent_infra/outer_loop.py` writes `ESCALATION.md` into the run directory and logs a reflection.

Research alignment:
- SHML supports the monitor-diagnose-adapt-test loop.
- MindGuard supports dependence-graph reasoning from traces.
- Ferrante et al. supports dependence thinking as a causal-analysis primitive.

## Flow 4: Learn Across Runs

**Primary files:** `operator/agent_infra/skill_library.py`, `operator/agent_infra/action_trust.py`, `operator/agent_infra/summarizer.py`, `operator/agent_infra/outer_loop.py`

1. A successful run can be ingested into `operator/cre/skill_library.json`.
2. Repeated success updates maturity from candidate to proven to master.
3. `operator/agent_infra/action_trust.py` updates `operator/cre/action_trust.json` so cheap, repeated actions can skip expensive verification.
4. `operator/agent_infra/outer_loop.py` records verbal lessons in `operator/cre/runs/reflection_journal.jsonl` and explicit rules in `operator/cre/runs/rules.jsonl` when available.
5. `operator/agent_infra/summarizer.py` compresses recent trajectory context for later VLM prompts.

This is the memory and efficiency layer. The project is not stateless.

## Flow 5: Evidence Production and Interpretation

**Primary files:** `operator/cre/runs/`, `operator/cre/runs/LAST_20_RUNS_EXHAUSTIVE.md`, `operator/cre/test_kleki_bmw.py`, `operator/cre/ablation_harness.py`

1. Run directories store machine-readable execution truth.
2. Long-form run summaries such as `operator/cre/runs/LAST_20_RUNS_EXHAUSTIVE.md` convert those artifacts into human-readable diagnostic narratives.
3. `operator/cre/test_kleki_bmw.py` produces a different evidence pattern from the Excalidraw harness, including iterative screenshots and annotations.
4. `operator/cre/ablation_harness.py` measures component contributions under controlled environment toggles.

The repo should be understood through both source and evidence. Reading code alone is insufficient.
