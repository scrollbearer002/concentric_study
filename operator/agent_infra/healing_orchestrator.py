"""Self-healing orchestrator for the dual-agent loop.

Implements the automated fix-and-retry cycle described in CoAct-1 (ICLR 2026)
and informed by ConceptAgent (arXiv:2410.06108) which achieved 20% task
completion improvement from recovery alone.

Enhanced with Decision Dependence Graph (DDG) analysis adapted from:
- MindGuard (arXiv:2508.20412): DDG formalizes LLM reasoning as a weighted
  directed graph for causal provenance tracking. 94-99% precision.
- AgentArmor (arXiv:2508.01249): Runtime trace → CFG/DFG/PDG for security
  enforcement. 95.75% TPR, 3.66% FPR.
- TraceCoder (ICSE 2026, arXiv:2602.06875): Observe-Analyze-Repair with
  Historical Lesson Learning to prevent repeated failures.

Build-order: Phase 3 depends on Phase 1 (TraceWriter) and Phase 2
(DiagnosticReader). The orchestrator reads structured traces, classifies
failures, and decides on corrective actions.

The orchestrator does NOT modify code autonomously — it produces structured
diagnoses and recommendations that the code agent (Cursor/Opus) can act on.
This separation follows the CodeDelegator (2025) pattern of Ephemeral-Persistent
State Separation: the orchestrator maintains persistent strategic oversight
while individual repair actions are scoped and contained.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from agent_infra.diagnostic_reader import DiagnosticReader

logger = logging.getLogger(__name__)


class FailureClassification:
    """Structured failure classification with confidence and recommended action.

    Categories follow the taxonomy from the APR Survey (arXiv:2506.23749):
    - transient: temporary environmental issue (popup, focus loss, timing)
    - grounding: visual grounding failed (element not found, wrong coordinates)
    - execution: action executed but had wrong effect (drawing drift, misclick)
    - logic: plan or handler has a structural bug
    - environment: app crash, network failure, permission issue
    """

    __slots__ = ("category", "confidence", "action", "details", "step_index", "error_summary")

    CATEGORIES = ("transient", "grounding", "execution", "logic", "environment")
    ACTIONS = ("retry", "adjust_parameters", "escalate_to_code_agent", "abort")

    def __init__(
        self,
        category: str,
        confidence: float,
        action: str,
        details: str,
        step_index: int | None = None,
        error_summary: str = "",
    ) -> None:
        self.category = category
        self.confidence = confidence
        self.action = action
        self.details = details
        self.step_index = step_index
        self.error_summary = error_summary

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "confidence": self.confidence,
            "action": self.action,
            "details": self.details,
            "step_index": self.step_index,
            "error_summary": self.error_summary,
        }


class HealingOrchestrator:
    """Orchestrates the self-healing loop across multiple test runs.

    Core loop (from CoAct-1 + ConceptAgent):
        1. Read the trace from the most recent run
        2. If success: record in history, return
        3. If failure: classify the failure
        4. Based on classification, recommend an action
        5. Track attempts to prevent infinite loops

    The orchestrator is stateless across instantiations — all state is
    persisted to the runs directory via TraceWriter and manifest files.
    """

    def __init__(self, runs_dir: str | Path, max_attempts: int = 3) -> None:
        self._runs_dir = Path(runs_dir)
        self._max_attempts = max_attempts
        self._history: list[dict[str, Any]] = []

    @property
    def max_attempts(self) -> int:
        return self._max_attempts

    def analyze_run(self, run_dir: str | Path) -> FailureClassification | None:
        """Analyze a completed run and return a failure classification.

        Returns None if the run succeeded.
        """
        reader = DiagnosticReader(run_dir)
        manifest = reader._load_manifest()

        if manifest["outcome"] == "success":
            self._history.append({
                "run_id": manifest["run_id"],
                "outcome": "success",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            })
            return None

        failure_step = reader.get_failure_step_data()
        failure_category = manifest.get("failure_category", "unknown")
        error_summary = manifest.get("error_summary", "unknown error")

        classification = self._classify_failure(failure_step, failure_category, error_summary)

        self._history.append({
            "run_id": manifest["run_id"],
            "outcome": "failure",
            "classification": classification.to_dict(),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })

        return classification

    def analyze_run_with_ddg(self, run_dir: str | Path) -> FailureClassification | None:
        """Enhanced failure analysis using Decision Dependence Graph.

        Builds a DDG from the execution trace, detects structural
        anomalies, extracts the causal chain leading to the failure,
        and uses this evidence to improve classification confidence
        and root-cause attribution.

        The DDG provides three signals that keyword heuristics cannot:
        1. Orphaned actions: steps with no causal predecessor suggest
           the agent hallucinated or skipped a prerequisite.
        2. Causal chain depth: shallow chains suggest direct failures;
           deep chains suggest cascading errors from an early misstep.
        3. State discontinuities: failures at steps with no incoming
           data-flow edges point to missing prerequisites.

        Research basis:
        - MindGuard (arXiv:2508.20412): DDG + attention → provenance
        - AgentArmor (arXiv:2508.01249): trace → PDG → type checking
        - IPIGuard (arXiv:2508.15310, EMNLP 2025): TDG for tool deps
        """
        base_classification = self.analyze_run(run_dir)
        if base_classification is None:
            return None

        try:
            from agent_infra.decision_graph import DecisionDependenceAnalyzer

            reader = DiagnosticReader(run_dir)
            steps = reader._load_steps()
            if not steps or len(steps) < 2:
                return base_classification

            analyzer = DecisionDependenceAnalyzer()
            analyzer.build_from_trace(steps)

            if base_classification.step_index is not None:
                context = analyzer.get_failure_context(
                    base_classification.step_index
                )
                chain = context["causal_chain"]
                chain_anomalies = context["chain_anomalies"]
                max_severity = context["max_anomaly_severity"]

                ddg_notes: list[str] = []
                ddg_notes.append(
                    f"Causal chain: {len(chain)} steps "
                    f"({' → '.join(str(s) for s in chain)})"
                )

                if chain_anomalies:
                    ddg_notes.append(
                        f"{len(chain_anomalies)} anomalies in chain"
                    )
                    for a in chain_anomalies[:3]:
                        ddg_notes.append(
                            f"  [{a['anomaly_type']}] step "
                            f"{a['step_index']}: {a['description']}"
                        )

                base_classification.details += (
                    "\n[DDG Analysis] " + "; ".join(ddg_notes)
                )

                if max_severity > 0.5:
                    boost = min(0.15, max_severity * 0.15)
                    base_classification.confidence = min(
                        1.0, base_classification.confidence + boost
                    )

                if any(
                    a["anomaly_type"] == "state_discontinuity"
                    for a in chain_anomalies
                ):
                    if base_classification.category == "logic":
                        base_classification.category = "grounding"
                        base_classification.details += (
                            "\n[DDG] Reclassified: state discontinuity "
                            "suggests missing grounding, not logic error"
                        )

        except ImportError:
            logger.debug("decision_graph module not available; DDG analysis skipped")
        except Exception as exc:
            logger.warning("DDG analysis failed: %s", exc)

        return base_classification

    def should_retry(self) -> bool:
        """Determine if another attempt should be made.

        Checks:
        1. Haven't exceeded max_attempts
        2. The last failure was not classified as 'abort'
        3. We're not in a repeated-failure loop (same error 3+ times)
        """
        failures = [h for h in self._history if h["outcome"] == "failure"]

        if len(failures) >= self._max_attempts:
            return False

        if failures and failures[-1].get("classification", {}).get("action") == "abort":
            return False

        if len(failures) >= 3:
            last_3_errors = [f.get("classification", {}).get("error_summary", "") for f in failures[-3:]]
            if len(set(last_3_errors)) == 1 and last_3_errors[0]:
                return False

        return True

    def get_diagnostic_for_code_agent(self, run_dir: str | Path) -> str:
        """Produce a full diagnostic report for the code agent to consume.

        Combines DiagnosticReader output with failure classification and
        attempt history. This is the primary interface between the GUI
        agent's failure and the code agent's repair capability.
        """
        reader = DiagnosticReader(run_dir)
        classification = self.analyze_run(run_dir)

        parts = [reader.full_diagnostic()]

        if classification:
            parts.append("")
            parts.append("=== FAILURE CLASSIFICATION ===")
            parts.append(f"Category: {classification.category}")
            parts.append(f"Confidence: {classification.confidence:.0%}")
            parts.append(f"Recommended action: {classification.action}")
            parts.append(f"Details: {classification.details}")

        if self._history:
            parts.append("")
            parts.append(f"=== ATTEMPT HISTORY ({len(self._history)} runs) ===")
            for h in self._history:
                status = h["outcome"].upper()
                run_id = h["run_id"]
                if h["outcome"] == "failure":
                    cat = h.get("classification", {}).get("category", "?")
                    parts.append(f"  {run_id}: {status} ({cat})")
                else:
                    parts.append(f"  {run_id}: {status}")

            if not self.should_retry():
                parts.append("")
                parts.append("STATUS: No more retries recommended.")
                if len([h for h in self._history if h["outcome"] == "failure"]) >= self._max_attempts:
                    parts.append(f"REASON: Max attempts ({self._max_attempts}) reached.")
            else:
                remaining = self._max_attempts - len([h for h in self._history if h["outcome"] == "failure"])
                parts.append(f"\nSTATUS: {remaining} retry attempt(s) remaining.")

        return "\n".join(parts)

    def get_attempt_count(self) -> int:
        """Return the number of failed attempts so far."""
        return len([h for h in self._history if h["outcome"] == "failure"])

    def get_history(self) -> list[dict[str, Any]]:
        """Return the full attempt history."""
        return list(self._history)

    # ------------------------------------------------------------------
    # Classification Engine
    # ------------------------------------------------------------------

    def _classify_failure(
        self,
        failure_step: dict[str, Any] | None,
        failure_category: str,
        error_summary: str,
    ) -> FailureClassification:
        """Classify a failure based on trace data and error metadata.

        Uses keyword-based heuristics for deterministic, testable classification.
        """
        error_lower = error_summary.lower()
        step_index = failure_step["step"] if failure_step else None

        if failure_category == "launch_failure":
            return FailureClassification(
                category="environment",
                confidence=0.95,
                action="abort",
                details="Application launch failed. Check Safari installation and network.",
                step_index=step_index,
                error_summary=error_summary,
            )

        if failure_category == "non_recoverable_error":
            if any(kw in error_lower for kw in ("permission", "crash", "killed", "segfault")):
                return FailureClassification(
                    category="environment",
                    confidence=0.90,
                    action="abort",
                    details="Non-recoverable environment error.",
                    step_index=step_index,
                    error_summary=error_summary,
                )
            return FailureClassification(
                category="logic",
                confidence=0.70,
                action="escalate_to_code_agent",
                details="Non-recoverable error suggests a code-level bug.",
                step_index=step_index,
                error_summary=error_summary,
            )

        if any(kw in error_lower for kw in ("popup", "dialog", "modal", "overlay", "focus")):
            return FailureClassification(
                category="transient",
                confidence=0.85,
                action="retry",
                details="Transient UI obstruction detected. Retry should resolve.",
                step_index=step_index,
                error_summary=error_summary,
            )

        if any(kw in error_lower for kw in ("not found", "element not found", "grounding", "target not")):
            return FailureClassification(
                category="grounding",
                confidence=0.80,
                action="adjust_parameters",
                details="Visual grounding failed. Consider AX API fallback or iterative refinement.",
                step_index=step_index,
                error_summary=error_summary,
            )

        if any(kw in error_lower for kw in ("timeout", "timed out")):
            return FailureClassification(
                category="transient",
                confidence=0.75,
                action="retry",
                details="Operation timed out. May be a transient load issue.",
                step_index=step_index,
                error_summary=error_summary,
            )

        if any(kw in error_lower for kw in ("assertion", "visual assert", "expected")):
            action_type = ""
            if failure_step:
                action_type = failure_step.get("action", {}).get("type", "")

            if action_type in ("draw_path", "draw_concentric_triangles"):
                return FailureClassification(
                    category="execution",
                    confidence=0.75,
                    action="adjust_parameters",
                    details=f"Drawing action '{action_type}' failed visual verification. Consider adjusting timing or coordinates.",
                    step_index=step_index,
                    error_summary=error_summary,
                )

            return FailureClassification(
                category="grounding",
                confidence=0.65,
                action="escalate_to_code_agent",
                details="Visual assertion failed. Root cause unclear — needs code agent investigation.",
                step_index=step_index,
                error_summary=error_summary,
            )

        repeated_failures = len([
            h for h in self._history
            if h["outcome"] == "failure"
            and h.get("classification", {}).get("error_summary") == error_summary
        ])
        if repeated_failures >= 2:
            return FailureClassification(
                category="logic",
                confidence=0.80,
                action="escalate_to_code_agent",
                details=f"Same error repeated {repeated_failures + 1} times. Likely a structural code issue.",
                step_index=step_index,
                error_summary=error_summary,
            )

        return FailureClassification(
            category="logic",
            confidence=0.50,
            action="escalate_to_code_agent",
            details="Unrecognized failure pattern. Escalating for code agent investigation.",
            step_index=step_index,
            error_summary=error_summary,
        )
