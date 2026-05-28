import pandas as pd


THRESHOLDS = {
    'SAP': {
        'L': 100000,
        'KG': 500000,
        'M3': 50000,
    },
    'UTILITY': {
        'kWh': 500000,
    },
    'TRAVEL': {
        'flight_km': 15000,
    }
}


def analyze_batch(records, source):
    if not records:
        return records

    df = pd.DataFrame(records)

    # pick grouping column per source
    if source == 'SAP':
        group_col = 'material'
    elif source == 'UTILITY':
        group_col = 'meter_id'
    else:
        group_col = 'trip_type'

    # only analyze rows that passed validation
    valid_mask = df['validation_errors'].apply(lambda e: len(e) == 0)
    valid_df = df[valid_mask].copy()

    if valid_df.empty:
        return records

    # calculate median per group
    valid_df['quantity'] = pd.to_numeric(valid_df['quantity'], errors='coerce')

    if group_col in valid_df.columns:
        median_by_group = valid_df.groupby(group_col)['quantity'].transform('median')
    else:
        median_by_group = valid_df['quantity'].median()

    # analyze each valid row
    for i in valid_df.index:
        flags = []
        qty = valid_df.at[i, 'quantity']
        unit = str(df.at[i, 'unit']).strip()

        # spike vs median
        try:
            median = median_by_group[i] if hasattr(median_by_group, '__getitem__') else median_by_group
            if pd.notna(qty) and pd.notna(median) and median > 0:
                ratio = qty / median
                if ratio > 10:
                    flags.append(
                        f'Quantity is {round(ratio)}x the batch median'
                    )
        except Exception:
            pass

        # fixed threshold
        source_thresholds = THRESHOLDS.get(source, {})
        threshold = source_thresholds.get(unit)
        if threshold and pd.notna(qty) and qty > threshold:
            flags.append(
                f'Exceeds absolute threshold of {threshold} {unit}'
            )

        # travel specific
        if source == 'TRAVEL':
            trip_type = str(df.at[i, 'trip_type']).strip().lower() \
                if 'trip_type' in df.columns else ''
            if trip_type == 'flight' and pd.notna(qty) and qty > 15000:
                flags.append('Flight distance exceeds maximum possible')

        df.at[i, 'analysis_flags'] = flags

    return df.to_dict('records')