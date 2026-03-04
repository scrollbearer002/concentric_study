"""Decision Dependence Graph analyzer for trace-level causal reasoning.

Adapts MindGuard's Decision Dependence Graph (DDG) concept for offline
trace analysis. Where MindGuard (arXiv:2508.20412) constructs DDGs from
LLM attention weights to detect tool poisoning in real-time, we construct
DDGs from the structured trace data already produced by TraceWriter to
strengthen failure root-cause analysis in the HealingOrchestrator.

The key insight: each TraceStep already records pre_state, thought, action,
action_result, and post_state — these ARE the vertices of a causal decision
graph. We don't need attention weights; we have the actual state transitions.

Research basis:
- MindGuard (arXiv:2508.20412, Aug 2025): Decision Dependence Graph
  formalizes LLM reasoning as weighted directed graph. Vertices represent
  logical concepts (invoked tool, arguments, prior results, registered
  tools, user query). Edges quantify attention-based causal dependencies.
  94-99% average precision in detecting poisoned invocations with
  processing times under 1 second and zero additional token cost.

- AgentArmor (Wang et al., ByteDance, arXiv:2508.01249, Aug 2025):
  Converts agent runtime traces into graph-based intermediate
  representations — Control Flow Graphs (CFG), Data Flow Graphs (DFG),
  and Program Dependency Graphs (PDG). Enforces security policies via
  a type system over the graph. 95.75% TPR, 3.66% FPR on AgentDojo.

- IPIGuard (arXiv:2508.15310, EMNLP 2025): Tool Dependency Graph (TDG)
  models task execution as graph traversal, decoupling action planning
  from interaction with external (untrusted) data. Prevents malicious
  tool invocations by structuring tool call dependencies.

- Ferrante, Ottenstein & Warren (1987), "The Program Dependence Graph
  and Its Use in Optimization", ACM TOPLAS 9(3):319-349: Original
  formalism for program dependence graphs combining control and data
  flow in a single structure. Our DDG adapts this for agent traces.

- TraceCoder (ICSE 2026, arXiv:2602.06875): Observe-Analyze-Repair
  with Historical Lesson Learning. The causal chain extraction here
  serves the "Analyze" phase by identifying which prior steps causally
  contributed to a failure.

Design principles:
- ZERO imports from agent_infra (preserves unidirectional dependency chain)
- All data structures are JSON-serializable for trace storage
- Anomaly detection is deterministic (no LLM calls required)
- Causal chain extraction enables targeted root-cause analysis
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field, asdict
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Graph Data Structures
# ---------------------------------------------------------------------------

@dataclass
class DDGNode:
    """A vertex in the Decision Dependence Graph.

    Maps to MindGuard's V = {invoked_tool, arguments, prior_results,
    registered_tools, user_query}, adapted for trace steps:
    - step_index: temporal position in the execution trace
    - action_type: the tool/action invoked (MindGuard's "invoked tool")
    - thought: the agent's reasoning (captures intent → action mapping)
    - pre_state_keys: state variables available before this step
    - post_state_keys: state variables produced by this step
    - success: whether the action succeeded
    - parameters: action parameters for dependency analysis
    """

    step_index: int
    action_type: str
    thought: str = ""
    pre_state_keys: frozenset[str] = field(default_factory=frozenset)
    post_state_keys: frozenset[str] = field(default_factory=frozenset)
    success: bool = True
    parameters: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_index": self.step_index,
            "action_type": self.action_type,
            "thought": self.thought,
            "pre_state_keys": sorted(self.pre_state_keys),
            "post_state_keys": sorted(self.post_state_keys),
            "success": self.success,
        }


@dataclass
class DDGEdge:
    """A directed edge in the Decision Dependence Graph.

    Represents a causal dependency between two trace steps.
    Edge types follow the PDG decomposition (Ferrante et al., 1987):

    - data_flow: step B's pre_state includes keys produced by step A's
      post_state. This is the primary causal signal.
    - control_flow: step B's thought explicitly references step A's
      action type or outcome. Detected via keyword matching.
    - state_dependency: step B acts on the same UI elements or state
      variables that step A modified.
    """

    source: int
    target: int
    edge_type: str
    weight: float = 1.0
    shared_keys: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AnomalyReport:
    """A detected anomaly in the decision graph.

    Anomaly types (inspired by MindGuard's poisoning indicators and
    AgentArmor's type system violations):

    - orphaned_action: An action with no data-flow dependency on any
      prior step. In a well-structured execution, every action should
      consume state produced by a predecessor. Orphans suggest the
      agent acted without proper grounding.

    - state_discontinuity: A failed step that has no incoming edges.
      The failure likely stems from missing prerequisites rather than
      the action itself.

    - repeated_failure_chain: The same action type failed multiple
      times in sequence, indicating a structural problem rather than
      a transient issue.

    - thought_action_divergence: The agent's thought mentions one
      action type but actually performs a different one, suggesting
      plan-execution misalignment.
    """

    step_index: int
    anomaly_type: str
    severity: float
    description: str
    related_steps: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Decision Dependence Analyzer
# ---------------------------------------------------------------------------

class DecisionDependenceAnalyzer:
    """Constructs and analyzes Decision Dependence Graphs from trace data.

    The analyzer builds a directed graph where:
    - Nodes are trace steps (with action type, state keys, success/failure)
    - Edges represent causal dependencies (data flow, control flow, state)
    - Anomalies are detected via graph structural analysis

    This provides the HealingOrchestrator with:
    1. Causal chains: "step 7 failed because steps 3→5→7 form a
       dependency chain, and step 5 produced incomplete state"
    2. Anomaly reports: "step 4 is an orphaned action with no causal
       predecessor — it may be a hallucinated or unnecessary step"
    3. Confidence adjustments: anomalies in the causal chain of a
       failure increase classification confidence

    Usage::

        analyzer = DecisionDependenceAnalyzer()
        analyzer.build_from_trace(trace_steps)
        anomalies = analyzer.detect_anomalies()
        chain = analyzer.get_causal_chain(failure_step_index)
    """

    def __init__(self) -> None:
        self._nodes: list[DDGNode] = []
        self._edges: list[DDGEdge] = []
        self._adjacency: dict[int, list[int]] = {}  # target → [sources]

    @property
    def nodes(self) -> list[DDGNode]:
        return list(self._nodes)

    @property
    def edges(self) -> list[DDGEdge]:
        return list(self._edges)

    def build_from_trace(self, steps: list[dict[str, Any]]) -> None:
        """Construct the DDG from a list of trace step dicts.

        Phase 1: Create nodes from steps.
        Phase 2: Build data-flow edges (state key overlap).
        Phase 3: Build control-flow edges (thought references).
        """
        self._nodes.clear()
        self._edges.clear()
        self._adjacency.clear()

        # Phase 1: Node construction
        for step in steps:
            action = step.get("action", {})
            node = DDGNode(
                step_index=step.get("step", 0),
                action_type=(
                    action.get("type", "unknown")
                    if isinstance(action, dict) else str(action)
                ),
                thought=step.get("thought", ""),
                pre_state_keys=frozenset(step.get("pre_state", {}).keys()),
                post_state_keys=frozenset(step.get("post_state", {}).keys()),
                success=step.get("action_result", {}).get("success", True),
                parameters=(
                    action.get("parameters", {})
                    if isinstance(action, dict) else {}
                ),
            )
            self._nodes.append(node)

        # Phase 2: Data-flow edges
        for i, target in enumerate(self._nodes):
            for j, source in enumerate(self._nodes[:i]):
                shared = source.post_state_keys & target.pre_state_keys
                if shared:
                    weight = len(shared) / max(len(target.pre_state_keys), 1)
                    edge = DDGEdge(
                        source=source.step_index,
                        target=target.step_index,
                        edge_type="data_flow",
                        weight=weight,
                        shared_keys=sorted(shared),
                    )
                    self._edges.append(edge)
                    self._adjacency.setdefault(
                        target.step_index, []
                    ).append(source.step_index)

        # Phase 3: Control-flow edges (thought references prior actions)
        action_types_by_step: dict[int, str] = {
            n.step_index: n.action_type for n in self._nodes
        }
        for i, target in enumerate(self._nodes):
            if not target.thought:
                continue
            thought_lower = target.thought.lower()
            for j, source in enumerate(self._nodes[:i]):
                source_type = source.action_type.lower().replace("_", " ")
                if len(source_type) > 3 and source_type in thought_lower:
                    if source.step_index not in self._adjacency.get(
                        target.step_index, []
                    ):
                        edge = DDGEdge(
                            source=source.step_index,
                            target=target.step_index,
                            edge_type="control_flow",
                            weight=0.5,
                        )
                        self._edges.append(edge)
                        self._adjacency.setdefault(
                            target.step_index, []
                        ).append(source.step_index)

    def detect_anomalies(self) -> list[AnomalyReport]:
        """Detect structural anomalies in the decision graph.

        Returns a list of AnomalyReports sorted by severity descending.
        """
        anomalies: list[AnomalyReport] = []
        target_steps = {e.target for e in self._edges}

        for node in self._nodes:
            # Skip step 0 — it's the root, no predecessors expected
            if node.step_index == 0:
                continue

            # Orphaned action: no incoming edges
            if node.step_index not in target_steps:
                anomalies.append(AnomalyReport(
                    step_index=node.step_index,
                    anomaly_type="orphaned_action",
                    severity=0.5 if node.success else 0.7,
                    description=(
                        f"Step {node.step_index} ({node.action_type}) has no "
                        f"data-flow or control-flow dependency on prior steps"
                    ),
                ))

            # State discontinuity: failed step with no incoming edges
            if not node.success and node.step_index not in target_steps:
                anomalies.append(AnomalyReport(
                    step_index=node.step_index,
                    anomaly_type="state_discontinuity",
                    severity=0.8,
                    description=(
                        f"Failed step {node.step_index} ({node.action_type}) "
                        f"has no state dependencies — potential root cause"
                    ),
                ))

        # Repeated failure chain: same action type fails consecutively
        failed_nodes = [n for n in self._nodes if not n.success]
        for i in range(len(failed_nodes) - 1):
            if failed_nodes[i].action_type == failed_nodes[i + 1].action_type:
                anomalies.append(AnomalyReport(
                    step_index=failed_nodes[i + 1].step_index,
                    anomaly_type="repeated_failure_chain",
                    severity=0.75,
                    description=(
                        f"Action '{failed_nodes[i].action_type}' failed "
                        f"consecutively at steps {failed_nodes[i].step_index} "
                        f"and {failed_nodes[i + 1].step_index} — structural "
                        f"issue likely"
                    ),
                    related_steps=[failed_nodes[i].step_index],
                ))

        # Thought-action divergence
        common_actions = {
            "click", "type", "draw", "scroll", "clear", "select",
            "navigate", "set", "drag", "screenshot",
        }
        for node in self._nodes:
            if not node.thought:
                continue
            thought_actions = set()
            for word in re.findall(r"[a-z_]+", node.thought.lower()):
                for action_word in common_actions:
                    if action_word in word:
                        thought_actions.add(action_word)
            actual_type_lower = node.action_type.lower()
            if thought_actions and not any(
                a in actual_type_lower for a in thought_actions
            ):
                anomalies.append(AnomalyReport(
                    step_index=node.step_index,
                    anomaly_type="thought_action_divergence",
                    severity=0.4,
                    description=(
                        f"Step {node.step_index}: thought mentions "
                        f"{thought_actions} but action is "
                        f"'{node.action_type}'"
                    ),
                ))

        anomalies.sort(key=lambda a: a.severity, reverse=True)
        return anomalies

    def get_causal_chain(self, failure_step: int) -> list[int]:
        """Trace backward from a failure step to find its causal chain.

        Uses BFS over the reverse adjacency graph to find all steps
        that transitively contributed state to the failure step.

        This implements TraceCoder's "Analyze" phase: identifying
        which prior steps are causally implicated in the failure.
        """
        chain = [failure_step]
        visited = {failure_step}
        queue = [failure_step]

        while queue:
            current = queue.pop(0)
            for source in self._adjacency.get(current, []):
                if source not in visited:
                    visited.add(source)
                    chain.append(source)
                    queue.append(source)

        chain.sort()
        return chain

    def get_failure_context(self, failure_step: int) -> dict[str, Any]:
        """Produce a structured failure context for the HealingOrchestrator.

        Combines causal chain, anomalies, and graph metrics into a
        single diagnostic payload.
        """
        chain = self.get_causal_chain(failure_step)
        anomalies = self.detect_anomalies()
        chain_anomalies = [a for a in anomalies if a.step_index in chain]

        failure_node = None
        for node in self._nodes:
            if node.step_index == failure_step:
                failure_node = node
                break

        return {
            "failure_step": failure_step,
            "failure_action": failure_node.action_type if failure_node else "unknown",
            "causal_chain": chain,
            "causal_chain_length": len(chain),
            "total_anomalies": len(anomalies),
            "chain_anomalies": [a.to_dict() for a in chain_anomalies],
            "max_anomaly_severity": max(
                (a.severity for a in chain_anomalies), default=0.0
            ),
            "graph_stats": {
                "total_nodes": len(self._nodes),
                "total_edges": len(self._edges),
                "data_flow_edges": sum(
                    1 for e in self._edges if e.edge_type == "data_flow"
                ),
                "control_flow_edges": sum(
                    1 for e in self._edges if e.edge_type == "control_flow"
                ),
            },
        }

    def to_dict(self) -> dict[str, Any]:
        """Serialize the full graph for trace storage."""
        return {
            "nodes": [n.to_dict() for n in self._nodes],
            "edges": [e.to_dict() for e in self._edges],
        }
