#!/usr/bin/env python3
"""Apply a YAML/JSON edit spec to a .pptx file.

Usage::

    python3 scripts/edit_ppt.py input.pptx --spec edits.yaml -o output.pptx

See ``skills/edit-ppt/SKILL.md`` for the full spec schema.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from slideforge.editor import apply_edits, load_edit_spec


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", help="Path to the .pptx to edit")
    p.add_argument("--spec", required=True, help="Path to the YAML/JSON edit spec")
    p.add_argument("-o", "--output", help="Output .pptx path (default: <input>.edited.pptx)")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")

    output = args.output
    if not output:
        base, ext = os.path.splitext(args.input)
        output = base + ".edited" + (ext or ".pptx")

    spec = load_edit_spec(args.spec)
    report = apply_edits(args.input, spec, output)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"Wrote -> {output}")
    return 0 if report.get("failed", 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
