# Trophy Room (Unit W.5) Increment 2 - Live Records - Registration (memo 4 of 4) - DRAFT

**Date:** 2026-06-22
**Session type:** DECIDE (registration). No repo/DB writes. DRAFT for founder ratification + commit.
**Chain position:** memo 4 of 4 - closes the increment-2 chain.
**Anchors:** engine HEAD `5464526`; frontend `a6eb95b`.

---

## 1. What this registers

The increment-2 (Live Records) four-memo chain is complete:

1. Selection-prep - `OBSERVATIONS_2026_06_22_W5_INC2_LIVE_RECORDS_SELECTION_PREP`
2. Decision-readiness - `OBSERVATIONS_2026_06_22_W5_INC2_LIVE_RECORDS_DECISION_READINESS`
3. Specification - `OBSERVATIONS_2026_06_22_W5_INC2_LIVE_RECORDS_SPECIFICATION`
4. Registration - this memo

Specified on probe-confirmed data (`w5_inc2_threshold_and_playoff_probe.py`, 1177 decided games), not guesses.

## 2. Binding decisions sealed

- **The Executioner threshold = win by 60+** (pinned definitional constant; 80 blowouts / 17 seasons, ~5/season).
- **The Unbroken Chain DEFERRED** - playoff-entrant facts are not in the canonical event model (champion-week
  matchups expose only the 2 finalists). Rendered = nothing, per silence-over-speculation. One open out before
  final defer: a `championship_timeline` bracket-reconstruction check (registered, non-gating).
- **Staging:** Wave 1 = #24 Cavallini Standard, #25 Dynasty, #26 Eternal Runner-Up, #30 The Floor (existing
  synced `franchise_season_records`, frontend-only). Wave 2 = #28 Iron Curtain (points-against) + #27 The
  Executioner (blowout-60), after the engine->frontend sync extension. Deferred = #29 Unbroken Chain.
- Custody = traveling record: derived-holder reads, multi-valued on tie (C6, The Floor); NO manual
  `trophy_custody_events` ledger (that is the Belt's, increment 1).

## 3. Registration landing (EXECUTE / doc session - repo writes, not this lane)

One topic per commit:

1. Commit the four increment-2 chain memos to `_observations/` (drop `_DRAFT`).
2. Commit the probe `scripts/audit_queries/w5_inc2_threshold_and_playoff_probe.py` (reusable audit query).
3. STATE seating (section 4).
4. Docs-map registration if the gate requires it.

## 4. STATE seating

Add: **"W.5 INCREMENT 2 (Live Records) SPECIFIED 2026-06-22 (DECIDE): four-memo chain complete on
probe-confirmed data. Executioner threshold = 60+ (pinned); Unbroken Chain DEFERRED (not exactly derivable).
Wave 1 = Cavallini Standard / Dynasty / Eternal Runner-Up / The Floor (existing synced data, frontend-only);
Wave 2 = Iron Curtain + Executioner (after points-against + blowout-60 sync extension). Build-ready; Wave 1 first."**
Keep to one dated line.

## 5. Build hand-off (after registration)

- **Wave 1 (EXECUTE, frontend-only):** four derived reads off `franchise_season_records` + the Live Records
  section/cards + The Floor multi-valued render. No migration.
- **Wave 2 (EXECUTE, engine + frontend):** sync extension (points-against column + blowout-60 count,
  engine-derived/immutable, founder-applied migration, fresh prod object-existence probe) -> two reads.
- **Deferred:** Unbroken Chain (registered; optional `championship_timeline` check first).

## 6. Constitutional carry

C1 (holder = derived read, never stored). C5 (Unbroken Chain history-not-gamification; deferred). C6 (The
Floor co-held = multi-valued). Silence over speculation (Unbroken Chain defers). Boundary: no
points/leaderboards/live-streak mechanics; append-only; human approves. Architecture frozen.

## 7. Provenance / status

DRAFT, DECIDE 2026-06-22. Closes the increment-2 four-memo chain. Pending founder ratification + commit; on
ratification, the registration landing lands the chain + probe + STATE, then the Wave 1 build opens (EXECUTE).

