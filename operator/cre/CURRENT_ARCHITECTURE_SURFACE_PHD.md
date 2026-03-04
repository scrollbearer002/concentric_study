# Current Architecture Surface (PhD)

## Scope
- Live repo: `/Users/christianpardo/Desktop/concentric_study`
- Excludes: `operator/venv/`, `operator/cre/runs/`

## Baseline Truth
- Python code surface excluding `venv` and `runs`: `114`
- Test baseline:
  - return code: `0`
  - summary: `193 passed, 3 skipped, 5 warnings in 22.30s`
- Architecture conformance:
  - return code: `0`
- Host-tool health:
  - return code: `0`

## Current Runtime Surface
The live current runtime is centered on:
- universal-agent path in `operator/agent.py`
- native execution in `operator/agent_core.py`
- typed action surface in `operator/action_space.py`
- shared infrastructure in `operator/agent_infra/`
- security in `operator/security/`
- perception/grounding in:
  - `operator/window_capture.py`
  - `operator/visual_engine.py`
  - `operator/a11y_engine.py`
  - `operator/element_map.py`
  - `operator/web_primitives.py`

## Counts
- `current`: `107`
- `optional`: `0`
- `legacy`: `16`
- `experimental`: `171`
- `generated`: `67`
- `historical_reference`: `55`
- `stale_candidate`: `510`

## Major role counts
- `artifact_or_demo`: `612`
- `documentation`: `129`
- `generated_support`: `62`
- `integration_current`: `25`
- `shared_infrastructure`: `20`
- `operational_script`: `19`
- `core_runtime`: `10`
- `audit_tooling`: `8`
- `legacy_runtime`: `7`
- `governance_tooling`: `5`
- `core_regression`: `5`
- `compatibility_only`: `5`
- `governance_regression`: `4`
- `integration_experimental`: `4`
- `legacy_compatibility`: `4`
- `security`: `3`
- `fixture`: `2`
- `support_path`: `2`

## Live current runtime modules
- `operator/a11y_engine.py` — Current runtime module for a11y engine.
- `operator/action_space.py` — Current runtime module for action space.
- `operator/agent.py` — Current runtime module for agent.
- `operator/agent_core.py` — Current runtime module for agent core.
- `operator/agent_infra/__init__.py` — Shared infrastructure module for   init  .
- `operator/agent_infra/action_allowlist.py` — Shared infrastructure module for action allowlist.
- `operator/agent_infra/action_contracts.py` — Shared infrastructure module for action contracts.
- `operator/agent_infra/action_handlers.py` — Shared infrastructure module for action handlers.
- `operator/agent_infra/action_trust.py` — Shared infrastructure module for action trust.
- `operator/agent_infra/benchmark_evaluator.py` — Shared infrastructure module for benchmark evaluator.
- `operator/agent_infra/decision_graph.py` — Shared infrastructure module for decision graph.
- `operator/agent_infra/diagnostic_reader.py` — Shared infrastructure module for diagnostic reader.
- `operator/agent_infra/healing_orchestrator.py` — Shared infrastructure module for healing orchestrator.
- `operator/agent_infra/host_tool_health.py` — Shared infrastructure module for host tool health.
- `operator/agent_infra/outer_loop.py` — Shared infrastructure module for outer loop.
- `operator/agent_infra/recovery.py` — Shared infrastructure module for recovery.
- `operator/agent_infra/research_agent.py` — Shared infrastructure module for research agent.
- `operator/agent_infra/site_knowledge.py` — Shared infrastructure module for site knowledge.
- `operator/agent_infra/skill_library.py` — Shared infrastructure module for skill library.
- `operator/agent_infra/startup.py` — Shared infrastructure module for startup.
- `operator/agent_infra/summarizer.py` — Shared infrastructure module for summarizer.
- `operator/agent_infra/trace_writer.py` — Shared infrastructure module for trace writer.
- `operator/agent_infra/verification_gate.py` — Shared infrastructure module for verification gate.
- `operator/agent_infra/visual_monitor.py` — Shared infrastructure module for visual monitor.
- `operator/capability_router.py` — Current runtime module for capability router.
- `operator/element_map.py` — Current runtime module for element map.
- `operator/inference_router.py` — Current runtime module for inference router.
- `operator/security/__init__.py` — Security module for   init  .
- `operator/security/credential_vault.py` — Security module for credential vault.
- `operator/security/sanitizer.py` — Security module for sanitizer.
- `operator/visual_engine.py` — Current runtime module for visual engine.
- `operator/web_primitives.py` — Current runtime module for web primitives.
- `operator/window_capture.py` — Current runtime module for window capture.
