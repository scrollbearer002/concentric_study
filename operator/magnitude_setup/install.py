"""Install simulation / optional ollama pull, plus harness config writer."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterator

from .catalog import ModelCandidate, RankedModel


ProgressCb = Callable[[str, float], None]


HARNESSES = [
    {
        "id": "concentric",
        "name": "Concentric Study",
        "blurb": "Wire local model into inference_router LOCAL tier",
    },
    {
        "id": "pi",
        "name": "Pi",
        "blurb": "Configure Pi agent to use the selected local model",
    },
    {
        "id": "opencode",
        "name": "OpenCode",
        "blurb": "Write OpenCode provider endpoint for local inference",
    },
    {
        "id": "claude-code",
        "name": "Claude Code",
        "blurb": "Point Claude Code at a local OpenAI-compatible endpoint",
    },
    {
        "id": "codex",
        "name": "Codex",
        "blurb": "Configure Codex client for local model traffic",
    },
    {
        "id": "cline",
        "name": "Cline",
        "blurb": "Set Cline custom model provider to localhost",
    },
    {
        "id": "builtin",
        "name": "Built-in harness",
        "blurb": "Use Magnitude-style built-in agent harness",
    },
]


@dataclass
class SetupResult:
    model_id: str
    model_name: str
    harness_id: str
    preference: str
    hardware: dict
    config_path: str
    demo: bool

    def to_dict(self) -> dict:
        return asdict(self)


def simulate_install(
    ranked: RankedModel,
    *,
    demo: bool = True,
    steps: int = 20,
    delay_s: float = 0.03,
) -> Iterator[tuple[str, float]]:
    """Yield (status, progress 0..1) while 'installing' a model."""
    name = ranked.model.display_name
    phases = [
        (0.15, f"Verifying {name}..."),
        (0.55, f"Downloading {name}..."),
        (0.85, f"Loading {name} into memory..."),
        (1.0, f"Ready: {name}"),
    ]
    if not demo and ranked.model.ollama_tag and shutil.which("ollama"):
        yield (f"Pulling {ranked.model.ollama_tag} via ollama...", 0.05)
        try:
            proc = subprocess.Popen(
                ["ollama", "pull", ranked.model.ollama_tag],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            assert proc.stdout is not None
            for i, _line in enumerate(proc.stdout):
                pct = min(0.95, 0.05 + (i + 1) * 0.02)
                yield (f"Pulling {ranked.model.ollama_tag}...", pct)
            proc.wait(timeout=600)
            yield (f"Ready: {name}", 1.0)
            return
        except Exception as exc:
            yield (f"ollama pull failed ({exc}); falling back to demo install", 0.2)

    cursor = 0.0
    for target, label in phases:
        while cursor < target:
            cursor = min(target, cursor + (1.0 / steps))
            yield (label, cursor)
            if delay_s:
                time.sleep(delay_s)


def write_harness_config(
    *,
    ranked: RankedModel,
    harness_id: str,
    preference: str,
    hardware: dict,
    output_dir: Path,
    demo: bool = True,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "local_model_setup.json"
    payload = {
        "version": 1,
        "demo": demo,
        "preference": preference,
        "hardware": hardware,
        "model": {
            "id": ranked.model.id,
            "name": ranked.model.display_name,
            "quant": ranked.model.quant,
            "ollama_tag": ranked.model.ollama_tag,
            "context_k": ranked.model.context_k,
            "scores": ranked.scores,
            "speed_tok_s": list(ranked.speed_tok_s),
            "memory_label": ranked.memory_label,
        },
        "harness": next((h for h in HARNESSES if h["id"] == harness_id), {"id": harness_id}),
        "endpoint": {
            "base_url": "http://127.0.0.1:11434/v1",
            "api_style": "openai-compatible",
        },
        "concentric": {
            "inference_router_local_model": ranked.model.ollama_tag or ranked.model.id,
            "enable_local": True,
        },
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    # Also drop a tiny dotenv-style hint for operator tooling.
    env_path = output_dir / "local_model.env"
    env_path.write_text(
        "\n".join(
            [
                f"CONCENTRIC_LOCAL_MODEL={ranked.model.ollama_tag or ranked.model.id}",
                "CONCENTRIC_ENABLE_LOCAL=1",
                f"CONCENTRIC_LOCAL_HARNESS={harness_id}",
                f"CONCENTRIC_MODEL_DISPLAY={ranked.model.display_name}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def mark_installed(model: ModelCandidate) -> ModelCandidate:
    return ModelCandidate(**{**model.to_dict(), "installed": True, "loadable": True})
