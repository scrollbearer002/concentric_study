# PhD-Depth Audit: Initial Priority Areas

## Scope

This is the first audit pass using the project-understanding corpus. It focuses on:
- `operator/agent_infra/`
- `operator/cre/`
- `operator/agent.py`
- `operator/cre/test_excalidraw_covt.py`
- `operator/security/`

The aim is not style critique. The aim is architectural comprehension, risk exposure,
and evidence-backed next audit targets.

## Audit 1: `operator/agent_infra/`

### Context
- The inventory classifies 26 files under the `shared-infrastructure` subsystem.
- The subsystem dependency report shows 18 Python nodes and 20 intra-subsystem edges.
- The package export surface in `operator/agent_infra/__init__.py` re-exports a wide set of services.
- The subsystem has only 4 edges outward to the runtime orchestrator layer, compared with much heavier inward reuse.

### Findings
1. `operator/agent_infra/` is the most architecturally coherent part of the repo.
2. The package is dense but mostly disciplined: tracing, diagnosis, healing, learning, verification, and benchmarking are all grouped where a maintainer would expect them.
3. The export facade in `operator/agent_infra/__init__.py` increases ergonomics, but it also concentrates coupling and can hide module-boundary slippage.
4. `operator/agent_infra/recovery.py` and `operator/agent_infra/action_handlers.py` are the behavioral hinge files inside the package; any future audit should treat them as first-class architectural centers rather than utility modules.

### Consequences
- Positive: this folder is the best canonical starting point for architecture recovery.
- Risk: interface growth in `__init__.py` can make it harder to know which consumers truly need broad infra imports.
- Risk: internal density means schema changes in tracing or context objects can propagate quickly.

## Audit 2: `operator/cre/`

### Context
- `operator/cre/` outside `runs/` and `project_understanding/` currently contains 414 files.
- Artifact-class distribution in that surface is dominated by `evidence_image` with 289 files.
- The same folder also contains 45 research docs, 20 tests, 9 library modules, 8 design docs, multiple scripts, state stores, and site-knowledge files.

### Findings
1. `operator/cre/` is not a subsystem in the normal software-engineering sense. It is a mixed research workspace.
2. The folder's visual size significantly overstates the amount of executable logic because evidence images dominate the file count.
3. The folder does contain critical runtime-facing assets, especially `test_excalidraw_covt.py`, `test_kleki_bmw.py`, `ablation_harness.py`, and persistent JSON state files.
4. Any newcomer who reads `operator/cre/` as a flat code folder will form a distorted mental model of the project.

### Consequences
- Positive: the folder preserves research provenance and experimental history.
- Risk: discoverability is poor because code, state, evidence, and long-form analysis coexist without strong subfolder separation.
- Risk: architectural understanding can be drowned by screenshot noise unless the inventory or walkthrough is used.

## Audit 3: `operator/agent.py` and `operator/cre/test_excalidraw_covt.py`

### Context
- The subsystem dependency report identifies `operator/agent.py` as a top importer with out-degree 11.
- It identifies `operator/cre/test_excalidraw_covt.py` as the largest importer in the graph with out-degree 13.
- The source shows duplicated helper/function surfaces across the two files:
  - `_compute_region_phash`
  - `_validate_coord_cache_entry`
  - `_load_coord_cache`
  - `_execute_plan`
- The two files represent different orchestration centers: universal agent versus flagship traced harness.

### Findings
1. The repo currently has two real orchestration poles, not one.
2. These poles share important execution concerns but do not yet share a single canonical abstraction for several helpers.
3. This duplication is not just cosmetic. It creates a drift risk where verification, cache validation, or execution semantics can evolve differently across entrypoints.
4. The duplication is understandable historically because one file is a benchmark harness and the other is a generalized orchestrator, but the architectural pressure is now visible in the graph.

### Consequences
- Positive: the project can evolve the universal agent without destabilizing the benchmark harness immediately.
- Risk: correctness or observability fixes may land in one orchestrator path and not the other.
- Risk: future maintainers may not know which file is the canonical place to improve shared execution helpers.

## Audit 4: `operator/security/`

### Context
- The security subsystem has 3 Python files and only 2 internal edges.
- Cross-subsystem imports into security are limited.
- `operator/security/sanitizer.py` and `operator/security/credential_vault.py` are both marked high-value in the inventory.

### Findings
1. `operator/security/` is architecturally clean and intentionally narrow.
2. This narrowness is good: it indicates that security concerns remain boundary-focused rather than spread diffusely through the codebase.
3. The strategic importance of the folder is much higher than its file count suggests.
4. The right audit question here is not size but coverage: whether all sensitive flows actually route through these modules.

### Consequences
- Positive: the folder is easy to inspect deeply.
- Risk: because the boundary is small, bypasses elsewhere in the repo would be especially important to detect.

## Synthesis

### Strongest architectural strengths
- Clear existence of a canonical infrastructure package
- Rich run evidence and post-hoc diagnosis pipeline
- Explicit persistence for learning, trust, and reflection
- Security boundary that is small enough to reason about

### Highest-priority architectural risks
1. Mixed-concern sprawl in `operator/cre/`
2. Dual-orchestrator duplication between `operator/agent.py` and `operator/cre/test_excalidraw_covt.py`
3. Coupling concentration in `operator/agent_infra/__init__.py` and legacy shims

## Next Audit Moves

1. Perform a line-by-line duplication audit between `operator/agent.py` and `operator/cre/test_excalidraw_covt.py`.
2. Audit shim usage to determine whether callers can be migrated to canonical `agent_infra` imports.
3. Audit sensitive flows for direct credential or submission behavior that bypasses `operator/security/`.
4. Build a doc-to-code traceability matrix for `operator/cre/` so design claims can be tied directly to implementation files and run evidence.
