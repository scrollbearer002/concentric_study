# Tool Connections Diagram

This diagram is the compact architecture view of how the current tools connect.
It is derived from the definitive inventory in `operator/cre/MASTER_TOOL_LIST_PHD.md`
and the stage grouping in `operator/cre/artifacts/tool_inventory_by_stage.json`.

```mermaid
flowchart LR
    Task["Task + URL"] --> Guards

    subgraph Runtime["Current runtime"]
        Guards["Guardrails<br/>InputSanitizer<br/>CredentialVault<br/>HITLGuard"]
        Router["Entrypoint + routing<br/>agent.py<br/>capability_router.py<br/>action_space.py<br/>inference_router.py"]
        Research["Research + site knowledge<br/>ResearchAgent<br/>SiteKnowledge<br/>ExplorationLoop<br/>ToolAffordance<br/>InteractionRule<br/>ButtonMapEntry"]
        Memory["Memory + context<br/>SkillLibrary<br/>SemanticSkillIndex<br/>Summarizer<br/>ReflectionJournal<br/>RulesStore"]
        Perception["Perception stack<br/>window_capture.py<br/>visual_engine.py<br/>a11y_engine.py<br/>element_map.py"]
        Execute["Execution stack<br/>web_primitives.py<br/>agent_core.py"]
        Observe["Trace + verification<br/>TraceWriter<br/>VisualMonitor<br/>VerificationGate"]
        Diagnose["Diagnosis + evaluation<br/>DiagnosticReader<br/>DecisionDependenceAnalyzer<br/>HealingOrchestrator<br/>BenchmarkEvaluator<br/>TaskClaim"]
        Trust["Adaptive trust<br/>ActionTrustTracker"]
        Outer["Outer loop<br/>OuterLoop"]
    end

    subgraph Platform["Python + macOS substrate"]
        BaseDeps["Base deps<br/>google-genai<br/>pydantic<br/>Pillow"]
        OptDeps["Optional deps<br/>ImageHash<br/>numpy<br/>scipy<br/>sentence-transformers<br/>macapptree<br/>pyax"]
        NativePy["PyObjC bridge<br/>pyobjc-framework-Cocoa<br/>pyobjc-framework-Quartz"]
        NativeSys["System tools and APIs<br/>open<br/>osascript<br/>screencapture<br/>security CLI<br/>Quartz/CoreGraphics<br/>Cocoa/AppKit"]
    end

    subgraph Legacy["Legacy alternate path"]
        LegacyClient["CodexClient"]
        LegacyVLM["VLMCoordinator"]
        LegacyKernel["Hammerspoon kernel<br/>codex_kernel.lua"]
        LegacyDeps["Legacy deps<br/>requests<br/>openai"]
    end

    Guards --> Router
    Router --> Research
    Router --> Memory
    Router --> Perception
    Router --> Execute
    Research --> Memory
    Memory --> Router
    Perception --> Execute
    Execute --> Observe
    Observe --> Trust
    Trust -. verification skip / re-enable .-> Router
    Observe --> Diagnose
    Diagnose --> Outer
    Outer --> Memory
    Outer --> Router

    Router --> BaseDeps
    Perception --> BaseDeps
    Perception -. optional backends .-> OptDeps
    Observe -. optional math / hashes .-> OptDeps
    Memory -. optional dense retrieval .-> OptDeps
    Execute --> NativePy
    Execute --> NativeSys
    Perception --> NativeSys
    Observe --> NativeSys

    LegacyClient --> LegacyKernel
    LegacyClient --> LegacyDeps
    LegacyVLM --> LegacyDeps
    LegacyClient -. alternate execution path .-> Execute
    LegacyVLM -. alternate model path .-> Router
```

## Reading Notes
- Left to right is the normal execution flow: guardrails, plan, perceive, act, verify, diagnose, adapt.
- The lower `Platform` layer is shared substrate, not an independent workflow stage.
- The `Legacy` block is intentionally separated because it is still present in-repo but not the primary runtime.
