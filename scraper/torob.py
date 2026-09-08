"""
Torob scraper.

Torob is a price-comparison engine: one product page lists many sellers.
We need at least the 3 cheapest (project requirement #2-b).

Strategy order:

  1. EMBEDDED __NEXT_DATA__ JSON — Torob's product page is a Next.js app; the
     full seller/price list used to hydrate the page ships as a JSON blob
     inside `<script id="__next_data__">` (or `id="__NEXT_DATA__"`). We parse
     it and recursively search for dict objects that look like a seller offer
     (matched by *sets of synonymous keys* so small renames don't break us —
     see `find_dicts_with_keys` in base.py).
  2. PLAYWRIGHT (rendered DOM) — if the JSON blob is missing/renamed, render
     the page and scrape the visible seller rows with a best-effort CSS
     selector. This is the slowest and most fragile path, kept as a last
     resort only.

Every seller's price is already in Toman on Torob (unlike Digikala's API).
"""
from __future__ import annotations

import json
import logging
import re

from scraper.base import ScrapeResult, SellerOffer, fetch, find_dicts_with_keys, normalize_price

logger = logging.getLogger("price_monitor.scraper.torob")

# Synonymous key-sets that a "seller offer" object might use across Torob's
# JSON versions. Widen this list first if extraction starts coming back empty.
_OFFER_KEY_GROUPS = [
    {"shop_name", "price"},
    {"shop_text", "price"},
    {"seller_name", "price"},
    {"name", "price", "url"},
    {"title", "price", "link"},
]

_NEXT_DATA_RE = re.compile(
    r'<script[^>]+id="(?:__NEXT_DATA__|__next_data__)"[^>]*>(.*?)</script>',
    re.DOTALL,
)


def _offer_from_dict(d: dict) -> SellerOffer | None:
    store_name = (
        d.get("shop_name") or d.get("shop_text") or d.get("seller_name")
        or d.get("name") or d.get("title")
    )
    price = normalize_price(d.get("price"))
    url = d.get("url") or d.get("link") or d.get("shop_url")
    if not store_name or price is None:
        return None
    # filter out unrelated dicts that merely happen to share key names
    # (e.g. breadcrumb/category nodes) by requiring a plausible price range
    if price < 1000:
        return None
    return SellerOffer(store_name=str(store_name).strip(), price=price, url=url, is_available=True)


_PRK_RE = re.compile(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})")


def _strategy_api(url: str) -> ScrapeResult | None:
    """Strategy 1: Direct JSON API from Torob."""
    m = _PRK_RE.search(url)
    if not m:
        return None
    prk = m.group(1)

    extra_h = {
        "Accept": "application/json, text/plain, */*",
        "Referer": f"https://torob.com/p/{prk}/",
        "Origin": "https://torob.com",
    }

    # 1. Try sellers list API
    sellers_url = f"https://api.torob.com/v4/base-product/sellers/?prk={prk}"
    resp = fetch(sellers_url, extra_headers=extra_h)
    if resp is not None and resp.status_code == 200:
        try:
            data = resp.json()
            results = data.get("results", [])
            offers: list[SellerOffer] = []
            seen = set()
            for r in results:
                price = normalize_price(r.get("price"))
                shop = r.get("shop_name") or r.get("shop_name2") or "فروشگاه ترب"
                page_url = r.get("page_url")
                is_avail = bool(r.get("availability", True))
                if price and is_avail and price > 1000 and (shop, price) not in seen:
                    offers.append(SellerOffer(store_name=shop, price=price, url=page_url, is_available=True))
                    seen.add((shop, price))
            if offers:
                offers.sort(key=lambda o: o.price)
                return ScrapeResult(
                    source="torob",
                    product_name=None,
                    price=offers[0].price,
                    is_available=True,
                    url=url,
                    offers=offers[:10],
                    strategy_used="torob_api_v4_sellers",
                )
        except Exception as exc:
            logger.info("Torob sellers API parse error: %s", exc)

    # 2. Try details-log-click API
    details_url = f"https://api.torob.com/v4/base-product/details-log-click/?prk={prk}"
    resp_details = fetch(details_url, extra_headers=extra_h)
    if resp_details is not None and resp_details.status_code == 200:
        try:
            d = resp_details.json()
            price = normalize_price(d.get("price"))
            name = d.get("name1")
            if price and price > 1000:
                return ScrapeResult(
                    source="torob",
                    product_name=name,
                    price=price,
                    is_available=True,
                    url=url,
                    offers=[SellerOffer(store_name="کف قیمت ترب", price=price, is_available=True)],
                    strategy_used="torob_api_v4_details",
                )
        except Exception as exc:
            logger.info("Torob details API parse error: %s", exc)

    return None


