"""CLI entry: python -m magnitude_setup setup."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _ensure_path() -> None:
    op_root = Path(__file__).resolve().parent.parent
    if str(op_root) not in sys.path:
        sys.path.insert(0, str(op_root))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="magnitude_setup",
        description="Find the right local model for your agent harness (Magnitude-inspired setup).",
    )
    parser.add_argument("--version", action="store_true", help="Print version and exit")
    sub = parser.add_subparsers(dest="command")

    setup = sub.add_parser("setup", help="Interactive hardware-aware model setup")
    setup.add_argument("--demo", action="store_true", default=True, help="Simulate downloads (default)")
    setup.add_argument("--no-demo", action="store_true", help="Attempt real ollama pull when available")
    setup.add_argument("--json", action="store_true", help="Print machine-readable result JSON")
    setup.add_argument(
        "--rich-demo",
        action="store_true",
        help="Render Rich snapshot frames (non-interactive; great for demos/CI)",
    )
    setup.add_argument(
        "--preference",
        default="Smarter",
        choices=["Fastest", "Faster", "Balanced", "Smarter", "Smartest"],
    )
    setup.add_argument("--harness", default="concentric")
    setup.add_argument("--output-dir", default="operator/cre/runs/magnitude_setup_demo")
    setup.add_argument("--select", type=int, default=1, help="1-based model index for non-interactive modes")

    profile = sub.add_parser("profile", help="Print hardware profile only")
    profile.add_argument("--json", action="store_true")

    rank = sub.add_parser("rank", help="Rank models for this machine and exit")
    rank.add_argument(
        "--preference",
        default="Balanced",
        choices=["Fastest", "Faster", "Balanced", "Smarter", "Smartest"],
    )
    rank.add_argument("--json", action="store_true")
    rank.add_argument("--limit", type=int, default=10)
    return parser


def main(argv: list[str] | None = None) -> int:
    _ensure_path()
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] not in {"setup", "profile", "rank", "-h", "--help", "--version"}:
        if argv[0].startswith("-"):
            argv = ["setup", *argv]

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.version:
        from magnitude_setup import __version__

        print(__version__)
        return 0

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "profile":
        from magnitude_setup.hardware import profile_hardware

        hw = profile_hardware()
        if args.json:
            print(json.dumps(hw.to_dict(), indent=2))
        else:
            print(hw.summary_line())
        return 0

    if args.command == "rank":
        from magnitude_setup.catalog import Preference, rank_models
        from magnitude_setup.hardware import profile_hardware

        hw = profile_hardware()
        ranked = rank_models(hw, Preference(args.preference), limit=args.limit)
        if args.json:
            print(json.dumps([r.to_dict() for r in ranked], indent=2))
        else:
            print(hw.summary_line())
            print(f"Preference: {args.preference}")
            for i, r in enumerate(ranked, start=1):
                low, high = r.speed_tok_s
                print(
                    f"{i:2}. {r.model.display_name:28}  fit={r.fit_score:.2f}  "
                    f"~{low:g}-{high:g} tok/s  {r.memory_label}"
                )
        return 0

    if args.command == "setup":
        from magnitude_setup.catalog import Preference, rank_models
        from magnitude_setup.demo_render import render_choose_frame
        from magnitude_setup.hardware import profile_hardware
        from magnitude_setup.install import HARNESSES, simulate_install, write_harness_config
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table

        demo = not args.no_demo
        out = Path(args.output_dir)
        hw = profile_hardware()
        pref = Preference(args.preference)
        ranked = rank_models(hw, pref)
        idx = max(0, min(len(ranked) - 1, args.select - 1))
        chosen = ranked[idx]

        interactive = (
            not args.json
            and not args.rich_demo
            and sys.stdout.isatty()
            and sys.stdin.isatty()
        )

        if interactive:
            from magnitude_setup.tui import run_tui

            result = run_tui(demo=demo, output_dir=out, preference=args.preference)
            if args.json:
                print(json.dumps(result, indent=2))
            return 0 if not result.get("cancelled") else 1

        console = Console(stderr=args.json)
        console.print(render_choose_frame(hw, pref, ranked, idx))
        mid = None
        for status, pct in simulate_install(chosen, demo=True, delay_s=0.0):
            mid = (status, pct)
            if pct >= 0.78:
                break
        if mid:
            console.print()
            console.print(render_choose_frame(hw, pref, ranked, idx, progress=mid))

        path = write_harness_config(
            ranked=chosen,
            harness_id=args.harness,
            preference=pref.value,
            hardware=hw.to_dict(),
            output_dir=out,
            demo=demo,
        )

        harness_table = Table(title="Select harness", box=None)
        harness_table.add_column("#")
        harness_table.add_column("Harness")
        harness_table.add_column("Notes")
        for i, h in enumerate(HARNESSES, start=1):
            mark = ">" if h["id"] == args.harness else " "
            harness_table.add_row(f"{mark}{i}", h["name"], h["blurb"])
        console.print()
        console.print(Panel(harness_table, border_style="blue", title="● Select harness"))
        console.print(f"[green]Wrote[/green] {path}")

        result = {
            "hardware": hw.to_dict(),
            "preference": pref.value,
            "selected_model": chosen.to_dict(),
            "harness_id": args.harness,
            "config_path": str(path),
            "ranked": [r.to_dict() for r in ranked],
            "demo": demo,
        }
        if args.json:
            print(json.dumps(result, indent=2))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
