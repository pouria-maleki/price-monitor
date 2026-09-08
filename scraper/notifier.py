"""
Telegram price-alert notifier.

Sends a message when:
  * price INCREASED by >= TELEGRAM_NOTIFY_THRESHOLD_PERCENT (default 10%), or
  * price DECREASED by any amount

Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env to enable. If either is
missing, notify() silently no-ops (so the rest of the system keeps working
without Telegram configured) — it logs once at startup instead of failing.
"""
from __future__ import annotations

import logging

import requests

from backend.app.config import get_settings

logger = logging.getLogger("price_monitor.notifier")

_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def _format_message(product_name: str, store_name: str, old_price: int | None, new_price: int, change_percent: float) -> str:
    arrow = "🔺" if change_percent > 0 else "🔻"
    old_price_txt = f"{old_price:,}" if old_price else "نامشخص"
    return (
        f"⚠️ تغییر قیمت\n\n"
        f"محصول:\n{product_name}\n\n"
        f"فروشگاه:\n{store_name}\n\n"
        f"قیمت قبلی:\n{old_price_txt}\n\n"
        f"قیمت جدید:\n{new_price:,}\n\n"
        f"تغییر:\n{arrow} {change_percent:+.1f}%"
    )


def should_notify(change_percent: float | None, threshold: float) -> bool:
    if change_percent is None:
        return False
    if change_percent < 0:
        return True  # any drop is notified
    return change_percent >= threshold


def notify_price_change(product_name: str, store_name: str, old_price: int | None, new_price: int, change_percent: float) -> bool:
    """Returns True if a message was actually sent."""
    settings = get_settings()
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        logger.debug("Telegram not configured; skipping alert for %s", product_name)
        return False

    text = _format_message(product_name, store_name, old_price, new_price, change_percent)
    try:
        resp = requests.post(
            _API_URL.format(token=settings.TELEGRAM_BOT_TOKEN),
            json={"chat_id": settings.TELEGRAM_CHAT_ID, "text": text},
            timeout=10,
        )
        if resp.status_code != 200:
            logger.warning("Telegram API returned %s: %s", resp.status_code, resp.text[:300])
            return False
        return True
    except requests.RequestException as exc:
        logger.warning("Failed to send Telegram alert: %s", exc)
        return False
