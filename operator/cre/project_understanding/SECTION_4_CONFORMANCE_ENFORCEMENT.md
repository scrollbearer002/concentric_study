# Section 4: Conformance Regression Enforcement

## 1. Purpose

Section 3 established what the current architecture is doing.
This section makes that architecture testable.

The question is not "can we describe the current conformance state?"
The question is:

**How do we keep known architectural drift from silently growing while the repo continues to evolve?**

## 2. Research Basis

- Software Reflexion Models supports keeping a high-level model live against source reality, not treating conformance as a one-time comparison.
- SEI's "Why Architecture Conformance Matters for Evolvable Systems" supports ongoing conformance checking to prevent erosion.
- `operator/cre/project_understanding/PHD_PATH_REVALIDATION.md` identified conformance regression enforcement as the strongest next step before dynamic execution recovery or major refactoring.

## 3. Enforcement Policy

### 3.1 Hard-fail rules
The enforcement layer fails when any of these regressions appear:
- new reverse-layer dependencies from `shared_infrastructure` into `runtime_orchestrator` beyond the currently justified boundary adapters
- any foundational infra leak downward into runtime or security
- any violation of the canonical `TraceWriter -> DiagnosticReader -> HealingOrchestrator -> OuterLoop` chain
- any production-layer dependency on harness/test code
- any outbound dependency growth from the security subsystem

### 3.2 Frozen debt surfaces
The enforcement layer also freezes two currently tolerated debt surfaces so they cannot grow silently:
- compatibility-shim imports
- direct `agent_infra` facade imports

This means:
- removing existing debt is allowed
- adding new instances of that debt fails the gate

For shim imports, this is no longer reported as generic drift. It is tracked as
explicit monitored debt in `ARCHITECTURE_DEBT_REGISTER.md`, with an owner,
review date, rationale, and bounded allowed scope.

## 4. Implementation

Code added:
- `operator/cre/project_understanding/tools/build_architecture_conformance.py`
- `operator/cre/test_architecture_conformance.py`

Key public behavior:
- `python3 operator/cre/project_understanding/tools/build_architecture_conformance.py`
  runs the default pure `--check` path: live verification, no writes
- `python3 operator/cre/project_understanding/tools/build_architecture_conformance.py --check`
  explicitly runs the same pure read/verify path and exits non-zero on hard regressions
- `python3 operator/cre/project_understanding/tools/build_architecture_conformance.py --regen-graph`
  explicitly rewrites `artifacts/import_graph.json` from the live repo
- `python3 operator/cre/project_understanding/tools/build_architecture_conformance.py --write-artifacts`
  explicitly rewrites `architecture_conformance.json` and `architecture_conformance.csv`
- `pytest` coverage is provided by `operator/cre/test_architecture_conformance.py`

Determinism note:
- the conformance tool now rebuilds the import graph from live Python files on
  each run and normalizes file and edge ordering so CI and local runs evaluate
  the same graph for the same repo state
- verification is now pure by default: checking never rewrites the source-tree
  artifacts it is evaluating

## 5. What This Enforces Today

### Enforced strictly
- subsystem layering constraints
- foundational infra independence
- canonical infra-chain directionality
- harness consumption direction
- security isolation

### Enforced as bounded debt
- current shim-import caller set (`AC006`, reported as monitored debt rather than drift)
- current facade-import caller set

### Not yet enforced automatically
- dynamic execution/call-flow conformance
- scenario-based quality-attribute thresholds
- runtime evidence completeness rules across all run families

## 6. Why This Is The Right Stopping Point Before Further Refactoring

Because the repo still contains known shim debt, immediate broad refactoring would
risk mixing architectural repair with architectural measurement.

The enforcement layer changes that:
- it preserves the current intended model
- it stops known debt from growing
- it creates a stable baseline for the next stronger step: dynamic execution architecture recovery

## 7. Usage

From the repo root:

```bash
python3 operator/cre/project_understanding/tools/build_architecture_conformance.py --check
```

From the project test flow:

```bash
cd operator
./venv/bin/python -m pytest cre/test_architecture_conformance.py -v --tb=short
```

## 8. Next Step After Enforcement

The next strongest section is a dynamic execution architecture view derived from
actual runs and traces, not another static-only pass.
