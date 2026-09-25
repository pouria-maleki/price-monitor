"""
RoyalDigi scraper.

Fetches product prices and stock availability directly from royaldigi.ir
via WooCommerce canonical product ID or slug URL.
Uses embedded Schema.org JSON-LD for 100% reliable extraction.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Optional

from scraper.base import ScrapeResult, SellerOffer, fetch, normalize_price

logger = logging.getLogger("price_monitor.scraper.royaldigi")

_JSON_LD_RE = re.compile(
    r'<script\s+type="application/ld\+json"[^>]*>(.*?)</script>',
    re.DOTALL,
)
_PRICE_REGEX = re.compile(r'"price":\s*"(\d+)"')


def scrape_royaldigi(
    url_or_id: str | int,
    product_slug_url: str | None = None,
) -> ScrapeResult:
    """
    Scrapes royaldigi.ir product page by woo_id (e.g. 1779) or full URL.
    """
    if isinstance(url_or_id, int) or (isinstance(url_or_id, str) and url_or_id.isdigit()):
        url = f"https://royaldigi.ir/?p={url_or_id}"
    elif isinstance(url_or_id, str) and url_or_id.startswith("http"):
        url = url_or_id
    elif product_slug_url and product_slug_url.startswith("http"):
        url = product_slug_url
    else:
        return ScrapeResult(source="royaldigi", url=str(url_or_id), error="Invalid RoyalDigi URL or ID")

    resp = fetch(url, extra_headers={"Referer": "https://royaldigi.ir/"})
    if resp is None or resp.status_code != 200:
        return ScrapeResult(source="royaldigi", url=url, error="Failed to fetch page")

    html = resp.text
    final_url = resp.url

    # Strategy 1: Schema.org JSON-LD
    for block in _JSON_LD_RE.findall(html):
        try:
            data = json.loads(block)
            nodes = data.get("@graph", [data]) if isinstance(data, dict) else data
            if isinstance(nodes, dict):
                nodes = [nodes]
            for node in nodes:
                if not isinstance(node, dict):
                    continue
                offers = node.get("offers")
                if isinstance(offers, list) and offers:
                    offers = offers[0]
                if isinstance(offers, dict):
                    raw_price = offers.get("price")
                    price = normalize_price(raw_price)
                    is_in_stock = "InStock" in str(offers.get("availability", ""))
                    if price:
                        return ScrapeResult(
                            source="royaldigi",
                            product_name=node.get("name"),
                            price=price,
                            is_available=is_in_stock,
                            url=final_url,
                            offers=[SellerOffer(store_name="رویال‌دیجی", price=price, is_available=is_in_stock)],
                            strategy_used="json_ld",
                        )
        except Exception as exc:
            logger.debug("Error parsing JSON-LD in %s: %s", url, exc)

    # Strategy 2: Fast Regex Fallback for "price": "123456"
    price_matches = _PRICE_REGEX.findall(html)
    if price_matches:
        price = normalize_price(price_matches[0])
        if price and price > 1000:
            return ScrapeResult(
                source="royaldigi",
                price=price,
                is_available=True,
                url=final_url,
                offers=[SellerOffer(store_name="رویال‌دیجی", price=price, is_available=True)],
                strategy_used="regex_price",
            )

    return ScrapeResult(source="royaldigi", url=final_url, error="Price not found on page")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    test_id = sys.argv[1] if len(sys.argv) > 1 else "1779"
    res = scrape_royaldigi(test_id)
    print(res)
