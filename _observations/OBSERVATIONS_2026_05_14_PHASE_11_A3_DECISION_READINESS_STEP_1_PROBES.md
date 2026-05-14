# Phase 11 A3 (Championship Timeline) Decision-Readiness Step 1 — Empirical Probes (D1 + D2)

**Date:** 2026-05-14
**Status:** Provisional / observational. No tier. Not registered in Documentation Map. Step 2 of the four-memo A3 chain (selection-prep → decision-readiness Step 1 → Step 2 → specification → registration).
**Filing precedent:** Tier 5 Live Observation Cadence Doctrine at `1cf4142`. Matches predecessor memo filings at `5a865a1` / `a1f4624` / `9093a07` / `ba8b58a` / `ba44ba4` / `fb4f827` / `582c3cf` / `cddcfb5` / `5291c46` / `3e9065f` / `2da7f21` / `d30a6a9` / `ee671da` / `24e63fa`.

**HEAD at probe-run:** `24e63fa` (A3 selection-prep memo). All gates passed at session start: pytest 2095 passed / 2 skipped; ruff clean in `src/`; mypy clean across 64 source files in `src/squadvault/core/`. Memory edit #25 baseline confirmed.

**Predecessors:**

- `bb0f325` — Reset Memo v1.0 (doctrinal source)
- `ba8b58a` — Phase 11 Surface Roadmap (chain pattern §4.1)
- `24e63fa` — A3 selection-prep memo (**direct upstream**; §4.2 candidate catalog; §6 diagnostic registration; §7.1 leading-hypothesis trio §4.2.1 + §4.2.2 + §4.2.4)
- `fb4f827` — A1 Step 1 probes memo (chain-step shape precedent)
- `2da7f21` — A2 Step 1 probes memo (**direct structural precedent** — most recent within-Phase-11 Step 1 deliverable)
- `cddcfb5` — A1 specification (Reading 1 / D3-Alpha / D4.1-Gamma / D4.2-Alpha / D5-Gamma inheritance source)
- `ee671da` — A2 specification (second-cycle inheritance confirmation)
- `642d6dc` — A1 `championship_roll.md` archive (Step 1 D2 alignment-check anchor)
- `src/squadvault/core/recaps/context/league_history_v1.py` — `load_all_matchups`, `HistoricalMatchup`; data-loader entry point exercised this session
- `src/squadvault/core/recaps/context/hall_of_fame_aggregations_v1.py` — `compute_championship_roll` (lines 220-317); structural read this session
- `src/squadvault/core/recaps/context/franchise_deep_angles_v1.py` — D39 `detect_championship_history` (lines 1248-1333), D50 `detect_the_almost` (lines 1407-1468); structural read + internal-logic replication this session

**Output:** Empirical confirmation (and qualification) of the substrate-coverage and historical-data-completeness priors named in the A3 selection-prep §6.1 (D1) and §6.2 (D2) diagnostics. Five D2 findings (α through ε); three D1 findings (one per leading-hypothesis sub-shape). Sub-shape readiness disposition for the in-scope leading-hypothesis trio. **One major substrate finding** (D2-γ: duplicate W17/W18 championship rows in post-2021 era, cause uncharacterized) that gates a §4.2.1 spec-stage presentation decision. **Six findings for Step 2** registered for the framing analysis to weigh. The largely-confirmatory expectation set in selection-prep §6.1 holds: A3 is the most-substrate-mature Phase 11 candidate at its own selection-prep moment, and the probe surfaces no v1-blocking unreadiness — but it does surface one spec-stage adjudication question and one threshold-calibration question.

---

## 1. §-content verification block — carry-forward

Per A3 selection-prep §2 and Roadmap §6.1: the doctrinal §-substance load-bearing on A3 selection is source-anchored in the predecessor chain. No fresh §-claim has surfaced during probe execution. Roadmap §7.5 source-access procedure not invoked.

**Confidence on carry-forward:** **High**.

---

## 2. Probe scope

**In-scope sub-shapes per A3 selection-prep §7.1 leading-hypothesis trio:**

- §4.2.1 — Per-season playoff bracket presentation (playoff-detection trick lift to multi-playoff-week scope)
- §4.2.2 — Cross-season playoff records (D39 cross-season aggregation lift)
- §4.2.4 — Bridesmaids and almosts (cross-season runner-up + D50 cross-season aggregation)

**Out-of-scope sub-shapes per A3 selection-prep §4.2 catalog and Anti-Drift §10 #3** (anchor, not forcing; Step 2 may elect to admit additional sub-shapes):

- §4.2.3 — Regular-season vs playoff record splits (D45 cross-season lift)
- §4.2.5 — Repeat-bracket-meeting patterns
- §4.2.6 — Title-game opponent records (absorbed by A1 per selection-prep §4.2.6)

**Empirical inputs to this session** (ephemeral probe at `/tmp/probe_a3_step1.py`; not committed):

- D2 SQL probes against `v_canonical_best_events` for league `70985`: per-(season, week) `WEEKLY_MATCHUP_RESULT` count distribution 2010-2025; per-season regular-season-mode + playoff-week extraction via the trick; bracket-shape (round-count) per season; 2020 → 2021 format-shift transition characterization; 2025 bracket reconstruction.
- D1 production-loader exercise: `load_all_matchups(db_path, league_id)` from `league_history_v1.py` invoked against the local sqlite; `compute_championship_roll` exercised on the full matchup set; generalized playoff-bracket extraction replicated (emit all playoff weeks, not just championship); D39 internal cross-season aggregation logic replicated with per-season set semantics; D50 detector dry-run at production `min_times=3` with synthetic 2026 week-gate; D50 internal logic replicated at `min_times=1` for full leaderboard; cross-era runner-up aggregation over `compute_championship_roll`'s `runner_up_id` column.

---

## 3. D1 substrate-coverage findings per in-scope sub-shape

