# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

SlideForge is a Python CLI/library toolkit for generating, editing, and converting PowerPoint (.pptx) presentations from Markdown/YAML outlines. No web servers, databases, or Docker required. The main code lives under `scripts/slideforge/` with CLI entry points in `scripts/`.

### Development setup

- **Python 3.9+** is required. Dependencies: `pip install -r requirements.txt`
- **pytest** is needed for testing but is not listed in `requirements.txt`; install with `pip install pytest`
- **cairosvg** provides high-fidelity SVG-to-PNG icon conversion; install with `pip install cairosvg`
- **ruff** can be used for linting: `pip install ruff && ruff check .`
- The codebase has no `pyproject.toml` or `setup.py`; scripts use `sys.path.insert` to locate the `slideforge` package

### Mermaid diagram rendering

Mermaid diagrams are rendered by `mmdc` (mermaid-cli). The update script installs it globally via `npm install -g @mermaid-js/mermaid-cli`.

In the Cloud Agent VM, mermaid-cli needs a puppeteer config at `~/.puppeteer.json` to find Chrome and run with `--no-sandbox`:

```json
{"launchOptions":{"args":["--no-sandbox","--disable-setuid-sandbox","--disable-dev-shm-usage","--disable-gpu"],"executablePath":"/opt/google/chrome/chrome"}}
```

The update script creates this file automatically. The env var `PUPPETEER_EXECUTABLE_PATH=/opt/google/chrome/chrome` is also set in `~/.bashrc` as a fallback.

### Running tests

```
python3 -m pytest tests/ -v
```

Tests are self-contained and create temporary PPTX files. No network access or external services needed.

### Running CLI scripts

All scripts are under `scripts/` and accept `--help`:

```
python3 scripts/generate_research_ppt.py examples/outline-demo.md -o output.pptx
python3 scripts/md_to_pptx.py examples/outline-demo.md -o output.pptx
python3 scripts/pptx_to_md.py input.pptx -o output.md
python3 scripts/edit_ppt.py input.pptx --spec examples/edit-spec-demo.yaml -o output.pptx
```

### Linting

```
ruff check .
```

There is no project-level linter config; ruff runs with defaults. Existing code has some unused-import warnings (F401) and ambiguous variable name warnings (E741) — these are pre-existing.

### Gotchas

- The actual source code is on the `cursor/add-ppt-skills-162a` feature branch; `main` only has `README.md` and `LICENSE`.
- The `summary` layout warning (`layout 'summary' not found; using fallback`) is expected behavior when using the demo outline.
- `$HOME/.local/bin` must be on `PATH` for user-installed `pytest`/`ruff` binaries to be found.
- System packages `fonts-noto-cjk`, `libcairo2-dev`, and Chrome-related libs (`libnss3`, `libgbm1`, etc.) must be installed for mermaid and cairosvg to work. The update script handles this.
