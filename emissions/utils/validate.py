VALID_CURRENCIES = ['USD', 'EUR', 'INR', 'GBP', 'AUD', 'SGD']

VALID_AIRPORT_CODES = [
    'DEL', 'BOM', 'BLR', 'HYD', 'MAA', 'CCU', 'AMD',
    'JFK', 'LHR', 'DXB', 'SIN', 'CDG', 'FRA', 'NRT',
    'SYD', 'LAX', 'ORD', 'DFW', 'ATL', 'SFO'
]

VALID_TRIP_TYPES = ['flight', 'hotel', 'ground_transport']


def validate_sap(row):
    errors = []

    if not row.get('date'):
        errors.append('Missing or invalid date')

    quantity = row.get('quantity')
    if quantity is None:
        errors.append('Missing quantity')
    else:
        try:
            qty = float(quantity)
            if qty < 0:
                errors.append('Negative quantity')
        except (ValueError, TypeError):
            errors.append('Quantity is not a number')

    if not row.get('unit'):
        errors.append('Missing unit')

    if not row.get('material'):
        errors.append('Missing material code')

    if not row.get('plant'):
        errors.append('Missing plant code')

    currency = str(row.get('currency', '')).strip().upper()
    if currency and currency not in VALID_CURRENCIES:
        errors.append(f'Unknown currency: {currency}')

    return errors


def validate_utility(row):
    errors = []

    if not row.get('date'):
        errors.append('Missing or invalid date')

    quantity = row.get('quantity')
    if quantity is None:
        errors.append('Missing usage value')
    else:
        try:
            qty = float(quantity)
            if qty < 0:
                errors.append('Negative electricity usage')
        except (ValueError, TypeError):
            errors.append('Usage value is not a number')

    if not row.get('unit'):
        errors.append('Missing unit')

    if not row.get('meter_id'):
        errors.append('Missing meter ID')

    if not row.get('facility_code'):
        errors.append('Missing facility code')

    return errors


def validate_travel(row):
    errors = []

    if not row.get('date'):
        errors.append('Missing or invalid date')

    trip_type = str(row.get('trip_type', '')).strip().lower()

    if not trip_type:
        errors.append('Missing trip type')
    elif trip_type not in VALID_TRIP_TYPES:
        errors.append(f'Unknown trip type: {trip_type}')

    if trip_type == 'flight':
        origin = str(row.get('origin', '')).strip().upper()
        destination = str(row.get('destination', '')).strip().upper()
        if origin not in VALID_AIRPORT_CODES:
            errors.append(f'Unknown origin airport: {origin}')
        if destination not in VALID_AIRPORT_CODES:
            errors.append(f'Unknown destination airport: {destination}')

    if trip_type == 'ground_transport':
        quantity = row.get('quantity')
        if quantity is not None:
            try:
                if float(quantity) < 0:
                    errors.append('Negative distance')
            except (ValueError, TypeError):
                errors.append('Distance is not a number')

    if trip_type == 'hotel':
        quantity = row.get('quantity')
        if quantity is not None:
            try:
                if float(quantity) < 0:
                    errors.append('Negative nights stayed')
            except (ValueError, TypeError):
                errors.append('Nights value is not a number')

    return errors