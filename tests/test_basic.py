"""Smoke tests for the SlideForge skill scripts.

Run with::

    python3 -m pytest tests/

These tests do not require network access (mermaid blocks fall back to
placeholder PNGs if mermaid-cli isn't installed).
"""
from __future__ import annotations

import os
import sys
import tempfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from slideforge.editor import apply_edits  # noqa: E402
from slideforge.md_parser import parse_markdown  # noqa: E402
from slideforge.pptx_builder import build_pptx  # noqa: E402
from slideforge.pptx_reader import pptx_to_markdown  # noqa: E402


SIMPLE_MD = """\
---
title: "Test Deck"
subtitle: "by SlideForge"
---

## Background
<!-- layout: standard -->

- bullet one
- bullet two
  - nested

---

## Results

| Method | Acc |
|--------|-----|
| Base   | 0.8 |
| Ours   | 0.9 |
"""


def test_parse_markdown():
    deck = parse_markdown(SIMPLE_MD)
    assert deck.front_matter["title"] == "Test Deck"
    assert len(deck.slides) == 2
    assert deck.slides[0].title == "Background"
    assert deck.slides[0].layout == "standard"
    assert deck.slides[1].has_table()


def test_md_to_pptx_to_md_roundtrip(tmp_path):
    pptx_path = str(tmp_path / "deck.pptx")
    md_out_path = str(tmp_path / "deck.md")

    deck = parse_markdown(SIMPLE_MD)
    build_pptx(deck, pptx_path)
    assert os.path.exists(pptx_path)

    md = pptx_to_markdown(pptx_path, out_md_path=md_out_path)
    assert "Background" in md
    assert "bullet one" in md
    assert "| Method | Acc |" in md or "Method" in md


def test_edit_replace_text(tmp_path):
    deck = parse_markdown(SIMPLE_MD)
    pptx_in = str(tmp_path / "in.pptx")
    pptx_out = str(tmp_path / "out.pptx")
    build_pptx(deck, pptx_in)

    spec = {
        "operations": [
            {"op": "replace_text", "slide": 2, "target": "title", "text": "New Background"},
        ]
    }
    report = apply_edits(pptx_in, spec, pptx_out)
    assert report["applied"] == 1
    assert report["failed"] == 0

    md = pptx_to_markdown(pptx_out, out_md_path=str(tmp_path / "out.md"))
    assert "New Background" in md


def test_edit_add_icon_and_align(tmp_path):
    deck = parse_markdown(SIMPLE_MD)
    pptx_in = str(tmp_path / "in.pptx")
    pptx_out = str(tmp_path / "out.pptx")
    build_pptx(deck, pptx_in)

    spec = {
        "operations": [
            {"op": "add_icon", "slide": 2, "target": "title",
             "icon": "lightbulb", "position": "left", "size": 0.4},
            {"op": "align", "slide": 2, "target": "title",
             "align": "center_h", "reference": "slide"},
            {"op": "set_font", "slide": 2, "target": "all",
             "font": "Arial", "size": 16},
        ]
    }
    report = apply_edits(pptx_in, spec, pptx_out)
    assert report["failed"] == 0
    assert report["applied"] == 3
