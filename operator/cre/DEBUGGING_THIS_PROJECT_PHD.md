# Debugging This Project, PhD Style

## Executive Summary
`concentric_study` is not a normal backend service, library, or website. It is a layered macOS visual web-agent system with:

- host substrate assumptions
- browser/app state assumptions
- perception pipelines
- semantic and native interaction layers
- self-healing and verification layers
- architecture/governance layers
- a very large memo/artifact surface

The best way to debug this project is **not** to start from symptoms and guess. The best way is to debug it in a fixed order that matches the architecture actually present in the live repo.

The correct debugging order for this repo is:

1. **Substrate truth**
2. **Architecture/conformance truth**
3. **Task-surface truth**
4. **Perception truth**
5. **Interaction/action truth**
6. **Recovery/refinement truth**
7. **Verification truth**
8. **Artifact/reproducibility truth**
9. **Claim-discipline/documentation truth**
10. **Dead-weight / signal-to-noise truth**

That order is not stylistic. It is justified by the actual failure history of this repo:
- local environment drift can masquerade as task failure
- wrong-surface perception can masquerade as bad planning
- weak interaction semantics can masquerade as weak reasoning
- stale documentation can masquerade as architecture truth
- artifact mutation can hide real conformance regressions

## Environment Basis
This debugging doctrine is anchored to the live repo on this machine:

- Repo root: `/Users/christianpardo/Desktop/concentric_study`
- This path is not a Git checkout here; filesystem truth matters more than Git history
- Current full `cre/test_*.py` baseline:
  - `193 passed`
  - `3 skipped`
  - `5 warnings`
- Current architecture conformance pure check:
  - passes
  - graph digest: `baba844c630282c619b7184e7de120bc6283a11c85fdddb91882abedb120716b`
- Current host-tool health:
  - `all_required_ready: true`
  - selected backends:
    - `operator_venv_python`
    - `osascript_system_events`
    - `pyobjc_native_stack`
    - `screencapture_cli`
    - `safari_bundle`
    - `security_cli`

These are not assumptions. They were re-checked live before this memo was written.

## What This Project Actually Is
The current strong path is a universal-agent runtime built around:

- main path orchestration in `operator/agent.py`
- native macOS execution in `operator/agent_core.py`
- host/tool readiness in `operator/agent_infra/host_tool_health.py`
- trace logging in `operator/agent_infra/trace_writer.py`
- progressive failure reading in `operator/agent_infra/diagnostic_reader.py`
- recovery/refinement in `operator/agent_infra/recovery.py`
- monitoring in `operator/agent_infra/visual_monitor.py`
- final verification in `operator/agent_infra/verification_gate.py`
- causal postmortem analysis in `operator/agent_infra/decision_graph.py`
- perception via `operator/visual_engine.py`, `operator/a11y_engine.py`, `operator/element_map.py`
- browser/site actions through `operator/web_primitives.py`

This means debugging must honor the fact that a visible failure may have originated in a different layer than the one where it appeared.

## Layer 1: Substrate Truth
### What it is
The substrate is the machine-level capability set required before a task can even make sense:

- selected Python runtime
- AppleScript/System Events
- PyObjC native stack
- screenshot capture
- Safari presence
- credential backend

### Local code
- `operator/agent_infra/host_tool_health.py:1`
- `operator/agent_infra/host_tool_health.py:37`
- `operator/agent_infra/host_tool_health.py:69`
- `operator/agent.py:2315`

### Why debug here first
If this layer is wrong, downstream failures are misclassified. A site task can look broken when the machine substrate is the real cause.

### First checks
1. run host health summary
2. verify selected backends
3. check required class readiness
4. confirm full-screen Safari/window state when relevant

### Failure signatures
- no screenshots
- AppleScript failures
- focus/activation failures
- pyobjc import/runtime failures
- browser bundle not found

### What not to do
Do not start with prompt changes, selector changes, or visual heuristics if required substrate classes are not healthy.

### Research support
- NIST SSDF
- Apple Accessibility permissions guidance
- Apple screen-recording permissions guidance
- Google SRE monitoring principles

## Layer 2: Architecture / Conformance Truth
### What it is
The project has an explicit architecture-conformance system. It is there to separate real structural drift from anecdotal suspicion.

