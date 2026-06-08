"""JEBAT Browser Automation — Playwright-based web interaction.

Provides headless browser control with accessibility-tree snapshots,
element referencing (@eN), navigation, form input, screenshots, and
JS console access.  Lazy-initialises a singleton Chromium instance on
first tool call; tears down gracefully on timeout or shutdown.
"""

from __future__ import annotations

import base64
from typing import Any

from jebat.tools import register_tool

# ── Playwright availability guard ────────────────────────────────────────

_PLAYWRIGHT_AVAILABLE = True
_IMPORT_ERROR: str | None = None

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
except ImportError as exc:
    _PLAYWRIGHT_AVAILABLE = False
    _IMPORT_ERROR = (
        "Playwright is not installed.  Run:\n"
        "  pip install playwright && python -m playwright install chromium\n"
        f"Details: {exc}"
    )

# ── Singleton browser state ──────────────────────────────────────────────

_playwright_instance = None
_browser: Browser | None = None
_context: BrowserContext | None = None
_page: Page | None = None
_console_messages: list[dict[str, str]] = []
_ref_map: dict[str, str] = {}          # @eN -> CSS selector / xpath
_ref_counter: int = 0
_MAX_SNAPSHOT_CHARS = 8000


def _not_available() -> dict[str, Any]:
    """Return a helpful error when Playwright is missing."""
    return {"error": _IMPORT_ERROR or "Playwright is not available."}


async def _ensure_page() -> Page:
    """Lazily start Playwright + Chromium and return the active Page."""
    global _playwright_instance, _browser, _context, _page

    if not _PLAYWRIGHT_AVAILABLE:
        raise RuntimeError(_IMPORT_ERROR)

    if _page is not None and not _page.is_closed():
        return _page

    # Tear down stale resources
    await _cleanup_browser()

    _playwright_instance = await async_playwright().start()
    _browser = await _playwright_instance.chromium.launch(headless=True)
    _context = await _browser.new_context(
        viewport={"width": 1280, "height": 900},
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
    )
    _page = await _context.new_page()

    # Capture console output
    _page.on("console", _on_console_message)

    return _page


def _on_console_message(msg: Any) -> None:
    """Store JS console messages for later retrieval."""
    try:
        _console_messages.append({
            "type": msg.type,
            "text": msg.text,
        })
    except Exception:
        pass


async def _cleanup_browser() -> None:
    """Close browser, context, and stop Playwright."""
    global _page, _context, _browser, _playwright_instance
    try:
        if _page and not _page.is_closed():
            await _page.close()
    except Exception:
        pass
    try:
        if _context:
            await _context.close()
    except Exception:
        pass
    try:
        if _browser:
            await _browser.close()
    except Exception:
        pass
    try:
        if _playwright_instance:
            await _playwright_instance.stop()
    except Exception:
        pass
    _page = None
    _context = None
    _browser = None
    _playwright_instance = None


# ── Accessibility tree helpers ───────────────────────────────────────────

async def _build_ax_tree(page: Page) -> tuple[str, dict[str, str]]:
    """Snapshot the accessibility tree and assign @eN refs.

    Returns (formatted_text, ref_map).
    """
    global _ref_counter, _ref_map

    snapshot = await page.accessibility.snapshot(interesting_only=True)
    if snapshot is None:
        return "(empty page)", {}

    lines: list[str] = []
    ref_map: dict[str, str] = {}
    counter = 0

    def _walk(node: dict, depth: int = 0) -> None:
        nonlocal counter
        role = node.get("role", "")
        name = node.get("name", "")
        value = node.get("value", "")
        focused = node.get("focused", False)
        disabled = node.get("disabled", False)

        # Skip generic containers with no useful info
        if role in ("none", "generic", "presentation") and not name:
            for child in node.get("children", []):
                _walk(child, depth)
            return

        indent = "  " * depth
        parts = [f"{indent}[{role}]"]
        if name:
            parts.append(f'"{name}"')
        if value:
            val_str = str(value)[:80]
            parts.append(f"value={val_str!r}")
        if focused:
            parts.append("(focused)")
        if disabled:
            parts.append("(disabled)")

        # Assign a ref for interactive elements
        interactive_roles = {
            "link", "button", "textbox", "checkbox", "radio",
            "combobox", "listbox", "option", "tab", "menuitem",
            "searchbox", "spinbutton", "switch", "slider",
        }
        if role in interactive_roles and name:
            ref = f"@e{counter}"
            counter += 1
            # Build a best-effort CSS selector
            selector = _selector_for_node(node, role, name)
            ref_map[ref] = selector
            parts.append(ref)

        lines.append(" ".join(parts))

        for child in node.get("children", []):
            _walk(child, depth + 1)

    _walk(snapshot)
    _ref_counter = counter
    _ref_map = ref_map
    return "\n".join(lines), ref_map


