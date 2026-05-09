---
name: pptx-to-markdown
description: Convert a PPTX file to a SlideForge-flavored Markdown document. Slide titles become `## headings`, layouts are preserved as `<!-- layout: ... -->` comments, bullet lists / tables / images / speaker notes are extracted faithfully, and embedded pictures are exported to a sibling image directory. Use when the user wants to "convert PPT to markdown", "extract text from a PPT", "PPT 转 md", or to inspect a deck before editing.
license: Apache-2.0
compatibility: Requires Python 3.9+, python-pptx>=0.6.21, lxml.
metadata:
  author: SlideForge
  version: "0.1"
---

# PPTX → Markdown

Extract slide content from a `.pptx` and emit a Markdown document that
round-trips back to PPTX via the [`markdown-to-pptx`](../markdown-to-pptx/SKILL.md)
or [`generate-research-ppt`](../generate-research-ppt/SKILL.md) skills.

## When to use

- "把这份 PPT 转成 markdown 文档"
- "Extract the outline from this slide deck"
- "Read slide 3's text so I can edit it"
- Or as a *prerequisite step* before invoking `edit-ppt` so the LLM can see
  the current slide text and identify good `text_match:` selectors.

## Running

```bash
python3 <skill_root>/../../scripts/pptx_to_md.py <input.pptx> \
    [-o <output.md>] [--img-dir <dir>] [--no-notes]
```

Defaults:

- `-o` → `<basename>.md` next to the input.
- `--img-dir` → `<basename>-img/` next to the markdown.
- speaker notes are included as `<!-- notes: ... -->` comments unless
  `--no-notes` is passed.

## Output format

```markdown
---
title: "<first slide title or filename>"
source: "<input.pptx>"
---

## Slide 1 Title
<!-- layout: Title Slide -->

Body paragraph or bullet list.

---

## Slide 2 Title
<!-- layout: Title and Content -->

- bullet 1
- bullet 2
  - sub-bullet

| col1 | col2 |
|------|------|
| a    | b    |

![Picture 4](deck-img/slide2-5.png)

<!-- notes: speaker notes from this slide -->
```

## What is preserved

| PPTX element | Markdown |
|--------------|----------|
| Slide title placeholder | `## Heading` |
| Slide layout name | `<!-- layout: ... -->` comment |
| Text frames (multi-paragraph) | bullet list (`- ...`) |
| Bullet indent levels | 2-space indent per level |
| Tables | standard markdown tables |
| Pictures | extracted to `--img-dir` and referenced via `![alt](path)` |
| Speaker notes | `<!-- notes: ... -->` comment |

## What is NOT preserved (yet)

- Inline run formatting (bold / italic / color) — text is flattened to plain.
- Charts (native Excel chart objects) — they become `[chart]` placeholders or are skipped.
- Mermaid diagrams that were *originally* rendered to PNG remain as PNG image references; the original `.mmd` source isn't recoverable without an out-of-band sidecar.
- Animations, transitions, slide masters.

## Tips

- Re-import the produced markdown via `generate-research-ppt` with the same
  source `.pptx` as `--template` to round-trip while keeping the original
  template's style.
- For automated pipelines, prefer `--no-notes` if speaker notes contain
  sensitive information you don't want in the markdown.
