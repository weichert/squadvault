# OBSERVATIONS 2026-06-24 - franchise_season_records W-L + PF Regular-Season Defect - CLOSE-OUT

**Lane:** EXECUTE. **Engine:** from `cfb9d87`. **Frontend:** from `9597110`. **Spec:**
`OBSERVATIONS_2026_06_24_FRANCHISE_RECORDS_WL_REGSEASON_DEFECT_SPECIFICATION.md` (v2 ratified). Anchor
adjudication `..._CHAMPIONSHIP_WEEK17_CANONICALIZATION_ADJUDICATION` section 9.3.

## The defect
`gen_franchise_records.build_records` sourced W-L / ties / points_for from `compute_all_season_records` over
ALL matchups, while points_against (`compute_extras`) already excluded the final. So the championship game
leaked into the two finalists' W-L and PF every season (champion +1 win, runner-up +1 loss, both PF inflated
by the final's score). This made `franchise_season_records` disagree with the recap verifier
(`_compute_season_record(regular_season_only=True)`): the verifier gave 0005/2024 = 10-6, the records 11-6.
Migration 029 propagated the 11-6 to prod.

## The fix (PF = A ratified - all 16 seasons)
LOCAL to `gen_franchise_records.build_records`: filter the input to the regular-season set before the shared
aggregator - `reg = [m for m in matchups if m.week < _champ_week(m.season)]; records =
compute_all_season_records(reg)`. W-L / ties / PF are now all regular-season, consistent with PA and the
verifier. `compute_all_season_records` (SHARED with the hall-of-fame archive) is NOT modified - only its input.
`compute_championship_roll` stays on the FULL matchups (the title is decided by the games filtered out).

## Census + proofs
- **Census:** exactly **32 finalist rows** differ (2/season x 16); champion -1 win, runner-up -1 loss, both PF
  -final-score; **ties never change; no non-finalist row changes**; only wins/losses/points_for columns move.
- **Determinism:** regenerate twice -> byte-identical JSON.
- **Hand-checks:** 0005/2024 11-6 -> **10-6**; 0001/2021 -> 10-6; 0004/2015 (pre-2021 finalist) 13-3 -> 12-3.
- **Regression test** (the missing guard): `Tests/test_gen_franchise_records_regseason_v1.py` - a synthetic
  2024 champion (10-6 regular + a wk17 title win) pins build_records to 10-6 not 11-6 and PF excluding the
  final; a non-finalist row is unchanged by the filter. Self-contained (monkeypatches load_all_matchups; the
  CI fixture has no league-70985 matchups).
- **ruff / mypy(core) / prove_ci:** green.

## Plaque-flip re-check (section 9.6) - realized == approved 10
The complete plaque sweep (NOT just the previewed Banner + Engine) found **10** changes, reconciled
artifact-vs-prior. The 2 Climb flips were surfaced + founder-sighted (the §9.6 re-confirm caught a second-order
derived read the preview undercounted). Approved + realized set:
- **#10 The Banner (win-pct ties, W-L-driven):** 2016 {0010}->{0006,0010}, 2019 {0002}->{0002,0005}.
- **#11 The Engine (max season PF, PF-driven):** 2010 0006->0002, 2015 0004->0009, 2016 0005->0002,
  2019 0005->0009, 2020 0002->0001, 2023 0009->0006.
- **#8 The Climb (YoY win-pct gain, W-L second-order):** 2012 0002->0008, 2015 0004->0005.
All other plaques (Cavallini, Floor, Iron Curtain, Perfect Storm, Sieve, Dynasty, Runner-Up, Executioner)
stable. The 3 already-applied 029 moves (Banner 2021/2024, Sieve 2025) unchanged by this unit.
**Total member-facing plaque consequence = 13** (3 prior 029 + 2 Banner ties + 6 Engine + 2 Climb).

## Verifier and generator now agree
On 2021+ records the recap verifier (`regular_season_only`) and `gen_franchise_records` both yield the
regular-season W-L (0005/2024 = 10-6). The contradiction that motivated this unit is closed.

## Prod-apply (FOUNDER-gated; NO prod write this session)
029 is live. **Migration 030** (`gen_supabase_rebuild --wl-correction`) is a TARGETED idempotent FK-SAFE
UPDATE of wins/losses/points_for across all 16 seasons (supersedes 029's W-L for 2021+, adds the 2010-2020
finalists; ties/PA/blowout untouched). Sequence: apply 030 -> run the proofs (`supabase/proofs/` section 4) ->
post the ONE consolidated league note (covers all 13 plaque changes; names Banner, Engine, and Climb).

## Guardrails
No analytics/optimization/prediction. No verifier change. No edit to compute_all_season_records (shared).
Append-only intact (derived-projection correction; ledger never in play). Silence over speculation.
