# Section 2: Doc-to-Code Traceability Matrix

## 1. Purpose

This section adds the missing correspondence layer between the repo's architectural
claims and the implementation/runtime evidence that should support them.

The question is not "does the documentation sound plausible?"
The question is:

**Which major claims in the repo's architecture documents are directly supported
by code, persistent artifacts, and observed runtime evidence, and where do the
docs simplify or drift from the implementation?**

Primary generated artifacts:
- `operator/cre/project_understanding/artifacts/traceability_matrix.json`
- `operator/cre/project_understanding/artifacts/traceability_matrix.csv`
- `operator/cre/project_understanding/tools/build_traceability_matrix.py`

## 2. Research Basis

### 2.1 View correspondence and mappings
- ISO/IEC/IEEE 42010 defines architecture descriptions in terms of views,
  viewpoints, and correspondences rather than one undifferentiated document.
- The ISO guidance on mappings between views supports explicit linkage from one
  representation to another, which is the exact methodological role of this
  matrix.
- Link: https://www.iso-architecture.org/ieee-1471/mv/

### 2.2 Modeling and traceability as comprehension tools
- SEI's "Software Modeling: What to Model and Why" argues that models are useful
  when they help readers move between different concerns and levels of detail.
- A traceability matrix is one such movement mechanism: architecture claim ->
  implementation point -> artifact evidence.
- Link: https://insights.sei.cmu.edu/library/software-modeling-what-to-model-and-why/

### 2.3 Traceability as lifecycle follow-through
- CACM's "Requirements Tracing" frames traceability as the ability to follow a
  concern across its lifecycle and representations.
- We adapt that principle here from requirement-level tracing to
  architecture-claim tracing.
- Link: https://cacm.acm.org/research/requirements-tracing/

### 2.4 Dynamic evidence is required, not optional
- Cornelissen et al.'s survey of program comprehension through dynamic analysis
  supports combining source reading with runtime evidence when understanding an
  evolving system.
- That matters here because `concentric_study` is a run-artifact-heavy repo.
- Link: https://ieeexplore.ieee.org/document/4634918

## 3. Method

### 3.1 Claim selection
This section does not try to trace every sentence in every markdown file.
It traces the repo's highest-value architectural claims first, using:
- `operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md`
- `AGENTS.md`
- the canonical implementation modules in `operator/agent_infra/` and `operator/security/`
- dynamic run evidence from `operator/cre/runs/LAST_20_RUNS_EXHAUSTIVE.md`

### 3.2 Evidence layers
Each claim is linked across up to four evidence layers:
1. source documentation claim
2. implementation line references
3. persistent artifact paths
4. runtime evidence or run-analysis evidence

### 3.3 Validation rule
The generator validates every local file/line reference in the matrix.
This matters because a traceability document that cannot validate its own
pointers is not a trustworthy correspondence artifact.

Current validation result:
- 9 claims audited
- 92 validated local references
- 0 invalid local references

### 3.4 Status semantics
- `verified`: the documentation claim is supported directly by the implementation and evidence
- `refined`: the documentation claim is directionally correct but materially simplified or incomplete relative to the implementation

## 4. Results Overview

### 4.1 Status summary
- `verified`: 7 claims
- `refined`: 2 claims
- `unsupported`: 0 claims in this audited set

### 4.2 Claims audited

| Claim ID | Status | Concern | Conclusion |
|---|---|---|---|
| `C001` | `verified` | observability | `TraceWriter` really does create per-run `trace.jsonl` and `manifest.json` artifacts |
| `C002` | `verified` | diagnostics | `DiagnosticReader` implements the documented Level 1/2/3 progressive-disclosure interface |
| `C003` | `verified` | healing | `HealingOrchestrator` classifies failed runs from structured trace/manifest evidence |
| `C004` | `refined` | outer-loop memory and escalation | docs describe the handoff correctly but understate that code also writes `ESCALATION.json`; `rules.jsonl` is implemented but not observed in this snapshot |
| `C005` | `verified` | learning | `SkillLibrary` enforces maturity gating and trusted-tier retrieval as described |
| `C006` | `refined` | verification control | docs simplify the trust logic; code now uses a Bayesian posterior bound rather than a naive 5-success threshold |
| `C007` | `verified` | recovery | the recovery path implements diagnose -> recover -> verify and injects reflection/rule context when available |
| `C008` | `verified` | security | `InputSanitizer` covers free-text sanitization plus MCP tool/schema defenses |
| `C009` | `verified` | credential safety | `CredentialVault` and `HITLGuard` form the documented sensitive-action boundary |

## 5. Detailed Findings

### 5.1 Observability and diagnostic substrate

### Context
The repo's core self-understanding claim is that it is trace-centric rather than
black-box. If that is wrong, most later architectural claims weaken immediately.

### Evidence
- `operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:22`
- `operator/agent_infra/trace_writer.py:84`
- `operator/agent_infra/trace_writer.py:107`
- `operator/agent_infra/trace_writer.py:155`
- `operator/agent_infra/diagnostic_reader.py:57`
- `operator/agent_infra/diagnostic_reader.py:87`
- `operator/agent_infra/diagnostic_reader.py:151`
- `operator/cre/runs/LAST_20_RUNS_EXHAUSTIVE.md:4`

