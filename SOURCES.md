# SOURCES.md — Real-World Source Research

## Source 1 — SAP Fuel & Procurement

### What we researched
SAP Materials Management (MM) module stores procurement and inventory data in tables MSEG (material document segment) and MKPF (material document header). The standard transaction for extracting material movements is MB51 — Material Document List. This transaction exports a flat file with ERP-style field codes rather than human-readable column names.

A typical SAP MM flat file export contains:

| SAP Field | Meaning | Example |
|---|---|---|
| MATNR | Material number | DSL001, PET002 |
| MAKTX | Material description | Diesel, Petrol |
| MENGE | Quantity | 500.000 |
| MEINS | Unit of measure | L, GAL, KG, TON |
| BUDAT | Posting date | 20260101 (YYYYMMDD) |
| WERKS | Plant code | PL01, PL02 |
| BWART | Movement type | 201 (goods issue), 101 (goods receipt) |

Date format is YYYYMMDD by default in SAP exports — no separators. Units depend on how the material master was configured — the same material can appear as L in one plant and GAL in another if the material master was set up inconsistently across plants.

### What we learned
SAP exports are not analyst-friendly. Column headers are ERP abbreviations, dates are in non-standard formats, and units are inconsistent. The plant code (WERKS) is meaningless without a client-specific lookup table that maps codes to facility names. Material numbers (MATNR) follow client-defined naming conventions — we used a prefix convention (DSL = diesel, PET = petrol, LNG = liquefied natural gas, COL = coal, BIO = biomass) to determine scope.

Movement type (BWART) distinguishes goods issue (consumption) from goods receipt (procurement) — in a production system only goods issues should count toward emissions. We simplified this by treating all rows as consumption.

### What our sample data looks like and why
Our sample SAP CSV uses tab-delimited format with SAP field names as headers. Quantities include fuel materials (DSL001, PET002, LNG003, COL004, BIO005) mapped to Scope 1, and non-fuel procurement rows mapped to Scope 3. Units deliberately include L, GAL, KG, TON, and M3 to exercise unit normalization. Dates use YYYYMMDD format. One row has a negative quantity, one has a missing unit, and one has an extreme quantity — to exercise validation and anomaly detection.

### What would break in a real deployment
- Plant codes (WERKS) would need a client-provided lookup table to map to meaningful facility names
- Movement type filtering (BWART) is not implemented — goods receipts would incorrectly count as emissions
- SAP exports from different clients use different encodings (UTF-8, Latin-1, CP1252) — our parser assumes UTF-8
- Some SAP configurations export German column headers (MENGE becomes Menge, MEINS becomes ME) — our parser would fail
- Material number conventions are client-specific — our prefix-based scope classification would not generalize

---

## Source 2 — Utility Electricity

### What we researched
Utility electricity data is accessed through three main channels: PDF bills, utility portal CSV exports, and the Green Button standard (an NAESB standard for electricity data in XML/CSV format, common in the US). For enterprise clients in India, the most common handoff is a portal CSV export — facilities teams log into the utility portal (BESCOM, Tata Power, MSEDCL etc.) and download consumption reports.

A typical utility portal CSV export contains:

| Field | Meaning | Example |
|---|---|---|
| meter_id | Meter identifier | MTR-001 |
| account_number | Utility account | ACC-2024-001 |
| billing_start | Start of billing period | 2026-01-03 |
| billing_end | End of billing period | 2026-02-02 |
| usage_value | Consumption quantity | 45230.5 |
| usage_unit | Unit of consumption | kWh, MWh |
| tariff_code | Tariff classification | HT-1, LT-2 |

### What we learned
Utility billing periods do not align with calendar months. A billing cycle is typically 28-35 days depending on meter reading schedules. This means a January emissions report cannot simply sum all rows with billing_start in January — a single billing period may span December and January. For this prototype we use billing_start as the date field, which is a simplification.

Units vary — some portals export in kWh, others in MWh. Our normalizer converts MWh to kWh (× 1000). Usage values can be very large for industrial meters — a single row for a large facility might show 450,000 kWh, which is legitimate but triggers our fixed threshold anomaly check. Analysts reviewing utility data need to understand this.

### What our sample data looks like and why
Our sample utility CSV uses billing_start, billing_end, meter_id, usage_value, and usage_unit. Units include both kWh and MWh to exercise conversion. One row has an extreme usage value to trigger anomaly detection. One row has a missing unit to trigger validation failure. Billing periods are set to 30-day cycles starting on different dates to reflect real non-calendar alignment.

### What would break in a real deployment
- Billing period attribution: allocating consumption to calendar months requires pro-rating across period boundaries — not implemented
- Estimated reads: utility portals flag some reads as estimated (E) vs actual (A) — estimated reads should be reviewed differently, we do not track this
- Multi-meter aggregation: large facilities have multiple meters per site — we treat each meter row independently, no site-level rollup
- Portal CSV schemas vary significantly across utilities — column names and date formats differ between BESCOM, Tata Power, and others
- Green Button XML format (common in US clients) is not supported — our parser only handles CSV

---

## Source 3 — Corporate Travel

### What we researched
Corporate travel data is managed through platforms like Concur (SAP), Navan (formerly TripActions), and Egencia. These platforms expose data via API and expense report CSV export. The standard analyst handoff is a CSV export from the travel management platform — travel managers or finance teams export trip reports periodically.

A typical Concur-style travel export contains:

| Field | Meaning | Example |
|---|---|---|
| employee_id | Traveller identifier | EMP001 |
| trip_id | Unique trip reference | TRIP-001 |
| travel_date | Date of travel | 2026-01-15 |
| travel_type | Category | flight, hotel, ground |
| origin_airport | IATA origin code | DEL |
| destination_airport | IATA destination code | BOM |
| distance_km | Trip distance | 1148.0 |
| travel_class | Cabin class | economy, business |
| nights_stayed | For hotels | 2 |
| ground_transport_type | For ground | taxi, train, rental_car |

### What we learned
Corporate travel platforms expose three emission categories with different characteristics. Flights use IATA airport codes — distance is sometimes provided, sometimes it must be calculated from great-circle distance between airport coordinates. Hotels use nights stayed as the quantity. Ground transport uses distance in km.

IATA codes are a validation point — an invalid code like XXX indicates bad data. We validate airport codes against a known list. Distance for flights is provided in our sample data — in production, if distance is missing, a great-circle calculation would be needed.

Travel class (economy vs business) has a significant impact on emission factors — business class has a multiplier of approximately 2.5× economy. We store travel_class but do not apply class-specific factors in this prototype.

### What our sample data looks like and why
Our sample travel CSV includes all three travel types: flights with IATA codes and distances, hotels with nights stayed, and ground transport with distances. One row has an invalid airport code (XXX) to trigger validation failure. One flight has an extreme distance to trigger anomaly detection. Dates use ISO format (YYYY-MM-DD). Employee IDs and trip IDs follow a consistent naming convention to reflect real platform exports.

### What would break in a real deployment
- Travel class multipliers are not applied — business class trips are undercounted relative to economy
- Missing distances: if a platform does not provide distance_km, great-circle calculation from airport coordinates is needed — not implemented
- Hotel emission factors vary by country and star rating — we use a flat quantity (nights) with no factor applied
- Ground transport fuel type affects emission factor significantly — taxi vs electric train vs rental car are very different
- Concur API exports include expense line items that are not travel (meals, incidentals) — filtering logic would be needed in production
- Platform-specific field names vary: Navan uses different column names than Concur — our parser assumes Concur-style headers