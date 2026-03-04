# High-Value File Profiles

## `AGENTS.md`
- Role: repo-wide operating contract for agents
- Why it matters: defines architecture-critical files, imports, test commands, run monitoring rules, and subsystem purposes
- Read when: starting any non-trivial task in this workspace

## `.cursor/rules/concentric-study.mdc`
- Role: strict local rulebook for PhD-grade workflow
- Why it matters: upgrades the expected working method from "make a change" to "research, analyze, strategize, execute, reflect"
- Read when: deciding how much investigation is required before edits

## `operator/agent.py`
- Role: universal orchestrator for goal + URL driven execution
- Distinguishing feature: integrates capability routing and action-space-based planning rather than being tied to a single benchmark script
- Key collaborators: `operator/capability_router.py`, `operator/action_space.py`, `operator/agent_infra/recovery.py`, `operator/agent_infra/skill_library.py`

## `operator/agent_core.py`
- Role: macOS interaction kernel
- Distinguishing feature: converts logical/pixel coordinates into Quartz actions, manages screenshots, and performs visual assertions
- Why it matters: all high-level autonomy eventually collapses into this file's OS-level control path

## `operator/cre/test_excalidraw_covt.py`
- Role: flagship traced Excalidraw harness
- Distinguishing feature: shows the most complete inner-loop assembly of logging, tracing, planning, episodic memory, coordinate cache, evidence capture, and finalization
- Why it matters: best single file for understanding the end-to-end experiment

## `operator/agent_infra/trace_writer.py`
- Role: foundational trace subsystem
- Distinguishing feature: the rest of the infra stack depends on its schema
- Why it matters: manifest or trace schema changes ripple outward

## `operator/agent_infra/diagnostic_reader.py`
- Role: structured reader for completed runs
- Distinguishing feature: progressive disclosure instead of dumping raw JSONL
- Why it matters: turns trace data into a usable human and machine diagnostic interface

## `operator/agent_infra/healing_orchestrator.py`
- Role: failure classifier and action recommender
- Distinguishing feature: bridges raw evidence and next-step orchestration
- Why it matters: central to self-healing and escalation decisions

## `operator/agent_infra/recovery.py`
- Role: action execution with diagnosis and recovery
- Distinguishing feature: combines sanity checks, recovery actions, postcondition verification, rules injection, and trust-aware verification skipping
- Why it matters: this file operationalizes the repo's Reflexion-style self-healing behavior

## `operator/agent_infra/action_handlers.py`
- Role: concrete action implementation layer
- Distinguishing feature: very broad command surface including drawing primitives, palette control, page navigation, and task-specific drawing phases
- Why it matters: most visible behavior differences across tasks live here

## `operator/agent_infra/outer_loop.py`
- Role: dual-agent orchestration and cross-run memory management
- Distinguishing feature: subprocess execution, diagnosis, retries, reflections, rule extraction, and escalation output
- Why it matters: best file for understanding the project's "self-improving system" claim

## `operator/agent_infra/skill_library.py`
- Role: reusable skill memory with maturity gating and semantic retrieval
- Distinguishing feature: bridges successful historical traces into future task acceleration
- Why it matters: persistent learning depends on this store

## `operator/agent_infra/site_knowledge.py`
- Role: structured site affordance model
- Distinguishing feature: captures tool affordances, interaction rules, and button maps for supported sites
- Why it matters: this is the closest thing to explicit domain knowledge in the planner stack

## `operator/action_space.py`
- Role: typed schema for planner-visible actions
- Distinguishing feature: lifts the flat handler surface into a semantically organized action space
- Why it matters: key bridge between planning and execution

## `operator/capability_router.py`
- Role: task-to-capability activation layer
- Distinguishing feature: decides what subsystems should be active for a given site and goal
- Why it matters: explains why universal-run manifests include capability lists

## `operator/security/sanitizer.py`
- Role: prompt/tool safety filter
- Distinguishing feature: explicitly covers MCP-oriented attack classes, not only generic prompt injection
- Why it matters: defines safe autonomy boundaries

## `operator/security/credential_vault.py`
- Role: secret handling and HITL gate
- Distinguishing feature: separates automation competence from permission to perform sensitive actions
- Why it matters: this is where the project stops being fully autonomous by design

## `operator/cre/runs/LAST_20_RUNS_EXHAUSTIVE.md`
- Role: dynamic truth report over many real runs
- Distinguishing feature: exposes failure shapes, run diversity, and task-specific artifact patterns that source code alone does not reveal
- Why it matters: best single runtime evidence document in the repo