### Assessment
This part of the architecture is strongly supported.
The trace writer, manifest writer, and progressive diagnostic reader all exist
exactly where the docs say they do, and the run-analysis corpus is explicitly
built from those artifacts.

### 5.2 Healing and supervisory orchestration

### Context
The next architectural question is whether the repo actually closes the loop
from run evidence to retry/escalation, or merely claims to.

### Evidence
- `operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:26`
- `operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:79`
- `operator/agent_infra/healing_orchestrator.py:105`
- `operator/agent_infra/outer_loop.py:308`
- `operator/agent_infra/outer_loop.py:379`
- `operator/agent_infra/outer_loop.py:509`
- `operator/agent_infra/outer_loop.py:637`
- `operator/agent_infra/outer_loop.py:664`

### Assessment
The supervisory architecture is real, but the docs currently compress two
important details:
- the handoff is hybrid, not markdown-only, because the code writes both
  `ESCALATION.md` and `ESCALATION.json`
- the rules store is implemented and wired, but `operator/cre/runs/rules.jsonl`
  is not present in the current workspace snapshot, so runtime evidence for that
  path is weaker than code evidence

### 5.3 Learning and verification control

### Context
The repo claims to learn from successful runs and to reduce verification cost
without abandoning safety.

### Evidence
- `operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:24`
- `operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:28`
- `operator/agent_infra/skill_library.py:178`
- `operator/agent_infra/skill_library.py:290`
- `operator/agent_infra/skill_library.py:383`
- `operator/agent_infra/action_trust.py:57`
- `operator/agent_infra/action_trust.py:102`
- `operator/agent_infra/action_trust.py:112`
- `operator/cre/skill_library.json`
- `operator/cre/action_trust.json`

### Assessment
The learning claim is verified directly.
The trust claim is verified in principle but refined in detail: the code is now
more rigorous than the docs. It no longer uses the simple threshold phrasing
found in some documentation; it uses a posterior lower-bound test.

This is not a contradiction in intent. It is a documentation-drift issue.

### 5.4 Recovery memory injection

### Context
The repo claims that failure diagnosis is not stateless and that lessons/rules
can be reinjected on later attempts.

### Evidence
- `operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:82`
- `operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:122`
- `operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:123`
- `operator/agent_infra/recovery.py:67`
- `operator/agent_infra/recovery.py:90`
- `operator/agent_infra/recovery.py:98`
- `operator/agent_infra/recovery.py:172`
- `operator/agent_infra/recovery.py:532`
- `operator/cre/runs/reflection_journal.jsonl`

### Assessment
The implementation supports episodic-memory and rule injection exactly as the
architecture claims. The only caution is evidentiary: the reflection journal is
present in this snapshot, while `rules.jsonl` has not yet been observed.

### 5.5 Security boundary claims

### Context
Security claims are easy to overstate in architecture docs. They need direct
code verification.

### Evidence
- `operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:30`
- `operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:102`
- `operator/cre/PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md:103`
- `operator/security/sanitizer.py:198`
- `operator/security/sanitizer.py:275`
- `operator/security/sanitizer.py:316`
- `operator/security/sanitizer.py:332`
- `operator/security/credential_vault.py:54`
- `operator/security/credential_vault.py:66`
- `operator/security/credential_vault.py:146`
- `operator/security/credential_vault.py:158`

### Assessment
These claims are well supported.
The sanitizer and credential/HITL boundary are small enough that the source can
be read directly and matched to the docs without much ambiguity.

## 6. Corrections To The Corpus

### 6.1 Escalation is dual-format
The corpus should now treat unresolved-run escalation as a dual-format artifact:
- `operator/cre/runs/<run_id>/ESCALATION.md`
- `operator/cre/runs/<run_id>/ESCALATION.json`

### 6.2 Action trust is statistically stricter than the prose suggests
The corpus should no longer summarize verification skipping as merely
"after 5 consecutive successes" without qualification.
That phrasing survives in some repo documents, but the current canonical code in
`operator/agent_infra/action_trust.py` uses a posterior-bound test.

### 6.3 Rules-store evidence is weaker than implementation evidence
The repo contains:
- code support for `rules.jsonl`
- documentation claiming `rules.jsonl`
- no observed `operator/cre/runs/rules.jsonl` file in this snapshot

That is not a design failure, but it is a real evidence asymmetry that future
runs should either materialize or the docs should qualify.

## 7. Consequences

### Positive
- The architecture docs are substantially more accurate than typical research repos.
- The core self-healing, tracing, and memory claims are implemented, not merely aspirational.
- The new matrix gives a reusable mechanism for future doc-drift checks.

### Risks
- Simplified prose can lag behind strengthened implementations, as seen in `action_trust.py`.
- Claims about runtime artifacts can silently become stronger in documentation than in observed evidence, as seen with `rules.jsonl`.

### Next section
The next justified step is architecture conformance checking:
compare the intended layering recovered by the corpus against the actual import
and ownership boundaries, using this traceability matrix as the claim baseline.
