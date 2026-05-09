# SlideForge

> 一款用于快速「锻造」幻灯片的开源工具 —— Forge beautiful slides, effortlessly.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](./LICENSE)
[![Status](https://img.shields.io/badge/status-early--development-orange)](#项目状态)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](#贡献指南)

[English](#english) · [简体中文](#简体中文)

---

## 简体中文

### 项目简介

**SlideForge** 是一个开源的幻灯片（演示文稿）创作工具，致力于让用户用最少的精力，做出兼具美感与表达力的演示稿。无论你想用 Markdown 写讲稿、用模板快速搭建商业汇报，还是借助 AI 一键生成全套 Slides，SlideForge 都希望成为你的"锻造炉"。

### 核心理念

- **代码即幻灯片（Slides as Code）**：用 Markdown / 纯文本即可描述完整演示。
- **模板驱动**：内置常用模板（汇报、产品介绍、技术分享、教学课件等），开箱即用。
- **可扩展**：插件机制支持自定义主题、组件、动画与导出格式。
- **多端导出**：一份源文件，导出 HTML / PDF / PPTX / 图片等多种格式。

### 项目状态

> 当前仓库处于 **早期初始化阶段**，尚未包含可运行的源码，欢迎参与共建。

近期路线图：

- [ ] 项目脚手架与开发环境搭建
- [ ] Markdown → Slides 的核心解析与渲染
- [ ] 默认主题（Light / Dark）
- [ ] CLI 工具：`slideforge build` / `slideforge dev`
- [ ] PDF / PPTX 导出
- [ ] 模板市场与插件机制
- [ ] AI 辅助生成（大纲、配图、文案润色）

### 快速开始

> 以下命令为规划中的使用方式，待首个版本发布后可用。

```bash
# 安装（规划中）
npm install -g slideforge

# 新建一份演示
slideforge new my-deck

# 本地预览（带热更新）
cd my-deck && slideforge dev

# 构建产物
slideforge build --format pdf
```

最简幻灯片源文件示例：

```markdown
---
title: Hello SlideForge
theme: default
---

# 第一页

欢迎使用 SlideForge ✨

---

# 第二页

- 用 Markdown 写
- 用浏览器看
- 一键导出 PDF / PPTX
```

### 目录结构

```text
SlideForge/
├── LICENSE        # Apache 2.0 协议
└── README.md      # 项目说明（即本文件）
```

> 后续模块（如 `packages/core`、`packages/cli`、`themes/`、`docs/`、`examples/` 等）将在功能落地时陆续加入。

### 贡献指南

我们欢迎任何形式的贡献，包括但不限于：

- 提交 Issue 反馈 Bug 或讨论新特性
- 提交 Pull Request 修复问题或实现功能
- 完善文档、提供示例与模板
- 翻译与本地化

参与流程：

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 提交变更：`git commit -m "feat: add your feature"`
4. 推送分支：`git push origin feature/your-feature`
5. 发起 Pull Request

### 许可协议

本项目基于 [Apache License 2.0](./LICENSE) 开源，可自由用于商业与非商业用途。

---

## English

### Overview

**SlideForge** is an open-source presentation authoring tool that helps you forge beautiful slides with minimal effort. Whether you want to write decks in Markdown, scaffold a business report from a template, or generate slides with AI assistance, SlideForge aims to be your forge.

### Key Ideas

- **Slides as Code** — describe an entire deck in Markdown / plain text.
- **Template-driven** — built-in templates for reports, product intros, tech talks, and lectures.
- **Extensible** — plugin system for custom themes, components, animations and exporters.
- **Multi-format export** — one source, exported to HTML / PDF / PPTX / images.

### Project Status

This repository is in an **early bootstrap phase** — no runnable source code yet. Contributions are welcome.

Roadmap highlights:

- [ ] Project scaffolding and dev environment
- [ ] Markdown → Slides parser and renderer
- [ ] Default Light / Dark themes
- [ ] CLI: `slideforge build` / `slideforge dev`
- [ ] PDF / PPTX export
- [ ] Template marketplace and plugin system
- [ ] AI-assisted authoring (outline, images, copy polish)

### Getting Started (Planned)

```bash
npm install -g slideforge
slideforge new my-deck
cd my-deck && slideforge dev
slideforge build --format pdf
```

### Contributing

Issues and pull requests are very welcome. Please fork the repo, create a feature branch, commit your changes, and open a PR.

### License

Released under the [Apache License 2.0](./LICENSE).
