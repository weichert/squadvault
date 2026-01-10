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

<!-- OPERATOR COMMANDS SENTINEL -->

## Operator Commands (Weekly Recaps)

SquadVault weekly recaps are governed by a **single canonical lifecycle** and exposed via one operator CLI.

This is the **only supported entrypoint** for rendering, regenerating, approving, and validating weekly recaps.

```bash
./scripts/recap <command> [args]
```

### Golden Path (Regression Gate – recommended)

Runs a **non-destructive** end-to-end check:
- no-delta path (fingerprint unchanged → no approval)
- forced path (new draft → explicit approval)
- approval invariants

```bash
./scripts/recap check \
  --db .local_squadvault.sqlite \
  --league-id 70985 \
  --season 2024 \
  --week-index 6 \
  --approved-by steve
```

### Render a week (debug / operator visibility)

```bash
./scripts/recap render-week \
  --db .local_squadvault.sqlite \
  --league-id 70985 \
  --season 2024 \
  --week-index 6
```

### Regenerate a DRAFT artifact (idempotent unless forced)

```bash
./scripts/recap regen \
  --db .local_squadvault.sqlite \
  --league-id 70985 \
  --season 2024 \
  --week-index 6 \
  --reason LEDGER_SYNC
```

Force-create a new DRAFT even if the fingerprint is unchanged:

```bash
./scripts/recap regen \
  --db .local_squadvault.sqlite \
  --league-id 70985 \
  --season 2024 \
  --week-index 6 \
  --reason LEDGER_SYNC \
  --force
```

### Approve latest DRAFT artifact

```bash
./scripts/recap approve \
  --db .local_squadvault.sqlite \
  --league-id 70985 \
  --season 2024 \
  --week-index 6 \
  --approved-by steve
```

Require that a DRAFT exists (refuse otherwise):

```bash
./scripts/recap approve \
  --db .local_squadvault.sqlite \
  --league-id 70985 \
  --season 2024 \
  --week-index 6 \
  --approved-by steve \
  --require-draft
```

### Fetch the currently APPROVED artifact

```bash
./scripts/recap fetch-approved \
  --db .local_squadvault.sqlite \
  --league-id 70985 \
  --season 2024 \
  --week-index 6
```

