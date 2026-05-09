"""Build a .pptx from a parsed Deck (slide IR), inheriting an optional template.

Design choices
--------------
* When a ``template`` path is provided we open it as the base presentation
  (``Presentation(template_path)``). This is the simplest way to inherit
  masters/layouts/theme/fonts verbatim. Any pre-existing slides in the
  template are **removed** so the output starts clean.
* When no template is given we use python-pptx's built-in default theme.
* Layout selection per slide: explicit alias/index/name, then auto-pick
  based on content (chart > image-only > text-only > standard).
"""
from __future__ import annotations

import logging
import os
from copy import deepcopy
from typing import Any, Iterable, List, Optional

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches, Pt

from . import diagrams as _diagrams
from .md_parser import (
    BulletItem,
    BulletList,
    Deck,
    DiagramBlock,
    ImageBlock,
    Paragraph,
    Slide,
    TableBlock,
)
from .template_style import resolve_layout

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_pptx(deck: Deck, output_path: str, template_path: Optional[str] = None,
               img_dir: Optional[str] = None) -> str:
    """Build the deck and save to ``output_path``. Returns the saved path."""
    template_path = template_path or deck.front_matter.get("template")
    if template_path:
        template_path = os.path.expanduser(template_path)
        if not os.path.exists(template_path):
            log.warning("template not found: %s — using built-in default", template_path)
            template_path = None

    prs = Presentation(template_path) if template_path else Presentation()
    _strip_existing_slides(prs)

    img_dir = img_dir or os.path.join(os.path.dirname(os.path.abspath(output_path)) or ".", "_diagrams")

    theme = deck.front_matter.get("theme") or {}
    primary_color = _parse_color(theme.get("primary_color"))
    body_font = theme.get("font")

    # Title slide from front-matter (only if first slide isn't already a cover)
    fm_title = deck.front_matter.get("title")
    fm_subtitle = deck.front_matter.get("subtitle")
    if fm_title and (not deck.slides or (deck.slides[0].layout or "").lower() not in ("cover", "title-slide")):
        _add_title_slide(prs, fm_title, fm_subtitle, primary_color, body_font)

    for slide_ir in deck.slides:
        _add_slide(prs, slide_ir, img_dir=img_dir, primary_color=primary_color, body_font=body_font)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
    prs.save(output_path)
    return output_path


# ---------------------------------------------------------------------------
# Slide construction
# ---------------------------------------------------------------------------


def _add_title_slide(prs, title: str, subtitle: Optional[str],
                     primary_color: Optional[RGBColor], body_font: Optional[str]):
    layout = resolve_layout(prs, "cover")
    slide = prs.slides.add_slide(layout)
    if slide.shapes.title is not None:
        _set_text(slide.shapes.title.text_frame, title, font=body_font, color=primary_color, bold=True)
    if subtitle:
        for ph in slide.placeholders:
            if ph.placeholder_format.idx != 0 and ph.has_text_frame:
                _set_text(ph.text_frame, subtitle, font=body_font)
                break


def _add_slide(prs, ir: Slide, img_dir: str,
               primary_color: Optional[RGBColor], body_font: Optional[str]):
    layout_spec = ir.layout or _auto_select_layout(ir)
    layout = resolve_layout(prs, layout_spec)
    slide = prs.slides.add_slide(layout)

    # Title
    if ir.title and slide.shapes.title is not None:
        _set_text(slide.shapes.title.text_frame, ir.title, font=body_font,
                  color=primary_color, bold=True)

    # Speaker notes
    if ir.notes:
        slide.notes_slide.notes_text_frame.text = ir.notes

    # Body content
    body_ph = _find_body_placeholder(slide)
    text_blocks: List[Any] = []
    visual_blocks: List[Any] = []
    for blk in ir.blocks:
        if isinstance(blk, (Paragraph, BulletList)):
            text_blocks.append(blk)
        else:
            visual_blocks.append(blk)

    # 1) Render text into the body placeholder if available
    if text_blocks and body_ph is not None and body_ph.has_text_frame:
        _render_text_into(body_ph.text_frame, text_blocks, font=body_font)
        text_blocks = []  # consumed
    elif text_blocks:
        # No body placeholder; create a textbox covering left half
        sw = prs.slide_width
        sh = prs.slide_height
        tb = slide.shapes.add_textbox(Inches(0.6), Inches(1.6), sw - Inches(1.2), sh - Inches(2.0))
        _render_text_into(tb.text_frame, text_blocks, font=body_font)
        text_blocks = []

    # 2) Visual blocks (images, tables, diagrams) laid out below or on right
    if visual_blocks:
        _layout_visual_blocks(slide, prs, visual_blocks, img_dir=img_dir,
                              has_text=bool(ir.has_bullets() or any(isinstance(b, Paragraph) for b in ir.blocks)))


def _find_body_placeholder(slide):
    """Return the first non-title text placeholder, if any."""
    for ph in slide.placeholders:
        if ph.placeholder_format.idx == 0:
            continue
        if ph.has_text_frame:
            return ph
    return None


def _render_text_into(tf, blocks: Iterable[Any], font: Optional[str] = None):
    tf.clear()
    first = True
    for blk in blocks:
        if isinstance(blk, Paragraph):
            p = tf.paragraphs[0] if first else tf.add_paragraph()
            first = False
            run = p.add_run()
            run.text = blk.text
            if font:
                run.font.name = font
        elif isinstance(blk, BulletList):
            for item in _flatten_bullets(blk.items):
                p = tf.paragraphs[0] if first else tf.add_paragraph()
                first = False
                p.level = min(item.level, 4)
                run = p.add_run()
                run.text = item.text
                if font:
                    run.font.name = font


