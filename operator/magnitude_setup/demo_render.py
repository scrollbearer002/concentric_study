"""Rich fallback renderer for demo / non-TTY / CI captures."""

from __future__ import annotations

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .catalog import Preference, RankedModel, rank_models
from .hardware import HardwareProfile, profile_hardware
from .install import HARNESSES, simulate_install, write_harness_config
from .radar import metric_lines, render_radar
from pathlib import Path


def _stepper(step: int) -> Text:
    labels = ["Choose model", "Install model", "Select harness"]
    out = Text()
    for i, label in enumerate(labels):
        if i < step:
            out.append(f"● {label}", style="cyan")
        elif i == step:
            out.append(f"● {label}", style="bold cyan")
        else:
            out.append(f"○ {label}", style="dim")
        if i < len(labels) - 1:
            out.append("  ——  ", style="dim")
    return out


def _preference_bar(pref: Preference) -> Text:
    out = Text()
    for i, p in enumerate(Preference.ordered()):
        if i:
            out.append(" — ", style="dim")
        if p is pref:
            out.append(f"[{p.value}]", style="bold cyan")
        else:
            out.append(p.value, style="dim")
    return out


def render_choose_frame(
    hw: HardwareProfile,
    pref: Preference,
    ranked: list[RankedModel],
    selected: int = 0,
    progress: tuple[str, float] | None = None,
) -> Panel:
    header = Text.assemble(
        ("MAGNITUDE SETUP", "bold"),
        "\n",
        _stepper(0),
        "\n",
        (hw.summary_line(), "dim cyan"),
        "\n\n",
        _preference_bar(pref),
    )

    body = Table.grid(expand=True, padding=(0, 2))
    left = Table(show_header=True, box=None, pad_edge=False, expand=True)
    left.add_column("RECOMMENDED MODELS", style="white")
    for i, r in enumerate(ranked[:10], start=1):
        prefix = ">" if i - 1 == selected else " "
        tag = "  Load" if r.model.loadable and not (i - 1 == selected) else ""
        style = "bold cyan" if i - 1 == selected else ""
        left.add_row(Text(f"{prefix} {i}. {r.model.display_name}{tag}", style=style))

    local = [r for r in ranked if r.model.installed]
    if local:
        left.add_row("")
        left.add_row(Text("ON THIS COMPUTER", style="bold dim"))
        for r in local[:4]:
            left.add_row(Text(f"  {r.model.name}  Load", style="dim"))

    current = ranked[selected]
    radar = render_radar(
        [
            current.scores["intelligence"],
            current.scores["speed"],
            current.scores["speculation"],
            current.scores["memory"],
            current.scores["accuracy"],
        ]
    )
    right = Text()
    right.append(f"{current.model.display_name}\n", style="bold")
    right.append(
        f"{current.model.context_k}K CONTEXT · {current.model.days_ago} days ago · "
        f"{current.model.architecture} · {current.model.modalities}\n\n",
        style="dim",
    )
    right.append(radar + "\n\n", style="cyan")
    for line in metric_lines(current):
        right.append(line + "\n", style="white")

    body.add_row(left, right)

    progress_render: Text | str = ""
    if progress:
        label, pct = progress
        filled = int(40 * pct)
        progress_render = Text(
            f"{label}\n[{'█' * filled}{'░' * (40 - filled)}] {pct:.0%}\n",
            style="cyan",
        )

    footer = Text("←/→ change preferences  ↑/↓ choose models  Enter to download  Ctrl+C to exit", style="dim")
    content = Group(header, Text(""), progress_render, body, Text(""), footer)
    return Panel(content, border_style="blue", title="magnitude setup", subtitle="inspired recreation")


def run_demo(
    *,
    preference: str = "Smarter",
    output_dir: Path | None = None,
    harness_id: str = "concentric",
    console: Console | None = None,
) -> dict:
    console = console or Console()
    hw = profile_hardware()
    pref = Preference(preference)
    ranked = rank_models(hw, pref)
    selected = 0

    console.print(render_choose_frame(hw, pref, ranked, selected))
    console.print()

    chosen = ranked[selected]
    # Show a mid-progress install frame for walkthrough evidence
    mid = None
    for status, pct in simulate_install(chosen, demo=True, delay_s=0.0):
        mid = (status, pct)
        if pct >= 0.78:
            break
    if mid:
        console.print(render_choose_frame(hw, pref, ranked, selected, progress=mid))
        console.print()

    out = output_dir or Path("operator/cre/runs/magnitude_setup_demo")
    config_path = write_harness_config(
        ranked=chosen,
        harness_id=harness_id,
        preference=pref.value,
        hardware=hw.to_dict(),
        output_dir=out,
        demo=True,
    )

    harness_table = Table(title="Select harness", box=None)
    harness_table.add_column("#")
    harness_table.add_column("Harness")
    harness_table.add_column("Notes")
    for i, h in enumerate(HARNESSES, start=1):
        mark = ">" if h["id"] == harness_id else " "
        harness_table.add_row(f"{mark}{i}", h["name"], h["blurb"])
    console.print(Panel(harness_table, border_style="blue", title="● Select harness"))
    console.print(f"[green]Wrote[/green] {config_path}")

    return {
        "hardware": hw.to_dict(),
        "preference": pref.value,
        "selected_model": chosen.to_dict(),
        "harness_id": harness_id,
        "config_path": str(config_path),
        "ranked": [r.to_dict() for r in ranked],
    }
