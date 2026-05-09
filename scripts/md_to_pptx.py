#!/usr/bin/env python3
"""Convert a SlideForge-flavored markdown file to a .pptx.

Usage::

    python3 scripts/md_to_pptx.py input.md [-t template.pptx] [-o output.pptx]
                                 [--img-dir _diagrams]
"""
from __future__ import annotations

import argparse
import logging
import os
import sys

# Allow running this script directly without installing the package.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from slideforge.md_parser import parse_markdown_file
from slideforge.pptx_builder import build_pptx


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", help="Path to the input markdown file")
    p.add_argument("-t", "--template", help="Optional reference .pptx template")
    p.add_argument("-o", "--output", help="Output .pptx path")
    p.add_argument("--img-dir", default=None, help="Directory for rendered diagrams")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")

    deck = parse_markdown_file(args.input)
    output = args.output
    if not output:
        base = os.path.splitext(os.path.basename(args.input))[0]
        output = base + ".pptx"
    template = args.template or deck.front_matter.get("template")
    saved = build_pptx(deck, output, template_path=template, img_dir=args.img_dir)
    print(f"Wrote {len(deck.slides)} slides -> {saved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
