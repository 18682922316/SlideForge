"""Inspect a .pptx template's theme: layouts, fonts, and theme colors.

The goal is to give the rest of the package enough info to *match* a
reference template's look-and-feel when generating new slides.

Most style-matching is achieved by simply opening the template as the base
presentation (so masters/layouts/theme are inherited verbatim by python-pptx).
This module just exposes some inspection helpers and a layout-alias resolver.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pptx import Presentation
from pptx.util import Emu

log = logging.getLogger(__name__)


# Standard layout aliases (semantic name -> common PowerPoint layout names).
# When a user requests a layout via alias we look up these candidates in the
# template's slide_layouts list (case-insensitive substring match).
LAYOUT_ALIASES: Dict[str, List[str]] = {
    "cover":      ["title slide", "title", "cover", "封面"],
    "toc":        ["table of contents", "agenda", "contents", "目录"],
    "section":    ["section header", "section", "chapter", "章节"],
    "summary":    ["closing", "summary", "conclusion", "thank", "总结", "结束"],
    "standard":   ["title and content", "title + content", "content", "标准"],
    "two-column": ["two content", "comparison", "two column", "双栏"],
    "image":      ["picture with caption", "picture", "image", "图片"],
    "title-only": ["title only", "blank", "free", "仅标题"],
}


@dataclass
class LayoutInfo:
    index: int
    name: str
    placeholder_count: int
    placeholder_types: List[str] = field(default_factory=list)


@dataclass
class TemplateInfo:
    path: str
    slide_width_emu: int
    slide_height_emu: int
    layouts: List[LayoutInfo]
    major_font: Optional[str] = None
    minor_font: Optional[str] = None

    @property
    def slide_width(self) -> Emu:
        return Emu(self.slide_width_emu)

    @property
    def slide_height(self) -> Emu:
        return Emu(self.slide_height_emu)


def inspect_template(path: str) -> TemplateInfo:
    """Open ``path`` and collect layout & font info."""
    prs = Presentation(path)
    layouts: List[LayoutInfo] = []
    for idx, layout in enumerate(prs.slide_layouts):
        try:
            ph_types = []
            for ph in layout.placeholders:
                try:
                    ph_types.append(str(ph.placeholder_format.type).rsplit(".", 1)[-1])
                except Exception:
                    ph_types.append("UNKNOWN")
            layouts.append(LayoutInfo(
                index=idx,
                name=getattr(layout, "name", f"Layout {idx}"),
                placeholder_count=len(list(layout.placeholders)),
                placeholder_types=ph_types,
            ))
        except Exception as exc:
            log.warning("failed to read layout %s: %s", idx, exc)

    major, minor = _read_theme_fonts(prs)
    return TemplateInfo(
        path=path,
        slide_width_emu=prs.slide_width,
        slide_height_emu=prs.slide_height,
        layouts=layouts,
        major_font=major,
        minor_font=minor,
    )


def _read_theme_fonts(prs: Presentation):
    """Extract major (heading) and minor (body) font names from the theme XML."""
    try:
        master = prs.slide_masters[0]
        theme_elem = master.element.getroottree().getroot()
        # Walk masters' related theme parts
        for rel in master.part.rels.values():
            if "theme" in rel.reltype:
                theme_part = rel.target_part
                xml = theme_part.element
                ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
                major = xml.find(".//a:fontScheme/a:majorFont/a:latin", ns)
                minor = xml.find(".//a:fontScheme/a:minorFont/a:latin", ns)
                return (
                    major.get("typeface") if major is not None else None,
                    minor.get("typeface") if minor is not None else None,
                )
    except Exception as exc:
        log.debug("could not read theme fonts: %s", exc)
    return None, None


def resolve_layout(prs: Presentation, layout_spec: Optional[str]):
    """Resolve a layout spec to an actual SlideLayout from ``prs``.

    The spec may be:
      * None                     -> fall back to standard / first layout
      * an integer string "5"    -> by index
      * a known alias (cover...) -> first layout matching alias candidates
      * an exact (or partial) layout name match
    """
    layouts = list(prs.slide_layouts)
    if not layouts:
        raise ValueError("Template has no slide layouts")

    if layout_spec is None or not str(layout_spec).strip():
        return _fallback_layout(layouts)

    spec = str(layout_spec).strip()

    # numeric index
    if spec.isdigit():
        i = int(spec)
        if 0 <= i < len(layouts):
            return layouts[i]
        log.warning("layout index %s out of range, using fallback", i)
        return _fallback_layout(layouts)

    spec_l = spec.lower()

    # alias?
    if spec_l in LAYOUT_ALIASES:
        for cand in LAYOUT_ALIASES[spec_l]:
            for lyt in layouts:
                if cand.lower() in (lyt.name or "").lower():
                    return lyt

    # exact name
    for lyt in layouts:
        if (lyt.name or "").lower() == spec_l:
            return lyt
    # partial name
    for lyt in layouts:
        if spec_l in (lyt.name or "").lower():
            return lyt

    log.warning("layout %r not found; using fallback", spec)
    return _fallback_layout(layouts)


def _fallback_layout(layouts):
    # prefer 'Title and Content' style, else first non-title-slide, else 0
    for lyt in layouts:
        n = (lyt.name or "").lower()
        if "title and content" in n or "标准" in n or "content" in n:
            return lyt
    if len(layouts) > 1:
        return layouts[1]
    return layouts[0]
