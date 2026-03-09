# The Internet (Site 2) Full Sweep — PhD Evidence Memo

Date: March 4, 2026  
Environment: macOS + Safari, `concentric_study` runner stack

## Objective

Upgrade site 2 from a curated subset benchmark to a full public no-login sweep, with explicit exclusion policy and reproducible trace artifacts.

## Method

1. Enumerate the public example surface from `https://the-internet.herokuapp.com/`.
2. Exclude only auth-gated pages from the no-login track.
3. Execute each in-scope module serially in Safari under traced run control.
4. For each module, require a page-specific success predicate (not just page load).
5. Persist per-module evidence (JSON + screenshot) and full run trace.
6. Harden failures iteratively until pass/blocked state is explicit.

## Scope Classification

Auth-gated exclusions (explicitly out-of-scope for this track):

- `/basic_auth`
- `/digest_auth`
- `/login`
- `/download_secure`

In-scope modules executed: 41

## Final Result

Final run: `01f40bba880b`  
Outcome: `success`  

Coverage counts:

- Passed: `41`
- Failed: `0`
- Excluded (auth policy): `4`
- In-scope total: `41`
- Site total represented by this harness: `45` (41 in-scope + 4 excluded)

## Iterative Hardening Evidence

The harness reached full pass only after two failed/partial intermediate runs:

- `4e924c6a8999`: first full-sweep attempt, multiple rubric/hang issues discovered.
- `b959d3f96790`: second attempt, reduced to two residual failures.
- `01f40bba880b`: final attempt, full in-scope pass.

This sequence is important evidence that success came from genuine robustness improvements, not from reducing scope.

## What This Demonstrates

The stack can now complete a broad cross-section of website interaction families on a non-toy external benchmark:

- dynamic controls and delayed rendering
- iframe and nested frames manipulation
- context-menu and JavaScript dialog handling
- file upload and file retrieval workflows
- multi-window management in Safari
- shadow DOM reading
- redirect and status-code traversal
- sortable data and deep DOM traversal

## Methodological Caveats (Explicit)

- Geolocation uses native attempt first, then explicit injected provider fallback if browser prompt control is unavailable in-session.
- Download verification uses page-discovered URLs with auxiliary HTTP retrieval when Safari UI download automation is unreliable in-process.

These caveats are recorded as strategy-level metadata in module artifacts and are deliberate, transparent tradeoffs to keep the benchmark complete and reproducible.

## Artifact Index

- Run manifest: `operator/cre/runs/01f40bba880b/manifest.json`
- Run summary: `operator/cre/runs/01f40bba880b/the_internet_mastery_summary.json`
- Run diagnostic: `operator/cre/runs/01f40bba880b/diagnostic.txt`
- Per-module JSON + screenshots: `operator/cre/runs/01f40bba880b/modules/`
- Harness: `operator/cre/run_the_internet_mastery.py`

