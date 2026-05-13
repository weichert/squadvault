# Phase 11 A2 (Draft History Vault) Decision-Readiness Step 1 — Empirical Probes (D1 + D2)

**Date:** 2026-05-13
**Status:** Provisional / observational. No tier. Not registered in Documentation Map. Step 2 of the four-memo A2 chain (selection-prep → decision-readiness Step 1 → Step 2 → specification → registration).
**Filing precedent:** Tier 5 Live Observation Cadence Doctrine at `1cf4142`. Matches predecessor memo filings at `5a865a1` / `a1f4624` / `9093a07` / `ba8b58a` / `ba44ba4` / `fb4f827` / `582c3cf` / `cddcfb5` / `5291c46` / `3e9065f`.

**Predecessors:**

- `bb0f325` — Reset Memo v1.0 (doctrinal source)
- `ba8b58a` — Phase 11 Surface Roadmap (chain pattern §4.1)
- `3e9065f` — A2 selection-prep memo (direct upstream; §4.2 candidate catalog; §6 diagnostic registration; §7.1 leading-hypothesis trio)
- `fb4f827` — A1 Step 1 probes memo (**direct structural precedent**)
- `cddcfb5` — A1 specification (D3-Alpha / D4.1-Gamma / D4.2-Alpha / D5-Gamma inheritance source for the A2 chain)
- `src/squadvault/core/recaps/context/auction_draft_angles_v1.py` (908 LOC) — auction detector implementation; data loaders empirically exercised this session

**Output:** Empirical confirmation (or qualification) of the substrate-coverage and historical-data-completeness priors named in the selection-prep §6.1 (D1) and §6.2 (D2) diagnostics. Five D2 findings (α through ε); three D1 findings (one per leading-hypothesis sub-shape). Sub-shape readiness disposition for the in-scope leading-hypothesis trio. Step 2 inheritance findings registered for the framing analysis to weigh.

---

## 1. §-content verification block — carry-forward

Per selection-prep §2 and Roadmap §6.1: the doctrinal §-substance load-bearing on A2 selection is source-anchored in the predecessor chain. No fresh §-claim has surfaced during probe execution. Roadmap §7.5 source-access procedure not invoked.

**Confidence on carry-forward:** **High**.

---

## 2. Probe scope

**In-scope sub-shapes per selection-prep §7.1 leading-hypothesis trio:**

- §4.2.1 — Auction-most-expensive history (D28 lift)
- §4.2.2 — Auction-bust hall (D22 cross-season lift)
- §4.2.3 — Auction-bargain hall (D21 cross-season lift)

**Out-of-scope sub-shapes per Anti-Drift §10 #3** (anchor, not forcing; Step 2 may elect to admit additional sub-shapes):

- §4.2.4 — Position-cost inflation (D26)
- §4.2.5 — Per-franchise drafting tendencies (D23 + D24)
- §4.2.6 — Auction-strategy consistency (D25)
- §4.2.7 — FAAB-pipeline composite (D27)

**Empirical inputs to this session** (ephemeral probe at `/tmp/probe_a2_step1.py`; not committed):

- D2 SQL probes against `v_canonical_best_events` for league `70985`: per-season `DRAFT_PICK` distribution with `bid_amount` analysis; pre-2018 `DRAFT_PICK` characterization; `WEEKLY_PLAYER_SCORE` per-season coverage 2010-2025; `WAIVER_BID_AWARDED` per-season coverage; Cavallini/Mahomes 2018 verification anchor.
- D1 production-loader exercise: `_load_all_auction_picks` and `_load_player_season_scoring` from `auction_draft_angles_v1.py` invoked against the local sqlite; `detect_auction_most_expensive_history` (D28) dry-run; cross-season aggregation simulations for D22 (bust) and D21 (bargain) sketches.

---

## 3. D1 substrate-coverage findings per in-scope sub-shape

All three in-scope sub-shapes consume the same canonical event types: `DRAFT_PICK` (with `bid_amount` from payload) joined to `player_directory` for position metadata, plus `WEEKLY_PLAYER_SCORE` for the value-vs-cost calculations on §4.2.2 and §4.2.3. The shared substrate read is a structural fact — the trio is a pure-derivation sibling set on two canonical event streams plus the position-enrichment table.

**Confidence on shared-substrate finding:** **High**.

### 3.1 — §4.2.1 Auction-most-expensive history

**Canonical event types consumed:** `DRAFT_PICK` + `player_directory`.

