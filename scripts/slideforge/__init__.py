"""SlideForge core package.

Modules
-------
- md_parser:      Parse the SlideForge markdown dialect into slide IR.
- pptx_builder:   Build a .pptx from slide IR + (optional) template.
- pptx_reader:    Extract slide content from a .pptx into IR / markdown.
- template_style: Inspect a template's theme (fonts, colors, layouts).
- diagrams:       Render mermaid blocks to PNG images via mermaid-cli.
- icons:          Resolve icon names / paths to image files.
- editor:         Apply structured edit operations to a .pptx.
"""
__version__ = "0.1.0"
