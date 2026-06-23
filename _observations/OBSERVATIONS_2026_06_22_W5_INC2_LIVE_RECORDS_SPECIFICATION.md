# Trophy Room (Unit W.5) Increment 2 - Live Records - Specification (memo 3 of 4) - DRAFT

**Date:** 2026-06-22
**Session type:** DECIDE (specification). No repo/DB writes. DRAFT for founder ratification + commit.
**Chain position:** memo 3 of 4 (increment 2). Executes the ratified D1-D5 rulings (memo 2) on probe-confirmed data.
**Anchors:** engine HEAD `5464526`; frontend `a6eb95b` (increment 1 discharged). Probe: `w5_inc2_threshold_and_playoff_probe.py` (1177 decided games, league 70985).

---

## 1. Ratified inputs carried in

- **D1** - staged delivery (Wave 1 now / Wave 2 after sync extension / Unbroken Chain deferred).
- **D2** - The Executioner threshold = **win by 60 or more points** (pinned constant; probe: 80 blowouts across 17 seasons, ~5/season - rare by design; "awards should mean something").
- **D3** - The Unbroken Chain **DEFERS**: probe shows champion-week matchups contain only the 2 finalists, so "made the playoffs" (the bracket field) is NOT in `WEEKLY_MATCHUP_RESULT`. Not exactly derivable -> render nothing, not a guess (silence over speculation).
- **D4/D5** - derived-holder reads, multi-valued on tie (C6), reusing the increment-1 shared architecture; no manual `trophy_custody_events` ledger (records derive from completed facts).

## 2. Surface and shared-architecture reuse

The **Live Records section** of the Trophy Room renders the qualifying plaques as Trophy Cards on
increment 1's shared architecture: Room section, Trophy Card (section 3 of the inc-1 spec), Docket ID
(`TR-LRC-<#>-<season>`), trust bar (provenance = CANONICAL, engine-derived facts), commissioner approval
(publication gate). A Live Record writes **no** custody event; its current holder is a derived read off
synced record data (C1). Drill-in shows the record's chronological holder history (section 6).

## 3. Wave 1 - 4 plaques on existing synced data (`franchise_season_records`)

Each is a derived read; the immutable qualification stays pure (no baked-in holder, per the Constitutional pass).

- **#24 The Cavallini Standard** (all-time win-pct leader): aggregate `wins / (wins+losses+ties)` across all
  seasons per franchise; holder = max. Ties in pct -> multi-valued.
- **#25 The Dynasty** (most titles): count `result = 'CHAMPION'` per franchise; holder = max.
- **#26 The Eternal Runner-Up** (most runner-ups, no title): count `result = 'RUNNER_UP'` per franchise
  **where CHAMPION count = 0**; holder = max.
- **#30 The Floor** (worst single-season record; tone-care): the season-row with the worst W-L (lowest
  win-pct, tie broken toward more losses) across all `(franchise, season)`. **Multi-valued on tie (C6):**
  the render lists ALL co-holders, never one arbitrary franchise. Pairs with The Perfect Storm (increment 3,
  permanent multi-list) per C6 - distinct artifacts, distinct custody.

## 4. Wave 2 - 2 plaques after a scoped engine->frontend sync extension

### 4.1 The sync extension (engine-derived, immutable, same provenance idiom)

Both facts are exactly derivable off completed `WEEKLY_MATCHUP_RESULT` (winner/loser scores per matchup):

- **points-against** per `(franchise, season)` = sum of opponents' scores. Add as a column on
  `franchise_season_records` (sibling of `points_for`), `provenance = 'engine:matchup-derived'`, immutable.
- **blowout wins (>= 60)** per franchise = count of wins where `winner_score - loser_score >= 60`. The
  **60 is a pinned definitional constant** (not a runtime knob); the engine computes the count; sync carries
  it (a column on a per-franchise all-time record sibling, or recomputed-on-sync). Migration mirrors siblings
  (immutable, engine-provenance). FRESH prod object-existence probe before any apply (standing hazard).

### 4.2 The reads

- **#28 The Iron Curtain** (best all-time points-allowed avg): `sum(points_against) / seasons` per franchise;
  holder = **min** (best defense). Multi-valued on tie.
- **#27 The Executioner** (most blowout wins, margin >= 60): the synced blowout-60 count per franchise;
  holder = max. Multi-valued on tie. (Probe: holder derives to franchise 0009 - illustrative only, never
  baked into the definition.)

## 5. Deferred - #29 The Unbroken Chain (do not render)

Per D3: not rendered. The qualification (longest consecutive playoff-appearance streak) requires per-season
playoff-entrant facts that are not in the canonical event model (no playoff/bracket event; champion-week
matchups expose only the 2 finalists). Rendering a streak here would be speculation. **One open out before
finalizing the defer:** whether `championship_timeline` bracket-reconstruction independently yields clean
per-season entrants - a follow-on probe can check; absent a clean source, the plaque stays deferred (C5 +
silence over speculation). Registered, not rendered.

## 6. Record provenance chain (drill-in)

A Live Record's "chain" = the chronological history of prior holders, derived by replaying completed seasons
(the mark over time), surfaced on drill-in - the computed analogue of the Belt's ratified chain. No live
counter, no streak-as-game mechanic (C5/boundary): the value and its history are displayed as record, not contest.

## 7. Constitutional carry

C1 (holder = derived read, never stored). C5 (Unbroken Chain = history not gamification; deferred here). C6
(The Floor co-held = multi-valued render). Silence over speculation (Unbroken Chain defers; no guessed
holders or backfill). Boundary: no points/leaderboards/live-streak mechanics; append-only facts; human
approves publication. Architecture frozen.

## 8. Build path (memo 4 registers; EXECUTE builds)

- **Wave 1:** FRONTEND-only - four derived reads off existing synced `franchise_season_records` + the Live
  Records section/cards + multi-valued render for The Floor. No migration.
- **Wave 2:** ENGINE sync extension (points-against + blowout-60 count, derived + immutable) -> sync to
  frontend -> two reads. Founder-applied migration (section 7), fresh prod object-existence probe first.
- **Deferred:** Unbroken Chain (registered).

## 9. Provenance / status

DRAFT, DECIDE 2026-06-22. Memo 3 of the increment-2 chain, on probe-confirmed data and the pinned 60-point
threshold. Pending founder ratification + commit; on ratification, memo 4 registers and the build opens
(Wave 1 first).

