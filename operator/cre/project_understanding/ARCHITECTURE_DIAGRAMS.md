# Architecture Diagrams

## Method

These diagrams are derived from:
- `operator/cre/project_understanding/artifacts/import_graph.json`
- `operator/cre/project_understanding/artifacts/subsystem_dependency_report.json`
- `operator/cre/project_understanding/artifacts/artifact_flow_matrix.csv`
- `operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`
- `operator/cre/DEEP_DIVE_ADDENDUM.md`

The modeling approach follows architecture-recovery and program-comprehension work:
- RepoUnderstander for repository-level synthesis
- ArchAgent for multi-view architecture documentation
- Ferrante et al. for dependence reasoning
- Cornelissen et al. for combining structure with dynamic evidence

## Diagram 1: Subsystem Dependency Overview

This diagram is generated from the subsystem dependency report. It shows how the
Python import graph clusters at subsystem level.

```mermaid
flowchart LR
    cre_docs_and_artifacts["CRE Docs/Artifacts"]
    experiment_harnesses["Experiment Harnesses"]
    runtime_orchestrator["Runtime Orchestrator"]
    security["Security"]
    shared_infrastructure["Shared Infrastructure"]
    workspace_root["Workspace Root"]
    cre_docs_and_artifacts -->|1| runtime_orchestrator
    experiment_harnesses -->|28| runtime_orchestrator
    experiment_harnesses -->|2| security
    experiment_harnesses -->|21| shared_infrastructure
    runtime_orchestrator -->|13| runtime_orchestrator
    runtime_orchestrator -->|1| security
    runtime_orchestrator -->|13| shared_infrastructure
    security -->|2| security
    shared_infrastructure -->|4| runtime_orchestrator
    shared_infrastructure -->|20| shared_infrastructure
```

Interpretation:
- `experiment_harnesses` depends heavily on both `runtime_orchestrator` and `shared_infrastructure`.
- `shared_infrastructure` is internally dense but has limited outward dependency.
- `security` is intentionally small and lightly coupled.
- `cre_docs_and_artifacts` barely touches runtime code, which is correct for a doc-heavy surface.

## Diagram 2: Canonical Execution Stack

```mermaid
flowchart TD
    Goal[Goal / Task Prompt]
    Harness[operator/cre/test_excalidraw_covt.py]
    Startup[operator/agent_infra/startup.py]
    Planner[generate_action_plan / generate_dynamic_plan]
    Recovery[operator/agent_infra/recovery.py]
    Handlers[operator/agent_infra/action_handlers.py]
    Core[operator/agent_core.py]
    Trace[operator/agent_infra/trace_writer.py]
    RunDir[operator/cre/runs/<run_id>/]

    Goal --> Harness
    Harness --> Startup
    Harness --> Planner
    Planner --> Recovery
    Recovery --> Handlers
    Handlers --> Core
    Recovery --> Trace
    Trace --> RunDir
```

Interpretation:
- High-level intent becomes a plan in the harness layer.
- Recovery is the control hinge between planning and concrete action handlers.
- `agent_core.py` is the OS-level actuator.
- `trace_writer.py` turns every step into durable evidence.

## Diagram 3: Diagnose-Heal-Escalate Loop

```mermaid
flowchart TD
    Run[Completed or Failed Run]
    Reader[DiagnosticReader]
    Healer[HealingOrchestrator]
    DDG[DecisionDependenceAnalyzer]
    Outer[OuterLoop]
    Retry[Retry / Adjust Env]
    Esc[ESCALATION.md]
    Journal[reflection_journal.jsonl / rules.jsonl]

    Run --> Reader
    Reader --> Healer
    Run --> DDG
    DDG --> Healer
    Healer --> Outer
    Outer --> Retry
    Outer --> Esc
    Outer --> Journal
```

Interpretation:
- Post-run reasoning is a first-class subsystem, not an afterthought.
- The outer loop is where evidence becomes memory and policy.

## Diagram 4: Persistent Learning and Control State

```mermaid
flowchart LR
    Success[Successful Run] --> Skills[skill_library.json]
    Success --> Trust[action_trust.json]
    Failure[Failed Run] --> Journal[reflection_journal.jsonl]
    Failure --> Rules[rules.jsonl]
    Router[InferenceRouter] --> Routing[routing_state.json]
    Skills --> Agent[agent.py / harnesses]
    Trust --> Recovery[recovery.py]
    Journal --> Recovery
    Rules --> Recovery
    Routing --> Agent
```

Interpretation:
- The project has several persistent memories, not one.
- These files influence future execution decisions and must be treated as active state.

## Diagram 5: Knowledge and Perception Stack

```mermaid
flowchart LR
    A11y[a11y_engine.py]
    SoM[visual_engine.py]
    ElementMap[element_map.py]
    WebPrim[web_primitives.py]
    SiteKnowledge[agent_infra/site_knowledge.py]
    Planner[agent.py / test_excalidraw_covt.py]

    A11y --> ElementMap
    SoM --> ElementMap
    ElementMap --> WebPrim
    SiteKnowledge --> Planner
    WebPrim --> Planner
```

Interpretation:
- Perception is hybrid, not purely visual.
- Site knowledge sits beside perception rather than inside it.
