# Read This Repo In 90 Minutes

## Goal

This is the fastest high-rigor reading path for someone who wants a real mental
model of `concentric_study` in one sitting. The walkthrough is designed using the
repo's own evidence-first rules plus repo-comprehension and onboarding research:
- start with governing intent
- move to architecture
- inspect canonical code paths
- validate understanding against runtime evidence

## Before You Start

Keep these files side by side:
- `operator/cre/project_understanding/README.md`
- `operator/cre/project_understanding/FOLDER_ATLAS.md`
- `operator/cre/project_understanding/RUNTIME_FLOWS.md`
- `operator/cre/project_understanding/artifacts/file_catalog.csv`

## 0-10 Minutes: Governance And Project Thesis

Read:
1. `AGENTS.md`
2. `.cursor/rules/concentric-study.mdc`
3. `operator/cre/PHD_DECISION_PRACTICE.md`

Questions to answer:
- What quality bar does this repo demand?
- What files are architecture-critical?
- What counts as evidence before a decision?

Expected outcome:
- You understand that this repo is explicitly research-driven and that architecture is documented, not improvised.

## 10-20 Minutes: What The Project Claims To Be

Read:
1. `operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`
2. `operator/cre/ESSAY_PROJECT_OVERLAP_PHD.md`
3. `operator/cre/DEEP_DIVE_ADDENDUM.md`

Questions to answer:
- What is the project's one-sentence definition?
- Which claims are already implemented versus aspirational?
- What task families and entrypoint variants exist?

Expected outcome:
- You know the difference between the flagship Excalidraw flow, the universal agent, and the experimental extensions.

## 20-35 Minutes: Folder And Subsystem Shape

Read:
1. `operator/cre/project_understanding/FOLDER_ATLAS.md`
2. `operator/cre/project_understanding/ARCHITECTURE_DIAGRAMS.md`
3. `operator/cre/project_understanding/SUBSYSTEM_DEPENDENCY_REPORT.md`

Questions to answer:
- Which folders are canonical code versus evidence or docs?
- Which subsystem imports which?
- Where is the real center of gravity in the repo?

Expected outcome:
- You can explain the layered architecture without opening random files.

## 35-55 Minutes: Canonical Execution Path

Read:
1. `operator/cre/test_excalidraw_covt.py`
2. `operator/agent_infra/recovery.py`
3. `operator/agent_infra/action_handlers.py`
4. `operator/agent_core.py`

Questions to answer:
- How does a task become a plan?
- How does a step become a trace event?
- Where do recovery and verification happen?
- Where does OS-level control actually occur?

Expected outcome:
- You can narrate the end-to-end inner loop of the main benchmark task.

## 55-65 Minutes: Cross-Run Intelligence

Read:
1. `operator/agent_infra/trace_writer.py`
2. `operator/agent_infra/diagnostic_reader.py`
3. `operator/agent_infra/healing_orchestrator.py`
4. `operator/agent_infra/outer_loop.py`
5. `operator/agent_infra/skill_library.py`

Questions to answer:
- How does the system learn from success?
- How does it reason over failure?
- When does it retry, escalate, or abort?

Expected outcome:
- You understand the difference between single-run execution and the dual-agent outer loop.

## 65-75 Minutes: Universalization And Security

Read:
1. `operator/agent.py`
2. `operator/capability_router.py`
3. `operator/action_space.py`
4. `operator/security/sanitizer.py`
5. `operator/security/credential_vault.py`

Questions to answer:
- How does the system generalize beyond one site?
- What capabilities are turned on per task?
- Where are the autonomy boundaries and HITL controls?

Expected outcome:
- You can explain how the project expands beyond a single Excalidraw script without losing safety constraints.

## 75-85 Minutes: Validate Against Runtime Evidence

Read:
1. `operator/cre/runs/LAST_20_RUNS_EXHAUSTIVE.md`
2. one successful run directory in `operator/cre/runs/`
3. one failed run directory in `operator/cre/runs/`
4. `operator/cre/project_understanding/EVIDENCE_AND_RUN_ARTIFACTS.md`

Questions to answer:
- What failure shapes recur in practice?
- Which artifact families belong to which execution stage?
- Do the docs match the actual run outputs?

Expected outcome:
- Your understanding is grounded in behavior, not just declared architecture.

## 85-90 Minutes: Final Synthesis

Do this:
- open `operator/cre/project_understanding/HIGH_VALUE_FILE_PROFILES.md`
- skim `operator/cre/project_understanding/PHD_DEPTH_AUDIT.md`
- scan `operator/cre/project_understanding/artifacts/file_catalog.csv`

Write down answers to these four prompts:
1. What is the canonical path for one task execution?
2. What persistent memories affect future runs?
3. Which two files are the highest-value audit targets next?
4. What part of `operator/cre/` is code, and what part is evidence?

If you can answer those without guessing, you have a working research-grade model of the repo.
