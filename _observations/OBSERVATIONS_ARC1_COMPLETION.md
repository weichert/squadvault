# Arc 1 Completion Memo: Data Integrity
## SquadVault | Commissioner Review Arc
**Date:** 2026-05-17
**HEAD at completion:** e1246e3
**Baseline at arc open:** 4946733 (2227 passed / 3 skipped)
**Baseline at arc close:** e1246e3 (2268 passed / 3 skipped)
**New tests added:** 41

---

## Goal

Hard factual errors do not reach the commissioner. The commissioner reads a
recap, judges quality, and approves or rejects it. No fact investigation required.

**Result:** Goal achieved. Every identified fabrication pathway now has a
verifier check and a prompt constraint. The review surface surfaces failures
inline before the approval prompt.

---

## Root causes addressed

RC1 (Writer's Room generates beyond Signal Scout scope):
- A2: System prompt hard rule added -- every dollar amount must appear verbatim
  in Signal Scout context. Omit rather than invent.
- A3: Individual player+bid pairs from WAIVER_BID_AWARDED now flow into Writer
  Room context as a labeled block: "ONLY these amounts may be cited in prose."

RC2 (Verifier scope too narrow):
- B1: FAAB_CLAIM check fixed -- removed early-return guard that silently passed
  fabricated acquisitions for players with no WAIVER_BID_AWARDED record.
- B2: CHAMPIONSHIP_CLAIM and SEASON_RECORD_CLAIM added (Cat 9).
- B3: PLAYER_AVG_CLAIM added (Cat 10) -- catches "averaging X points" beyond 10%.
- B4: NUMERIC_UNANCHORED added (Cat 11, SOFT) -- catches aggregate transaction counts.

RC3 (Fabrications persist across weeks):
- C: Tier-aware retry policy -- FAAB_CLAIM and NUMERIC_UNANCHORED are Tier 2
  (no-retry). Same context produces same hallucination; retrying wastes API calls.

RC4 (Review surface has no claim-level transparency):
- D: render_verification_report() in editorial_review_week.py. D1 inline claim
  annotation, D2 summary header, D3 suggested edits, D4 edit burden counter.
  Injected between recap display and decision prompt.

---

## Verifier category inventory at arc close

| Cat | Name                   | Severity | Description                                      |
|-----|------------------------|----------|--------------------------------------------------|
|  1  | SCORE                  | HARD     | Matchup scores vs canonical                      |
| 1b  | SCORE_VERBATIM         | HARD     | Verbatim score string format                     |
|  2  | SUPERLATIVE            | HARD     | Season high / all-time record claims             |
|  3  | STREAK                 | HARD     | Win/loss streak counts and direction             |
| 3b  | STREAK_INVERSION       | HARD     | Snapped vs extended inversion                    |
| 3c  | RECORD_CLAIM_ANCHORING | HARD     | League record claims anchored to angles block    |
|  4  | SERIES                 | HARD     | Head-to-head series records                      |
|  5  | BANNED_PHRASE          | SOFT     | Cliche / speculation detection                   |
|     | SPECULATION            | SOFT     | Emotional attribution                            |
|  6  | PLAYER_SCORE           | HARD     | Individual player scores (this week)             |
|  7  | PLAYER_FRANCHISE       | HARD     | Player-franchise attribution                     |
|  8  | FAAB_CLAIM             | HARD     | FAAB dollar amounts (Arc 1 B1 enhanced)          |
|  9  | CHAMPIONSHIP_CLAIM     | HARD     | Championship appearance counts (Arc 1 B2 new)    |
|     | SEASON_RECORD_CLAIM    | HARD     | Season W-L records (Arc 1 B2 new)                |
| 10  | PLAYER_AVG_CLAIM       | HARD     | Player scoring averages (Arc 1 B3 new)           |
| 11  | NUMERIC_UNANCHORED     | SOFT     | Aggregate transaction counts (Arc 1 B4 new)      |

checks_run = 14 per orchestrator call.

---

## No-retry categories (Tier 2)

FAAB_CLAIM, NUMERIC_UNANCHORED

Rationale: same context produces same hallucination. Correction feedback
does not supply missing data. These failures trigger immediate facts-only
fallback without consuming retry API calls.

---

## Audit query library (Phase E)

Five standalone scripts in scripts/audit_queries/:
  faab_spend_by_franchise.py    -- cumulative FAAB by franchise + per-player breakdown
  player_bid_lookup.py          -- canonical bid for a specific player
  championship_appearances.py   -- championship appearances per franchise
  season_records_alltime.py     -- all-time best season W-L records ranked by pct
  player_scoring_by_week.py     -- player scores by week with avg/min/max

---

## Confirmed fabrications from 2025 review -- status after arc

  Brian Thomas Jr. ($51, Brandon) W4/W12  -> B1 catches (no WAIVER_BID_AWARDED record)
  Ladd McConkey ($32, Eddie) W4           -> B1 catches
  Brock Bowers ($46, Steve) W4            -> B1 catches
  Justin Jefferson ($60, Michele) W13/W14 -> B1 catches
  "six times" championship (actual: 7)    -> B2 CHAMPIONSHIP_CLAIM catches
  "12-2 record" (actual: 15-2)            -> B2 SEASON_RECORD_CLAIM catches

---

## What is NOT in scope -- remains for Arc 2+

- Player performance layer (Arc 2)
- Manager identity / voice profile surface (Arc 3)
- Distribution tooling
- Rivalry Chronicles enhancements
- UI/UX surface (Arc 7)