def _selector_for_node(node: dict, role: str, name: str) -> str:
    """Build a Playwright-compatible selector from an AX node."""
    # Prefer role+name selectors which Playwright supports natively
    role_map = {
        "link": "link",
        "button": "button",
        "textbox": "textbox",
        "checkbox": "checkbox",
        "radio": "radio",
        "combobox": "combobox",
        "tab": "tab",
        "menuitem": "menuitem",
        "searchbox": "textbox",
        "spinbutton": "spinbutton",
        "switch": "checkbox",
        "slider": "slider",
        "option": "option",
        "listbox": "listbox",
    }
    pw_role = role_map.get(role, role)
    # Use case-insensitive name matching via Playwright's :text-matches
    return 'role=' + pw_role + '[name="' + name + '"i]'


# ── Tool: browser_navigate ───────────────────────────────────────────────

@register_tool(
    "browser_navigate",
    schema={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL to navigate to"},
        },
        "required": ["url"],
    },
    safety_tier="auto",
    timeout=30,
    max_output=20_000,
    description="Navigate to a URL and return page title, URL, and element refs.",
)
async def browser_navigate(url: str) -> dict[str, Any]:
    """Navigate to a URL and return page info with accessible element refs."""
    if not _PLAYWRIGHT_AVAILABLE:
        return _not_available()
    try:
        page = await _ensure_page()
        response = await page.goto(url, wait_until="domcontentloaded", timeout=25000)
        status = response.status if response else None
        title = await page.title()
        current_url = page.url

        ax_text, ref_map = await _build_ax_tree(page)
        truncated = len(ax_text) > _MAX_SNAPSHOT_CHARS
        if truncated:
            ax_text = ax_text[:_MAX_SNAPSHOT_CHARS] + "\n... (truncated)"

        return {
            "url": current_url,
            "title": title,
            "status": status,
            "elements": ax_text,
            "element_count": len(ref_map),
            "truncated": truncated,
        }
    except Exception as exc:
        return {"error": f"Navigation failed: {exc}", "url": url}


# ── Tool: browser_snapshot ───────────────────────────────────────────────

@register_tool(
    "browser_snapshot",
    schema={
        "type": "object",
        "properties": {
            "full": {
                "type": "boolean",
                "default": False,
                "description": "Return complete content (summarised if very large)",
            },
        },
    },
    safety_tier="auto",
    timeout=20,
    max_output=50_000,
    description="Get accessibility tree snapshot with @eN element refs.",
)
async def browser_snapshot(full: bool = False) -> dict[str, Any]:
    """Get accessibility tree snapshot of the current page."""
    if not _PLAYWRIGHT_AVAILABLE:
        return _not_available()
    try:
        page = await _ensure_page()
        ax_text, ref_map = await _build_ax_tree(page)

        if full:
            # Also grab visible text content for summarisation
            body_text = await page.inner_text("body")
            summary_lines = body_text.splitlines()[:200]
            summary = "\n".join(summary_lines)
            if len(body_text) > 10000:
                summary += "\n... (page text truncated)"
            return {
                "url": page.url,
                "title": await page.title(),
                "accessibility_tree": ax_text,
                "page_text_summary": summary,
                "element_count": len(ref_map),
            }

        truncated = len(ax_text) > _MAX_SNAPSHOT_CHARS
        if truncated:
            ax_text = ax_text[:_MAX_SNAPSHOT_CHARS] + "\n... (truncated, use full=True for more)"

        return {
            "url": page.url,
            "title": await page.title(),
            "snapshot": ax_text,
            "element_count": len(ref_map),
            "truncated": truncated,
        }
    except Exception as exc:
        return {"error": f"Snapshot failed: {exc}"}


# ── Tool: browser_click ──────────────────────────────────────────────────

