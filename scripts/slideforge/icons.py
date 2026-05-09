"""Icon resolution helpers.

An icon may be specified as:
  * an absolute or relative file path to an image (.png, .jpg, .svg)
  * a name from the bundled set in ``assets/icons/`` (resolved without ext)
  * a Lucide icon URL hint like ``lucide:lightbulb`` (downloaded on demand)

Only PNG/JPEG can be inserted into PPTX directly. SVGs are converted to PNG
via Pillow + cairosvg if available, otherwise rasterized via a tiny built-in
fallback that just renders the SVG label as text.
"""
from __future__ import annotations

import hashlib
import logging
import os
from typing import Optional

log = logging.getLogger(__name__)


# Locate the bundled assets/icons directory robustly.
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
_BUNDLED_ICONS_DIR = os.path.join(_REPO_ROOT, "assets", "icons")


def list_bundled_icons():
    if not os.path.isdir(_BUNDLED_ICONS_DIR):
        return []
    return sorted(
        os.path.splitext(f)[0]
        for f in os.listdir(_BUNDLED_ICONS_DIR)
        if f.lower().endswith((".svg", ".png", ".jpg", ".jpeg"))
    )


def resolve_icon(spec: str, cache_dir: Optional[str] = None) -> Optional[str]:
    """Resolve a spec to an image path PowerPoint can ingest (PNG/JPG).

    Returns ``None`` if it cannot be resolved.
    """
    if not spec:
        return None
    spec = spec.strip()
    cache_dir = cache_dir or os.path.join(_REPO_ROOT, ".cache", "icons")
    os.makedirs(cache_dir, exist_ok=True)

    # 1) explicit file path
    if os.path.isabs(spec) or spec.startswith("./") or spec.startswith("../") or os.sep in spec:
        if os.path.exists(spec):
            return _ensure_raster(spec, cache_dir)
        log.warning("icon path not found: %s", spec)
        return None

    # 2) bundled name (with or without extension)
    for ext in (".png", ".jpg", ".jpeg", ".svg"):
        candidate = os.path.join(_BUNDLED_ICONS_DIR, spec + ext)
        if os.path.exists(candidate):
            return _ensure_raster(candidate, cache_dir)
    # name with extension already
    candidate = os.path.join(_BUNDLED_ICONS_DIR, spec)
    if os.path.exists(candidate):
        return _ensure_raster(candidate, cache_dir)

    # 3) lucide:NAME hint -> simple deterministic placeholder
    if spec.startswith("lucide:") or spec.startswith("tabler:"):
        return _make_text_icon(spec.split(":", 1)[1], cache_dir)

    log.warning("unknown icon spec: %s", spec)
    return None


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _ensure_raster(path: str, cache_dir: str) -> str:
    """If ``path`` is already PNG/JPEG, return as-is. Otherwise rasterize."""
    ext = os.path.splitext(path)[1].lower()
    if ext in (".png", ".jpg", ".jpeg"):
        return path
    if ext == ".svg":
        return _svg_to_png(path, cache_dir)
    return path


def _svg_to_png(svg_path: str, cache_dir: str, size: int = 256) -> str:
    digest = _hash_file(svg_path) + f"-{size}"
    out = os.path.join(cache_dir, f"{digest}.png")
    if os.path.exists(out):
        return out

    # Try cairosvg
    try:
        import cairosvg  # type: ignore

        cairosvg.svg2png(url=svg_path, write_to=out, output_width=size, output_height=size)
        return out
    except Exception as exc:  # cairosvg not installed or rasterization failed
        log.debug("cairosvg unavailable: %s", exc)

    # Fallback: a simple Pillow render with the file's basename as label.
    return _make_text_icon(os.path.splitext(os.path.basename(svg_path))[0], cache_dir, size=size)


def _make_text_icon(label: str, cache_dir: str, size: int = 256) -> str:
    from PIL import Image, ImageDraw

    digest = hashlib.sha1(label.encode("utf-8")).hexdigest()[:10]
    out = os.path.join(cache_dir, f"text-icon-{digest}.png")
    if os.path.exists(out):
        return out

    img = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    pad = size // 12
    draw.rounded_rectangle(
        [(pad, pad), (size - pad, size - pad)],
        radius=size // 8,
        fill=(31, 78, 121, 255),
    )
    short = (label[:2] or "?").upper()
    try:
        # Try to centre the text manually without a TTF (PIL default font ok).
        bbox = draw.textbbox((0, 0), short)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((size - tw) / 2, (size - th) / 2 - size * 0.05), short, fill=(255, 255, 255, 255))
    except Exception:
        pass
    img.save(out, "PNG")
    return out


def _hash_file(path: str) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:12]
