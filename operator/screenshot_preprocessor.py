"""Screenshot preprocessing utilities for verification and comparison.

Provides lightweight artifact validation, normalization, and ROI export for
the agent's screenshot-heavy workflows. The functions are deliberately
dependency-light: Pillow is required, while `filetype` is used opportunistically
when installed for content-based MIME detection.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from PIL import Image, ImageOps


ProfileName = Literal["comparison", "verification", "ocr"]


@dataclass
class ImageArtifactInfo:
    """Validation and preparation metadata for one image artifact."""

    path: str
    is_valid: bool
    format: str = ""
    mime_type: str = ""
    width: int = 0
    height: int = 0
    detector: str = ""
    normalized_path: str | None = None
    error: str = ""


_PROFILE_MAX_DIMENSION: dict[ProfileName, int | None] = {
    "comparison": None,
    "verification": 2048,
    "ocr": 1600,
}

_RGBA_MODES = {"RGBA", "LA"}


def inspect_image_artifact(path: str | Path) -> ImageArtifactInfo:
    """Validate that a path points to a readable image artifact."""

    artifact_path = Path(path)
    info = ImageArtifactInfo(path=str(artifact_path), is_valid=False)

    if not artifact_path.exists():
        info.error = "file does not exist"
        return info
    if not artifact_path.is_file():
        info.error = "path is not a file"
        return info

    mime_type = ""
    detector = ""
    try:
        sample = artifact_path.read_bytes()
    except OSError as exc:
        info.error = f"read failed: {exc}"
        return info

    try:
        import filetype

        kind = filetype.guess(sample)
        if kind is not None:
            mime_type = kind.mime
            detector = "filetype"
            if not kind.mime.startswith("image/"):
                info.error = f"not an image ({kind.mime})"
                return info
    except Exception:
        pass

    try:
        with Image.open(artifact_path) as image:
            image.verify()
        with Image.open(artifact_path) as image:
            info.format = str(image.format or "").upper()
            info.width, info.height = image.size
    except Exception as exc:
        info.error = f"invalid image data: {exc}"
        return info

    if not mime_type:
        fmt = info.format.lower()
        if fmt:
            mime_type = f"image/{fmt}"
            detector = detector or "pillow"

    info.is_valid = True
    info.mime_type = mime_type
    info.detector = detector or "pillow"
    return info


def load_normalized_image(
    path: str | Path,
    *,
    mode: str = "RGB",
    background: tuple[int, int, int] = (255, 255, 255),
) -> Image.Image:
    """Open and normalize an image for downstream pixel analysis."""

    info = inspect_image_artifact(path)
    if not info.is_valid:
        raise ValueError(f"Invalid image artifact at {path}: {info.error}")

    with Image.open(path) as image:
        normalized = ImageOps.exif_transpose(image)

        if mode == "RGB" and (
            normalized.mode in _RGBA_MODES or "transparency" in normalized.info
        ):
            alpha = normalized.convert("RGBA")
            composite = Image.new("RGBA", alpha.size, background + (255,))
            normalized = Image.alpha_composite(composite, alpha).convert("RGB")
        elif normalized.mode != mode:
            normalized = normalized.convert(mode)

        return normalized.copy()


def prepare_image_copy(
    source_path: str | Path,
    dest_path: str | Path,
    *,
    profile: ProfileName = "verification",
    background: tuple[int, int, int] = (255, 255, 255),
) -> ImageArtifactInfo:
    """Validate and write a normalized image copy for a specific workflow."""

    info = inspect_image_artifact(source_path)
    if not info.is_valid:
        return info

    output_path = Path(dest_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    image = load_normalized_image(source_path, mode="RGB", background=background)
    max_dimension = _PROFILE_MAX_DIMENSION[profile]
    if max_dimension and max(image.size) > max_dimension:
        image.thumbnail((max_dimension, max_dimension), Image.LANCZOS)

    image.save(output_path, format="PNG")

    prepared = inspect_image_artifact(output_path)
    prepared.normalized_path = str(output_path)
    return prepared


def export_cropped_region(
    source_path: str | Path,
    dest_path: str | Path,
    box: tuple[int, int, int, int],
    *,
    padding: int = 0,
    profile: ProfileName = "ocr",
) -> ImageArtifactInfo:
    """Export a cropped and normalized region of interest."""

    image = load_normalized_image(source_path, mode="RGB")
    x1, y1, x2, y2 = box
    left = max(0, min(x1, x2) - padding)
    top = max(0, min(y1, y2) - padding)
    right = min(image.width, max(x1, x2) + padding)
    bottom = min(image.height, max(y1, y2) + padding)
    if right <= left or bottom <= top:
        return ImageArtifactInfo(
            path=str(source_path),
            is_valid=False,
            error="invalid crop box",
        )

    cropped = image.crop((left, top, right, bottom))
    output_path = Path(dest_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    max_dimension = _PROFILE_MAX_DIMENSION[profile]
    if max_dimension and max(cropped.size) > max_dimension:
        cropped.thumbnail((max_dimension, max_dimension), Image.LANCZOS)

    cropped.save(output_path, format="PNG")
    prepared = inspect_image_artifact(output_path)
    prepared.normalized_path = str(output_path)
    return prepared
