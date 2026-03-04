"""Agent Infrastructure Package — shared foundation for the dual-agent system.

Provides structured execution tracing, diagnostic reading, self-healing
orchestration, skill library management, and the dual-agent outer loop.
All modules are independently usable and follow a unidirectional dependency chain:

    TraceWriter -> DiagnosticReader -> HealingOrchestrator
    TraceWriter -> SkillLibrary
    All of the above -> OuterLoop (integration layer)

New modules (zero agent_infra imports — independently usable):
    DecisionDependenceAnalyzer: Causal graph analysis for trace-level reasoning
    BenchmarkEvaluator: MCP-Atlas-inspired multi-dimensional evaluation
    SemanticSkillIndex: Dense vector retrieval for skill library (optional)

Architecture backed by:
- OpenHands SDK (arXiv:2511.03690): decoupled, independently consumable packages
- AGENT KB (ICML 2025, arXiv:2507.06229): shared knowledge infrastructure
- CRADLE (NeurIPS 2024): modular agent framework with reusable components
- AgentHub (arXiv:2510.03495): agents as reusable software packages
- SHML (NeurIPS 2024, arXiv:2411.00186): Monitor → Diagnose → Adapt → Test
- VIGIL (arXiv:2512.07094): stage-gated supervisory pipeline
- Reflexion (NeurIPS 2023, arXiv:2303.11366): verbal self-reflection
- MindGuard (arXiv:2508.20412): Decision Dependence Graph for causal analysis
- RAG-MCP (arXiv:2505.03275): Semantic retrieval for tool/skill selection
- MCP-Atlas (arXiv:2602.00933): Claims-based benchmark evaluation
- OWASP MCP Top 10 (2025): MCP-specific security vulnerability taxonomy
"""

from agent_infra.trace_writer import TraceWriter, TraceStep
from agent_infra.diagnostic_reader import DiagnosticReader
from agent_infra.healing_orchestrator import HealingOrchestrator, FailureClassification
from agent_infra.skill_library import SkillLibrary, SkillRecord, SkillMaturity, SemanticSkillIndex
from agent_infra.outer_loop import OuterLoop, OuterLoopResult, ReflectionJournal, RulesStore, TASK_ENV_MAP
from agent_infra.action_trust import ActionTrustTracker
from agent_infra.summarizer import Summarizer
from agent_infra.site_knowledge import SiteKnowledge, ExplorationLoop, ToolAffordance, InteractionRule, ButtonMapEntry
from agent_infra.host_tool_health import HostToolHealth
from agent_infra.visual_monitor import VisualMonitor, Snapshot, ComparisonResult
from agent_infra.research_agent import ResearchAgent, ResearchBrief
from agent_infra.verification_gate import VerificationGate, VerificationResult as VerificationGateResult, Constraint
from agent_infra.decision_graph import DecisionDependenceAnalyzer, DDGNode, DDGEdge, AnomalyReport
from agent_infra.benchmark_evaluator import BenchmarkEvaluator, BenchmarkResult, TaskClaim

__all__ = [
    # Phase 1: Tracing
    "TraceWriter",
    "TraceStep",
    # Phase 2: Diagnostics
    "DiagnosticReader",
    # Phase 3: Self-Healing
    "HealingOrchestrator",
    "FailureClassification",
    # Phase 5: Skill Library
    "SkillLibrary",
    "SkillRecord",
    "SkillMaturity",
    "SemanticSkillIndex",
    # Phase A: Outer Loop
    "OuterLoop",
    "OuterLoopResult",
    "ReflectionJournal",
    "RulesStore",
    "TASK_ENV_MAP",
    # VLM Optimization
    "ActionTrustTracker",
    "Summarizer",
    # Site Knowledge
    "SiteKnowledge",
    "ExplorationLoop",
    "ToolAffordance",
    "InteractionRule",
    "ButtonMapEntry",
    # Host tool health
    "HostToolHealth",
    # Visual Monitoring
    "VisualMonitor",
    "Snapshot",
    "ComparisonResult",
    # Research Agent
    "ResearchAgent",
    "ResearchBrief",
    # Verification Gate
    "VerificationGate",
    "VerificationGateResult",
    "Constraint",
    # Decision Dependence Graph (MindGuard-inspired)
    "DecisionDependenceAnalyzer",
    "DDGNode",
    "DDGEdge",
    "AnomalyReport",
    # Benchmark Evaluator (MCP-Atlas-inspired)
    "BenchmarkEvaluator",
    "BenchmarkResult",
    "TaskClaim",
]
