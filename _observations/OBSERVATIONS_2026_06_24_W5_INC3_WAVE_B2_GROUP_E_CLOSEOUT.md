# OBSERVATIONS 2026-06-24 - W.5 Inc 3 Wave B2 Group E (#23 The Lifeline) - CLOSE-OUT

**Lane:** EXECUTE. **Engine:** from `338de9b` (Group D). **Spec:** `SquadVault_Group_E_Specification_2026_06_24.md`
(pins A-H ratified). Generator extension only - no schema change. **After #23, W.5 Inc 3 is COMPLETE.**

## What shipped
`scripts/gen_season_award_winners.py` extended with **#23 The Lifeline** (AWARDS now 18). The award: per
season, the franchise's highest regular-season STARTED production from a player it acquired in-season
(waiver / free agent / awarded blind bid). Generator-local additions:
- `_ACQ_CHANNELS` = `WAIVER_BID_AWARDED`, `TRANSACTION_FREE_AGENT`, `TRANSACTION_WAIVER` (Pin B). The raw twin
  `TRANSACTION_BBID_WAIVER` and all trade/IR/load-rosters/auction/draft/AUTO_PROCESS markers are excluded.
- `_nested` + `_first_added` - double-decode the transaction payload (`payload_json` -> `raw_mfl_json` JSON
  string -> nested dict) and read the first ADDED player.
- `_load_inseason_acquired` - the set of `(season, franchise, player)` acquired in-season, from
  **memory_events** (the transaction ledger; transactions are not canonicalized facts). This is a
  GENERATOR-LOCAL read in `scripts/` - the `check_no_memory_reads.sh` gate scans only `src/`, so prove_ci is
  unaffected. Verified the gate scope before building.
- `_load_started_by_franchise` - regular-season started production keyed PER franchise (Pin G), reusing the
  existing `_load_regular_season_weeks` (10-franchise rule) and `_is_starter`.
- Emit block (Pin E floor `starter_weeks >= 4`; per-franchise max started; C6 co-holders fold to
  `detail.co_player_ids`; silence where none qualify).

## Census (read-only, proved BEFORE the build)
The section-4 winner fingerprint reproduced EXACTLY (all 16 seasons; franchise/player/value/starts). The
week-floor is dropped per Pin D and verified floored == unfloored (per-franchise keying already prevents
cross-franchise leakage; per-week historical dates are not stored). Acquisition channels confirmed present in
memory_events (FREE_AGENT 1338, WAIVER 1328, WAIVER_BID_AWARDED 374; BBID twin 52 excluded).

## Proofs
- **Fingerprint (spec section 4) reproduced EXACTLY** - 16 single-winner rows, lowest floor 2012 (4 starts),
  hand-checks 2010/0006/4891=352.00/8, 2017/0005/5848=320.00/12, 2022/0002/14983=86.90/7,
  2025/0008/9431=171.60/6 all pass.
- **Counts: 256 rows / 18 awards** (was 240/17); Group E adds exactly 16 rows.
- **Additive:** the prior 17 awards' 240 rows are BYTE-IDENTICAL (zero change outside award_id 23).
- **Determinism:** JSON and seed re-run byte-identical. **Unique-key violations: 0** (all single-winner).
- ruff / mypy(src core + the script) / prove_ci green.

## Prod-apply (FOUNDER-gated; NO prod write this session)
Seed 004 now carries **18 awards** (the prior 17 byte-identical; #23 additive). Founder hand-applies the seed
ONCE - it SUBSUMES every prior pending seed-004 apply (idempotent FK-safe DELETE-then-INSERT; canonical text
codes, no hardcoded UUIDs). Provenance for 23: `engine:transaction-acquisition-derived`. Independent and still
separately pending: the migration 029->030 W-L/PF correction thread (NOT in Group E's path).

## State
**W.5 Inc 3 is COMPLETE** (all of Wave A + Wave B1 + Wave B2 sub-wave-1 + Groups C/D/E built) pending the
single 18-award seed-004 prod apply. No Wave B2 units remain. The Founder's Seal (#31) stays an attested
placeholder pending founder confirmation (separate from Wave B2). Carry-forward (not Group E's path): KP
2018/12171 auction finalize via the Manual Source Adapter; the 029->030 W-L/PF prod-apply reconciliation.

## Guardrails
Clean retrospective facts (production of completed-season pickups). Never a waiver-strategy recommender, FAAB
optimizer, or forward projection - no-analytics/optimization/prediction load-bearing. No FAAB amount surfaced
(definition (a)). Tone-care factual. Silence where no candidate clears the floor. memory_events read is
generator-local (scripts/), outside the src/ canonical boundary the gate protects.
