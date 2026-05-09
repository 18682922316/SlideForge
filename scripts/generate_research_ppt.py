#!/usr/bin/env python3
"""Generate a research/technical .pptx from an outline (markdown or YAML).

The outline may be:
  * A SlideForge-flavored markdown file (preferred).
  * A YAML file describing slides; this is then converted to markdown
    in-memory before being built.

Usage::

    python3 scripts/generate_research_ppt.py outline.md \
        [-t reference_template.pptx] [-o out.pptx]

YAML outline schema (alternative input)::

    title: "Paper Title"
    subtitle: "Author / Affiliation"
    template: "tpl.pptx"
    theme:
      primary_color: "#1F4E79"
      font: "Source Han Sans CN"
    slides:
      - title: "Background"
        layout: standard
        bullets:
          - "Motivation 1"
          - "Motivation 2"
      - title: "Architecture"
        layout: two-column
        bullets:
          - "Encoder"
          - "Decoder"
        diagram:
          type: mermaid
          code: |
            flowchart LR
              A[Input] --> B[Encoder] --> C[Decoder] --> D[Output]
      - title: "Results"
        table:
          headers: ["Method", "Acc", "F1"]
          rows:
            - ["Baseline", "0.81", "0.79"]
            - ["Ours",     "0.88", "0.86"]
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import Any, Dict, List

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from slideforge.md_parser import parse_markdown
from slideforge.pptx_builder import build_pptx


def yaml_outline_to_markdown(spec: Dict[str, Any]) -> str:
    """Render a YAML outline into SlideForge markdown."""
    lines: List[str] = ["---"]
    fm_keys = ("title", "subtitle", "template", "output", "theme")
    fm = {k: spec[k] for k in fm_keys if k in spec}
    lines.append(yaml.safe_dump(fm, allow_unicode=True, sort_keys=False).strip())
    lines.append("---")
    lines.append("")

    for i, slide in enumerate(spec.get("slides", [])):
        if i > 0:
            lines.append("---")
            lines.append("")
        title = slide.get("title", f"Slide {i + 1}")
        lines.append(f"## {title}")
        if slide.get("layout"):
            lines.append(f"<!-- layout: {slide['layout']} -->")
        if slide.get("notes"):
            lines.append(f"<!-- notes: {slide['notes']} -->")
        lines.append("")

        if slide.get("paragraph"):
            lines.append(slide["paragraph"])
            lines.append("")

        for b in slide.get("bullets", []) or []:
            if isinstance(b, str):
                lines.append(f"- {b}")
            elif isinstance(b, dict):
                lines.append(f"- {b.get('text', '')}")
                for sub in b.get("children", []) or []:
                    lines.append(f"  - {sub}")
        if slide.get("bullets"):
            lines.append("")

        tbl = slide.get("table")
        if tbl and tbl.get("headers"):
            lines.append("| " + " | ".join(tbl["headers"]) + " |")
            lines.append("|" + "|".join(["---"] * len(tbl["headers"])) + "|")
            for row in tbl.get("rows", []):
                lines.append("| " + " | ".join(str(c) for c in row) + " |")
            lines.append("")

        for img in slide.get("images", []) or []:
            if isinstance(img, str):
                lines.append(f"![image]({img})")
            else:
                lines.append(f"![{img.get('alt', '')}]({img['path']})")
        if slide.get("images"):
            lines.append("")

        diag = slide.get("diagram")
        if diag and diag.get("code"):
            lang = diag.get("type", "mermaid")
            lines.append(f"```{lang}")
            lines.append(diag["code"].rstrip())
            lines.append("```")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input", help="Outline file (.md or .yaml)")
    p.add_argument("-t", "--template", help="Reference .pptx template (style inheritance)")
    p.add_argument("-o", "--output", help="Output .pptx path")
    p.add_argument("--img-dir", default=None, help="Directory for rendered diagrams")
    p.add_argument("--dump-md", help="Write the intermediate markdown to this path (debug)")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")

    ext = os.path.splitext(args.input)[1].lower()
    if ext in (".yaml", ".yml"):
        with open(args.input, "r", encoding="utf-8") as f:
            spec = yaml.safe_load(f) or {}
        md_text = yaml_outline_to_markdown(spec)
    else:
        with open(args.input, "r", encoding="utf-8") as f:
            md_text = f.read()

    if args.dump_md:
        with open(args.dump_md, "w", encoding="utf-8") as f:
            f.write(md_text)

    deck = parse_markdown(md_text)

    output = args.output
    if not output:
        base = os.path.splitext(os.path.basename(args.input))[0]
        output = base + ".pptx"

    template = args.template or deck.front_matter.get("template")
    saved = build_pptx(deck, output, template_path=template, img_dir=args.img_dir)
    print(f"Wrote {len(deck.slides)} slides -> {saved}")
    if template:
        print(f"  Style inherited from: {template}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
