---
name: generate-research-ppt
description: Generate an editable scientific/technical PPTX from an outline (markdown or YAML). Supports text, bullet lists, tables, images, icons, and Mermaid-rendered diagrams (flowchart, sequence, architecture). When a reference template PPTX is provided, the generated deck inherits its layouts, fonts, theme colors, and overall style. Use this when the user wants to "generate slides", "make a research PPT", "write a paper deck", "生成科研 PPT", "做一个技术汇报", etc.
license: Apache-2.0
compatibility: Requires Python 3.9+, python-pptx>=0.6.21, PyYAML, lxml, Pillow. Optional Node.js + mermaid-cli (auto-installed via `npx -y @mermaid-js/mermaid-cli`) for diagram rendering.
metadata:
  author: SlideForge
  version: "0.1"
---

# Generate Research / Technical PPT

Build an **editable** `.pptx` from an outline. The script parses a SlideForge-flavored markdown (or YAML) file, optionally inherits style from a reference template `.pptx`, and emits a presentation that opens cleanly in PowerPoint, Keynote, and WPS.

## When to use

Trigger this skill when the user wants to create a presentation from scratch or from notes, especially in a research / engineering context:

- "帮我把这份大纲做成 PPT" / "生成一份技术汇报 PPT"
- "I have an outline, build a research deck"
- "Make a paper presentation with architecture and result tables"
- "Use this template's style and generate slides for ..."

## Inputs

| Input | Required | Description |
|------|----------|-------------|
| outline file | yes | A `.md` or `.yaml` file. If the user gives free-form text, first ask them to confirm or write it to a temp file in the SlideForge markdown dialect (see below). |
| reference template `.pptx` | no | Used as the base presentation. Layouts / theme / fonts are inherited verbatim. |
| output path | no | Defaults to `<input_basename>.pptx`. |

## Steps for the agent

1. **Gather / draft the outline.** If the user has not provided an outline:
   - Ask for the topic, audience, time budget, and key sections, OR
   - Draft an outline yourself in the SlideForge markdown dialect (see *Markdown dialect* below) and confirm before building.
2. **Pick a template.** If the user provides a reference `.pptx`, use it as `--template`. Otherwise the built-in default theme is used. You can call `inspect_template` (helper below) to list available layouts.
3. **Run the generator:**
   ```bash
   python3 <skill_root>/../../scripts/generate_research_ppt.py <outline> \
       [-t <template.pptx>] [-o <output.pptx>] [--img-dir <dir>]
   ```
   Replace `<skill_root>` with the absolute path to this skill's directory.
4. **Report**: number of slides generated, output path, and whether mermaid-cli was used. If diagrams fell back to placeholders, suggest installing mermaid-cli.

### Optional: inspect template layouts first

If the user provides a custom template, you can list its layouts to choose appropriate aliases:

```python
from slideforge.template_style import inspect_template
info = inspect_template("ref.pptx")
for lyt in info.layouts:
    print(lyt.index, lyt.name, lyt.placeholder_types)
```

## Markdown dialect

Front matter (YAML):

```markdown
---
title: "Paper / Talk Title"
subtitle: "Author · Affiliation · 2026"
template: "templates/lab_template.pptx"   # optional
theme:
  primary_color: "#1F4E79"
  font: "Source Han Sans CN"
---
```

Slides are separated by lines containing only `---`. Each slide has a `## Title` heading and any of the supported blocks below.

### Slide-level layout hint

Use an HTML comment to override auto layout selection:

```markdown
## Method
<!-- layout: two-column -->
```

Recognized aliases (resolved against the template's layouts):

| Alias | Use case |
|-------|----------|
| `cover` / `title-slide` / `封面` | Opening slide |
| `toc` / `agenda` / `目录` | Table of contents |
| `section` / `chapter` / `章节` | Section divider |
| `summary` / `conclusion` / `总结` | Closing slide |
| `standard` / `title-content` / `标准` | Title + body (default) |
| `two-column` / `双栏` | Side-by-side comparison or text + diagram |
| `image` / `picture` / `图片` | Visual-heavy slide |
| `title-only` / `blank` / `仅标题` | Free-form layout |

### Supported blocks

| Block | Markdown |
|-------|----------|
| Bullet list | `- item` (indent with 2 spaces per nested level) |
| Paragraph | plain text lines |
| Table | standard markdown table |
| Image | `![alt](path/to/image.png)` |
| Diagram | fenced `mermaid` code block — flowchart / sequenceDiagram / architecture-beta / classDiagram all supported |
| Speaker notes | `<!-- notes: ... -->` |

### Diagrams

Embed Mermaid directly. The build script renders each block to a PNG via `mermaid-cli` (auto-installed on first use through `npx -y @mermaid-js/mermaid-cli`).

```markdown
## System Architecture
<!-- layout: image -->

\`\`\`mermaid
flowchart LR
  Q[Query] --> R[Router]
  K[Key/Value] --> R
  R -->|Top-k| A[Sparse Attention]
  A --> O[Output]
\`\`\`
```

Supported diagram types via Mermaid:

- `flowchart` / `graph` — flow & data-flow diagrams
- `sequenceDiagram` — sequence / interaction diagrams
- `architecture-beta` — technical architecture diagrams
- `classDiagram` / `stateDiagram-v2` / `erDiagram`

If `mermaid-cli` is not available, a labeled placeholder PNG is inserted and a warning is printed; suggest installing Node.js or running the script with network access so `npx` can fetch it.

### Icons

Icons are inserted via the [`edit-ppt`](../edit-ppt/SKILL.md) skill *after* generation. To pre-place icons during generation, include them as `![alt](path)` images.

## YAML alternative (structured outline)

For users who prefer structured input, the script also accepts YAML:

```yaml
title: "Paper Title"
template: "ref.pptx"
slides:
  - title: "Background"
    layout: standard
    bullets: ["Motivation 1", "Motivation 2"]
  - title: "Architecture"
    layout: two-column
    bullets: ["Encoder", "Decoder"]
    diagram:
      type: mermaid
      code: |
        flowchart LR
          A --> B --> C
  - title: "Results"
    table:
      headers: ["Method", "Acc", "F1"]
      rows:
        - ["Baseline", "0.81", "0.79"]
        - ["Ours",     "0.88", "0.86"]
```

## Examples

See [`examples/outline-demo.md`](../../examples/outline-demo.md) and
[`examples/outline-demo.yaml`](../../examples/outline-demo.yaml) in the
SlideForge repository for end-to-end demos.

## Tips

- **Inherit, don't fight the template.** If a user supplies a corporate / lab
  template, prefer using its layout aliases via `<!-- layout: ... -->` rather
  than overriding fonts and colors via `theme:`.
- **Long bullets** auto-wrap; keep each bullet ≤ ~22 Chinese chars / ~14 English
  words for readability.
- **Tables**: bold headers and numerical columns automatically; for headers
  with arrows (↑ / ↓) use the actual unicode arrows for clarity.
- **Mathematical notation**: use plain text (e.g. `O(n^2)`) or LaTeX-style
  `\(...\)`. Real LaTeX rendering is not yet supported.
