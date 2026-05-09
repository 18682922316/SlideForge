---
name: edit-ppt
description: Apply structured edits to an existing PPTX — replace/polish text in academic style, add icons next to text frames, align/distribute shapes, and unify fonts. The skill consumes a YAML/JSON edit spec, so the LLM can plan the edits and then apply them in a single deterministic pass. Use when the user asks to "modify this PPT", "add icons", "align these boxes", "polish this slide's wording", "PPT 加图标", "把这两个文本框对齐", etc.
license: Apache-2.0
compatibility: Requires Python 3.9+, python-pptx>=0.6.21, PyYAML, Pillow.
metadata:
  author: SlideForge
  version: "0.1"
---

# Edit PPT

Apply a structured set of operations to an existing `.pptx`. The script never
guesses meaning — the LLM is responsible for composing the edit spec; the
script just does the deterministic mechanical work.

## When to use

- "帮我把第 2 页文本框前面加个灯泡 icon"
- "把这三个组件按左对齐，并按水平方向均匀分布"
- "用学术风把这一页的内容润色一下"
- "把所有页的字体统一为 Source Han Sans CN"
- "Replace the title of slide 1 with ..."

## High-level flow for the agent

The LLM should:

1. **Inspect the deck** if needed by first running the
   [`pptx-to-markdown`](../pptx-to-markdown/SKILL.md) skill to read the
   current content. This reveals slide indices, titles, and approximate text.
2. **Plan the edits** in natural language, then convert to a YAML edit spec.
3. **Run** `edit_ppt.py` with the spec.
4. **Inspect the result** by running `pptx-to-markdown` again, or simply
   trust the report (`applied / skipped / failed`).

For polish-style edits the LLM does the rewriting itself (in chat) and emits
`replace_text` operations carrying the polished strings.

## Running

```bash
python3 <skill_root>/../../scripts/edit_ppt.py <input.pptx> \
    --spec <edits.yaml> -o <output.pptx>
```

The script prints a JSON report indicating which operations succeeded.

## Edit-spec schema

```yaml
operations:           # list of operations applied in order
  - op: <name>        # one of: replace_text, add_icon, align, set_font
    slide: <n>        # 1-based slide index
    ...               # op-specific keys
```

### Operation: `replace_text`

Replace the text content of a target shape, preserving font formatting by
default.

```yaml
- op: replace_text
  slide: 2
  target: "title"             # selector (see below)
  text: "新的标题文本"
  keep_format: true           # default true; preserves first run's formatting
```

**Use case — academic polish.** The LLM reads existing text via
`pptx-to-markdown`, polishes it in chat, then emits one `replace_text` per
text frame:

```yaml
- op: replace_text
  slide: 3
  target: "text_match:我们的方法"
  text: "我们提出了一种基于动态路由的稀疏注意力机制（DRSA），通过轻量级路由器为每个查询动态选择 Top-k 关键键值对，在显著降低计算复杂度的同时维持精度。"
```

### Operation: `add_icon`

Insert an icon image next to a text frame.

```yaml
- op: add_icon
  slide: 2
  target: "title"             # the text frame to attach the icon to
  icon: "lightbulb"           # bundled name | path/to/icon.png | lucide:NAME
  position: left              # left | right | top | bottom (default: left)
  size: 0.45                  # inches (default: 0.4)
```

`icon` resolution order:

1. Absolute or relative file path (`.png` / `.jpg` / `.svg` — SVG is
   rasterized via `cairosvg` if installed, else via a simple text fallback).
2. Bundled name from `assets/icons/` (currently includes: `lightbulb`,
   `gear`, `check`, `arrow-right`, `chart`, `code`, `database`, `cpu`).
3. `lucide:NAME` / `tabler:NAME` hint — produces a colored badge with the
   first two letters of NAME (best-effort placeholder).

### Operation: `align`

Align or distribute a set of shapes.

```yaml
- op: align
  slide: 4
  targets:                    # ≥2 selectors, or a single selector matching ≥2
    - "text_match:Encoder"
    - "text_match:Decoder"
  align: left                 # left | right | top | bottom
                              # | center_h | center_v
                              # | distribute_h | distribute_v
  reference: first            # first (default) | last | slide
```

Alignment semantics:

- `reference: first` — all other targets are aligned to the first target's edge.
- `reference: last`  — all aligned to the last target's edge.
- `reference: slide` — each target aligned relative to the slide bounds (e.g. `align: center_h, reference: slide` centres horizontally on the slide).
- `distribute_h` / `distribute_v` — evenly space the in-between targets between the outermost two; needs ≥3 targets.

### Operation: `set_font`

Update font name / size / color across one or more shapes.

```yaml
- op: set_font
  slide: 1
  target: "all"               # selector
  font: "Source Han Sans CN"
  size: 18                    # points (optional)
  color: "#1F4E79"            # optional hex
```

## Target selectors

Selectors are strings (or lists of strings) that resolve to one or more
shapes on a slide:

| Selector | Meaning |
|----------|---------|
| `all` | Every shape on the slide |
| `title` | The slide title placeholder |
| `placeholder:<idx>` | Placeholder by `idx` (e.g. `placeholder:1`) |
| `shape_name:<name>` | Shape with exact name (visible in PowerPoint > Selection Pane) |
| `text_match:<substr>` | Any shape whose text contains `<substr>` (case-insensitive) |
| `<int>` | Shape by 0-based ordinal in `slide.shapes` |

`text_match` is the most useful selector for LLM-generated specs: it lets you
target a shape by a snippet of its current text (which the LLM has just read
from `pptx-to-markdown`).

## Recipes

### Add icons before each bullet-point title

```yaml
operations:
  - op: add_icon
    slide: 2
    target: "text_match:Motivation"
    icon: "lightbulb"
  - op: add_icon
    slide: 2
    target: "text_match:Architecture"
    icon: "gear"
  - op: add_icon
    slide: 2
    target: "text_match:Results"
    icon: "chart"
```

### Center the title on every slide horizontally

Iterate per slide (one op each):

```yaml
operations:
  - {op: align, slide: 1, target: "title", align: center_h, reference: slide}
  - {op: align, slide: 2, target: "title", align: center_h, reference: slide}
```

### Polish a slide's text in academic style

1. Run `pptx-to-markdown` on the input to extract current text.
2. Rewrite each paragraph in chat (e.g. tighter, more formal, third-person).
3. Emit one `replace_text` op per text frame.

### Distribute three architecture boxes evenly

```yaml
- op: align
  slide: 5
  targets:
    - "shape_name:BoxA"
    - "shape_name:BoxB"
    - "shape_name:BoxC"
  align: distribute_h
```

## Notes & limitations

- Operations on shapes that don't have a text frame (e.g. pictures) are
  silently ignored for `replace_text` / `set_font`.
- `add_icon` may place the icon outside slide bounds if the target sits at
  the very edge; the script clamps to (0,0) but does not re-flow.
- The script does **not** undo previous edits — make a copy of the input
  before destructive runs, or use `-o output.pptx` (default already writes
  to a `.edited.pptx` next to the input).
