#!/usr/bin/env python3
"""
Set-of-Mark visual grounding engine.

Draws a numbered Cartesian grid over screenshots for VLM spatial grounding.
Returns a coordinate mapping (box_id -> center x, y) for deterministic clicks.
"""

from __future__ import annotations

import logging
import os
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


class VisualGroundingEngine:
    """Generates Set-of-Mark overlay and coordinate mapping for VLM target extraction."""

    def __init__(self, grid_size: int = 12, output_dir: str = "./") -> None:
        self.grid_size = grid_size
        self.output_dir = output_dir

    def generate_som_overlay(
        self,
        image_path: str,
        output_filename: str = "som_overlay.png",
    ) -> tuple[dict[str, tuple[int, int]], str]:
        """
        Draws a numbered Cartesian grid over the target screenshot.
        Returns (coordinate_map, output_path).
        coordinate_map: {"1": (center_x, center_y), "2": (...), ...}
        """
        output_path = os.path.join(self.output_dir, output_filename)
        coordinate_map: dict[str, tuple[int, int]] = {}

        try:
            img = Image.open(image_path).convert("RGBA")
            width, height = img.size
            overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)

            cell_width = width / self.grid_size
            cell_height = height / self.grid_size

            try:
                font = ImageFont.truetype("Menlo.ttc", size=int(cell_height * 0.3))
            except OSError:
                font = ImageFont.load_default()

            box_id = 1

            for row in range(self.grid_size):
                for col in range(self.grid_size):
                    x1 = col * cell_width
                    y1 = row * cell_height
                    x2 = x1 + cell_width
                    y2 = y1 + cell_height

                    center_x = int(x1 + (cell_width / 2))
                    center_y = int(y1 + (cell_height / 2))
                    coordinate_map[str(box_id)] = (center_x, center_y)

                    draw.rectangle(
                        [x1, y1, x2, y2],
                        outline=(255, 0, 0, 100),
                        width=2,
                    )

                    text_bbox = draw.textbbox((0, 0), str(box_id), font=font)
                    text_w = text_bbox[2] - text_bbox[0]
                    text_h = text_bbox[3] - text_bbox[1]
                    text_x = center_x - (text_w / 2)
                    text_y = center_y - (text_h / 2)

                    draw.rectangle(
                        [
                            text_x - 2,
                            text_y - 2,
                            text_x + text_w + 2,
                            text_y + text_h + 2,
                        ],
                        fill=(0, 0, 0, 180),
                    )
                    draw.text(
                        (text_x, text_y),
                        str(box_id),
                        fill=(255, 255, 255, 255),
                        font=font,
                    )

                    box_id += 1

            final_img = Image.alpha_composite(img, overlay)
            final_img.convert("RGB").save(output_path, quality=100)

            logger.info("SoM grid applied. %s target zones mapped.", box_id - 1)
            return coordinate_map, output_path

        except Exception as e:
            logger.error("Failed to generate SoM overlay: %s", e)
            raise

    # ------------------------------------------------------------------
    # Adaptive resolution SoM (OmniParser-inspired, arxiv:2408.00203)
    # ------------------------------------------------------------------

    _RESOLUTION_PRESETS: dict[str, int] = {
        "coarse": 8,
        "standard": 12,
        "fine": 20,
    }

    def generate_som_overlay_adaptive(
        self,
        image_path: str,
        resolution: str = "standard",
        region: tuple[int, int, int, int] | None = None,
        output_filename: str | None = None,
    ) -> tuple[dict[str, tuple[int, int]], str]:
        """Adaptive-resolution SoM overlay.

        Args:
            image_path: Path to the source screenshot.
            resolution: One of "coarse" (8x8), "standard" (12x12), "fine" (20x20).
            region: Optional (x1, y1, x2, y2) crop rectangle in image pixels.
                    When provided, the grid is applied only to the cropped area
                    and returned coordinates are in the original image space.
            output_filename: Override for the output file name.

        Returns:
            (coordinate_map, output_path) — same contract as generate_som_overlay.
        """
        grid = self._RESOLUTION_PRESETS.get(resolution, 12)
        if output_filename is None:
            output_filename = f"som_overlay_{resolution}.png"
        output_path = os.path.join(self.output_dir, output_filename)
        coordinate_map: dict[str, tuple[int, int]] = {}

        try:
            full_img = Image.open(image_path).convert("RGBA")

            if region is not None:
                rx1, ry1, rx2, ry2 = region
                img = full_img.crop((rx1, ry1, rx2, ry2))
                offset_x, offset_y = rx1, ry1
            else:
                img = full_img
                offset_x, offset_y = 0, 0

            width, height = img.size
            overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)

            cell_w = width / grid
            cell_h = height / grid

            try:
                font = ImageFont.truetype("Menlo.ttc", size=max(10, int(cell_h * 0.3)))
            except OSError:
                font = ImageFont.load_default()

            box_id = 1
            for row in range(grid):
                for col in range(grid):
                    x1 = col * cell_w
                    y1 = row * cell_h
                    x2 = x1 + cell_w
                    y2 = y1 + cell_h

                    cx = int(x1 + cell_w / 2) + offset_x
                    cy = int(y1 + cell_h / 2) + offset_y
                    coordinate_map[str(box_id)] = (cx, cy)

                    draw.rectangle([x1, y1, x2, y2], outline=(255, 0, 0, 100), width=2)

                    text_bbox = draw.textbbox((0, 0), str(box_id), font=font)
                    tw = text_bbox[2] - text_bbox[0]
                    th = text_bbox[3] - text_bbox[1]
                    tx = int(x1 + cell_w / 2) - tw / 2
                    ty = int(y1 + cell_h / 2) - th / 2

                    draw.rectangle([tx - 2, ty - 2, tx + tw + 2, ty + th + 2], fill=(0, 0, 0, 180))
                    draw.text((tx, ty), str(box_id), fill=(255, 255, 255, 255), font=font)

                    box_id += 1

            composited = Image.alpha_composite(img, overlay)

            if region is not None:
                full_copy = full_img.copy()
                full_copy.paste(composited, (offset_x, offset_y))
                full_copy.convert("RGB").save(output_path, quality=100)
            else:
                composited.convert("RGB").save(output_path, quality=100)

            logger.info(
                "Adaptive SoM (%s, %dx%d) applied. %d zones mapped.",
                resolution, grid, grid, box_id - 1,
            )
            return coordinate_map, output_path

        except Exception as e:
            logger.error("Failed to generate adaptive SoM overlay: %s", e)
            raise
