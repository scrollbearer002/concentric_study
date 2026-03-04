"""Hybrid inference router for tiered model selection.

Routes VLM queries to the appropriate model based on task complexity,
latency requirements, and cost constraints.  Implements the routing
strategies from Firewall Routing (EMNLP 2025) and AOrchestra
(arXiv:2602.03786).

Model tiers:
- Flash: Gemini 2.0 Flash — fast, cheap, binary YES/NO assertions
- Pro: Gemini 2.5 Pro — strategic planning, complex grounding
- Local: Qwen3-VL-2B via Ollama — temporal polling, simple grounding

Adaptive routing (PhD-level enhancement):
  After each VLM call, the caller reports actual latency and success/failure
  via ``record_outcome()``. The router uses exponential moving averages to
  track per-task-type latency and error rates. When a Flash-routed task
  consistently fails (error rate > PROMOTE_ERROR_THRESHOLD over a window),
  it is auto-promoted to Pro. When a Pro-routed task consistently succeeds
  under the Flash latency ceiling (< DEMOTE_LATENCY_MS), it can be demoted.

  This follows Firewall Routing's online learning loop (EMNLP 2025, Sec 4.2)
  and AOrchestra's task-specific routing table refinement. Learned routing
  state is persisted to JSON so adaptations survive across runs.

Research basis:
- Firewall Routing (EMNLP 2025): 80.7% of queries handled locally;
  60.2% cost reduction. Online routing refinement in Sec 4.2.
- AOrchestra (arXiv:2602.03786): Tiered model selection based on
  task-specific routing tables with dynamic reassignment.
- OS-Kairos (arXiv:2503.16465): Asymmetric compute for GUI agents.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class ModelTier(Enum):
    FLASH = "flash"
    PRO = "pro"
    LOCAL = "local"


@dataclass
class RoutingDecision:
    """The router's decision on which model to use."""
    tier: ModelTier
    model_name: str
    reason: str
    estimated_latency_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "tier": self.tier.value,
            "model": self.model_name,
            "reason": self.reason,
            "est_latency_ms": self.estimated_latency_ms,
        }


@dataclass
class RoutingStats:
    """Tracks routing decisions for cost analysis."""
    total_queries: int = 0
    flash_count: int = 0
    pro_count: int = 0
    local_count: int = 0
    total_latency_ms: int = 0

    @property
    def flash_ratio(self) -> float:
        return self.flash_count / max(self.total_queries, 1)

    @property
    def estimated_cost_savings(self) -> float:
        """Estimate savings vs all-Pro routing (Pro = 1.0 cost unit)."""
        if self.total_queries == 0:
            return 0.0
        pro_cost = self.total_queries * 1.0
        actual_cost = self.pro_count * 1.0 + self.flash_count * 0.1 + self.local_count * 0.01
        return (pro_cost - actual_cost) / pro_cost

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total_queries,
            "flash": self.flash_count,
            "pro": self.pro_count,
            "local": self.local_count,
            "flash_ratio": f"{self.flash_ratio:.1%}",
            "est_savings": f"{self.estimated_cost_savings:.1%}",
        }


_TASK_ROUTING: dict[str, ModelTier] = {
    "assert_visual_state": ModelTier.FLASH,
    "confirm_click_target": ModelTier.FLASH,
    "verify_canvas_empty": ModelTier.FLASH,
    "verify_pen_selected": ModelTier.FLASH,
    "verify_color_set": ModelTier.FLASH,
    "verify_triangles": ModelTier.FLASH,
    "readiness_poll": ModelTier.FLASH,
    "analyze_ui": ModelTier.PRO,
    "extract_target": ModelTier.PRO,
    "generate_plan": ModelTier.PRO,
    "diagnose_failure": ModelTier.PRO,
    "summarize": ModelTier.FLASH,
    "temporal_poll": ModelTier.LOCAL,
}