### Local code
- `operator/cre/project_understanding/tools/build_architecture_conformance.py`
- `operator/cre/test_architecture_conformance.py`
- `operator/cre/project_understanding/ARCHITECTURE_DEBT_REGISTER.md`

### Why debug here second
If the architecture layer is already lying, or if the conformance model is stale, then local reasoning about where a bug “should” live becomes unreliable.

### First checks
1. run pure conformance check
2. confirm no artifact mutation in check mode
3. inspect `AC006` monitored debt instead of treating it as vague drift
4. confirm graph digest and warnings

### Failure signatures
- reverse-layer edges
- facade/shim import growth
- stale import graph assumptions
- architecture docs stronger than live conformance truth

### What not to do
Do not patch runtime code to match outdated tests or stale docs before checking the live conformance layer.

### Research support
- ISO/IEC/IEEE 42010
- SEI Views and Beyond
- SEI Architecture Reconstruction Guidelines
- Reproducible Builds / Bazel hermeticity

## Layer 3: Task-Surface Truth
### What it is
The project often fails because the **page or app surface** is not what the system thinks it is.

Examples from this repo:
- wrong visible surface while Safari was frontmost
- leave-page dialog interference
- art site canvas not actually in the expected state
- Brilliant replay surface not matching the remembered blocked step

### Local evidence patterns
- `operator/cre/BRILLIANT_LIVE_TEST_LOG.md`
- `operator/cre/JSPAINT_DRAW_FAILURE_FORENSICS_PHD.md`
- `operator/cre/FRESH_LIVE_ART_BENCHMARK_PHD.md`

### Why debug here before perception internals
Many perception “failures” are actually task-surface mismatches:
- modal dialog present
- tool panel changed
- page layout moved
- stale recovered session
- unexpected composer state

### First checks
1. capture the live front window
2. verify page/app mode
3. verify no blocking overlays/dialogs
4. verify actual work area / canvas / composer state
5. verify current page is really the intended step/surface

### Failure signatures
- cursor seems “wrong” but actual page changed
- visual assertions mention the wrong site/surface
- drawing lands on the wrong layer or clipped region
- replay fails because the page reloaded to a different internal state

### What not to do
Do not infer the live surface from memory, URLs alone, or prior screenshots.

### Research support
- OSWorld
- SeeAct
- UI-Hawk
- ShowUI

## Layer 4: Perception Truth
### What it is
Perception in this repo is hybrid:
- screenshots / SoM visual grounding
- accessibility extraction
- fused element map
- window capture

### Local code
- `operator/visual_engine.py`
- `operator/a11y_engine.py`
- `operator/element_map.py`
- `operator/window_capture.py`

### Why debug this after task-surface truth
Perception is only meaningful if it is pointed at the right surface.

### First checks
1. confirm the screenshot is of the intended front window
2. confirm SoM/element overlays are aligned with the live page
3. confirm accessibility backend availability and coverage
4. confirm the canvas/work area geometry is computed from the real surface

### Failure signatures
- click target is visually correct in logs but wrong on screen
- overlay aligns to a stale crop
- actual canvas/export mismatch
- a11y tree is sparse or irrelevant

### What not to do
Do not trust screenshot-derived geometry over DOM/window geometry when the latter is available and more stable.

### Research support
- SeeAct
- OSWorld
- GUI-explorer

## Layer 5: Interaction / Action Truth
### What it is
The repo has two complementary action layers:
- site-agnostic semantic wrappers in `operator/web_primitives.py`
- native Quartz execution in `operator/agent_core.py`

### Local code
- `operator/web_primitives.py:68`
- `operator/web_primitives.py:95`
- `operator/web_primitives.py:120`
- `operator/agent_core.py:551`
- `operator/agent_core.py:636`
- `operator/agent_core.py:694`
- `operator/agent_core.py:844`

### Why debug here after perception
Many action failures are really perception failures. Once perception is true, action debugging becomes meaningful.

### First checks
1. identify the intended semantic action
2. verify it maps to a real current action-space primitive
3. confirm target coordinates/element identity from the live surface
4. check whether the action needs semantic edit behavior, not more force

### Failure signatures
- empty-slot fill works but occupied-slot edit does not
- sliders work but controlled widgets do not
- pointer events land but no state change occurs
- click path works in fixture but hangs in broader run finalization

