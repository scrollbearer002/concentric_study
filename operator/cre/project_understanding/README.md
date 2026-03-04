# Concentric Study Project Understanding Corpus

## Purpose

This directory is the PhD-level project-comprehension layer for `concentric_study`.
It exists to answer three questions with evidence instead of guesswork:

1. What does each major part of the repo do?
2. How do code, experiments, traces, and docs fit together?
3. Where should a human or agent look first when trying to understand or change the system?

The corpus follows the repo's own evidence-first rules in `AGENTS.md`,
`.cursor/rules/concentric-study.mdc`, and `operator/cre/PHD_DECISION_PRACTICE.md`.
It also follows repo-comprehension practice from dynamic-analysis and architecture
recovery literature: read structure, read behavior, then synthesize.

## Method

### Context
- The repo mixes runtime code, tests, research docs, screenshots, persistent state,
  and run histories.
- `operator/agent_infra/` is the canonical infrastructure package.
- `operator/cre/` is the most overloaded surface: it contains tests, many docs,
  evidence images, state files, scripts, and `runs/`.
- Several root-level Python files inside `operator/` are backward-compatible shims,
  not canonical implementations.
- The canonical repository now lives in git, but this corpus still distinguishes
  durable source artifacts from rebuildable local inventories and run byproducts.

### Decision
We document the repo in layers:
- machine-readable full inventory first
- folder map second
- runtime/data-flow explanations third
- deep profiles for high-value files fourth
- evidence/run-artifact interpretation fifth
- bibliography last

### Consequences
- Positive: the corpus scales to hundreds of files without flattening everything
  into one unreadable monograph.
- Positive: humans and agents can move from overview to detail without losing provenance.
- Trade-off: repeated evidence artifacts are explained by family plus per-file catalog row,
  not bespoke narrative for every screenshot.

## Reading Order

1. `AGENTS.md`
2. `.cursor/rules/concentric-study.mdc`
3. `operator/cre/PHD_DECISION_PRACTICE.md`
4. `operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`
5. `operator/cre/ESSAY_PROJECT_OVERLAP_PHD.md`
6. `operator/cre/DEEP_DIVE_ADDENDUM.md`
7. `operator/cre/runs/LAST_20_RUNS_EXHAUSTIVE.md`
8. `FOLDER_ATLAS.md`
9. `ARCHITECTURE_DIAGRAMS.md`
10. `SUBSYSTEM_DEPENDENCY_REPORT.md`
11. `RUNTIME_FLOWS.md`
12. `WALKTHROUGH_90_MINUTES.md`
13. `HIGH_VALUE_FILE_PROFILES.md`
14. `PHD_DEPTH_AUDIT.md`
15. `SECTION_1_ENTRYPOINT_DUPLICATION_AUDIT.md`
16. `SECTION_2_TRACEABILITY_MATRIX.md`
17. `SECTION_3_ARCHITECTURE_CONFORMANCE.md`
18. `SECTION_4_CONFORMANCE_ENFORCEMENT.md`
19. `SECTION_5_DYNAMIC_EXECUTION_ARCHITECTURE.md`
20. `PHD_EXTERNAL_RESEARCH_VALIDATION.md`
21. `PHD_PATH_REVALIDATION.md`
22. `EVIDENCE_AND_RUN_ARTIFACTS.md`
23. `BIBLIOGRAPHY.md`

## Generated Artifacts

These artifacts are rebuildable outputs. The canonical repository keeps the
builder scripts and the human-facing corpus, but snapshot inventories may be
excluded from version control when they only mirror the current local tree.
Regenerate them locally when you need a fresh inventory of the present workspace.

