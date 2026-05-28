# MODEL.md — Data Model & Architecture

## Overview

This system ingests emissions data from three enterprise sources — SAP fuel and procurement, utility electricity, and corporate travel. The core challenge is not carbon calculation — it is that every source arrives in a completely different shape, with different column names, date formats, units, and data quality issues.

Every row from every source is normalized into a single common schema, validated against hard rules, analyzed for anomalies, and surfaced for analyst review before being locked for audit.

---

## Why Two Core Tables

Most naive implementations create separate tables per source — a SAP table, a utility table, a travel table. This was deliberately avoided.

The problem with separate tables: the analyst dashboard, filters, approval workflow, and audit trail would need to handle three completely different schemas. Every query becomes a UNION. Every new feature needs to be built three times.

The solution: one normalized EmissionRecord table that every source maps into. Downstream review workflows operate on the normalized schema regardless of source, while provenance is preserved separately through batch linkage and raw_data.

---

## Table 1 — Organization

Every client is an Organization. All data is scoped to an organization.

| Field | Type | Purpose |
|---|---|---|
| id | int | Primary key |
| name | string | Client organization name |
| created_at | datetime | When the org was onboarded |

Multi-tenancy is handled at this layer. Every UploadBatch belongs to an Organization. Queries filter by organization. Analysts are scoped to their organization via UserProfile. Data is fully isolated per client.

The UserProfile table links Django's built-in User model to an Organization:

| Field | Type | Purpose |
|---|---|---|
| user | FK → User | Which user |
| organization | FK → Organization | Which client they belong to |

Superusers have no UserProfile and can see all organizations — intended for Breathe ESG internal admin use only.

---

## Table 2 — UploadBatch

Every file upload creates one UploadBatch record. It is the receipt for that upload.

| Field | Type | Purpose |
|---|---|---|
| id | int | Primary key |
| organization | FK → Organization | Which client this belongs to |
| source | string | SAP / UTILITY / TRAVEL |
| filename | string | Original filename as uploaded |
| uploaded_by | FK → User | Which analyst uploaded |
| uploaded_at | datetime | Exact timestamp of upload |
| total_rows | int | Total rows processed |
| failed_rows | int | Rows that failed validation |
| suspicious_rows | int | Rows flagged by anomaly analysis |
| is_locked | bool | Whether batch is locked for audit |

Without UploadBatch, an auditor cannot answer: which file created this row? Who uploaded it? When? Every EmissionRecord links back to its batch, making the full chain traceable.

---

## Table 3 — EmissionRecord

Every single row from every source lands here — normalized into identical columns.

| Field | Type | Purpose |
|---|---|---|
| id | int | Primary key |
| batch | FK → UploadBatch | Which upload created this row |
| source_row_number | int | Exact row number in original CSV |
| source | string | SAP / UTILITY / TRAVEL |
| scope | string | scope_1 / scope_2 / scope_3 |
| date | date | Normalized date |
| description | text | Human readable description |
| quantity | float | Normalized quantity |
| unit | string | Normalized unit |
| status | string | pending / suspicious / failed / approved / rejected |
| validation_errors | JSONField | Hard rule failures |
| analysis_flags | JSONField | Soft suspicious flags |
| transformations | JSONField | Every change made during normalization |
| raw_data | JSONField | Original row exactly as received |
| approved_by | FK → User | Which analyst approved or rejected |
| approved_at | datetime | When decision was made |
| created_at | datetime | When record was saved |

---

## Common Schema Design

Different sources use completely different column names for the same concepts. Normalization maps all of them to a common internal schema:

| Source | Raw field | Normalized to |
|---|---|---|
| SAP | MENGE | quantity |
| SAP | MEINS | unit |
| SAP | BUDAT | date |
| SAP | MAKTX | description |
| SAP | WERKS | plant |
| Utility | usage_value | quantity |
| Utility | usage_unit | unit |
| Utility | billing_start | date |
| Travel | distance_km | quantity |
| Travel | travel_date | date |

---

## Scope 1/2/3 Categorization

Scope is determined during ingestion, before rule evaluation, so validation and analysis rules can be scope-aware.

| Source | Scope | Reasoning |
|---|---|---|
| SAP fuel materials — DSL001, PET002, LNG003, COL004, BIO005 | Scope 1 | Direct combustion of fossil fuels owned by the company |
| SAP non-fuel procurement | Scope 3 | Purchased goods and services — indirect |
| Utility electricity | Scope 2 | Purchased electricity — indirect but significant |
| Corporate flights | Scope 3 | Business travel — indirect |
| Corporate hotels | Scope 3 | Business travel — indirect |
| Corporate ground transport | Scope 3 | Business travel — indirect |

