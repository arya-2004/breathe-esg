# Breathe ESG — Emissions Ingestion Platform

A prototype system for ingesting, normalizing, validating, and reviewing enterprise emissions data from three sources: SAP fuel and procurement, utility electricity, and corporate travel.


## What it does

Enterprise clients send emissions data as CSV files from three systems — SAP, utility portals, and corporate travel platforms. Every file arrives in a different shape with different column names, date formats, and units. This system ingests all three, normalizes every row into a common schema, flags validation failures and anomalies, and surfaces everything for analyst review before the data is locked for audit.


## Setup

**Requirements**
- Python 3.12
- Node.js 18+

**Backend**
```bash
cd breathe_esg
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

Backend runs at `http://localhost:8000`
Frontend runs at `http://localhost:5173`


## Credentials

| Role | Username | Password |
|---|---|---|
| Admin | admin | admin1234 |
| Analyst | analyst | analyst1234 |

Admin can upload files, review records, lock batches, and manage users.
Analyst can upload files and review records.


## Sample Data

The `sample_data/` folder contains test CSV files for all three sources.

- `sap_test.csv` — SAP MM flat file export with fuel and procurement rows
- `utility_test.csv` — Utility portal electricity billing export
- `travel_test.csv` — Concur-style corporate travel export

Each file contains clean rows, rows with validation failures, and rows designed to trigger anomaly detection. Upload all three to see the full review workflow.


## How to test the full workflow

1. Log in as admin or analyst
2. Go to Upload and upload all three sample CSVs
3. Go to Dashboard to see batch summaries and all records
4. Click Review on any suspicious or failed row to see flags and raw data
5. Approve or reject rows
6. Log in as admin to lock a batch once all rows are reviewed


## Architecture

**Backend** — Django 6, Django REST Framework, SQLite (local), PostgreSQL (production)

**Frontend** — React, Vite, Axios

**Pipeline** — Parse → Normalize → Determine Scope → Validate → Analyze → Save

Every row is saved regardless of status. Nothing is discarded. The original raw data and every normalization change are stored permanently against the record.


## Project structure

breathe_esg/
backend/          Django settings and URL config
emissions/        Models, views, parsers, utils
parsers/      Source-specific CSV parsers
utils/        Normalize, validate, analyze
frontend/
src/
pages/    Login, Upload, Dashboard, Review
sample_data/      Test CSVs for all three sources
MODEL.md          Data model and architecture
DECISIONS.md      Design decisions and ambiguity resolution
TRADEOFFS.md      Deliberate tradeoffs
SOURCES.md        Real-world source research


## Deployment

Backend deployed on Render. Frontend deployed on Vercel.

Live URL: https://breathe-6x1z3xhz5-arya-2004s-projects.vercel.app
