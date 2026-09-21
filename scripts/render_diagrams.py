#!/usr/bin/env python3
"""Render Mermaid .mmd diagram sources to SVG, PNG, and PDF.

Usage:
    python scripts/render_diagrams.py

Reads docs/diagrams/*.mmd, writes docs/diagrams/<name>.svg, .png,
and a combined docs/diagrams/jebat-workflows.pdf.
"""
from __future__ import annotations

import base64
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas as pdf_canvas
from PIL import Image

DIAGRAMS = Path("docs/diagrams")
MERMAID_JS = DIAGRAMS / "mermaid.min.js"
DIAGRAM_TITLES = {
    "01-mcp-load": "1. MCP Load-Time Flow (IDE connects)",
    "02-cli-startup": "2. CLI Startup Flow (REPL boots)",
    "03-tool-call": "3. Runtime Tool-Call Flow",
    "04-intelligence-layer": "4. Session Intelligence Layer",
    "05-failure-loop": "5. Failure -> Learning Loop",
}

# Plain template (NOT an f-string) so JS braces stay literal.
# __MERMAID_PATH__ and __SRC_B64__ are replaced at runtime.
HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script src="__MERMAID_PATH__"></script>
<style>
  html, body { margin: 0; padding: 0; background: #ffffff; }
  #diagram { display: inline-block; }
</style>
</head>
<body>
  <div class="mermaid" id="diagram"></div>
  <script>
    const src = decodeURIComponent(escape(atob("__SRC_B64__")));
    mermaid.initialize({
      startOnLoad: false,
      theme: "default",
      securityLevel: "loose",
      flowchart: { htmlLabels: true, curve: "basis" },
      sequence: { showSequenceNumbers: false },
    });
    window.__render = async () => {
      const el = document.getElementById("diagram");
      el.textContent = src;
      const out = await mermaid.render("mmd", src);
      el.innerHTML = out.svg;
      return out.svg;
    };
  </script>
</body>
</html>"""


def write_page_file(mermaid_src: str, out_dir: Path) -> Path:
    """Write a temp HTML page (relative mermaid src) into out_dir."""
    b64 = base64.b64encode(mermaid_src.encode("utf-8")).decode("ascii")
    html = (
        HTML_TEMPLATE
        .replace("__MERMAID_PATH__", "./mermaid.min.js")
        .replace("__SRC_B64__", b64)
    )
    page_file = out_dir / "page.html"
    page_file.write_text(html, encoding="utf-8")
    return page_file


def main() -> int:
    mmd_files = sorted(DIAGRAMS.glob("*.mmd"))
    if not mmd_files:
        print("No .mmd files found in docs/diagrams/", file=sys.stderr)
        return 1
    if not MERMAID_JS.exists():
        print("mermaid.min.js not cached in docs/diagrams/", file=sys.stderr)
        return 1

    png_paths: list[Path] = []

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        # mermaid.min.js must sit next to page.html for the relative src.
        (tmp / "mermaid.min.js").write_bytes(MERMAID_JS.read_bytes())

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            for mmd in mmd_files:
                src = mmd.read_text(encoding="utf-8")
                page_file = write_page_file(src, tmp)
                page = browser.new_page(viewport={"width": 1600, "height": 1200})
                page.goto(page_file.as_uri(), wait_until="load")
                page.wait_for_function("typeof window.__render === 'function'")
                svg = page.evaluate("window.__render()")
                page.wait_for_selector("#diagram svg")

                svg_path = mmd.with_suffix(".svg")
                svg_path.write_text(svg, encoding="utf-8")

                el = page.query_selector("#diagram svg")
                if el is None:
                    print(f"  {mmd.name}: SVG element not found", file=sys.stderr)
                    page.close()
                    continue
                png_path = mmd.with_suffix(".png")
                el.screenshot(path=str(png_path), type="png")
                png_paths.append(png_path)

                print(
                    f"  {mmd.name}: SVG {svg_path.stat().st_size}B, "
                    f"PNG {png_path.stat().st_size}B"
                )
                page.close()
            browser.close()

    # Combined PDF (landscape, one diagram per page, fit to width).
    pdf_path = DIAGRAMS / "jebat-workflows.pdf"
    c = pdf_canvas.Canvas(str(pdf_path), pagesize=landscape(letter))
    pw, ph = landscape(letter)
    margin = 36
    for png in png_paths:
        title = DIAGRAM_TITLES.get(png.stem, png.stem)
        iw, ih = Image.open(png).size
        avail_w, avail_h = pw - 2 * margin, ph - 2 * margin - 24
        scale = min(avail_w / iw, avail_h / ih)
        w, h = iw * scale, ih * scale
        x, y = (pw - w) / 2, margin + (avail_h - h) / 2
        c.setFont("Helvetica-Bold", 14)
        c.drawString(margin, ph - margin, title)
        c.drawInlineImage(str(png), x, y, width=w, height=h)
        c.showPage()
    c.save()
    print(f"  PDF: {pdf_path} ({pdf_path.stat().st_size}B, {len(png_paths)} pages)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
