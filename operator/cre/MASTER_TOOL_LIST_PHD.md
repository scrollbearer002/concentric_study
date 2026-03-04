# Master Tool List (PhD)

## Scope
This is the single definitive tool inventory for the project as of February 28, 2026. It reconciles:
- `AGENTS.md`
- `operator/requirements.txt`
- live imports across `operator/**/*.py`
- subprocess/system-tool usage across `operator/**/*.py`
- operational scripts and legacy kernel files under `operator/cre/`
- historical references found during the oldest-to-newest file pass

Statuses used in this inventory:
- `current`: canonical and live in the current architecture or hot path
- `optional`: live in code, but only used when installed, enabled, or available
- `legacy`: still present and usable, but not the primary current path
- `historical_reference`: referenced in docs or experiments, but not a current project-owned runtime tool

Requirement coverage values:
- `pinned_in_requirements`: explicitly listed in `operator/requirements.txt`
- `missing_from_requirements`: imported or used in code but not listed in `operator/requirements.txt`
- `not_applicable`: internal module, script, system tool, or historical reference

## Definitive Master List
| Tool | Category | Status | Requirement coverage | Primary location | Notes |
|---|---|---|---|---|---|
| `TraceWriter` | internal_module | `current` | `not_applicable` | `operator/agent_infra/trace_writer.py` | Structured JSONL trace and manifest writer. |
| `DiagnosticReader` | internal_module | `current` | `not_applicable` | `operator/agent_infra/diagnostic_reader.py` | Progressive disclosure trace reader. |
| `HealingOrchestrator` | internal_module | `current` | `not_applicable` | `operator/agent_infra/healing_orchestrator.py` | Failure classification and corrective recommendation layer. |
| `SkillLibrary` | internal_module | `current` | `not_applicable` | `operator/agent_infra/skill_library.py` | Skill persistence, maturity, coord reuse. |
| `SemanticSkillIndex` | internal_module | `current` | `not_applicable` | `operator/agent_infra/skill_library.py` | Semantic retrieval layer over skills. |
| `OuterLoop` | internal_module | `current` | `not_applicable` | `operator/agent_infra/outer_loop.py` | Monitor-diagnose-adapt-test orchestration. |
| `ReflectionJournal` | internal_module | `current` | `not_applicable` | `operator/agent_infra/outer_loop.py` | Episodic memory over failures and lessons. |
| `RulesStore` | internal_module | `current` | `not_applicable` | `operator/agent_infra/outer_loop.py` | Extracted reusable failure rules. |
| `ActionTrustTracker` | internal_module | `current` | `not_applicable` | `operator/agent_infra/action_trust.py` | Verification-skip trust tracker. |
| `Summarizer` | internal_module | `current` | `not_applicable` | `operator/agent_infra/summarizer.py` | Context folding and trace summarization. |
| `ResearchAgent` | internal_module | `current` | `not_applicable` | `operator/agent_infra/research_agent.py` | Pre-execution subject/method/tool research integrated in the universal-agent path; not universal across every entrypoint. |
| `HostToolHealth` | internal_module | `current` | `not_applicable` | `operator/agent_infra/host_tool_health.py` | Environment-readiness gate: host-tool health discovery and backend selection before capability activation. |
| `VisualMonitor` | internal_module | `current` | `not_applicable` | `operator/agent_infra/visual_monitor.py` | Background screenshot monitor and timeline, integrated in the universal-agent path and selected demos/tests. |
| `VerificationGate` | internal_module | `current` | `not_applicable` | `operator/agent_infra/verification_gate.py` | Post-execution verification layer implemented in the universal-agent path and selected demos/tests. |
| `DecisionDependenceAnalyzer` | internal_module | `current` | `not_applicable` | `operator/agent_infra/decision_graph.py` | Causal trace analysis and anomaly detection. |
| `BenchmarkEvaluator` | internal_module | `current` | `not_applicable` | `operator/agent_infra/benchmark_evaluator.py` | Claims-based evaluation and scoring. |
| `TaskClaim` | internal_module | `current` | `not_applicable` | `operator/agent_infra/benchmark_evaluator.py` | Claim unit used by benchmark evaluator. |
| `SiteKnowledge` | internal_module | `current` | `not_applicable` | `operator/agent_infra/site_knowledge.py` | Structured site-specific knowledge base. |
| `ExplorationLoop` | internal_module | `current` | `not_applicable` | `operator/agent_infra/site_knowledge.py` | Site exploration and knowledge acquisition. |
| `ToolAffordance` | internal_module | `current` | `not_applicable` | `operator/agent_infra/site_knowledge.py` | Site tool representation schema. |
| `InteractionRule` | internal_module | `current` | `not_applicable` | `operator/agent_infra/site_knowledge.py` | Site interaction rule schema. |
| `ButtonMapEntry` | internal_module | `current` | `not_applicable` | `operator/agent_infra/site_knowledge.py` | Site button-map schema. |
| `agent.py` | internal_module | `current` | `not_applicable` | `operator/agent.py` | Main universal entrypoint and execution loop. |
| `agent_core.py` | internal_module | `current` | `not_applicable` | `operator/agent_core.py` | Native macOS execution core. |
| `action_space.py` | internal_module | `current` | `not_applicable` | `operator/action_space.py` | Typed planner/executor action surface. |
| `capability_router.py` | internal_module | `current` | `not_applicable` | `operator/capability_router.py` | Task-to-capability activation and routing. |
| `window_capture.py` | internal_module | `current` | `not_applicable` | `operator/window_capture.py` | Front-window-scoped capture utilities. |
| `visual_engine.py` | internal_module | `current` | `not_applicable` | `operator/visual_engine.py` | Set-of-Mark visual grounding engine. |
| `a11y_engine.py` | internal_module | `current` | `not_applicable` | `operator/a11y_engine.py` | Accessibility tree extraction layer. |
| `element_map.py` | internal_module | `current` | `not_applicable` | `operator/element_map.py` | Fuses SoM and a11y data. |
| `web_primitives.py` | internal_module | `current` | `not_applicable` | `operator/web_primitives.py` | Site-agnostic web interaction primitives. |
| `inference_router.py` | internal_module | `current` | `not_applicable` | `operator/inference_router.py` | Flash/Pro/local inference routing. |
| `InputSanitizer` | internal_module | `current` | `not_applicable` | `operator/security/sanitizer.py` | Prompt injection and MCP poisoning defense. |
| `CredentialVault` | internal_module | `current` | `not_applicable` | `operator/security/credential_vault.py` | macOS Keychain-backed credential retrieval. |
| `HITLGuard` | internal_module | `current` | `not_applicable` | `operator/security/credential_vault.py` | Human approval gate for sensitive actions. |
| `pyobjc-framework-Cocoa` | python_dependency | `current` | `pinned_in_requirements` | `operator/requirements.txt` | AppKit/Cocoa bridge for macOS windowing and focus. |
| `pyobjc-framework-Quartz` | python_dependency | `current` | `pinned_in_requirements` | `operator/requirements.txt` | Quartz/CoreGraphics event posting and window APIs. |
| `google-genai` | python_dependency | `current` | `pinned_in_requirements` | `operator/requirements.txt` | Gemini API client used in the main path. |
| `pydantic` | python_dependency | `current` | `pinned_in_requirements` | `operator/requirements.txt` | Structured schema validation for model IO. |
| `Pillow` | python_dependency | `current` | `pinned_in_requirements` | `operator/requirements.txt` | Screenshot/image processing. |
| `requests` | python_dependency | `current` | `pinned_in_requirements` | `operator/requirements.txt` | Used by legacy/fallback kernel client path. |
| `imagehash` | python_dependency | `optional` | `missing_from_requirements` | `operator/agent.py`, `operator/agent_infra/skill_library.py` | pHash-based cache validation. |
| `numpy` | python_dependency | `optional` | `missing_from_requirements` | `operator/agent_infra/verification_gate.py`, `operator/agent_infra/visual_monitor.py` | Pixel diff and vector math support. |
| `scipy` | python_dependency | `optional` | `missing_from_requirements` | `operator/agent_infra/action_trust.py` | Optional Beta posterior quantile path. |
| `sentence_transformers` | python_dependency | `optional` | `missing_from_requirements` | `operator/agent_infra/skill_library.py` | Optional dense retrieval backend. |
| `macapptree` | python_dependency | `optional` | `missing_from_requirements` | `operator/a11y_engine.py` | Preferred accessibility backend when available. |
| `pyax` | python_dependency | `optional` | `missing_from_requirements` | `operator/a11y_engine.py` | Accessibility backend fallback. |
| `openai` | python_dependency | `optional` | `missing_from_requirements` | `operator/vlm_coordinator.py` | Legacy/OpenAI-based VLM path, not the primary current path. |
| `open` | system_tool | `current` | `not_applicable` | subprocess usage in `operator/agent.py` and startup scripts | Launches Safari and related apps. |
| `osascript` | system_tool | `current` | `not_applicable` | subprocess usage in `operator/agent.py`, handlers, startup | AppleScript control for Safari and UI queries. |
| `screencapture` | system_tool | `current` | `not_applicable` | subprocess usage across runtime modules | Screenshot capture in the main runtime path. |
| `security` CLI | system_tool | `current` | `not_applicable` | `operator/security/credential_vault.py` | Shell access to macOS Keychain. |
| `Quartz/CoreGraphics` | system_tool | `current` | `not_applicable` | `operator/agent_core.py`, handlers | Native HID events and window info APIs. |
| `Cocoa/AppKit` | system_tool | `current` | `not_applicable` | `operator/agent_core.py`, `operator/window_capture.py` | Focus, workspace, and screen/window APIs. |
| `CodexClient` | legacy_runtime | `legacy` | `not_applicable` | `operator/codex_client.py` | Hammerspoon-backed fallback client. |
| `VLMCoordinator` | legacy_runtime | `legacy` | `not_applicable` | `operator/vlm_coordinator.py` | Older fallback coordinator for the kernel path. |
| `Hammerspoon kernel` | legacy_runtime | `legacy` | `not_applicable` | `operator/cre/codex_kernel.lua` | Lua HTTP kernel used by `CodexClient`. |
| `operator/cre/codex_kernel.lua` | operational_script | `legacy` | `not_applicable` | `operator/cre/codex_kernel.lua` | Operational kernel file for the legacy stack. |
| `operator/cre/showcase.sh` | operational_script | `legacy` | `not_applicable` | `operator/cre/showcase.sh` | Hammerspoon/kernel demonstration script. |
| `operator/cre/verify_kernel.sh` | operational_script | `legacy` | `not_applicable` | `operator/cre/verify_kernel.sh` | Kernel verification helper script. |
| `operator/cre/run_agent.sh` | operational_script | `legacy` | `not_applicable` | `operator/cre/run_agent.sh` | Older shell entrypoint around the agent. |
| `operator/cre/run_ultimate_tests.sh` | operational_script | `legacy` | `not_applicable` | `operator/cre/run_ultimate_tests.sh` | Legacy test orchestration around kernel/client demos. |
| `cliclick` | historical_reference | `historical_reference` | `not_applicable` | historical docs under `operator/cre/` | Discussed as replaced by Hammerspoon/Quartz, not current runtime code. |
| `hs.eventtap` | historical_reference | `historical_reference` | `not_applicable` | historical docs under `operator/cre/` | Hammerspoon primitive referenced in legacy docs. |
| `hs.axuielement` | historical_reference | `historical_reference` | `not_applicable` | historical docs under `operator/cre/` | Hammerspoon accessibility primitive referenced in docs. |
| `hs.screen` | historical_reference | `historical_reference` | `not_applicable` | historical docs under `operator/cre/` | Hammerspoon screenshot primitive referenced in docs. |
| `cursor_ocr_map.py` | historical_reference | `historical_reference` | `not_applicable` | referenced in older docs only | Referenced in docs, not present as a current repo file. |

## Reconciliation Against `operator/requirements.txt`
### Covered by `operator/requirements.txt`
- `pyobjc-framework-Cocoa`
- `pyobjc-framework-Quartz`
- `google-genai`
- `pydantic`
- `Pillow`
- `requests`

### Missing from `operator/requirements.txt` but imported or used in code
- `imagehash`
- `numpy`
- `scipy`
- `sentence_transformers`
- `macapptree`
- `pyax`
- `openai`

## Final Verdict
The canonical tool inventory is larger than `AGENTS.md` plus `operator/requirements.txt` alone suggest.

Most important reconciliation finding:
- `operator/requirements.txt` is accurate for the primary minimum path, but it is not a complete declaration of every tool the repo can use.

Most important status distinction:
- `CodexClient`, `VLMCoordinator`, and the Hammerspoon kernel are real repo tooling, but they should be treated as `legacy`, not `current`.
