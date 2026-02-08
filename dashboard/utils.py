# dashboard/utils.py

import os
import csv
from django.conf import settings
import numpy as np
from datetime import datetime
def clean_price(value):
    """
    Convert price to nice format:
    - If it's a whole number → return as integer (no .0)
    - Otherwise keep 1 or 2 decimals
    """
    try:
        num = float(value)
        if num.is_integer():
            return int(num)          # 2785.0 → 2785
        elif num >= 100:
            return round(num, 1)     # e.g. 2785.3 → 2785.3
        else:
            return round(num, 2)     # silver/oil usually 2 decimals
    except (ValueError, TypeError):
        return value  # fallback: keep original if not number


def append_to_financial_csv(new_row_dict):
    """
    Appends one new row to financial_data.csv
    - Ensures file ends with newline
    - Cleans prices (removes .0 when whole number)
    - Skips if date already exists
    Returns: (success: bool, msg: str, added_date: str or None)
    """
    csv_path = os.path.join(settings.BASE_DIR, 'data', 'financial_data.csv')
    
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    fieldnames = ['date', 'gold_price', 'silver_price', 'oil_price']

    if 'date' not in new_row_dict:
        return False, "Missing 'date' field", None

    date_str = str(new_row_dict['date']).strip()

    # Check for duplicate date
    if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('date', '').strip() == date_str:
                    return False, f"Date {date_str} already exists — not adding again", None

    # Ensure file ends with newline
    if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
        with open(csv_path, 'rb+') as f:
            f.seek(-1, os.SEEK_END)
            last_char = f.read(1)
            if last_char != b'\n':
                f.write(b'\n')

    file_already_has_content = os.path.exists(csv_path) and os.path.getsize(csv_path) > 0

    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_already_has_content:
            writer.writeheader()
        
        # Clean prices before writing
        clean_row = {
            'date': date_str,
            'gold_price': clean_price(new_row_dict.get('gold_price', '')),
            'silver_price': clean_price(new_row_dict.get('silver_price', '')),
            'oil_price': clean_price(new_row_dict.get('oil_price', ''))
        }
        writer.writerow(clean_row)

    return True, f"Added row for date: {date_str}", date_str



def generate_realistic_next_prices(prev_gold, prev_silver, prev_oil):
    """
    Generate next day's prices with small realistic daily changes.
    2026 rough ranges: Gold 2300–3400, Silver 25–50, Oil 50–130
    """
    np.random.seed()  # fresh randomness each call

    # Daily volatility (standard deviation)
    gold_change   = np.random.normal(0, 28)     # ~1–1.5% daily move
    silver_change = np.random.normal(0, 1.4)
    oil_change    = np.random.normal(0, 4.0)

    new_gold   = round(max(2300, min(3400, prev_gold   + gold_change)),   1)
    new_silver = round(max(25,   min(50,   prev_silver + silver_change)), 2)
    new_oil    = round(max(50,   min(130,  prev_oil    + oil_change)),    2)

    return new_gold, new_silver, new_oil