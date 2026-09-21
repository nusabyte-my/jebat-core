"""Visual UI critique pipeline for JEBAT (Pawang Estetika).

Renders UI markup or live URLs in headless Chromium via Playwright, captures screenshots,
measures real layout facts (WCAG relative luminance contrast, horizontal overflow,
interactive touch targets, font sizes, prefers-reduced-motion), and combines static
Hallmark critique with vision analysis.
"""

from __future__ import annotations
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

from jebat.features.browser.browser import _ensure_page, _PLAYWRIGHT_AVAILABLE
from jebat.tools.design_tools import ui_critique

VIEWPORTS: Dict[str, Dict[str, int]] = {
    "desktop": {"width": 1280, "height": 900},
    "tablet": {"width": 768, "height": 1024},
    "mobile": {"width": 375, "height": 812},
}

JS_MEASUREMENTS_SCRIPT = """
() => {
    function getLuminance(r, g, b) {
        const a = [r, g, b].map(v => {
            v /= 255;
            return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
        });
        return a[0] * 0.2126 + a[1] * 0.7152 + a[2] * 0.0722;
    }

    function parseRgb(colorStr) {
        if (!colorStr) return [255, 255, 255];
        const match = colorStr.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)/);
        if (match) {
            return [parseInt(match[1]), parseInt(match[2]), parseInt(match[3])];
        }
        return [255, 255, 255];
    }

    function getContrast(rgb1, rgb2) {
        const l1 = getLuminance(rgb1[0], rgb1[1], rgb1[2]);
        const l2 = getLuminance(rgb2[0], rgb2[1], rgb2[2]);
        const lighter = Math.max(l1, l2);
        const darker = Math.min(l1, l2);
        return (lighter + 0.05) / (darker + 0.05);
    }

    const body = document.body;
    const bodyStyle = window.getComputedStyle(body);
    const textEl = document.querySelector('p, span, h1, h2, h3, h4, button, a') || body;
    const textStyle = window.getComputedStyle(textEl);
    const fgRgb = parseRgb(textStyle.color);
    let bgRgb = parseRgb(textStyle.backgroundColor);
    if (textStyle.backgroundColor === 'rgba(0, 0, 0, 0)' || textStyle.backgroundColor === 'transparent') {
        bgRgb = parseRgb(bodyStyle.backgroundColor);
    }
    const contrastRatio = Math.round(getContrast(fgRgb, bgRgb) * 100) / 100;

    const docEl = document.documentElement;
    const hasHorizontalOverflow = docEl.scrollWidth > docEl.clientWidth;

    const fontSizes = new Set();
    document.querySelectorAll('*').forEach(el => {
        const fs = window.getComputedStyle(el).fontSize;
        if (fs) fontSizes.add(fs);
    });

    const interactiveElements = [];
    document.querySelectorAll('button, a, input, select, [role="button"]').forEach(el => {
        const rect = el.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0) {
            interactiveElements.push({
                tag: el.tagName.toLowerCase(),
                text: (el.innerText || el.value || el.getAttribute('aria-label') || '').slice(0, 30).trim(),
                width: Math.round(rect.width),
                height: Math.round(rect.height),
                meets_apple_44px: rect.width >= 44 && rect.height >= 44,
                meets_material_48px: rect.width >= 48 && rect.height >= 48
            });
        }
    });

    let respectsReducedMotion = true;
    const animated = Array.from(document.querySelectorAll('*')).some(el => {
        const style = window.getComputedStyle(el);
        return (style.animationName && style.animationName !== 'none') ||
               (style.transitionDuration && style.transitionDuration !== '0s');
    });
    if (animated) {
        let hasMediaRule = false;
        for (const sheet of Array.from(document.styleSheets)) {
            try {
                for (const rule of Array.from(sheet.cssRules || [])) {
                    if (rule.media && rule.media.mediaText.includes('prefers-reduced-motion')) {
                        hasMediaRule = true;
                        break;
                    }
                }
            } catch (e) {}
        }
        respectsReducedMotion = hasMediaRule;
    }

    return {
        body_contrast: {
            ratio: contrastRatio,
            foreground: textStyle.color,
            background: textStyle.backgroundColor !== 'rgba(0, 0, 0, 0)' ? textStyle.backgroundColor : bodyStyle.backgroundColor,
            meets_wcag_aa_body: contrastRatio >= 4.5,
            meets_wcag_aa_large: contrastRatio >= 3.0
        },
        horizontal_overflow: hasHorizontalOverflow,
        scroll_width: docEl.scrollWidth,
        client_width: docEl.clientWidth,
        font_sizes_applied: Array.from(fontSizes).slice(0, 10),
        interactive_elements: interactiveElements.slice(0, 15),
        respects_reduced_motion: respectsReducedMotion
    };
}
"""


