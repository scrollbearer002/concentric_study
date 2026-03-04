# Project Tooling Deep Audit (PhD)

## Summary
This audit goes beyond `AGENTS.md` and `operator/requirements.txt` to identify tooling that is:
- canonical in the current architecture
- optional but live in code
- legacy or fallback but still present in the repo
- invoked through macOS system commands rather than Python packages

## Canonical Internal Project Tools
Source of truth: `AGENTS.md`, `operator/agent_infra/__init__.py`, live imports in `operator/agent.py`.

### Shared infrastructure (`operator/agent_infra/`)
- `TraceWriter`
- `DiagnosticReader`
- `HealingOrchestrator`
- `SkillLibrary`
- `SemanticSkillIndex`
- `OuterLoop`
- `ReflectionJournal`
- `RulesStore`
- `ActionTrustTracker`
- `Summarizer`
- `SiteKnowledge`
- `ExplorationLoop`
- `ToolAffordance`
- `InteractionRule`
- `ButtonMapEntry`
- `ResearchAgent`
- `VisualMonitor`
- `VerificationGate`
- `DecisionDependenceAnalyzer`
- `BenchmarkEvaluator`
- `TaskClaim`

### Runtime/orchestration modules (`operator/`)
- `agent.py`
- `agent_core.py`
- `action_space.py`
- `capability_router.py`
- `window_capture.py`
- `visual_engine.py`
- `a11y_engine.py`
- `element_map.py`
- `web_primitives.py`
- `inference_router.py`
- `security/sanitizer.py`
- `security/credential_vault.py`

## External Python Packages Confirmed in Current Code
### Pinned in `operator/requirements.txt`
- `pyobjc-framework-Cocoa`
- `pyobjc-framework-Quartz`
- `google-genai`
- `pydantic`
- `Pillow`
- `requests`

### Optional or unpinned but imported in the repo
- `imagehash`
- `numpy`
- `scipy` (`scipy.stats.beta` in `operator/agent_infra/action_trust.py`)
- `sentence_transformers`
- `macapptree`
- `pyax`
- `openai`

## macOS / System Tools Confirmed in Code
Detected from `subprocess.run(...)` calls and runtime modules.
- `open`
- `osascript`
- `screencapture`
- Quartz/CoreGraphics event APIs
- Cocoa/AppKit APIs
- macOS Keychain via `security/credential_vault.py`

## Legacy / Fallback Tooling Still Present
These are not the primary current path, but they remain part of the project.
- `CodexClient` in `operator/codex_client.py`
- Hammerspoon HTTP kernel (`localhost:9999`) used by `CodexClient`
- `VLMCoordinator` in `operator/vlm_coordinator.py`
- OpenAI support in `operator/vlm_coordinator.py`
- Historical `cliclick` / `hs.eventtap` / `hs.axuielement` / `hs.screen` references in research and migration docs

## Tools Missed In The Earlier Short Answer
The earlier answer captured the main architecture, but it undercounted these real tools/components:
- `SemanticSkillIndex`
- `ReflectionJournal`
- `RulesStore`
- `SiteKnowledge`
- `ExplorationLoop`
- `ToolAffordance`
- `InteractionRule`
- `ButtonMapEntry`
- `action_space.py`
- `capability_router.py`
- `window_capture.py`
- `visual_engine.py`
- `CodexClient`
- `VLMCoordinator`
- `imagehash`
- `numpy`
- `scipy`
- `sentence_transformers`
- `macapptree`
- `pyax`
- `openai`
- `open`, `osascript`, `screencapture`

## Classification Notes
- `CodexClient` and `VLMCoordinator` are still real repo modules, but they are best treated as legacy/fallback paths relative to the current `agent.py` + `agent_core.py` path.
- `openai` is present in `operator/vlm_coordinator.py`, but the current documented primary model path is Gemini.
- `macapptree` and `pyax` are optional accessibility backends; AppleScript remains the lowest common fallback.
- `sentence_transformers` is optional. The skill library falls back to TF-IDF when it is missing.
- `imagehash`, `numpy`, and `scipy` are live code dependencies in some paths, but they are not pinned in the top-level `operator/requirements.txt`, so the requirements file understates the full tooling surface.

## Bottom Line
Yes, the earlier answer missed tools.

The most important misses were:
1. capability and planning infrastructure: `action_space.py`, `capability_router.py`, `window_capture.py`
2. episodic/site knowledge tooling: `RulesStore`, `ReflectionJournal`, `SiteKnowledge`, `ExplorationLoop`
3. optional-but-real dependencies: `imagehash`, `numpy`, `scipy`, `sentence_transformers`, `macapptree`, `pyax`, `openai`
4. legacy-but-still-present runtime tooling: `CodexClient`, `VLMCoordinator`, Hammerspoon kernel
5. macOS command-line tools actually invoked: `open`, `osascript`, `screencapture`
