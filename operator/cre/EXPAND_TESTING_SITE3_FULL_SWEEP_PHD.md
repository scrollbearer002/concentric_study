# Expand Testing (Site 3) Full Sweep — PhD Evidence Memo

Date: March 4, 2026  
Environment: macOS + Safari, `concentric_study` runner stack

## Objective

Execute a full no-login sweep of Website 3 (`practice.expandtesting.com`) with explicit scope governance, artifacted evidence, and reproducible pass/fail accounting.

## Method

1. Build a dated module-surface baseline from the site’s homepage-linked graph.
2. Classify modules into:
   - auth-gated exclusions
   - non-core/meta exclusions
   - in-scope no-login UI benchmark modules
3. Run a serial Safari sweep over all in-scope modules.
4. Use deep solver checks for high-value interaction families and generic probes for remaining in-scope modules.
5. Persist per-module JSON + screenshots, full trace, summary, and diagnostic.

Harness:
- `operator/cre/run_expandtesting_mastery.py`

## Scope Policy

Auth-gated exclusions:
- `/basic-auth`
- `/digest-auth`
- `/login`
- `/otp-login`
- `/register`
- `/download-secure`

Non-core/meta exclusions include docs/API/assets and explicitly non-core pages for this benchmark phase.

## Iterative Evidence Trail

The final pass required iterative hardening:

1. `8c47cd8f3182`  
   First full attempt. Exposed timeout/scalability and strictness mismatches.

2. `fb800c3187b1`  
   Core-scope pass with residual solver mismatches.  
   Result: `47 passed / 6 failed` in-scope.

3. `57bf64cfbc40`  
   After first hardening pass.  
   Result: `52 passed / 1 failed` in-scope.

4. `313708867c3f`  
   Final run after generic-probe fix for low-control pages.  
   Result: `53 passed / 0 failed` in-scope.

This progression is essential evidence: success came from targeted solver and rubric improvements, not scope reduction.

## Final Result

Final run ID: `313708867c3f`  
Outcome: `success`

Counts:
- Passed: `53`
- Failed: `0`
- Excluded (auth): `6`
- Excluded (meta/non-core): `39`
- In-scope total: `53`
- Site total represented in the dated baseline: `98`

## Methodological Caveats (Explicit)

- Download validation uses page-link extraction with auxiliary HTTP retrieval fallback paths when UI download semantics are inconsistent.
- IFrame validation requires at least one accessible frame and does not force cross-origin TinyMCE or YouTube write access.
- Exit-intent and entry-ad pages permit content-presence fallback where modal rendering behavior differs from The Internet variants.

These caveats are recorded in module artifacts and were used to avoid false negatives from variant implementation details.

## Artifact Index

- Final manifest: `operator/cre/runs/313708867c3f/manifest.json`
- Final summary: `operator/cre/runs/313708867c3f/expandtesting_mastery_summary.json`
- Final diagnostic: `operator/cre/runs/313708867c3f/diagnostic.txt`
- Final module artifacts: `operator/cre/runs/313708867c3f/modules/`
- Machine-readable result: `operator/cre/artifacts/expandtesting_site3_full_sweep_result.json`