def _flatten_bullets(items: List[BulletItem]) -> Iterable[BulletItem]:
    for item in items:
        yield item
        if item.children:
            yield from _flatten_bullets(item.children)


# ---------------------------------------------------------------------------
# Visual layout
# ---------------------------------------------------------------------------


def _layout_visual_blocks(slide, prs, blocks: List[Any], img_dir: str, has_text: bool):
    """Place tables / images / diagrams. Simple heuristic layout.

    * has_text=True   -> visuals occupy the right half of the slide
    * has_text=False  -> visuals tile across the full content area
    """
    sw, sh = prs.slide_width, prs.slide_height
    margin = Inches(0.5)
    top = Inches(1.6)

    if has_text:
        x = sw // 2 + Inches(0.2)
        avail_w = sw - x - margin
    else:
        x = margin
        avail_w = sw - 2 * margin
    avail_h = sh - top - margin

    # split available height across blocks evenly
    n = len(blocks)
    block_h = max(Inches(2), avail_h // max(1, n))

    cur_y = top
    for blk in blocks:
        try:
            if isinstance(blk, ImageBlock):
                _add_image_block(slide, blk, x, cur_y, avail_w, block_h)
            elif isinstance(blk, TableBlock):
                _add_table_block(slide, blk, x, cur_y, avail_w, block_h)
            elif isinstance(blk, DiagramBlock):
                _add_diagram_block(slide, blk, x, cur_y, avail_w, block_h, img_dir=img_dir)
        except Exception as exc:
            log.warning("failed to place %s: %s", type(blk).__name__, exc)
        cur_y += block_h


def _add_image_block(slide, blk: ImageBlock, x, y, w, h):
    if not os.path.exists(blk.path):
        log.warning("image not found: %s", blk.path)
        _add_caption(slide, x, y, w, Inches(0.4), f"[missing image: {blk.path}]")
        return
    pic = slide.shapes.add_picture(blk.path, x, y, width=w)
    if pic.height > h:
        ratio = h / pic.height
        pic.height = int(pic.height * ratio)
        pic.width = int(pic.width * ratio)
    if blk.alt:
        _add_caption(slide, x, y + pic.height + Emu(50000), w, Inches(0.3), blk.alt)


def _add_diagram_block(slide, blk: DiagramBlock, x, y, w, h, img_dir: str):
    png_path = None
    lang = (blk.language or "").lower()
    if lang in ("mermaid", "mmd"):
        png_path = _diagrams.render_mermaid(blk.code, img_dir)
    if not png_path:
        png_path = _diagrams.make_placeholder_png(img_dir, label=blk.language or "diagram")
    pic = slide.shapes.add_picture(png_path, x, y, width=w)
    if pic.height > h:
        ratio = h / pic.height
        pic.height = int(pic.height * ratio)
        pic.width = int(pic.width * ratio)
    if blk.caption:
        _add_caption(slide, x, y + pic.height + Emu(50000), w, Inches(0.3), blk.caption)


def _add_table_block(slide, blk: TableBlock, x, y, w, h):
    rows = len(blk.rows) + 1
    cols = max(1, len(blk.headers))
    tbl_shape = slide.shapes.add_table(rows, cols, x, y, w, min(h, Inches(0.4) * rows))
    tbl = tbl_shape.table
    for j, header in enumerate(blk.headers):
        if j >= cols:
            break
        cell = tbl.cell(0, j)
        cell.text = header
        for p in cell.text_frame.paragraphs:
            for r in p.runs:
                r.font.bold = True
    for i, row in enumerate(blk.rows, start=1):
        for j, val in enumerate(row):
            if j >= cols:
                break
            tbl.cell(i, j).text = str(val)


def _add_caption(slide, x, y, w, h, text: str):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.text = text
    for p in tf.paragraphs:
        p.alignment = PP_ALIGN.CENTER
        for r in p.runs:
            r.font.size = Pt(10)
            r.font.italic = True
            r.font.color.rgb = RGBColor(0x60, 0x60, 0x60)


# ---------------------------------------------------------------------------
# Auto layout selection
# ---------------------------------------------------------------------------


def _auto_select_layout(ir: Slide) -> str:
    if ir.has_diagram() and (ir.has_bullets() or any(isinstance(b, Paragraph) for b in ir.blocks)):
        return "two-column"
    if ir.has_diagram() or ir.has_image() and not ir.has_bullets():
        return "image"
    if ir.has_table() and not ir.has_bullets():
        return "standard"
    if not ir.blocks and ir.title:
        return "section"
    return "standard"


# ---------------------------------------------------------------------------
# Misc helpers
# ---------------------------------------------------------------------------


def _strip_existing_slides(prs: Presentation):
    sldIdLst = prs.slides._sldIdLst  # noqa: SLF001
    for sldId in list(sldIdLst):
        rId = sldId.get(
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        )
        try:
            prs.part.drop_rel(rId)
        except Exception:
            pass
        sldIdLst.remove(sldId)


def _set_text(tf, text: str, font: Optional[str] = None,
              color: Optional[RGBColor] = None, bold: Optional[bool] = None):
    tf.clear()
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = text
    if font:
        run.font.name = font
    if color is not None:
        run.font.color.rgb = color
    if bold is not None:
        run.font.bold = bold


def _parse_color(spec: Any) -> Optional[RGBColor]:
    if not spec:
        return None
    if isinstance(spec, RGBColor):
        return spec
    s = str(spec).strip().lstrip("#")
    if len(s) == 6:
        try:
            return RGBColor(int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
        except ValueError:
            return None
    return None
