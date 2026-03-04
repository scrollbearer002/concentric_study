# Answer Compliance Audit Layer (PhD)

## Purpose
This layer reduces the residual risk that repo rules are present but under-applied.
It does that by adding three operator-facing artifacts:
- a fixed checklist schema
- a JSONL compliance ledger
- a periodic review summary of misses

## Environment Basis
System of interest:
- `concentric_study`

Local environment:
- this repo already relies on `.cursor/rules/concentric-study.mdc` for behavioral governance
- there is no external runtime auditor for answers
- therefore the strongest practical enforcement available inside this repo is a visible checklist + append-only log + periodic review

Repo-specific constraints:
- this must not interfere with the strong runtime path
- this should remain outside the hot path for Safari/web-agent execution
- it should support, not replace, the existing environment-justification gate

## What This Adds
### 1. Fixed checklist schema
- `operator/cre/artifacts/environment_answer_compliance_template.json`

This records:
- task summary
- system of interest
- local environment
- repo-specific evidence
- stakeholder objective
- directly supported / inferred / unknown claims
- pass/fail/relaxed status
- failure reasons
- non-regression classification

### 2. Append-only compliance ledger
- `operator/cre/tools/log_environment_compliance.py`
- default log: `operator/cre/artifacts/environment_answer_compliance_log.jsonl`

Purpose:
- turn answer governance into an auditable trail
- make repeated misses visible instead of anecdotal

### 3. Periodic miss review
- `operator/cre/tools/review_environment_compliance.py`
- outputs:
  - `operator/cre/artifacts/environment_answer_compliance_review.json`
  - `operator/cre/ENVIRONMENT_COMPLIANCE_REVIEW_PHD.md`

Purpose:
- summarize pass/fail/relaxed rates
- surface repeated failure reasons
- create a simple review loop for drift

## Why This Fits This Repo
This repo already values:
- traces
- manifests
- benchmarks
- audits
- evidence-led decisions

This audit layer extends that discipline to the answer-governance boundary without touching:
- `operator/agent.py`
- `operator/agent_core.py`
- `operator/agent_infra/*` hot execution logic

That makes it a safe governance enhancement, not a runtime regression risk.

## Intended Use
Use the compliance logger for substantive turns involving:
- research memos
- architecture recommendations
- implementation plans
- non-trivial code changes
- high-stakes product or delivery advice

If the gate is satisfied:
- record `status=pass`

If the answer had to relax the gate:
- record `status=relaxed`
- give explicit reasons

If the answer materially failed the gate:
- record `status=fail`
- review the miss later rather than hiding it

## Non-Regression Classification
Each entry can classify the recommendation as:
- `not_applicable`
- `core enhancement with non-regression evidence`
- `isolated experimental branch to avoid weakening the core`

This aligns the new audit layer with the repo's bounded-growth rule.

## Why This Is Better Than More Wording Alone
A prose rule can still be forgotten.
A log plus review loop creates:
- visibility
- accountability
- trend detection
- a concrete surface for future hardening

## Limits
This is not an external blocker.
It does not prove perfect compliance.
It is still stronger than prose-only enforcement because it creates an observable record.

## Next Hardening Step
If later needed, the next stronger layer would be:
- an external answer-auditing system or CI-style validator for structured answer artifacts

That is deliberately not added now because the current goal is stronger local enforcement without contaminating the project's strong runtime path.
