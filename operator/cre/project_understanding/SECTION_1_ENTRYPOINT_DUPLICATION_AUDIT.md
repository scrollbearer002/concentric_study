# Section 1: Entrypoint Duplication Audit

## 1. Purpose

This is the first staged follow-on audit after the initial corpus build.
It focuses narrowly on the two orchestration poles already identified as
high-risk for drift:
- `operator/agent.py`
- `operator/cre/test_excalidraw_covt.py`

The question is not "are these files similar in spirit?"
The question is:

**Where do they duplicate implementation responsibility in ways that can create
architectural drift, maintenance cost, or observability inconsistency?**

## 2. Research Basis

### 2.1 Architecture and conformance
- ISO/IEC/IEEE 42010 supports the use of multiple architectural views and model correspondences.
- SEI Architecture Reconstruction Guidelines support recovering structure from implementation artifacts before making architecture claims.
- Murphy and Notkin's Software Reflexion Models provide the classic source-vs-model conformance lens: once we know the intended layering, we can compare source reality against it.
- SEI's "Why Architecture Conformance Matters for Evolvable Systems" supports turning recovered structure into explicit conformance work rather than leaving it descriptive only.

### 2.2 Clone and drift analysis
- SourcererCC supports the importance of near-miss clone detection, not only exact-copy duplicate detection.
- That matters here because the highest-risk duplicates are not exact copies. They are structurally similar helpers that have already started to diverge.

### 2.3 Method chosen for this section
We use three evidence layers:
1. direct source reading of both files
2. generated overlap artifact at `operator/cre/project_understanding/artifacts/entrypoint_duplication_audit.json`
3. line-based comparison of overlapping top-level functions

This is deliberately narrower than a full clone-detection pass across the whole repo.
The goal is architectural clarity for the two main entrypoints first.

## 3. Data Sources

### 3.1 Primary repo evidence
- `operator/agent.py`
- `operator/cre/test_excalidraw_covt.py`
- `operator/cre/project_understanding/artifacts/entrypoint_duplication_audit.json`
- `operator/cre/project_understanding/artifacts/entrypoint_duplication_audit.csv`
- `operator/cre/project_understanding/artifacts/subsystem_dependency_report.json`

### 3.2 External references
- SourcererCC: https://arxiv.org/abs/1512.06448
- Software Reflexion Models: https://www.cs.ubc.ca/~murphy/papers/rm/fse95.html
- Why Architecture Conformance Matters: https://www.sei.cmu.edu/library/why-architecture-conformance-matters/

## 4. Overlap Surface

### 4.1 Shared top-level function names
The generated audit finds 5 shared top-level function names:
- `_compute_region_phash`
- `_execute_plan`
- `_load_coord_cache`
- `_trace`
- `_validate_coord_cache_entry`

### 4.2 Summary metrics
- common top-level functions: 5
- high-overlap functions by heuristic threshold: 3
- top shared orchestration risk remains the pair:
  - `operator/agent.py`
  - `operator/cre/test_excalidraw_covt.py`

## 5. Function-Level Findings

## 5.1 `_compute_region_phash`

### Evidence
- `operator/agent.py:148`
- `operator/cre/test_excalidraw_covt.py:119`
- structure similarity: `0.852`
- token similarity: `0.787`
- heuristic class: `near_miss_clone`

### Interpretation
The implementations are structurally very close.
They both compute a perceptual hash from a cropped screenshot region around cached coordinates.
The differences are mostly around:
- local coding style
- docstring depth
- crop/resizing details
- import style

### Risk
This is a classic near-miss utility clone.
If pHash semantics change in one file but not the other, coordinate-cache validity may diverge between the universal agent and the flagship harness.

## 5.2 `_load_coord_cache`

### Evidence
- `operator/agent.py:912`
- `operator/cre/test_excalidraw_covt.py:671`
- structure similarity: `0.777`
- token similarity: `0.749`
- heuristic class: `partial_duplicate`

### Interpretation
Both functions load resolved coordinates from the master skill path and materialize a cache keyed by action/color.
The implementations diverge mainly in:
- logging and user feedback
- stale-skill handling messaging
- exception reporting style

