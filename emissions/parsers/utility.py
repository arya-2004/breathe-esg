import pandas as pd
from ..utils.normalize import normalize_date, normalize_unit
from ..utils.validate import validate_utility
from ..utils.analyze import analyze_batch

UTILITY_COLUMN_MAP = {
    'meter_id': 'meter_id',
    'facility_code': 'facility_code',
    'billing_start': 'date',
    'usage_value': 'quantity',
    'usage_unit': 'unit',
    'tariff_type': 'tariff_type',
    'total_cost': 'amount',
    'currency': 'currency',
    'provider': 'provider',
}


def process_utility(file):
    # Step 1 — parse
    try:
        df = pd.read_csv(file, dtype=str)
        df = df.drop_duplicates()
    except Exception as e:
        raise ValueError(f'Could not read file: {e}')

    # strip whitespace
    df = df.apply(lambda col: col.str.strip() if col.dtype == 'object' else col)

    # Step 2 — map columns
    df = df.rename(columns=UTILITY_COLUMN_MAP)

    records = []

    for i, row in df.iterrows():
        raw = row.to_dict()
        raw = {k: (None if isinstance(v, float) and v != v else v) for k, v in raw.items()}
        normalized = raw.copy()
        transformations = []

        # Step 3 — normalize date
        normalized['date'], date_transform = normalize_date(
            raw.get('date', '')
        )
        if date_transform:
            transformations.append(date_transform)

        # Step 4 — normalize unit
        if raw.get('unit') and raw.get('quantity'):
            std_unit, new_qty, unit_transform = normalize_unit(
                raw['unit'],
                raw['quantity']
            )
            normalized['unit'] = std_unit
            normalized['quantity'] = new_qty
            if unit_transform:
                transformations.append(unit_transform)

        # Step 5 — scope is always scope_2 for electricity
        scope = 'scope_2'

        # Step 6 — validate
        validation_errors = validate_utility(normalized)

        records.append({
            'source_row_number': i + 2,
            'source': 'UTILITY',
            'scope': scope,
            'date': normalized.get('date'),
            'description': f"{normalized.get('meter_id', '')} — {normalized.get('facility_code', '')}",
            'quantity': normalized.get('quantity'),
            'unit': normalized.get('unit', ''),
            'material': None,
            'plant': None,
            'meter_id': normalized.get('meter_id', ''),
            'trip_type': None,
            'validation_errors': validation_errors,
            'analysis_flags': [],
            'transformations': transformations,
            'raw_data': raw,
            'status': 'failed' if validation_errors else 'pending',
        })

    # Step 7 — analyze batch
    records = analyze_batch(records, 'UTILITY')

    # Step 8 — update suspicious status
    for record in records:
        if record['status'] != 'failed' and record['analysis_flags']:
            record['status'] = 'suspicious'

    return records