def _strategy_next_data(url: str) -> ScrapeResult | None:
    resp = fetch(url)
    if resp is None:
        return None
    match = _NEXT_DATA_RE.search(resp.text)
    if not match:
        return None
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        logger.info("Torob __NEXT_DATA__ not valid JSON for %s: %s", url, exc)
        return None

    candidate_dicts = find_dicts_with_keys(data, _OFFER_KEY_GROUPS)
    offers: list[SellerOffer] = []
    seen = set()
    for d in candidate_dicts:
        offer = _offer_from_dict(d)
        if offer and (offer.store_name, offer.price) not in seen:
            offers.append(offer)
            seen.add((offer.store_name, offer.price))

    if not offers:
        return None

    offers.sort(key=lambda o: o.price)

    # try to also grab a product title for logging/verification purposes
    name = None
    title_match = re.search(r'"page_title"\s*:\s*"([^"]+)"', match.group(1))
    if title_match:
        name = title_match.group(1)

    top = offers[0]
    return ScrapeResult(
        source="torob",
        product_name=name,
        price=top.price,
        is_available=True,
        url=url,
        offers=offers[:10],
        strategy_used="next_data",
    )


def _strategy_playwright(url: str) -> ScrapeResult | None:
    try:
        from scraper.playwright_utils import render_page_html
    except ImportError:
        return None
    html = render_page_html(url, wait_selector="body")
    if not html:
        return None
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.warning("beautifulsoup4 not installed; cannot run Torob DOM fallback")
        return None

    soup = BeautifulSoup(html, "html.parser")
    offers: list[SellerOffer] = []
    # Best-effort: Torob seller rows are typically <a> or <div> blocks that
    # contain both a shop name and a price ending in "تومان". Inspect the
    # live page and tighten this selector if it returns nothing useful.
    for row in soup.select("[class*='shop'], [class*='seller'], [class*='price-row']"):
        text = row.get_text(" ", strip=True)
        price_match = re.search(r"([\d,،]{4,})\s*تومان", text)
        if not price_match:
            continue
        price = normalize_price(price_match.group(1))
        name_guess = text.split(price_match.group(0))[0].strip()[:60] or "فروشگاه نامشخص"
        link = row.get("href")
        if price:
            offers.append(SellerOffer(store_name=name_guess, price=price, url=link))

    if not offers:
        return None
    offers.sort(key=lambda o: o.price)
    return ScrapeResult(
        source="torob", price=offers[0].price, is_available=True, url=url,
        offers=offers[:10], strategy_used="playwright",
    )


def scrape_torob(url: str, min_sellers: int = 3) -> ScrapeResult:
    """
    Public entry point. Returns a ScrapeResult whose `offers` list holds at
    least `min_sellers` cheapest sellers when available (fewer if the product
    genuinely has fewer listings). Never raises.
    """
    if not url or "torob.com" not in url:
        return ScrapeResult(source="torob", url=url, error="invalid or missing url")

    for strategy in (_strategy_api, _strategy_next_data, _strategy_playwright):
        try:
            result = strategy(url)
        except Exception as exc:
            logger.warning("Torob strategy %s raised: %s", strategy.__name__, exc)
            result = None
        if result is not None:
            return result

    return ScrapeResult(source="torob", url=url, error="all strategies failed")


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)
    test_url = sys.argv[1] if len(sys.argv) > 1 else "https://torob.com/p/3ecfc90f-9000-4222-8ac8-f3e4b1798404/"
    r = scrape_torob(test_url)
    print(r)
    for o in r.offers:
        print(" -", o)
