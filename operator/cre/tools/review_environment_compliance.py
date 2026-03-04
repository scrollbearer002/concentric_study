from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
ARTIFACTS = ROOT / "operator" / "cre" / "artifacts"
DEFAULT_LOG = ARTIFACTS / "environment_answer_compliance_log.jsonl"
DEFAULT_JSON = ARTIFACTS / "environment_answer_compliance_review.json"
DEFAULT_MD = ROOT / "operator" / "cre" / "ENVIRONMENT_COMPLIANCE_REVIEW_PHD.md"


def load_entries(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    entries: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        entries.append(json.loads(line))
    return entries


def summarize(entries: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(e.get("status", "unknown") for e in entries)
    reason_counts = Counter()
    for entry in entries:
        for reason in entry.get("failure_reasons", []):
            reason_counts[reason] += 1
    misses = [e for e in entries if e.get("status") != "pass"]
    return {
        "total_entries": len(entries),
        "status_counts": dict(status_counts),
        "miss_count": len(misses),
        "top_failure_reasons": reason_counts.most_common(10),
        "recent_misses": misses[-10:],
    }


def write_markdown(summary: dict[str, Any], out_path: Path) -> None:
    lines = [
        "# Environment Compliance Review (PhD)",
        "",
        f"- total entries: `{summary['total_entries']}`",
        f"- miss count: `{summary['miss_count']}`",
        "",
        "## Status Counts",
        "",
    ]
    for status, count in sorted(summary["status_counts"].items()):
        lines.append(f"- `{status}`: `{count}`")
    lines.extend(["", "## Top Failure Reasons", ""])
    if summary["top_failure_reasons"]:
        for reason, count in summary["top_failure_reasons"]:
            lines.append(f"- `{reason}`: `{count}`")
    else:
        lines.append("- None")
    lines.extend(["", "## Recent Misses", ""])
    if summary["recent_misses"]:
        for entry in summary["recent_misses"]:
            lines.append(f"### `{entry.get('timestamp_utc', 'unknown')}`")
            lines.append(f"- task: `{entry.get('task_summary', '')}`")
            lines.append(f"- status: `{entry.get('status', '')}`")
            lines.append(f"- reasons: {', '.join(entry.get('failure_reasons', [])) or 'None'}")
            lines.append(f"- notes: {entry.get('notes', '') or 'None'}")
            lines.append("")
    else:
        lines.append("- No misses recorded.")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review environment-justification compliance log.")
    parser.add_argument("--log", default=str(DEFAULT_LOG))
    parser.add_argument("--json-out", default=str(DEFAULT_JSON))
    parser.add_argument("--md-out", default=str(DEFAULT_MD))
    parser.add_argument("--print-summary", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    entries = load_entries(Path(args.log))
    summary = summarize(entries)
    Path(args.json_out).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_markdown(summary, Path(args.md_out))
    if args.print_summary:
        print(json.dumps(summary, indent=2))
    else:
        print(Path(args.json_out))
        print(Path(args.md_out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
