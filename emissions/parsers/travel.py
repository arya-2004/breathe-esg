import pandas as pd
from ..utils.normalize import normalize_date
from ..utils.validate import validate_travel
from ..utils.analyze import analyze_batch

TRAVEL_COLUMN_MAP = {
    'employee_id': 'employee_id',
    'trip_type': 'trip_type',
    'travel_date': 'date',
    'origin': 'origin',
    'destination': 'destination',
    'distance_km': 'quantity',
    'class_or_type': 'class_or_type',
    'amount': 'amount',
    'currency': 'currency',
    'vendor': 'vendor',
}

SCOPE_MAP = {
    'flight': 'scope_3',
    'hotel': 'scope_3',
    'ground_transport': 'scope_3',
}


def build_description(row):
    trip_type = str(row.get('trip_type', '')).strip().lower()

    if trip_type == 'flight':
        origin = row.get('origin', '')
        destination = row.get('destination', '')
        return f"Flight {origin} → {destination}"

    elif trip_type == 'hotel':
        destination = row.get('destination', '') or row.get('origin', '')
        return f"Hotel stay — {destination}"

    elif trip_type == 'ground_transport':
        origin = row.get('origin', '')
        destination = row.get('destination', '')
        return f"Ground transport {origin} → {destination}"

    return 'Travel record'


def process_travel(file):
    # Step 1 — parse
    try:
        df = pd.read_csv(file, dtype=str)
        df = df.drop_duplicates()
    except Exception as e:
        raise ValueError(f'Could not read file: {e}')

    # strip whitespace
    df = df.apply(
        lambda col: col.str.strip() if col.dtype == 'object' else col
    )

    # lowercase trip_type for consistency
    if 'trip_type' in df.columns:
        df['trip_type'] = df['trip_type'].str.lower()

    # Step 2 — map columns
    df = df.rename(columns=TRAVEL_COLUMN_MAP)

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

        # Step 4 — normalize quantity
        # travel distance stays in km, no unit conversion needed
        # but we still clean it
        quantity = raw.get('quantity')
        if quantity:
            try:
                normalized['quantity'] = float(quantity)
                normalized['unit'] = 'km'
            except (ValueError, TypeError):
                normalized['quantity'] = None
                normalized['unit'] = ''
        else:
            # flights often have no distance
            normalized['quantity'] = None
            normalized['unit'] = 'km'

        # Step 5 — scope
        trip_type = str(normalized.get('trip_type', '')).strip().lower()
        scope = SCOPE_MAP.get(trip_type, 'scope_3')

        # Step 6 — validate
        validation_errors = validate_travel(normalized)

        # Step 7 — build description
        description = build_description(normalized)

        records.append({
            'source_row_number': i + 2,
            'source': 'TRAVEL',
            'scope': scope,
            'date': normalized.get('date'),
            'description': description,
            'quantity': normalized.get('quantity'),
            'unit': normalized.get('unit', 'km'),
            'material': None,
            'plant': None,
            'meter_id': None,
            'trip_type': trip_type,
            'validation_errors': validation_errors,
            'analysis_flags': [],
            'transformations': transformations,
            'raw_data': raw,
            'status': 'failed' if validation_errors else 'pending',
        })

    # Step 8 — analyze batch
    records = analyze_batch(records, 'TRAVEL')

    # Step 9 — update suspicious status
    for record in records:
        if record['status'] != 'failed' and record['analysis_flags']:
            record['status'] = 'suspicious'

    return records