---

## Source-of-Truth Tracking

Every EmissionRecord stores four things that together answer any audit question:

**batch** — which file upload created this row, who uploaded it, when

**source_row_number** — the exact row number in the original CSV file. If row 48 failed, the analyst can open the original file and find it immediately.

**raw_data** — the original row exactly as it arrived, before any normalization. Never modified. If we normalized GAL to L, raw_data still shows GAL.

**transformations** — a list of every change made during normalization, with before and after values. For example:
- "unit: GAL → L, quantity: 120.0 × 3.785 = 454.2"
- "date: 20260101 → 2026-01-10"

Together these mean an auditor can always answer:
- Which file produced this row?
- Who uploaded that file?
- When?
- What did the original data look like?
- What exactly did the system change?
- Who reviewed it?
- When was the decision made?

---

## Unit Normalization

All quantities are converted to standard units during ingestion. The conversion happens on a copy of the row — raw_data is saved before this step.

| Original unit | Standard unit | Conversion factor |
|---|---|---|
| L | L | × 1 |
| LTR | L | × 1 |
| GAL | L | × 3.785 |
| KG | KG | × 1 |
| TON | KG | × 1000 |
| kWh | kWh | × 1 |
| MWh | kWh | × 1000 |
| km | km | × 1 |
| M3 | M3 | × 1 |

String matching uses `.strip().lower()` before lookup to handle mixed case and whitespace.

---

## Validation vs Analysis — Two Separate Concepts

These are stored in separate JSONFields — `validation_errors` and `analysis_flags` — because they represent fundamentally different things.

### Validation — hard rules, row is objectively wrong

| Rule | Example |
|---|---|
| Invalid or missing date | 20261301 does not exist |
| Negative quantity | -300 litres of diesel |
| Missing unit | quantity exists but unit is empty |
| Missing material code | SAP row has no MATNR |
| Unknown airport code | XXX is not a real IATA code |
| Negative nights stayed | hotel row shows -2 nights |

Status becomes **failed**. Row is shown in red on dashboard.

### Analysis — soft rules, row is valid but suspicious

**Fixed thresholds** — absolute limits that are always suspicious:
- SAP: quantity > 100,000 units
- Utility: usage > 500,000 kWh
- Travel: flight distance > 15,000 km

**Batch median comparison** — relative to similar rows in the same upload:
- Quantity > 10x the batch median for that material/meter/trip type

**Why median and not average:** outliers destroy averages. If one row has quantity 999,999 and five rows have quantity 500, the average becomes ~166,832 — useless as a baseline. The median stays at 500.

**Why deterministic rules and not ML:** auditors must be able to answer why a row was flagged. With deterministic rules the answer is always exact. With ML the answer is "the model thought it looked unusual" — unacceptable in a compliance context.

Status becomes **suspicious**. Row is shown in yellow on dashboard.

---

## Pipeline Order

Parse → Normalize → Determine Scope → Validate → Analyze → Save

**Parse** — read CSV, rename columns to internal schema

**Normalize** — fix date formats, convert units, strip whitespace. raw_data saved before this step.

**Determine Scope** — classify as scope_1/2/3 based on source and material type

**Validate** — apply hard rules. Mark failed rows.

**Analyze** — apply soft rules using batch median and fixed thresholds. Only runs on rows that passed validation.

**Save** — every row saved regardless of status. Nothing is discarded.

---

## Status Flow

pending → suspicious (if analysis flags exist)
pending → failed (if validation errors exist)
suspicious → approved (analyst decision)
suspicious → rejected (analyst decision)
failed → approved (analyst override)
failed → rejected (analyst decision)
approved → locked (batch lock by admin)


Analysts may approve rows that failed validation — the original validation errors remain preserved in the audit trail. This is intentional: the analyst has context the system does not.

---

## Audit Trail

| Question | Answered by |
|---|---|
| Who uploaded this file? | UploadBatch.uploaded_by |
| When was it uploaded? | UploadBatch.uploaded_at |
| Which client does this belong to? | UploadBatch.organization |
| Which file created this row? | EmissionRecord.batch |
| Which row in the original file? | EmissionRecord.source_row_number |
| What did the original data look like? | EmissionRecord.raw_data |
| What did the system change? | EmissionRecord.transformations |
| Who reviewed this row? | EmissionRecord.approved_by |
| When was the decision made? | EmissionRecord.approved_at |

