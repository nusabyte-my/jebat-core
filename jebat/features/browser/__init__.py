"""JEBAT Browser Automation — Playwright-based web interaction tools.

Exports all browser_* tools for registration in the JEBAT tool registry.
Import this package to make browser tools available.
"""

from jebat.features.browser.browser import (
    browser_back,
    browser_cleanup,
    browser_click,
    browser_console,
    browser_get_images,
    browser_navigate,
    browser_scroll,
    browser_snapshot,
    browser_type,
    browser_vision,
)

__all__ = [
    "browser_navigate",
    "browser_snapshot",
    "browser_click",
    "browser_type",
    "browser_scroll",
    "browser_back",
    "browser_vision",
    "browser_console",
    "browser_get_images",
    "browser_cleanup",
]
