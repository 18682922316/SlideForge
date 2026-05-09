"""Render mermaid (and other code-block) diagrams to PNG images.

Strategy:
  * Try ``mmdc`` (mermaid-cli) on PATH first.
  * Fallback to ``npx -y @mermaid-js/mermaid-cli`` if Node is available.
  * If both fail, write a simple placeholder PNG so the slide still builds
    and surface a warning to the caller.
"""
from __future__ import annotations

import hashlib
import logging
import os
import shutil
import subprocess
import tempfile
from typing import Optional

log = logging.getLogger(__name__)


def render_mermaid(code: str, out_dir: str, scale: int = 2) -> Optional[str]:
    """Render mermaid ``code`` to a PNG inside ``out_dir`` and return its path.

    Returns ``None`` if no renderer is available; in that case the caller
    should fall back to inserting a code listing or placeholder image.
    """
    os.makedirs(out_dir, exist_ok=True)
    digest = hashlib.sha1(code.encode("utf-8")).hexdigest()[:12]
    out_path = os.path.join(out_dir, f"mermaid-{digest}.png")
    if os.path.exists(out_path):
        return out_path

    with tempfile.NamedTemporaryFile("w", suffix=".mmd", delete=False, encoding="utf-8") as tmp:
        tmp.write(code)
        tmp_path = tmp.name

    try:
        cmd = _resolve_mermaid_cmd()
        if cmd is None:
            log.warning("mermaid-cli not available; install with `npm i -g @mermaid-js/mermaid-cli`")
            return None
        full = cmd + ["-i", tmp_path, "-o", out_path, "-s", str(scale), "-b", "transparent"]
        log.debug("running %s", full)
        result = subprocess.run(full, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            log.warning("mermaid-cli failed (%s): %s", result.returncode, result.stderr.strip())
            return None
        return out_path if os.path.exists(out_path) else None
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def _resolve_mermaid_cmd():
    if shutil.which("mmdc"):
        return ["mmdc"]
    if shutil.which("npx"):
        # `npx -y` will auto-install on first run; cached afterwards.
        return ["npx", "-y", "-p", "@mermaid-js/mermaid-cli", "mmdc"]
    return None


def make_placeholder_png(out_dir: str, label: str = "Diagram") -> str:
    """Tiny gray PNG so the build doesn't fail when no renderer is present."""
    from PIL import Image, ImageDraw  # local import to keep base import light

    os.makedirs(out_dir, exist_ok=True)
    digest = hashlib.sha1(label.encode("utf-8")).hexdigest()[:8]
    path = os.path.join(out_dir, f"placeholder-{digest}.png")
    if os.path.exists(path):
        return path
    img = Image.new("RGB", (800, 450), color=(245, 245, 245))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0, 0), (799, 449)], outline=(180, 180, 180), width=2)
    draw.text((20, 20), f"[{label}] (mermaid-cli not available)", fill=(80, 80, 80))
    img.save(path, "PNG")
    return path