@dataclass
class _TaskPerformance:
    """Per-task-type performance tracking for adaptive routing.

    Uses exponential moving averages (EMA) for latency and error rate,
    following the online learning approach in Firewall Routing (EMNLP 2025).
    EMA smoothing factor alpha=0.3 gives ~80% weight to the last 5 observations.
    """
    total_calls: int = 0
    total_errors: int = 0
    ema_latency_ms: float = 0.0
    ema_error_rate: float = 0.0
    last_promotion: str = ""
    last_demotion: str = ""

    _ALPHA: float = field(default=0.3, repr=False)

    def update(self, latency_ms: int, success: bool) -> None:
        self.total_calls += 1
        error_val = 0.0 if success else 1.0
        if not success:
            self.total_errors += 1
        if self.total_calls == 1:
            self.ema_latency_ms = float(latency_ms)
            self.ema_error_rate = error_val
        else:
            self.ema_latency_ms = self._ALPHA * latency_ms + (1 - self._ALPHA) * self.ema_latency_ms
            self.ema_error_rate = self._ALPHA * error_val + (1 - self._ALPHA) * self.ema_error_rate

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_calls": self.total_calls,
            "total_errors": self.total_errors,
            "ema_latency_ms": round(self.ema_latency_ms, 1),
            "ema_error_rate": round(self.ema_error_rate, 4),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "_TaskPerformance":
        p = cls()
        p.total_calls = d.get("total_calls", 0)
        p.total_errors = d.get("total_errors", 0)
        p.ema_latency_ms = d.get("ema_latency_ms", 0.0)
        p.ema_error_rate = d.get("ema_error_rate", 0.0)
        p.last_promotion = d.get("last_promotion", "")
        p.last_demotion = d.get("last_demotion", "")
        return p