All three in-scope sub-shapes consume the same canonical event type — `WEEKLY_MATCHUP_RESULT` — and the same `HistoricalMatchup` dataclass produced by `load_all_matchups`. The shared substrate is even more concentrated than A2's trio (which spanned `DRAFT_PICK` + `WEEKLY_PLAYER_SCORE` + `player_directory`). A3's trio is a pure-derivation sibling set on **one** canonical event stream. The playoff-detection trick (`_regular_season_matchup_count` + matchup-count filter; Architectural Audit §8 entanglement hotspot #3) is the shared analytical primitive across all three. **Confidence on shared-substrate finding:** **High**.

**Overall probe shape:** 1,182 `WEEKLY_MATCHUP_RESULT`-derived matchups loaded; 16 seasons present (2010-2025; no gaps); 16/16 seasons produce detectable championships via `compute_championship_roll`; 16/16 seasons produce detectable brackets via the generalized extraction. Substrate is dense and complete for the trio.

### 3.1 — §4.2.1 Per-season playoff bracket presentation

**Canonical event types consumed:** `WEEKLY_MATCHUP_RESULT` → `HistoricalMatchup` tuples via `load_all_matchups`.

**Existing aggregation primitive:** `hall_of_fame_aggregations_v1.compute_championship_roll` (lines 234-317). Uses the playoff-detection trick (`_regular_season_matchup_count` returns mode of per-week matchup counts; weeks with fewer matchups than the mode are playoff weeks; championship week is the playoff week with the fewest matchups, ties broken by latest week). A3 §4.2.1 generalizes this: emit *all* playoff-week matchups per season rather than narrow to the championship-week singleton.

**Render-readiness:** Adaptation required, smallest of the trio in computational scope. A new public function `compute_playoff_bracket(matchups) -> dict[int, tuple[BracketRound, ...]]` would generalize `compute_championship_roll` to emit per-season tuples of `(week, round_label, matchups_in_round)`. The within-trick logic is unchanged; the consumer-side narrowing-to-championship-week is what gets lifted. No new event types; no schema; no detector classes.

**Spot-check sample (PROBE D1.1):** Loaded 1,182 total matchups across 16 distinct seasons (2010-2025). Generalized extraction produced **detectable brackets for 16/16 seasons**. Bracket-shape distribution:

| # of playoff rounds | Seasons | Round-shape (matchups per round) |
|---|---|---|
| 3 | 2010-2020 (11 seasons) | W14:4 → W15:2 → W16:1 |
| 4 | 2021-2025 (5 seasons) | W15:4 → W16:2 → W17:1 → W18:1 |

**Sample render — 2025 bracket** (verification anchor per selection-prep §6.2):

- **W15 — Preliminary round (4 matchups):** 0002 176.90 def. 0004 125.25; 0003 119.80 def. 0001 114.75; 0005 101.55 def. 0007 100.15; 0009 142.05 def. 0006 135.75.
- **W16 — Semifinal (2 matchups):** 0002 162.20 def. 0009 111.25; 0005 131.80 def. 0003 127.25.
- **W17 — Championship (1 matchup):** 0002 139.40 def. 0005 118.65.
- **W18 — Championship (1 matchup):** 0002 139.40 def. 0005 118.65.

**Critical substrate finding surfaced:** **The post-2021 W17 and W18 championship rows are identical** — same winner (0002), same loser (0005), same scores (139.40 vs 118.65). This is uniform across all 5 post-2021 seasons (2021-2025) per the D2.3 distribution above; both rows always have exactly 1 matchup with verbatim-identical data. This is the substrate's actual state, not a probe artifact. **A1's `championship_roll.md` is unaffected** (the trick's championship-week tiebreaker picks the latest week, W18, and the data is the same game). But A3 §4.2.1's bracket presentation must adjudicate: render 3 played rounds (collapsing W17/W18 into a single "Championship" row), or render 4 rounds with admission of the duplication? Recorded as **finding D2-γ** in §4.3 below, with cause-candidates; spec-session adjudicates.

**Sub-shape readiness:** **High on substrate**; **gated on spec-stage W17/W18 presentation call.** Substrate is complete; the playoff-detection trick produces clean brackets across all 16 seasons; the generalization from `compute_championship_roll` is structurally trivial. The W17/W18 duplication is a presentation decision, not a substrate readiness issue. Promotes from selection-prep's "high based on structural read + A1-production-validation" to "high on substrate, with one spec-stage adjudication question surfaced."

**Confidence:** **High** on substrate completeness; **high** on the per-season generalization tractability; **medium-high** on the W17/W18 presentation call (multiple defensible options; spec adjudicates).

### 3.2 — §4.2.2 Cross-season playoff records

**Canonical event types consumed:** `WEEKLY_MATCHUP_RESULT` → `HistoricalMatchup`. Same as §4.2.1.

**Existing aggregation primitive:** `franchise_deep_angles_v1.detect_championship_history` (D39, lines 1248-1333). Already operates at cross-season scope within the playoff-week branch (lines 1268-1298 count `champ_appearances` and `playoff_appearances` per franchise across all `completed_seasons`). The current-week-must-be-playoff-week gate at lines 1259-1265 is a **consumption-side gate** for weekly-recap context, not a primitive-side limitation; A3's archive consumer lifts the cross-season aggregation independent of any current-week check.

**Render-readiness:** Adaptation required. Two distinct lifts:

1. **Appearance-count dimension:** Per-franchise `champ_appearances` and `playoff_appearances` across all 16 seasons. Trivial lift — D39 already does the aggregation; A3 exposes it as a sortable leaderboard rather than the divergence-threshold-filtered single-headline.
2. **Streak dimension:** Longest playoff-active and longest playoff-drought per franchise. Computational extension over the same per-season-playoff-participation matrix D39 produces internally.

**Spot-check sample (PROBE D1.2):** Cross-era per-franchise playoff records (replicated D39 internal logic with per-season set semantics; see §6.3 below for the per-matchup-vs-per-season semantics finding):

| Franchise | Playoff seasons | Champ-matchup appearances | Championships won | Runner-up |
|---|---|---|---|---|
| 0001 | 14 | 3 | 3 | 0 |
| 0002 | 14 | 7 | 4 | 3 |
| 0003 | 12 | 2 | 1 | 1 |
| 0004 | 12 | 3 | 1 | 2 |
| 0005 | 14 | 4 | 1 | 3 |
| 0006 | 11 | 3 | 1 | 2 |
| 0007 | 12 | 2 | 1 | 1 |
| 0008 | 12 | 3 | 0 | 3 |
| 0009 | 14 | 3 | 3 | 0 |
| 0010 | 13 | 2 | 1 | 1 |

**Per-franchise streak detection** (longest active playoff streak; longest drought; across all 16 active seasons):

| Franchise | Longest active streak | Longest drought |
|---|---|---|
| 0001 | 9 | 1 |
| 0002 | 12 | 1 |
| 0003 | 5 | 2 |
| 0004 | 5 | 2 |
| 0005 | 11 | 1 |
| 0006 | 4 | 2 |
| 0007 | 5 | 2 |
| 0008 | 8 | 2 |
| 0009 | 11 | 2 |
| 0010 | 7 | 1 |

**Cross-era observations** (substrate facts, not adjudicated):

- 0002 leads with 7 champ-matchup appearances (4 titles + 3 runner-up); the dynastic-frequency story.
- 0001 and 0009 tie at 3 titles each (with 0009 winning 3 of 3 championship matchups; 0001 winning 3 of 3); both also at 14/16 playoff seasons. Two "perfect in the title game" franchises.
- **0008 has 3 championship-matchup appearances and zero titles** — the perennial-bridesmaid archetype, narratively the densest "almost" story in PFL Buddies' substrate (also surfaces in §3.3 below).
- Playoff field is dense: every franchise made the playoffs ≥11 of 16 seasons. The longest drought across all franchises is 2 seasons; **no franchise has ever missed the playoffs 3 seasons in a row** in the digital era. This dampens the "long playoff drought" narrative dimension — recorded as §6.4 below.

**Sub-shape readiness:** **High.** Substrate complete; D39's cross-season aggregation tractable; appearance-count and streak-detection both clean.

**Confidence:** **High** on substrate readiness; **high** on appearance-count tractability; **medium-high** on streak-detection narrative density (mathematically clean; substrate-density dampens story-richness — §6.4 weighs).

### 3.3 — §4.2.4 Bridesmaids and almosts

**Canonical event types consumed:** `WEEKLY_MATCHUP_RESULT` → `HistoricalMatchup`. Same as §4.2.1.

**Existing aggregation primitives** (two-leg sub-shape per selection-prep §4.2.4):

1. **Runner-up leg:** Aggregation over `compute_championship_roll`'s `runner_up_id` column. NEW small derivation (not a D46 lift; see §6 selection-prep §10.2 finding). Structurally trivial: group `compute_championship_roll(matchups)` by `runner_up_id`, count.
2. **Almost leg:** `franchise_deep_angles_v1.detect_the_almost` (D50, lines 1407-1468). Already operates at cross-season scope (lines 1431-1455 count `almost_counts` across `completed_seasons`); detector surfaces franchises with `almost_counts[fid] >= min_times` (default 3). A3's lift renders the cross-era leaderboard.

**Render-readiness:** Both legs adaptation-required, but very different in shape:

- Runner-up leg: trivial new aggregation; pure group-by over `compute_championship_roll`'s output.
- Almost leg: detector dry-run at production threshold `min_times=3` returns **zero angles** for PFL Buddies' substrate. Detector internal logic replicated at `min_times=1` (any positive count) for full leaderboard; result is thin (see below). Spec-session must adjudicate whether to lower the threshold for A3's archive presentation, or whether to drop the almost leg from v1 entirely.

**Spot-check sample (PROBE D1.3b — runner-up leg):** Cross-era championship-runner-up leaderboard, all 16 seasons:

| Franchise | Runner-up count | Seasons |
|---|---|---|
| 0002 | 3 | 2014, 2021, 2024 |
| 0005 | 3 | 2016, 2019, 2025 |
| 0008 | 3 | 2012, 2015, 2022 |
| 0004 | 2 | 2017, 2023 |
| 0006 | 2 | 2010, 2018 |
| 0003 | 1 | 2011 |
| 0007 | 1 | 2020 |
| 0010 | 1 | 2013 |

**Eight distinct franchises** have appeared as championship runner-up across 16 seasons. The leaderboard's top three (0002, 0005, 0008) each have 3 runner-up finishes; **0008 has 3 runner-ups and zero titles** (cross-reference §3.2) — substrate-dense bridesmaid story. The runner-up leg is narratively rich.

**Spot-check sample (PROBE D1.3 / D1.3 — almost leg):** Full cross-era "one game out of playoffs" leaderboard at `min_times=1`:

| Franchise | Almost count |
|---|---|
| 0005 | 2 |
| 0001 | 1 |
| 0002 | 1 |
| 0007 | 1 |

**Only 4 distinct franchises** with any positive count across 16 seasons; max count per franchise is 2. **D50 production threshold `min_times=3` produces 0 angles** — the detector never fires for PFL Buddies' substrate. This is a thin almost-leg; see §6.2 for spec-session implications.

**Sub-shape readiness:** **Mixed.** Runner-up leg: **high readiness, dense substrate, narratively rich**. Almost leg: **low substrate density, requires threshold-lowering for any v1 presentation**, or drop from v1. Recommendation surfaced for Step 2 framing.

**Confidence:** **High** on runner-up leg readiness; **high** on the empirical thinness of the almost leg; **medium-high** on the spec-stage call (drop vs lower-threshold vs keep-asymmetric).

---

## 4. D2 historical-data-completeness findings

### 4.1 — WEEKLY_MATCHUP_RESULT coverage complete 2010-2025 (D2-α)

`WEEKLY_MATCHUP_RESULT` per-(season, week) coverage matrix for league 70985 across the digital era is **complete**: 16 seasons present, no inter-season gaps, no intra-season week gaps. Per-season week ranges:

- **2010-2020 (11 seasons):** W1-W16, all weeks present, regular-season weeks W1-W13 (5 matchups each) + playoff weeks W14 (4 matchups) + W15 (2) + W16 (1).
- **2021-2025 (5 seasons):** W1-W18, all weeks present, regular-season weeks W1-W14 (5 matchups each) + playoff weeks W15 (4) + W16 (2) + W17 (1) + W18 (1).

Total matchups loaded: 1,182. Distinct franchises: 10 (consistent 10-team league across all 16 seasons; no roster expansion or contraction).

**Contrast with A2 D2-α:** A2's auction substrate had a 7-of-8-seasons gap (2021 had zero `DRAFT_PICK` events); A3's matchup substrate has **no gap**. A1 Step 1's analogous probe established the same — `WEEKLY_MATCHUP_RESULT` is the most-mature canonical event substrate. A3 inherits this completeness directly.

**Ramification for the trio:** All three sub-shapes have clean substrate-data backing across all 16 seasons.

**Confidence:** **High** on completeness; **high** on the contrast with A2's drift-laden auction substrate.

### 4.2 — Pre-2021 vs post-2021 bracket-shape distribution (D2-β)

The 2021 NFL format-shift moved more than just the championship week. Two distinct PFL Buddies playoff-bracket shapes per the empirical distribution:

| Era | Seasons | Regular-season weeks | Playoff weeks | Championship week | Rounds |
|---|---|---|---|---|---|
| Pre-2021 (14-game NFL) | 2010-2020 (11) | W1-W13 | W14 (4) → W15 (2) → W16 (1) | W16 | 3 |
| Post-2021 (15-game NFL) | 2021-2025 (5) | W1-W14 | W15 (4) → W16 (2) → W17 (1) + W18 (1) | W18 (selected by trick) | 4 (3 + duplicate) |

**Three substantive observations:**

1. The post-2021 4-round shape includes a **duplicate** W17/W18 row pair where W17 and W18 are verbatim-identical. The post-2021 actual played bracket is 3 rounds (preliminary 4 → semifinal 2 → championship 1); the substrate stores the championship as both W17 and W18. Cause uncharacterized; recorded as **finding D2-γ** below (§4.3).
2. **A1 spec §3.7's format-shift normalization is single-week-scoped** — A1 only consumed the championship-week subset and the trick lands cleanly on W16 or W18 per era. A3 §4.2.1 consumes the entire bracket and must handle era-mixed bracket shapes (pre-2021: 3 rounds; post-2021: 3 played + 1 duplicate; or 4 rendered rounds). This is the spec-stage version of A1's framing-copy declaration (A1 spec §3.6) elevated to a bracket-structure declaration.
3. The cross-era leaderboards in §4.2.2 (appearance-counts, streaks) **naturally pool 3-round pre-2021 seasons with 4-round post-2021 seasons**. For "made the playoffs N seasons" this is clean — a playoff appearance is a playoff appearance regardless of bracket shape. For "made the championship matchup N seasons" the trick picks one championship row per season cleanly. For "made the semifinal N seasons" cross-era is computable (W15:2 pre-2021 and W16:2 post-2021 both have 2 matchups), but the bracket positions don't translate one-to-one (the W15:2 matchup pool is the entire field minus the W14 winners; the post-2021 W16:2 pool is the W15 winners only, after the preliminary round has narrowed). Semifinal-counting semantics is a spec-session normalization question.

**Confidence:** **High** on the empirical era-distribution; **high** on the 2021 format-shift's bracket-structure ramification; **medium-high** on the cross-era pooling normalization (multiple defensible semantics).

### 4.3 — Duplicate W17/W18 championship rows in post-2021 era (D2-γ) — *the substrate finding*

For each of the 5 post-2021 seasons (2021-2025), the `WEEKLY_MATCHUP_RESULT` substrate contains two championship-format rows: W17 and W18, with **verbatim-identical winner_id, loser_id, winner_score, and loser_score**. Confirmed empirically for 2025 (sample render in §3.1); the pattern is uniform across the era per D1.1's bracket-shape distribution table.

**Cause is uncharacterized this session.** Three candidate explanations, in rough order of plausibility:

- **(a) MFL platform behavior**: The platform may store the championship game in both the "last regular-NFL-week" slot (W17) and the "league season end" slot (W18) as a calendar accommodation — the championship is played in NFL Week 17 (or league W17) and the league's "season-end" week is logged as W18 with the same result. This pattern is consistent with the post-2021 NFL calendar shift (15-game regular season) creating a layout where the championship's "week of play" and "week of record" differ. **Most likely candidate** given the data is verbatim-identical and the pre-2021 11-season era has zero such duplication.
- **(b) Ingest-time double-writing**: The MFL Platform Adapter may emit two `WEEKLY_MATCHUP_RESULT` events per championship for post-2021 seasons. Memory edit notes the adapter resolves PFL Buddies' history-chain via a single API call across 8 different MFL league IDs; the adapter's behavior on post-2021 championship rows is worth a structural read.
- **(c) Genuine W17 + W18 league design**: The league may have intentionally designed a "championship + championship-recap" two-week structure post-2021. **Lowest-plausibility** given the data is identical (a genuine two-week design would produce different scores in the two weeks, e.g., a two-game championship series).

**Affected surfaces:**

- **A1's `championship_roll.md` (`642d6dc`)** is **NOT affected.** The trick's championship-week tiebreaker (line 295: `min(week_counts, key=lambda w: (week_counts[w], -w))`) picks the latest week when tied on matchup count. For post-2021 seasons, W17 and W18 both have count=1, and W18 wins on `-w` (so W18 is picked). A1's existing surface row uses the W18 data, which is verbatim-equal to the W17 data — semantically unaffected.
- **A3 §4.2.1 bracket presentation IS affected.** A3 generalizes the trick to emit all playoff weeks per season. The naive generalization shows both W17 and W18 as separate championship rounds, which is presentation-incorrect (one was played, the other is a duplicate row). **A3 §4.2.1 spec must adjudicate.**

**Three spec-stage adjudication options:**

1. **Collapse-by-content** at the derivation layer: when two consecutive playoff weeks have identical (`winner_id`, `loser_id`, `winner_score`, `loser_score`) tuples, treat the later week as a duplicate and emit only the earlier week as the "Championship" round. This is a fully-deterministic derivation rule with no platform-knowledge dependency.
2. **Era-aware filter**: hardcode a rule that for post-2021 seasons, the W17 row is the canonical championship and the W18 row is suppressed. This is a platform-knowledge derivation rule that couples the surface to era-specific MFL behavior.
3. **Admit both rows** in the bracket presentation, with a framing-copy note (analog to A1 spec §3.6's digital-era declaration). The bracket rendering shows the championship played twice as a substrate-honest depiction.

**Recommendation (anchor for Step 2):** Option 1 (collapse-by-content) is the only fully-deterministic choice that doesn't couple A3's surface to platform-knowledge. The pattern would emit a single "Championship" row across both eras. **Option 1 is what selection-prep §3.3 / Reset Memo §2.3 "silence over speculation" defaults to** — the substrate has redundancy; the derivation collapses redundancy cleanly. But Step 2 may surface considerations favoring (2) or (3); the recommendation is an anchor, not a forcing.

**What does NOT need to happen at A3's level:** investigating the substrate-origin of the duplication. That work belongs to either the adapter test surface or a Phase 12 ingest-audit observation, not A3's spec. A3 must produce a clean presentation given the substrate's current state; substrate-fix is independent. **Recorded for Step 2 framing.**

**Confidence:** **High** on the empirical duplication finding; **medium** on cause-candidate (a) being most-likely; **high** on the A1-unaffected diagnosis; **high** on the A3-affected diagnosis; **medium-high** on the Option-1-collapse-by-content recommendation (multiple defensible choices; spec adjudicates).

### 4.4 — compute_championship_roll output alignment with A1 archive (D2-δ)

The probe ran `compute_championship_roll(matchups)` against the full 1,182-matchup substrate. Output: 16 championship rows covering 2010-2025, no gaps. Per-row data:

| Season | Champion | Runner-up | Champ wk | Champ score | Runner score |
|---|---|---|---|---|---|
| 2010 | 0007 | 0006 | W16 | 129.50 | 97.50 |
| 2011 | 0009 | 0003 | W16 | 137.00 | 92.00 |
| 2012 | 0002 | 0008 | W16 | 142.00 | 105.50 |
| 2013 | 0009 | 0010 | W16 | 95.00 | 94.00 |
| 2014 | 0001 | 0002 | W16 | 62.50 | 50.00 |
| 2015 | 0004 | 0008 | W16 | 118.00 | 92.50 |
| 2016 | 0010 | 0005 | W16 | 107.00 | 100.00 |
| 2017 | 0003 | 0004 | W16 | 72.95 | 63.35 |
| 2018 | 0001 | 0006 | W16 | 133.65 | 108.45 |
| 2019 | 0002 | 0005 | W16 | 109.85 | 108.40 |
| 2020 | 0002 | 0007 | W16 | 140.30 | 82.65 |
| 2021 | 0001 | 0002 | W18 | 132.75 | 107.80 |
| 2022 | 0006 | 0008 | W18 | 114.60 | 108.35 |
| 2023 | 0009 | 0004 | W18 | 126.35 | 102.30 |
| 2024 | 0005 | 0002 | W18 | 148.90 | 135.80 |
| 2025 | 0002 | 0005 | W18 | 139.40 | 118.65 |

**Alignment check:** Output structure matches A1's `championship_roll.md` (`642d6dc`) by-row: same season range (2010-2025), same champion column, same runner-up column, same championship-week column (W16 pre-2021, W18 post-2021), same score columns. A1's archive is a render of this exact tuple set. **A1-A3 substrate primitive sharing is empirically confirmed** — both surfaces consume `compute_championship_roll`'s output; A1 renders the championship-week-only view; A3 (per §4.2.1) renders the full bracket including the rounds before championship week. The boundary documented in A3 selection-prep §3.1 (substrate-shared / presentation-disjoint) is **substrate-confirmed**.

**Substrate-density observations** (not adjudicated; recorded for spec session):

- **2014 championship** has unusually low scores (62.50 vs 50.00). Likely reflects a low-scoring NFL Week 16; substrate-correct. Worth framing-copy attention.
- **2013 championship** was a 1-point game (95.00 vs 94.00). Substrate-tightest championship in the era; narrative-rich. Worth framing-copy attention.
- **2019 championship** was a 1.45-point game (109.85 vs 108.40). Second-tightest. Worth framing-copy attention.

**Confidence:** **High** on the 16/16 alignment; **high** on the A1-A3 substrate sharing; **high** on the tight-championship substrate facts.

### 4.5 — 2025 bracket reconstruction (D2-ε) — *verification anchor*

Per A3 selection-prep §6.2 verification-anchor designation, the 2025 bracket was reconstructed from the substrate. Result matches league memory (and A1's `championship_roll.md` row for 2025 — 0002 def. 0005, 139.40 vs 118.65 at W18):

- **W15 — Preliminary round (4 matchups):** 0002 def. 0004 (176.90 vs 125.25); 0003 def. 0001 (119.80 vs 114.75); 0005 def. 0007 (101.55 vs 100.15); 0009 def. 0006 (142.05 vs 135.75).
- **W16 — Semifinal (2 matchups):** 0002 def. 0009 (162.20 vs 111.25); 0005 def. 0003 (131.80 vs 127.25).
- **W17 — Championship (1 matchup):** 0002 def. 0005 (139.40 vs 118.65).
- **W18 — Championship (1 matchup, identical to W17):** 0002 def. 0005 (139.40 vs 118.65).

**Verification disposition:** The bracket is **reconstructible from substrate alone** for the actual played rounds. The W17/W18 duplication is recorded in §4.3. Sub-shape §4.2.1 has clean substrate backing for the played-rounds presentation; the duplication is a presentation-layer adjudication, not a substrate-readiness issue.

**Cross-check observations**:

- 2025 W15 had **two single-digit-margin upsets** (0003 over 0001 by 5.05; 0005 over 0007 by 1.40); 2025 W16 had a 4.55-point semifinal (0005 over 0003). The 2025 bracket was bracket-narratively dense — alignment with A3 selection-prep §10.1's reference to 2025 as the most-attended-to recent season per A1 spec §3.5.
- The 0002 → 0005 → 0007 elimination chain across W15 + W16 + W17 (0007 lost to 0005 in W15; 0005 won the semifinal; 0005 lost the championship to 0002) is the kind of bracket-arc A3's §4.2.1 surface presentation makes visible at archive resolution.

**Confidence:** **High** on the substrate-anchored bracket reconstruction.

---

## 5. Sub-shape readiness disposition

Per A1 Step 1 §5 and A2 Step 1 §5 precedent framework:

| Sub-shape | Selection-prep §4.2 rating | Post-probe rating | Disposition |
|---|---|---|---|
| §4.2.1 Per-season playoff bracket presentation | High (structural-read) | **High (empirical)** | **Ready for v1 spec.** Adaptation: generalize `compute_championship_roll` to emit all playoff weeks; collapse-by-content for post-2021 W17/W18 duplication (Option 1 anchor per §4.3). |
| §4.2.2 Cross-season playoff records | High (structural-read) | **High (empirical)** | **Ready for v1 spec.** Adaptation: lift D39's internal cross-season aggregation with per-season set semantics (not D39's per-matchup over-counting); streak-detection extension is small. |
| §4.2.4 Bridesmaids and almosts | Medium-high (structural-read) | **Mixed (high runner-up leg, low almost-leg density)** | **Ready for v1 spec; one threshold-or-drop adjudication.** Runner-up leg: dense substrate, narratively rich, ready. Almost leg: D50 production threshold (`min_times=3`) produces zero PFL Buddies angles; full leaderboard at `min_times=1` is thin (4 franchises). Step 2 / spec adjudicates lower-threshold vs drop-from-v1. |

**The selection-prep leading-hypothesis trio confirms as ready for v1 spec across all three sub-shapes.** None of the three lands as "not ready." Three spec-stage adjudications surfaced:

- **§4.2.1 W17/W18 presentation** (§4.3 anchor: Option 1 collapse-by-content).
- **§4.2.2 per-matchup-vs-per-season semantics** (§3.2 / §6.3 anchor: per-season set semantics, not D39's internal per-matchup).
- **§4.2.4 almost-leg threshold-or-drop** (§3.3 anchor: spec-stage adjudication; substrate-density supports either choice; framing-copy-honest choice favors lower threshold OR clean drop).

Plus the universal **format-shift bracket-shape framing-copy caveat** (§4.2; spec-stage display disposition; analog to A1 spec §3.7's format-shift normalization elevated to bracket-structure scope).

**Confidence on dispositions:** **High** for §4.2.1, §4.2.2 readiness (probe-confirmed); **mixed** for §4.2.4 (runner-up leg confirmed; almost leg empirically thin; spec-stage adjudication necessary).

---

## 6. Findings for Step 2

Six findings surfaced during probe execution that should inform Step 2's framing analysis (D3 GAF / lore-pick framing, D4 operational rhythm). Each is registered as a fact, not a recommendation; Step 2's framing-pass adjudicates.

### 6.1 — W17/W18 duplication ramifications for §4.2.1 spec (the substrate-finding)

The duplication finding (§4.3) is the most substantive Step-1 → spec-session input. Three adjudication options surfaced:

1. Collapse-by-content (preferred anchor per §4.3 reasoning — fully-deterministic; no platform-knowledge).
2. Era-aware filter (couples surface to MFL-adapter-era behavior).
3. Admit both rows + framing-copy note (substrate-honest depiction with redundancy).

The spec session decides. **Step 2's job is to weigh these against the artisan-frame and Voice-Profile-§5 framing**, not to add a fourth option. The selection-prep §3.3 silence-over-speculation default + Reset Memo §2.3 substrate-derivation discipline both point toward Option 1.

**Step 2 weighing input:** The substrate's redundancy is presentation-incoherent (two championship rounds, same data). A bracket presentation honoring league memory shows the championship played once. Option 1 is the natural fit unless Step 2's framing-pass surfaces a substantive reason to break silence.

### 6.2 — D50 production threshold too high for PFL Buddies substrate

`detect_the_almost(min_times=3)` produces **zero angles** across PFL Buddies' 16-season substrate. Max `almost_counts` per franchise is 2 (franchise 0005). The detector's `min_times=3` default appears to be calibrated for either (a) a longer league history, (b) a different league dynamics regime where playoff fields are less dense, or (c) a generic-recap default that doesn't fit PFL Buddies' actual narrative density.

**Spec-session implications for §4.2.4 almost-leg:**

- If §4.2.4's almost-leg is admitted to v1, the threshold MUST be lowered (probe used `min_times=1` and surfaced 4 franchises; even `min_times=2` would surface only franchise 0005). The display at `min_times=1` is a 4-row table.
- Alternatively, drop the almost-leg from v1 and ship §4.2.4 as a single-leg (runner-up-only) sub-shape. Runner-up leg is dense (8 franchises; 16 rows of source data); the resulting presentation is narratively complete.

**Step 2 weighing input:** The runner-up leg is the substantively-richer leg empirically. The almost-leg's thinness is a substrate fact, not a presentation fix-able problem. Both choices are defensible; the spec adjudicates against §9.2 artisan-frame fit.

**Side observation:** D50's production-side default fires only at `min_times=3` in real recap context; this means **D50 has been silent across PFL Buddies' entire production history** to date. This is a separate find — D50 may be candidate for either a calibration revisit (Phase 10 / Tier 5 observation territory) or admission that the detector is unfit-for-purpose for this league's density. **Out-of-scope for A3; recorded for cross-cluster carry-forward** (selection-prep §9.2).

### 6.3 — D39 internal `playoff_appearances` per-matchup counting (silent semantics)

D39 (`detect_championship_history`) builds an internal `playoff_appearances: dict[str, int]` at lines 1284-1287:

```python
for m in playoff_weeks:
    playoff_appearances[m.winner_id] = playoff_appearances.get(m.winner_id, 0) + 1
    playoff_appearances[m.loser_id] = playoff_appearances.get(m.loser_id, 0) + 1
```

This increments **per-matchup**, not per-season. A franchise that wins in W14 and loses in W15 of a single pre-2021 season would get `playoff_appearances += 2`. The semantically-intended "made the playoffs N seasons" count would be `+= 1` for that season.

**The over-counting is silent in production** — D39's surfaced angles (lines 1305-1326) read only `champ_appearances`, never `playoff_appearances`. The internal dict is computed-but-unused; the bug is latent.

**Ramification for A3 §4.2.2 spec:** A3's lift must NOT directly consume D39's `playoff_appearances` dict. The probe's §3.2 replication used per-season set semantics (`season_playoff_fids: set[str]`; increment counter once per franchise per season). The §4.2.2 spec MUST specify per-season semantics; the spec note prevents future maintainers from "fixing" the count by importing D39's internal logic and inheriting the over-counting.

**Step 2 weighing input:** This is a substrate-side finding. Not blocking A3's spec; in fact, A3 is a forcing-function for clarifying D39's intended semantics if D39 is ever refactored to surface `playoff_appearances`. **Recorded; not adjudicated this session.**

### 6.4 — Dense playoff field dampens streak-detection narrative

PFL Buddies' playoff field is dense:

- Every franchise made the playoffs ≥11 of 16 seasons.
- Longest playoff-drought is 2 seasons (six franchises); no franchise has ever missed the playoffs 3+ seasons in a row.
- Longest active streak ranges 4-12; only 4 franchises have active streaks <7.

**Ramification for §4.2.2 spec:** Streak detection (longest playoff-active; longest playoff-drought) is mathematically clean, but the streak-numbers are narratively dampened by the dense field. "Franchise 0006's 4-year streak" is true but doesn't carry the same narrative weight as a streak in a league where droughts of 5-10 years are common.

**Step 2 weighing input:** Three spec-stage options:

- **Surface both dimensions** (active + drought); admit that the league's playoff-field density is part of its identity. Voice-Profile §5 framing.
- **Surface only the active dimension** (the dynastic-frequency story is densely realized; 0002's 12-season streak is real and notable).
- **Drop streaks from v1**; ship §4.2.2 as appearance-counts-only.

The "appearance-counts-only" option is the most-substrate-conservative; streaks-and-appearance-counts is the most-substrate-complete; appearance-counts-plus-active-streak is a hybrid. **Step 2 framing-pass adjudicates.**

### 6.5 — Cross-era bracket-shape mixing (3-round pre-2021 vs 4-round post-2021)

§4.2 / §4.2.2 cross-era leaderboards naturally pool 3-round pre-2021 seasons with 4-round post-2021 seasons. For most dimensions this is clean:

- **Playoff seasons count**: clean — a playoff appearance is a playoff appearance regardless of bracket shape.
- **Championship-matchup count**: clean — the trick picks one championship row per season.
- **Championship-wins count**: clean — same primitive as A1.
- **Runner-up count**: clean — same primitive.
- **Active/drought streaks**: clean — same per-season-binary participation matrix.

**One dimension is non-trivial: "made the semifinal" count.** Pre-2021 W15:2 and post-2021 W16:2 both have 2 matchups (the 4 surviving teams play in 2 matchups for 2 spots in the championship). The bracket-positions correspond loosely (both are "round before championship"). But:

- Pre-2021: the semifinal is the **second** playoff round (after W14 narrows 10 → 8).
- Post-2021: the semifinal is the **third** playoff round (after W15 narrows 10 → 8 → 6, then W16 narrows 6 → 4).

Wait — re-examination needed. Pre-2021 W14 has 4 matchups (8 teams play; some bye-into-W15?). Post-2021 W15 has 4 matchups (8 teams play). Both eras have 8 teams in the first playoff round; the post-2021 era adds a fourth round (W18 duplicate of W17). **Per the substrate, both eras' bracket-paths have the same logical shape: 8 teams → 4 teams → 2 teams → 1 champion.** The "extra" post-2021 round is the W17/W18 duplication (§4.3), not a structurally-different bracket size.

If §4.3's Option 1 collapse-by-content is adopted, **the eras share identical bracket-structure semantics**:

- Round 1 (preliminary): 4 matchups, 8 teams play.
- Round 2 (semifinal): 2 matchups, 4 teams play.
- Round 3 (championship): 1 matchup, 2 teams play.

The week-labels differ (W14/15/16 pre-2021; W15/16/17 played + W18 duplicate post-2021), but the bracket-position semantics are stable. **Cross-era pooling is clean under Option 1.**

**Step 2 weighing input:** §4.3 Option 1 simplifies §4.2 cross-era pooling. Adopting Option 1 makes the cross-era leaderboards (§4.2.2 appearance-counts; §4.2.4 runner-up counts) bracket-position-coherent across both eras. This is a non-trivial argument for Option 1 over Options 2/3 from §4.3.

### 6.6 — Substrate-density observations (championship scores; bracket tightness)

Three substrate facts worth framing-copy attention at the spec session (not adjudicated; substrate-honest depictions):

- **2014 championship** had unusually low scores: 62.50 vs 50.00. ~50-60% of the era's typical championship score (most are 90-150). Likely reflects a low-scoring NFL Week 16; substrate-correct.
- **2013 championship** was a **1-point game** (95.00 vs 94.00). Substrate-tightest championship in the digital era. Voice-Profile §5-resonant moment.
- **2019 championship** was a **1.45-point game** (109.85 vs 108.40). Second-tightest. Narrative-rich.

These are bracket-honest facts that a spec-stage framing-copy pass should attend to (the "highlights row" or "notable championships" sidebar pattern, analog to A1 spec §3.4's spectacular-mode pattern). **Step 2 surfaces; spec adjudicates content.**

---

## 7. Confidence labeling — summary

**Highest-confidence findings:**

- WEEKLY_MATCHUP_RESULT coverage complete 2010-2025 (D2-α; 1,182 matchups; no gaps).
- Two distinct bracket shapes in the digital era: 3-round pre-2021, 4-round post-2021 (D2-β; uniform within era).
- Duplicate W17/W18 championship rows in all 5 post-2021 seasons (D2-γ; verbatim-identical data).
- `compute_championship_roll` produces 16/16 detectable championships matching A1's archive (D2-δ).
- 2025 bracket reconstruction matches league memory (D2-ε).
- Sub-shape readiness for §4.2.1 and §4.2.2 (D1.1 + D1.2).
- §4.2.4 runner-up leg is dense and narratively rich (D1.3b).
- §4.2.4 almost-leg is thin: 4 franchises with positive counts; max count = 2; D50 production threshold (`min_times=3`) produces zero angles (D1.3).

**Medium-high confidence findings:**

- The duplicate W17/W18 cause-candidate (a) — MFL platform stores championship at both "week of play" and "season-end week" — is most-likely but uncharacterized (§4.3).
- §4.3 Option 1 (collapse-by-content) is the spec-stage anchor recommendation (§4.3, §6.1, §6.5).
- §4.2.2 streak-detection narrative is dampened by dense playoff field (§3.2, §6.4).
- §4.2.4 spec-stage almost-leg adjudication: lower-threshold vs drop (§3.3, §6.2).

**Medium confidence findings:**

- Cause-candidate ordering for D2-γ (cause (a) > (b) > (c); the order is plausible but uncharacterized).
- D39's silent per-matchup over-counting is a future-maintainer hazard (§6.3); not blocking.
- D50's production-side silence across PFL Buddies' entire history (§6.2 side observation); recorded for cross-cluster carry-forward.

**Confidence floor (limitations to flag):**

- Cause of D2-γ duplication is not characterized this session. Investigation is out-of-scope for A3 — substrate-fix is independent of A3's spec.
- Cross-era bracket-position semantics depend on Option 1 adoption (§6.5).
- Streak-detection's narrative dampening is a substrate-density argument; reasonable observers could disagree on whether to surface streaks in v1.

---

## 8. Chain disposition

A3 decision-readiness Step 1 (chain step 2 of 4) is **complete**. All five diagnostics from A3 selection-prep §6 have empirical resolution or registered findings:

- **D1 substrate-coverage per sub-shape**: discharged. Trio ready for v1 spec; three spec-stage adjudications surfaced (§5).
- **D2 historical-data-completeness**: discharged. Coverage complete; one major substrate finding (D2-γ W17/W18 duplication); five sub-findings α-ε.
- **D3 GAF / lore-pick framing**: deferred to Step 2 (§6 findings inform).
- **D4 operational rhythm**: deferred to Step 2.
- **D5 meta-surface question**: dissolved by Reading 1 inheritance per A3 selection-prep §6.5.

**Step 2 inputs registered** (per §6 findings):

1. W17/W18 duplication adjudication (Option 1 anchor; §6.1).
2. §4.2.4 almost-leg threshold-or-drop (§6.2).
3. §4.2.2 streak-detection narrative dampening (§6.4).
4. §4.2 cross-era bracket-position coherence depends on Option 1 (§6.5).
5. Substrate-density observations for framing-copy attention (§6.6).
6. D39 per-matchup over-counting (semantic hazard; non-blocking; §6.3).

**Chain advances:** "candidate-set characterized; diagnostics registered" → "candidate-set substrate-confirmed; spec-stage adjudications named; ready for Step 2 framing analysis."

**Next chain step:** A3 decision-readiness Step 2 — D3 framing analysis (Reading 1 inheritance reconfirmation; GAF / lore-pick framing; cluster-A artisan-frame fit) + D4 framing analysis (D4.1 cadence / D4.2 revision-point Alpha-vs-Beta election; D4.2-Beta candidate per selection-prep §8.2 substance-honesty argument).

**Sequencing:** Step 2 is doc-only memo; pattern matches A1 Step 2 (`582c3cf`) and A2 Step 2 (`d30a6a9`). No empirical work required for Step 2; the §6 findings here are the inputs. After Step 2, the spec session (chain step 4) authors A3's per-surface constitutional memo using template v1.0 at `5291c46`.

---

## 9. Cross-references

- `bb0f325` — Reset Memo v1.0 (doctrinal source; §2.3 silence-over-speculation; §8.4 source-anchoring)
- `ac96447` — Documentation Map v1.6 (registry; Tier 0V — Vision Source)
- `46736a0` — Map v1.6 §4.2 patch
- `1cf4142` — Tier 5 Live Observation Cadence Doctrine v1.0 (filing precedent)
- `5a865a1` — Phase 11 surface-selection memo (Cluster A admissibility source)
- `a1f4624` — Phase 11 decision-readiness memo (Disposition A; Cluster A carry-forward)
- `9093a07` — Phase 11 first-surface specification for E1
- `ba8b58a` — Phase 11 Surface Roadmap (§4.1 four-memo chain pattern; §2.2 admissible-set)
- `ba44ba4` — Phase 11 A1 selection-prep memo
- `fb4f827` — A1 Step 1 probes (chain-step precedent; format-shift source)
- `582c3cf` — A1 Step 2 (chain-step shape precedent for A3's next memo)
- `cddcfb5` — Phase 11 A1 specification (Reading 1 / D3-Alpha / D4.1-Gamma / D4.2-Alpha / D5-Gamma inheritance; §3.7 format-shift normalization precedent)
- `eb6042d` / `97c8bf0` / `642d6dc` — A1 implementation arc (A1 archive substrate-validation for §4.4 alignment)
- `5291c46` — Per-surface constitutional-memo template v1.0 (binds A3's spec at chain step 4)
- `3e9065f` — Phase 11 A2 selection-prep memo
- `2da7f21` — **Phase 11 A2 Step 1 probes memo (direct structural precedent — this memo mirrors its shape)**
- `d30a6a9` — A2 Step 2 (chain-step shape precedent)
- `ee671da` — Phase 11 A2 specification (second registered per-surface constitutional memo)
- `87ebdad` / `4f9c379` / `9189a7d` — A2 implementation arc
- `24e63fa` — **Phase 11 A3 selection-prep memo (direct upstream)**
- `PFL_Buddies_Voice_Profile_v1_0.md` §5 — championship and playoff-bracket language patterns (§9.2 anchor)
- `ARCHITECTURAL_AUDIT_2026_04_16.md` §8 entanglement hotspot #3 — playoff-detection trick characterization
- `Narrative_Angles_v2_Definitive_Scope.md` Dimension 9 — D36-D50 franchise-history detector family scope
- `src/squadvault/core/recaps/context/league_history_v1.py` — `load_all_matchups` (lines 214-271); `HistoricalMatchup` dataclass (lines 44-54); structural read this session
- `src/squadvault/core/recaps/context/hall_of_fame_aggregations_v1.py` — `compute_championship_roll` (lines 234-317); `_regular_season_matchup_count` helper (lines 92-117); A3 §4.2.1 generalization source
- `src/squadvault/core/recaps/context/franchise_deep_angles_v1.py` — D39 `detect_championship_history` (lines 1248-1333); D50 `detect_the_almost` (lines 1407-1468); A3 §4.2.2 and §4.2.4 substrate sources
- `archive/hall_of_fame_and_shame/championship_roll.md` (`642d6dc`) — A1's live championship roll; A3-A1 substrate-sharing confirmation source

---

*Filing: `_observations/OBSERVATIONS_2026_05_14_PHASE_11_A3_DECISION_READINESS_STEP_1_PROBES.md`.*
*Provisional / observational. No tier. No Map registration. Matches Tier 5 doctrine precedent at `1cf4142` and predecessor memo filings.*
