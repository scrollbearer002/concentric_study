# Section 3: Architecture Conformance Checks

## 1. Purpose

This section moves the corpus from architecture recovery to architecture
conformance.

The question is not "what architecture can we describe from the repo?"
The question is:

**Does the live implementation still conform to the repo's intended layering,
canonical dependency chain, and canonical import surfaces?**

Primary generated artifacts:
- `operator/cre/project_understanding/artifacts/architecture_conformance.json`
- `operator/cre/project_understanding/artifacts/architecture_conformance.csv`
- `operator/cre/project_understanding/tools/build_architecture_conformance.py`

## 2. Research Basis

### 2.1 Source-vs-model comparison
- Murphy and Notkin's Software Reflexion Models provide the classical method:
  compare a high-level intended model against source-level dependency reality.
- This is the core method used in this section.
- Link: https://www.cs.ubc.ca/~murphy/papers/rm/fse95.html

### 2.2 Why conformance matters after recovery
- SEI's "Why Architecture Conformance Matters for Evolvable Systems" argues that
  architecture recovery is not enough; systems need explicit conformance checks
  so erosion is observed rather than normalized.
- Link: https://www.sei.cmu.edu/library/why-architecture-conformance-matters/

### 2.3 Architecture descriptions need correspondences
- ISO/IEC/IEEE 42010 treats architecture as a set of views plus correspondences.
- Conformance checking is one of the ways those correspondences are tested,
  rather than merely asserted.
- Link: https://www.iso-architecture.org/ieee-1471/

### 2.4 Recovery before conformance
- SEI's Architecture Reconstruction Guidelines support recovering the as-built
  architecture first, then evaluating it against the intended structure.
- That is why this section is staged after the subsystem report and
  traceability matrix, not before them.
- Link: https://www.sei.cmu.edu/library/architecture-reconstruction-guidelines-third-edition/

## 3. Intended Model Used For Checking

### 3.1 Repo-local intended layering
The intended model is taken from repo-local architectural claims, not invented by
this checker:
- `operator/agent_infra/__init__.py:5`
- `operator/agent_infra/__init__.py:7`
- `operator/agent_infra/__init__.py:9`
- `operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:69`
- `operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:173`
- `operator/cre/project_understanding/SUBSYSTEM_DEPENDENCY_REPORT.md:96`

### 3.2 Practical subsystem model
For conformance purposes, the repo is checked as five practical layers:
1. `experiment_harnesses`
2. `runtime_orchestrator`
3. `shared_infrastructure`
4. `security`
5. `cre_docs_and_artifacts`

### 3.3 Rule types
This section checks three kinds of conformance:
1. subsystem layering
2. canonical infra-chain directionality
3. canonical import-surface discipline

## 4. Method

### 4.1 Data source
All measurements are taken from:
- `operator/cre/project_understanding/artifacts/import_graph.json`
- the intended-architecture claims already documented in the corpus

The import graph is now treated as a generated artifact, not as the authority
for ordinary checking. The live conformance path rebuilds the graph in memory
from the current repo; `import_graph.json` is updated only through explicit
regeneration commands.

### 4.2 Rule semantics
- `conforms`: measured graph matches the intended rule
- `conforms_with_exceptions`: measured graph matches the intended rule except for explicitly justified boundary exceptions
- `drift`: the implementation diverges from the intended rule in live code
- `monitored_debt`: bounded, explicitly tolerated debt with owner, review date, rationale, and allowed scope
- `advisory`: not a violation, but a concentrated risk surface worth monitoring

### 4.3 Current measured result
- 7 conformance rules evaluated
- 4 `conforms`
- 1 `conforms_with_exceptions`
- 1 `monitored_debt`
- 1 `advisory`

## 5. Executive Findings

1. The repo is mostly conformant at subsystem level.
2. The main subsystem-level reverse dependency is narrow and localized: `operator/agent_infra/startup.py` and `operator/agent_infra/recovery.py` reach into runtime modules as boundary adapters.
3. The canonical `TraceWriter -> DiagnosticReader -> HealingOrchestrator -> OuterLoop` chain still conforms to the intended unidirectional model.
4. `security/` remains clean and self-contained.
5. The clearest live architecture debt is not subsystem layering but import-surface erosion: nine current imports still target compatibility shims instead of canonical `agent_infra` modules.
6. The `agent_infra` package facade is useful, but it is now a real coupling concentrator and should be treated as monitored architecture, not neutral convenience.

## 6. Rule-by-Rule Results

### 6.1 AC001: Shared infrastructure should not grow broad reverse dependencies into runtime code

#### Status
`conforms_with_exceptions`

#### Evidence
- `operator/agent_infra/startup.py -> operator/agent_core.py [agent_core]`
- `operator/agent_infra/startup.py -> operator/inference_router.py [inference_router]`
- `operator/agent_infra/startup.py -> operator/visual_engine.py [visual_engine]`
- `operator/agent_infra/recovery.py -> operator/agent_core.py [agent_core]`

#### Interpretation
This is the single largest subsystem-level departure from a strict one-way stack,
but it is still controlled.

The important point is that the reverse edges are not spread across the infra
package. They are concentrated in:
- `operator/agent_infra/startup.py`
- `operator/agent_infra/recovery.py`

That makes them boundary exceptions rather than generalized architectural erosion.

#### Consequence
The layering is still credible, but these two files should be treated as
architecture-sensitive adapters, not ordinary utilities.

### 6.2 AC002: Foundational infra modules remain independent

#### Status
`conforms`