class InferenceRouter:
    """Routes VLM queries to the appropriate model tier.

    The router uses a static routing table for known task types and
    falls back to Pro for unknown tasks. It tracks statistics and
    per-task-type performance for adaptive routing refinement.

    Adaptive behavior (enabled when ``persist_path`` is provided):
    - Flash tasks with EMA error rate > PROMOTE_ERROR_THRESHOLD are
      auto-promoted to Pro (the Flash model can't handle that task).
    - Pro tasks with EMA latency < DEMOTE_LATENCY_MS and EMA error rate
      near zero are auto-demoted to Flash (Pro is overkill for that task).
    - Adaptations require MIN_OBSERVATIONS before triggering.
    - Learned routes persist to JSON across runs.
    """

    FLASH_MODEL = "gemini-2.0-flash"
    PRO_MODEL = "gemini-2.5-pro"
    LOCAL_MODEL = "qwen3-vl-2b"

    PROMOTE_ERROR_THRESHOLD = 0.20
    DEMOTE_LATENCY_MS = 3000.0
    DEMOTE_ERROR_CEILING = 0.05
    MIN_OBSERVATIONS = 5

    # Hysteresis band to prevent rapid oscillation (thrashing) between
    # model tiers. After a promotion, the task must sustain success for
    # HYSTERESIS_COOLDOWN observations before demotion is considered.
    # This follows the control-theoretic hysteresis principle: asymmetric
    # switching thresholds prevent chattering in bang-bang controllers
    # (Åström & Murray, Feedback Systems, 2008, Ch. 10).
    HYSTERESIS_COOLDOWN = 8  # observations after promotion before demotion eligible

    def __init__(
        self,
        enable_local: bool = False,
        custom_routes: dict[str, ModelTier] | None = None,
        persist_path: str | Path | None = None,
    ) -> None:
        self._routes = dict(_TASK_ROUTING)
        if custom_routes:
            self._routes.update(custom_routes)
        self._enable_local = enable_local
        self._stats = RoutingStats()
        self._local_available: bool | None = None
        self._perf: dict[str, _TaskPerformance] = {}
        self._persist_path = Path(persist_path) if persist_path else None
        self._adaptations: list[str] = []
        self._promotion_obs: dict[str, int] = {}  # task -> obs since last promotion
        if self._persist_path and self._persist_path.exists():
            self._load_learned_state()

    @property
    def stats(self) -> RoutingStats:
        return self._stats

    @property
    def adaptations(self) -> list[str]:
        return list(self._adaptations)

    def route(self, task_type: str) -> RoutingDecision:
        """Decide which model to use for a given task type."""
        tier = self._routes.get(task_type, ModelTier.PRO)

        if tier == ModelTier.LOCAL and not self._is_local_available():
            tier = ModelTier.FLASH

        model_name = self._tier_to_model(tier)
        reason = f"Static route: {task_type} -> {tier.value}"
        if task_type not in self._routes:
            reason = f"Unknown task '{task_type}', defaulting to Pro"

        est_latency = {
            ModelTier.FLASH: 2000,
            ModelTier.PRO: 8000,
            ModelTier.LOCAL: 500,
        }.get(tier, 5000)

        self._stats.total_queries += 1
        if tier == ModelTier.FLASH:
            self._stats.flash_count += 1
        elif tier == ModelTier.PRO:
            self._stats.pro_count += 1
        else:
            self._stats.local_count += 1

        return RoutingDecision(
            tier=tier, model_name=model_name,
            reason=reason, estimated_latency_ms=est_latency,
        )

    def get_model_for(self, task_type: str) -> str:
        """Convenience: return just the model name string."""
        return self.route(task_type).model_name

    def record_outcome(self, task_type: str, latency_ms: int, success: bool) -> None:
        """Report the outcome of a VLM call for adaptive routing.

        Updates the EMA latency and error rate for the task type, then
        checks whether a promotion (Flash->Pro) or demotion (Pro->Flash)
        is warranted. Adaptations are logged and persisted.
        """
        perf = self._perf.setdefault(task_type, _TaskPerformance())
        perf.update(latency_ms, success)

        if perf.total_calls >= self.MIN_OBSERVATIONS:
            self._maybe_adapt(task_type, perf)

        if self._persist_path:
            self._save_learned_state()

    def _maybe_adapt(self, task_type: str, perf: _TaskPerformance) -> None:
        """Check whether promotion or demotion is warranted, with hysteresis.

        Hysteresis prevents rapid oscillation: once promoted from Flash to Pro,
        the task must accumulate HYSTERESIS_COOLDOWN successful observations at
        the Pro tier before becoming eligible for demotion back to Flash.
        Without this cooldown, borderline tasks would thrash between tiers on
        every other call, wasting tokens and destabilizing latency.
        """
        current_tier = self._routes.get(task_type, ModelTier.PRO)

        # Track observations since last promotion for cooldown
        if task_type in self._promotion_obs:
            self._promotion_obs[task_type] += 1

        if current_tier == ModelTier.FLASH and perf.ema_error_rate > self.PROMOTE_ERROR_THRESHOLD:
            self._routes[task_type] = ModelTier.PRO
            self._promotion_obs[task_type] = 0  # reset cooldown counter
            msg = (
                f"[ADAPT] Promoted {task_type}: Flash->Pro "
                f"(error_rate={perf.ema_error_rate:.2%} > {self.PROMOTE_ERROR_THRESHOLD:.0%})"
            )
            perf.last_promotion = time.strftime("%Y-%m-%dT%H:%M:%S")
            self._adaptations.append(msg)

        elif (
            current_tier == ModelTier.PRO
            and perf.ema_latency_ms < self.DEMOTE_LATENCY_MS
            and perf.ema_error_rate < self.DEMOTE_ERROR_CEILING
            and self._promotion_obs.get(task_type, self.HYSTERESIS_COOLDOWN) >= self.HYSTERESIS_COOLDOWN
        ):
            self._routes[task_type] = ModelTier.FLASH
            self._promotion_obs.pop(task_type, None)
            msg = (
                f"[ADAPT] Demoted {task_type}: Pro->Flash "
                f"(latency={perf.ema_latency_ms:.0f}ms, error_rate={perf.ema_error_rate:.2%}, "
                f"cooldown satisfied)"
            )
            perf.last_demotion = time.strftime("%Y-%m-%dT%H:%M:%S")
            self._adaptations.append(msg)

    def _tier_to_model(self, tier: ModelTier) -> str:
        if tier == ModelTier.FLASH:
            return self.FLASH_MODEL
        elif tier == ModelTier.LOCAL:
            return self.LOCAL_MODEL
        return self.PRO_MODEL

    def _is_local_available(self) -> bool:
        """Check if a local model is available via Ollama."""
        if not self._enable_local:
            return False
        if self._local_available is not None:
            return self._local_available
        try:
            import subprocess
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True, text=True, timeout=5,
            )
            self._local_available = self.LOCAL_MODEL in result.stdout
        except Exception:
            self._local_available = False
        return self._local_available

    def add_route(self, task_type: str, tier: ModelTier) -> None:
        """Add or update a routing rule."""
        self._routes[task_type] = tier

    def get_routing_table(self) -> dict[str, str]:
        return {k: v.value for k, v in self._routes.items()}

    def get_performance_summary(self) -> dict[str, Any]:
        return {k: v.to_dict() for k, v in self._perf.items()}

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _save_learned_state(self) -> None:
        if self._persist_path is None:
            return
        data = {
            "learned_routes": {
                k: v.value for k, v in self._routes.items()
                if k not in _TASK_ROUTING or _TASK_ROUTING[k] != v
            },
            "performance": {k: v.to_dict() for k, v in self._perf.items()},
            "adaptations": self._adaptations[-20:],
        }
        self._persist_path.parent.mkdir(parents=True, exist_ok=True)
        self._persist_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def _load_learned_state(self) -> None:
        if self._persist_path is None:
            return
        try:
            data = json.loads(self._persist_path.read_text(encoding="utf-8"))
            for task_type, tier_str in data.get("learned_routes", {}).items():
                try:
                    self._routes[task_type] = ModelTier(tier_str)
                except ValueError:
                    pass
            for task_type, perf_dict in data.get("performance", {}).items():
                self._perf[task_type] = _TaskPerformance.from_dict(perf_dict)
            self._adaptations = list(data.get("adaptations", []))
        except (json.JSONDecodeError, ValueError):
            pass
