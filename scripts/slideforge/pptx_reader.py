"""Extract text / tables / images from a .pptx into Markdown.

This is the inverse of pptx_builder for round-tripping. Diagram images are
extracted to ``<output_dir>/<basename>-img/`` and referenced via relative
``![alt](path)`` links.
"""
from __future__ import annotations

import logging
import os
from typing import List, Optional, Tuple

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

log = logging.getLogger(__name__)


def pptx_to_markdown(pptx_path: str, out_md_path: Optional[str] = None,
                     img_dir: Optional[str] = None,
                     include_notes: bool = True) -> str:
    """Convert ``pptx_path`` to a markdown document. Returns the md content.

    If ``out_md_path`` is given the markdown is also written to that file.
    Images embedded in the pptx are extracted into ``img_dir`` (default:
    ``<basename>-img`` next to the output md).
    """
    prs = Presentation(pptx_path)
    base = os.path.splitext(os.path.basename(pptx_path))[0]
    if out_md_path is None:
        out_md_path = base + ".md"
    if img_dir is None:
        img_dir = os.path.join(os.path.dirname(os.path.abspath(out_md_path)) or ".", base + "-img")
    os.makedirs(img_dir, exist_ok=True)

    lines: List[str] = []
    title = base
    # Try first slide title for document title
    if prs.slides:
        first_title = _slide_title(prs.slides[0])
        if first_title:
            title = first_title

    lines.append("---")
    lines.append(f'title: "{title}"')
    lines.append(f'source: "{os.path.basename(pptx_path)}"')
    lines.append("---")
    lines.append("")

    for idx, slide in enumerate(prs.slides):
        if idx > 0:
            lines.append("---")
            lines.append("")

        slide_title = _slide_title(slide) or f"Slide {idx + 1}"
        lines.append(f"## {slide_title}")
        layout_name = getattr(slide.slide_layout, "name", None)
        if layout_name:
            lines.append(f"<!-- layout: {layout_name} -->")
        lines.append("")

        for shape in slide.shapes:
            if shape == slide.shapes.title:
                continue
            md = _shape_to_md(shape, slide_index=idx, img_dir=img_dir,
                              md_dir=os.path.dirname(os.path.abspath(out_md_path)) or ".")
            if md:
                lines.append(md)
                lines.append("")

        if include_notes and slide.has_notes_slide:
            note = slide.notes_slide.notes_text_frame.text.strip()
            if note:
                lines.append(f"<!-- notes: {note.replace(chr(10), ' ')} -->")
                lines.append("")

    md = "\n".join(lines).rstrip() + "\n"
    with open(out_md_path, "w", encoding="utf-8") as f:
        f.write(md)
    return md


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _slide_title(slide) -> Optional[str]:
    if slide.shapes.title is not None and slide.shapes.title.has_text_frame:
        text = slide.shapes.title.text_frame.text.strip()
        if text:
            return text
    return None


def _shape_to_md(shape, slide_index: int, img_dir: str, md_dir: str) -> str:
    try:
        if shape.has_text_frame:
            return _text_frame_to_md(shape.text_frame)
        if shape.has_table:
            return _table_to_md(shape.table)
        if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
            return _picture_to_md(shape, slide_index, img_dir, md_dir)
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            parts = []
            for sub in shape.shapes:
                p = _shape_to_md(sub, slide_index, img_dir, md_dir)
                if p:
                    parts.append(p)
            return "\n\n".join(parts)
    except Exception as exc:
        log.debug("skipping shape: %s", exc)
    return ""


def _text_frame_to_md(tf) -> str:
    lines: List[str] = []
    for p in tf.paragraphs:
        text = "".join(run.text for run in p.runs).strip()
        if not text:
            continue
        level = getattr(p, "level", 0) or 0
        if level > 0:
            lines.append("  " * level + "- " + text)
        else:
            # Heuristic: if text frame has multiple paragraphs, treat as bullets;
            # otherwise treat as paragraph.
            lines.append(text)
    if not lines:
        return ""
    multi = sum(1 for l in lines if l.strip()) > 1
    if multi and not any(l.lstrip().startswith("- ") for l in lines):
        return "\n".join("- " + l for l in lines)
    return "\n".join(lines)


def _table_to_md(table) -> str:
    rows = list(table.rows)
    if not rows:
        return ""
    headers = [_cell_text(c) for c in rows[0].cells]
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("|" + "|".join(["---"] * len(headers)) + "|")
    for row in rows[1:]:
        lines.append("| " + " | ".join(_cell_text(c) for c in row.cells) + " |")
    return "\n".join(lines)


def _cell_text(cell) -> str:
    return " ".join(cell.text.split())


def _picture_to_md(shape, slide_index: int, img_dir: str, md_dir: str) -> str:
    try:
        image = shape.image
        ext = image.ext or "png"
        name = f"slide{slide_index + 1}-{shape.shape_id}.{ext}"
        path = os.path.join(img_dir, name)
        with open(path, "wb") as f:
            f.write(image.blob)
        rel = os.path.relpath(path, md_dir)
        alt = (shape.name or "image").replace("\n", " ")
        return f"![{alt}]({rel})"
    except Exception as exc:
        log.debug("could not extract picture: %s", exc)
        return ""
