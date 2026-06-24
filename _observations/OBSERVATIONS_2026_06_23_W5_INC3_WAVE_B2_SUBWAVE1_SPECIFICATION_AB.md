# Trophy Room (Unit W.5) Increment 3 - Wave B2 - Sub-wave 1 Specification (Groups A + B) - DRAFT

**Prepared:** 2026-06-23. **Session type:** DECIDE. **Anchor:** engine `main` `d101b78`.
**Scope:** the four sub-wave-1 awards - #6 The Benchwarmer, #7 The Clairvoyant, #9 The Oracle (Group A, optimal-lineup), #3 The Hammer (Group B, margin). All SHIP all 16 seasons per the ratified framing.
**Extends:** `scripts/gen_season_award_winners.py` `build_awards` + `AWARDS`; the `season_award_winners` seed. No new table, no schema change, no engine-core change. The three B1 awards (#4/#12/#33) are untouched.
**Status:** Pins ratified 2026-06-23 - full-season scope (founder); the other four resolved by delegation (section 3). BUILD-READY.

## 1. Shared substrate and conventions (verified against the generator at d101b78)

- **Loaders to reuse:** `load_all_matchups(db, league)` -> `HistoricalMatchup(season, week, winner_id, loser_id, winner_score, loser_score, is_tie)` for margins/outcomes (#3, #9); the season `WEEKLY_PLAYER_SCORE` loader in `core/recaps/context/player_week_context_v1.py` (load-all-for-season, organized by franchise/player) for `is_starter`, `should_start`, `score`, `player_id`, `week` (#6, #7, #9). Confirm the exact field names at build; do not assume.
- **Emit pattern (match B1 exactly):** append `{"award_id", "season", "franchise_id", "value": round(x, 2), "detail": {...}}`; **co-holders on tie** (C6) by emitting one row per tied winner, as #4/#12 do. Output sorted `(award_id, season, franchise_id)`.
- **Optimal-indicator gate (A1):** Group A rows participate only where the raw `shouldStart` is parseable (in {'0','1'}). Coverage is 100% across all 16 seasons, so this excludes ~0 rows, but the computation is written to honor it (a row with empty raw `shouldStart` contributes to neither numerator nor denominator). `should_start == True` is the optimal-lineup indicator.
- **Regenerability / determinism:** these are per-season DERIVED grants (no custody ledger; C1-custody does not apply). The generator recomputes them deterministically from canonical events; re-running reproduces identical rows. Tie handling is multi-valued (C6), never a nondeterministic single pick.
- **Provenance:** keep the B1 seed shape; suggest `engine:lineup-derived` for #6/#7/#9 and `engine:matchup-lineup-derived` for #3 (confirm the column accepts per-award provenance).

## 2. Per-award specifications

### #6 The Benchwarmer (Group A; tone-care; no-optimization LOAD-BEARING)

**Definition (recommended).** Per franchise, the season total of points scored by players the optimal indicator wanted started but the manager benched: sum of `score` over `WEEKLY_PLAYER_SCORE` rows where `should_start == True AND is_starter == False`. The franchise with the highest total is the Benchwarmer.
**Computation.** For each (franchise, season): `bench_points = SUM(score) WHERE should_start AND NOT is_starter`, over the scoped weeks (section 3). Winner = max `bench_points`; co-holders on tie.
**value** = `round(bench_points, 2)`. **detail** = `{"bench_points": X, "weeks": N, "top_left_on_bench": [{"week", "player_id", "score"}, ... up to 3]}`.
**Guardrails.** No-optimization (load-bearing): this is a RETROSPECTIVE season-total FACT ("left the most points on the bench in 2023"). It MUST NOT compute or expose any forward-looking optimal-lineup suggestion, "set your lineup better" guidance, or per-future-week optimization. detail is historical only. Tone-care: factual, never mocking - no editorializing strings in detail.
**Alternative (flag, section 3):** (b) net points lost = optimal_score - actual_score per week, summed. Recommend (a) as it matches the taxonomy phrasing and needs no optimal-lineup-score reconstruction.

### #7 The Clairvoyant (Group A; C2 no-prediction)

**Definition (recommended).** Per franchise, the season rate at which actual starters were optimal starters: `optimal_starts / total_starts`, where `optimal_starts = COUNT(is_starter AND should_start)` and `total_starts = COUNT(is_starter)`, summed across scoped weeks. Highest rate = Clairvoyant.
**Computation.** For each (franchise, season): `rate = SUM_weeks(count[is_starter AND should_start]) / SUM_weeks(count[is_starter])`. Winner = max `rate`; co-holders on tie.
**value** = `round(rate, 4)` (a rate needs more than 2 dp; confirm format vs the B1 round-2 convention - section 3). **detail** = `{"optimal_starts": A, "total_starts": B, "weeks": N}`.
**Guardrails.** C2: a RETROSPECTIVE rate over completed `(lineup, optimal)` facts only - never a predicted-accuracy score, running forecast counter, or forecast-and-grade mechanic. No projection of future accuracy.
**Note.** The starts-based denominator (not all rostered player-weeks) is deliberate: counting obvious bench players inflates every franchise toward 1.0 and loses discrimination. (Alternative denominator flagged in section 3.)

### #9 The Oracle (Group A; C2 no-prediction)

**Definition.** Per franchise, the count of weeks the franchise LOST but its optimal lineup would have WON - consequence, not volume. An "Oracle week" is: the franchise is the (non-tie) loser of its matchup AND `optimal_score > opponent_actual_score`.
**Computation.** Join the franchise's per-week `optimal_score = SUM(score WHERE should_start)` with `load_all_matchups`. For each scoped week where `loser_id == franchise` and `not is_tie`: if `optimal_score(franchise, week) > winner_score` (the opponent's actual score), it is an Oracle week. `oracle_count = COUNT(Oracle weeks)`. Winner = max `oracle_count`; co-holders on tie.
**value** = `oracle_count` (integer, stored `round(.,2)`-compatible). **detail** = `{"oracle_weeks": [{"week", "actual_score", "optimal_score", "opponent_score", "opponent_franchise_id"}], "count": N}`.
**Guardrails.** C2: RETROSPECTIVE counterfactual over completed games ("lost N games the optimal lineup would have won in 2023") - never a forecast. `optimal_score >= actual_score` always (optimal is a valid lineup), so the flip condition is well-defined. Strict inequalities: actual loss (`loser_score < winner_score`) and optimal win (`optimal_score > winner_score`); an optimal tie is not a win.

### #3 The Hammer (Group B; margin)

**Definition (recommended = Option A, "most often").** The started player who, across the season, most often scored more than his franchise's winning margin - i.e., was decisive (without him, the franchise would not have won). Per (franchise, player): count scoped weeks where the franchise WON (non-tie), the player was `is_starter`, and `player_score > (winner_score - loser_score)`. The (franchise, player) with the highest count is the Hammer; granted to the franchise, player in detail.
**Computation.** For each won matchup (`winner_id == franchise`, not tie): `margin = winner_score - loser_score`. For each `is_starter` player on that franchise that week with `score > margin`, increment that player's decisive-week count. Across the league, find the global max count; emit a row for each (franchise, player) at the max (co-holders on tie, possibly across franchises).
**value** = `decisive_weeks` (integer). **detail** = `{"player_id", "decisive_weeks": N, "weeks": [{"week", "player_score", "margin", "opponent_franchise_id"}]}`.
**Guardrails.** Started players only (a benched score cannot have shaped the actual margin). Wins only (no winning margin exists in a loss/tie).
**Alternative (flag, section 3):** (B) single largest margin-exceeding score in one matchup. Recommend (A): "most often" denotes a tally, not a single instance.

## 3. Definitional decisions - RATIFIED 2026-06-23

1. **Temporal scope (all four): FULL SEASON, including playoffs** (founder-ratified). Consistent with B1's single-week superlatives and complete for a memory vault - a championship-game Hammer counts. Accepted tradeoff: deeper-playoff teams have more weeks to accumulate on the count/sum awards (#6/#9/#3); this is treated as part of the record, not a distortion to correct.
2. **#3 Hammer = Option A** (season tally of decisive weeks). "Most often" denotes a tally; a repeatedly-decisive player is the intended fact.
3. **#6 Benchwarmer = (a)** gross bench points of benched should-starts. Matches the phrasing; no optimal-score reconstruction; stays a clean retrospective fact.
4. **#7 Clairvoyant = starts-based rate** (`optimal_starts / total_starts`). The full-binary alternative inflates every franchise toward 1.0 and loses discrimination.
5. **#7 value = `round(rate, 4)`** so near-ties remain distinguishable.

All four computations in section 2 stand as the recommended definitions; "scoped weeks" throughout = full season.

## 4. Constitutional guardrails (consolidated)

- **No-optimization (load-bearing) - #6:** retrospective fact only; no forward-looking lineup tooling anywhere in the computation or detail.
- **C2 (no prediction) - #7, #9:** retrospective rate / consequence over completed facts; never a forecast, running counter, or grade-the-prediction mechanic.
- **Tone-care - #6:** factual detail only; no editorializing.
- **C6 - all four:** multi-valued on tie (co-holders), matching B1.
- **C1-custody:** N/A - per-season derived grants, no custody ledger.
- **Surfacing / no-engagement-loop (carry to the frontend).** These awards are clean retrospective facts; they earn return visits by being legible, true, and permanent - never by engagement machinery. When surfaced on the site, NO return-nudge notifications, streaks, FOMO, rival-alert push loops, or time-on-site optimization may be attached to them. "No engagement loops, ever" applies to the presentation layer as firmly as the no-optimization line applies to #6. (Recorded here so the boundary is on the record before frontend work begins.)

## 5. Generator changes (EXECUTE)

1. Extend `AWARDS` to `("4","12","33","3","6","7","9")` (sub-wave 1 adds 3/6/7/9).
2. In `build_awards`, after the B1 block, add a per-season loop that loads `WEEKLY_PLAYER_SCORE` (season loader) and reuses the already-loaded matchups, computing #6/#7/#9/#3 per the section-2 definitions, appending dicts in the B1 shape with co-holders on tie.
3. Apply the ratified section-3 choices (scope, Hammer/Benchwarmer/Clairvoyant definitions, value formats).
4. Regenerate the seed (`004_season_award_winners.sql`) - it already DELETEs+INSERTs by `award_id`, so the new ids extend idempotently; confirm the DELETE id-list includes the new ids.
5. The three B1 branches and their rows are not modified.

## 6. Acceptance / verification (the build must prove)

- Determinism: two runs produce byte-identical seed output.
- C6: a constructed tie yields co-holder rows, not one arbitrary winner.
- Guardrails: no forward-looking output anywhere; #7/#9 read only completed facts; #6 detail carries no editorializing.
- Sanity: spot-check one season per award against hand computation (e.g., a known optimal-lineup miss; a known close win where a star exceeded the margin).
- Scope: the chosen section-3.1 window is applied uniformly across all four.

## 7. Out of scope

- Group C (#13-18), Group D (#19-22), Group E (#23) - later sub-waves.
- The 2018 `DRAFT_PICK` de-contamination (Group D spec, marker-aware per the Manual Source Adapter Contract section 2/8) - does NOT touch sub-wave 1, which uses no DRAFT_PICK data.
- The 2021 manual import - separate adapter-build + calibration track.
- No engine/schema change beyond the generator + seed; no analytics/optimization/engagement/prediction.

## 8. Provenance / status

- Built on: the ratified Wave B2 framing (A/B SHIP all 16 seasons); the B1 generator pattern at d101b78; the existing matchup + player-score loaders.
- DRAFT. On ratification of the section-3 pins, this is one EXECUTE build unit (extend the generator, regenerate the seed, prove acceptance), B1-style.