### What not to do
Do not jump straight to stronger pointer force when the missing capability is actually semantic editing or commit behavior.

### Research support
- W3C UI Events
- WAI-ARIA keyboard/interface guidance
- MDN `getBoundingClientRect`
- SeeAct

## Layer 6: Recovery / Refinement Truth
### What it is
Recovery in this repo is not a generic retry loop. It is screenshot-backed diagnosis plus concrete corrective action plus postcondition verification.

### Local code
- `operator/agent_infra/recovery.py:42`
- `operator/agent_infra/recovery.py:59`
- `operator/agent_infra/recovery.py:119`
- `operator/agent_infra/recovery.py:196`
- `operator/agent_infra/recovery.py:238`

### Why debug this after action truth
If the action was ill-posed, recovery can only do so much. Once the action is understood, the question becomes whether refinement behaved intelligently.

### First checks
1. inspect the diagnostic screenshot and prompt
2. inspect the selected recovery action
3. check whether postcondition verification actually ran
4. inspect monitor checkpoints around the recovery

### Failure signatures
- diagnosis is correct but recovery action is `none`
- repeated identical failure with no state-changing repair
- recovery “passes” but task surface still wrong
- refinement loop stops before a meaningful retry

### What not to do
Do not accept “diagnosed correctly” as success if no corrective state transition followed.

### Research support
- Reflexion
- UI-Hawk
- VisionDirector

## Layer 7: Verification Truth
### What it is
This repo already distinguishes:
- action-effect checks
- monitor comparisons
- final `VerificationGate`

### Local code
- `operator/agent_infra/verification_gate.py:1`
- `operator/agent_infra/verification_gate.py:137`
- `operator/agent_infra/verification_gate.py:231`
- `operator/agent.py:2289`

### Why debug this before changing task logic
A surprising number of “bad task” reports are actually:
- weak checkpointing
- wrong comparison mode
- premature success claims
- final verification prompts that are too weak or too generic

### First checks
1. inspect final constraints decomposition
2. inspect checkpoint schedule if present
3. inspect whether verification used the correct reference or target-free mode
4. inspect deficiencies returned by the gate

### Failure signatures
- task obviously bad but run still says success
- task good but gate asks the wrong question
- major step drift not caught until the final screenshot

### What not to do
Do not weaken final verification to make runs look green.

### Research support
- CRAFT
- MCP-Atlas
- ScreenAgent

## Layer 8: Artifact and Reproducibility Truth
### What it is
This repo is evidence-heavy. Traces, manifests, screenshots, checkpoint artifacts, conformance outputs, and memos can help or hurt depending on whether they are reproducible and truthful.

### Local code
- `operator/agent_infra/trace_writer.py:21`
- `operator/agent_infra/trace_writer.py:71`
- `operator/agent_infra/diagnostic_reader.py:57`
- `operator/agent_infra/decision_graph.py:162`

### Why debug this before blaming the model
If the artifacts are stale, mutated, mis-scoped, or misleading, reasoning from them becomes unreliable.

### First checks
1. confirm the trace/manifest pair corresponds to the same run
2. confirm the screenshot is of the right layer/window
3. confirm conformance checks are pure read-only when in check mode
4. confirm exports actually match the visible canvas/page state

### Failure signatures
- saved artifact does not match visible page
- replay uses stale page state
- cropped canvas export lies about what was on screen
- check tooling writes the artifact it is verifying

### What not to do
Do not trust a single screenshot artifact if the page and the exported target disagree.

### Research support
- Reproducible Builds
- Bazel hermeticity

## Layer 9: Claim-Discipline / Documentation Truth
### What it is
This repo has a dense research/memo surface. Documentation can be an asset or a debugging trap.

### Current known issue class
We already found and corrected cases where docs overstated:
- universal enforcement
- architecture health
- trust-tracker behavior

### Why debug here
If the docs are ahead of the code, or stronger than the tests, engineers debug the wrong system.

### First checks
1. compare strong claims to live tests
2. compare docs to current imports/entrypoints
3. mark claims as:
   - directly supported
   - analogical support
   - intended/proposed

### Failure signatures
- docs say “always,” tests say “not everywhere”
- docs imply one universal path but demos/tests diverge
- summary docs duplicate or outrun authoritative docs

### What not to do
Do not treat polished memo language as runtime truth.

