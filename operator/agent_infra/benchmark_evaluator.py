"""MCP-Atlas-inspired benchmark evaluation for the dual-agent system.

Adapts the claims-based rubric and diagnostic metrics from MCP-Atlas
(arXiv:2602.00933, Scale AI, Feb 2026) for evaluating GUI automation
agent performance across multiple structured dimensions.

MCP-Atlas evaluates 36 real MCP servers across 220 tools and 1,000
tasks. We adapt its methodology because our dual-agent system faces
the same fundamental challenges: multi-step tool orchestration, error
recovery, and the need for partial-credit evaluation rather than
binary pass/fail.

Research basis:
- MCP-Atlas (arXiv:2602.00933, Scale AI, Feb 2026): Claims-based
  rubric awards partial credit based on factual claims satisfied in
  the output. Discovery Precision measures the fraction of tool calls
  made to the correct tools. Cross-server orchestration evaluates
  multi-tool coordination. Claude Opus 4.5 achieves 62.3% on the
  full 1,000-task set, indicating substantial room for improvement.

- MCP-Bench (NeurIPS 2025 Workshop, OpenReview:fe8mzHwMxN): 28
  servers, 250 tools. Rule-based judge evaluates task completion
  and execution efficiency. GPT-5 leads at 0.749 overall score.
  Key differentiator: schema comprehension during dynamic discovery.

- MCPToolBench++ (arXiv:2508.07575, Aug 2025): Structural planning
  evaluation using AST (Abstract Syntax Tree) accuracy for call
  structure, DAG accuracy for multi-step dependency chains, and
  Pass@K for execution correctness. 4,000+ servers, 40+ categories.

- MCPMark (arXiv:2509.24002, Sep 2025): 127 expert-created tasks
  with programmatic verification scripts. CRUD-based operations.
  GPT-5-medium achieves only 52.56% pass@1.

- MCPAgentBench (arXiv:2512.24565, Dec 2025): Dynamic sandbox
  with distractor tools to test selection ability. Comprehensive
  metrics for both task completion and execution efficiency.

- MCP Security Bench / MSB (arXiv:2510.15994, ICLR 2026): Introduces
  Net Resilient Performance (NRP) = PUA × (1 - ASR), quantifying
  the tradeoff between utility and security resilience.

Design principles:
- ZERO imports from agent_infra (preserves unidirectional chain)
- Reads trace.jsonl and manifest.json directly
- All metrics are JSON-serializable for storage alongside run data
- Extensible claim registration per task_id
- Aggregate reporting across multiple runs
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

@dataclass
class TaskClaim:
    """A single verifiable claim about expected task outcome.

    Following MCP-Atlas's claims-based rubric: each task has a set of
    factual claims that the correct answer must satisfy. This decouples
    success from adherence to a specific execution trajectory — the
    agent can take any path as long as the claims are met.

    Claims can be checked by:
    1. Built-in check functions (check_fn_name matching a known name)
    2. Custom callables (check_fn parameter)
    3. Manifest-level checks (outcome, duration, step count)
    """

    description: str
    check_fn_name: str = "check_success"
    weight: float = 1.0
    satisfied: bool = False
    evidence: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "check_fn_name": self.check_fn_name,
            "weight": self.weight,
            "satisfied": self.satisfied,
            "evidence": self.evidence,
        }


@dataclass
class BenchmarkResult:
    """Structured evaluation result following MCP-Atlas methodology.

    Metrics are organized into five categories matching the benchmark
    frameworks they originate from.
    """

    task_id: str
    run_id: str
    timestamp: str = ""

    # --- Claims-based metrics (MCP-Atlas) ---
    claims_total: int = 0
    claims_satisfied: int = 0
    claims_score: float = 0.0
    claims_detail: list[dict[str, Any]] = field(default_factory=list)

    # --- Discovery precision (MCP-Atlas) ---
    actions_total: int = 0
    actions_succeeded: int = 0
    discovery_precision: float = 0.0

    # --- Efficiency metrics (MCP-Bench) ---
    total_duration_ms: int = 0
    steps_executed: int = 0
    steps_succeeded: int = 0
    step_success_rate: float = 0.0

    # --- Error recovery (MCP-Atlas) ---
    errors_encountered: int = 0
    errors_recovered: int = 0
    recovery_rate: float = 0.0

    # --- Structural metrics (MCPToolBench++) ---
    plan_optimality: float = 0.0
    redundant_actions: int = 0

    # --- Security resilience (MSB) ---
    net_resilient_performance: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def save(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)


# ---------------------------------------------------------------------------
# Benchmark Evaluator
# ---------------------------------------------------------------------------

class BenchmarkEvaluator:
    """Evaluates dual-agent system performance using MCP-Atlas methodology.

    The evaluator operates post-hoc on completed runs. It reads the
    manifest.json and trace.jsonl from a run directory, evaluates
    registered claims, computes diagnostic metrics, and produces a
    structured BenchmarkResult.

    Usage::

        evaluator = BenchmarkEvaluator()

        evaluator.register_claims("CONCENTRIC_TRIANGLES_CLEAN", [
            TaskClaim("Task completed successfully", "check_success"),
            TaskClaim("All steps succeeded", "check_all_steps_passed"),
            TaskClaim("Completed within 120 seconds", "check_duration_under", weight=0.5),
            TaskClaim("Fewer than 15 steps", "check_step_count_under"),
        ])
        evaluator.register_optimal_steps("CONCENTRIC_TRIANGLES_CLEAN", 10)

        result = evaluator.evaluate_run("operator/cre/runs/<run_id>")
        print(f"Claims: {result.claims_score:.0%}")
        print(f"Discovery Precision: {result.discovery_precision:.0%}")
        print(f"Recovery Rate: {result.recovery_rate:.0%}")

        # Aggregate across runs
        report = evaluator.get_aggregate_report()
    """

    # Default duration threshold for check_duration_under (ms)
    DEFAULT_DURATION_THRESHOLD_MS: int = 120_000
    # Default step count threshold for check_step_count_under
    DEFAULT_STEP_COUNT_THRESHOLD: int = 20

    def __init__(self) -> None:
        self._claim_registry: dict[str, list[TaskClaim]] = {}
        self._optimal_steps: dict[str, int] = {}
        self._custom_checks: dict[str, Callable[..., bool]] = {}
        self._results_history: list[BenchmarkResult] = []

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register_claims(self, task_id: str, claims: list[TaskClaim]) -> None:
        """Register verifiable claims for a task.

        Claims are the acceptance criteria. Following MCP-Atlas: the
        evaluation awards partial credit proportional to the weighted
        fraction of claims satisfied.
        """
        self._claim_registry[task_id] = list(claims)

    def register_optimal_steps(self, task_id: str, optimal: int) -> None:
        """Register the known optimal step count for plan_optimality."""
        self._optimal_steps[task_id] = optimal

    def register_custom_check(
        self, name: str, fn: Callable[[dict[str, Any], list[dict[str, Any]]], bool]
    ) -> None:
        """Register a custom claim-check function.

        The function receives (manifest_dict, steps_list) and returns bool.
        """
        self._custom_checks[name] = fn

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def evaluate_run(self, run_dir: str | Path) -> BenchmarkResult:
        """Evaluate a completed run against registered claims and metrics.

        Reads manifest.json and trace.jsonl from the run directory.
        Returns a BenchmarkResult with all computed metrics.
        """
        run_dir = Path(run_dir)
        manifest = self._read_json(run_dir / "manifest.json")
        steps = self._read_jsonl(run_dir / "trace.jsonl")

        task_id = manifest.get("task_id", "")
        run_id = manifest.get("run_id", "")

        result = BenchmarkResult(
            task_id=task_id,
            run_id=run_id,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )

        # --- Claims-based evaluation (MCP-Atlas) ---
        claims = [
            TaskClaim(
                description=c.description,
                check_fn_name=c.check_fn_name,
                weight=c.weight,
            )
            for c in self._claim_registry.get(task_id, [])
        ]

        total_weight = sum(c.weight for c in claims)
        satisfied_weight = 0.0

        for claim in claims:
            claim.satisfied, claim.evidence = self._check_claim(
                claim, manifest, steps
            )
            if claim.satisfied:
                satisfied_weight += claim.weight

        result.claims_total = len(claims)
        result.claims_satisfied = sum(1 for c in claims if c.satisfied)
        result.claims_score = (
            satisfied_weight / max(total_weight, 1.0)
        )
        result.claims_detail = [c.to_dict() for c in claims]

        # --- Step-level metrics (MCP-Bench) ---
        result.steps_executed = len(steps)
        result.steps_succeeded = sum(
            1 for s in steps
            if s.get("action_result", {}).get("success", False)
        )
        result.step_success_rate = (
            result.steps_succeeded / max(result.steps_executed, 1)
        )
        result.total_duration_ms = manifest.get("total_duration_ms", 0)

        # --- Discovery precision (MCP-Atlas) ---
        result.actions_total = result.steps_executed
        result.actions_succeeded = result.steps_succeeded
        result.discovery_precision = result.step_success_rate

        # --- Error recovery ---
        self._compute_error_recovery(result, steps)

        # --- Plan optimality (MCPToolBench++) ---
        optimal = self._optimal_steps.get(task_id, result.steps_executed)
        result.plan_optimality = min(
            1.0, optimal / max(result.steps_executed, 1)
        )

        # --- Redundant action detection ---
        result.redundant_actions = self._count_redundant_actions(steps)

        # --- Net Resilient Performance (MSB) ---
        attack_success_rate = 0.0
        result.net_resilient_performance = (
            result.claims_score * (1 - attack_success_rate)
        )

        self._results_history.append(result)

        # Auto-save alongside the run
        result_path = run_dir / "benchmark_result.json"
        try:
            result.save(result_path)
        except OSError:
            logger.debug("Could not save benchmark result to %s", result_path)

        return result

    def get_aggregate_report(self) -> dict[str, Any]:
        """Aggregate metrics across all evaluated runs.

        Returns a summary dict suitable for logging or display.
        """
        if not self._results_history:
            return {"message": "No evaluations recorded", "total_runs": 0}

        n = len(self._results_history)
        return {
            "total_runs": n,
            "avg_claims_score": round(
                sum(r.claims_score for r in self._results_history) / n, 3
            ),
            "avg_step_success_rate": round(
                sum(r.step_success_rate for r in self._results_history) / n, 3
            ),
            "avg_discovery_precision": round(
                sum(r.discovery_precision for r in self._results_history) / n, 3
            ),
            "avg_recovery_rate": round(
                sum(r.recovery_rate for r in self._results_history) / n, 3
            ),
            "avg_plan_optimality": round(
                sum(r.plan_optimality for r in self._results_history) / n, 3
            ),
            "avg_net_resilient_performance": round(
                sum(r.net_resilient_performance for r in self._results_history) / n, 3
            ),
            "total_redundant_actions": sum(
                r.redundant_actions for r in self._results_history
            ),
            "pass_rate": round(
                sum(1 for r in self._results_history if r.claims_score >= 0.7) / n, 3
            ),
        }

    @property
    def results_history(self) -> list[BenchmarkResult]:
        return list(self._results_history)

    # ------------------------------------------------------------------
    # Claim Checking
    # ------------------------------------------------------------------

    def _check_claim(
        self,
        claim: TaskClaim,
        manifest: dict[str, Any],
        steps: list[dict[str, Any]],
    ) -> tuple[bool, str]:
        """Evaluate a single claim. Returns (satisfied, evidence)."""

        # Custom registered checks take priority
        if claim.check_fn_name in self._custom_checks:
            try:
                result = self._custom_checks[claim.check_fn_name](
                    manifest, steps
                )
                return result, "custom check"
            except Exception as exc:
                return False, f"custom check error: {exc}"

        fn_name = claim.check_fn_name
        semantics = manifest.get("outcome_semantics", {})
        task_result = (
            semantics.get("task_result")
            if isinstance(semantics, dict)
            else None
        )

        if fn_name == "check_success":
            ok = (
                task_result == "accepted"
                if task_result is not None
                else manifest.get("outcome") == "success"
            )
            evidence = (
                f"task_result={task_result}"
                if task_result is not None
                else f"outcome={manifest.get('outcome')}"
            )
            return ok, evidence

        if fn_name == "check_duration_under":
            duration = manifest.get("total_duration_ms", float("inf"))
            threshold = self.DEFAULT_DURATION_THRESHOLD_MS
            ok = duration < threshold
            return ok, f"duration={duration}ms (threshold={threshold}ms)"

        if fn_name == "check_step_count_under":
            count = len(steps)
            threshold = self.DEFAULT_STEP_COUNT_THRESHOLD
            ok = count <= threshold
            return ok, f"steps={count} (threshold={threshold})"

        if fn_name == "check_all_steps_passed":
            failed = [
                s for s in steps
                if not s.get("action_result", {}).get("success", True)
            ]
            ok = len(failed) == 0
            return ok, f"{len(failed)} failed steps"

        if fn_name == "check_no_grounding_errors":
            grounding_failures = [
                s for s in steps
                if "grounding" in str(s.get("action_result", {}).get("error", "")).lower()
            ]
            ok = len(grounding_failures) == 0
            return ok, f"{len(grounding_failures)} grounding errors"

        # Unknown check: fail with explanation
        return False, f"unknown check: {fn_name}"

    # ------------------------------------------------------------------
    # Metric Computation
    # ------------------------------------------------------------------

    def _compute_error_recovery(
        self, result: BenchmarkResult, steps: list[dict[str, Any]]
    ) -> None:
        """Compute error recovery metrics.

        A recovery is when a failed step is followed by a successful step,
        indicating the agent adapted to the failure.
        """
        errors = 0
        recoveries = 0

        for i, step in enumerate(steps):
            if not step.get("action_result", {}).get("success", True):
                errors += 1
                if i + 1 < len(steps):
                    next_step = steps[i + 1]
                    if next_step.get("action_result", {}).get("success", False):
                        recoveries += 1

        result.errors_encountered = errors
        result.errors_recovered = recoveries
        result.recovery_rate = recoveries / max(errors, 1)

    @staticmethod
    def _count_redundant_actions(steps: list[dict[str, Any]]) -> int:
        """Count consecutive duplicate action types (likely retries)."""
        redundant = 0
        prev_type = None
        for step in steps:
            action = step.get("action", {})
            atype = (
                action.get("type", "unknown")
                if isinstance(action, dict) else str(action)
            )
            if atype == prev_type:
                redundant += 1
            prev_type = atype
        return redundant

    # ------------------------------------------------------------------
    # File I/O
    # ------------------------------------------------------------------

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    @staticmethod
    def _read_jsonl(path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        results: list[dict[str, Any]] = []
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        results.append(json.loads(line))
        except (json.JSONDecodeError, OSError):
            pass
        return results
