---
name: markdown-to-pptx
description: Convert a SlideForge-flavored Markdown document to an editable PPTX. Supports text, bullets, tables, images, Mermaid diagrams (flowchart/sequence/architecture), speaker notes, and template-based style inheritance. Use when the user wants to "convert markdown to PPT", "build slides from this md", "md 转 PPT", etc. Lighter-weight sibling of `generate-research-ppt` for users who already have markdown ready.
license: Apache-2.0
compatibility: Requires Python 3.9+, python-pptx>=0.6.21, PyYAML, lxml, Pillow. Optional Node.js + mermaid-cli.
metadata:
  author: SlideForge
  version: "0.1"
---

# Markdown → PPTX

Take a SlideForge-flavored markdown file and emit an editable `.pptx`.

This is the same engine used by [`generate-research-ppt`](../generate-research-ppt/SKILL.md) but exposed as a thinner wrapper for the common "I already have the markdown, just build the PPT" case.

## When to use

- "build my slides.md into a pptx"
- "把这个 .md 转成 PPT"
- The user has already iterated on the markdown outline (perhaps after a
  `pptx-to-markdown` round trip) and just wants the binary output.

## Running

```bash
python3 <skill_root>/../../scripts/md_to_pptx.py <input.md> \
    [-t <template.pptx>] [-o <output.pptx>] [--img-dir <dir>]
```

If the markdown front-matter contains a `template:` field, that template is
used unless overridden by `-t`.

## Markdown dialect

See [`generate-research-ppt`'s SKILL.md](../generate-research-ppt/SKILL.md#markdown-dialect)
for the full reference. Quick summary:

```markdown
---
title: "Deck Title"
subtitle: "Author · 2026"
template: "tpl.pptx"        # optional
theme:
  primary_color: "#1F4E79"
  font: "Source Han Sans CN"
---

## Slide 1
<!-- layout: standard -->

- bullet
- bullet
  - nested

---

## Architecture
<!-- layout: image -->

\`\`\`mermaid
flowchart LR
  A --> B --> C
\`\`\`

---

## Results

| Method | Acc | F1 |
|--------|-----|----|
| Ours   | .88 | .86 |
```

Slide separator: a line containing only `---`.

## Recipes

### Round-trip: PPT → MD → PPT (with style preserved)

```bash
# Extract markdown from an existing deck (also extracts images).
python3 scripts/pptx_to_md.py input.pptx -o slides.md

# Re-build using the original deck as the style template.
python3 scripts/md_to_pptx.py slides.md -t input.pptx -o rebuilt.pptx
```

### Build with a corporate / lab template

```bash
python3 scripts/md_to_pptx.py slides.md -t templates/lab.pptx -o talk.pptx
```

The build keeps the template's masters / layouts / fonts / theme verbatim;
only the slide content is replaced.

## Notes

- Each `## Heading` after a `---` separator becomes a new slide. Content
  before the first `##` of a slide block is treated as body content.
- For mermaid blocks, the build script auto-runs `mermaid-cli` (via `npx`)
  to render them to PNG. First run may take 30–60 s while `npx` fetches
  `@mermaid-js/mermaid-cli`. Subsequent runs are cached.
- For best results with reference templates, ensure the template's layouts
  include common ones (Title Slide, Title and Content, Two Content,
  Picture with Caption). The build falls back gracefully if a layout is
  missing.
