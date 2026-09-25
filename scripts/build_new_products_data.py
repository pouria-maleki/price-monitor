import openpyxl
import json
import csv
from pathlib import Path
from datetime import datetime, timezone
import sys
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent

# 1. Load CSV URLs
csv_map = {}
csv_path = BASE_DIR / "sources" / "royaldigi-products-urls.csv"
if csv_path.exists():
    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if len(row) >= 2 and row[0].strip():
                csv_map[row[0].strip()] = row[1].strip()

# 2. Parse Excel
excel_path = BASE_DIR / "sources" / "links_torob_and_Digikala.xlsx"
wb = openpyxl.load_workbook(excel_path, data_only=True)
ws = wb['Royal_Selected']
rows = list(ws.iter_rows(values_only=True))
headers = rows[0]

items = []
for idx, r in enumerate(rows[1:], 1):
    name = r[2]
    if not name:
        continue
    name = str(name).strip()
    woo_id = r[1]
    center_id = r[0]
    raw_qty = r[4] or 0
    quantity = int(raw_qty) if isinstance(raw_qty, (int, float)) else 0
    item_type = str(r[6] or "").strip()
    is_new = item_type.lower() == 'new'
    grade = r[7] or ""
    warranty = r[8] or ""
    status_text = r[9] or ""
    
    # Prices
    final_price = r[12] if isinstance(r[12], (int, float)) and r[12] > 0 else None
    suggested_price = r[13] if isinstance(r[13], (int, float)) and r[13] > 0 else None
    
    # Torob prices from Excel
    t1 = r[14] if isinstance(r[14], (int, float)) and r[14] > 0 else None
    t2 = r[15] if isinstance(r[15], (int, float)) and r[15] > 0 else None
    t3 = r[16] if isinstance(r[16], (int, float)) and r[16] > 0 else None
    torob_prices = [p for p in (t1, t2, t3) if p]
    torob_price = min(torob_prices) if torob_prices else None
    
    # Digikala price from Excel
    dk_price = r[17] if isinstance(r[17], (int, float)) and r[17] > 0 else None
    
    # URLs - Requirement: Torob link MUST be from main link (r[21]), NOT stock link (r[22])
    torob_url = r[21] or None
    digikala_url = r[23] or None
    
    # RoyalDigi URL
    royaldigi_url = None
    if name in csv_map:
        royaldigi_url = csv_map[name]
    elif woo_id:
        royaldigi_url = f"https://royaldigi.ir/?p={woo_id}"

    # Market Average Calculation
    market_components = []
    if torob_price:
        market_components.append(torob_price)
    if dk_price:
        market_components.append(dk_price)
        
    market_avg = round(sum(market_components) / len(market_components)) if market_components else None
    
    # Discrepancy check: RoyalDigi vs Market Average
    diff = None
    diff_percent = None
    is_discrepant = False
    diff_status = "بدون قیمت مقایسه"
    
    if final_price and market_avg:
        diff = final_price - market_avg
        diff_percent = round((diff / market_avg) * 100, 1)
        if diff != 0:
            is_discrepant = True
            if diff > 0:
                diff_status = f"رویال {diff_percent:+}% گران‌تر"
            else:
                diff_status = f"رویال {diff_percent:+}% ارزان‌تر"
        else:
            diff_status = "هم‌قیمت بازار"
    elif final_price:
        diff_status = "فقط در رویال‌دیجی"
        
    # Valuation
    item_val_royal = (quantity * final_price) if (final_price and quantity) else 0
    item_val_market = (quantity * market_avg) if (market_avg and quantity) else item_val_royal
    
    item = {
        "id": f"royal_{center_id or idx}",
        "file_order": idx,
        "center_id": center_id,
        "woo_id": woo_id,
        "name": name,
        "item_type": "New" if is_new else "Stock",
        "item_type_fa": "کالای نو" if is_new else "کالای استوک",
        "quantity": quantity,
        "grade": grade,
        "warranty": warranty,
        "status_text": status_text,
        "royaldigi_price": final_price,
        "suggested_price": suggested_price,
        "torob_price": torob_price,
        "torob_offers": [{"seller": f"ترب {i+1}", "price": p} for i, p in enumerate(torob_prices)],
        "digikala_price": dk_price,
        "market_avg_price": market_avg,
        "diff_amount": diff,
        "diff_percent": diff_percent,
        "is_discrepant": is_discrepant,
        "diff_status": diff_status,
        "royaldigi_url": royaldigi_url,
        "torob_url": torob_url,
        "digikala_url": digikala_url,
        "notes": r[24] or "",
        "item_val_royal": item_val_royal,
        "item_val_market": item_val_market,
        "sparkline": [
            final_price or market_avg or 1000000,
            torob_price or market_avg or final_price or 1000000,
            market_avg or final_price or 1000000,
            dk_price or market_avg or final_price or 1000000,
            final_price or market_avg or 1000000
        ]
    }
    items.append(item)

print(f"Total items created: {len(items)}")
discrepant_count = sum(1 for x in items if x['is_discrepant'])
new_count = sum(1 for x in items if x['item_type'] == 'New')
stock_count = sum(1 for x in items if x['item_type'] == 'Stock')
total_qty = sum(x['quantity'] for x in items)
total_val_royal = sum(x['item_val_royal'] for x in items)
total_val_market = sum(x['item_val_market'] for x in items)

print(f"Discrepant items (Red column): {discrepant_count} / {len(items)}")
print(f"New items: {new_count}")
print(f"Stock items: {stock_count}")
print(f"Total warehouse units: {total_qty}")
print(f"Total RoyalDigi inventory valuation: {total_val_royal:,} Tomans")
print(f"Total Market inventory valuation: {total_val_market:,} Tomans")
