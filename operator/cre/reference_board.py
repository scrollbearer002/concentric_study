"""Reference-board helpers for grounded art and visual planning.

This module keeps the first implementation intentionally small:
- load the checked-in template
- populate a reference board for a concrete subject
- persist board / subject brief / composition plan as stable artifacts

It is repo-safe and does not depend on the browser/runtime hot path.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
TEMPLATE_PATH = ROOT / "artifacts" / "reference_board_template.json"


@dataclass(frozen=True)
class ReferenceItem:
    title: str
    url: str | None
    rationale: str
    source_type: str = "reference"
    query: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)


@dataclass
class ReferenceBoard:
    schema: str
    purpose: str
    lanes: list[dict[str, Any]]
    subject_brief: dict[str, Any]
    composition_plan: dict[str, Any]

    @classmethod
    def from_template(cls) -> ReferenceBoard:
        payload = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
        return cls(
            schema=payload["schema"],
            purpose=payload["purpose"],
            lanes=payload["lanes"],
            subject_brief=payload["subject_brief"],
            composition_plan=payload["composition_plan"],
        )

    def add_reference(self, lane_name: str, item: ReferenceItem) -> None:
        for lane in self.lanes:
            if lane["name"] == lane_name:
                lane.setdefault("references", []).append(item.to_dict())
                return
        raise KeyError(f"Unknown reference-board lane: {lane_name}")

    def add_research_query(
        self,
        lane_name: str,
        *,
        title: str,
        query: str,
        rationale: str,
        source_type: str = "search_query",
    ) -> None:
        self.add_reference(
            lane_name,
            ReferenceItem(
                title=title,
                url=None,
                rationale=rationale,
                source_type=source_type,
                query=query,
            ),
        )

    def set_subject_brief(
        self,
        *,
        one_sentence_goal: str,
        must_have_parts: list[str],
        must_avoid: list[str],
        style_notes: list[str],
    ) -> None:
        self.subject_brief = {
            "one_sentence_goal": one_sentence_goal,
            "must_have_parts": must_have_parts,
            "must_avoid": must_avoid,
            "style_notes": style_notes,
        }

    def set_composition_plan(
        self,
        *,
        pose: str,
        camera_angle: str,
        primary_subject_bbox_goal: str | None = None,
        passes: list[str] | None = None,
    ) -> None:
        self.composition_plan = {
            "primary_subject_bbox_goal": primary_subject_bbox_goal
            or self.composition_plan.get(
                "primary_subject_bbox_goal",
                "occupy 35%-60% of drawable area unless task says otherwise",
            ),
            "pose": pose,
            "camera_angle": camera_angle,
            "passes": passes
            or self.composition_plan.get(
                "passes",
                ["silhouette", "structure", "detail", "color", "verification"],
            ),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "purpose": self.purpose,
            "lanes": self.lanes,
            "subject_brief": self.subject_brief,
            "composition_plan": self.composition_plan,
        }

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")

    def save_split_artifacts(self, output_dir: str | Path, stem: str) -> dict[str, Path]:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        board_path = output / f"{stem}_reference_board.json"
        subject_path = output / f"{stem}_subject_brief.json"
        composition_path = output / f"{stem}_composition_plan.json"
        self.save(board_path)
        subject_path.write_text(
            json.dumps(self.subject_brief, indent=2) + "\n",
            encoding="utf-8",
        )
        composition_path.write_text(
            json.dumps(self.composition_plan, indent=2) + "\n",
            encoding="utf-8",
        )
        return {
            "reference_board": board_path,
            "subject_brief": subject_path,
            "composition_plan": composition_path,
        }


def build_polo_bear_panther_reference_board() -> ReferenceBoard:
    board = ReferenceBoard.from_template()
    board.add_reference(
        "subject_identity",
        ReferenceItem(
            title="Ralph Lauren official site",
            url="https://www.ralphlauren.com/",
            rationale="Use as the canonical source for Ralph Lauren / Polo brand identity and styling cues.",
        ),
    )
    board.add_reference(
        "subject_identity",
        ReferenceItem(
            title="Ralph Lauren media assets",
            url="https://corporate.ralphlauren.com/media-assets",
            rationale="Use for press-approved brand imagery and logo-adjacent visual identity cues.",
        ),
    )
    board.add_reference(
        "real_world_anatomy_or_form",
        ReferenceItem(
            title="Britannica polar bear reference",
            url="https://www.britannica.com/animal/polar-bear",
            rationale="Use for real polar bear anatomy: muzzle, shoulder mass, ear placement, and limb proportions.",
        ),
    )
    board.add_reference(
        "costume_or_style_family",
        ReferenceItem(
            title="Smithsonian Black Panther Party uniform reference",
            url="https://nmaahc.si.edu/explore/stories/black-panther-party-uniform",
            rationale="Use for historically grounded clothing cues: beret, sunglasses, dark leather jacket, and political styling.",
        ),
    )
    board.set_subject_brief(
        one_sentence_goal=(
            "Draw a real-anatomy polar bear styled with Ralph Lauren identity cues and historical "
            "Black Panther Party-inspired clothing in a readable full-body composition."
        ),
        must_have_parts=[
            "full polar bear body",
            "realistic bear head and muzzle proportions",
            "Ralph Lauren / Polo identity cues",
            "black beret",
            "dark sunglasses",
            "dark jacket silhouette",
        ],
        must_avoid=[
            "canvas clipping",
            "generic costume drift",
            "logo-free random fashion styling",
            "Marvel/Wakanda suit assumptions unless explicitly requested",
        ],
        style_notes=[
            "Use real polar bear massing before costume detail.",
            "Prefer a clean, iconic fashion silhouette over excessive line noise.",
            "Keep the entire figure inside the calibrated canvas margins.",
        ],
    )
    board.set_composition_plan(
        pose="three-quarter standing pose with readable torso, arms, and boots",
        camera_angle="straight-on to slight three-quarter view",
        passes=["silhouette", "anatomy", "costume", "detail", "verification"],
    )
    return board


def build_generic_reference_board(
    *,
    request: str,
    primary_subject: str,
    anatomy_anchor: str | None = None,
    identity_anchor: str | None = None,
    style_anchor: str | None = None,
    must_have_parts: list[str] | None = None,
    must_avoid: list[str] | None = None,
    style_notes: list[str] | None = None,
    pose: str = "readable full-subject pose",
    camera_angle: str = "straight-on to slight three-quarter view",
    passes: list[str] | None = None,
) -> ReferenceBoard:
    board = ReferenceBoard.from_template()

    board.add_research_query(
        "subject_identity",
        title=f"{primary_subject} identity references",
        query=f"{primary_subject} official reference images",
        rationale="Use authoritative or canonical images to lock the subject identity before drawing.",
    )
    if identity_anchor:
        board.add_research_query(
            "subject_identity",
            title=f"{identity_anchor} style identity references",
            query=f"{identity_anchor} official design reference",
            rationale="Use the named brand, franchise, or identity source to ground distinctive visual cues.",
        )

    board.add_research_query(
        "real_world_anatomy_or_form",
        title=f"{primary_subject} anatomy/form references",
        query=f"{anatomy_anchor or primary_subject} anatomy reference",
        rationale="Use real-world structure, silhouette, and proportions as the grounding layer.",
    )

    if style_anchor:
        board.add_research_query(
            "costume_or_style_family",
            title=f"{style_anchor} costume/style references",
            query=f"{style_anchor} clothing reference",
            rationale="Use the requested clothing, era, or style family to ground wardrobe and accessories.",
        )

    board.set_subject_brief(
        one_sentence_goal=request,
        must_have_parts=must_have_parts
        or [
            primary_subject,
            "full readable silhouette",
            "recognizable identity cues",
        ],
        must_avoid=must_avoid
        or [
            "canvas clipping",
            "generic costume drift",
            "unreadable silhouette",
        ],
        style_notes=style_notes
        or [
            "Ground the drawing in references before adding detail.",
            "Keep the full subject inside calibrated canvas margins.",
            "Use a multi-pass build: silhouette, structure, detail, color, verification.",
        ],
    )
    board.set_composition_plan(
        pose=pose,
        camera_angle=camera_angle,
        passes=passes
        or ["silhouette", "anatomy", "costume", "detail", "color", "verification"],
    )
    return board