- `artifacts/repo_inventory.json`: one record per in-scope file
- `artifacts/file_catalog.csv`: spreadsheet-friendly inventory
- `artifacts/import_graph.json`: deterministic generated import-graph artifact refreshed only through explicit regeneration
- `artifacts/subsystem_dependency_report.json`: derived subsystem graph and dependency summary
- `artifacts/architecture_overview.mmd`: Mermaid source for the subsystem diagram
- `artifacts/entrypoint_duplication_audit.json`: focused overlap analysis for `operator/agent.py` and `operator/cre/test_excalidraw_covt.py`
- `artifacts/entrypoint_duplication_audit.csv`: spreadsheet-friendly duplication audit
- `artifacts/traceability_matrix.json`: validated claim-to-code-to-artifact correspondence matrix
- `artifacts/traceability_matrix.csv`: spreadsheet-friendly traceability matrix
- `artifacts/architecture_conformance.json`: explicit write-mode conformance artifact generated from the live repo graph
- `artifacts/architecture_conformance.csv`: spreadsheet-friendly write-mode conformance artifact
- `artifacts/dynamic_execution_architecture.json`: recovered execution-family, phase, and runtime-semantics view over live traces
- `artifacts/dynamic_transition_matrix.csv`: spreadsheet-friendly action transition matrix derived from `trace.jsonl`
- `artifacts/dynamic_execution_overview.mmd`: Mermaid source for the runtime-plane diagram
- `artifacts/folder_records.json`: machine-readable folder atlas backing data
- `artifacts/artifact_flow_matrix.csv`: producer/consumer map for persistent artifacts
- `artifacts/inventory_summary.json`: snapshot counts by class, subsystem, and extension
- `artifacts/bibliography_seed.json`: machine-readable seed list of external references

Generate or refresh them with:

```bash
python3 operator/cre/project_understanding/tools/build_understanding_artifacts.py
```

Conformance artifacts are now intentionally split:

```bash
python3 operator/cre/project_understanding/tools/build_architecture_conformance.py --check
python3 operator/cre/project_understanding/tools/build_architecture_conformance.py --regen-graph --write-artifacts
```

## How To Use This Corpus

- If you need the canonical runtime path, start with `RUNTIME_FLOWS.md`.
- If you need the subsystem graph first, start with `ARCHITECTURE_DIAGRAMS.md` and `SUBSYSTEM_DEPENDENCY_REPORT.md`.
- If you need a fast onboarding path, use `WALKTHROUGH_90_MINUTES.md`.
- If you need the first architecture-risk audit, use `PHD_DEPTH_AUDIT.md`.
- If you need the first sectioned follow-on audit, use `SECTION_1_ENTRYPOINT_DUPLICATION_AUDIT.md`.
- If you need verified doc-to-code correspondences and documentation-drift findings, use `SECTION_2_TRACEABILITY_MATRIX.md`.
- If you need measured architecture conformance against the intended layering, use `SECTION_3_ARCHITECTURE_CONFORMANCE.md`.
- If you need the live regression gate that prevents architecture drift from growing, use `SECTION_4_CONFORMANCE_ENFORCEMENT.md`.
- If you need the recovered runtime architecture from real `trace.jsonl` and `manifest.json` data, use `SECTION_5_DYNAMIC_EXECUTION_ARCHITECTURE.md`.
- If you need external-method validation from standards, SEI, and recent research, use `PHD_EXTERNAL_RESEARCH_VALIDATION.md`.
- If you need the strongest research-backed sequencing for what should happen next, use `PHD_PATH_REVALIDATION.md`.
- If you need ownership of a specific folder, start with `FOLDER_ATLAS.md`.
- If you need one-file accountability, use `artifacts/file_catalog.csv`.
- If you need to understand old screenshots or run directories, use
  `EVIDENCE_AND_RUN_ARTIFACTS.md`.
- If you need related-work grounding or thesis references, use `BIBLIOGRAPHY.md`.

## Research Basis

Internal sources:
- `operator/cre/PHD_DECISION_PRACTICE.md`
- `operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`
- `operator/cre/ESSAY_PROJECT_OVERLAP_PHD.md`
- `operator/cre/DEEP_DIVE_ADDENDUM.md`
- `DUAL_AGENT_LOOP_PLAN.md`
- `operator/cre/project_understanding/PHD_EXTERNAL_RESEARCH_VALIDATION.md`

External sources:
- ISO/IEC/IEEE 42010 and its architecture-description guidance
- SEI Views and Beyond and architecture reconstruction guidance
- Ferrante et al., program dependence graphs
- Cornelissen et al., dynamic-analysis-based program comprehension
- SHML, self-healing monitor-diagnose-adapt-test loops
- MindGuard, dependence-graph reasoning for trace attribution
- recent repository-understanding and architecture-recovery papers such as DependEval, RepoFusion, RepoScope, Code-Survey, and ArchAgent
- AppAgent, research-first study of environment and affordances
- ISO 42010 correspondence guidance, SEI modeling guidance, and CACM requirements tracing for doc-to-code traceability
- ADR practice from Cognitect and adr.github.io

The exact bibliography is in `BIBLIOGRAPHY.md`.