**Existing aggregation primitive:** `auction_draft_angles_v1.py:803` `detect_auction_most_expensive_history`. Already cross-auction-era scope (loads via `_load_all_auction_picks` without season filter; requires `min_seasons=2`). Internally computes `pos_max: dict[str, tuple[_AuctionPick, float]]` (per-position max bid across all loaded picks) at lines 818-824, then surfaces only the overall max as a single `NarrativeAngle`.

**Render-readiness:** Adaptation required, smallest of the trio. **Structural finding:** the detector already builds the per-position records internally but discards them in favor of the overall record. For A2's archive view, the per-position records are exactly what's needed — a "Top RB pick ever / Top WR pick ever / Top QB pick ever" presentation is more substantively informative than the single overall-RB-dominated row (§6.2 below). A new public function `compute_most_expensive_history(picks, top_n=N) -> dict[str, list[_AuctionPick]]` would expose the internal `pos_max` plus per-position top-N rather than per-position top-1. No new event types; no schema; no detector classes.

**Spot-check sample (PROBE D1.1):** Loaded 1163 total auction picks across 7 distinct seasons. D28 production-function output: 1 angle, *"0002's $76 on 13604 in 2019 is the most ever spent on a single player in a league auction"*, position RB. Cross-era top-10:

| # | Bid | Season | Franchise | Player | Pos |
|---|---|---|---|---|---|
| 1 | $76 | 2019 | 0002 | 13604 | RB |
| 2 | $76 | 2020 | 0002 | 13130 | RB |
| 3 | $74 | 2018 | 0004 | 12625 | RB |
| 4 | $73 | 2020 | 0010 | 13604 | RB |
| 5 | $73 | 2022 | 0002 | 14802 | RB |
| 6 | $70 | 2018 | 0005 | 12150 | RB |
| 7 | $70 | 2022 | 0010 | 13404 | RB |
| 8 | $70 | 2024 | 0009 | 13130 | RB |
| 9 | $69 | 2019 | 0009 | 13130 | RB |
| 10 | $69 | 2020 | 0003 | 12652 | WR |

**Sub-shape readiness:** **High.** Substrate complete; detector already does the across-era computation; adaptation is exposure of the internally-computed per-position structure. Promotes from selection-prep's "high based on structural read" to "high based on empirical probe with detector dry-run."

**Confidence:** **High**.

### 3.2 — §4.2.2 Auction-bust hall

**Canonical event types consumed:** `DRAFT_PICK` + `player_directory` + `WEEKLY_PLAYER_SCORE`.

**Existing aggregation primitive:** `auction_draft_angles_v1.py:413` `detect_auction_bust`. Single-season scope (filters `picks` by `current_season` at line 428). Flags top-3 picks per franchise by bid amount whose `starter_weeks >= 4` and player-avg below `league_starter_avg × 0.5`.

**Render-readiness:** Adaptation required, cross-season lift. New derivation function `compute_bust_hall(picks, scoring, top_n=N) -> tuple[BustEntry, ...]` that runs the within-season bust signal across all auction-era seasons and ranks by combined severity (`(league_avg − player_avg) × bid_amount` or analogous). The within-season logic is the existing detector's; the across-season aggregation is computational extension — analog to A1 §4.2.3 blowouts hall's "one-line sort" trivial lift, but with a per-pick scoring lookup so a touch more involved.

**Spot-check sample (PROBE D1.2):** Cross-season lift produced **185 bust candidates** at the single-season-D22 threshold (≥4 starts; player-avg below 50% of season league-starter-avg). Top-10 by signal (severity × bid):

| # | Season | Franchise | Player | Bid | Player avg | Starts |
|---|---|---|---|---|---|---|
| 1 | 2020 | 0008 | 10271 | $62 | 13.4 | 9 |
| 2 | 2019 | 0006 | 11679 | $64 | 10.1 | 12 |
| 3 | 2020 | 0005 | 13299 | $56 | 13.3 | 6 |
| 4 | 2024 | 0009 | 13130 | $70 | 10.1 | 4 |
| 5 | 2023 | 0004 | 13404 | $64 | 11.9 | 13 |
| 6 | 2020 | 0007 | 14073 | $55 | 13.8 | 14 |
| 7 | 2023 | 0001 | 16161 | $61 | 12.1 | 14 |
| 8 | 2023 | 0009 | 15281 | $63 | 13.4 | 16 |
| 9 | 2023 | 0006 | 11244 | $57 | 12.5 | 13 |
| 10 | 2023 | 0005 | 13164 | $50 | 10.6 | 9 |

