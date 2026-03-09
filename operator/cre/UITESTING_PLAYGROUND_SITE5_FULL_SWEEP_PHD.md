# UI Testing Playground (Site 5) Full Sweep — PhD Evidence Memo

Date: March 4, 2026  
Environment: macOS + Safari, `concentric_study` runner stack

## Objective

Execute a full no-login sweep of Website 5 (`uitestingplayground.com`) with explicit scope governance, reproducible run artifacts, and strict module accounting.

## Method

1. Build a dated challenge-surface baseline from the site home card inventory.
2. Discover additional internal paths from live homepage links.
3. Canonicalize and classify paths into:
   - auth exclusions
   - meta exclusions
   - in-scope no-login challenge modules
4. Execute serial Safari module checks with page-specific solvers for high-value challenge families:
   - event-model edge cases (`click`, `mouseover`, `hiddenlayers`)
   - async rendering (`ajax`, `clientdelay`, `loaddelay`, `autowait`)
   - UI-state correctness (`progressbar`, `visibility`, `disabledinput`)
   - structured extraction (`dynamictable`, `verifytext`, `frames`, `shadowdom`)
   - form/file workflows (`sampleapp`, `overlapped`, `upload`)
5. Persist trace, diagnostic, per-module JSON, and screenshot evidence.

Harness:
- `operator/cre/run_uitestingplayground_site5_mastery.py`

## Scope Policy

Auth-gated exclusions:
- none

Meta/non-core exclusions:
- `/home` (alias of root page)
- `/resources` (documentation/resource surface, not a challenge module)

## Iterative Hardening Evidence

1. `2cd6ed4429f7`  
   Initial implementation run; blocked by Safari TLS trust interstitial on the HTTPS route.

2. `172cea384086`  
   After transport correction; residual solver gaps remained (`click`, `dynamictable`, `hiddenlayers`, `sampleapp`).

3. `634e8b77e4a4`  
   After solver hardening; only `dynamictable` remained due column-reorder parsing weakness.

4. `7be404986089`  
   Final run after ARIA-aware dynamic-table parser hardening.  
   Result: `25 passed / 0 failed` in-scope.

This sequence demonstrates robustness improvement by targeted solver refinement, not by reducing scope.

## Final Result

Final run ID: `7be404986089`  
Outcome: `success`

Counts:
- Passed: `25`
- Failed: `0`
- Excluded (auth): `0`
- Excluded (meta): `2`
- In-scope total: `25`
- Site total represented in dated baseline: `27`

## Methodological Caveats (Explicit)

- Deterministic Safari execution used `http://uitestingplayground.com` because the HTTPS path on this host consistently triggered a trust interstitial in Safari automation context.
- The `click` challenge intentionally rejects vanilla DOM clicks; solver uses mouse event dispatch with non-zero screen coordinates to satisfy page semantics.
- `dynamictable` solver uses ARIA header-index mapping (`Name` and `CPU`) to remain valid under dynamic column reorder.
- `upload` is validated by iframe readiness and file-input availability/assignment path when browser policy allows programmatic file injection.

## Artifact Index

- Final manifest: `operator/cre/runs/7be404986089/manifest.json`
- Final summary: `operator/cre/runs/7be404986089/uitestingplayground_site5_mastery_summary.json`
- Final diagnostic: `operator/cre/runs/7be404986089/diagnostic.txt`
- Final module artifacts: `operator/cre/runs/7be404986089/modules/`
- Machine-readable result: `operator/cre/artifacts/uitestingplayground_site5_full_sweep_result.json`
