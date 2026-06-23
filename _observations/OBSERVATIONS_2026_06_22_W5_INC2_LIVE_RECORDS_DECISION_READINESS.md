# Trophy Room (Unit W.5) Increment 2 - Live Records - Decision-Readiness (memo 2 of 4) - DRAFT

**Date:** 2026-06-22
**Session type:** DECIDE (decision-readiness: probes + framing). No repo/DB writes. DRAFT for founder ratification + commit.
**Chain position:** memo 2 of 4 (increment 2). Builds on the selection-prep (memo 1).
**Anchors:** engine HEAD `5464526`; frontend `a6eb95b`. Input: taxonomy v1.2 section 5 (7 plaques).

---

## Part A - Probe: data-source partition (confirmed against the repos)

`WEEKLY_MATCHUP_RESULT` (engine canonical) carries `winner_score` / `loser_score` / franchise IDs /
`is_tie` per matchup, so margins and points-against are exactly derivable at the engine (margin
computation already exists in `hall_of_fame_render_v1`). The frontend holds `franchise_season_records`
(008): `(franchise, season, wins, losses, ties, points_for, result[CHAMPION/RUNNER_UP])`, synced. The
7 plaques partition three ways:

| Group | Plaques | Status |
|---|---|---|
| **A - ships now** | #24 Cavallini Standard (aggregate win-pct), #25 Dynasty (count CHAMPION), #26 Eternal Runner-Up (count RUNNER_UP, zero titles), #30 The Floor (worst season W-L; co-held) | From existing synced `franchise_season_records`. No new data. |
| **B1 - exactly derivable, needs a scoped sync extension** | #28 The Iron Curtain (points-against avg), #27 The Executioner (blowout wins above a margin) | Engine has the raw facts (opponent scores -> points-against; winner-loser delta -> margin). Add the exact derived facts to the engine->frontend sync. |
| **B2 - derivability UNCONFIRMED, defer candidate** | #29 The Unbroken Chain (longest playoff-*appearance* streak; C5) | Requires "made the playoffs" per season. `franchise_season_records` records only CHAMPION/RUNNER_UP; the 008 comment flags granular playoff finish as "not exactly derivable." If playoff appearance is not exactly recorded in canonical data, DEFER per silence-over-speculation - do not render a guessed streak. |

## Part B - Framing the decisions (each ready for your ruling)

### D1 - Staging (recommended: ship in waves)

- **Wave 1 (now):** Group A - 4 plaques on existing synced data. No engine change. Lowest risk; delivers
  the marquee records (win-pct leader, dynasty, runner-up, The Floor) immediately.
- **Wave 2:** Group B1 - 2 plaques after the sync extension (D2). Exactly derivable; no constitutional risk.
- **Deferred:** Group B2 - The Unbroken Chain, pending the playoff-appearance derivability check (D3).

Founder to rule. Alternative = hold all 7 until B1/B2 resolve; not recommended (delays 4 ready plaques).

### D2 - Sync extension scope (Group B1)

Minimal exact additions to the engine->frontend sync, both computed off completed `WEEKLY_MATCHUP_RESULT`:
- **points-against** per (franchise, season) - sum of opponents' scores. Add as a column on
  `franchise_season_records` (or a sibling), engine-derived, immutable, same provenance idiom.
- **blowout wins above the margin threshold** per franchise - count of wins where `winner_score -
  loser_score >= threshold`. The **threshold is a definition input** the spec must pin (a stated constant,
  not a tunable) - founder confirms the margin value. Reuse the existing engine margin computation.

No new prediction or aggregation beyond exact counts off completed facts. Founder to rule on the threshold.

### D3 - The Unbroken Chain (C5) - a data-fact check only you can answer

C5 permits the streak ONLY as history computed from completed postseason facts. The open question is
purely factual: **is "which franchises made the playoffs each season" exactly recorded/derivable in the
canonical data, or not?** If yes -> it joins Wave 2 (derive the consecutive-appearance streak, display as
history, never a live counter). If no -> DEFER; render nothing rather than a guessed streak (silence over
speculation). Founder/data confirms; the spec does not assume.

### D4 - Derived-holder read for traveling records (no manual ledger)

A Live Record's current holder = the current extreme value computed from the data (max win-pct, most
titles, worst season, etc.) - a derived read, never stored (C1), never the manual `trophy_custody_events`
ledger (that is the Belt's). **The Floor is multi-valued on tie (C6):** the render shows ALL co-holders,
never one arbitrary holder. The provenance "chain" for a record = the chronological history of prior
record-holders, itself derivable by replaying completed seasons - surfaced on drill-in, like the Belt's
chain but computed, not ratified.

### D5 - Rendering (reuse the shared architecture)

The Live Records section reuses increment 1's Room sections, Trophy Card, Docket ID (`TR-LRC-<#>-<season>`),
trust bar (CANONICAL - engine-derived facts), and approval flow. No new custody machinery; no points,
leaderboards, or live streak counters (C5/boundary) - the record value and its transfer history are
factual, displayed as history.

## Part C - What memo 3 (specification) executes

The Group A derived reads (4) + the multi-valued co-held render (The Floor); the Group B1 sync extension
(points-against, blowout-count at the pinned threshold) + their reads (2); the deferred-or-derived
disposition of The Unbroken Chain per D3; the record provenance-chain drill-in. All on the increment-1
shared architecture.

## Constitutional carry

C1 (holder = derived read, never stored). C5 (Unbroken Chain = history, not a live counter; exact
postseason facts only). C6 (The Floor co-held = multi-valued render). Silence over speculation (B2 defers
rather than guesses). Boundary: no points/leaderboards/live-streak mechanics; append-only; human approves.

## Provenance / status

DRAFT, DECIDE 2026-06-22. Memo 2 of the increment-2 chain. Part A is probe output; Part B frames D1-D5 for
ruling. The only item needing a founder fact (not a design choice) is D3 (playoff-appearance derivability).
On ratification, the rulings feed memo 3.

