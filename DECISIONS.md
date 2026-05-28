# DECISIONS.md — Design Decisions & Ambiguity Resolution

## Source Format Decisions

### SAP — Flat File CSV, not IDoc or OData

SAP exposes data through multiple mechanisms: IDocs (Electronic Data Interchange documents), OData services, BAPIs, and flat file exports. We chose flat file CSV export from SAP MM transaction MB51.

IDoc requires EDI middleware and SAP basis configuration — not realistic for a prototype handoff. OData requires live SAP system access and authentication setup. Flat file is what enterprise clients actually send over email or SFTP when onboarding — a sustainability analyst exports MB51 and sends the file. This matches the realistic client handoff described in the brief.

What we handled: fuel materials (diesel, petrol, LNG, coal, biomass) and non-fuel procurement rows. Scope determined by material code prefix.

What we ignored: plant code lookup tables (WERKS maps to facility names via client-specific config), movement type filtering (BWART distinguishes goods issue from goods receipt — we treated all rows as consumption), document type distinctions.

### Utility — Portal CSV, not PDF or API

Utility data arrives three ways in practice: PDF bills, portal CSV exports, or Green Button API (US standard). PDF requires OCR — brittle and out of scope. Green Button API requires utility-specific OAuth — not realistic for prototype. Portal CSV is what a facilities team actually downloads and sends. Fields are consistent enough across major portals to normalize.

What we handled: meter-level electricity consumption with billing period start date, usage value, and unit (kWh/MWh).

What we ignored: multi-meter aggregation, estimated vs actual read flags, tariff structure (time-of-use vs flat rate affects emissions intensity), billing periods that span across months.

### Travel — Concur-style CSV, not API

Concur and Navan expose travel data via API and expense report CSV export. API requires OAuth, client-specific configuration, and scope approval — not realistic for onboarding prototype. CSV export is the standard handoff format — travel managers export and send.

What we handled: flights (origin/destination airport codes, distance), hotels (nights stayed), ground transport (distance, type).

What we ignored: travel class emissions multipliers (business vs economy have different factors), hotel chain-specific factors, ground transport fuel type.

---

## Architecture Decisions

### One Normalized EmissionRecord Table, Not Source-Specific Tables

The analyst workflow — filtering, status tracking, approval, audit trail — is operationally identical across all three sources. If we had separate SAP, Utility, Travel tables, the dashboard, review page, and audit trail would each need to be written three times. Every query would be a UNION. Every new feature would need to be built three times.

Source-specific variability is handled at ingestion. Downstream review workflows operate on the normalized schema regardless of source, while provenance is preserved separately through batch linkage and raw_data.

### Normalization at Ingestion Time, Not Query Time

Normalization happens when the file is uploaded — not when the analyst queries the dashboard. This means the analyst sees exactly what will go to auditors. If we normalized at query time, a change in conversion logic would silently change the meaning of historical records. Ingestion-time normalization freezes the record — `raw_data` stores the original, `transformations` stores exactly what changed and how.

### Batch-Local Anomaly Detection, Not Historical Cross-Batch

Anomaly detection computes the median within the uploaded batch only. Cross-batch historical comparison would give stronger baselines — but onboarding prototypes often lack sufficient historical clean data to establish reliable baselines. Within-batch median gives deterministic, explainable behavior without requiring historical warehouse infrastructure.

### Median, Not Average, for Anomaly Detection

Outliers destroy averages. If one row has quantity 999,999 and five rows have quantity 500, the average becomes ~166,832 — useless as a baseline. The median stays at 500. Anomaly detection works correctly even when the upload itself contains bad data.

### Deterministic Rules, Not ML

Auditors must be able to answer: why was this row flagged? With deterministic rules the answer is always exact — "quantity is 2499x the batch median." With ML the answer is "the model thought it looked unusual" — unacceptable in a compliance context.

### Scope Determined Before Rule Evaluation

Certain validation and analysis rules depend on emission category and expected units, so scope is determined before rule evaluation. A suspicious quantity for electricity (kWh) is completely different from a suspicious quantity for diesel (litres). Scope must be known first so the right thresholds apply.

### Failed Rows Are Never Discarded

Every row is saved regardless of status. Analysts see everything that came in. Analysts may still approve rows that failed validation, but the original validation errors remain preserved in the audit trail. This is intentional — the analyst has context the system does not.

### Role-Based Access — Admin and Analyst

Upload and review are analyst functions. Batch locking and batch management are admin functions. This separation means an analyst cannot accidentally lock or remove a batch that is under review, and an auditor can trace every approval decision to a named analyst with a timestamp.

---

## What I Would Ask the PM

**1. Can analysts edit normalized values before approval, or only approve/reject?**
This fundamentally changes the data model. If editing is allowed, we need immutable revision history, edit versioning, and change tracking. Currently the system is approve/reject only — normalized values cannot be changed post-ingestion.

**2. Is approval at row level, batch level, or both?**
Currently row-level with optional batch lock by admin. If batch-level approval is the real workflow, the status model and dashboard change significantly.

**3. Should suspicious rows block audit export until reviewed, or can they proceed?**
Currently suspicious rows do not block locking — an admin can lock a batch with unreviewed suspicious rows. If suspicious rows must be reviewed before lock, the lock logic needs to change.

**4. Should scope categorization be rule-based, or will the client provide authoritative mappings?**
We used rule-based classification — SAP fuel material codes map to Scope 1, electricity to Scope 2, travel to Scope 3. A real client may have custom material codes or edge cases that break these rules. Client-provided mappings would need a configuration layer.

**5. Should the prototype assume consistent CSV schemas per source, or tolerate client-specific variations?**
We assumed a consistent schema per source. Real SAP exports vary by client configuration — column names, date formats, and encoding differ. A production system needs configurable field mapping per client.

**6. Once approved, can approval be reversed?**
Currently approved rows can be rejected if the batch is not locked. Post-lock, nothing can be changed. If reversal is never allowed under any circumstance, the lock logic should enforce this more strictly.

**7. Should anomaly detection consider historical uploads or only the current batch?**
Currently detection is batch-local. Cross-batch historical comparison would give better baselines but requires storing and indexing historical aggregates — a significant infrastructure decision.