@register_tool(
    "browser_click",
    schema={
        "type": "object",
        "properties": {
            "ref": {"type": "string", "description": "Element reference (@eN)"},
        },
        "required": ["ref"],
    },
    safety_tier="auto",
    timeout=15,
    max_output=10_000,
    description="Click an element by its @eN reference.",
)
async def browser_click(ref: str) -> dict[str, Any]:
    """Click an element identified by @eN ref."""
    if not _PLAYWRIGHT_AVAILABLE:
        return _not_available()
    if ref not in _ref_map:
        return {
            "error": f"Unknown ref '{ref}'. Take a snapshot first to get valid refs.",
            "available_refs": list(_ref_map.keys())[:20],
        }
    try:
        page = await _ensure_page()
        selector = _ref_map[ref]
        locator = page.locator(selector).first
        await locator.click(timeout=10000)
        # Wait briefly for navigation / DOM update
        await page.wait_for_timeout(500)
        title = await page.title()
        return {
            "clicked": ref,
            "selector": selector,
            "url": page.url,
            "title": title,
        }
    except Exception as exc:
        return {"error": f"Click failed for {ref}: {exc}"}


# ── Tool: browser_type ───────────────────────────────────────────────────

@register_tool(
    "browser_type",
    schema={
        "type": "object",
        "properties": {
            "ref": {"type": "string", "description": "Element reference (@eN)"},
            "text": {"type": "string", "description": "Text to type into the element"},
        },
        "required": ["ref", "text"],
    },
    safety_tier="auto",
    timeout=15,
    max_output=10_000,
    description="Type text into an element by @eN ref (clears existing content first).",
)
async def browser_type(ref: str, text: str) -> dict[str, Any]:
    """Type text into an element, clearing it first."""
    if not _PLAYWRIGHT_AVAILABLE:
        return _not_available()
    if ref not in _ref_map:
        return {
            "error": f"Unknown ref '{ref}'. Take a snapshot first.",
            "available_refs": list(_ref_map.keys())[:20],
        }
    try:
        page = await _ensure_page()
        selector = _ref_map[ref]
        locator = page.locator(selector).first
        await locator.fill(text, timeout=10000)
        return {
            "typed_into": ref,
            "text_length": len(text),
            "selector": selector,
        }
    except Exception as exc:
        return {"error": f"Type failed for {ref}: {exc}"}


# ── Tool: browser_scroll ─────────────────────────────────────────────────

@register_tool(
    "browser_scroll",
    schema={
        "type": "object",
        "properties": {
            "direction": {
                "type": "string",
                "enum": ["up", "down"],
                "default": "down",
                "description": "Scroll direction",
            },
        },
    },
    safety_tier="auto",
    timeout=10,
    max_output=5_000,
    description="Scroll the page up or down.",
)
async def browser_scroll(direction: str = "down") -> dict[str, Any]:
    """Scroll the page in the given direction."""
    if not _PLAYWRIGHT_AVAILABLE:
        return _not_available()
    try:
        page = await _ensure_page()
        delta = 600 if direction == "down" else -600
        await page.evaluate(f"window.scrollBy(0, {delta})")
        await page.wait_for_timeout(300)
        scroll_y = await page.evaluate("window.scrollY")
        return {
            "direction": direction,
            "scroll_y": scroll_y,
            "url": page.url,
        }
    except Exception as exc:
        return {"error": f"Scroll failed: {exc}"}


# ── Tool: browser_back ───────────────────────────────────────────────────

@register_tool(
    "browser_back",
    schema={"type": "object", "properties": {}},
    safety_tier="auto",
    timeout=15,
    max_output=10_000,
    description="Navigate back to the previous page.",
)
async def browser_back() -> dict[str, Any]:
    """Navigate back in browser history."""
    if not _PLAYWRIGHT_AVAILABLE:
        return _not_available()
    try:
        page = await _ensure_page()
        await page.go_back(wait_until="domcontentloaded", timeout=15000)
        title = await page.title()
        ax_text, ref_map = await _build_ax_tree(page)
        truncated = len(ax_text) > _MAX_SNAPSHOT_CHARS
        if truncated:
            ax_text = ax_text[:_MAX_SNAPSHOT_CHARS] + "\n... (truncated)"
        return {
            "url": page.url,
            "title": title,
            "elements": ax_text,
            "element_count": len(ref_map),
            "truncated": truncated,
        }
    except Exception as exc:
        return {"error": f"Back navigation failed: {exc}"}


# ── Tool: browser_vision ─────────────────────────────────────────────────

