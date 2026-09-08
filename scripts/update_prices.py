"""
قیمت‌ها را از دیجی‌کالا و ترب برای تمامی محصولات موجود در فایل اکسل انبار
(گزارش انبارمون - لینک و قیمت.xlsx) استخراج، مقایسه و در فایل JSON ذخیره می‌کند.
این اسکریپت برای اجرا در GitHub Actions یا روی سیستم محلی طراحی شده است.
"""
from __future__ import annotations

import argparse
import concurrent.futures
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import re
import sys
import time
import zipfile
import xml.etree.ElementTree as ET

# Ensure repository root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from scraper.digikala import scrape_digikala
from scraper.torob import scrape_torob
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


def parse_excel_products(excel_path: str | Path) -> list[dict]:
    """Parse products from both sheets in the warehouse Excel file without external dependencies."""
    excel_path = Path(excel_path)
    if not excel_path.exists():
        raise FileNotFoundError(f"Excel file not found: {excel_path}")

    products = []
    with zipfile.ZipFile(excel_path) as z:
        # Load shared strings
        shared_strings = []
        if "xl/sharedStrings.xml" in z.namelist():
            tree = ET.fromstring(z.read("xl/sharedStrings.xml"))
            ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
            for si in tree.findall("m:si", ns):
                text_parts = [elem.text for elem in si.iter() if elem.tag.endswith("}t") and elem.text]
                shared_strings.append("".join(text_parts))

        # Find sheets
        wb_tree = ET.fromstring(z.read("xl/workbook.xml"))
        wb_rels_tree = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        rel_map = {}
        for rel in wb_rels_tree:
            rel_map[rel.attrib.get("Id")] = rel.attrib.get("Target")

        ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        sheets_info = []
        for s in wb_tree.findall("m:sheets/m:sheet", ns):
            s_name = s.attrib.get("name")
            r_id = s.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
            target = rel_map.get(r_id, "")
            if not target.startswith("xl/"):
                target = "xl/" + target.lstrip("/")
            sheets_info.append((s_name, target))

        category_map = {
            "محصولات نو": "new",
            "محصولات استوک": "stock",
        }

        for sheet_name, target_file in sheets_info:
            category = category_map.get(sheet_name)
            if not category:
                continue

            sheet_tree = ET.fromstring(z.read(target_file))
            for row in sheet_tree.findall(".//m:row", ns):
                r_num = int(row.attrib.get("r", 0))
                if r_num < 4:  # Header rows are 1-3, data starts at row 4
                    continue

                vals = {}
                for c in row.findall("m:c", ns):
                    col = "".join([ch for ch in c.attrib.get("r", "") if ch.isalpha()])
                    t = c.attrib.get("t")
                    v = c.find("m:v", ns)
                    val = v.text if v is not None else ""
                    if t == "s" and val.isdigit():
                        idx = int(val)
                        val = shared_strings[idx] if idx < len(shared_strings) else ""
                    vals[col] = val.strip()

                row_idx = vals.get("A", "")
                if not row_idx or not row_idx.isdigit():
                    continue

                item_id = f"{category}-{row_idx}"
                warehouse_title = vals.get("B") or ""
                quantity = int(vals.get("C")) if vals.get("C", "").isdigit() else None
                name = vals.get("D") or ""
                digikala_url = vals.get("E") if vals.get("E", "").startswith("http") else None
                digikala_price = normalize_price(vals.get("F"))
                torob_url = vals.get("G") if vals.get("G", "").startswith("http") else None
                torob_price = normalize_price(vals.get("H"))

                if not name:
                    continue

                products.append({
                    "id": item_id,
                    "row_index": int(row_idx),
                    "category": category,
                    "category_fa": "محصولات نو" if category == "new" else "محصولات استوک",
                    "warehouse_title": warehouse_title,
                    "name": name,
                    "quantity": quantity,
                    "digikala_url": digikala_url,
                    "initial_digikala_price": digikala_price,
                    "current_digikala_price": None,
                    "digikala_available": False,
                    "digikala_seller": None,
                    "digikala_offers": [],
                    "torob_url": torob_url,
                    "initial_torob_price": torob_price,
                    "current_torob_price": None,
                    "torob_available": False,
                    "torob_offers": [],
                    "best_current_price": None,
                    "price_change_amount": 0,
                    "price_change_percent": None,
                    "status": "pending",
                    "last_checked": None,
                })

    return products


