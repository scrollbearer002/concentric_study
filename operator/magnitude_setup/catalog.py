"""Bundled model catalog and preference-aware ranking for this machine."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable

from .hardware import HardwareProfile


class Preference(str, Enum):
    FASTEST = "Fastest"
    FASTER = "Faster"
    BALANCED = "Balanced"
    SMARTER = "Smarter"
    SMARTEST = "Smartest"

    @classmethod
    def ordered(cls) -> list["Preference"]:
        return [cls.FASTEST, cls.FASTER, cls.BALANCED, cls.SMARTER, cls.SMARTEST]

    def index(self) -> int:
        return self.ordered().index(self)


@dataclass(frozen=True)
class ModelCandidate:
    id: str
    name: str
    quant: str
    params_b: float
    architecture: str  # Dense / MoE
    modalities: str
    context_k: int
    days_ago: int
    intelligence: float  # 0-10
    accuracy: float  # 0-10
    speculation: float  # 0-10
    base_tok_s: float  # reference tok/s on 16GB Apple-class machine
    memory_gb: float
    ollama_tag: str | None = None
    installed: bool = False
    loadable: bool = False

    @property
    def display_name(self) -> str:
        return f"{self.name} ({self.quant})"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RankedModel:
    model: ModelCandidate
    fit_score: float
    speed_tok_s: tuple[float, float]
    memory_label: str
    accuracy_label: str
    speculation_label: str
    intelligence_pct: int
    scores: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model.to_dict(),
            "fit_score": self.fit_score,
            "speed_tok_s": list(self.speed_tok_s),
            "memory_label": self.memory_label,
            "accuracy_label": self.accuracy_label,
            "speculation_label": self.speculation_label,
            "intelligence_pct": self.intelligence_pct,
            "scores": self.scores,
        }


_CATALOG_PATH = Path(__file__).parent / "data" / "models.json"


def load_catalog(path: Path | None = None) -> list[ModelCandidate]:
    catalog_path = path or _CATALOG_PATH
    raw = json.loads(catalog_path.read_text(encoding="utf-8"))
    return [ModelCandidate(**item) for item in raw]


def _speed_scale(hw: HardwareProfile) -> float:
    # Rough relative throughput vs a 16GB Apple-class reference box.
    mem_factor = min(hw.memory_gb / 16.0, 1.4)
    core_factor = min(hw.cores / 10.0, 1.3)
    accel_boost = {"MTL": 1.0, "CUDA": 1.15, "NEON": 0.75, "CPU": 0.45}.get(hw.accel, 0.5)
    return max(0.2, mem_factor * 0.45 + core_factor * 0.25 + accel_boost * 0.55)


def _memory_label(gb: float) -> str:
    if gb < 5:
        return f"Light ({gb:.1f} GB)"
    if gb < 10:
        return f"Medium ({gb:.1f} GB)"
    if gb < 20:
        return f"Heavy ({gb:.1f} GB)"
    return f"Very heavy ({gb:.1f} GB)"


def _accuracy_label(quant: str, accuracy: float) -> str:
    q = quant.upper()
    if "Q8" in q or "FP16" in q or "BF16" in q:
        return f"Very high ({quant})"
    if "Q6" in q or "Q5" in q:
        return f"High ({quant})"
    if "QAT" in q:
        return f"Very high ({quant})"
    if accuracy >= 8.0:
        return f"High ({quant})"
    if accuracy >= 6.5:
        return f"Reduced ({quant})"
    return f"Low ({quant})"


def _speculation_label(score: float) -> str:
    if score <= 0.1:
        return "None"
    if score < 4:
        return "Light"
    if score < 7:
        return "Moderate"
    return "Aggressive"


def _preference_weights(pref: Preference) -> dict[str, float]:
    # Higher preference index → weight intelligence/accuracy more than speed/memory.
    table = {
        Preference.FASTEST: dict(speed=0.45, memory=0.30, intelligence=0.10, accuracy=0.10, speculation=0.05),
        Preference.FASTER: dict(speed=0.35, memory=0.25, intelligence=0.15, accuracy=0.15, speculation=0.10),
        Preference.BALANCED: dict(speed=0.22, memory=0.20, intelligence=0.22, accuracy=0.22, speculation=0.14),
        Preference.SMARTER: dict(speed=0.15, memory=0.15, intelligence=0.30, accuracy=0.28, speculation=0.12),
        Preference.SMARTEST: dict(speed=0.08, memory=0.12, intelligence=0.38, accuracy=0.32, speculation=0.10),
    }
    return table[pref]


def estimate_speed(model: ModelCandidate, hw: HardwareProfile) -> tuple[float, float]:
    scale = _speed_scale(hw)
    # Larger models slow down roughly with parameter count vs 4B baseline.
    size_penalty = max(0.35, (4.0 / max(model.params_b, 0.5)) ** 0.55)
    mid = model.base_tok_s * scale * size_penalty
    low = max(1.0, round(mid * 0.85, 1))
    high = max(low + 1.0, round(mid * 1.05, 1))
    return (low, high)


def fits_memory(model: ModelCandidate, hw: HardwareProfile) -> bool:
    # Leave ~30% headroom for OS + harness.
    budget = hw.memory_gb * 0.7
    return model.memory_gb <= budget


def score_model(model: ModelCandidate, hw: HardwareProfile, pref: Preference) -> RankedModel:
    low, high = estimate_speed(model, hw)
    mid_speed = (low + high) / 2.0

    # Normalize component scores to 0-10 for radar + fit.
    speed_score = min(10.0, (mid_speed / 50.0) * 10.0)
    # Memory score: lighter is better relative to machine budget.
    budget = max(hw.memory_gb * 0.7, 1.0)
    memory_score = max(0.0, min(10.0, (1.0 - (model.memory_gb / budget)) * 10.0))
    if not fits_memory(model, hw):
        memory_score = min(memory_score, 2.0)

    scores = {
        "intelligence": model.intelligence,
        "speed": round(speed_score, 2),
        "speculation": model.speculation,
        "memory": round(memory_score, 2),
        "accuracy": model.accuracy,
    }
    weights = _preference_weights(pref)
    fit = sum(scores[k] * weights[k] for k in weights)
    if not fits_memory(model, hw):
        fit *= 0.35
    # Prefer installed models slightly when browsing "on this computer" merging.
    if model.installed:
        fit += 0.3

    return RankedModel(
        model=model,
        fit_score=round(fit, 3),
        speed_tok_s=(low, high),
        memory_label=_memory_label(model.memory_gb),
        accuracy_label=_accuracy_label(model.quant, model.accuracy),
        speculation_label=_speculation_label(model.speculation),
        intelligence_pct=int(round(model.intelligence * 10)),
        scores=scores,
    )


def rank_models(
    hw: HardwareProfile,
    pref: Preference = Preference.BALANCED,
    catalog: Iterable[ModelCandidate] | None = None,
    limit: int = 10,
) -> list[RankedModel]:
    models = list(catalog) if catalog is not None else load_catalog()
    ranked = [score_model(m, hw, pref) for m in models]
    ranked.sort(key=lambda r: r.fit_score, reverse=True)
    return ranked[:limit]


def installed_models(catalog: Iterable[ModelCandidate] | None = None) -> list[ModelCandidate]:
    models = list(catalog) if catalog is not None else load_catalog()
    return [m for m in models if m.installed or m.loadable]