@register_tool(
    "browser_vision",
    schema={
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "Question about what is visible on screen",
            },
            "annotate": {
                "type": "boolean",
                "default": False,
                "description": "Annotate screenshot with element bounding boxes",
            },
        },
        "required": ["question"],
    },
    safety_tier="auto",
    timeout=20,
    max_output=20_000,
    description="Take a screenshot and describe what is visible.",
)
async def browser_vision(question: str, annotate: bool = False) -> dict[str, Any]:
    """Capture a screenshot and provide analysis.

    Note: Full AI vision requires an external vision model.  This tool
    captures the screenshot and returns it as base64 along with the
    accessibility tree so the calling agent can analyse it.
    """
    if not _PLAYWRIGHT_AVAILABLE:
        return _not_available()
    try:
        page = await _ensure_page()
        screenshot_bytes = await page.screenshot(type="png", full_page=False)
        b64 = base64.b64encode(screenshot_bytes).decode("ascii")

        # Provide the AX tree as structured context for the question
        ax_text, ref_map = await _build_ax_tree(page)

        result: dict[str, Any] = {
            "question": question,
            "url": page.url,
            "title": await page.title(),
            "screenshot_base64": b64[:100] + "... (truncated for display)",
            "screenshot_size_bytes": len(screenshot_bytes),
            "accessibility_context": ax_text[:4000],
            "note": (
                "Screenshot captured as PNG. Use the accessibility_context "
                "above to answer the question. For full visual analysis, "
                "pass screenshot_base64 to a vision-capable model."
            ),
        }

        if annotate:
            # Gather bounding boxes for all interactive elements
            annotations: list[dict[str, Any]] = []
            for ref, selector in list(ref_map.items())[:30]:
                try:
                    box = await page.locator(selector).first.bounding_box(timeout=2000)
                    if box:
                        annotations.append({
                            "ref": ref,
                            "x": round(box["x"]),
                            "y": round(box["y"]),
                            "width": round(box["width"]),
                            "height": round(box["height"]),
                        })
                except Exception:
                    pass
            result["annotations"] = annotations

        return result
    except Exception as exc:
        return {"error": f"Vision capture failed: {exc}"}


# ── Tool: browser_console ────────────────────────────────────────────────

@register_tool(
    "browser_console",
    schema={
        "type": "object",
        "properties": {
            "clear": {
                "type": "boolean",
                "default": False,
                "description": "Clear stored console messages",
            },
            "expression": {
                "type": "string",
                "description": "JavaScript expression to evaluate",
            },
        },
    },
    safety_tier="confirm",
    timeout=15,
    max_output=20_000,
    description="Access JS console output or evaluate a JavaScript expression.",
)
async def browser_console(clear: bool = False, expression: str | None = None) -> dict[str, Any]:
    """Get console messages or evaluate JS."""
    if not _PLAYWRIGHT_AVAILABLE:
        return _not_available()
    try:
        page = await _ensure_page()

        if clear:
            _console_messages.clear()
            return {"cleared": True, "message_count": 0}

        if expression is not None:
            result = await page.evaluate(expression)
            return {
                "expression": expression,
                "result": str(result)[:5000],
                "result_type": type(result).__name__,
            }

        # Return stored console messages
        msgs = _console_messages[-100:]  # last 100
        return {
            "messages": msgs,
            "total_stored": len(_console_messages),
            "showing": len(msgs),
        }
    except Exception as exc:
        return {"error": f"Console operation failed: {exc}"}


# ── Tool: browser_get_images ─────────────────────────────────────────────

@register_tool(
    "browser_get_images",
    schema={"type": "object", "properties": {}},
    safety_tier="auto",
    timeout=15,
    max_output=20_000,
    description="List all images on the current page with URLs and alt text.",
)
async def browser_get_images() -> dict[str, Any]:
    """Extract all <img> elements with src and alt attributes."""
    if not _PLAYWRIGHT_AVAILABLE:
        return _not_available()
    try:
        page = await _ensure_page()
        images = await page.evaluate("""
            () => {
                const imgs = document.querySelectorAll('img');
                return Array.from(imgs).map(img => ({
                    src: img.src || '',
                    alt: img.alt || '',
                    width: img.naturalWidth || img.width || 0,
                    height: img.naturalHeight || img.height || 0,
                    loading: img.loading || 'eager',
                }));
            }
        """)
        return {
            "url": page.url,
            "image_count": len(images),
            "images": images,
        }
    except Exception as exc:
        return {"error": f"Image extraction failed: {exc}"}


# ── Cleanup hook ─────────────────────────────────────────────────────────

async def browser_cleanup() -> None:
    """Public cleanup function for graceful shutdown."""
    await _cleanup_browser()
