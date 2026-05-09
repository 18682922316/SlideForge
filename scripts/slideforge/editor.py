"""Apply structured edit operations to an existing .pptx.

Edit specs are YAML/JSON documents of the form::

    operations:
      - op: replace_text
        slide: 2                  # 1-based slide index
        target: "shape_name | placeholder:idx | text_match:foo"
        text: "New text..."

      - op: add_icon
        slide: 3
        target: "placeholder:1"
        icon: "lucide:lightbulb"  # or path / bundled name
        position: left            # left | right | top
        size: 0.4                 # inches

      - op: align
        slide: 4
        targets: ["text_match:Architecture", "text_match:Pipeline"]
        align: left               # left|right|top|bottom|center_h|center_v
                                  # |distribute_h|distribute_v
        reference: first          # first|last|slide

      - op: set_font
        slide: 1
        target: "all"
        font: "Source Han Sans CN"

The rest of this module implements those operations against python-pptx.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import yaml
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Emu, Inches

from .icons import resolve_icon

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def apply_edits(pptx_path: str, spec: Dict[str, Any], output_path: str) -> Dict[str, Any]:
    """Apply ``spec`` to ``pptx_path`` and save to ``output_path``.

    Returns a small report dict with applied / skipped / failed counts.
    """
    prs = Presentation(pptx_path)
    operations = spec.get("operations") or []
    if not isinstance(operations, list):
        raise ValueError("'operations' must be a list")

    report = {"applied": 0, "skipped": 0, "failed": 0, "details": []}
    for i, op in enumerate(operations):
        name = op.get("op")
        try:
            handler = _OP_HANDLERS.get(name)
            if handler is None:
                report["skipped"] += 1
                report["details"].append({"index": i, "op": name, "status": "unknown_op"})
                continue
            handler(prs, op)
            report["applied"] += 1
            report["details"].append({"index": i, "op": name, "status": "ok"})
        except Exception as exc:
            log.exception("operation %s (#%d) failed", name, i)
            report["failed"] += 1
            report["details"].append({"index": i, "op": name, "status": "error",
                                       "error": str(exc)})

    os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
    prs.save(output_path)
    return report


def load_edit_spec(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    if path.lower().endswith((".yaml", ".yml")):
        return yaml.safe_load(text) or {}
    return json.loads(text)


# ---------------------------------------------------------------------------
# Target resolution
# ---------------------------------------------------------------------------


def _get_slide(prs: Presentation, idx_one_based: int):
    if idx_one_based is None:
        raise ValueError("operation missing 'slide'")
    i = int(idx_one_based) - 1
    slides = list(prs.slides)
    if not (0 <= i < len(slides)):
        raise IndexError(f"slide index {idx_one_based} out of range (have {len(slides)})")
    return slides[i]


def _resolve_targets(slide, target: Any) -> List[Any]:
    """Resolve a target spec (string or list) to a list of shapes.

    Selectors:
      * "all"                 -> every shape
      * "title"               -> slide title
      * "placeholder:<idx>"   -> placeholder by idx
      * "shape_name:<name>"   -> shape with matching name
      * "text_match:<text>"   -> any shape whose text contains <text>
      * "<int>"               -> shape by ordinal index (0-based)
    """
    if target is None:
        return []
    if isinstance(target, list):
        out: List[Any] = []
        for t in target:
            out.extend(_resolve_targets(slide, t))
        return out

    s = str(target).strip()
    shapes = list(slide.shapes)
    if s == "all":
        return shapes
    if s == "title":
        return [slide.shapes.title] if slide.shapes.title is not None else []
    if s.isdigit():
        i = int(s)
        return [shapes[i]] if 0 <= i < len(shapes) else []
    if ":" in s:
        kind, val = s.split(":", 1)
        kind, val = kind.strip(), val.strip()
        if kind == "placeholder":
            try:
                want = int(val)
            except ValueError:
                return []
            for ph in slide.placeholders:
                if ph.placeholder_format.idx == want:
                    return [ph]
            return []
        if kind == "shape_name":
            return [s for s in shapes if (s.name or "") == val]
        if kind == "text_match":
            out = []
            for shape in shapes:
                if shape.has_text_frame and val.lower() in shape.text_frame.text.lower():
                    out.append(shape)
            return out
    return []


# ---------------------------------------------------------------------------
# Op handlers
# ---------------------------------------------------------------------------


def _op_replace_text(prs, op):
    slide = _get_slide(prs, op.get("slide"))
    targets = _resolve_targets(slide, op.get("target"))
    if not targets:
        raise ValueError(f"replace_text: no targets matched {op.get('target')!r}")
    new_text = op.get("text", "")
    keep_format = op.get("keep_format", True)
    for shape in targets:
        if not shape.has_text_frame:
            continue
        _replace_text_in_frame(shape.text_frame, new_text, keep_format=keep_format)


def _replace_text_in_frame(tf, new_text: str, keep_format: bool = True):
    """Replace text content of ``tf`` with ``new_text``.

    If ``keep_format`` is True we try to retain the formatting of the first
    run by overwriting it and clearing the rest. Otherwise we wipe the frame.
    """
    paragraphs = list(tf.paragraphs)
    if not paragraphs or not keep_format:
        tf.clear()
        tf.paragraphs[0].add_run().text = new_text
        return
    p0 = paragraphs[0]
    runs = list(p0.runs)
    if runs:
        runs[0].text = new_text
        for r in runs[1:]:
            r.text = ""
    else:
        p0.add_run().text = new_text
    # remove subsequent paragraphs
    for p in paragraphs[1:]:
        p._p.getparent().remove(p._p)  # noqa: SLF001


def _op_add_icon(prs, op):
    slide = _get_slide(prs, op.get("slide"))
    targets = _resolve_targets(slide, op.get("target"))
    if not targets:
        raise ValueError(f"add_icon: no targets matched {op.get('target')!r}")
    icon_path = resolve_icon(op["icon"])
    if not icon_path:
        raise ValueError(f"could not resolve icon: {op['icon']}")
    size_in = float(op.get("size", 0.4))
    position = (op.get("position") or "left").lower()
    gap = Inches(0.1)
    for shape in targets:
        size_emu = Inches(size_in)
        if position == "left":
            x = shape.left - size_emu - gap
            y = shape.top + (shape.height - size_emu) // 2
        elif position == "right":
            x = shape.left + shape.width + gap
            y = shape.top + (shape.height - size_emu) // 2
        elif position == "top":
            x = shape.left + (shape.width - size_emu) // 2
            y = shape.top - size_emu - gap
        else:  # bottom
            x = shape.left + (shape.width - size_emu) // 2
            y = shape.top + shape.height + gap
        # clamp to slide bounds
        x = max(Emu(0), x)
        y = max(Emu(0), y)
        slide.shapes.add_picture(icon_path, x, y, width=size_emu, height=size_emu)


def _op_align(prs, op):
    slide = _get_slide(prs, op.get("slide"))
    targets = _resolve_targets(slide, op.get("targets") or op.get("target"))
    if len(targets) < 2 and op.get("reference") not in ("slide", "page"):
        raise ValueError("align: need ≥2 targets, or reference='slide'")
    direction = (op.get("align") or "left").lower()
    reference = (op.get("reference") or "first").lower()

    sw, sh = prs.slide_width, prs.slide_height

    if reference == "slide":
        for shape in targets:
            _align_to_slide(shape, direction, sw, sh)
        return

    # pick reference geometry
    if reference == "last":
        ref = targets[-1]
        rest = targets[:-1]
    else:
        ref = targets[0]
        rest = targets[1:]

    if direction == "distribute_h":
        _distribute(targets, axis="x")
        return
    if direction == "distribute_v":
        _distribute(targets, axis="y")
        return

    for shape in rest:
        if direction == "left":
            shape.left = ref.left
        elif direction == "right":
            shape.left = ref.left + ref.width - shape.width
        elif direction == "top":
            shape.top = ref.top
        elif direction == "bottom":
            shape.top = ref.top + ref.height - shape.height
        elif direction == "center_h":
            shape.left = ref.left + (ref.width - shape.width) // 2
        elif direction == "center_v":
            shape.top = ref.top + (ref.height - shape.height) // 2
        else:
            raise ValueError(f"unknown align direction: {direction}")


def _align_to_slide(shape, direction: str, sw, sh):
    if direction == "left":
        shape.left = Emu(0)
    elif direction == "right":
        shape.left = sw - shape.width
    elif direction == "top":
        shape.top = Emu(0)
    elif direction == "bottom":
        shape.top = sh - shape.height
    elif direction == "center_h":
        shape.left = (sw - shape.width) // 2
    elif direction == "center_v":
        shape.top = (sh - shape.height) // 2
    else:
        raise ValueError(f"unknown align direction: {direction}")


def _distribute(shapes: List[Any], axis: str):
    if len(shapes) < 3:
        return
    if axis == "x":
        sorted_shapes = sorted(shapes, key=lambda s: s.left)
        first, last = sorted_shapes[0], sorted_shapes[-1]
        total_w = last.left + last.width - first.left
        used_w = sum(s.width for s in sorted_shapes)
        gap = max(0, (total_w - used_w) // (len(sorted_shapes) - 1))
        cur = first.left + first.width + gap
        for s in sorted_shapes[1:-1]:
            s.left = cur
            cur += s.width + gap
    else:
        sorted_shapes = sorted(shapes, key=lambda s: s.top)
        first, last = sorted_shapes[0], sorted_shapes[-1]
        total_h = last.top + last.height - first.top
        used_h = sum(s.height for s in sorted_shapes)
        gap = max(0, (total_h - used_h) // (len(sorted_shapes) - 1))
        cur = first.top + first.height + gap
        for s in sorted_shapes[1:-1]:
            s.top = cur
            cur += s.height + gap


def _op_set_font(prs, op):
    slide = _get_slide(prs, op.get("slide"))
    targets = _resolve_targets(slide, op.get("target") or "all")
    font = op.get("font")
    size = op.get("size")
    color = op.get("color")
    rgb = None
    if color:
        s = str(color).lstrip("#")
        if len(s) == 6:
            rgb = RGBColor(int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
    for shape in targets:
        if not shape.has_text_frame:
            continue
        for p in shape.text_frame.paragraphs:
            for r in p.runs:
                if font:
                    r.font.name = font
                if size:
                    from pptx.util import Pt
                    r.font.size = Pt(int(size))
                if rgb is not None:
                    r.font.color.rgb = rgb


_OP_HANDLERS = {
    "replace_text": _op_replace_text,
    "add_icon": _op_add_icon,
    "align": _op_align,
    "set_font": _op_set_font,
}
