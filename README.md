# SlideForge

> 面向科研与技术汇报的 PPT 生成 / 编辑 / 互转 Skills。
> Agent Skills for forging research & technical slide decks.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](./LICENSE)
[![Skills](https://img.shields.io/badge/skills-4-brightgreen)](./skills)
[![python-pptx](https://img.shields.io/badge/python--pptx-%E2%89%A50.6.21-blue)](https://python-pptx.readthedocs.io)

[English](#english) · [简体中文](#简体中文)

---

## 简体中文

SlideForge 是一组 [Agent Skills](https://docs.anthropic.com/en/docs/agents-and-tools/agent-skills/overview) 风格的 PPT 工具集，专为科研与技术场景设计。每个 skill 由一个 `SKILL.md`（声明能力 + 调用说明）和一组 Python 脚本组成，可被 Claude / 其它 LLM Agent 直接调用，也可在命令行独立使用。

### 包含的 Skills

| Skill | 能力 | 入口脚本 |
|------|------|----------|
| [`generate-research-ppt`](./skills/generate-research-ppt/SKILL.md) | 给定大纲（Markdown / YAML），生成可编辑科研 PPT；支持文本、流程图、时序图、技术架构图、图片、表格；可继承参考模版 PPT 的布局/字体/风格 | `scripts/generate_research_ppt.py` |
| [`edit-ppt`](./skills/edit-ppt/SKILL.md) | 对已有 PPT 应用结构化编辑：为文本框加 icon、按要求对齐/分布组件、替换/学术风润色文本、统一字体 | `scripts/edit_ppt.py` |
| [`pptx-to-markdown`](./skills/pptx-to-markdown/SKILL.md) | 将 PPT 提取为 SlideForge 方言的 Markdown，含标题、布局、文本、表格、图片、备注 | `scripts/pptx_to_md.py` |
| [`markdown-to-pptx`](./skills/markdown-to-pptx/SKILL.md) | 反向：把 Markdown 转为 PPT，可选用模版继承样式 | `scripts/md_to_pptx.py` |

### 三大用户场景

1. **科研技术 PPT 生成**：`generate-research-ppt`
   - 输入：内容大纲（Markdown 或 YAML）+（可选）参考模版 PPT
   - 输出：可在 PowerPoint / Keynote / WPS 中再编辑的 `.pptx`
   - 内置块：文本段、多级 bullet、表格、图片、icon（通过 `edit-ppt` 二次插入）、Mermaid 流程图 / 时序图 / 架构图
2. **PPT 编辑**：`edit-ppt`
   - 给文本框旁加 icon（内置 8 个常用图标，亦支持任意 SVG/PNG 路径）
   - 将多个组件按 left / right / top / bottom / center / 均匀分布对齐
   - 用学术风润色文本（LLM 在对话中改写，再用 `replace_text` 落盘）
   - 统一字体 / 字号 / 颜色
3. **PPT 与 Markdown 互转**：`pptx-to-markdown` + `markdown-to-pptx`
   - 任何已有 PPT → Markdown（图片自动导出到子目录）
   - Markdown → PPT，配合 `--template` 可保留原 PPT 的布局与主题

### 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 生成一份科研 PPT（使用示例大纲）
python3 scripts/generate_research_ppt.py examples/outline-demo.md \
    -o demo.pptx
#   或基于 YAML 大纲
python3 scripts/generate_research_ppt.py examples/outline-demo.yaml \
    -o demo.pptx

# 3. 用模版风格重做一份（继承字体/布局）
python3 scripts/generate_research_ppt.py examples/outline-demo.md \
    -t path/to/your_template.pptx -o demo-styled.pptx

# 4. 把已有 PPT 转成 Markdown
python3 scripts/pptx_to_md.py demo.pptx -o demo.md

# 5. 应用一组结构化编辑
python3 scripts/edit_ppt.py demo.pptx \
    --spec examples/edit-spec-demo.yaml -o demo.edited.pptx
```

> **关于流程图 / 时序图 / 架构图**：脚本通过 `mermaid-cli` 渲染。如果系统已装 Node.js，首次运行会自动通过 `npx -y @mermaid-js/mermaid-cli` 拉取并缓存；如未安装，则插入占位图并打印警告，不会中断生成。

### Markdown 方言示例

```markdown
---
title: "Efficient Sparse Attention for Long-Context LLMs"
subtitle: "Author · 2026"
template: "templates/lab.pptx"      # 可选
theme:
  primary_color: "#1F4E79"
  font: "Source Han Sans CN"
---

## Background
<!-- layout: standard -->

- 长上下文场景对注意力机制提出新挑战
- 全注意力复杂度 O(n²)，显存压力显著

---

## Architecture
<!-- layout: image -->

\`\`\`mermaid
flowchart LR
  Q[Query] --> R[Router] --> A[Sparse Attention] --> O[Output]
\`\`\`

---

## Results

| Method | Acc ↑ | Latency (ms) ↓ |
|--------|-------|----------------|
| Baseline | 0.81 | 612 |
| **Ours** | **0.88** | **187** |
```

完整示例见 [`examples/outline-demo.md`](./examples/outline-demo.md)。

### 编辑规范（edit-spec）示例

```yaml
operations:
  - op: replace_text
    slide: 1
    target: "title"
    text: "DRSA：面向长上下文 LLM 的高效稀疏注意力"

  - op: add_icon
    slide: 2
    target: "title"
    icon: "lightbulb"
    position: left
    size: 0.45

  - op: align
    slide: 2
    target: "title"
    align: center_h
    reference: slide

  - op: set_font
    slide: 2
    target: "all"
    font: "Source Han Sans CN"
    size: 18
```

完整字段参考 [`skills/edit-ppt/SKILL.md`](./skills/edit-ppt/SKILL.md)。

### 目录结构

```text
SlideForge/
├── skills/
│   ├── generate-research-ppt/SKILL.md
│   ├── edit-ppt/SKILL.md
│   ├── pptx-to-markdown/SKILL.md
│   └── markdown-to-pptx/SKILL.md
├── scripts/
│   ├── generate_research_ppt.py
│   ├── edit_ppt.py
│   ├── md_to_pptx.py
│   ├── pptx_to_md.py
│   └── slideforge/                # 内部 Python 包
│       ├── md_parser.py
│       ├── pptx_builder.py
│       ├── pptx_reader.py
│       ├── template_style.py
│       ├── editor.py
│       ├── diagrams.py
│       └── icons.py
├── examples/
│   ├── outline-demo.md
│   ├── outline-demo.yaml
│   └── edit-spec-demo.yaml
├── assets/icons/                  # 内置 SVG 图标
├── tests/
├── requirements.txt
└── LICENSE
```

### 设计原则

- **Skills as code**：每个能力都是「`SKILL.md` + 可执行脚本」的双重表达；`SKILL.md` 写给 LLM Agent 看，脚本写给机器执行。
- **模版优先**：所有生成任务都鼓励使用现成模版作为 base，把复杂的样式问题交给 PowerPoint 的 master/layout/theme 去解决。
- **LLM 负责语义、脚本负责机械操作**：例如「学术风润色」由 LLM 在对话中完成，脚本只做 `replace_text`；「选 Top-k 关键 token 加 icon」由 LLM 决定加哪些，脚本只做 `add_icon`。
- **Markdown 是中间表达**：所有能力围绕一个统一的 Markdown 方言协作，便于 LLM 阅读、生成和组合。

### 路线图

- [x] Markdown / YAML → PPT（含 mermaid 渲染）
- [x] PPT → Markdown（含图片导出）
- [x] PPT 编辑：replace_text / add_icon / align / set_font
- [ ] 原生图表（Excel-style chart）支持
- [ ] 时序图 / PlantUML 直接渲染
- [ ] 模版抽取：从一份 PPT 中提取可复用的「空模版」
- [ ] LaTeX 数学公式渲染
- [ ] 更多内置 icon（lucide / tabler 全集，按需下载）

### 许可

Apache License 2.0，详见 [LICENSE](./LICENSE)。

---

## English

**SlideForge** is a set of [Agent Skills](https://docs.anthropic.com/en/docs/agents-and-tools/agent-skills/overview) for forging research / technical slide decks. Each skill ships as a `SKILL.md` plus a small set of Python scripts, and can be invoked by Claude (or any LLM agent) or used standalone from the CLI.

### Skills

| Skill | What it does |
|-------|--------------|
| [`generate-research-ppt`](./skills/generate-research-ppt/SKILL.md) | Build an editable PPTX from a markdown / YAML outline; supports text, bullets, tables, images, icons, and Mermaid flowchart / sequence / architecture diagrams; inherits style (layouts, fonts, theme) from a reference template. |
| [`edit-ppt`](./skills/edit-ppt/SKILL.md) | Apply structured edits: add icons next to text frames, align/distribute shapes, polish text in academic style, unify fonts. |
| [`pptx-to-markdown`](./skills/pptx-to-markdown/SKILL.md) | Extract a deck's content into a SlideForge-flavored markdown document. |
| [`markdown-to-pptx`](./skills/markdown-to-pptx/SKILL.md) | The inverse — build a PPTX from markdown, optionally using a template for style. |

### Quickstart

```bash
pip install -r requirements.txt

# Generate a research PPT from an outline
python3 scripts/generate_research_ppt.py examples/outline-demo.md -o demo.pptx

# With template style inheritance
python3 scripts/generate_research_ppt.py examples/outline-demo.md \
    -t path/to/template.pptx -o demo.pptx

# Convert a deck to markdown
python3 scripts/pptx_to_md.py demo.pptx -o demo.md

# Apply structured edits
python3 scripts/edit_ppt.py demo.pptx \
    --spec examples/edit-spec-demo.yaml -o demo.edited.pptx
```

### Design principles

- **Skills as code.** Each capability is a `SKILL.md` (instructions for the LLM) + executable script (mechanical work).
- **Template-first.** Style matching is handled by reusing PowerPoint's master/layout/theme, not by reinventing them.
- **LLM does semantics, scripts do mechanics.** Polishing wording is an LLM job; the script just does deterministic `replace_text`. Choosing which icons to add is an LLM job; the script just does `add_icon`.
- **Markdown as the lingua franca.** All skills cooperate around one markdown dialect.

### License

Apache License 2.0 — see [LICENSE](./LICENSE).
