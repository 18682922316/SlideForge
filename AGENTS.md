# SlideForge

## Cursor Cloud specific instructions

### Overview

SlideForge is a pure Python CLI toolkit (no web servers, databases, or Docker). It has 4 skills for PPT generation, editing, and conversion. See the [README](./README.md) for full details.

### Running the project

- **Install deps:** `pip install -r requirements.txt`
- **Tests:** `python3 -m pytest tests/ -v`
- **Lint:** `ruff check .` (pre-existing warnings exist; exit code 1 is expected)
- All 4 CLI entry points are in `scripts/`:
  - `python3 scripts/generate_research_ppt.py examples/outline-demo.md -o out.pptx`
  - `python3 scripts/pptx_to_md.py out.pptx -o out.md`
  - `python3 scripts/edit_ppt.py out.pptx --spec examples/edit-spec-demo.yaml -o edited.pptx`
  - `python3 scripts/md_to_pptx.py examples/outline-demo.md -o from-md.pptx`

### Gotchas

- `ruff check .` returns exit code 1 due to pre-existing unused-import and ambiguous-variable warnings (F401, E741, F841). These are in the existing codebase, not introduced by changes.
- Mermaid diagram rendering requires Node.js + `@mermaid-js/mermaid-cli`. If unavailable, placeholder PNGs are silently inserted — generation does **not** fail.
- The `slideforge` package lives at `scripts/slideforge/` (not a top-level package). Tests add `scripts/` to `sys.path` manually.
- The `'summary'` layout warning during generation (`layout 'summary' not found; using fallback`) is expected — the default blank template doesn't include that layout.
