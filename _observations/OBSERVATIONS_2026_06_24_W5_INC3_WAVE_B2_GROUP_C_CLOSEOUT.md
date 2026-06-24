# OBSERVATIONS 2026-06-24 - W.5 Inc 3 Wave B2 Group C (Positional Awards #13-18) - CLOSE-OUT

**Lane:** EXECUTE. **Engine:** `main` extended from `68d4b6e` (branch `feat/w5-inc3-waveb2-groupc-positional`
`85bd3ee`). **Frontend:** from `d0e9a52` (branch `feat/w5-inc3-waveb2-groupc-seed` `000a124`).
**Spec:** `OBSERVATIONS_2026_06_24_W5_INC3_WAVE_B2_GROUP_C_SPECIFICATION.md` (memo 3 of 4). Option B ratified.

## What shipped
Six per-season positional awards extending `scripts/gen_season_award_winners.py`:
13 Signal Caller (QB), 14 Workhorse (RB), 15 Deep Threat (WR), 16 Tight Window (TE), 17 The Boot (PK),
18 The Wall (Def). For each season+position: the single best STARTED player by season total of started-week
scores, granted to that player's franchise, player named in `detail`. Reads ONLY `is_starter` + `score` +
the `player_directory` position join (NOT `opt`/`raw_ok` - those are Group A). No new table, no schema change,
no migration (028 already prod-live). No engine-core change, no verifier change.

## STEP 1 census (gating) - result
`player_directory` carries MFL's full NFL roster DB (incl. IDP positions LB 5764 / CB 4374 / S / DE / DT, plus
Coach/PN/TM*/ST/Off/XX). The decisive test is what the league STARTS. Among `is_starter=1` player-weeks the
positions are EXACTLY: WR 5713, RB 4393, QB 2351, **Def 2346**, **PK 2341**, TE 2242 - **0 unresolved, no IDP
position ever started.**
- (a) Kicker string CONFIRMED literal `PK`.
- (b) Team-defense string CONFIRMED literal `Def` (the league starts a team-defense unit, not IDP).
- (c) NO IDP-defense era -> no HALT; `POSITION_AWARDS` map keys frozen as `{QB,RB,WR,TE,PK,Def}` unchanged.

## Coverage ledger (silence-render)
All 96 position-seasons (6 positions x 16 seasons 2010-2025) have started rows -> **0 silence-rendered**.
Group C emits 97 rows (96 + one same-season co-holder tie at #17 PK 2017). The silence path (`continue` on an
empty position-season) is implemented + correct but never fires on this league's data.

## Proofs
1. **Determinism:** generated twice -> byte-identical JSON + seed.
2. **Unique key:** 0 violations of `(award_id, season, franchise_id)` across all 216 rows.
3. **Additive non-regression:** awards 4/12/33/3/6/7/9 byte-identical to the pre-change seed (119 rows) -
   Group C perturbs nothing.
4. **Hand-checks (vs known fantasy facts):** all-time #13 QB = Drew Brees 2011 724.0 (SQL-verified the top
   started-QB season total); #14 RB = Christian McCaffrey 2019 369.1; #15 WR = Cooper Kupp 2021 309.1. Trade
   split confirmed: players started by two franchises in one season (e.g. 2025 pid 11247 across 0007/0003) are
   credited per franchise-of-start by the `(franchise, player)` key - no special-casing.
5. **Coverage ledger:** above (none).
6. **Gates:** ruff clean; mypy `src/squadvault/core/` clean (71 files); `scripts/prove_ci.sh` green.

## Constitutional guardrails
- **No analytics / optimization / prediction.** Clean retrospective facts ("started [position] points, season
  total") - not a lineup recommender or forecast.
- **No engagement loop.** Boundary at the frontend surfacing layer (no return-nudges/streaks/FOMO on the
  positional trophies); the generator emits facts, the frontend displays the derived most-recent holder.
- **No verifier change.** Group C writes only `season_award_winners` (a frontend display surface, not recap
  prose). The recap verifier is untouched.
- **Silence over speculation.** Empty position-seasons emit nothing (never a guess or zero-holder).

## Prod-apply hand-off (FOUNDER-gated; NO prod write this session)
Prod `season_award_winners` currently holds ONLY the B1 awards (4/12/33). The regenerated 13-award `seed_004`
SUBSUMES the pending 7-award apply (idempotent DELETE-then-INSERT over the full AWARDS set; the 7 are
byte-identical), so the founder applies the 13-award `seed_004` ONCE via the Supabase SQL editor to bring prod
from 3 awards to 13. SEPARATE + still pending: `migration 029` (Wave A plaque flips on
`franchise_season_records` - a different table) remains its own hand-apply. Neither double-applies.

## Out of scope (later units)
Group D (#19-22 auction) and Group E (#23 waiver) per spec section 11. No schema work, no frontend logic
beyond the seed regen + apply.
