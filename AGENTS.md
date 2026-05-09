# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

SlideForge is a Python CLI/library toolkit for generating, editing, and converting PowerPoint (.pptx) presentations from Markdown/YAML outlines. No web servers, databases, or Docker required. The main code lives under `scripts/slideforge/` with CLI entry points in `scripts/`.

### Development setup

- **Python 3.9+** is required. Dependencies: `pip install -r requirements.txt`
- **pytest** is needed for testing but is not listed in `requirements.txt`; install with `pip install pytest`
- **ruff** can be used for linting: `pip install ruff && ruff check .`
- The codebase has no `pyproject.toml` or `setup.py`; scripts use `sys.path.insert` to locate the `slideforge` package

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
- Mermaid diagram rendering is optional and requires Node.js + `@mermaid-js/mermaid-cli`. Without it, placeholder PNGs are inserted instead — tests and CLI scripts still pass.
- `cairosvg` is optional for SVG icon rasterization; the code falls back to text labels without it.
- The `summary` layout warning (`layout 'summary' not found; using fallback`) is expected behavior.
- `$HOME/.local/bin` must be on `PATH` for user-installed `pytest`/`ruff` binaries to be found.
