from __future__ import annotations

from pathlib import Path

from PIL import Image

from agent_infra.verification_gate import VerificationGate
from agent_infra.visual_monitor import VisualMonitor
from screenshot_preprocessor import (
    export_cropped_region,
    inspect_image_artifact,
    load_normalized_image,
    prepare_image_copy,
)


def test_inspect_image_artifact_rejects_plain_text(tmp_path: Path) -> None:
    bad = tmp_path / "not_image.txt"
    bad.write_text("not an image", encoding="utf-8")

    info = inspect_image_artifact(bad)

    assert info.is_valid is False
    assert info.error


def test_prepare_image_copy_flattens_alpha_and_writes_png(tmp_path: Path) -> None:
    src = tmp_path / "alpha.png"
    out = tmp_path / "prepared" / "alpha_prepared.png"

    img = Image.new("RGBA", (10, 10), (255, 0, 0, 128))
    img.save(src)

    info = prepare_image_copy(src, out, profile="verification")

    assert info.is_valid is True
    assert info.normalized_path == str(out)
    with Image.open(out) as prepared:
        assert prepared.mode == "RGB"
        assert prepared.format == "PNG"


def test_export_cropped_region_clamps_padding_to_image_bounds(tmp_path: Path) -> None:
    src = tmp_path / "source.png"
    out = tmp_path / "crop.png"
    Image.new("RGB", (40, 30), (10, 20, 30)).save(src)

    info = export_cropped_region(src, out, (-5, -5, 20, 15), padding=10)

    assert info.is_valid is True
    with Image.open(out) as cropped:
        assert cropped.size == (30, 25)


def test_load_normalized_image_removes_transparency(tmp_path: Path) -> None:
    src = tmp_path / "transparent.png"
    Image.new("RGBA", (5, 5), (0, 0, 0, 0)).save(src)

    normalized = load_normalized_image(src)

    assert normalized.mode == "RGB"
    assert normalized.getpixel((0, 0)) == (255, 255, 255)


def test_verification_gate_rejects_invalid_screenshot_artifact(tmp_path: Path) -> None:
    bad = tmp_path / "bad.png"
    bad.write_text("definitely not a png", encoding="utf-8")

    gate = VerificationGate(
        task_description="Draw a triangle.",
        output_dir=tmp_path / "verification",
    )
    result = gate.verify(screenshot_path=str(bad))

    assert result.passed is False
    assert "Invalid screenshot artifact" in result.verdict


def test_visual_monitor_compare_rejects_invalid_current_image(tmp_path: Path) -> None:
    ref = tmp_path / "reference.png"
    cur = tmp_path / "current.png"
    Image.new("RGB", (10, 10), (255, 255, 255)).save(ref)
    cur.write_text("bad image", encoding="utf-8")

    result = VisualMonitor._pixel_compare(str(ref), str(cur))

    assert result.similarity_score == -1.0
    assert "Invalid current image" in result.assessment