async def run_visual_critique(
    markup: str = "",
    url: str = "",
    viewport: str = "desktop",
) -> Dict[str, Any]:
    """Render UI markup or URL, capture screenshot, measure layout facts, and run critique."""
    if not _PLAYWRIGHT_AVAILABLE:
        return {
            "rendered": False,
            "error": "Playwright is not available. Install with: pip install playwright && python -m playwright install chromium",
            "static_critique": await ui_critique(markup or "", component_type="generic") if markup else {},
            "visual_analysis": "unavailable",
            "verdict": "Unrendered — Playwright unavailable.",
        }

    vp = VIEWPORTS.get(viewport.lower(), VIEWPORTS["desktop"])
    temp_html_path: Path | None = None
    target_url: str = ""

    if url:
        target_url = url
    elif markup:
        standalone_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{ margin: 0; padding: 16px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #ffffff; color: #111827; }}
  </style>
</head>
<body>
  {markup}
</body>
</html>"""
        fd, tmp_file = tempfile.mkstemp(suffix=".html", prefix="jebat_ui_")
        os.write(fd, standalone_html.encode("utf-8"))
        os.close(fd)
        temp_html_path = Path(tmp_file).resolve()
        target_url = temp_html_path.as_uri()
    else:
        return {
            "rendered": False,
            "error": "Neither markup nor url provided.",
            "visual_analysis": "unavailable",
            "verdict": "No input provided.",
        }

    screenshot_path: Path | None = None
    measurements: Dict[str, Any] = {}
    rendered = False

    try:
        page = await _ensure_page()
        await page.set_viewport_size(vp)
        await page.goto(target_url, wait_until="load", timeout=15000)
        await page.wait_for_timeout(300)

        # 1. Capture screenshot
        fd_png, tmp_png = tempfile.mkstemp(suffix=".png", prefix="jebat_screenshot_")
        os.close(fd_png)
        screenshot_path = Path(tmp_png).resolve()
        await page.screenshot(path=str(screenshot_path), type="png")
        rendered = True

        # 2. Run in-page layout and contrast measurements
        measurements = await page.evaluate(JS_MEASUREMENTS_SCRIPT)

    except Exception as exc:
        return {
            "rendered": False,
            "error": f"Rendering failed: {exc}",
            "static_critique": await ui_critique(markup or "", component_type="generic") if markup else {},
            "visual_analysis": "unavailable",
            "verdict": f"Render failed: {exc}",
        }
    finally:
        if temp_html_path and temp_html_path.exists():
            try:
                temp_html_path.unlink()
            except Exception:
                pass

    # 3. Static critique
    static_critique = await ui_critique(markup or "", component_type="generic") if markup else {}

    # 4. Vision analysis via existing vision pipeline
    visual_analysis: str = "unavailable"
    if screenshot_path and screenshot_path.exists():
        try:
            from jebat.features.vision.vision import vision_analyze
            prompt = (
                "Evaluate this UI screenshot against the Hallmark 6-axis anti-slop rubric: "
                "Philosophy, Hierarchy, Execution, Specificity, Restraint, Variety. "
                "Provide concrete observations and identify any visual defects."
            )
            v_result = await vision_analyze(image_url=str(screenshot_path), question=prompt)
            if isinstance(v_result, dict) and "error" in v_result:
                visual_analysis = f"unavailable: {v_result.get('error')}"
            elif isinstance(v_result, dict):
                visual_analysis = v_result.get("answer", str(v_result))
            else:
                visual_analysis = str(v_result)
        except RuntimeError as err:
            visual_analysis = f"unavailable: {err}"
        except Exception as exc:
            visual_analysis = f"unavailable: {exc}"

    # 5. Formulate verdict
    verdict_items = []
    if measurements:
        contrast = measurements.get("body_contrast", {})
        if not contrast.get("meets_wcag_aa_body", True):
            verdict_items.append(f"Low text contrast ({contrast.get('ratio')}:1 fails WCAG AA 4.5:1)")
        if measurements.get("horizontal_overflow"):
            verdict_items.append("Horizontal overflow detected (scrollWidth > clientWidth)")

        failed_targets = [
            el["tag"] for el in measurements.get("interactive_elements", [])
            if not el.get("meets_apple_44px")
        ]
        if failed_targets:
            verdict_items.append(f"{len(failed_targets)} interactive elements below 44px touch target")

    static_status = static_critique.get("status", "pass")
    if static_status == "needs_revision":
        verdict_items.append(f"Static critique identified {len(static_critique.get('violations', []))} violations")

    if not verdict_items:
        verdict = "PASS — Clean visual rendering, WCAG AA contrast compliant, no overflow detected."
    else:
        verdict = f"NEEDS REVISION — {'; '.join(verdict_items)}."

    # 6. Terse mode check
    is_terse = False
    try:
        from jebat.features.mcp.mcp_server import mcp_terse_mode
        is_terse = mcp_terse_mode()
    except Exception:
        pass

    if is_terse:
        return {
            "rendered": rendered,
            "status": "pass" if not verdict_items else "needs_revision",
            "scores": static_critique.get("scores", {}),
            "contrast_ratio": measurements.get("body_contrast", {}).get("ratio"),
            "horizontal_overflow": measurements.get("horizontal_overflow", False),
        }

    return {
        "rendered": rendered,
        "screenshot_path": str(screenshot_path) if screenshot_path else "",
        "dimensions": vp,
        "measurements": measurements,
        "static_critique": static_critique,
        "visual_analysis": visual_analysis,
        "verdict": verdict,
    }