Cross-era distribution spans 2018-2025 with no era-clustering anomalies in the top-10. The 2021 gap (§4.1 below) naturally skips with zero candidates from that season.

**Cross-list signal: player 13130 appears at row 4 here** (2024 bust by franchise 0009 at $70) **and at rows 2, 8, 9 of §3.1's most-expensive top-10**. The same player_id is simultaneously a multi-time historical-most-expensive pick AND a top-10 cross-era bust. The "high-priced star who declined" arc made visible (§6.3 below).

**Sub-shape readiness:** **High.** Substrate complete; cross-season lift confirmed tractable; pattern matches expected shape. Promotes from selection-prep's "medium-high based on structural read" to "high based on empirical probe."

**Confidence:** **High** on substrate-readiness; **high** on cross-season lift tractability; **medium-high** on the precise severity-ranking formula (the simulation used `(league_avg − player_avg) × bid_amount`; alternative formulas are defensible; spec-stage call).

### 3.3 — §4.2.3 Auction-bargain hall

**Canonical event types consumed:** `DRAFT_PICK` + `player_directory` + `WEEKLY_PLAYER_SCORE`.

**Existing aggregation primitive:** `auction_draft_angles_v1.py:365` `detect_auction_dollar_per_point`. Single-season scope (same pattern as D22).

**Render-readiness:** Adaptation required, same shape as §3.2. New derivation function `compute_bargain_hall(picks, scoring, min_points=N, top_n=M) -> tuple[BargainEntry, ...]` that ranks cross-auction-era picks by lowest `bid_amount / total_points` at a meaningful-production threshold. Spec-stage parameter calls: min-production threshold (the probe used `>= 50 total points`; spec may elect higher or lower); top-N display count.

**Spot-check sample (PROBE D1.3):** Cross-season lift produced **761 candidates** with ≥50 total points. Top-10 cross-era bargains by lowest $/point:

| # | Season | Franchise | Player | Bid | Total points | $/pt |
|---|---|---|---|---|---|---|
| 1 | 2019 | 0005 | 13593 | $1 | 519 | 0.002 |
| 2 | 2018 | 0001 | 9099 | $1 | 425 | 0.002 |
| 3 | 2023 | 0004 | 15698 | $1 | 420 | 0.002 |
| 4 | 2022 | 0002 | 15237 | $1 | 366 | 0.003 |
| 5 | 2020 | 0005 | 10697 | $1 | 350 | 0.003 |
| 6 | 2019 | 0006 | 12620 | $1 | 346 | 0.003 |
| 7 | 2025 | 0004 | 16579 | $1 | 326 | 0.003 |
| 8 | 2019 | 0002 | 11760 | $1 | 318 | 0.003 |
| 9 | 2025 | 0003 | 14782 | $1 | 315 | 0.003 |
| 10 | 2023 | 0003 | 10703 | $1 | 306 | 0.003 |

Top-10 are uniformly $1 picks with 306-519 total-point returns. The "legendary $1 pick that won the year" pattern (selection-prep §4.2.3) is empirically dense — the substrate has multiple instances per auction-era season. The $1 bid floor confirmed across all 7 auction-substrate seasons in §4.1.

**Sub-shape readiness:** **High.** Substrate complete; cross-season lift confirmed tractable; pattern matches expected shape and Voice Profile §3-§5 framing.

**Confidence:** **High**.

---

## 4. D2 historical-data-completeness findings

### 4.1 — Per-season DRAFT_PICK coverage and the 2021 gap finding (D2-α)

Per-season `DRAFT_PICK` distribution across the 2010-2025 digital era:

| Season | Total picks | Positive bid | Zero bid | Min bid | Max bid |
|---|---|---|---|---|---|
| 2018 | 153 | 153 | 0 | $1 | $74 |
| 2019 | 150 | 150 | 0 | $1 | $76 |
| 2020 | 180 | 180 | 0 | $1 | $76 |
| **2021** | **0** | **0** | **0** | — | — |
| 2022 | 170 | 170 | 0 | $1 | $73 |
| 2023 | 170 | 170 | 0 | $1 | $69 |
| 2024 | 170 | 170 | 0 | $1 | $70 |
| 2025 | 170 | 170 | 0 | $1 | $66 |