#### Evidence base
- `operator/agent_infra/trace_writer.py`
- `operator/agent_infra/diagnostic_reader.py`
- `operator/agent_infra/skill_library.py`
- `operator/agent_infra/action_trust.py`

#### Interpretation
The most important base modules still match the intended architecture:
- no downward runtime dependency
- no security dependency
- no hidden layer leakage

This is a high-value result because these modules define the evidence and memory
substrate that later layers rely on.

### 6.3 AC003: The canonical infra chain remains unidirectional

#### Status
`conforms`

#### Evidence
- `operator/agent_infra/healing_orchestrator.py -> operator/agent_infra/diagnostic_reader.py [agent_infra.diagnostic_reader]`
- `operator/agent_infra/outer_loop.py -> operator/agent_infra/diagnostic_reader.py [agent_infra.diagnostic_reader]`
- `operator/agent_infra/outer_loop.py -> operator/agent_infra/healing_orchestrator.py [agent_infra.healing_orchestrator]`

#### Interpretation
No reverse edge violates the documented chain.
This matters because it means the trace/diagnose/heal/supervise progression is
still architecturally legible in code.

### 6.4 AC004 and AC005: Harnesses remain consumers; security remains isolated

#### Status
- `AC004`: `conforms`
- `AC005`: `conforms`

#### Interpretation
Two healthy architectural properties are still present:
- production layers do not import harness/test code
- the security subsystem does not fan outward into unrelated layers

These are strong signs that the repo has not collapsed into flat dependency chaos.

### 6.5 AC006: Canonical import-surface debt through compatibility shims

#### Status
`monitored_debt`

#### Evidence
- `operator/cre/test_excalidraw_covt.py -> operator/trace_writer.py [trace_writer]`
- `operator/cre/test_trace_writer.py -> operator/trace_writer.py [trace_writer]`
- `operator/cre/test_skill_library.py -> operator/skill_library.py [skill_library]`
- `operator/cre/test_outer_loop.py -> operator/trace_writer.py [trace_writer]`
- `operator/cre/test_trace_integration.py -> operator/trace_writer.py [trace_writer]`
- `operator/cre/test_healing_orchestrator.py -> operator/healing_orchestrator.py [healing_orchestrator]`
- `operator/cre/test_healing_orchestrator.py -> operator/trace_writer.py [trace_writer]`
- `operator/cre/test_diagnostic_reader.py -> operator/diagnostic_reader.py [diagnostic_reader]`
- `operator/cre/test_diagnostic_reader.py -> operator/trace_writer.py [trace_writer]`

#### Interpretation
This is the clearest live bounded debt found in Section 3.
The repo has already documented these root-level modules as compatibility shims,
which means continued direct imports are not neutral. They extend migration debt
and keep the architecture graph noisier than necessary.

This is not just stylistic cleanup. It affects conformance clarity because shim
imports make old surfaces look more canonical than they are.

This debt is now tracked explicitly in:
- `operator/cre/project_understanding/ARCHITECTURE_DEBT_REGISTER.md`

#### Consequence
The most justified next code change after Section 3 is still a shim-retirement
sweep in tests and harnesses, but the current state should be read as managed
debt, not as an unexplained regression.

### 6.6 AC007: `agent_infra` facade coupling is a monitored risk, not yet a violation

#### Status
`advisory`

#### Evidence
- `operator/capability_router.py -> operator/agent_infra/__init__.py [agent_infra]`
- `operator/agent.py -> operator/agent_infra/__init__.py [agent_infra]`
- `operator/cre/test_excalidraw_covt.py -> operator/agent_infra/__init__.py [agent_infra]`
- `operator/cre/test_kleki_bmw.py -> operator/agent_infra/__init__.py [agent_infra]`
- `operator/cre/test_canva_draw.py -> operator/agent_infra/__init__.py [agent_infra]`
- `operator/cre/test_login_flow.py -> operator/agent_infra/__init__.py [agent_infra]`

#### Interpretation
The facade is working as intended, but it concentrates import traffic.
That is not automatically bad. It becomes bad when maintainers lose sight of
which concrete module boundaries are actually being crossed.

This should be watched, not immediately treated as a defect.

## 7. Architectural Judgment

### Context
- The repo claims a layered architecture with a unidirectional infra chain.
- The static graph already showed mostly disciplined subsystem structure.
- The traceability matrix showed that the architecture docs are broadly honest,
  with a few bounded debt and drift points.

### Decision
The repo is **architecturally conformant in its main layering**, with two kinds
of qualified exceptions:
- justified boundary adapters inside `operator/agent_infra/`
- live shim-import monitored debt in tests and harnesses

### Consequences
- Positive: the architecture is more disciplined than many mixed research repos.
- Positive: the core tracing/diagnosis/healing/outer-loop stack is still structurally legible.
- Risk: shim imports keep the old surface alive and blur the canonical module map.
- Risk: `startup.py` and `recovery.py` can become erosion hotspots if more runtime dependencies accumulate there.

## 8. Highest-Value Next Actions

1. Migrate shim imports in tests and harnesses to canonical `agent_infra.*` imports.
2. Add a lightweight regression check so new shim imports fail the conformance audit.
3. Consider whether `operator/agent_infra/recovery.py:374` should read `GRADED_TRUST_THRESHOLD` through dependency injection or config instead of importing `agent_core` directly.
4. Keep `operator/agent_infra/startup.py` explicitly documented as a boundary adapter so future contributors do not generalize its runtime dependencies across the infra package.
