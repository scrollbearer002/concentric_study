# Tool Cheat Sheet (PhD)

Derived from the definitive inventory in `operator/cre/MASTER_TOOL_LIST_PHD.md` and
`operator/cre/artifacts/master_tool_list.json`.

## Inventory Snapshot
- Total tool entries: `67`
- `current`: `47`
- `optional`: `7`
- `legacy`: `8`
- `historical_reference`: `5`

## Workflow Stages
| Stage | What happens here | Primary tools | Supporting tools |
|---|---|---|---|
| Intake and guardrails | Accept a goal, prove the local substrate is ready, classify the task, and gate unsafe actions before execution starts. | `agent.py`, `HostToolHealth`, `capability_router.py`, `action_space.py`, `InputSanitizer`, `CredentialVault`, `HITLGuard`, `inference_router.py` | `google-genai`, `pydantic`, `osascript`, `screencapture`, `open` |
| Research and reusable knowledge | Gather site/task context, recall prior successes, and compress usable context for the current run. | `ResearchAgent`, `SiteKnowledge`, `ExplorationLoop`, `ToolAffordance`, `InteractionRule`, `ButtonMapEntry`, `SkillLibrary`, `SemanticSkillIndex`, `Summarizer`, `ReflectionJournal`, `RulesStore` | `sentence-transformers` (optional dense retrieval) |
| Perception and grounding | Capture the state of the UI and fuse visual and accessibility signals into actionable elements. | `window_capture.py`, `visual_engine.py`, `a11y_engine.py`, `element_map.py` | `Pillow`, `screencapture`, `Quartz/CoreGraphics`, `Cocoa/AppKit`, `ImageHash` (optional pHash), `macapptree` (optional), `pyax` (optional), `numpy` (optional) |
| Execution and navigation | Convert grounded intent into actual clicks, keys, drags, and reusable web actions. | `agent_core.py`, `web_primitives.py`, `action_space.py` | `pyobjc-framework-Cocoa`, `pyobjc-framework-Quartz`, `open`, `osascript`, `Quartz/CoreGraphics`, `Cocoa/AppKit` |
| Trace, verify, and diagnose | Record what happened, check whether it actually worked, and extract why failures happened. | `TraceWriter`, `DiagnosticReader`, `VisualMonitor`, `VerificationGate`, `ActionTrustTracker`, `DecisionDependenceAnalyzer`, `HealingOrchestrator`, `BenchmarkEvaluator`, `TaskClaim` | `numpy` (optional pixel diffs), `scipy` (optional Beta quantiles) |
| Outer-loop adaptation | Retry with evidence, promote lessons into memory, and stop blind repetition. | `OuterLoop`, `ReflectionJournal`, `RulesStore`, `SkillLibrary` | Run artifacts under `operator/cre/runs/` |
| Legacy alternate path | Older but still repo-owned execution/model stack kept for fallback, audit, and historical comparison. | `CodexClient`, `VLMCoordinator`, `Hammerspoon kernel`, `operator/cre/codex_kernel.lua`, `operator/cre/showcase.sh`, `operator/cre/verify_kernel.sh`, `operator/cre/run_agent.sh`, `operator/cre/run_ultimate_tests.sh` | `requests`, `openai` |
| Historical references only | Mentioned in older docs, not part of the current repo-owned runtime. | `cliclick`, `hs.eventtap`, `hs.axuielement`, `hs.screen`, `cursor_ocr_map.py` | None |

## Canonical Install Sets
### Base
Use for the primary Gemini + native macOS runtime:

```bash
cd operator
./venv/bin/pip install -r requirements-base.txt
```

- `pyobjc-framework-Cocoa`
- `pyobjc-framework-Quartz`
- `google-genai`
- `pydantic`
- `Pillow`

### Optional
Add only when you want the extra capability:

```bash
cd operator
./venv/bin/pip install -r requirements-optional.txt
```

- `ImageHash`: pHash coordinate-cache and UI fingerprint validation
- `numpy`: pixel-diff comparison and vector math
- `scipy`: exact Beta posterior quantiles for trust tracking
- `sentence-transformers`: dense semantic skill retrieval
- `macapptree`: preferred accessibility backend, but may need environment-specific resolution
- `pyax`: alternate accessibility backend

### Legacy
Install only for the older Hammerspoon/OpenAI stack:

```bash
cd operator
./venv/bin/pip install -r requirements-legacy.txt
```

- `requests`: HTTP client used by `CodexClient`
- `openai`: alternate/older VLM path used by `VLMCoordinator`

### Compatibility umbrella
`operator/requirements.txt` is kept as the compatibility install path used by
older docs. It intentionally remains an umbrella file; the canonical split is:

- `requirements-base.txt`
- `requirements-optional.txt`
- `requirements-legacy.txt`

## Read This With
- Architecture flow: `operator/cre/TOOL_CONNECTIONS_DIAGRAM.md`
- Definitive inventory: `operator/cre/MASTER_TOOL_LIST_PHD.md`
