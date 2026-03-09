#!/usr/bin/env python3
"""Render a markdown document into a simple paginated PDF with no external deps."""

from __future__ import annotations

import re
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path


PAGE_WIDTH = 612
PAGE_HEIGHT = 792
LEFT_MARGIN = 54
RIGHT_MARGIN = 54
TOP_MARGIN = 54
BOTTOM_MARGIN = 54
CONTENT_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN


@dataclass
class Line:
    text: str
    font: str
    size: int
    gap_before: int = 0
    page_break_before: bool = False


def strip_inline_markdown(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    return text.replace("\u2014", "-")


def estimate_wrap_width(font_size: int, indent: int = 0) -> int:
    usable = CONTENT_WIDTH - indent
    return max(24, int(usable / (font_size * 0.55)))


def parse_markdown(markdown: str) -> list[Line]:
    lines: list[Line] = []
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if not paragraph:
            return
        text = strip_inline_markdown(" ".join(part.strip() for part in paragraph if part.strip()))
        if text:
            for chunk in textwrap.wrap(text, width=estimate_wrap_width(11)):
                lines.append(Line(chunk, "F1", 11))
            lines.append(Line("", "F1", 11, gap_before=4))
        paragraph = []

    for raw in markdown.splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            flush_paragraph()
            continue
        if not line.strip():
            flush_paragraph()
            continue
        if line.startswith("---"):
            flush_paragraph()
            lines.append(Line("", "F1", 11, page_break_before=True))
            continue
        if line.startswith("# "):
            flush_paragraph()
            heading = strip_inline_markdown(line[2:].strip())
            lines.append(Line(heading, "F2", 20, gap_before=10, page_break_before=bool(lines)))
            lines.append(Line("", "F1", 11, gap_before=8))
            continue
        if line.startswith("## "):
            flush_paragraph()
            heading = strip_inline_markdown(line[3:].strip())
            lines.append(Line(heading, "F2", 16, gap_before=10))
            lines.append(Line("", "F1", 11, gap_before=4))
            continue
        if line.startswith("### "):
            flush_paragraph()
            heading = strip_inline_markdown(line[4:].strip())
            lines.append(Line(heading, "F2", 13, gap_before=8))
            lines.append(Line("", "F1", 11, gap_before=2))
            continue
        if line.startswith(("- ", "* ")):
            flush_paragraph()
            bullet = strip_inline_markdown(line[2:].strip())
            wrapped = textwrap.wrap(bullet, width=estimate_wrap_width(11, indent=18))
            for idx, chunk in enumerate(wrapped):
                prefix = "• " if idx == 0 else "  "
                lines.append(Line(prefix + chunk, "F1", 11))
            lines.append(Line("", "F1", 11, gap_before=2))
            continue
        paragraph.append(line)

    flush_paragraph()
    return lines


def escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def paginate(lines: list[Line]) -> list[list[tuple[int, Line]]]:
    pages: list[list[tuple[int, Line]]] = []
    current: list[tuple[int, Line]] = []
    y = PAGE_HEIGHT - TOP_MARGIN

    def commit_page() -> None:
        nonlocal current, y
        if current:
            pages.append(current)
        current = []
        y = PAGE_HEIGHT - TOP_MARGIN

    for line in lines:
        if line.page_break_before:
            commit_page()
        gap = line.gap_before
        if gap:
            y -= gap
        line_height = max(14, int(line.size * 1.45))
        if y - line_height < BOTTOM_MARGIN:
            commit_page()
        y -= line_height
        current.append((y, line))

    commit_page()
    return pages


def render_page_stream(page_lines: list[tuple[int, Line]], page_number: int, total_pages: int) -> bytes:
    commands: list[str] = []
    for y, line in page_lines:
        if not line.text:
            continue
        commands.append(
            f"BT /{line.font} {line.size} Tf 1 0 0 1 {LEFT_MARGIN} {y} Tm ({escape_pdf_text(line.text)}) Tj ET"
        )
    footer = f"Page {page_number} of {total_pages}"
    commands.append(
        f"BT /F1 10 Tf 1 0 0 1 {LEFT_MARGIN} 28 Tm ({escape_pdf_text(footer)}) Tj ET"
    )
    return "\n".join(commands).encode("utf-8")


def build_pdf(pages: list[list[tuple[int, Line]]]) -> bytes:
    objects: list[bytes | None] = [None]

    def reserve() -> int:
        objects.append(None)
        return len(objects) - 1

    catalog_id = reserve()
    pages_id = reserve()
    font_regular_id = reserve()
    font_bold_id = reserve()

    page_ids: list[int] = []
    content_ids: list[int] = []

    for _ in pages:
        content_ids.append(reserve())
        page_ids.append(reserve())

    objects[font_regular_id] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    objects[font_bold_id] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>"

    total_pages = len(pages)
    for idx, page in enumerate(pages, start=1):
        content = render_page_stream(page, idx, total_pages)
        content_obj = (
            f"<< /Length {len(content)} >>\nstream\n".encode("utf-8")
            + content
            + b"\nendstream"
        )
        objects[content_ids[idx - 1]] = content_obj
        page_obj = (
            f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
            f"/Resources << /Font << /F1 {font_regular_id} 0 R /F2 {font_bold_id} 0 R >> >> "
            f"/Contents {content_ids[idx - 1]} 0 R >>"
        ).encode("utf-8")
        objects[page_ids[idx - 1]] = page_obj

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[pages_id] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("utf-8")
    objects[catalog_id] = f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode("utf-8")

    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0] * len(objects)

    for obj_id in range(1, len(objects)):
        offsets[obj_id] = len(output)
        output.extend(f"{obj_id} 0 obj\n".encode("utf-8"))
        output.extend(objects[obj_id] or b"<<>>")
        output.extend(b"\nendobj\n")

    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects)}\n".encode("utf-8"))
    output.extend(b"0000000000 65535 f \n")
    for obj_id in range(1, len(objects)):
        output.extend(f"{offsets[obj_id]:010d} 00000 n \n".encode("utf-8"))

    trailer = (
        f"trailer\n<< /Size {len(objects)} /Root {catalog_id} 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    )
    output.extend(trailer.encode("utf-8"))
    return bytes(output)


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: markdown_to_basic_pdf.py <input.md> <output.pdf>", file=sys.stderr)
        return 2

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    markdown = input_path.read_text(encoding="utf-8")
    lines = parse_markdown(markdown)
    pages = paginate(lines)
    pdf = build_pdf(pages)
    output_path.write_bytes(pdf)
    print(f"wrote {output_path} ({len(pages)} pages)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
