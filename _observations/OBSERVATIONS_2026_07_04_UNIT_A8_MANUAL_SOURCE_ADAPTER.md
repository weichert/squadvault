# Observation - Unit A8: Manual Source Adapter

Dated 2026-07-04 (Claude Code, Opus 4.8). Builds the ratified Manual Source Adapter Contract
v1.0 (`docs/contracts/manual_source_adapter_contract_v1.md`, RATIFIED `d101b78` / PR #6). Brief:
`_observations/session_brief_unit_a8_manual_source_adapter.md` (landed `5da60d6`). Three founder
gates (G1 reconciliation + design; G2 test plan; G3 diff + merge); this memo is filed at G3.

## What shipped (the governed testimony door, envelope model)

The adapter admits commissioner-attested auction facts into the existing append-only
`memory_events` ledger as ordinary `DRAFT_PICK` envelopes - NO new table, NO schema change to the
event ledger, NO new event type. Provenance rides `external_source = "MANUAL:<tag>"` (C1). Seven
components:

- **`src/squadvault/ingest/manual_auction.py`** - pure derivation: MANUAL envelopes
  (`mfl_type="MANUAL_AUCTION_WON"`, retention fields); artifact-native deterministic `external_id`
  (contract section 3; re-import is a byte-identical no-op); C1 tag guard (malformed provenance
  refuses entry); C4 partial-truth (unreconciled identity held absent); section 6.4 LOAD_ROSTERS
  integrity anchor (off-roster picks blocked); marker-aware `select_auction_winners` (excludes
  contaminants, never a win-type whitelist); content-addressed `sha256_file` (C2/D3).
- **`src/squadvault/ingest/manual_import.py`** - C3 approval gate (record/has/require; an import
  with no recorded approval is REFUSED - no silent ingestion); conflict surfacing (a manual fact
  disagreeing with a canonical fact is reported; canonical WINS and is never mutated); append-only
  write via `SQLiteStore.append_events`.
- **`src/squadvault/core/storage/schema.sql`** - `manual_import_approvals` table (C3): who/when/
  which-artifact-by-hash. Append-only; stores approvals, never facts.
- **Verifier third path (D5)** in `recap_verifier_v1.py` Category 13: a figure over
  commissioner-attested coverage that re-derives correctly is SURFACED as human-attested (SOFT),
  not silently passed as adapter-grade; a contradiction is still HARD (fabrication vs the imported
  rows is caught). MFL-covered franchises never enter this branch.
- **Provenance threading** in `auction_draft_angles_v1.py`: `AuctionPick` gains `external_source`
  (additive; the shared loader `load_all_auction_picks` selects it) so the verifier and consumers
  can distinguish the branch.
- **`scripts/manual_import_auction_v1.py`** - the ops-shim CLI: the explicit founder act
  (extract -> reconcile -> C3 approve -> emit into a SCRATCH db). Refuses without approval.
- **Tests** (38): `test_ingest_manual_auction_v1` (25), `test_manual_import_store_v1` (7),
  `test_manual_auction_verifier_v1` (4), `test_manual_import_cli_v1` (2) - the frozen G2 plan
  (T1.1-TB.1 + T4.3), including the AUCTION_WON-whitelist regression (TA.1) and the MFL-byte-
  identity guard (T6.2).

## Three corrections recorded this night (append-only)

1. **Brief section 1(a) was stale carry-forward.** The brief described "the schema for attested
   fact rows ... every sibling table," a NEW-table model imported from the FRONTEND Founder's Seal
   (migration 031) precedent. The RATIFIED contract v1.0 governs and is envelope-only: section 2 /
   section 7 "No engine or schema change; manual facts use the existing DRAFT_PICK envelope." Per
   the founder's G1 ruling, contract governs; the brief's section 1(a) is corrected here, not
   silently followed. (The `manual_import_approvals` table is an APPROVALS ledger, not a facts
   table - it stores the C3 attestation act, not the attested facts.)

2. **KP 2018/12171 is NOT an A8 manual import - it is a de-contamination case (-> Unit A9).** The
   G1 Q1 read-only prod probe (prod hash `effb00e5` unchanged) found the "provisional 0002/$67"
   already present as canonical MFL data, with a competing duplicate win:

   ```
   id    src  fr    pl     ty           bid
   3877  MFL  0002  12171  AUCTION_WON  67.0
   3891  MFL  0005  12171  AUCTION_WON  63.0   (duplicate win - two franchises "won" 12171)
   3892  MFL  0005  12171  AUCTION_BID  63.0   (intermediate-bid contaminant)
   ```

   Per the founder's pre-declared decision rule, rows-present routes this to the section 8
   de-contamination filter fix - registered here as **Unit A9 (2018 auction de-contamination)**.
   The KP-sheet adjudicates the true winner of 12171 in that unit. A8 POINTS, never acts: A8 does
   not exclude `AUCTION_BID` from the existing loader (that would change existing 2018 disposition),
   and its acceptance fixture is the 2021 hole (2021 `DRAFT_PICK` absent; `LOAD_ROSTERS` seed x11
   present).

3. **`.gitignore` trap (fixed permanently).** Line 79 `squadvault/` (unanchored) silently ignored
   every NEW file under `src/squadvault/` (existing files grandfathered-tracked; Tests/ negated),
   which would have dropped the two new adapter modules from any commit without `git add -f`.
   Anchored to `/squadvault/` so it only matches a top-level scratch dir; core_engine/eal hold only
   `__pycache__` (separately ignored) and `.DS_Store` is independently ignored, so nothing else is
   exposed. A trap that required every future session to remember `-f` is now disarmed.

## 2021 fixture walkthrough (scratch; prod untouched)

Against a SCRATCH db seeded with the REAL 2021 `LOAD_ROSTERS` seed (11 rows, copied read-only from
prod): (1) without approval -> REFUSED (exit 3), nothing written; (2) with the founder `--approve`
act -> `0002/14136/$50` admitted as `MANUAL_AUCTION_WON` under `MANUAL:KP-AUCTION-2021`; an
off-roster `0002/99999` held absent by the section 6.4 anchor; 0 conflicts. Prod DB hash
`effb00e5` unchanged throughout (verified before/after).

## Checks

- Full trio: ruff clean; mypy clean; pytest green (existing suite unchanged + 38 new).
- prove_ci: green (the determinism / golden-path proofs are the TB.1 zero-diff guard for existing
  artifacts).
- TB.1: existing MFL artifacts regenerate byte-identically - the third path and provenance
  threading are additive and fire only on MANUAL rows, which do not exist in current data.
- Prod DB hash `effb00e5` UNCHANGED for the entire session; zero prod writes. Production entry of
  any KP fact remains a separate founder act (post KP-sheet confirmation).

## Out of scope (per the brief; unchanged)

Entering the KP fact into prod; new fact classes beyond the ratified auction-amount set;
canonical-branch changes; the 2019/2020 FAAB back-fill; the 2018 de-contamination itself (Unit A9);
frontend changes (the engine emits `external_source`; the visible ATTESTED render label is a later
frontend unit).
