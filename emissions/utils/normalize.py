from datetime import datetime


def normalize_date(date_str):
    if not date_str or str(date_str).strip() == '':
        return None, 'date: empty value'

    date_str = str(date_str).strip()

    formats = [
        '%Y-%m-%d',
        '%d.%m.%Y',
        '%Y/%m/%d',
        '%d-%m-%Y',
        '%m/%d/%Y',
    ]

    for fmt in formats:
        try:
            parsed = datetime.strptime(date_str, fmt).date()
            transformation = f"date: {date_str} → {parsed}"
            return parsed, transformation
        except ValueError:
            continue

    return None, f"date: {date_str} → could not parse"


def normalize_unit(unit, quantity):
    if not unit or str(unit).strip() == '':
        return '', quantity, None

    unit_clean = str(unit).strip().lower()

    conversions = {
        'l':   ('L', 1),
        'ltr': ('L', 1),
        'gal': ('L', 3.785),
        'kg':  ('KG', 1),
        'ton': ('KG', 1000),
        'kwh': ('kWh', 1),
        'mwh': ('kWh', 1000),
        'km':  ('km', 1),
        'm3':  ('M3', 1),
    }

    try:
        qty = float(quantity)
    except (ValueError, TypeError):
        return unit_clean, quantity, None

    if unit_clean in conversions:
        std_unit, factor = conversions[unit_clean]
        new_qty = round(qty * factor, 4)
        transformation = f"unit: {unit} → {std_unit}, quantity: {qty} × {factor} = {new_qty}"
        return std_unit, new_qty, transformation

    return unit_clean, qty, None