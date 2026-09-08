"""
Digikala scraper.

Strategy order (each wrapped independently — see scraper/base.py):

  1. PUBLIC PRODUCT API — Digikala's own web frontend calls
     `https://api.digikala.com/v1/product/{id}/` to render the product page,
     and this endpoint has historically been reachable without auth. This is
     far more stable than scraping rendered HTML, so we try it first.
  2. EMBEDDED JSON-LD — a `<script type="application/ld+json">` block with
     schema.org Product/Offer data, present on most Digikala product pages
     for SEO. Good fallback if the API shape changes.
  3. PLAYWRIGHT (rendered DOM) — last resort: render the page with a real
     browser and pull the price from the page text via a loose regex. Slowest,
     but survives markup changes that break strategies 1 and 2.

Digikala prices in the API are expressed in Rial; the storefront displays
Toman (Rial / 10). We normalize everything in this project to Toman, matching
the source Excel file ("قیمت دیجی‌کالا (تومان)").
"""
from __future__ import annotations

import json
import logging
import re

from scraper.base import ScrapeResult, fetch, fetch_json, normalize_price

logger = logging.getLogger("price_monitor.scraper.digikala")

_PRODUCT_ID_RE = re.compile(r"/product/dkp-(\d+)")
_API_URL = "https://api.digikala.com/v1/product/{product_id}/"


def _extract_product_id(url: str) -> str | None:
    m = _PRODUCT_ID_RE.search(url)
    return m.group(1) if m else None


def _strategy_api(url: str) -> ScrapeResult | None:
    product_id = _extract_product_id(url)
    if not product_id:
        return None
    data = fetch_json(_API_URL.format(product_id=product_id))
    if not data:
        return None
    try:
        product = data["data"]["product"]
        name = product.get("title_fa") or product.get("title_en")

        variant = product.get("default_variant") or {}
        # some categories nest variants differently; fall back to the first one
        if not variant and product.get("variants"):
            variant = product["variants"][0]

        price_block = variant.get("price") or {}
        status = variant.get("status", "")
        is_available = status == "marketable" or bool(price_block.get("selling_price"))

        rial_price = price_block.get("selling_price") or price_block.get("rrp_price")
        toman_price = normalize_price(rial_price)
        if toman_price:
            toman_price = toman_price // 10  # rial -> toman

        return ScrapeResult(
            source="digikala",
            product_name=name,
            price=toman_price if is_available else None,
            is_available=is_available,
            url=url,
            strategy_used="api",
        )
    except (KeyError, TypeError) as exc:
        logger.info("Digikala API shape unexpected for %s: %s", url, exc)
        return None


def _strategy_jsonld(url: str) -> ScrapeResult | None:
    resp = fetch(url)
    if resp is None:
        return None
    try:
        blocks = re.findall(
            r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
            resp.text,
            re.DOTALL,
        )
        for block in blocks:
            try:
                data = json.loads(block.strip())
            except json.JSONDecodeError:
                continue
            candidates = data if isinstance(data, list) else [data]
            for item in candidates:
                if not isinstance(item, dict):
                    continue
                if item.get("@type") not in ("Product", ["Product"]):
                    continue
                offers = item.get("offers") or {}
                if isinstance(offers, list):
                    offers = offers[0] if offers else {}
                price = normalize_price(offers.get("price"))
                availability = str(offers.get("availability", "")).lower()
                is_available = "outofstock" not in availability
                return ScrapeResult(
                    source="digikala",
                    product_name=item.get("name"),
                    price=price if is_available else None,
                    is_available=is_available and price is not None,
                    url=url,
                    strategy_used="jsonld",
                )
    except Exception as exc:  # never let a parsing bug take down the whole run
        logger.info("Digikala JSON-LD parse failed for %s: %s", url, exc)
    return None


def _strategy_playwright(url: str) -> ScrapeResult | None:
    try:
        from scraper.playwright_utils import render_page_text
    except ImportError:
        return None
    text = render_page_text(url, wait_selector="body")
    if not text:
        return None
    # Loose heuristic: look for a run of digits (possibly comma-grouped)
    # immediately followed by "تومان" somewhere on the rendered page.
    m = re.search(r"([\d,،]{4,})\s*تومان", text)
    price = normalize_price(m.group(1)) if m else None
    is_available = "ناموجود" not in text[:2000] and price is not None
    return ScrapeResult(
        source="digikala",
        price=price,
        is_available=is_available,
        url=url,
        strategy_used="playwright",
    )


def scrape_digikala(url: str) -> ScrapeResult:
    """Public entry point. Never raises — always returns a ScrapeResult."""
    if not url or "digikala.com" not in url:
        return ScrapeResult(source="digikala", url=url, error="invalid or missing url")

    for strategy in (_strategy_api, _strategy_jsonld, _strategy_playwright):
        try:
            result = strategy(url)
        except Exception as exc:  # belt-and-suspenders: a strategy must never propagate
            logger.warning("Digikala strategy %s raised: %s", strategy.__name__, exc)
            result = None
        if result is not None:
            return result

    return ScrapeResult(source="digikala", url=url, error="all strategies failed")


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)
    test_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.digikala.com/product/dkp-2433607/"
    print(scrape_digikala(test_url))
