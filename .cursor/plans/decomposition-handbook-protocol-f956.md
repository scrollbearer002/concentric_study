# Plan: Land the Decomposition Handbook Protocol

## 1) Objective and Constraints

- objective: Make the Decomposition Handbook a discoverable, runnable protocol in `concentric_study` without touching core runtime.
- hard constraints: no `agent_infra/` changes; no new alwaysApply `.mdc`; no invented Odyssey tree/data; follow doc-surface governance.
- soft constraints: match placement of peer method/protocol docs; keep AGENTS.md to one-line pointers.
- out of scope: Phase-4 interactive periodic table; Python coordinator runner in `agent_infra`; re-running the Odyssey decomposition.

## 2) Evidence Used

- docs placement: `operator/cre/DOC_SURFACE_GOVERNANCE_PHD.md`, `CANONICAL_RESEARCH_INDEX_PHD.md`, `cre_top_level_doc_registry.json`
- wiring pattern: `PHD_DECISION_PRACTICE.md` + `Use:` cites in `.cursor/rules/concentric-study.mdc`; `AGENTS.md` § Agent Workflow
- code cousins: OuterLoop / ResearchAgent exist; no WBS/funnel/dedup harness — docs + prompt stub only
- presentation: no Odyssey data files in repo → interactive Phase 4 deferred

## 3) Plan and Checkpoints

1. checkpoint: handbook + master prompt on disk
   - expected outcome: `operator/cre/DECOMPOSITION_HANDBOOK_PHD.md` + `artifacts/decomposition_handbook_master_prompt.txt`
   - pass: files present, handbook includes §0–§14 content + repo placement note
   - fail: missing sections or placed under `project_understanding/` / root
2. checkpoint: discoverability wiring
   - expected outcome: `Use:` in concentric-study.mdc; AGENTS.md protocol row; index + registry entry; plan-template bullet
   - pass: greppable path from rules/AGENTS/index
   - fail: new alwaysApply rule or full handbook body in AGENTS.md
3. checkpoint: non-regression
   - expected outcome: no changes under `operator/agent_infra/`
   - pass: `git diff --stat` shows zero agent_infra paths
   - fail: any core infra edit

## 4) Risk and Stop Conditions

- stop if: placement would require claiming Odyssey artifacts that are not in this workspace
- rollback: revert branch; handbook is additive-only
- downgrade: handbook-only commit without index/registry if registry regen fails

## 5) Verification

- `test -f operator/cre/DECOMPOSITION_HANDBOOK_PHD.md`
- `rg -n "DECOMPOSITION_HANDBOOK" AGENTS.md .cursor/rules/concentric-study.mdc operator/cre/CANONICAL_RESEARCH_INDEX_PHD.md`
- `git diff --name-only | grep agent_infra` → empty

## Classification

`isolated experimental branch to avoid weakening the core` — governance/method surface only until adherence is observed in live runs.