def load_previous_data(json_path: Path) -> dict[str, dict]:
    """Load previously scraped data to keep track of history and avoid losing prices."""
    if not json_path.exists():
        return {}
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            items = data.get("items", [])
            return {item["id"]: item for item in items if "id" in item}
    except Exception as e:
        logger.warning("Could not load previous data from %s: %s", json_path, e)
        return {}


def scrape_product_live(product: dict, previous_item: dict | None = None, only_digikala: bool = False) -> dict:
    """Scrapes live prices for a single product and calculates changes."""
    item = dict(product)
    now_iso = datetime.now(timezone.utc).isoformat()
    item["last_checked"] = now_iso

    # Scrape Digikala
    if item.get("digikala_url"):
        try:
            dk_res = scrape_digikala(item["digikala_url"])
            if dk_res and dk_res.price is not None:
                item["current_digikala_price"] = dk_res.price
                item["digikala_available"] = dk_res.is_available
                item["digikala_offers"] = [
                    {"seller": o.store_name, "price": o.price}
                    for o in dk_res.offers
                ]
                if dk_res.offers:
                    item["digikala_seller"] = dk_res.offers[0].store_name
            elif previous_item and previous_item.get("current_digikala_price"):
                item["current_digikala_price"] = previous_item["current_digikala_price"]
                item["digikala_available"] = previous_item.get("digikala_available", False)
                item["digikala_seller"] = previous_item.get("digikala_seller")
                item["digikala_offers"] = previous_item.get("digikala_offers", [])
        except Exception as e:
            logger.warning("Digikala error for %s: %s", item["name"], e)

    # Scrape Torob
    if not only_digikala and item.get("torob_url"):
        try:
            torob_res = scrape_torob(item["torob_url"])
            if torob_res and torob_res.price is not None:
                item["current_torob_price"] = torob_res.price
                item["torob_available"] = torob_res.is_available
                item["torob_offers"] = [
                    {"seller": o.store_name, "price": o.price, "url": o.url}
                    for o in torob_res.offers
                ]
            elif previous_item and previous_item.get("current_torob_price"):
                item["current_torob_price"] = previous_item["current_torob_price"]
                item["torob_available"] = previous_item.get("torob_available", False)
                item["torob_offers"] = previous_item.get("torob_offers", [])
        except Exception as e:
            logger.warning("Torob error for %s: %s", item["name"], e)

    # Base price (previous price from Excel)
    base_price = item.get("initial_digikala_price") or item.get("initial_torob_price")
    item["base_price"] = base_price
    item["base_price_label"] = "قیمت قبلی انبار (اکسل)"

    # Determine best current price
    prices = [p for p in (item.get("current_digikala_price"), item.get("current_torob_price")) if p is not None]
    if prices:
        item["best_current_price"] = min(prices)
    elif previous_item and previous_item.get("best_current_price"):
        item["best_current_price"] = previous_item["best_current_price"]
    else:
        item["best_current_price"] = None

    # Calculate change against base Excel price (previous price)
    curr_ref = item.get("best_current_price") or item.get("current_digikala_price") or item.get("current_torob_price")

    if base_price and curr_ref:
        diff = curr_ref - base_price
        percent = (diff / base_price) * 100
        item["price_change_amount"] = diff
        item["price_change_percent"] = round(percent, 1)

        if percent > 0.5:
            item["status"] = "increased"
        elif percent < -0.5:
            item["status"] = "decreased"
        else:
            item["status"] = "unchanged"
    elif not item.get("digikala_available") and not item.get("torob_available") and curr_ref is None:
        item["status"] = "out_of_stock"
        item["price_change_amount"] = 0
        item["price_change_percent"] = None
    else:
        item["status"] = "unchanged"
        item["price_change_amount"] = 0
        item["price_change_percent"] = 0.0

    # Digikala specific diff
    if item.get("initial_digikala_price") and item.get("current_digikala_price"):
        dk_diff = item["current_digikala_price"] - item["initial_digikala_price"]
        item["digikala_change_percent"] = round((dk_diff / item["initial_digikala_price"]) * 100, 1)
    else:
        item["digikala_change_percent"] = None

    # Torob specific diff
    if item.get("initial_torob_price") and item.get("current_torob_price"):
        tr_diff = item["current_torob_price"] - item["initial_torob_price"]
        item["torob_change_percent"] = round((tr_diff / item["initial_torob_price"]) * 100, 1)
    else:
        item["torob_change_percent"] = None

    # Inventory Valuation calculations
    qty = item.get("quantity") or 0
    effective_curr = item.get("best_current_price") or base_price or 0
    item["inventory_value_base"] = (qty * base_price) if (base_price and qty) else 0
    item["inventory_value_current"] = (qty * effective_curr) if (effective_curr and qty) else 0
    item["inventory_profit_loss"] = item["inventory_value_current"] - item["inventory_value_base"]

    # History preservation
    prev_history = previous_item.get("history", []) if previous_item else []
    current_snapshot = {
        "timestamp": now_iso,
        "digikala_price": item.get("current_digikala_price"),
        "torob_price": item.get("current_torob_price"),
    }
    if not prev_history or (
        prev_history[-1].get("digikala_price") != current_snapshot["digikala_price"] or
        prev_history[-1].get("torob_price") != current_snapshot["torob_price"]
    ):
        item["history"] = prev_history + [current_snapshot]
    else:
        item["history"] = prev_history

    # Sparkline generation (smooth trajectory for mini chart)
    spark = []
    if prev_history and len(prev_history) >= 4:
        for h in prev_history[-7:]:
            p = h.get("digikala_price") or h.get("torob_price")
            if p:
                spark.append(p)
    if len(spark) < 4 and base_price:
        target_p = curr_ref or base_price
        import math
        for step in range(7):
            ratio = step / 6.0
            val = int(base_price + (target_p - base_price) * ratio)
            if 0 < step < 6 and target_p != base_price:
                val += int((target_p - base_price) * 0.08 * math.sin(step))
            spark.append(max(val, 0))
    elif not spark and curr_ref:
        spark = [curr_ref] * 7
    item["sparkline"] = spark

    return item