### Research support
- SEI architecture documentation and reconstruction guidance
- SEI technical debt identification

## Layer 10: Dead-Weight / Signal-to-Noise Truth
### What it is
This repo has a large artifact and memo surface outside `operator/cre/runs/`. Debugging gets slower when too much weakly-linked material competes with the strong core.

### Local evidence
The whole-project truth audit identified the biggest dead-weight risk surface as `operator/cre/` memo/demo/artifact density.

### Why this matters for debugging
Dead weight does not only waste space. It reduces debugging clarity by:
- multiplying candidate “truth” sources
- preserving stale screenshots and demos
- keeping low-authority summaries alive next to canonical docs

### First checks
1. identify whether a file is current, legacy, experimental, generated, or stale candidate
2. prefer authoritative docs and current artifacts
3. ignore orphaned demo outputs during first-pass debugging unless they are directly relevant

## Default Debugging Decision Tree
When a live task looks wrong, debug in this order:

1. **Substrate**: is the machine substrate healthy?
2. **Conformance**: is the architecture/governance layer truthful?
3. **Task surface**: is the page/app in the expected state?
4. **Perception**: are we seeing the correct thing, correctly?
5. **Action**: is the intended action the right primitive?
6. **Recovery**: did the refine loop actually change state?
7. **Verification**: is the gate asking the right question?
8. **Artifacts**: do the screenshots/exports/traces tell the truth?
9. **Docs**: is the claimed architecture actually current?
10. **Noise**: are stale artifacts/memos confusing the diagnosis?

## Repo-Specific Anti-Patterns Already Learned
1. **Deliverable substitution**
- writing a memo when the user asked for an operational result

2. **Wrong-surface debugging**
- treating a page-state mismatch as a logic bug

3. **Geometry afterthought**
- drawing before fitting to the real canvas

4. **Screenshot overreach**
- using brittle screenshot heuristics where geometry truth was available

5. **Force before semantics**
- escalating pointer force when the missing capability was an edit/replace semantic

6. **Stale-truth debugging**
- trusting cached artifacts or overstated docs over live checks

## Best Short Form
The best way to debug this project is:

- prove the machine
- prove the architecture
- prove the live surface
- prove the perception
- prove the action
- prove the recovery
- prove the verification
- prove the artifacts
- only then touch the docs or claim the system changed

If you reverse that order, you will waste time.

## References
### Architecture / documentation / debt
- ISO/IEC/IEEE 42010 architecture descriptions: `https://www.iso-architecture.org/ieee-1471/ads/`
- SEI Views and Beyond: `https://www.sei.cmu.edu/library/documenting-software-architectures-views-and-beyond-second-edition/`
- SEI Architecture Reconstruction Guidelines: `https://www.sei.cmu.edu/library/architecture-reconstruction-guidelines-third-edition/`
- SEI technical debt identification: `https://www.sei.cmu.edu/library/managing-technical-debt-identify-technical-debt-items/`
- SEI issue-tracker visibility of debt: `https://www.sei.cmu.edu/library/got-technical-debt-surfacing-elusive-technical-debt-in-issue-trackers/`

### Reproducibility / evidence discipline
- Reproducible Builds: `https://reproducible-builds.org/docs/why/`
- Reproducible Builds plans: `https://reproducible-builds.org/docs/plans/`
- Bazel hermeticity: `https://docs.bazel.build/versions/master/hermeticity.html`

### GUI-agent systems / runtime debugging
- OSWorld: `https://arxiv.org/abs/2404.07972`
- SeeAct: `https://arxiv.org/abs/2401.01614`
- AppAgent: `https://arxiv.org/abs/2312.13771`
- GUI-explorer: `https://arxiv.org/abs/2505.16827`
- MCP-Atlas: `https://arxiv.org/abs/2602.00933`
- OWASP GenAI/MCP guidance: `https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/`

### Environment / monitoring
- Google SRE monitoring: `https://sre.google/sre-book/monitoring-distributed-systems/`
- Apple Accessibility permissions: `https://support.apple.com/guide/mac-help/allow-accessibility-apps-to-access-your-mac-mh43185/mac`
- Apple screen recording permissions: `https://support.apple.com/guide/mac-help/control-access-to-screen-and-system-audio-recording-on-mac-mchld6aa7d23/mac`
