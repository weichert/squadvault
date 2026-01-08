# squadvault-ingest

Python-based MFL → Notion ingestion for SquadVault (PFL Buddies).

## Setup

1) Create a virtualenv (recommended)
2) Install deps
3) Copy env template and fill secrets
4) Validate schema
5) Run backfill

## Commands

Validate-only (no writes):
```bash
PYTHONPATH=src python -m squadvault.main --validate-only
```

Backfill a year:
```bash
PYTHONPATH=src python -m squadvault.main --years 2024
```

Backfill multiple years:
```bash
PYTHONPATH=src python -m squadvault.main --years 2019,2020,2021,2022,2023,2024
```

## Notes
* Notion is the canonical warehouse.
* Schema-first: the app hard-fails if any database schema deviates from expected.
* Idempotent ingestion: deterministic keys; pages are upserted by Title property.
* Raw MFL JSON is stored (truncated if necessary) and source URLs are preserved.
