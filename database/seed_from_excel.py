"""
Import products from the warehouse Excel report ("گزارش انبارمون - لینک و
قیمت.xlsx") into the database.

Expected file layout (matches the file this project ships with, at
database/inventory.xlsx):

  Sheet "محصولات نو"    -> category = new
  Sheet "محصولات استوک" -> category = stock

  Each sheet has 2 title/spacer rows, then a header row with columns:
    ردیف | عنوان داده‌شده انبار | تعداد | اسم دقیق ثبت‌شده در سایت |
    لینک دیجی‌کالا | قیمت دیجی‌کالا (تومان) | لینک ترب | قیمت ترب [کف] (تومان)

Run:
    python -m database.seed_from_excel                       # uses EXCEL_IMPORT_PATH
    python -m database.seed_from_excel /path/to/file.xlsx     # explicit path

Safe to re-run: products are matched by (name, category) and updated in
place rather than duplicated.
"""
from __future__ import annotations

import logging
import math
import re
import sys

import pandas as pd

from backend.app.config import get_settings
from backend.app.database import session_scope, init_db
from backend.app import models

logger = logging.getLogger("price_monitor.seed")

SHEET_CATEGORY_MAP = {
    "محصولات نو": models.ProductCategory.NEW,
    "محصولات استوک": models.ProductCategory.STOCK,
}

HEADER_ROW_INDEX = 2  # 0-indexed row within the sheet that holds the real column headers

# Torob's minimum-price column is named slightly differently across the two
# sheets in the source file ("قیمت ترب کف  (تومان)" vs "قیمت ترب (تومان)"),
# so we match it loosely instead of by exact string.
_TOROB_PRICE_COL_RE = re.compile(r"قیمت\s*ترب")


def _clean_url(value) -> str | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    text = str(value).strip()
    if not text or not text.startswith("http"):
        return None
    return text


def _clean_price(value) -> int | None:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, (int, float)):
        return int(value) if value > 0 else None
    text = str(value).strip()
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else None


def _find_torob_price_column(columns) -> str | None:
    for col in columns:
        if isinstance(col, str) and _TOROB_PRICE_COL_RE.search(col):
            return col
    return None


def _import_sheet(db, path: str, sheet_name: str, category) -> int:
    df = pd.read_excel(path, sheet_name=sheet_name, header=HEADER_ROW_INDEX)
    torob_price_col = _find_torob_price_column(df.columns)

    count = 0
    for _, row in df.iterrows():
        row_num = row.get("ردیف")
        # skip spacer rows and the trailing "جمع تعداد" (total) row
        if row_num is None or (isinstance(row_num, float) and math.isnan(row_num)):
            continue
        try:
            int(row_num)
        except (TypeError, ValueError):
            continue

        name = row.get("اسم دقیق ثبت‌شده در سایت")
        if not isinstance(name, str) or not name.strip():
            continue
        name = name.strip()

        warehouse_title = row.get("عنوان داده‌شده انبار")
        warehouse_title = str(warehouse_title).strip() if isinstance(warehouse_title, str) else None

        quantity = row.get("تعداد")
        quantity = int(quantity) if isinstance(quantity, (int, float)) and not math.isnan(quantity) else None

        digikala_url = _clean_url(row.get("لینک دیجی‌کالا"))
        torob_url = _clean_url(row.get("لینک ترب"))
        digikala_price = _clean_price(row.get("قیمت دیجی‌کالا (تومان)"))
        torob_price = _clean_price(row.get(torob_price_col)) if torob_price_col else None

        product = (
            db.query(models.Product)
            .filter(models.Product.name == name, models.Product.category == category)
            .first()
        )
        if not product:
            product = models.Product(name=name, category=category)
            db.add(product)

        product.warehouse_title = warehouse_title
        product.quantity = quantity
        product.digikala_url = digikala_url
        product.torob_url = torob_url
        product.url = digikala_url or torob_url
        product.is_active = bool(digikala_url or torob_url)
        db.flush()  # get product.id

        # seed an initial price snapshot from the spreadsheet so the
        # dashboard has data to show before the first live scrape runs
        if digikala_url and digikala_price:
            store = db.query(models.Store).filter(models.Store.name == "digikala").first()
            if not store:
                store = models.Store(name="digikala", kind="digikala")
                db.add(store)
                db.flush()
            existing = (
                db.query(models.Price)
                .filter(models.Price.product_id == product.id, models.Price.store_id == store.id)
                .first()
            )
            if not existing:
                db.add(models.Price(
                    product_id=product.id, store_id=store.id,
                    price=digikala_price, is_available=True, url=digikala_url,
                ))

        if torob_url and torob_price:
            store = db.query(models.Store).filter(models.Store.name == "torob:از فایل اکسل").first()
            if not store:
                store = models.Store(name="torob:از فایل اکسل", kind="torob_seller")
                db.add(store)
                db.flush()
            existing = (
                db.query(models.Price)
                .filter(models.Price.product_id == product.id, models.Price.store_id == store.id)
                .first()
            )
            if not existing:
                db.add(models.Price(
                    product_id=product.id, store_id=store.id,
                    price=torob_price, is_available=True, url=torob_url,
                ))

        count += 1

    return count


def import_excel(path: str | None = None) -> int:
    settings = get_settings()
    path = path or settings.EXCEL_IMPORT_PATH
    init_db()

    total = 0
    with session_scope() as db:
        for sheet_name, category in SHEET_CATEGORY_MAP.items():
            try:
                n = _import_sheet(db, path, sheet_name, category)
                logger.info("Imported %s products from sheet '%s'.", n, sheet_name)
                total += n
            except ValueError as exc:
                logger.warning("Sheet '%s' not found or unreadable in %s: %s", sheet_name, path, exc)

    logger.info("Import finished: %s products total.", total)
    return total


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    file_path = sys.argv[1] if len(sys.argv) > 1 else None
    import_excel(file_path)
