# Architecture Conformance Determinism (PhD)

## Environment Basis
- Repo: `concentric_study`
- Machine: local macOS arm64 environment
- Runtime under test: `operator/cre/project_understanding/tools/build_architecture_conformance.py`
- Scope: architecture-governance tooling only, not the Safari/web-agent runtime

## Problem
Once architecture conformance moved from a cached artifact model to a live-graph
model, the next invariant became:

> the live import graph must be deterministic for a fixed repo state.

Without that property, local and CI runs could disagree even when the source
tree is identical.

## Direct Local Evidence
- The conformance tool now rebuilds the graph live in
  `operator/cre/project_understanding/tools/build_architecture_conformance.py`.
- The graph builder previously consumed unsorted filesystem iteration from
  `iter_project_files()` in
  `operator/cre/project_understanding/tools/build_understanding_artifacts.py`.
- Repeated local graph builds on this machine produced the same digest, but that
  was an observation, not an enforced property.

## Hardening Applied
1. `iter_project_files()` now sorts repo paths by repo-relative path.
2. `build_import_graph()` now sorts Python paths before:
   - building the module map
   - traversing source files
3. `build_import_graph()` now sorts emitted edges by:
   - `from`
   - `to`
   - `import`
4. `operator/cre/test_architecture_conformance.py` now includes a regression
   test proving the graph is invariant to reversed input order.

## Why This Is the Correct Fix
The live import graph is a pure function of:
- the Python file set
- the file contents
- the module-resolution logic

So the deterministic contract should be enforced at the graph-builder boundary,
not patched later in the conformance layer.

## Primary Sources
- Python `sorted()` built-in:
  `https://docs.python.org/3/library/functions.html#sorted`
- Python `pathlib.Path.rglob()`:
  `https://docs.python.org/3/library/pathlib.html#pathlib.Path.rglob`
- Python `ast` module:
  `https://docs.python.org/3/library/ast.html`

## Interpretation
- `sorted()` provides an explicit ordering contract.
- `Path.rglob()` documents recursive enumeration but does not provide the
  ordering guarantee needed for deterministic conformance artifacts.
- `ast` parsing is deterministic for a fixed source file, so the remaining
  instability risk was file/input ordering, not parser behavior.

## Result
Architecture conformance is now:
- live
- deterministic by construction
- regression-tested against path-order variance
