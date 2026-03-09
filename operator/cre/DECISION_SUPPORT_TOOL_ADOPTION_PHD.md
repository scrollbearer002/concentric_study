# Decision Support Tool Adoption (PhD)

Date: `2026-03-05`

## 1. Purpose

This memo answers a different question from `operator/cre/CURSOR_MCP_LANDSCAPE_PHD.md`.

That earlier memo asked:
- which external Cursor MCPs or plugins fit this repo

This memo asks:
- which external software tools would most improve architectural decisions,
  safety decisions, observability, and overall repo discipline for
  `concentric_study`

In other words, this is a `whole-repo decision-support stack` memo, not an
`MCP marketplace` memo.

## 2. Local Baseline

Current active MCP state from `.cursor/mcp.json`:
- `context7`
- `concentric-health`
- `concentric-trace`

Local repo search shows that the main candidate tools discussed here are
currently present mostly as research references or backlog items, not as live
runtime integrations:
- `Playwright`
- `Langfuse`
- `Semgrep`
- `CodeScene`

There is no current live integration of:
- `Structurizr`
- `Import Linter`
- `OWASP Threat Dragon`
- `Log4brains`
- `MADR`
- `Phoenix`
- `OpenTelemetry`
- `SciTools Understand`

Interpretation:
- the repo already has strong native infrastructure
- new tools should be judged against actual gaps, not against a blank slate

## 3. Decision Criteria

An external tool is high-value for this repo only if it does at least one of the following:

1. makes architectural intent easier to preserve
2. makes design decisions more explicit and reviewable
3. improves observability or evaluation beyond current local traces
4. improves security assurance in a way the current Python runtime does not already cover
5. enables controlled comparison experiments without destabilizing the main runtime

Additional repo-specific constraints:
- low tool sprawl
- reversible adoption
- bounded security surface
- no duplication without a clear gain in rigor or maintainability
- preference for tools that complement `agent_infra`, not replace it

## 4. Research Verdict

The best external tools for this repo are not one category.
They break into five roles:

1. architecture and conformance
2. decision recording
3. observability and evaluation
4. security assurance
5. experimental comparison surfaces

The strongest conclusion is:

- `concentric_study` does **not** need a large new tool stack
- it **does** benefit from a small set of external tools that improve explicitness,
  calibration, and reviewability where the current repo is still weakest

## 5. Ranked Decision

## 5.1 Adopt Now

### A. `MADR` plus `Log4brains`

Why:
- the repo already produces many architecture and research memos
- what it lacks is a standardized, low-friction architecture-decision record flow
- this is the cleanest way to turn scattered PhD memos into a durable decision ledger

Why now:
- decision proliferation is already happening
- a decision record format is more urgent than another architecture visualization tool

Why this fits better than ad hoc markdown:
- `MADR` provides a structured ADR template
- `Log4brains` publishes ADRs as a browsable docs-as-code site and keeps them close to git history

Expected value:
- better decision traceability
- easier onboarding
- cleaner review of architectural choices
- lower risk of “same debate, different memo”

Adoption rule:
- use `MADR` as the template
- use `Log4brains` only if searchable publication is useful enough to justify the small node-based tool surface

### B. `Semgrep`

Why:
- it is the highest-value external security and policy tool that does not require re-architecting the runtime
- it can cover static rules, secrets, and supply-chain-relevant checks in one place

Why now:
- this repo already has a strong runtime security posture
- what it still lacks is a standardized external static assurance surface

Expected value:
- early detection of secret exposure
- policy checks for subprocess/network/security anti-patterns
- stronger evidence for future security assurance work

Adoption rule:
- start with narrow custom rules for this repo's real risk areas
- do not enable a broad noisy ruleset by default

## 5.2 Pilot Next

### C. `Structurizr`

Why:
- it is the best tool here for turning the current architecture corpus into a maintained architecture model rather than a set of prose artifacts

Why it is not in `Adopt Now`:
- the repo already has unusually good architecture documentation
- the next missing layer is not more diagrams alone, but making diagrams live and maintainable

Best use:
- C4 model for the main runtime
- explicit relationship between universal orchestrator, shared infra, security, and `cre` evidence surfaces
- dynamic views for canonical execution families

Pilot test:
- model only the current runtime surface first
- do not attempt the whole historical repo at once

### D. `Langfuse` or `Phoenix`, with `OpenTelemetry`

Why:
- the repo already has strong local tracing, but it lacks a standardized external observability and experiment-comparison layer

Why this is a pilot and not an immediate adoption:
- the project already has `TraceWriter`, `DiagnosticReader`, `BenchmarkEvaluator`, and `VerificationGate`
- external observability should prove incremental value before becoming permanent

Choice rule:
- choose `Langfuse` if richer prompt/eval/version visibility and external workflow UX are the priority
- choose `Phoenix` if open-source-first and self-host control are the priority
- use `OpenTelemetry` as the instrumentation base either way when possible

Pilot test:
- instrument only research/planning and verification calls first
- compare postmortem quality and experiment review quality against the current local-only stack

