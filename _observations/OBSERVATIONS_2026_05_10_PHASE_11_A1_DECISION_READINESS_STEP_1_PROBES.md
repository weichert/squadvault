# OBSERVATIONS — Phase 11 A1 Decision-Readiness Step 1 (Empirical Probes: D1 + D2)

**Date:** 2026-05-10
**HEAD at memo-write:** `ba44ba4` (A1 selection-prep memo, this session's direct predecessor)
**Session brief:** `session_brief_a1_decision_readiness_step_1_probes.md`
**Predecessor memo:** `_observations/OBSERVATIONS_2026_05_10_PHASE_11_A1_SELECTION_PREP.md`
**Scope:** Probe-and-document. SQL probe against `.local_squadvault.sqlite` + ephemeral Python probe via `./scripts/py /tmp/probe_a1_step1.py` (not committed). Source-file reads of `league_history_v1.py`, `franchise_deep_angles_v1.py`, `narrative_angles_v1.py`. No code changes.
**Chain step:** Decision-readiness Step 1 of 2. Step 2 (framing analysis: D3 GAF / D4 cadence / D5 meta-surface) and adjudication will inherit these findings as predecessor evidence.

---

## 1. Section-content carry-forward

Per brief §1 and selection-prep §2: §-substance load-bearing on this session was source-anchored in the A1 selection-prep memo at `ba44ba4`. Carry-forward applies. No re-authoring of §-verification this session.

**Confidence on carry-forward:** **High** (predecessor at HEAD; no §-substance dispute surfaced during probe).

---

## 2. Probe scope

Four in-scope sub-shapes per selection-prep §4.2 and brief §2:

- §4.2.1 — Championship roll
- §4.2.2 — Worst-season tracking
- §4.2.3 — Blowouts hall
- §4.2.4 — Manager records (head-to-head)

Three out-of-scope sub-shapes (§4.2.5 GAF/lore moments; §4.2.6 trade history hall; §4.2.7 draft history hall) not probed this session per brief §2 and Anti-Drift §8.

Empirical inputs to this session:

- D2 SQL probe: per-season `WEEKLY_MATCHUP_RESULT` count against `v_canonical_best_events` for league `70985`.
- Informational DISTINCT probe of `canonical_events.event_type`.
- Ephemeral Python probe (`/tmp/probe_a1_step1.py`) exercising production functions: `load_all_matchups`, `compute_head_to_head`, `build_cross_season_name_resolver`, `compute_franchise_tenures`; plus inline aggregations mirroring `_compute_season_records` and the playoff-detection trick from `franchise_deep_angles_v1.detect_championship_history`.

---

## 3. D1 substrate-coverage findings per in-scope sub-shape

All four in-scope sub-shapes consume the same single canonical event type: `WEEKLY_MATCHUP_RESULT`, read from `v_canonical_best_events` at `league_history_v1.py:245-253` (the `load_all_matchups` SELECT). Parsed shape per `_parse_matchup` (`league_history_v1.py:171`): `HistoricalMatchup(season, week, winner_id, loser_id, winner_score, loser_score, is_tie, margin)`. The shared substrate read is a structural fact — the four sub-shapes are pure-derivation siblings on one canonical event stream.

**Confidence on shared-substrate finding:** **High**.

### 3.1 — §4.2.1 Championship roll

**Canonical event type consumed:** `WEEKLY_MATCHUP_RESULT`.

**Existing aggregation primitive:** `franchise_deep_angles_v1.py:1248` `detect_championship_history`. Implements the playoff-detection trick: regular-season matchup mode per season (`_regular_season_matchup_count` at `franchise_deep_angles_v1.py:1474`) identifies the regular-season-week pattern (5 matchups/week for a 10-team league); weeks with fewer matchups are playoff weeks; championship week is the playoff week with fewest matchups; matchup winner on that week is the champion.

**Render-readiness:** Adaptation required, ~30 lines. The detector internally identifies the per-season champion at lines 1289-1298 (`champ_matchups[0].winner_id` for each completed season) but its public output aggregates across seasons into "most appearances" / "never appeared" narrative angles, gated by `current_season` being in a playoff week. A1's archive view needs the per-season `(season, champion_id)` list, not the across-season appearance counts. New derivation function `compute_championship_roll(matchups) -> tuple[ChampionshipResult, ...]` would lift the per-season identification without modifying the existing detector. No new event types, no schema, no detector classes.

**Spot-check sample:** Full 16-season championship list returned by PROBE 1; founder confirmed the list looks right as best recalled. Probe-derived title leaderboard:

- Paradis' Playmakers — 4 (2012, 2019, 2020, 2025)
- Italian Cavallini — 3 (2011, 2013, 2023)
- Stu's Crew — 3 (2014, 2018, 2021)
- Brandon Knows Ball — 1 (2016)
- Plus six other single-title franchises (Robb's 2010, Eddie 2015, Purple Haze 2017, Miller 2022, Weichert 2024)
- Ben's Gods — 0 championships across 16 seasons (subject to tenure-scoping disposition)

Every season produced a clean champion. No `NO_PLAYOFFS_DETECTED` anomalies. The playoff-detection trick is empirically rock-solid across 2010-2025.

**Sub-shape readiness:** **High.** Substrate complete; logic exists; adaptation is a lift from narrative-angle output to per-season-list output. Promotes from selection-prep's "high based on inference" to "high based on empirical probe with founder spot-check."

**Confidence:** **High**.

### 3.2 — §4.2.2 Worst-season tracking

**Canonical event type consumed:** `WEEKLY_MATCHUP_RESULT`.

**Existing aggregation primitives:**

- `league_history_v1.py:491` `_compute_season_records` — builds per-(franchise, season) win/loss/tie/PF dict; constructs `records: list[SeasonRecord]` (lines 515-524); then returns only `(by_best[0], by_worst[0])` extrema (line 531).
- `LeagueHistoryContextV1.worst_season_record` (line 155) — singular extremum field.
- `league_history_v1.py:370` `_compute_longest_streaks` — walks per-franchise game logs in chronological order across seasons; returns only `(longest_win, longest_loss)` extrema (lines 391-392).

**Render-readiness:** Adaptation required, ~20 lines per primitive. **Structural finding:** the existing `_compute_season_records` builds the full per-(franchise, season) records list internally and discards everything except the singular extrema. For A1's "last-place finishers by year; lowest-scoring seasons; longest losing streaks" view, the full list is exactly what's needed. A new public function `compute_all_season_records(matchups) -> tuple[SeasonRecord, ...]` would expose the internal list before the extrema-filter. Symmetric pattern for streak records (expose top-N rather than top-1).

**Spot-check sample:** "Miller went 1-13" Voice Profile §5 reference confirmed at PROBE 2 row 2: **Miller's Genuine Draft 2024, 1W-13L-0T, PF 1392.75.** The Voice Profile fact is empirically anchored at substrate.

**Bonus finding:** PROBE 2 row 1 is Brandon Knows Ball 2025 at 0W-14L-0T — a winless season just completed, more extreme than the cited Miller 1-13. New empirical signal of lore-density at the recent boundary; routed to §6 for Step 2 to weigh.

**Caveat (spec-level, not substrate-readiness):** Format shift at 2021 boundary (14→15 regular-season games per franchise; see §4.3) makes "1-13" structurally impossible pre-2021 (max 13 regular-season losses) but possible 2021+. Cross-era absolute comparisons of worst-record metrics are not strictly comparable. A1's display must handle this — winning-percentage normalization, era-sectioning, surface-copy acknowledgement, or some combination. **Spec-stage disposition, not substrate gap.**

**Sub-shape readiness:** **High.** Substrate complete; logic exists; adaptation is extraction of the internal full list.

**Confidence:** **High** on substrate readiness; **high** on the format-shift caveat being real; **medium-high** on how the caveat resolves at spec stage (multiple defensible options).

### 3.3 — §4.2.3 Blowouts hall

**Canonical event type consumed:** `WEEKLY_MATCHUP_RESULT`.

**Existing aggregation primitives:**

- `HistoricalMatchup.margin: float` — computed per-matchup at `league_history_v1.py:171` `_parse_matchup`. Every matchup in the 16-season window carries margin.
- `narrative_angles_v1.py:282` `_detect_margin_stories` — within-current-week BLOWOUT/NAIL_BITER detector, operates on `ctx.week_biggest_blowout` and `ctx.week_closest_game`. Within-season scope only.

**Render-readiness:** Adaptation required, smallest of the four. **No existing cross-season blowouts aggregation.** But the substrate is so directly accessible (margin is a per-matchup field) that `compute_blowouts_hall(matchups, top_n=10) -> tuple[HistoricalMatchup, ...]` is a one-line sort. Symmetric for nail-biters. Lowest implementation cost of the four sub-shapes.

**Spot-check sample:** PROBE 3 returned top-10 single-week margins ranging 85.50 to 106.60. Top-1: 2025 W14, Paradis' Playmakers 161.40 over Brandon Knows Ball 54.80, margin 106.60. Founder partially recognizes this — "I think I remember this happening, not 100% sure." The substrate-derivation is canonical regardless (the parser is the production parser). Empirical distribution: top-10 spans 2010-2025 with no era-clustering anomalies; three Paradis wins in top-10 but overall list distributes across the league.

**Sub-shape readiness:** **High.** Substrate complete; aggregation is trivial; distribution looks plausible.

**Confidence:** **High** on substrate readiness; **medium-high** on the partially-confirmed top-1 (a remembered event is plausible but the founder is not certain at the 106.60-margin level; the canonical value stands regardless of recall).

### 3.4 — §4.2.4 Manager records (head-to-head)

**Canonical event type consumed:** `WEEKLY_MATCHUP_RESULT` + `franchise_directory` (consumed by `compute_franchise_tenures`).

**Existing aggregation primitives:**

- `league_history_v1.py:330` `compute_head_to_head(matchups, a, b)` — pairwise H2H record for one specific pair; returns `HeadToHeadRecord(a_wins, b_wins, ties, meetings)`.
- `narrative_angles_v1.py:383` `_detect_rivalry_angles` — applies tenure-scoping post-hoc (lines 426-438) by reading `tenure_map: dict[str, int]` and filtering meetings to seasons ≥ tenure-start.
- `league_history_v1.py:587` `compute_franchise_tenures` — computes franchise-id → first-season-with-current-name from `franchise_directory`.

**Render-readiness:** Adaptation required, larger than the trio above. Two work items:

- **Cross-tabulation.** `compute_head_to_head` is pairwise. For A1's N×(N-1)/2 cross-tabulated table view, either wrap in a loop (O(N²·matchups), straightforward) or refactor to all-pairs single-pass (O(matchups), preferred). New derivation function, not a substrate change.
- **Tenure-policy disposition.** The current pattern applies tenure-scoping in `_detect_rivalry_angles` (a narrative-angle consumer), not in `compute_head_to_head` itself. For A1's cross-tabulated display, the choice between unfiltered all-time and tenure-scoped is **load-bearing**.

**Spot-check sample — empirical magnitude of tenure-scoping effect** (PROBE 4 vs PROBE 5, top-10 most-met pairs):

| Pair | Unfiltered | Tenure-scoped | Δ meetings |
|---|---|---|---|
| Stu's Crew / Ben's Gods | 17-16 (33) | 17-16 (33) | 0 |
| Purple Haze / Italian Cavallini | 14-18 (32) | 14-18 (32) | 0 |
| Purple Haze / Brandon Knows Ball | 14-17 (31) | 4-0 (4) | **-27** |
| Weichert's Warmongers / Miller's Genuine Draft | 13-17 (30) | 6-9 (15) | -15 |
| Miller's Genuine Draft / Ben's Gods | 16-14 (30) | 10-6 (16) | -14 |
| Stu's Crew / Paradis' Playmakers | 18-11 (29) | 18-11 (29) | 0 |
| Paradis' Playmakers / Weichert's Warmongers | 13-16 (29) | 13-16 (29) | 0 |
| Paradis' Playmakers / Miller's Genuine Draft | 18-11 (29) | 10-6 (16) | -13 |
| Paradis' Playmakers / Ben's Gods | 16-12-1 (29) | 17-12-1 (29) | 0 (probe-side tie-count artifact) |
| Italian Cavallini / Brandon Knows Ball | 18-10-1 (29) | 1-2 (3) | **-26** |

Five of top-10 pairs have tenure deltas of 13-27 meetings each. Most dramatic: Italian Cavallini / Brandon Knows Ball goes from 18-10-1 across 29 meetings to **1-2 across 3 meetings** under tenure-scoping. Brandon's tenure starts 2024; 26 prior meetings on that franchise-slot belong to the previous occupant. At 3-4 tenure-scoped meetings, the H2H "record" carries thin statistical weight.

(Note on probe-side artifact: in PROBE 5 the Paradis'/Ben's tenure-scoped count flips from 16 to 17 nominal a-wins; this is a probe-presentation bug — my inline PROBE 5 counts `winner_id == franchise_a` regardless of `is_tie`, so a tie where Paradis was nominally credited as winner double-counts. Does not affect the production `compute_head_to_head` semantics; flagged for transparency only.)

The selection-prep memo §4.2.4 cited tenure-scoping as "a settled pattern per `a68a6e0`." Empirically validated — the pattern works — but the **magnitude** of the transformation was understated. The cross-tabulated display reading is a load-bearing spec call, not a cosmetic toggle.

**Caveat surfaced:** Tenure-policy choice for cross-tabulated H2H display is a load-bearing spec decision. Three options A1 spec session must elect among:

- All-time unfiltered (transparency about franchise-slot continuity; risks attributing prior owners' results to current owners — exactly the integrity concern `a68a6e0` was built to avoid in the rivalry-angle context).
- Tenure-scoped only (matches `_detect_rivalry_angles` precedent; risks 3-4-meeting "records" reading as canonical for new-tenure pairs).
- Both, with explicit labeling and optionally a season-threshold for which view is foregrounded.

**Sub-shape readiness:** **Medium-high.** Substrate clean; adaptation is larger than the trio (cross-tabulation + tenure-policy spec call); tenure-policy disposition is non-trivial.

**Confidence:** **High** on substrate; **medium-high** on adaptation classification (the "small adaptation layer" framing fits but is borderline); the policy fork is a spec-stage finding, not a Step 1 conclusion.

---

## 4. D2 historical-data-completeness findings

### 4.1 — WEEKLY_MATCHUP_RESULT per-season coverage

| Era | Seasons | Matchups/season | Mode/week | Total weeks | Format interpretation |
|---|---|---|---|---|---|
| 2010-2020 | 11 | 72 | 5 | 16 | 14 regular + 2 playoff weeks |
| 2021-2025 | 5 | 78 | 5 | 18 | 15 regular + 3 playoff weeks |

No full-season gaps. No partial-season gaps. No anomalies on the per-week mode count (5 across every season — the 10-team format is stable across the entire window). Total matchups loaded: **1182** across 16 seasons. Playoff-detection trick works cleanly across the entire window (PROBE 1 returned a clean champion for every season; no `NO_PLAYOFFS_DETECTED` rows).

### 4.2 — Finding D2-α: substrate window is 16 seasons (2010-2025), not 17

The selection-prep memo (`ba44ba4` §4.2.1, §6.2), the Reset Memo (`bb0f325`), the userMemories ("~17 seasons of digital history"), and the brief itself reference "17 seasons" as the substrate window. **The probe returns 16 seasons.**

**Founder disposition (this session):** The league started in **1983**. The substrate captures the digital-MFL era from 2010 onward (16 seasons). Pre-2010 league history is real (27 prior seasons) but not present in any digitized form available for ingest. **This is not a backfill gap; the data does not exist in digitizable form.**

**Finding:** "16 seasons (2010-2025)" is the correct substrate window. The "17" was an approximation that got promoted across documents.

**Ramification for A1's framing — not a Step 1 conclusion, surfaced for Step 2:** A1's archive cannot honestly claim to represent "the league's full history" — it represents the **digital era**, which is approximately 38% of the league's 42-year arc. A1's framing must be careful: "the league's MFL era" or "since 2010" or "the digital archive" — not "all-time" without qualification, not "17 seasons" (now wrong), not "the league's full history."

This is a **scope-honesty** finding that intersects with §2.3 (silence over speculation) at the framing layer. Worst-season tracking, championship roll, and blowouts hall all read as legitimate sub-shapes within the 2010-2025 window; A1 must just not over-claim temporal coverage. The pre-1983-onward 27-season historical span is GAF-shaped by definition (real, culturally-significant, not substrate-derivable) and intersects directly with the D3 framing question selection-prep §6.3 surfaces.

**Confidence on the count:** **High** (probe + founder confirmation).
**Confidence on the ramification for Step 2:** **High** that framing requires care; the specific framing choice is Step 2 / spec territory.

### 4.3 — Finding D2-β: 72→78 format shift at 2021 boundary

Real league-format change. Regular season expanded by one week (14→15 games per franchise; mirrors the NFL's 17-game season starting 2021). Playoff bracket expanded by one round (2→3 playoff weeks; champion crowned at W16 pre-2021 vs W18 post-2021). The substrate correctly records both formats. Mode-per-week stays at 5 across the boundary (the 10-team format is unchanged).

**Ramification:** Cross-era absolute comparisons need spec-stage care (see §3.2 caveat). Per-game-normalized comparisons (win%, points-per-game) are stable across the boundary; absolute-count comparisons (wins-in-season, losses-in-season) are not. Not a substrate gap.

**Confidence:** **High** on the format-shift; **high** on the interpretation; **medium-high** on the right spec-stage treatment.

### 4.4 — Finding D2-γ: DISTINCT event_type informational aside

`canonical_events.event_type` DISTINCT list (global across leagues): `DRAFT_PICK`, `TRANSACTION_AUCTION_BID`, `TRANSACTION_AUCTION_WON`, `TRANSACTION_AUTO_PROCESS_WAIVERS`, `TRANSACTION_BBID_AUTO_PROCESS_WAIVERS`, `TRANSACTION_BBID_WAIVER`, `TRANSACTION_FREE_AGENT`, `TRANSACTION_IR`, `TRANSACTION_LOAD_ROSTERS`, `TRANSACTION_LOCK_ALL_PLAYERS`, `TRANSACTION_PROCESS_WAIVERS`, `TRANSACTION_TRADE`, `TRANSACTION_UNLOCK_ALL_PLAYERS`, `TRANSACTION_WAIVER`, `WAIVER_BID_AWARDED`, `WEEKLY_MATCHUP_RESULT`, `WEEKLY_PLAYER_SCORE`.

All four event types relevant to A1's full selection-prep enumeration (WEEKLY_MATCHUP_RESULT, WEEKLY_PLAYER_SCORE, TRANSACTION_TRADE, DRAFT_PICK) are present in the ledger. Per brief Anti-Drift §8, no further D2 probing this session for the three out-of-scope event types.

**Confidence:** **High** on presence; **not characterized** on per-league or per-season coverage for the three out-of-scope event types (those are future-session work).

---

## 5. Sub-shape readiness disposition

Per brief §5 disposition framework:

| Sub-shape | Selection-prep §4.2 rating | Post-probe rating | Disposition |
|---|---|---|---|
| §4.2.1 Championship roll | High (inferred) | High (empirical) | **Ready for v1 spec.** |
| §4.2.2 Worst-season tracking | High (inferred) | High (empirical, Voice Profile anchored) | **Ready with caveat** (2021 format-shift comparability; spec-stage). |
| §4.2.3 Blowouts hall | High (inferred) | High (empirical) | **Ready for v1 spec.** |
| §4.2.4 Manager records | High (inferred) | Medium-high (empirical; tenure-policy fork) | **Ready with caveat** (cross-tabulated tenure-policy disposition; spec-stage). |

The selection-prep memo's leading hypothesis trio (championship roll + worst-season tracking + blowouts hall) confirms as ready for v1 spec, with worst-season tracking carrying a spec-stage format-shift caveat. The "defensible expansion" fourth (manager records) is also ready, with a more substantial spec-stage tenure-policy caveat.

**None of the four lands as "not ready."**

**Confidence on dispositions:** **High** for §4.2.1 and §4.2.3; **medium-high** for §4.2.2 and §4.2.4 (the caveats are real but not blockers).

---

## 6. Findings for Step 2

Per brief §6, surfacing — not interpreting — what the probe incidentally produced that Step 2 should weigh.

### 6.1 — 1983-inception finding (D2-α ramification)

The 42-year-league-vs-16-season-substrate gap is the most consequential framing finding of Step 1. A1's "archive of league history" claim has a temporal-honesty floor that Step 2 (and the per-surface constitutional memo) must respect. Multiple framing options exist (illustrative, not exhaustive):

- A1 frames itself as "the digital era" / "the MFL years" / "since 2010" — honest about scope at the surface level.
- A1 includes a copy-level acknowledgement that the league predates the digital archive — affirms league memory while honoring substrate boundary.
- A1 routes pre-2010 lore to a separate (deferred) D3-Beta annotation surface — consistent with the GAF disposition question selection-prep §6.3 surfaces.

This intersects directly with D3 (GAF / lore moments): pre-2010 league memory is GAF-shaped by definition (real, culturally-significant, not substrate-derivable). Step 2's D3 framing call should incorporate this.

### 6.2 — 2021 format-shift cross-era comparability (D2-β ramification)

A1's display of worst-season records, championship roll, and blowouts hall must handle the era boundary at spec stage. Cadence (§D4) intersects: end-of-season updates to A1's archive land on different weeks pre- and post-2021 (championship is W16 vs W18; substrate-noted real-time updates to A1's championship-roll cell happen at different calendar-positions in the NFL season).

### 6.3 — Manager-records tenure-policy fork (§3.4 ramification)

The empirical magnitude of the tenure-scoping effect (5 of top-10 pairs transformed by 13-27 meetings; one pair from 29 meetings to 3) is larger than selection-prep §4.2.4 anticipated. Step 2's meta-surface question (D5) has implications: if manager-records ships as a single A1 sub-shape, the tenure-policy disposition lives inside A1's spec; if A1 is reread as a meta-surface, manager-records-by-tenure-policy may be a content class with its own governance. Surfacing the magnitude; not adjudicating.

### 6.4 — Voice Profile §5 corpus density (D3-Alpha-anchoring evidence)

The probe-derived worst-season ladder includes Miller 1-13 (2024), Brandon 0-14 (2025), Miller 2-11 (2017), Ben's Gods 2-11 (2011), Eddie 3-11 (2022), Cavallini 3-11 (2021), plus multiple 3-10 seasons — substantial instances of the "league remembers mistakes" pattern at the empirical bottom of the records distribution. The corpus density is real; A1's worst-season tracking sub-shape has substantive editorial weight from substrate alone, without GAF annotation. This is **D3-Alpha-anchoring evidence**: substrate-derivable proxies are dense enough to carry significant editorial load on their own. Step 2's D3 framing call should weigh this.

### 6.5 — 2025-boundary recency clustering

Both the worst-season top-1 (Brandon Knows Ball 0-14) and the blowouts-hall top-1 (Paradis' Playmakers 161.40 over Brandon Knows Ball 54.80, W14 2025, margin 106.60) are 2025-season events. Brandon 2025 also appears as the loser in the blowouts top-1 *and* the worst-season top-1 — empirical signal of one franchise-season being the empirical "worst of all time" across multiple A1 sub-shapes simultaneously. Recency-clustering in the leaderboards is a real signal for A1's first-impression visibility and for any cadence anchoring around end-of-season transitions. Not interpretation; observation.

**Confidence on Step 2 inheritance findings:** **Medium** — these are evidence categories surfaced from the probe, not framed conclusions; Step 2 weighs them at adjudication.

---

## 7. Confidence labeling — summary

**Highest-confidence claims this memo lands:**

- The substrate window is 16 seasons (2010-2025), confirmed empirically and against founder recollection. The league's actual inception is 1983; pre-2010 is not digitizable.
- All four in-scope sub-shapes consume `WEEKLY_MATCHUP_RESULT` and no other canonical event type.
- The playoff-detection trick produces a clean champion for every season in the window (16/16).
- Miller's 1-13 (Voice Profile §5 anchor) is empirically present at 2024.
- The tenure-scoping pattern (`compute_franchise_tenures`) is operational and produces non-trivial deltas for 5 of top-10 most-met pairs (13-27 meeting differences).
- None of the four sub-shapes lands as "not ready."

**Lowest-confidence claims this memo lands:**

- The 2025 W14 blowouts-hall top-1 (Paradis 161.40 - Brandon 54.80) is founder-partially-recognized; the substrate-derivation is canonical but the "remembered league event" framing is medium-confidence.
- The "small adaptation layer" framing for §4.2.4 is borderline; the cross-tabulation + tenure-policy adaptation is larger than the other three sub-shapes' adaptation work.
- Step 2 inheritance findings (§6.1-6.5) are evidence surfacings, not framed conclusions; Step 2 weighs them at adjudication.

**Claims this memo deliberately does not make:**

- No D3 GAF framing call (Step 2).
- No D4 cadence call (Step 2).
- No D5 meta-surface call (Step 2).
- No surface-vs-meta-surface adjudication (Step 2 or specification).
- No spec-stage decisions on tenure-policy, format-shift normalization, or pre-2010 framing copy (specification session).
- No proposed code changes, schema changes, or new event types (per brief non-scope).

---

## 8. Chain disposition

Step 1 (this session) ships. Step 2 inherits these findings as predecessor evidence and conducts the framing analysis (D3 / D4 / D5) plus the surface-vs-meta-surface adjudication. After Step 2, the specification session authors the per-surface constitutional memo for A1.

The leading hypothesis — championship roll + worst-season tracking + blowouts hall, with manager records as a defensible expansion — is **anchored more firmly** by this session's empirical findings, with two named caveats (format-shift comparability for worst-season tracking; tenure-policy disposition for manager records) routed to Step 2 / specification.

Decision-readiness chain step: Step 1 of 2 **discharged.** Step 2: next-elected.

---

**Filing:** `_observations/`. Provisional / observational. No tier. No Map registration. Matches Tier 5 doctrine precedent and predecessor memo filings per brief shape §SHAPE.
