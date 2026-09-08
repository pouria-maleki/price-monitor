"""
Shared building blocks for every site-specific scraper.

Design principle (per project requirement #2): a small change on Digikala's or
Torob's side must degrade gracefully, not crash the whole check cycle. So:

  * Every network call goes through `fetch()`, which retries and never raises
    on HTTP-level failure — it returns None instead.
  * Every scraper module exposes ONE public function that internally tries
    several extraction strategies in order (API > embedded JSON > rendered
    DOM) and wraps each strategy in its own try/except.
  * If every strategy fails, we return a ScrapeResult with price=None,
    is_available=False and `error` set, instead of raising. The caller
    (the scheduler) logs it and moves on to the next product.

IMPORTANT — selector maintenance:
Digikala and Torob are both JS-rendered (Next.js) storefronts that change
their markup/API responses periodically. The selectors and JSON key names
below reflect the sites' well-documented public structure at the time this
was written, but were not (and cannot be, from this environment) verified
against the live sites. Before relying on this in production:
  1. Run `python -m scraper.selftest <product-url>` (see bottom of digikala.py
     / torob.py) against a real product URL and confirm the output looks right.
  2. If a strategy stops working, open the product page in a browser, check
     DevTools > Network for the JSON endpoint (Digikala) or view-source for
     the __NEXT_DATA__ blob (Torob), and update the corresponding function
     below — the rest of the system (DB, API, scheduler, alerts) does not
     need to change.
"""
from __future__ import annotations

import logging
import random
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import requests

logger = logging.getLogger("price_monitor.scraper")

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


@dataclass
class SellerOffer:
    """One (store, price) offer — used for Torob's list of sellers."""
    store_name: str
    price: Optional[int]
    url: Optional[str] = None
    is_available: bool = True


@dataclass
class ScrapeResult:
    source: str                       # "digikala" | "torob"
    product_name: Optional[str] = None
    price: Optional[int] = None       # toman; None = unavailable / not found
    is_available: bool = False
    url: Optional[str] = None
    checked_at: datetime = field(default_factory=datetime.utcnow)
    offers: list[SellerOffer] = field(default_factory=list)  # populated by torob
    error: Optional[str] = None
    strategy_used: Optional[str] = None


def fetch(url: str, timeout: int = 20, max_retries: int = 2, extra_headers: dict | None = None) -> Optional[requests.Response]:
    """GET a URL with a browser-like UA and light retry/backoff. Never raises."""
    import os
    headers = {**DEFAULT_HEADERS, **(extra_headers or {})}
    torob_cookie = os.getenv("TOROB_CLEARANCE_COOKIE")
    if torob_cookie and "torob.com" in url and "Cookie" not in headers:
        headers["Cookie"] = f"trb_clearance={torob_cookie}"

    for attempt in range(max_retries + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                return resp
            if resp.status_code == 490:
                logger.info("Torob returned 490 (ArCaptcha challenge) for %s", url)
                return None
            if resp.status_code in (403, 429):
                # likely rate-limited / bot-blocked — back off and retry once
                logger.warning("HTTP %s from %s (attempt %s)", resp.status_code, url, attempt + 1)
                time.sleep(1.5 + random.random() * 2)
                continue
            logger.warning("HTTP %s from %s", resp.status_code, url)
            return None
        except requests.RequestException as exc:
            logger.warning("Request error for %s (attempt %s): %s", url, attempt + 1, exc)
            time.sleep(1 + random.random())
    return None


def fetch_json(url: str, timeout: int = 20, extra_headers: dict | None = None) -> Optional[dict]:
    resp = fetch(url, timeout=timeout, extra_headers=extra_headers)
    if resp is None:
        return None
    try:
        return resp.json()
    except ValueError:
        logger.warning("Response from %s was not valid JSON", url)
        return None


_DIGIT_RE = re.compile(r"[\d۰-۹,،٬]+")
_FA_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")


def normalize_price(raw) -> Optional[int]:
    """
    Turn '2,900,000', '۲۹۰۰۰۰۰', 2900000, or '2900000 تومان' into 2900000 (int).
    Returns None for anything that doesn't contain a usable number
    (e.g. 'ناموجود', 'یافت نشد', empty string).
    """
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        val = int(raw)
        return val if val > 0 else None
    text = str(raw).translate(_FA_DIGITS)
    match = _DIGIT_RE.search(text)
    if not match:
        return None
    digits = match.group(0).replace(",", "").replace("،", "").replace("٬", "")
    if not digits.isdigit():
        return None
    val = int(digits)
    return val if val > 0 else None


def find_dicts_with_keys(obj, key_groups: list[set[str]], _out: list | None = None) -> list[dict]:
    """
    Recursively walk an arbitrary JSON-like structure (Torob's __NEXT_DATA__,
    for example) and collect every dict that contains at least one full
    key-group from `key_groups`. Used so we don't depend on one exact schema —
    if Torob renames a field we still have a chance via the other synonyms.
    """
    if _out is None:
        _out = []
    if isinstance(obj, dict):
        keys = set(obj.keys())
        for group in key_groups:
            if group.issubset(keys):
                _out.append(obj)
                break
        for v in obj.values():
            find_dicts_with_keys(v, key_groups, _out)
    elif isinstance(obj, list):
        for item in obj:
            find_dicts_with_keys(item, key_groups, _out)
    return _out