### E. `Import Linter`

Why:
- in abstract, it is one of the best fits for a Python repo with architecture boundaries
- it enforces import contracts such as layers and allowed dependencies

Why it is only a pilot here:
- this repo already has a custom architecture-conformance tool and tests
- replacing or duplicating that work without a net gain would be wasteful

When it becomes worth it:
- if the custom conformance logic becomes difficult to maintain
- if the team wants a more standardized contract syntax for module boundaries

Pilot test:
- express only the hottest boundaries first:
  - root-level shim imports
  - `agent.py` composition boundaries
  - `cre/` inward dependency discipline

### F. `Playwright`

Why:
- it is the best controlled browser experiment surface
- it can provide deterministic cross-checks against the current Safari/macOS path

Why it is not an adoption target yet:
- it is not a direct replacement for this repo's macOS GUI-agent substrate
- the immediate need is better decisions and architecture discipline, not a second primary runtime

Pilot test:
- compare a small number of site tasks on determinism, observability, and debugging value
- keep it sandboxed and explicitly non-canonical

## 5.3 Defer

### G. `OWASP Threat Dragon`

Why defer:
- it is a strong threat-modeling tool, but it will create the most value only once the repo begins a formal security assurance case
- right now the stronger next step is Semgrep plus bounded security review, then threat modeling after that

### H. `CodeScene`

Why defer:
- hotspot and socio-technical analysis are useful
- but this repo's most immediate issues are semantic/runtime conformance and evaluation calibration, not hotspot discovery

### I. `SciTools Understand`

Why defer:
- technically credible for static exploration and reverse engineering
- but the repo already has a strong internal architecture corpus and generated structural artifacts
- the incremental value is lower than Structurizr plus the current custom tooling

## 5.4 Not Worth Prioritizing Now

- any large expansion of always-on external MCPs
- overlapping repo-retrieval SaaS tools
- external tools that mostly replicate existing `agent_infra` evidence features without better calibration or review workflows

## 6. Final Adoption Order

If the repo adopts tools in the strongest order, it should be:

1. `MADR`
2. `Log4brains` if ADR publication is needed
3. `Semgrep`
4. `Structurizr`
5. `Langfuse` or `Phoenix`
6. `OpenTelemetry` instrumentation under the chosen observability layer
7. `Import Linter`
8. `Playwright`
9. `OWASP Threat Dragon`
10. `CodeScene`
11. `SciTools Understand`

Interpretation:
- decisions first
- security second
- architecture model third
- observability fourth
- experimental browser comparison after the decision and evidence layers are stronger

## 7. Why This Order Is Right For This Repo

This repo already has:
- strong local traces
- strong architecture memos
- strong internal evaluation and verification concepts
- a bounded active MCP set

It still lacks:
- standardized architecture decision records
- a standardized external static assurance surface
- a maintained architecture model
- calibrated external observability for prompts/evals

That means the correct order is not:
- more MCPs first
- more browser automation first
- more general repo analytics first

It is:
- make decisions explicit
- make security review stronger
- make architecture models maintainable
- only then widen observability and experimental surfaces

## 8. Relationship To Existing Memos

This memo does not replace:
- `operator/cre/CURSOR_MCP_LANDSCAPE_PHD.md`
- `operator/cre/EXTERNAL_MCP_GOVERNANCE_PHD.md`
- `operator/cre/HIGH_VALUE_TOOL_ROLLOUT_PHD.md`

Instead:
- `CURSOR_MCP_LANDSCAPE_PHD.md` answers which Cursor-facing tools fit
- `EXTERNAL_MCP_GOVERNANCE_PHD.md` answers how to govern external MCP adoption
- `HIGH_VALUE_TOOL_ROLLOUT_PHD.md` answers which internal runtime tools to wire first
- this memo answers which external software tools best improve decisions and whole-repo discipline

## 9. Bottom Line

The best overall external additions for `concentric_study` are:

- `MADR` plus optionally `Log4brains`
- `Semgrep`
- `Structurizr`
- `Langfuse` or `Phoenix` with `OpenTelemetry`

Everything else is second wave.

The strongest immediate move is not a new runtime or a new MCP.
It is to standardize decisions and strengthen review surfaces around the runtime you already have.

## 10. Sources

- MADR: https://adr.github.io/madr/
- Log4brains: https://github.com/thomvaill/log4brains
- Structurizr docs: https://docs.structurizr.com/
- Import Linter docs: https://import-linter.readthedocs.io/
- Semgrep docs: https://semgrep.dev/docs/
- OWASP Threat Dragon: https://owasp.org/www-project-threat-dragon/
- Langfuse docs: https://langfuse.com/docs
- Phoenix: https://phoenix.arize.com/
- OpenTelemetry Python docs: https://opentelemetry.io/docs/languages/python/
- Playwright docs: https://playwright.dev/docs/intro
- Playwright Trace Viewer: https://playwright.dev/docs/trace-viewer
- CodeScene product docs: https://codescene.com/product/codescene-for-open-source
- SciTools Understand: https://scitools.com/index
