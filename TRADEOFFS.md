# TRADEOFFS.md — Deliberate Tradeoffs

## 1. Synchronous Pipeline over Async Processing

The ingestion pipeline runs synchronously — when a file is uploaded, the browser waits until every row has been parsed, normalized, validated, analyzed, and saved before a response is returned.

An async pipeline (Celery + Redis) would give better UX — the upload returns immediately and processing happens in the background. But async introduces a class of failure that is dangerous in a compliance context: partial batch state. If a background worker crashes at row 847, the batch exists in the database in an incomplete state — some rows saved, some not. Determining what succeeded and what did not requires additional recovery infrastructure.

Synchronous processing means the pipeline behaves as a single unit. In practice, processing and saving happen row by row — a crash mid-batch would leave partial data in the database. This is a known limitation acknowledged in the chunked streaming tradeoff below. The analyst always sees a complete, consistent batch. In a system where incomplete data reaching auditors is a serious problem, this tradeoff favors correctness over UX.

Production implication: large files will need chunked async processing. This prototype sets a 50MB upload limit to keep synchronous processing viable.

---

## 2. No Historical Cross-Batch Anomaly Detection

Anomaly detection operates within the uploaded batch only. The median is computed from rows in the current file — not from historical uploads.

Cross-batch detection would give stronger baselines. A quantity that looks normal within a single file might be an outlier compared to twelve months of historical data. But historical detection requires clean historical data to exist — which it does not at onboarding time. Using a corrupted or sparse historical baseline would produce worse anomaly detection than batch-local median. It also introduces infrastructure complexity: historical aggregates need to be stored, indexed, and updated incrementally.

Batch-local median gives deterministic, explainable behavior from the first upload. The tradeoff is weaker detection on early uploads where the batch itself may be small or contain unusual data.

---

## 3. Full File Load over Chunked Streaming

Every uploaded CSV is loaded into memory in full using `pandas.read_csv()` before any processing begins. Chunked streaming (`chunksize=1000`) would process the file in segments, keeping memory usage flat regardless of file size.

Full file load was chosen because batch-level statistics — specifically the median per material/meter/trip type used in anomaly detection — require seeing the entire file before any row can be analyzed. Chunked processing would require a two-pass approach: first pass to compute batch statistics, second pass to analyze rows. This adds complexity and doubles I/O.

The tradeoff is memory: a large file spikes memory on upload. The 50MB limit mitigates this at prototype scale. Production would need chunked two-pass processing or pre-aggregation.

---

## 4. No Post-Ingestion Analyst Edit Versioning

The system tracks every transformation made during ingestion — unit conversions, date normalization, column renaming — in the `transformations` field. The original row is preserved in `raw_data`. This covers the ingestion audit trail completely.

What is not tracked: if an analyst's approval decision changes — approved then rejected, or rejected then approved — the system records only the final state (`approved_by`, `approved_at`). Intermediate decision history is not stored.

A full revision system would store every status transition with timestamp and actor. This would answer questions like "who approved this row at 3pm and who reversed it at 5pm." That level of audit depth was scoped out of the prototype. The `transformations` field covers data changes; decision history versioning would be the next layer in a production system.