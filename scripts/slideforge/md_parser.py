"""Parse the SlideForge markdown dialect into a list of Slide IR objects.

The dialect is a small superset of CommonMark, focused on slides:

```
---
title: "..."
subtitle: "..."
template: "path/to/template.pptx"   # optional
theme:
  primary_color: "#1F4E79"
  font: "Source Han Sans CN"
output: "out.pptx"                  # optional
---

## Slide title
<!-- layout: cover -->

Optional intro paragraph.

- bullet 1
- bullet 2
  - nested

| col1 | col2 |
|------|------|
| a    | b    |

![alt](path/to/image.png)

\\`\\`\\`mermaid
flowchart LR
  A --> B
\\`\\`\\`

---

## Next slide
...
```

Slide separator: a line that contains only `---`.
Slide title: the first `##` heading inside a slide block. Anything before
the first `##` in a slide is treated as body content (e.g. for cover/intro
slides, the title comes from the front-matter `title`).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import yaml


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class TableBlock:
    headers: List[str]
    rows: List[List[str]]


@dataclass
class ImageBlock:
    path: str
    alt: str = ""


@dataclass
class DiagramBlock:
    """Mermaid / plantuml / generic code-block diagram."""

    language: str  # "mermaid", "plantuml", ...
    code: str
    caption: str = ""


@dataclass
class BulletItem:
    text: str
    level: int = 0  # 0-based indent level
    children: List["BulletItem"] = field(default_factory=list)


@dataclass
class BulletList:
    items: List[BulletItem]


@dataclass
class Paragraph:
    text: str


@dataclass
class Slide:
    title: str = ""
    layout: Optional[str] = None  # alias, name, or numeric index as str
    notes: str = ""
    blocks: List[Any] = field(default_factory=list)  # any of the *Block / Paragraph / BulletList

    # raw metadata (e.g. slide-level <!-- key: value --> comments)
    meta: Dict[str, str] = field(default_factory=dict)

    def has_diagram(self) -> bool:
        return any(isinstance(b, DiagramBlock) for b in self.blocks)

    def has_table(self) -> bool:
        return any(isinstance(b, TableBlock) for b in self.blocks)

    def has_image(self) -> bool:
        return any(isinstance(b, ImageBlock) for b in self.blocks)

    def has_bullets(self) -> bool:
        return any(isinstance(b, BulletList) for b in self.blocks)


@dataclass
class Deck:
    front_matter: Dict[str, Any]
    slides: List[Slide]


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

_FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_META_COMMENT_RE = re.compile(r"<!--\s*([a-zA-Z0-9_\-]+)\s*:\s*(.+?)\s*-->")


def parse_markdown(text: str) -> Deck:
    """Parse a SlideForge-flavored markdown string into a Deck."""
    fm, body = _split_front_matter(text)
    slide_chunks = _split_slides(body)
    slides = [_parse_slide(chunk) for chunk in slide_chunks if chunk.strip()]
    return Deck(front_matter=fm, slides=slides)


def parse_markdown_file(path: str) -> Deck:
    with open(path, "r", encoding="utf-8") as f:
        return parse_markdown(f.read())


# ----- helpers --------------------------------------------------------------


def _split_front_matter(text: str) -> Tuple[Dict[str, Any], str]:
    m = _FRONT_MATTER_RE.match(text)
    if not m:
        return {}, text
    fm_raw = m.group(1)
    body = text[m.end():]
    try:
        fm = yaml.safe_load(fm_raw) or {}
    except yaml.YAMLError:
        fm = {}
    if not isinstance(fm, dict):
        fm = {}
    return fm, body


def _split_slides(body: str) -> List[str]:
    """Split body on lines that consist solely of `---` (slide separator)."""
    chunks: List[str] = []
    current: List[str] = []
    in_fence = False
    fence_marker = ""
    for line in body.splitlines():
        stripped = line.strip()
        # track fenced code blocks so `---` inside code doesn't split slides
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = stripped[:3]
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif stripped.startswith(fence_marker):
                in_fence = False
                fence_marker = ""
            current.append(line)
            continue
        if not in_fence and stripped == "---":
            chunks.append("\n".join(current))
            current = []
            continue
        current.append(line)
    if current:
        chunks.append("\n".join(current))
    return chunks


def _parse_slide(chunk: str) -> Slide:
    slide = Slide()
    lines = chunk.splitlines()

    # Pull <!-- key: value --> comments (slide-level meta) anywhere in chunk
    cleaned: List[str] = []
    for line in lines:
        m_iter = list(_META_COMMENT_RE.finditer(line))
        if m_iter:
            for m in m_iter:
                key, value = m.group(1).strip(), m.group(2).strip()
                if key == "layout":
                    slide.layout = value
                elif key == "notes":
                    slide.notes = value
                else:
                    slide.meta[key] = value
            line_wo = _META_COMMENT_RE.sub("", line).rstrip()
            if line_wo.strip():
                cleaned.append(line_wo)
        else:
            cleaned.append(line)

    # Title = first '## ...' heading (also accept '# ...')
    title_idx = -1
    for i, line in enumerate(cleaned):
        if line.startswith("## "):
            slide.title = line[3:].strip()
            title_idx = i
            break
        if line.startswith("# "):
            slide.title = line[2:].strip()
            title_idx = i
            break

    body_lines = cleaned[title_idx + 1:] if title_idx >= 0 else cleaned

    slide.blocks = _parse_blocks(body_lines)
    return slide


def _parse_blocks(lines: List[str]) -> List[Any]:
    blocks: List[Any] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()

        # blank line: skip
        if not stripped:
            i += 1
            continue

        # fenced code block -> diagram
        if stripped.startswith("```") or stripped.startswith("~~~"):
            fence = stripped[:3]
            lang = stripped[3:].strip()
            code_lines: List[str] = []
            i += 1
            while i < n and not lines[i].strip().startswith(fence):
                code_lines.append(lines[i])
                i += 1
            i += 1  # consume closing fence
            blocks.append(DiagramBlock(language=lang or "text", code="\n".join(code_lines)))
            continue

        # markdown table (header followed by separator '|---|')
        if stripped.startswith("|") and i + 1 < n and re.match(r"^\s*\|?\s*[:\-\|\s]+\|?\s*$", lines[i + 1]):
            table, consumed = _parse_table(lines[i:])
            blocks.append(table)
            i += consumed
            continue

        # image-only line
        m_img = re.match(r"^\s*!\[(.*?)\]\((.+?)\)\s*$", line)
        if m_img:
            blocks.append(ImageBlock(path=m_img.group(2).strip(), alt=m_img.group(1).strip()))
            i += 1
            continue

        # bullet list (unordered or ordered)
        if re.match(r"^(\s*)([\-\*\+]|\d+\.)\s+", line):
            bl, consumed = _parse_bullet_list(lines[i:])
            blocks.append(bl)
            i += consumed
            continue

        # paragraph: collect consecutive non-empty, non-special lines
        para_lines = [line]
        j = i + 1
        while j < n:
            nxt = lines[j]
            ns = nxt.strip()
            if not ns:
                break
            if ns.startswith("```") or ns.startswith("~~~"):
                break
            if ns.startswith("|"):
                break
            if re.match(r"^\s*([\-\*\+]|\d+\.)\s+", nxt):
                break
            if re.match(r"^\s*!\[", nxt):
                break
            para_lines.append(nxt)
            j += 1
        blocks.append(Paragraph(text=" ".join(p.strip() for p in para_lines)))
        i = j
    return blocks


def _parse_table(lines: List[str]) -> Tuple[TableBlock, int]:
    def split_row(s: str) -> List[str]:
        s = s.strip()
        if s.startswith("|"):
            s = s[1:]
        if s.endswith("|"):
            s = s[:-1]
        return [c.strip() for c in s.split("|")]

    headers = split_row(lines[0])
    rows: List[List[str]] = []
    i = 2  # skip header + separator
    while i < len(lines):
        s = lines[i].strip()
        if not s.startswith("|"):
            break
        rows.append(split_row(lines[i]))
        i += 1
    return TableBlock(headers=headers, rows=rows), i


def _parse_bullet_list(lines: List[str]) -> Tuple[BulletList, int]:
    items: List[BulletItem] = []
    stack: List[Tuple[int, BulletItem]] = []  # (indent, item)
    i = 0
    pattern = re.compile(r"^(\s*)([\-\*\+]|\d+\.)\s+(.*)$")
    while i < len(lines):
        m = pattern.match(lines[i])
        if not m:
            break
        indent_spaces = len(m.group(1))
        text = m.group(3).strip()
        # Use 2 spaces per indent level by convention.
        level = indent_spaces // 2
        item = BulletItem(text=text, level=level)
        # Find appropriate parent
        while stack and stack[-1][0] >= level:
            stack.pop()
        if stack:
            stack[-1][1].children.append(item)
        else:
            items.append(item)
        stack.append((level, item))
        i += 1
    return BulletList(items=items), i
