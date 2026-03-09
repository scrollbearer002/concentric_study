from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import asdict
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parent / "tools" / "build_cre_doc_registry.py"
spec = importlib.util.spec_from_file_location("build_cre_doc_registry", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec is not None
assert spec.loader is not None
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def _records_by_name():
    return {record.name: record for record in mod.build_records()}


def _top_level_text_count() -> int:
    return sum(
        1
        for path in mod.CRE_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in mod.TEXT_SUFFIXES
    )


def test_build_records_classifies_key_doc_situations() -> None:
    records = _records_by_name()

    assert records["PROJECT_PHD_EXHAUSTIVE_DESCRIPTION.md"].category == "canonical_core"
    assert records["DOC_SURFACE_GOVERNANCE_PHD.md"].category == "canonical_core"
    assert records["CURSOR_OFFICIAL_UPDATES_2026_PHD_RESEARCH.md"].category == "canonical_snapshot"
    assert records["REDDIT_PRODUCTIZATION_PLAN_PHD_REVALIDATED.md"].category == "case_study"
    assert records["EXECUTION_SUMMARY.md"].category == "historical_report"
    assert records["SHOWCASE.md"].category == "local_operational"
    assert records["execution_log.txt"].category == "local_log"


def test_historical_and_log_records_point_to_successors() -> None:
    records = _records_by_name()

    historical = records["EXECUTION_SUMMARY.md"]
    assert historical.category == "historical_report"
    assert "CURRENT_ARCHITECTURE_SURFACE_PHD.md" in historical.superseded_by
    assert historical.placement_action == "move_to_archive"

    log_record = records["execution_log.txt"]
    assert log_record.category == "local_log"
    assert "DEBUGGING_THIS_PROJECT_PHD.md" in log_record.superseded_by
    assert log_record.recommended_target == "operator/cre/history/logs/"


def test_main_writes_registry_and_index_consistently() -> None:
    mod.main()

    registry = json.loads(mod.OUTPUT_JSON.read_text(encoding="utf-8"))
    markdown = mod.OUTPUT_MD.read_text(encoding="utf-8")

    assert registry["top_level_path"] == "operator/cre"
    assert registry["source_registry"] == "operator/cre/artifacts/cre_doc_surface_primary_sources.json"
    assert len(registry["records"]) == _top_level_text_count()
    assert "## External Research Basis" in markdown
    assert "ISO/IEC/IEEE 42010" in markdown
    assert "DOC_SURFACE_GOVERNANCE_PHD.md" in markdown


def test_registry_counts_match_built_records() -> None:
    records = mod.build_records()
    registry = json.loads(mod.OUTPUT_JSON.read_text(encoding="utf-8"))

    expected_counts: dict[str, int] = {}
    for record in records:
        expected_counts[record.category] = expected_counts.get(record.category, 0) + 1

    assert registry["counts"] == expected_counts

    registry_records = {entry["name"]: entry for entry in registry["records"]}
    for record in records:
        assert registry_records[record.name] == asdict(record)


def test_source_registry_covers_primary_external_evidence() -> None:
    sources = json.loads(mod.SOURCE_REGISTRY.read_text(encoding="utf-8"))
    urls = {entry["url"] for entry in sources}
    classes = {entry["source_class"] for entry in sources}

    assert len(sources) >= 8
    assert "https://www.iso-architecture.org/ieee-1471/" in urls
    assert "https://www.sei.cmu.edu/library/documenting-software-architectures-in-an-agile-world/" in urls
    assert "https://cacm.acm.org/research/requirements-tracing/" in urls
    assert "standard" in classes
    assert "official_guidance" in classes
    assert "research_paper" in classes