def export_to_excel(items: list[dict], output_path: str | Path):
    """Exports updated products into an organized Persian Excel file."""
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        logger.info("openpyxl not installed, skipping Excel export.")
        return

    wb = openpyxl.Workbook()
    # remove default sheet
    if wb.active:
        wb.remove(wb.active)

    headers = [
        "ردیف", "عنوان انبار", "تعداد در انبار", "نام دقیق ثبت‌شده در سایت",
        "قیمت قبلی انبار (تومان)", "قیمت روز دیجی‌کالا (تومان)", "تغییر دیجی‌کالا (%)", "فروشنده دیجی‌کالا", "وضعیت دیجی‌کالا",
        "قیمت قبلی ترب (تومان)", "قیمت روز ترب (تومان)", "تغییر ترب (%)",
        "ارزش کل موجودی به قیمت روز (تومان)", "سود / زیان کل انبار (تومان)",
        "لینک دیجی‌کالا", "لینک ترب"
    ]

    header_font = Font(name="Tahoma", size=10, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    regular_font = Font(name="Tahoma", size=9)
    center_align = Alignment(horizontal="center", vertical="center")
    right_align = Alignment(horizontal="right", vertical="center")
    
    green_fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
    red_fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")

    for cat_key, sheet_title in [("new", "محصولات نو"), ("stock", "محصولات استوک")]:
        ws = wb.create_sheet(title=sheet_title)
        ws.views.sheetView[0].rightToLeft = True
        ws.append(headers)
        for col_num in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_num)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_align

        cat_items = [x for x in items if x["category"] == cat_key]
        for row_idx, item in enumerate(cat_items, 2):
            dk_status_fa = "موجود" if item.get("digikala_available") else ("ناموجود" if item.get("digikala_url") else "فاقد لینک")
            row_vals = [
                item.get("row_index"),
                item.get("warehouse_title") or "",
                item.get("quantity") or "",
                item.get("name") or "",
                item.get("initial_digikala_price") or "",
                item.get("current_digikala_price") or "",
                f"{item.get('digikala_change_percent'):+.1f}%" if item.get("digikala_change_percent") is not None else "",
                item.get("digikala_seller") or "",
                dk_status_fa,
                item.get("initial_torob_price") or "",
                item.get("current_torob_price") or "",
                f"{item.get('torob_change_percent'):+.1f}%" if item.get("torob_change_percent") is not None else "",
                item.get("inventory_value_current") or 0,
                item.get("inventory_profit_loss") or 0,
                item.get("digikala_url") or "",
                item.get("torob_url") or "",
            ]
            ws.append(row_vals)
            for c_idx in range(1, len(headers) + 1):
                c = ws.cell(row=row_idx, column=c_idx)
                c.font = regular_font
                c.alignment = right_align if c_idx in (2, 4) else center_align
                if c_idx in (5, 6, 10, 11, 13, 14) and isinstance(c.value, (int, float)):
                    c.number_format = "#,##0"
                if c_idx == 7 and item.get("digikala_change_percent") is not None:
                    if item["digikala_change_percent"] > 0:
                        c.fill = red_fill
                    elif item["digikala_change_percent"] < 0:
                        c.fill = green_fill
                if c_idx == 12 and item.get("torob_change_percent") is not None:
                    if item["torob_change_percent"] > 0:
                        c.fill = red_fill
                    elif item["torob_change_percent"] < 0:
                        c.fill = green_fill
                if c_idx == 14 and isinstance(c.value, (int, float)):
                    if c.value > 0:
                        c.fill = green_fill
                    elif c.value < 0:
                        c.fill = red_fill

        # Auto-adjust column widths
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
    output_dirs: list[Path],
    concurrency: int = 1,
    delay_min: float = 2.5,
    delay_max: float = 5.0,
    limit: int | None = None,
    only_digikala: bool = False,
    dry_run: bool = False,
):
    excel_path = Path(excel_path)
    logger.info("Reading Excel products from %s ...", excel_path)
    products = parse_excel_products(excel_path)
    logger.info("Found %d products total in Excel.", len(products))

    if limit:
        products = products[:limit]
        logger.info("Limited run to first %d products.", len(products))

    primary_output = output_dirs[0] / "products_data.json"
    previous_data = load_previous_data(primary_output)

    updated_items = []
    logger.info("Starting live price extraction with concurrency=%d ...", concurrency)

    start_time = time.time()
    if concurrency > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            future_to_item = {
                executor.submit(scrape_product_live, p, previous_data.get(p["id"]), only_digikala): p
                for p in products
            }

            for idx, future in enumerate(concurrent.futures.as_completed(future_to_item), 1):
                orig_p = future_to_item[future]
                try:
                    res = future.result()
                    updated_items.append(res)
                    p_curr = res.get("current_digikala_price")
                    p_init = res.get("initial_digikala_price")
                    change_str = f"({res.get('price_change_percent')}%)" if res.get('price_change_percent') is not None else ""
                    logger.info(
                        "[%d/%d] %s: Live DK=%s (Excel was %s) %s",
                        idx, len(products), res["name"][:35],
                        f"{p_curr:,}" if p_curr else "None",
                        f"{p_init:,}" if p_init else "None",
                        change_str
                    )
                except Exception as exc:
                    logger.error("Error processing %s: %s", orig_p["name"], exc)
                    updated_items.append(orig_p)
    else:
        # Gentle sequential processing with human-like random jitter to prevent rate limiting & bot bans
        import random
        for idx, p in enumerate(products, 1):
            orig_p = p
            try:
                res = scrape_product_live(p, previous_data.get(p["id"]), only_digikala)
                updated_items.append(res)
                p_curr = res.get("current_digikala_price")
                p_tr = res.get("current_torob_price")
                p_init = res.get("initial_digikala_price") or res.get("initial_torob_price")
                change_str = f"({res.get('price_change_percent')}%)" if res.get('price_change_percent') is not None else ""
                logger.info(
                    "[%d/%d] %s: DK=%s, TR=%s (Base was %s) %s",
                    idx, len(products), res["name"][:30],
                    f"{p_curr:,}" if p_curr else "-",
                    f"{p_tr:,}" if p_tr else "-",
                    f"{p_init:,}" if p_init else "-",
                    change_str
                )
            except Exception as exc:
                logger.error("Error processing %s: %s", orig_p["name"], exc)
                updated_items.append(orig_p)

            if idx < len(products) and (delay_min > 0 or delay_max > 0):
                jitter = random.uniform(delay_min, max(delay_min, delay_max))
                time.sleep(jitter)

    duration = round(time.time() - start_time, 1)
    logger.info("Extraction finished in %s seconds.", duration)

    # Sort products by warehouse stock quantity (descending) as requested
    updated_items.sort(key=lambda x: (-(x.get("quantity") or 0), 0 if x["category"] == "new" else 1, x["row_index"]))

    increased_count = sum(1 for x in updated_items if x.get("status") == "increased")
    decreased_count = sum(1 for x in updated_items if x.get("status") == "decreased")
    unchanged_count = sum(1 for x in updated_items if x.get("status") == "unchanged")
    out_of_stock_count = sum(1 for x in updated_items if x.get("status") == "out_of_stock")
    new_count = sum(1 for x in updated_items if x.get("category") == "new")
    stock_count = sum(1 for x in updated_items if x.get("category") == "stock")

    total_quantity = sum(x.get("quantity") or 0 for x in updated_items)
    total_val_base = sum(x.get("inventory_value_base") or 0 for x in updated_items)
    total_val_current = sum(x.get("inventory_value_current") or 0 for x in updated_items)
    total_profit_loss = total_val_current - total_val_base
    total_pl_percent = round((total_profit_loss / total_val_base * 100), 1) if total_val_base else 0.0

    payload = {
        "metadata": {
            "last_updated_iso": datetime.now(timezone.utc).isoformat(),
            "last_updated_fa": get_persian_now_str(),
            "total_products": len(updated_items),
            "total_inventory_quantity": total_quantity,
            "total_inventory_base_value": total_val_base,
            "total_inventory_current_value": total_val_current,
            "total_inventory_profit_loss": total_profit_loss,
            "total_inventory_profit_loss_percent": total_pl_percent,
            "new_count": new_count,
            "stock_count": stock_count,
            "increased_count": increased_count,
            "decreased_count": decreased_count,
            "unchanged_count": unchanged_count,
            "out_of_stock_count": out_of_stock_count,
            "duration_seconds": duration,
        },
        "items": updated_items,
    }

    if dry_run:
        logger.info("Dry run complete. Not writing output files.")
        return payload

    for out_dir in output_dirs:
        out_dir.mkdir(parents=True, exist_ok=True)
        target_file = out_dir / "products_data.json"
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        logger.info("Saved data to %s (%d items)", target_file, len(updated_items))

    # Export updated Excel files
    excel_export_path = BASE_DIR / "گزارش_انبار_قیمت_به_روز.xlsx"
    export_to_excel(updated_items, excel_export_path)
    public_excel = BASE_DIR / "frontend" / "public" / "data" / "گزارش_انبار_قیمت_به_روز.xlsx"
    if public_excel.parent.exists():
        try:
            import shutil
            shutil.copyfile(excel_export_path, public_excel)
        except Exception as e:
            logger.warning("Could not copy Excel to public data: %s", e)

    if os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"):
        changed_items = [x for x in updated_items if x.get("status") in ("increased", "decreased")]
        if changed_items:
            logger.info("Sending Telegram alert for %d changed products...", len(changed_items))
            for ch in changed_items[:5]:
                old_p = ch.get("initial_digikala_price") or ch.get("initial_torob_price") or 0
                new_p = ch.get("current_digikala_price") or ch.get("current_torob_price") or 0
                notify_price_change(
                    product_name=ch["name"],
                    store_name="دیجی‌کالا / ترب",
                    old_price=old_p,
                    new_price=new_p,
                    change_percent=ch.get("price_change_percent") or 0.0,
                )

    return payload


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Price Monitor Updater")
    parser.add_argument("--excel", default=str(BASE_DIR / "گزارش انبارمون - لینک و قیمت.xlsx"), help="Path to Excel")
    parser.add_argument("--concurrency", type=int, default=1, help="Thread count (1 for gentle sequential with delay)")
    parser.add_argument("--delay-min", type=float, default=2.5, help="Minimum delay between requests in seconds")
    parser.add_argument("--delay-max", type=float, default=5.0, help="Maximum delay between requests in seconds")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of items for test")
    parser.add_argument("--only-digikala", action="store_true", help="Only scrape Digikala")
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
        output_dirs=output_dirs,
        concurrency=args.concurrency,
        delay_min=args.delay_min,
        delay_max=args.delay_max,
        limit=args.limit,
        only_digikala=args.only_digikala,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
