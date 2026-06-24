# OBSERVATIONS 2026-06-24 - W.5 Inc 3 Wave B2 Group D (Auction Awards #19-22) - CLOSE-OUT

**Lane:** EXECUTE. **Engine:** from `01a6096`. **Frontend seed:** `supabase/seed/004_season_award_winners.sql`.
**Spec:** `SquadVault_Group_D_Specification_2026_06_24.md` (build-ready, ratified). Generator extension only -
no schema change.

## What shipped
`scripts/gen_season_award_winners.py` extended with auction awards #19-22 (AWARDS now 17). Three new loaders
plus an emitter, all generator-local (engine-core untouched):
- `_load_resolved_picks` - marker-aware de-contam (drop `AUCTION_BID`, keep null-marker; 1.2) + canonical
  one-winner-per-`(season, player_id)` resolution (`occurred_at DESC, bid DESC, franchise_id ASC`; 1.3) +
  the constitutional contested report (1.4).
- `_load_regular_season_weeks` - the 10-franchise rule (1.7; no hardcoded week constant).
- `_load_started_anywhere` - regular-season started-anywhere production per `(season, player_id)`,
  trade-invariant (1.8).
- `_emit_pick_award` - one row per franchise (unique key `(award_id, season, franchise_id)` safe); a
  same-franchise co-holder tie folds to `detail.co_player_ids` (the Group C / Hammer idiom).

The four awards: #19 The Steal (max reg-season started ppd, `starter_weeks >= 6` guard, no bid floor);
#20 The Burning Money (highest bid with `starter_weeks == 0` and `bid >= 17`; silence when none;
SHAME_RECORD tone-care); #21 The Patience Premium (lowest dollars/started-points per franchise, zero-point
franchises excluded); #22 The Whale (max bid, co-holders).

## Census (read-only, proved BEFORE the build)
- **Contested: exactly one** - 2018/12171 (David Johnson, provisionally 0002 @ $67 by the resolution
  heuristic). Logged to stderr; the generator never treats it as authoritative. No additional contested case
  -> build proceeded. (12171 started and scored in 2018, so this resolution changes no award winner; it
  affects only 0002's #21 components, and 0002 is not the 2018 #21 winner.)
- **Coverage:** 7 auction seasons (2018-2020, 2022-2025); 2021 = 0 rows (off-platform FFLM, silence);
  2018 = 150 picks after dedup. Data-quality note (non-blocking): per-franchise pick counts 2018-19 = 15,
  2020 = 18, others = 17 - genuine, not a second contamination pocket.
- **Reg-season boundary** via the 10-franchise rule: weeks 1-13 (<=2020), 1-14 (2021+) - derived, not pinned.

## Proofs
- **Fingerprint (spec section 3) reproduced EXACTLY** - #19 all 7, #20 all 3 (+ 4 silent seasons), #21 all 7
  (at round-3), #22 all 7 (all-time Whale $76 co-held 0002/2019/13604 + 0002/2020/13130).
- **Additive:** the prior 13 awards' 216 rows are BYTE-IDENTICAL; Group D adds 24 rows -> 240 total.
- **Determinism:** JSON and seed re-run byte-identical. **Unique-key violations: 0.**
- ruff / mypy / prove_ci green.

## One precision pin (recorded, not a deviation)
#21's `value` is stored at **round-3**, not the round-2 of spec 1.11 - because the section-3 fingerprint is
round-3 (`0.127`) and round-2 would both mis-read the fingerprint (`0.13`) and FALSE-TIE 2024 (top two ratios
0.1271 vs 0.1272). Tie detection is on the RAW ratio (epsilon 1e-9); #19/#22 stay round-2. The fingerprint is
authoritative per the spec ("the generator output MUST match"), so round-3 follows the spec's own numbers.

## Prod-apply (FOUNDER-gated; NO prod write this session)
Seed 004 now carries 17 awards (the prior 13 byte-identical; Group D additive). Founder hand-applies the seed
(idempotent FK-safe DELETE-then-INSERT of awards 4/12/33/3/6/7/9/13-18/19-22; canonical text codes, no
hardcoded UUIDs). This supersedes the 13-award seed apply. Provenance for 19-22: `engine:auction-value-derived`.

## Carry-forward
- KP 12171 lookup finalizes the one contested 2018 row (provisional 0002/$67) via the Manual Source Adapter,
  later. Until then the provisional pick stands and is flagged in stderr at generation.
- #20 "never started in any game" variant is the recorded fallback if a future season yields a high-bid
  playoff-only stash above the $17 floor.
- Remaining W.5 Inc 3 award: Group E / #23 The Lifeline (in-season acquisition, nested
  `raw_mfl_json.$.timestamp`, 2021-2025).

## Guardrails
No analytics/optimization/prediction (#21 is a pure retrospective ratio, C3-cleared; #19 has no forward lineup
tooling). Facts immutable/append-only; narratives derived. Silence over speculation (non-auction seasons emit
nothing). compute_all_season_records / engine-core untouched - the four loaders are generator-local.