**Finding D2-α: the auction substrate window is 7 seasons (2018-2020, 2022-2025), NOT 8.** The selection-prep §3.1 prior derived from the `auction_draft_angles_v1.py` docstring claim *"data from 2018-2025"* was a structural-read prior; the empirical reality is **2018-2025 with a 2021 gap**. The 2021 season has clean `WEEKLY_PLAYER_SCORE` coverage (2227 rows; §4.3) — the league played that season — but **zero `DRAFT_PICK` events**.

**Cause of the 2021 gap is uncharacterized this session.** Three candidates worth founder confirmation:

- **(a) Auction format suspended for 2021.** The league ran a non-auction draft (snake or otherwise) and the substrate's ingest pipeline does not (or cannot) represent non-auction drafts as `DRAFT_PICK` events. **Most likely** given the clean 2010-2017 pre-auction-era absence (D2-β); 2021 may be a one-year reversion to a pre-2018 format, or a one-year experiment.
- **(b) Auction was conducted but events landed under a different `event_type`.** No supporting evidence; A1 Step 1 §4.4 enumerated the canonical `event_type` set and `DRAFT_PICK` is the only draft-event class.
- **(c) Ingest gap.** Possible but would be unusual given clean coverage on either side.

**Compound drift confirmation:** the Roadmap §2.2 "17 seasons" framing for A2 is now **doubly overstated** — selection-prep §3.1 surfaced 17 → 16 (digital era; same drift A1 surfaced) → 8 (auction-era structural-read prior). This session surfaces a third narrowing: 8 → 7 (auction-era empirical). The compound is recorded as a finding for the future Roadmap revision sweep (per selection-prep §10.1 framing).

**Ramification for A2 framing copy:** A2's spec session must acknowledge the 2021 gap explicitly at the surface header level, analog to A1 spec §3.6's digital-era declaration. Candidate phrasing: *"The Auction Era Archive: PFL Buddies auctions 2018–2025, with one missing year (2021)"* or similar. Cross-season averaging and trend detectors will naturally skip 2021 silently; the framing copy is the spec's mechanism for honoring the gap honestly.

**Anomalous row counts:** 2018 (153), 2019 (150), and 2020 (180) deviate from the 2022-2025-stable 170. Selection-prep §4.2 did not address roster-size history. Hypotheses (not adjudicated this session):

- 153 = 9 teams × 17 roster slots (single-team smaller in 2018?).
- 150 = 10 teams × 15 roster slots (different roster size in 2019?), or 9 teams × ~17, or other.
- 180 = 10 teams × 18 roster slots (one-year expanded roster in 2020?).
- 170 = 10 teams × 17 roster slots (stable from 2022 onward).

These do not affect the v1 trio admissibility but are substrate characterization for the spec session.

**Confidence on D2-α (the 2021 gap):** **High** (probe is empirical; cause is uncharacterized; founder may clarify).
**Confidence on the row-count anomalies:** **Medium** (pattern is real; explanations are hypotheses).

### 4.2 — Pre-2018 era: zero auction events (D2-β)

The probe returned **zero `DRAFT_PICK` events for any season 2010-2017**. The selection-prep §3.1 prior (auction-era begins at 2018) is empirically confirmed.

**Selection-prep §6.2's "snake-vs-zero-bid distinction" probe disposition:** *clean*. No `DRAFT_PICK` events with `bid_amount = 0` exist in the pre-2018 window; the `bid_amount > 0` filter at `auction_draft_angles_v1.py:121-122` has nothing pre-2018 to silently elide. The selection-prep §3.3 worry — that snake-draft picks might be ingested as canonical `DRAFT_PICK` events with zero bids — is **not** the substrate state. Pre-2018 draft events are simply not in the canonical event ledger at all.

**Ramification for the spec session:** A2's scope declaration honestly bounds at 2018 onward without ambiguity. The pre-2010 "all-time league history" framing (which A1 spec §3.1 explicitly excluded) plus the 2010-2017 pre-auction era plus the 2021 gap together define the temporal-honesty boundary A2's framing copy must honor.

**Confidence:** **High** on the pre-2018 absence; **high** on the snake-vs-zero-bid disposition (the worry-case did not materialize).

### 4.3 — WEEKLY_PLAYER_SCORE coverage complete 2010-2025 (D2-γ)

| Season | Rows | Season | Rows | Season | Rows | Season | Rows |
|---|---|---|---|---|---|---|---|
| 2010 | 1897 | 2014 | 1931 | 2018 | 1911 | 2022 | 2253 |
| 2011 | 1905 | 2015 | 1895 | 2019 | 1888 | 2023 | 2308 |
| 2012 | 1945 | 2016 | 1904 | 2020 | 2177 | 2024 | 2294 |
| 2013 | 1922 | 2017 | 1915 | 2021 | 2227 | 2025 | 2277 |