### Risk
The loading contract is semantically shared even though the implementations are not identical.
That means future changes to skill schema, stale-skill policy, or cache-key construction could drift across entrypoints.

## 5.3 `_trace`

### Evidence
- `operator/agent.py:95`
- `operator/cre/test_excalidraw_covt.py:37`
- structure similarity: `0.849`
- token similarity: `0.849`
- heuristic class: `partial_duplicate`

### Interpretation
This is a duplicated lightweight tracing helper with small formatting differences.

### Risk
Trace formatting or trace-call semantics can drift quietly, producing inconsistent debugging output across the two orchestrator paths.
The risk is not functional correctness first. The risk is observability drift.

## 5.4 `_validate_coord_cache_entry`

### Evidence
- `operator/agent.py:161`
- `operator/cre/test_excalidraw_covt.py:168`
- structure similarity: `0.328`
- token similarity: `0.343`
- heuristic class: `shared_responsibility`

### Interpretation
These functions no longer look like close clones.
They share responsibility but the test harness version has evolved further:
- adaptive tolerance behavior
- history tracking strategy
- richer logging and status output
- more explicit pHash comparison bookkeeping

### Risk
This is no longer a clone problem alone. It is a **semantic divergence** problem.
The same-named function suggests the same contract, but the implementations differ enough that they may no longer validate coordinates under the same assumptions.

## 5.5 `_execute_plan`

### Evidence
- `operator/agent.py:774`
- `operator/cre/test_excalidraw_covt.py:703`
- structure similarity: `0.391`
- token similarity: `0.465`
- heuristic class: `shared_responsibility`

### Interpretation
The names overlap, but the role has diverged.
- `operator/agent.py` resolves actions through `UnifiedActionSpace` and logs for the universal orchestrator.
- `operator/cre/test_excalidraw_covt.py` runs a benchmark/task harness with task-specific evidence capture and verification behavior.

### Risk
This is not a candidate for trivial deduplication.
The deeper issue is that both files still own orchestration logic, which keeps the repo in a dual-entrypoint architecture.

## 6. Architectural Interpretation

### Context
- The duplication artifact shows 3 high-overlap helper surfaces and 2 shared-responsibility surfaces.
- The subsystem dependency report shows both files are major import hubs.
- The code confirms that overlap is concentrated in utility helpers plus orchestration-adjacent logic.

### Decision
We should interpret the current state as:
1. **utility duplication** that is probably extractable
2. **semantic divergence** where same-named functions should either converge on a shared abstraction or be explicitly renamed by role
3. **intentional orchestration split** that should be documented as two different entrypoint responsibilities rather than treated as an accident

### Consequences
- Positive: this makes the next refactor target much clearer.
- Positive: not every overlap should be merged blindly.
- Risk: if the repo keeps same-named functions with diverging semantics, future maintenance will remain error-prone.

## 7. Extraction Candidates

## 7.1 High-confidence extraction candidates
These look like the best first extraction targets into a shared helper module:
- `_compute_region_phash`
- `_load_coord_cache`
- `_trace`

Reason:
- same responsibility
- measurable structural/token overlap
- lower conceptual coupling than orchestration methods

## 7.2 Not first-wave extraction candidates
These should not be merged first without deeper design work:
- `_execute_plan`
- `_validate_coord_cache_entry`

Reason:
- same names but deeper semantic divergence
- strong coupling to different execution contexts
- likely require a shared contract first, not just a shared helper file

## 8. What This Section Changes In The Corpus

This section adds two things that the earlier corpus only suggested:
1. a reproducible duplication artifact instead of only a narrative warning
2. a more precise separation between clone-style duplication and role-sharing divergence

## 9. Next Section

The next natural subsection after this audit is not a refactor yet.
It is a **doc-to-code traceability matrix** for the claims around:
- tracing
- recovery
- skill reuse
- verification
- security

That will let later conformance work compare intended architecture to actual implementation with stronger evidence than imports alone.
