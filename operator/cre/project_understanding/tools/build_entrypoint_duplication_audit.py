#!/usr/bin/env python3
"""Build a focused duplication audit for the two main orchestration entrypoints.

This script compares `operator/agent.py` and `operator/cre/test_excalidraw_covt.py`
at the top-level function surface. It is intentionally narrow: the goal is to
support an evidence-backed drift audit between the universal orchestrator and the
flagship traced Excalidraw harness.
"""
from __future__ import annotations

import ast
import csv
import difflib
import io
import json
import keyword
import tokenize
from dataclasses import dataclass, asdict
from pathlib import Path
from token import NAME, NUMBER, OP, STRING
from typing import Iterable

ROOT = Path(__file__).resolve().parents[4]
ARTIFACTS_DIR = ROOT / "operator" / "cre" / "project_understanding" / "artifacts"
TARGETS = [
    ROOT / "operator" / "agent.py",
    ROOT / "operator" / "cre" / "test_excalidraw_covt.py",
]


@dataclass
class FunctionRecord:
    path: str
    name: str
    lineno: int
    end_lineno: int
    text: str


@dataclass
class DuplicationRecord:
    function_name: str
    file_a: str
    line_a: int
    end_line_a: int
    file_b: str
    line_b: int
    end_line_b: int
    raw_similarity: float
    token_similarity: float
    structure_similarity: float
    exact_text: bool
    exact_tokens: bool
    exact_structure: bool
    heuristic_clone_class: str
    interpretation: str


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def iter_top_level_functions(path: Path) -> Iterable[FunctionRecord]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            yield FunctionRecord(
                path=rel(path),
                name=node.name,
                lineno=node.lineno,
                end_lineno=getattr(node, "end_lineno", node.lineno),
                text=ast.get_source_segment(source, node) or "",
            )


def token_stream(text: str, normalize_structure: bool = False) -> list[str]:
    stream = io.StringIO(text)
    tokens: list[str] = []
    try:
        for tok in tokenize.generate_tokens(stream.readline):
            tok_type = tok.type
            tok_val = tok.string
            if tok_type in {tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.COMMENT, tokenize.ENDMARKER}:
                continue
            if normalize_structure:
                if tok_type == NAME and not keyword.iskeyword(tok_val):
                    tokens.append("IDENT")
                    continue
                if tok_type == STRING:
                    tokens.append("STRING")
                    continue
                if tok_type == NUMBER:
                    tokens.append("NUMBER")
                    continue
            tokens.append(tok_val)
    except tokenize.TokenError:
        return []
    return tokens


def ratio(a: str | list[str], b: str | list[str]) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def classify(record: DuplicationRecord) -> tuple[str, str]:
    if record.exact_text:
        return "exact_duplicate", "Top-level function bodies are textually identical."
    if record.exact_tokens:
        return "token_duplicate", "Function bodies are token-identical after formatting/docstring differences."
    if record.exact_structure:
        return "structural_duplicate", "Function bodies share the same structure after identifier/literal normalization."
    if record.structure_similarity >= 0.85:
        return "near_miss_clone", "Functions are structurally very close and likely to drift if maintained separately."
    if record.token_similarity >= 0.60:
        return "partial_duplicate", "Functions share meaningful implementation overlap but have diverged behavior or instrumentation."
    return "shared_responsibility", "Function names overlap, but implementation has materially diverged or is only role-similar."


def main() -> int:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    by_file = {rel(path): {rec.name: rec for rec in iter_top_level_functions(path)} for path in TARGETS}
    common = sorted(set.intersection(*(set(items) for items in by_file.values())))
    file_a, file_b = [rel(p) for p in TARGETS]

    for name in common:
        left = by_file[file_a][name]
        right = by_file[file_b][name]
        left_tokens = token_stream(left.text, normalize_structure=False)
        right_tokens = token_stream(right.text, normalize_structure=False)
        left_struct = token_stream(left.text, normalize_structure=True)
        right_struct = token_stream(right.text, normalize_structure=True)

        rec = DuplicationRecord(
            function_name=name,
            file_a=file_a,
            line_a=left.lineno,
            end_line_a=left.end_lineno,
            file_b=file_b,
            line_b=right.lineno,
            end_line_b=right.end_lineno,
            raw_similarity=round(ratio(left.text, right.text), 3),
            token_similarity=round(ratio(left_tokens, right_tokens), 3),
            structure_similarity=round(ratio(left_struct, right_struct), 3),
            exact_text=left.text == right.text,
            exact_tokens=left_tokens == right_tokens,
            exact_structure=left_struct == right_struct,
            heuristic_clone_class="",
            interpretation="",
        )
        rec.heuristic_clone_class, rec.interpretation = classify(rec)
        records.append(rec)

    summary = {
        "files": [file_a, file_b],
        "common_top_level_functions": common,
        "common_function_count": len(common),
        "high_overlap_functions": [asdict(r) for r in records if r.structure_similarity >= 0.6 or r.token_similarity >= 0.6],
        "all_records": [asdict(r) for r in records],
    }

    (ARTIFACTS_DIR / "entrypoint_duplication_audit.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    with (ARTIFACTS_DIR / "entrypoint_duplication_audit.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(records[0]).keys()) if records else [])
        if records:
            writer.writeheader()
            writer.writerows(asdict(r) for r in records)

    print(json.dumps({
        "common_function_count": len(common),
        "high_overlap_count": len(summary["high_overlap_functions"]),
        "functions": [r.function_name for r in records],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
