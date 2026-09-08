"""
Periodic price-check job.

Every CHECK_INTERVAL seconds (env-configurable, default 3600 = 1 hour):
  1. Load every active product from the DB.
  2. For each one, scrape Digikala (if it has a digikala_url) and Torob
     (if it has a torob_url) — in a small thread pool, since these are
     network-bound calls.
  3. Upsert the "current price" row per (product, store).
  4. If the price changed since last time, append a PriceHistory row and,
     if the change crosses the alert threshold, fire a Telegram notification.

A failure scraping ONE product (network error, site change, anything) is
caught and logged; it never stops the rest of the cycle or crashes the
scheduler thread.
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from backend.app.config import get_settings
from backend.app.database import session_scope
from backend.app import models
from scraper.digikala import scrape_digikala
from scraper.torob import scrape_torob
from scraper.notifier import notify_price_change, should_notify

logger = logging.getLogger("price_monitor.scheduler")


def _get_or_create_store(db, name: str, kind: str) -> models.Store:
    store = db.query(models.Store).filter(models.Store.name == name).first()
    if store:
        return store
    store = models.Store(name=name, kind=kind)
    db.add(store)
    db.flush()
    return store


def _upsert_price(db, product: models.Product, store: models.Store, new_price, is_available: bool, url: str | None, threshold: float):
    """
    Update (or create) the current-price row for (product, store). If the
    price changed, log it to PriceHistory and possibly notify via Telegram.
    """
    existing = (
        db.query(models.Price)
        .filter(models.Price.product_id == product.id, models.Price.store_id == store.id)
        .first()
    )
    old_price = existing.price if existing else None

    if existing:
        existing.price = new_price
        existing.is_available = is_available
        existing.url = url or existing.url
        from datetime import datetime
        existing.checked_at = datetime.utcnow()
    else:
        existing = models.Price(
            product_id=product.id, store_id=store.id,
            price=new_price, is_available=is_available, url=url,
        )
        db.add(existing)

    price_actually_changed = (
        new_price is not None and old_price is not None and new_price != old_price
    )
    newly_found_price = new_price is not None and old_price is None

    if price_actually_changed or newly_found_price:
        change_percent = None
        if old_price:
            change_percent = round((new_price - old_price) / old_price * 100, 2)

        db.add(models.PriceHistory(
            product_id=product.id,
            store_id=store.id,
            old_price=old_price,
            new_price=new_price,
            change_percent=change_percent,
        ))

        if change_percent is not None and should_notify(change_percent, threshold):
            notify_price_change(product.name, store.name, old_price, new_price, change_percent)


def _check_one_product(product_id: int):
    """Runs in a worker thread: scrape both sources for one product, each with its own DB session."""
    settings = get_settings()
    with session_scope() as db:
        product = db.query(models.Product).filter(models.Product.id == product_id).first()
        if not product or not product.is_active:
            return

        if product.digikala_url:
            try:
                result = scrape_digikala(product.digikala_url)
                store = _get_or_create_store(db, "digikala", "digikala")
                _upsert_price(
                    db, product, store, result.price, result.is_available,
                    result.url, settings.TELEGRAM_NOTIFY_THRESHOLD_PERCENT,
                )
                if result.error:
                    logger.info("Digikala scrape issue for product %s: %s", product.id, result.error)
            except Exception:
                logger.exception("Unhandled error scraping Digikala for product %s", product.id)

        if product.torob_url:
            try:
                result = scrape_torob(product.torob_url)
                offers = result.offers or (
                    [] if result.price is None else
                    [type("Tmp", (), {"store_name": "torob", "price": result.price, "url": result.url})()]
                )
                for offer in offers[:5]:
                    store = _get_or_create_store(db, f"torob:{offer.store_name}", "torob_seller")
                    _upsert_price(
                        db, product, store, offer.price, True,
                        getattr(offer, "url", None) or result.url,
                        settings.TELEGRAM_NOTIFY_THRESHOLD_PERCENT,
                    )
                if result.error:
                    logger.info("Torob scrape issue for product %s: %s", product.id, result.error)
            except Exception:
                logger.exception("Unhandled error scraping Torob for product %s", product.id)


def run_check_cycle():
    settings = get_settings()
    logger.info("Starting price-check cycle...")
    with session_scope() as db:
        product_ids = [
            p.id for p in db.query(models.Product.id).filter(models.Product.is_active.is_(True)).all()
        ]

    if not product_ids:
        logger.info("No active products to check.")
        return

    ok, failed = 0, 0
    with ThreadPoolExecutor(max_workers=max(1, settings.SCRAPER_CONCURRENCY)) as pool:
        futures = {pool.submit(_check_one_product, pid): pid for pid in product_ids}
        for future in as_completed(futures):
            pid = futures[future]
            try:
                future.result()
                ok += 1
            except Exception:
                failed += 1
                logger.exception("Product %s failed the check cycle entirely", pid)

    logger.info("Price-check cycle finished: %s ok, %s failed, %s total.", ok, failed, len(product_ids))


def start_scheduler() -> BackgroundScheduler:
    settings = get_settings()
    scheduler = BackgroundScheduler(timezone="Asia/Tehran")
    scheduler.add_job(
        run_check_cycle,
        trigger=IntervalTrigger(seconds=settings.CHECK_INTERVAL),
        id="price_check_cycle",
        next_run_time=None,  # scheduled below, kicked off after a short delay
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()

    # Kick off a first run shortly after startup (not instantly, so the app
    # finishes booting first), without blocking the API from serving requests.
    import datetime as _dt
    scheduler.modify_job(
        "price_check_cycle",
        next_run_time=_dt.datetime.now() + _dt.timedelta(seconds=15),
    )
    return scheduler


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_check_cycle()
