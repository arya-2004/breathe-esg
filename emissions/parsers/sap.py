import pandas as pd
from ..utils.normalize import normalize_date, normalize_unit
from ..utils.validate import validate_sap
from ..utils.analyze import analyze_batch

SAP_COLUMN_MAP = {
    'MATNR': 'material',
    'MAKTX': 'description',
    'WERKS': 'plant',
    'MENGE': 'quantity',
    'MEINS': 'unit',
    'BUDAT': 'date',
    'LIFNR': 'vendor',
    'WAERS': 'currency',
    'DMBTR': 'amount',
    'KOSTL': 'cost_center',
}

FUEL_MATERIALS = ['DSL001', 'PET002', 'LNG003', 'COL004', 'BIO005']


def determine_scope(row):
    if row.get('material', '').strip() in FUEL_MATERIALS:
        return 'scope_1'
    return 'scope_3'


def process_sap(file):
    # Step 1 — parse
    try:
        df = pd.read_csv(file, sep='|', dtype=str)
        print("Columns found:", df.columns.tolist())
        print("Total rows:", len(df))
    except Exception:
        df = pd.read_csv(file, dtype=str)

    df = df.drop_duplicates()

    # strip whitespace from all values
    df = df.apply(lambda col: col.str.strip() if col.dtype == 'object' else col)

    # Step 2 — map columns to English
    df = df.rename(columns=SAP_COLUMN_MAP)

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

        # Step 5 — determine scope
        scope = determine_scope(normalized)

        # Step 6 — validate
        validation_errors = validate_sap(normalized)

        records.append({
            'source_row_number': i + 2,
            'source': 'SAP',
            'scope': scope,
            'date': normalized.get('date'),
            'description': normalized.get('description', ''),
            'quantity': normalized.get('quantity'),
            'unit': normalized.get('unit', ''),
            'material': normalized.get('material', ''),
            'plant': normalized.get('plant', ''),
            'trip_type': None,
            'meter_id': None,
            'validation_errors': validation_errors,
            'analysis_flags': [],
            'transformations': transformations,
            'raw_data': raw,
            'status': 'failed' if validation_errors else 'pending',
        })

    # Step 7 — analyze whole batch
    records = analyze_batch(records, 'SAP')

    # Step 8 — update status for suspicious
    for record in records:
        if record['status'] != 'failed' and record['analysis_flags']:
            record['status'] = 'suspicious'

    return records