"""
Playwright-based rendering, used ONLY as the last-resort fallback strategy
in digikala.py / torob.py (project requirement: "اگر سایت‌ها API نداشتند از
Playwright استفاده کن").

Kept in its own module and imported lazily (inside a try/except) so that:
  * the API/JSON-based fast paths work even if Playwright/browsers aren't
    installed in a given environment, and
  * a missing browser install never crashes the whole scrape cycle — it just
    disables the fallback for that run.

Requires: `pip install playwright && playwright install --with-deps chromium`
(see backend/requirements.txt and the Dockerfile, which do this at build time).
"""
from __future__ import annotations

import logging

logger = logging.getLogger("price_monitor.scraper.playwright")

_TIMEOUT_MS = 20_000


def _new_page(browser):
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        locale="fa-IR",
    )
    return context.new_page()


def render_page_html(url: str, wait_selector: str = "body", timeout_ms: int = _TIMEOUT_MS) -> str | None:
    """Render `url` in headless Chromium and return the final HTML, or None on any failure."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.info("playwright not installed; skipping browser fallback for %s", url)
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = _new_page(browser)
                page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
                page.wait_for_selector(wait_selector, timeout=timeout_ms)
                html = page.content()
                return html
            finally:
                browser.close()
    except Exception as exc:
        logger.warning("Playwright render failed for %s: %s", url, exc)
        return None


def render_page_text(url: str, wait_selector: str = "body", timeout_ms: int = _TIMEOUT_MS) -> str | None:
    html = render_page_html(url, wait_selector=wait_selector, timeout_ms=timeout_ms)
    if html is None:
        return None
    try:
        from bs4 import BeautifulSoup

        return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    except ImportError:
        # crude tag-stripping fallback if bs4 somehow isn't available
        import re

        return re.sub(r"<[^>]+>", " ", html)
