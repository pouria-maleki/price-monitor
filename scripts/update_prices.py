"""
سیستم مانیتورینگ استراتژیک قیمت رویال‌دیجی با ۳ فروشنده اول ترب و دیجی‌کالا
مطابق با فایل: sources/links_torob_and_Digikala.xlsx و sources/royaldigi-products-urls.csv

قوانین استراتژی قیمت‌گذاری رویال‌دیجی:
۱. ترب ۳ قیمت اول و ارزان‌ترین فروشندگان را در صدر نتایج نشان می‌دهد.
۲. رویال‌دیجی باید حتماً در بین ۳ فروشنده اول ترب باشد (رتبه ۱ یا ۲ یا ۳).
۳. اگر قیمت رویال‌دیجی از هر ۳ فروشنده اول بیشتر باشد: اخطار خروج از رقابت (قرمز).
۴. اگر قیمت رویال‌دیجی از رتبه ۱ ترب ارزان‌تر باشد: اخطار قیمت‌شکنی بیهوده و سود از دست رفته (هشدار).
۵. در صورت ناموجود بودن هر کالا، کلمه صریح «ناموجود» درج می‌شود.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import random
import re
import sys
import time

# Ensure repository root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from scraper.digikala import scrape_digikala
from scraper.torob import scrape_torob
from scraper.royaldigi import scrape_royaldigi
from scraper.base import normalize_price
from scraper.notifier import notify_price_change

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("price_monitor.updater")

_FA_MONTHS = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
]


def gregorian_to_jalali(gy: int, gm: int, gd: int):
    """Accurate Gregorian to Jalali date converter."""
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = gy if gm > 2 else gy - 1
    days = 355666 + (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + ((gy2 + 399) // 400) + gd + g_d_m[gm - 1]
    jy = -1595 + (33 * (days // 12053))
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + (days // 31)
        jd = 1 + (days % 31)
    else:
        jm = 7 + ((days - 186) // 30)
        jd = 1 + ((days - 186) % 30)
    return jy, jm, jd


def get_persian_now_str() -> str:
    now = datetime.now()
    jy, jm, jd = gregorian_to_jalali(now.year, now.month, now.day)
    return f"{jd} {_FA_MONTHS[jm - 1]} {jy} - {now.strftime('%H:%M')}"


def load_csv_urls(csv_path: str | Path) -> dict[str, str]:
    """Load product name -> URL mapping from royaldigi CSV."""
    mapping = {}
    p = Path(csv_path)
    if not p.exists():
        return mapping
    try:
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) >= 2 and row[0].strip() and row[1].strip():
                    mapping[row[0].strip()] = row[1].strip()
    except Exception as e:
        logger.warning("Could not read CSV URLs: %s", e)
    return mapping


def evaluate_torob_top3_status(
    royal_p: int | None,
    t1: int | None,
    t2: int | None,
    t3: int | None,
) -> dict:
    """
    Evaluates whether RoyalDigi's price is within the top 3 Torob sellers.
    """
    torob_prices = [p for p in (t1, t2, t3) if isinstance(p, (int, float)) and p > 0]
    
    if not royal_p:
        return {
            "status_code": "no_royal",
            "alert_level": "muted",
            "badge_text": "ناموجود در رویال",
            "is_alert": False,
            "diff_from_target": None,
            "rank_label": "ناموجود در رویال",
            "explanation": "قیمتی برای این کالا در سایت رویال‌دیجی تعریف نشده است.",
        }

    if not torob_prices:
        return {
            "status_code": "no_torob",
            "alert_level": "muted",
            "badge_text": "ناموجود در ترب",
            "is_alert": False,
            "diff_from_target": None,
            "rank_label": "ناموجود در ترب",
            "explanation": "این محصول در ۳ فروشگاه اول ترب موجود نیست.",
        }

    torob_prices.sort()
    t_min = torob_prices[0]
    t_max = torob_prices[-1]

    # Case 1: Royal is higher than all top 3 sellers (Out of competition!)
    if royal_p > t_max:
        diff = royal_p - t_max
        diff_pct = round((diff / t_max) * 100, 1)
        return {
            "status_code": "higher_than_top_3",
            "alert_level": "danger", # Red Alert
            "badge_text": "❌ اخطار: گران‌تر از ۳ رتبه اول",
            "is_alert": True,
            "diff_from_target": diff,
            "rank_label": f"+{diff:,} ت از رتبه ۳ ترب (+{diff_pct}%)",
            "explanation": f"قیمت رویال {diff:,} تومان از رتبه ۳ ترب بیشتر است و در ۳ نتیجه اول دیده نمی‌شوید.",
        }

    # Case 2: Royal is lower than seller 1 (Leaving money on the table!)
    elif royal_p < t_min:
        diff = t_min - royal_p
        diff_pct = round((diff / t_min) * 100, 1)
        return {
            "status_code": "lower_than_top_1",
            "alert_level": "warning", # Warning (Lost profit)
            "badge_text": "⚠️ اخطار: ارزان‌تر از رتبه ۱ (سود سوخته)",
            "is_alert": True,
            "diff_from_target": -diff,
            "rank_label": f"-{diff:,} ت از کف ترب (-{diff_pct}%)",
            "explanation": f"قیمت رویال {diff:,} تومان از کف ترب ارزان‌تر است (کاهش بی‌دلیل سود).",
        }

    # Case 3: Royal is WITHIN the top 3 (Target achieved!)
    else:
        if royal_p <= torob_prices[0]:
            rank = "رتبه ۱ ترب (کف قیمت)"
        elif len(torob_prices) > 1 and royal_p <= torob_prices[1]:
            rank = "رتبه ۲ ترب (ایده‌آل)"
        else:
            rank = "رتبه ۳ ترب (مجاز)"

        return {
            "status_code": "in_top_3",
            "alert_level": "success", # Green
            "badge_text": f"✓ {rank}",
            "is_alert": False,
            "diff_from_target": 0,
            "rank_label": rank,
            "explanation": f"قیمت رویال‌دیجی بین ۳ فروشنده اول ترب قرار دارد ({rank}).",
        }


def parse_excel_products(excel_path: str | Path, csv_map: dict[str, str] | None = None) -> list[dict]:
    """Parse products from links_torob_and_Digikala.xlsx (sheet: Royal_Selected)."""
    try:
        import openpyxl
        wb = openpyxl.load_workbook(str(excel_path), data_only=True)
        ws = wb["Royal_Selected"] if "Royal_Selected" in wb.sheetnames else wb.active
        rows = list(ws.iter_rows(values_only=True))
    except Exception as e:
        logger.error("Failed to load Excel with openpyxl: %s", e)
        raise

    if csv_map is None:
        csv_map = {}

    products = []
    for idx, r in enumerate(rows[1:], 1):
        if not r or len(r) < 3 or not r[2]:
            continue
        p_name = str(r[2]).strip()
        woo_id = r[1]
        center_id = r[0]
        raw_qty = r[4] or 0
        quantity = int(raw_qty) if isinstance(raw_qty, (int, float)) else 0
        item_type = str(r[6] or "").strip()
        is_new = item_type.lower() == "new"

        final_price = r[12] if isinstance(r[12], (int, float)) and r[12] > 0 else None
        suggested_price = r[13] if isinstance(r[13], (int, float)) and r[13] > 0 else None

        # Torob 1, 2, 3 columns
        t1 = r[14] if isinstance(r[14], (int, float)) and r[14] > 0 else None
        t2 = r[15] if isinstance(r[15], (int, float)) and r[15] > 0 else None
        t3 = r[16] if isinstance(r[16], (int, float)) and r[16] > 0 else None
        torob_prices = [p for p in (t1, t2, t3) if p]
        torob_initial_price = min(torob_prices) if torob_prices else None

        dk_initial_price = r[17] if isinstance(r[17], (int, float)) and r[17] > 0 else None

        # Torob link MUST be from main link (col 21), NOT stock link (col 22)
        torob_url = r[21] if len(r) > 21 and r[21] else None
        digikala_url = r[23] if len(r) > 23 and r[23] else None

        royaldigi_url = None
        if p_name in csv_map:
            royaldigi_url = csv_map[p_name]
        elif woo_id:
            royaldigi_url = f"https://royaldigi.ir/?p={woo_id}"

        # Evaluate Top 3 position
        top3_eval = evaluate_torob_top3_status(final_price, t1, t2, t3)

        market_comps = []
        if torob_initial_price:
            market_comps.append(torob_initial_price)
        if dk_initial_price:
            market_comps.append(dk_initial_price)
        market_avg = round(sum(market_comps) / len(market_comps)) if market_comps else None

        item_val_royal = (quantity * final_price) if (final_price and quantity) else 0
        item_val_market = (quantity * market_avg) if (market_avg and quantity) else item_val_royal

        prod = {
            "id": f"royal_{center_id or idx}",
            "file_order": idx,
            "center_id": center_id,
            "woo_id": woo_id,
            "name": p_name,
            "item_type": "New" if is_new else "Stock",
            "item_type_fa": "کالای نو" if is_new else "کالای استوک",
            "quantity": quantity,
            "grade": r[7] or "",
            "warranty": r[8] or "",
            "status_text": r[9] or "",
            "royaldigi_price": final_price,
            "initial_royaldigi_price": final_price,
            "current_royaldigi_price": final_price,
            "suggested_price": suggested_price,
            "torob_1": t1,
            "torob_2": t2,
            "torob_3": t3,
            "torob_price": torob_initial_price,
            "initial_torob_price": torob_initial_price,
            "current_torob_price": torob_initial_price,
            "digikala_price": dk_initial_price,
            "initial_digikala_price": dk_initial_price,
            "current_digikala_price": dk_initial_price,
            "market_avg_price": market_avg,
            "top3_status": top3_eval["status_code"],
            "top3_badge": top3_eval["badge_text"],
            "top3_rank_label": top3_eval["rank_label"],
            "top3_explanation": top3_eval["explanation"],
            "is_alert": top3_eval["is_alert"],
            "alert_level": top3_eval["alert_level"],
            "diff_from_target": top3_eval["diff_from_target"],
            "royaldigi_url": royaldigi_url,
            "torob_url": torob_url,
            "digikala_url": digikala_url,
            "notes": r[24] if len(r) > 24 and r[24] else "",
            "item_val_royal": item_val_royal,
            "item_val_market": item_val_market,
            "sparkline": [
                final_price or market_avg or 1000000,
                t1 or market_avg or final_price or 1000000,
                t2 or market_avg or final_price or 1000000,
                t3 or market_avg or final_price or 1000000,
                final_price or market_avg or 1000000,
            ],
            "last_checked": datetime.now(timezone.utc).isoformat(),
        }
        products.append(prod)

    return products


def scrape_product_live(product: dict, previous_item: dict | None = None, scrape_torob_flag: bool = True) -> dict:
    """Scrapes live prices for RoyalDigi, Digikala, and Torob."""
    item = dict(product)
    now_iso = datetime.now(timezone.utc).isoformat()
    item["last_checked"] = now_iso

    # 1. Scrape RoyalDigi live
    if item.get("woo_id") or item.get("royaldigi_url"):
        try:
            rd_res = scrape_royaldigi(item.get("woo_id") or item.get("royaldigi_url"))
            if rd_res and rd_res.price is not None:
                item["current_royaldigi_price"] = rd_res.price
                item["royaldigi_price"] = rd_res.price
                if rd_res.url and not item.get("royaldigi_url"):
                    item["royaldigi_url"] = rd_res.url
        except Exception as e:
            logger.debug("RoyalDigi error for %s: %s", item["name"], e)

    # 2. Scrape Digikala live
    if item.get("digikala_url"):
        try:
            dk_res = scrape_digikala(item["digikala_url"])
            if dk_res and dk_res.price is not None:
                item["current_digikala_price"] = dk_res.price
                item["digikala_price"] = dk_res.price
                if dk_res.offers:
                    item["digikala_seller"] = dk_res.offers[0].store_name
        except Exception as e:
            logger.debug("Digikala error for %s: %s", item["name"], e)

    # 3. Scrape Torob live (from main link)
    if scrape_torob_flag and item.get("torob_url"):
        try:
            tr_res = scrape_torob(item["torob_url"])
            if tr_res and tr_res.offers:
                offers = sorted([o for o in tr_res.offers if o.price], key=lambda o: o.price)
                if len(offers) >= 1:
                    item["torob_1"] = offers[0].price
                    item["current_torob_price"] = offers[0].price
                    item["torob_price"] = offers[0].price
                if len(offers) >= 2:
                    item["torob_2"] = offers[1].price
                if len(offers) >= 3:
                    item["torob_3"] = offers[2].price
            elif tr_res and tr_res.price is not None:
                item["torob_1"] = tr_res.price
                item["current_torob_price"] = tr_res.price
                item["torob_price"] = tr_res.price
        except Exception as e:
            logger.debug("Torob error for %s: %s", item["name"], e)

    # Re-evaluate Top 3 Position
    royal_p = item.get("current_royaldigi_price") or item.get("royaldigi_price")
    t1 = item.get("torob_1")
    t2 = item.get("torob_2")
    t3 = item.get("torob_3")

    top3_eval = evaluate_torob_top3_status(royal_p, t1, t2, t3)
    item["top3_status"] = top3_eval["status_code"]
    item["top3_badge"] = top3_eval["badge_text"]
    item["top3_rank_label"] = top3_eval["rank_label"]
    item["top3_explanation"] = top3_eval["explanation"]
    item["is_alert"] = top3_eval["is_alert"]
    item["alert_level"] = top3_eval["alert_level"]
    item["diff_from_target"] = top3_eval["diff_from_target"]

    # Market Average
    market_comps = [p for p in (t1, item.get("current_digikala_price") or item.get("digikala_price")) if p]
    market_avg = round(sum(market_comps) / len(market_comps)) if market_comps else None
    item["market_avg_price"] = market_avg

    # Valuation
    qty = item.get("quantity") or 0
    item["item_val_royal"] = (qty * royal_p) if (royal_p and qty) else 0
    item["item_val_market"] = (qty * market_avg) if (market_avg and qty) else item["item_val_royal"]

    # Sparkline
    prev_spark = previous_item.get("sparkline") if previous_item else None
    if prev_spark and len(prev_spark) >= 4:
        item["sparkline"] = prev_spark[1:] + [royal_p or market_avg or 1000000]
    else:
        item["sparkline"] = [
            royal_p or market_avg or 1000000,
            t1 or market_avg or royal_p or 1000000,
            t2 or market_avg or royal_p or 1000000,
            t3 or market_avg or royal_p or 1000000,
            royal_p or market_avg or 1000000,
        ]

    return item


def export_updated_excel(items: list[dict], output_path: str | Path):
    """Exports styled Persian Excel report with 3 Torob columns and alert fills."""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        logger.warning("openpyxl not installed; cannot export Excel.")
        return

    wb = Workbook()
    ws = wb.active
    ws.title = "مانیتورینگ ۳ فروشنده ترب"
    ws.views.sheetView[0].rightToLeft = True

    headers = [
        "ردیف", "کد کالا", "نوع کالا", "نام محصول", "موجودی انبار",
        "قیمت رویال‌دیجی (تومان)", "ترب ۱ (فروشنده اول)", "ترب ۲ (فروشنده دوم)", "ترب ۳ (فروشنده سوم)",
        "قیمت دیجی‌کالا (تومان)", "وضعیت در ۳ رتبه اول ترب", "اختلاف با محدوده مجاز",
        "ارزش کل موجودی رویال (تومان)", "لینک رویال‌دیجی", "لینک اصلی ترب", "لینک دیجی‌کالا"
    ]

    header_font = Font(name="Tahoma", size=10, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
    regular_font = Font(name="Tahoma", size=9)
    center_align = Alignment(horizontal="center", vertical="center")
    right_align = Alignment(horizontal="right", vertical="center")
    
    red_alert_fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid") # Red for higher than top 3
    orange_alert_fill = PatternFill(start_color="FFEDD5", end_color="FFEDD5", fill_type="solid") # Orange for lower than top 1
    green_top3_fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid") # Green for in top 3
    new_tag_fill = PatternFill(start_color="E0F2FE", end_color="E0F2FE", fill_type="solid")
    stock_tag_fill = PatternFill(start_color="F3E8FF", end_color="F3E8FF", fill_type="solid")

    ws.append(headers)
    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align

    for row_idx, item in enumerate(items, 2):
        row_vals = [
            item.get("file_order"),
            item.get("woo_id") or item.get("center_id") or "",
            item.get("item_type_fa"),
            item.get("name"),
            item.get("quantity") or 0,
            item.get("royaldigi_price") if item.get("royaldigi_price") else "ناموجود",
            item.get("torob_1") if item.get("torob_1") else "ناموجود",
            item.get("torob_2") if item.get("torob_2") else "ناموجود",
            item.get("torob_3") if item.get("torob_3") else "ناموجود",
            item.get("digikala_price") if item.get("digikala_price") else "ناموجود",
            item.get("top3_badge") or "ناموجود",
            item.get("top3_rank_label") or "—",
            item.get("item_val_royal") or 0,
            item.get("royaldigi_url") or "",
            item.get("torob_url") or "",
            item.get("digikala_url") or "",
        ]
        ws.append(row_vals)

        for c_idx in range(1, len(headers) + 1):
            c = ws.cell(row=row_idx, column=c_idx)
            c.font = regular_font
            c.alignment = right_align if c_idx == 4 else center_align

            # Number format for prices
            if c_idx in (6, 7, 8, 9, 10, 13) and isinstance(c.value, (int, float)):
                c.number_format = "#,##0"

            # Tag colors (New vs Stock)
            if c_idx == 3:
                if item.get("item_type") == "New":
                    c.fill = new_tag_fill
                else:
                    c.fill = stock_tag_fill

            # Royal price highlighting
            if c_idx == 6:
                if item.get("top3_status") == "higher_than_top_3":
                    c.fill = red_alert_fill
                elif item.get("top3_status") == "lower_than_top_1":
                    c.fill = orange_alert_fill
                elif item.get("top3_status") == "in_top_3":
                    c.fill = green_top3_fill

            # Status column
            if c_idx == 11:
                if item.get("top3_status") == "higher_than_top_3":
                    c.fill = red_alert_fill
                elif item.get("top3_status") == "lower_than_top_1":
                    c.fill = orange_alert_fill
                elif item.get("top3_status") == "in_top_3":
                    c.fill = green_top3_fill

    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, 11), 50)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(output_path))
    logger.info("Exported updated Excel report to %s", output_path)


def run_update(
    excel_path: str | Path,
    csv_path: str | Path,
    output_dirs: list[Path],
    concurrency: int = 1,
    delay_min: float = 2.5,
    delay_max: float = 4.5,
    limit: int | None = None,
    only_alerts: bool = False,
    dry_run: bool = False,
):
    excel_path = Path(excel_path)
    csv_path = Path(csv_path)
    logger.info("Reading CSV URLs from %s ...", csv_path)
    csv_map = load_csv_urls(csv_path)

    logger.info("Reading Excel products from %s ...", excel_path)
    products = parse_excel_products(excel_path, csv_map=csv_map)
    logger.info("Parsed %d products total.", len(products))

    # Load previous data if exists
    primary_output = output_dirs[0] / "products_data.json"
    previous_map = {}
    if primary_output.exists():
        try:
            with open(primary_output, encoding="utf-8") as f:
                prev_json = json.load(f)
                previous_map = {x["id"]: x for x in prev_json.get("items", [])}
        except Exception as e:
            logger.warning("Could not read previous products_data.json: %s", e)

    # Filter only alerts if requested
    items_to_scrape = products
    if only_alerts:
        items_to_scrape = [p for p in products if p.get("is_alert")]
        logger.info("Filtered to %d alert products for scraping.", len(items_to_scrape))

    if limit is not None:
        items_to_scrape = items_to_scrape[:limit]
        logger.info("Limited run to first %d products.", len(items_to_scrape))

    updated_dict = {}
    start_time = time.time()
    logger.info("Starting gentle extraction with delay=%.1f-%.1fs ...", delay_min, delay_max)

    for idx, p in enumerate(items_to_scrape, 1):
        prev_p = previous_map.get(p["id"])
        try:
            res = scrape_product_live(p, prev_p)
            updated_dict[res["id"]] = res
            logger.info(
                "[%d/%d] %s: Royal=%s, Torob=[%s, %s, %s], DK=%s -> %s",
                idx, len(items_to_scrape), res["name"][:25],
                f"{res.get('royaldigi_price'):,}" if res.get('royaldigi_price') else "ناموجود",
                f"{res.get('torob_1'):,}" if res.get('torob_1') else "ناموجود",
                f"{res.get('torob_2'):,}" if res.get('torob_2') else "ناموجود",
                f"{res.get('torob_3'):,}" if res.get('torob_3') else "ناموجود",
                f"{res.get('digikala_price'):,}" if res.get('digikala_price') else "ناموجود",
                res.get("top3_badge")
            )
        except Exception as exc:
            logger.error("Error scraping %s: %s", p["name"], exc)
            updated_dict[p["id"]] = p

        if idx < len(items_to_scrape) and (delay_min > 0 or delay_max > 0):
            jitter = random.uniform(delay_min, max(delay_min, delay_max))
            time.sleep(jitter)

    # Recombine all products in original file order
    final_items = []
    for p in products:
        item_to_add = dict(p)
        if p["id"] in updated_dict:
            item_to_add = updated_dict[p["id"]]
        elif p["id"] in previous_map:
            prev = previous_map[p["id"]]
            for k in ("current_royaldigi_price", "current_digikala_price", "current_torob_price", "sparkline", "last_checked", "digikala_seller"):
                if prev.get(k) is not None:
                    item_to_add[k] = prev[k]
            royal_p = item_to_add.get("current_royaldigi_price") or item_to_add.get("royaldigi_price")
            t1 = item_to_add.get("torob_1")
            t2 = item_to_add.get("torob_2")
            t3 = item_to_add.get("torob_3")
            top3_eval = evaluate_torob_top3_status(royal_p, t1, t2, t3)
            item_to_add["top3_status"] = top3_eval["status_code"]
            item_to_add["top3_badge"] = top3_eval["badge_text"]
            item_to_add["top3_rank_label"] = top3_eval["rank_label"]
            item_to_add["top3_explanation"] = top3_eval["explanation"]
            item_to_add["is_alert"] = top3_eval["is_alert"]
            item_to_add["alert_level"] = top3_eval["alert_level"]
            item_to_add["diff_from_target"] = top3_eval["diff_from_target"]
        final_items.append(item_to_add)

    # Guarantee exact file order: 1 to 166
    final_items.sort(key=lambda x: x.get("file_order", 0))

    duration = round(time.time() - start_time, 1)
    logger.info("Finished in %s seconds.", duration)

    # Statistics
    total_products = len(final_items)
    in_top_3_count = sum(1 for x in final_items if x.get("top3_status") == "in_top_3")
    higher_count = sum(1 for x in final_items if x.get("top3_status") == "higher_than_top_3")
    lower_count = sum(1 for x in final_items if x.get("top3_status") == "lower_than_top_1")
    alerts_total = higher_count + lower_count
    new_count = sum(1 for x in final_items if x.get("item_type") == "New")
    stock_count = sum(1 for x in final_items if x.get("item_type") == "Stock")
    total_quantity = sum(x.get("quantity") or 0 for x in final_items)
    total_val_royal = sum(x.get("item_val_royal") or 0 for x in final_items)
    total_val_market = sum(x.get("item_val_market") or 0 for x in final_items)

    payload = {
        "metadata": {
            "last_updated_iso": datetime.now(timezone.utc).isoformat(),
            "last_updated_fa": get_persian_now_str(),
            "schedule_info": "آپدیت خودکار روزانه ساعت ۱۰:۰۰ صبح (تهران)",
            "total_products": total_products,
            "in_top_3_count": in_top_3_count,
            "higher_than_top_3_count": higher_count,
            "lower_than_top_1_count": lower_count,
            "alerts_total": alerts_total,
            "new_count": new_count,
            "stock_count": stock_count,
            "total_inventory_quantity": total_quantity,
            "total_inventory_royal_value": total_val_royal,
            "total_inventory_market_value": total_val_market,
            "duration_seconds": duration,
        },
        "items": final_items,
    }

    if dry_run:
        logger.info("Dry run complete. No files written.")
        return payload

    # Write JSON files
    for out_dir in output_dirs:
        out_dir.mkdir(parents=True, exist_ok=True)
        json_path = out_dir / "products_data.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        logger.info("Saved data JSON to %s", json_path)

    # Write Excel reports
    excel_report_path = BASE_DIR / "گزارش_انبار_قیمت_به_روز.xlsx"
    export_updated_excel(final_items, excel_report_path)
    for out_dir in output_dirs:
        excel_copy = out_dir / "گزارش_انبار_قیمت_به_روز.xlsx"
        try:
            import shutil
            shutil.copy2(excel_report_path, excel_copy)
            logger.info("Copied Excel report to %s", excel_copy)
        except Exception as e:
            logger.warning("Could not copy Excel report: %s", e)

    # Automatically update dashboard.html
    try:
        from scripts.build_dashboard_html import generate_dashboard
        generate_dashboard()
        logger.info("Automatically refreshed dashboard.html")
    except Exception as e:
        logger.warning("Could not auto-generate dashboard.html: %s", e)

    return payload


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="RoyalDigi vs Torob Top 3 Monitor")
    parser.add_argument("--excel", default=str(BASE_DIR / "sources" / "links_torob_and_Digikala.xlsx"), help="Path to Excel")
    parser.add_argument("--csv", default=str(BASE_DIR / "sources" / "royaldigi-products-urls.csv"), help="Path to CSV")
    parser.add_argument("--concurrency", type=int, default=1, help="Thread count (1 for gentle sequential)")
    parser.add_argument("--delay-min", type=float, default=2.5, help="Min delay between requests")
    parser.add_argument("--delay-max", type=float, default=4.5, help="Max delay between requests")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of items for test")
    parser.add_argument("--only-alerts", action="store_true", help="Only scrape products with alerts")
    parser.add_argument("--dry-run", action="store_true", help="Do not write files")
    args = parser.parse_args()

    output_dirs = [
        BASE_DIR / "frontend" / "public" / "data",
        BASE_DIR / "data",
    ]
    dist_data = BASE_DIR / "frontend" / "dist" / "data"
    if dist_data.parent.exists():
        output_dirs.append(dist_data)

    run_update(
        excel_path=args.excel,
        csv_path=args.csv,
        output_dirs=output_dirs,
        concurrency=args.concurrency,
        delay_min=args.delay_min,
        delay_max=args.delay_max,
        limit=args.limit,
        only_alerts=args.only_alerts,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