No gaps across the entire 16-season digital era. Per-season counts climb from ~1900 (pre-2020) to ~2200-2300 (2020 onward); the climb is consistent with the 2021 NFL format-shift A1 Step 1 §4.3 identified (14-game → 15-game regular season) plus possible roster-slot expansion (paralleling §4.1's 2020 anomaly).

**Crucially: 2021 has complete `WEEKLY_PLAYER_SCORE` coverage (2227 rows) despite zero `DRAFT_PICK` events.** This is what anchors the D2-α finding: the league played in 2021; the production-data substrate was ingested; only the draft-event substrate is missing.

**Ramification for the trio:**

- §3.1 §4.2.1 (most-expensive history): no `WEEKLY_PLAYER_SCORE` dependency; D2-γ confirmation strengthens but does not gate.
- §3.2 §4.2.2 (bust hall): bust calculation requires production-side data; D2-γ confirmation means the 7 auction-substrate seasons all have clean production-data backing.
- §3.3 §4.2.3 (bargain hall): same as §4.2.2; D2-γ confirmation strengthens.

**Confidence:** **High** on coverage; **high** on the auction-substrate-bust/bargain backing.

### 4.4 — FAAB substrate begins 2021, narrows §4.2.7 admissibility (D2-δ)

`WAIVER_BID_AWARDED` per-season coverage:

| Season | Rows |
|---|---|
| 2010-2020 | 0 |
| 2021 | 41 |
| 2022 | 46 |
| 2023 | 48 |
| 2024 | 65 |
| 2025 | 57 |

**FAAB substrate begins at 2021, not 2018.** Pre-2021 has zero `WAIVER_BID_AWARDED` events.

**Ramification for selection-prep §4.2.7 (FAAB-pipeline composite):** This sub-shape is **out-of-scope for the leading-hypothesis trio** and out-of-scope for this session's D1 probes. But the D2 finding here is substantive and feeds Step 2 / future expansion discussions:

- FAAB substrate covers 5 seasons (2021-2025).
- Auction substrate covers 7 seasons (2018-2020, 2022-2025).
- **Overlap window where both substrates exist: 4 seasons (2022-2025).** The "draft + FAAB combined investment" sub-shape per the selection-prep §4.2.7 description can only run for this 4-season window.
- Selection-prep §4.2.7 characterized FAAB as "an open question on completeness across the 2018-2025 window"; the answer is **FAAB is not complete across that window** — it starts at 2021.

**§4.2.7 admissibility narrows substantively from the selection-prep characterization.** If §4.2.7 is elected at Step 2 or specification as a v1 addition, the cross-substrate window is 4 seasons, not 8 (and not 7).

**Confidence:** **High** on the FAAB-begin-at-2021 finding; **high** on the §4.2.7 admissibility narrowing.

### 4.5 — Italian Cavallini / Mahomes 2018 verification anchor CONFIRMED (D2-ε)

Per Narrative_Angles_v2 Phase 6 success example: *"Italian Cavallini spent $62 on Patrick Mahomes in the 2018 auction — the third-highest bid in league draft history — and that investment has returned 1,847 career points, more than any other auction pick ever."*

**Probe result:** **MATCH at franchise=0002, player_id=9988, $62 in 2018.**

**Career production check (PROBE D1.4 bonus):** Player 9988 total points across all `WEEKLY_PLAYER_SCORE` entries (any roster) = **1804.4 points** across 116 (season, week) entries.

- Narrative_Angles_v2 claim: 1,847 career points.
- Empirical: 1,804.4 career points.
- Delta: 42.6 points (~2.3%).
- **Order-of-magnitude check: PASSES.**

The 42-point delta is small and plausibly explained by either (a) v2 was authored at a slightly different in-season moment than the current substrate state (1,847 may have included some weeks that the current week-scoping logic excludes from "career" totals; the precise computation method is uncharacterized for v2's claim), or (b) v2 used a slightly different counting method (rounding; including playoff-week scores; including specific lineup contexts).

**Anti-Drift §6 verification target DISCHARGED.** The selection-prep memo cited the Cavallini-Mahomes record as a Step 1 verification target, not as substrate-confirmed; this session confirms it. The fact is now substrate-anchored.

**Side finding on the "third-highest bid" claim:** v2 records this pick as *"the third-highest bid in league draft history"* — at the moment of v2 authoring. The cross-era top-10 (§3.1) places $62 OUTSIDE the top-10 (the 10th-place bid is $69). The Cavallini-Mahomes $62 was the third-highest at 2018-onward-known-then state of the substrate; cross-era as of 2025, it ranks somewhere lower. **Narrative-claim drift between v2 authoring and current substrate state — same shape as the seasons-count Roadmap drift.** For A2's eventual spec, bid-rank claims must be substrate-derived at render time, not narrative-frozen. Surfaced for Step 2 / spec session weighing (§6.4 below).

**Confidence on the anchor confirmation:** **High** (exact bid + 2018 + franchise + player match).
**Confidence on the career-production order-of-magnitude:** **High** (delta is small and plausible).
**Confidence on the narrative-drift framing:** **High** (the rank claim is empirically not current).

---

## 5. Sub-shape readiness disposition

Per A1 Step 1 §5 precedent framework:

| Sub-shape | Selection-prep §4.2 rating | Post-probe rating | Disposition |
|---|---|---|---|
| §4.2.1 Auction-most-expensive history | High (structural-read) | **High (empirical)** | **Ready for v1 spec.** Adaptation: expose internally-computed `pos_max` plus per-position top-N. |
| §4.2.2 Auction-bust hall | Medium-high (structural-read) | **High (empirical)** | **Ready for v1 spec.** Adaptation: cross-season lift confirmed tractable; spec-stage severity-formula call. |
| §4.2.3 Auction-bargain hall | Medium-high (structural-read) | **High (empirical)** | **Ready for v1 spec.** Adaptation: same shape as §4.2.2; spec-stage min-production-threshold call. |

The selection-prep leading-hypothesis trio confirms as ready for v1 spec across all three sub-shapes. **None of the three lands as "not ready."** Two spec-stage caveats surfaced:

- §4.2.1 — per-position records exposure (mostly trivial; D28 internal data structure already has them).
- §4.2.2 / §4.2.3 — cross-season lift severity-and-threshold formula parameter calls (defensible options exist; spec-stage adjudication).

Plus the universal **2021 gap framing-copy caveat** (§4.1; spec-stage display disposition).

**Out-of-scope sub-shape with substantive D2 narrowing:**

- §4.2.7 FAAB-pipeline composite — admissibility narrows from "2018-2025 cross-era" to "2022-2025 (4 seasons)" overlap window per §4.4. Not in the v1 trio; Step 2 or specification weighs whether §4.2.7 enters v1 as a fourth sub-shape under the narrower window.

**Confidence on dispositions:** **High** for §4.2.1, §4.2.2, §4.2.3 readiness (probe-confirmed); **high** on the §4.2.7 narrowing (probe-confirmed).

---

## 6. Findings for Step 2

Per A1 Step 1 §6 precedent: surfacing — not interpreting — what the probe incidentally produced that Step 2 should weigh at framing analysis.

### 6.1 — The 2021 gap framing question (D2-α ramification)

A2's display of most-expensive history, bust hall, and bargain hall must handle the 2021 gap explicitly at framing copy. Three illustrative dispositions Step 2 may weigh (not exhaustive; spec session adjudicates):

- **Framing-copy acknowledgement only.** A2's archive header declares "the auction era (2018–2025, except 2021)" or similar; the leaderboards display only what exists.
- **Per-leaderboard footnote.** Each sub-shape's display has a "2021 not represented" footnote.
- **Substantive 2021 characterization** in framing copy. If founder knows the 2021-format-shift cause (one-year snake, one-year suspension, ingest gap), the framing copy can be more substantive: *"In 2021 the league reverted to a snake draft; auction history resumes in 2022."*

This also intersects with the cadence anchor question D4.2 in §3.5 of selection-prep: if D4.2-Gamma (auction-night anchor) is elected, the 2021 gap is one auction night where no archive update would have fired. Stable under D4.2-Alpha (NFL W1 anchor).

### 6.2 — Top-10 most-expensive position skew

§3.1's top-10 most-expensive picks are 9-of-10 RBs (the lone WR at position #10). The single overall-record D28 output ($76 on RB 13604 in 2019) hides position-wide structure. For §4.2.1's v1 view, the per-position records (already computed in D28's internal `pos_max`) would expose a more substantively informative leaderboard:

- "All-time most-expensive RB: 13604, $76 (2019)"
- "All-time most-expensive WR: 12652, $69 (2020)"
- "All-time most-expensive QB: 9988, $62 (2018)"  ← the Cavallini-Mahomes pick lands as the QB record
- etc.

The Cavallini-Mahomes pick lands as the QB-position record under the per-position view — preserving the Voice Profile §5 / `Narrative_Angles_v2` anchor pick's prominence in a way the overall-only view does not. **Recommended Step 2 / spec finding:** §4.2.1's v1 lifts both overall and per-position records, not just overall. Step 2 names; spec adjudicates.

### 6.3 — Cross-list player-id appearance pattern (player 13130)

Player 13130 appears in §3.1's top-10 most-expensive three times (2020 by 0002 at $76; 2024 by 0009 at $70; 2019 by 0009 at $69) **and** at rank 4 of §3.2's top-10 cross-era bust list (2024 by 0009 at $70, 10.1 avg, 4 starts).

This is a "high-priced star who declined" arc visible across two of A2's leaderboards simultaneously. Spec-session question: does A2's display cross-link or note this? Three options:

- A2 displays each leaderboard independently; cross-list patterns are reader-discoverable.
- A2 surfaces a cross-list "notable players who appear in multiple leaderboards" view as a v1 sub-shape addition.
- A2 surfaces a per-player aggregated view at click-through (deferred to a future expansion).

Surfacing the empirical pattern; not adjudicating.

### 6.4 — Narrative-claim drift between v2 authoring and current substrate (D2-ε ramification)

Narrative_Angles_v2 claims Cavallini's 2018 $62 on Mahomes was *"the third-highest bid in league draft history."* Cross-era as of 2025, $62 ranks outside the top-10 most-expensive (10th-place bid is $69). The claim was substrate-accurate at the moment v2 was authored; the substrate has accumulated additional auction history since.

**This is structurally identical to the 16-vs-17-vs-8-vs-7-seasons compound Roadmap drift.** Narrative claims about substrate state must be re-derived at render time, not narrative-frozen. For A2's spec: any sub-shape that surfaces ordinal-rank claims ("third-highest", "fifth-most-expensive", "twelfth-worst-season") must compute at render time against the current substrate, not store narrative-frozen rank descriptions.

This is a §2.3 silence-over-speculation alignment: A2 surfaces the current substrate-derived rank, not a historical-narrative-derived rank. The Voice Profile §5 anchor (the league remembers things affectionately) is preserved; the substrate's evolving rank-order is the source of truth.

### 6.5 — Roster-size history (D2-α anomalous row counts)

§4.1's row-count anomalies (2018=153, 2019=150, 2020=180, vs 2022-2025 stable at 170) suggest roster-size or team-count history that selection-prep §3.1 did not characterize. Step 2 or spec may surface founder-disposition on:

- Were 2018 and 2019 9-team years (153 / 150 implying 9 × ~17 / 9 × ~17)? Or smaller-roster (10 × 15 / 10 × 15)?
- Was 2020 an 18-roster-slot year (10 × 18)?
- When did the 10 × 17 stable format begin (it's stable from 2022 onward but 2021 has no draft-event data so the format-shift moment is not directly observable in DRAFT_PICK counts)?

Not load-bearing on the v1 trio; substrate characterization for spec-session framing.

### 6.6 — D4.2-Gamma (auction-night anchor) interaction with the 2021 gap

Selection-prep §6.4 / §8.2 surfaced D4.2-Gamma (auction-night anchor) as the substantively-relevant A2-specific alternative to D4.2-Alpha (NFL W1 anchor inherited from A1). The 2021 auction-substrate gap introduces a new wrinkle: if A2 anchors on auction night, the 2021 revision-point either doesn't fire (no auction occurred — or the 2021 non-auction-format draft doesn't carry the same revision-point semantics) or fires against the non-auction-format moment. Under D4.2-Alpha (NFL W1), the 2021 revision-point fires normally against the substrate state available at the moment (which simply lacks 2021 auction picks for that year). **The 2021 gap argues marginally more weight for D4.2-Alpha** on stability grounds. Step 2 weighs.

**Confidence on Step 2 inheritance findings:** **Medium** — these are evidence surfacings, not framed conclusions; Step 2 weighs them at adjudication.

---

## 7. Confidence labeling — summary

**Highest-confidence claims this memo lands:**

- The auction substrate window is **7 seasons (2018-2020, 2022-2025)**, not 8 — empirically confirmed; 2021 has zero `DRAFT_PICK` events despite normal `WEEKLY_PLAYER_SCORE` ingestion.
- Pre-2018 era has **zero auction events** of any kind; the silent-snake-elision worry case did not materialize.
- `WEEKLY_PLAYER_SCORE` coverage is **complete 2010-2025** with no gaps; the auction-era 7-season window has clean production-data backing for bust/bargain calculations.
- FAAB substrate **begins at 2021, not 2018**; the cross-substrate overlap window for §4.2.7 is 4 seasons (2022-2025), not 8.
- The **Italian Cavallini / Mahomes 2018 anchor is substrate-confirmed** at $62, franchise 0002, player 9988; career production 1804.4 points (order-of-magnitude matches v2's 1,847 claim).
- All three in-scope leading-hypothesis sub-shapes (§4.2.1, §4.2.2, §4.2.3) land **HIGH on post-probe readiness**.

**Medium-high-confidence claims:**

- The 2021 gap cause is uncharacterized; three candidates named (auction suspended; non-auction format; ingest gap). Founder may resolve.
- The §4.2.1 spec-session adaptation should expose per-position records (not just overall); recommendation grounded on RB-skew in the overall top-10 empirical distribution.

**Medium-confidence claims:**

- The §4.1 row-count anomalies (2018, 2019, 2020 deviating from 2022-2025 stable) suggest roster-size / team-count history not yet characterized.
- D4.2-Gamma (auction-night anchor) interaction with the 2021 gap argues marginally more weight for D4.2-Alpha inheritance, but the framing is a Step 2 founder-judgment call.

**Lowest-confidence claims:**

- Narrative-claim drift (the v2 "third-highest bid" claim) is empirically not current; the principle that "substrate-derived rank claims must compute at render time, not narrative-freeze" is a spec-session disposition surfaced from this finding.

**Claims this memo deliberately does not make:**

- No D3 GAF/lore-pick framing call (Step 2 inherits D3-Alpha from A1 by default; A2-specific friction not surfaced).
- No D4 cadence call (Step 2 weighs the auction-night-anchor question per §6.6).
- No D5 meta-surface call (dissolved by A1 Reading 1 inheritance per selection-prep §5).
- No surface-vs-meta-surface adjudication (closed by inheritance).
- No spec-stage decisions on 2021 framing copy, per-position-records exposure, bust/bargain severity formulas, or cross-list player-id display patterns.
- No proposed code changes, schema changes, or new event types.

---

## 8. Chain disposition

Step 1 (this session) ships. Step 2 inherits these findings as predecessor evidence and conducts the framing analysis (D3 GAF / D4 cadence) plus confirms the surface-vs-meta-surface carry-forward (D5 dissolved). After Step 2, the specification session authors the per-surface constitutional memo for A2 — the first empirical exercise of template v1.0 at `5291c46`.

The leading hypothesis — auction-most-expensive history + auction-bust hall + auction-bargain hall under Reading 1 inheritance — is **anchored more firmly** by this session's empirical findings, with the substantive 2021-gap framing disposition routed to Step 2 / specification. The selection-prep §10.1 compound-drift finding (16 → 7 with mid-window gap) is now empirically grounded.

Decision-readiness chain step: Step 1 of 2 **discharged.** Step 2: next-elected.

---

**Filing:** `_observations/`. Provisional / observational. No tier. No Map registration. Matches Tier 5 doctrine precedent at `1cf4142` and predecessor memo filings per session shape.

---

## 9. Cross-references

- `bb0f325` — Reset Memo v1.0
- `ba8b58a` — Phase 11 Surface Roadmap (§4.1 chain pattern; §2.2 admissibility framing; "17 seasons" framing drift source)
- `ba44ba4` — A1 selection-prep memo
- `fb4f827` — A1 Step 1 probes memo (direct structural precedent for this memo)
- `582c3cf` — A1 Step 2 framing memo
- `cddcfb5` — A1 specification (D3-Alpha / D4.1-Gamma / D4.2-Alpha / D5-Gamma inheritance)
- `5291c46` — Per-surface constitutional-memo template v1.0
- `3e9065f` — A2 selection-prep memo (direct upstream; §4.2 catalog; §6 diagnostic registration; §7.1 leading-hypothesis trio; §10.1 compound-drift framing)
- `src/squadvault/core/recaps/context/auction_draft_angles_v1.py` — auction detector implementation (lines 60-280 data loaders; line 803 D28; line 413 D22; line 365 D21; line 121-122 bid_amount > 0 filter)
- `Narrative_Angles_v2_Definitive_Scope.md` Phase 6 / Dimension 6 — Italian Cavallini / Mahomes success-example anchor (D2-ε source)
