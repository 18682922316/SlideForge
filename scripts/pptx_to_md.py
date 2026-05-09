#!/usr/bin/env python3
"""Convert a .pptx file to a SlideForge-flavored markdown document.

Usage::

    python3 scripts/pptx_to_md.py input.pptx [-o output.md] [--img-dir <dir>]
                                  [--no-notes]
"""
from __future__ import annotations

import argparse
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from slideforge.pptx_reader import pptx_to_markdown


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", help="Path to the input .pptx file")
    p.add_argument("-o", "--output", help="Output markdown path")
    p.add_argument("--img-dir", default=None, help="Directory for extracted images")
    p.add_argument("--no-notes", action="store_true", help="Skip speaker notes")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")

    out = args.output
    if not out:
        base = os.path.splitext(os.path.basename(args.input))[0]
        out = base + ".md"
    pptx_to_markdown(args.input, out_md_path=out, img_dir=args.img_dir,
                     include_notes=not args.no_notes)
    print(f"Wrote markdown -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
