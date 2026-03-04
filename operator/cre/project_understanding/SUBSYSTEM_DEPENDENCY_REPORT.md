# Subsystem Dependency Report

## Scope

This report is derived from `operator/cre/project_understanding/artifacts/import_graph.json`
and `operator/cre/project_understanding/artifacts/subsystem_dependency_report.json`.
It describes the static Python dependency shape of the repo at subsystem level.

## Executive Findings

1. The repo has three dominant executable subsystems: `runtime_orchestrator`, `shared_infrastructure`, and `experiment_harnesses`.
2. `experiment_harnesses` is the largest dependency consumer across subsystem boundaries.
3. `shared_infrastructure` is internally cohesive and comparatively disciplined: it is dense inwardly, but exports a stable service surface outward.
4. `security` is intentionally small and lightly imported, which is appropriate for a guardrail subsystem.
5. The static graph confirms that many `operator/cre/` Python files are harnesses around shared runtime code, not independent runtime systems.

## Subsystem Inventory

| Subsystem | Python nodes | Interpretation |
|---|---:|---|
| `experiment_harnesses` | 27 | Test and task-specific harnesses, including Excalidraw and Kleki flows |
| `shared_infrastructure` | 18 | Core tracing, diagnosis, recovery, learning, verification, and evaluation package |
| `runtime_orchestrator` | 17 | Runtime control, planning, perception, routing, and compatibility shims |
| `security` | 3 | Sanitization and credential/HITL boundary |
| `cre_docs_and_artifacts` | 3 | Small Python support footprint inside the larger `cre/` document/evidence surface |
| `workspace_root` | 1 | Standalone setup probe |

## Cross-Subsystem Edge Summary

| From | To | Edge count | Meaning |
|---|---|---:|---|
| `experiment_harnesses` | `runtime_orchestrator` | 28 | Harnesses lean heavily on the runtime control and perception layer |
| `experiment_harnesses` | `shared_infrastructure` | 21 | Harnesses reuse the canonical trace/recovery/memory stack |
| `runtime_orchestrator` | `shared_infrastructure` | 13 | Runtime code imports infra services rather than reimplementing them |
| `shared_infrastructure` | `runtime_orchestrator` | 4 | Infra still reaches into runtime-level modules for specific capabilities |
| `experiment_harnesses` | `security` | 2 | Security is invoked selectively, mostly for login/sensitive flows |
| `runtime_orchestrator` | `security` | 1 | Security remains a narrow boundary, not a pervasive coupling source |

## Internal Cohesion Signals

### `shared_infrastructure`
- 20 intra-subsystem import edges
- Interpretation: cohesive package with strong internal coordination
- Risk: internal density means interface changes can ripple quickly if not versioned carefully

### `runtime_orchestrator`
- 13 intra-subsystem import edges
- Interpretation: runtime code is interconnected but less dense than infra
- Risk: orchestration logic can accumulate too much responsibility if planning, perception, and execution remain fused

### `security`
- 2 intra-subsystem import edges
- Interpretation: minimal, controlled internal coupling
- Positive: easier to reason about safety boundaries

## Top Importers

| File | Out-degree | Meaning |
|---|---:|---|
| `operator/cre/test_excalidraw_covt.py` | 13 | Main harness is the broadest consumer of project capabilities |
| `operator/agent_infra/__init__.py` | 13 | Package export surface intentionally re-exports many infra modules |
| `operator/agent.py` | 11 | Universal orchestrator integrates many services directly |
| `operator/cre/test_login_flow.py` | 8 | Login flow pulls on multiple runtime/security pieces |
| `operator/capability_router.py` | 7 | Capability selection touches several runtime and infra components |

Interpretation:
- `operator/cre/test_excalidraw_covt.py` is not just a test. It is a large orchestration surface.
- `operator/agent.py` is a second major orchestration surface.
- Together, these two files represent the highest-risk sites for behavioral drift.

## Top Shared Dependencies

| File | In-degree | Meaning |
|---|---:|---|
| `operator/agent_infra/__init__.py` | 6 | Shared import facade for infra consumers |
| `operator/codex_client.py` | 6 | Frequently reused model-access client |
| `operator/agent_core.py` | 6 | Central execution kernel |
| `operator/trace_writer.py` | 6 | Shim still widely referenced by existing harnesses |
| `operator/inference_router.py` | 5 | Shared routing state/control layer |
| `operator/agent_infra/healing_orchestrator.py` | 5 | Widely reused failure-analysis service |
| `operator/agent_infra/skill_library.py` | 5 | Widely reused learning/memory service |

Interpretation:
- Compatibility shims still matter in the live graph.
- `agent_core.py` and `codex_client.py` are central runtime dependencies.
- Infra package exports are a convenience layer but also a coupling concentrator.

## Structural Interpretation

### Context
- The graph has 69 Python nodes and 105 import edges.
- Most meaningful cross-subsystem traffic flows from harnesses into runtime and infra.
- Infra outward dependency is limited relative to its inward reuse.

### Decision
We should read the repo as a layered system with these practical levels:
1. experiment harnesses
2. runtime orchestration and perception
3. shared infrastructure
4. security boundary
5. evidence/document layer

### Consequences
- Positive: this layering explains most of the repo with low ambiguity.
- Positive: it supports targeted audits and onboarding.
- Risk: two orchestrator centers exist, `operator/agent.py` and `operator/cre/test_excalidraw_covt.py`, which invites duplication and semantic drift.
- Risk: continued use of compatibility shims prolongs transition costs.

## Recommended Next Audits

1. Audit orchestration duplication between `operator/agent.py` and `operator/cre/test_excalidraw_covt.py`.
2. Audit infra boundary discipline, especially imports from infra back into runtime modules.
3. Audit shim retirement strategy so the graph can move toward canonical imports only.
