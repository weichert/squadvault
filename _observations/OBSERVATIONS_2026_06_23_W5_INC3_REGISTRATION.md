# Trophy Room (Unit W.5) Increment 3 - Grants / Accumulations / Fixed - Registration (memo 4 of 4) - DRAFT

**Date:** 2026-06-23
**Session type:** DECIDE (registration). No repo/DB writes. DRAFT for founder ratification + commit.
**Chain position:** memo 4 of 4 - closes the increment-3 chain.
**Anchors:** engine HEAD `0219b30` (verified this session); frontend `7e0ee94`.

---

## 1. What this registers

The increment-3 (Grants / Accumulations / Fixed) four-memo chain is complete:

1. Selection-prep - `OBSERVATIONS_2026_06_22_W5_INC3_SELECTION_PREP` (2026-06-22)
2. Decision-readiness - `OBSERVATIONS_2026_06_22_W5_INC3_DECISION_READINESS` (2026-06-22)
3. Specification - `OBSERVATIONS_2026_06_23_W5_INC3_SPECIFICATION` (2026-06-23, reconstructed)
4. Registration - this memo (2026-06-23)

The chain spans two dates because the original memo-3 draft was lost with a prior session's container scratch and rebuilt this session against verified engine HEAD `0219b30` and direct inspection of the generator pipeline. Memos 1-2 are anchor-correct as drafted. Specified on memo-2 probe-confirmed data (the player domain is ingested at the engine), not guesses.

## 2. Binding decisions sealed

- **All 37 committed** (founder-ratified 2026-06-22): the Trophy Room will hold every artifact; the player/draft/waiver domain is committed, not deferred wholesale.
- **Staging (D2):** **Wave A** (8) - frontend-only off existing synced `franchise_season_records`, no migration. **Wave B1** (3) - introduces `season_award_winners`, fed by a weekly-score generator. **Wave B2** (15) - player-domain, sequenced after B1, each award gated on its D3 data-fact pin.
- **`season_award_winners` architecture (D1):** a compact per-`(award_id, season, franchise_id)` fact table, immutable/append-only, multi-valued on tie (C6), franchise references resolving by `(league canonical_id, canonical_franchise_id)` - no hardcoded UUIDs. **Spec call sealed in memo 3:** Wave A reads `franchise_season_records` directly (not blocked on the table); B1's three weekly-derived awards are the table's first tenants.
- **Provenance lesson applied (from increment 2):** the synced-fact generator (`gen_season_award_winners.py`) is born tracked under `scripts/`, and the data lands via an idempotent FK-safe seed transaction (the `gen_supabase_rebuild` idiom), not a row-by-row untracked push.
- **The Founder's Seal (#31) is founder-attested** (the Herlth/PFL provenance idiom, C7), corroborated by a 2010-2025 franchise-continuity check; it computes no winner and writes no `season_award_winners` row.
- **D3 gate:** each B2 award must be EXACTLY computable before its read ships; anything that is not DEFERS (registered, not rendered - the Unbroken Chain precedent).
- **Custody:** per-season grant / accumulating multi-list / fixed permanent. No manual `trophy_custody_events` writes (that ledger is the Belt's, increment 1).
- **Tone-care:** SHAME_RECORD artifacts (Sieve, Black Rose, Benchwarmer, Burning Money) render factually, never mockingly.

**Build pins registered (non-gating, resolved at build):** the One-Point Club margin threshold/inclusivity and winner-only-vs-both-finalists; the Supabase migration number (latest known 026, so approximately 027).

## 3. Registration landing (EXECUTE / doc session - repo writes, not this lane)

One topic per commit:

1. Commit the four increment-3 chain memos to `_observations/` - drop `_DRAFT`, and align filenames to the `W5_INC3_<STAGE>` stem (the spec draft was authored as `..._GRANTS_ACCUMULATIONS_FIXED_SPECIFICATION_DRAFT`; commit it as `W5_INC3_SPECIFICATION` for chain parallelism, unless the descriptive form is preferred - a trivial call).
2. STATE seating (section 4).
3. Docs-map registration if the gate requires it.
4. If a reusable audit query backed the memo-2 player-domain derivability probe, commit it under `scripts/audit_queries/` (the increment-2 pattern); otherwise the D3 per-award probes are Wave-B2 build-time.

## 4. STATE seating

Add one dated line: **"W.5 INCREMENT 3 (Grants/Accumulations/Fixed) SPECIFIED 2026-06-23 (DECIDE): four-memo chain complete; all 37 committed. Wave A = 8 frontend-only off `franchise_season_records` (Bridesmaid Bouquet, Sieve, Climb, Banner, Engine, Inaugural Champion, Back-to-Back, Perfect Storm), no migration. Wave B1 = 3 via new `season_award_winners` table (Cannon, Black Rose, One-Point Club) after a weekly-score generator + migration ~027. Wave B2 = 15 player-domain, gated on D3 (defer if not exactly computable). Founder's Seal = attested + continuity-corroborated. Build-ready; Wave A first."**

## 5. Build hand-off (after registration)

- **Wave A (EXECUTE, frontend-only):** eight derived reads off `franchise_season_records` + the Trophy Room sections/cards + multi-valued render. No migration. **Precondition:** a fresh prod object-existence probe confirming increment-2 Wave 2's `points_against` is applied in prod (The Sieve reads it).
- **Wave B1 (EXECUTE, engine + frontend):** `gen_season_award_winners.py` (born tracked) computes the three weekly-derived awards per season -> `season_award_winners` migration (~027, founder-applied, fresh prod object-existence probe first) -> idempotent seed -> three reads.
- **Wave B2 (EXECUTE, engine + frontend):** extend the generator with the player-domain computations that pass their D3 pin -> reads; D3 deferrals registered, not rendered. Its own EXECUTE arc, after B1.
- **Founder's Seal (#31):** attested plaque; the founder supplies the fact at build; the continuity check corroborates.

## 6. Constitutional carry

C1 (holder = derived read, never stored). C2 (Clairvoyant/Oracle: completed `(season, lineup, optimal)` facts only). C4 (The Climb). C6 (Perfect Storm + One-Point Club multi-lists; multi-valued on every tie). C7 (the attestation idiom reused for the Founder's Seal). Silence over speculation (D3 deferrals; the registered build pins). Tone-care for SHAME_RECORD artifacts. Boundary: no points / leaderboards / live-streak mechanics / prediction / analytics / engagement loop; append-only facts; human approves publication. Architecture frozen.

## 7. Provenance / status

DRAFT, DECIDE 2026-06-23. Closes the increment-3 four-memo chain. Pending founder ratification + commit; on ratification, the registration landing lands the chain + STATE (+ any reusable probe), then the Wave A build opens (EXECUTE) - frontend-only, low-risk, lighting up 8 plaques immediately.
