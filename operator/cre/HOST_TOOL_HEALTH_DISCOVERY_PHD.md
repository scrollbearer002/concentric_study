# Host-Tool Health Discovery and Backend Selection (PhD)

## Executive Summary
`concentric_study` should add a first-class host-tool health layer before Phase 1 implementation proceeds. On this machine, the minimum substrate required for the current macOS + Safari runtime is healthy, but that health is currently implicit rather than modeled. The project venv can import the core macOS and imaging stack (`AppKit`, `Quartz`, `PIL`, `pydantic`, `google.genai`, `requests`, `numpy`, `scipy`, `imagehash`), while several augmentation backends remain absent (`sentence_transformers`, `macapptree`, `pyax`, `openai`).

That split is the design signal.

The health layer should not ask only "is Python installed?" or "does Safari exist?" It should explicitly model capability classes, choose the correct backend for each class, and fail closed when a required class is unhealthy for the current task.

## Environment Basis
System of interest:
- `concentric_study`

Local environment:
- macOS `26.3`, build `25D125`, `arm64`
- Cursor `2.5.26`
- Safari installed at `/Applications/Safari.app`
- repo runtime: `./operator/venv/bin/python`

Repo-specific evidence reviewed:
- `operator/capability_router.py`
- `operator/agent_infra/startup.py`
- `operator/agent_infra/action_contracts.py`
- `operator/agent_core.py`
- `operator/security/credential_vault.py`
- `operator/requirements.txt`
- `operator/cre/MASTER_TOOL_LIST_PHD.md`

Parent-environment evidence reviewed:
- `~/rust/operator/tool_status.py`
- `~/rust/operator/tool_catalog.yaml`
- `~/rust/cursor-nav/verify_nav_baseline.sh`
- `~/rust/operator/reset_cursor_baseline.sh`

## Local Findings
### Directly Supported Runtime Facts
Host/system tools callable now:
- `open`: present at `/usr/bin/open`
- `osascript`: present at `/usr/bin/osascript`
- `screencapture`: present at `/usr/sbin/screencapture`
- `security`: present at `/usr/bin/security`
- `git`: present at `/usr/bin/git`
- `rg`: present on PATH

Current machine checks passed:
- `osascript -e 'tell application "System Events" to return true'` returned `true`
- `screencapture -x <tempfile>` succeeded and wrote a file
- Safari and Cursor app bundles exist

### Python Runtime Split
System `python3` is not a valid proxy for repo readiness.

Using `/opt/homebrew/bin/python3`:
- missing `AppKit`, `Quartz`, `PIL`, `numpy`, `scipy`, `imagehash`, `sentence_transformers`, `macapptree`, `pyax`, `openai`

Using `./operator/venv/bin/python`:
- available: `AppKit`, `Quartz`, `PIL`, `pydantic`, `google.genai`, `requests`, `numpy`, `scipy`, `imagehash`
- missing: `sentence_transformers`, `macapptree`, `pyax`, `openai`

This is the most important environment-specific result. The health layer must validate the selected runtime, not an abstract host Python.

## What the Parent System Adds
The parent `~/rust` implementation contributes three design strengths:

1. **Capability classes**
- It models the environment in terms of classes such as `cursor_ui_automation`, `browser_automation`, `runtime_python`, `json_processing`, and `code_search`.

2. **Backend selection**
- It separates “what capability is needed” from “which concrete tool currently provides it.”
- Example: a class may prefer one backend but fall back to another if the first is unhealthy.

3. **Multi-step health checks**
- A tool is not healthy just because its binary exists.
- Checks include permission and behavioral probes, not only presence.

`concentric_study` currently has dynamic capability activation in `operator/capability_router.py`, but it does not yet have this explicit substrate-health gate.

## Primary-Source Research Basis
### Apple
- Accessibility permission is required for apps that control the Mac via accessibility APIs.
  - Source: Apple Support, "Allow accessibility apps to access your Mac"
  - https://support.apple.com/guide/mac-help/allow-accessibility-apps-to-access-your-mac-mh43185/mac
- Screen Recording / Screen & System Audio permissions affect screenshot and capture-based tooling.
  - Source: Apple Support, "Control access to screen and system audio recording on Mac"
  - https://support.apple.com/guide/mac-help/control-access-to-screen-and-system-audio-recording-on-mac-mchld6aa7d23/mac

### NIST
- Secure software practice requires defined environment assumptions, reproducible setup, and explicit verification of prerequisites.
  - Source: NIST SSDF SP 800-218
  - https://csrc.nist.gov/pubs/sp/800/218/final
