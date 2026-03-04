from __future__ import annotations

import json
from pathlib import Path

from reference_board import (
    TEMPLATE_PATH,
    ReferenceBoard,
    build_generic_reference_board,
    build_polo_bear_panther_reference_board,
)


def test_reference_board_template_loads() -> None:
    payload = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    assert payload["schema"] == "reference_board_v1"
    board = ReferenceBoard.from_template()
    assert len(board.lanes) == 3


def test_polo_bear_panther_reference_board_has_expected_lanes_and_artifacts(tmp_path: Path) -> None:
    board = build_polo_bear_panther_reference_board()
    lanes = {lane["name"]: lane["references"] for lane in board.lanes}
    assert len(lanes["subject_identity"]) == 2
    assert len(lanes["real_world_anatomy_or_form"]) == 1
    assert len(lanes["costume_or_style_family"]) == 1
    assert "full polar bear body" in board.subject_brief["must_have_parts"]

    written = board.save_split_artifacts(tmp_path, "demo")
    for path in written.values():
        assert path.exists()
        json.loads(path.read_text(encoding="utf-8"))


def test_generic_reference_board_builds_search_queries_and_artifacts(tmp_path: Path) -> None:
    board = build_generic_reference_board(
        request="Draw a realistic barn owl wearing a vintage aviator jacket at sunset.",
        primary_subject="barn owl",
        anatomy_anchor="barn owl",
        identity_anchor="aviator fashion",
        style_anchor="vintage aviator jacket",
        must_have_parts=["full barn owl body", "owl face disk", "aviator jacket"],
    )

    lanes = {lane["name"]: lane["references"] for lane in board.lanes}
    assert lanes["subject_identity"][0]["query"] == "barn owl official reference images"
    assert lanes["subject_identity"][1]["query"] == "aviator fashion official design reference"
    assert lanes["real_world_anatomy_or_form"][0]["query"] == "barn owl anatomy reference"
    assert lanes["costume_or_style_family"][0]["query"] == "vintage aviator jacket clothing reference"
    assert "full barn owl body" in board.subject_brief["must_have_parts"]

    written = board.save_split_artifacts(tmp_path, "owl_demo")
    for path in written.values():
        assert path.exists()
        json.loads(path.read_text(encoding="utf-8"))