- Baseline configuration is a first-class control surface, not an optional convenience.
  - Source: NIST SCAP / USGCB baseline configuration guidance
  - https://csrc.nist.gov/projects/security-content-automation-protocol/specifications/use-cases/usgcb

### Google SRE
- Health checking and monitoring should distinguish real service readiness from superficial liveness.
  - Source: Google SRE Book, Monitoring Distributed Systems
  - https://sre.google/sre-book/monitoring-distributed-systems/

### GUI-agent research
- Real computer-use agents fail on operational substrate and grounding, not only reasoning.
  - Source: OSWorld
  - https://arxiv.org/abs/2404.07972
- Correct current-screen / current-state understanding is sensitive to the real runtime substrate.
  - Source: UI-Hawk
  - https://aclanthology.org/2025.emnlp-main.920/
- Tighter visual-action coupling is necessary for robust GUI control.
  - Source: ShowUI
  - https://arxiv.org/abs/2411.17465

## Environment-Specific Interpretation
### Directly Supported
For this repo on this machine, the minimum required host substrate is:
1. selected Python runtime with pyobjc + imaging stack
2. AppleScript / System Events access
3. screenshot capture path
4. Safari launch/focus viability
5. app/window substrate suitable for front-window capture and native events

### Supported but Inferred
A formal host-health layer will reduce a meaningful portion of current startup ambiguity and failure triage overhead because the current runtime assumes those prerequisites implicitly.

### Unknown
We have not yet measured the optimal exact set of health probes for every task family. Some checks should be universal, while others should be activated conditionally by task.

## Recommended Capability Classes for `concentric_study`
### Required for the current universal macOS + Safari path
1. `runtime_python_selected`
- preferred backend: `./operator/venv/bin/python`
- checks:
  - interpreter exists
  - imports: `AppKit`, `Quartz`, `PIL`, `pydantic`, `google.genai`

2. `macos_ui_automation`
- backend: `osascript` + System Events
- checks:
  - `command -v osascript`
  - `osascript` can talk to System Events successfully

3. `native_event_backend`
- backend: pyobjc Quartz/Cocoa in selected runtime
- checks:
  - import `AppKit`, `Quartz`
  - instantiate a lightweight workspace/screen query without crashing

4. `screen_capture`
- backend: `screencapture`
- checks:
  - binary exists
  - temporary screenshot succeeds

5. `browser_target`
- backend: Safari app bundle + open/focus path
- checks:
  - Safari exists
  - `open -a Safari` is callable

### Required conditionally by task
6. `credential_backend`
- backend: macOS `security` CLI
- checks:
  - binary exists
  - only required when login/credential tasks are active

7. `site_capture_windowed`
- backend: current window capture path
- checks:
  - front-window capture returns a real file
  - only required for window-scoped verification flows

### Optional augmentation classes
8. `a11y_semantic_backend`
- preferred backends: `macapptree`, then `pyax`, then AppleScript fallback
- current machine state: augmentation backends missing, fallback still viable

9. `semantic_skill_embeddings`
- backend: `sentence_transformers`
- optional, not required for baseline runtime health

10. `legacy_openai_path`
- backend: `openai`
- optional/legacy only

## Why This Benefits This Environment
1. It will stop the repo from making silent substrate assumptions.
2. It will distinguish “task failed” from “machine not ready.”
3. It will let `capability_router` reason over proven host classes rather than only logical features.
4. It will give startup and recovery a stable machine-readiness contract.
5. It will make the current macOS + Safari path more explainable to operators and easier to demo.

## Design Recommendation
Implement the Phase 1 host-health layer as:
- a machine-readable catalog of capability classes and candidate backends
- a runtime checker that emits:
  - selected backend per class
  - passed/failed checks
  - missing required classes
  - task-conditioned readiness
- a fail-closed gate for required classes
- a degraded-mode report for optional classes

Do **not** copy the parent catalog literally.

Instead, adapt it to this repo’s real center of gravity:
- macOS native events
- Safari/site runtime
- screenshot and window capture
- selected venv runtime
- optional a11y and embedding augmentation

## Proposed Implementation Order
1. add tool catalog schema for `concentric_study`
2. implement health checker
3. integrate it ahead of `capability_router`
4. expose `--check-required` and class-selection behavior
5. feed its output into the future two-layer baseline/reset doctrine

## Stopping Rule
This memo stops here because the current evidence is saturated for the decision boundary:
- the host-health layer is justified
- the relevant local substrate is identified
- the parent design contribution is clear
- the main remaining unknown is implementation detail, not whether the layer is warranted
