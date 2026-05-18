# Arc 1–3 Closure Memo: Data Integrity + Player Performance Layer
## SquadVault | Commissioner Review Arc
**Date:** 2026-05-17
**HEAD at closure:** f1d53a9 (on GitHub; 8bcb58a in container)
**Arc open commit:** e0b870f (docs: Arc 1 completion memo)
**Arc commits:** 6 total (Arc 2: 8f61ef0, Arc 3: 87fa592, four diagnostic fixes)
**Test baseline at arc open:** 2268 passed / 3 skipped
**Test baseline at arc close:** 2308 passed / 3 skipped (+40 new tests)

---

## Why this arc existed

The 2026-05-16 commissioner review of all 13 approved 2025 season recaps
revealed that 12 of 13 required at least one factual edit before distribution.
The fabrication problem was characterized before arc open (Arc 1 session brief
`_observations/session_brief_commissioner_review_arc.md`). This arc executed
the fix across three sub-arcs and a validation pass.

Goal: hard factual errors do not reach the commissioner. The commissioner reads
a recap, judges quality, and approves or rejects it. No fact investigation required.

**Result: goal achieved.** W4 2025 — the primary regression target — passes clean
on the first attempt with no fabricated players. Brian Thomas Jr., Ladd McConkey,
and Brock Bowers are absent. The fabricated FAAB paragraph is gone.

---

## Arc 1: Data Integrity (8 commits, e0b870f baseline)

### Root causes addressed

| RC | Description | Fix |
|----|-------------|-----|
| RC1 | Writer's Room generates beyond Signal Scout scope — FAAB totals only, no per-player bids | A2 prompt constraint + A3 individual bids in context |
| RC2 | Verifier scope too narrow — FAAB, historical, average, streak claims unchecked | B1–B4 new categories (Cat 8 enhanced, Cat 9–11 new) |
| RC3 | Fabrications persist across weeks — same context, same hallucination, retry wastes API | Phase C tier-aware retry (FAAB_CLAIM = Tier 2, no retry) |
| RC4 | Review surface has no claim-level transparency | Phase D verification report in editorial_review_week.py |

### Verifier categories at arc close (15 checks per recap)

| Cat | Name | Severity | Description |
|-----|------|----------|-------------|
|  1  | SCORE | HARD | Matchup scores vs canonical |
| 1b  | SCORE_VERBATIM | HARD | Score string format (relaxed to proximity in validation) |
|  2  | SUPERLATIVE | HARD | Season high / all-time record claims |
|  3  | STREAK | HARD | Win/loss streak counts and direction |
| 3b  | STREAK_INVERSION | HARD | Snapped vs extended inversion |
| 3c  | RECORD_CLAIM_ANCHORING | HARD | League record claims vs angles block |
|  4  | SERIES | HARD | Head-to-head series records |
|  5  | BANNED_PHRASE | SOFT | Cliche / speculation detection |
|  6  | PLAYER_SCORE | HARD | Individual player scores (this week) |
|  7  | PLAYER_FRANCHISE | HARD | Player-franchise attribution |
|  8  | FAAB_CLAIM | HARD | FAAB dollar amounts (enhanced: two-pass, no early-return) |
|  9  | CHAMPIONSHIP_CLAIM | HARD | Championship appearance counts vs WEEKLY_MATCHUP_RESULT |
|     | SEASON_RECORD_CLAIM | HARD | Season W-L records vs computed wins/losses |
| 10  | PLAYER_AVG_CLAIM | HARD | Player scoring averages (±10% tolerance) |
| 11  | NUMERIC_UNANCHORED | SOFT | Aggregate transaction counts + precision historical ordinals |
| 12  | PLAYER_STREAK_CLAIM | HARD | N-straight X+ point game claims (Arc 3) |

### Phase E: Verification query library

Five standalone audit scripts at `scripts/audit_queries/`:
- `faab_spend_by_franchise.py`
- `player_bid_lookup.py`
- `championship_appearances.py`
- `season_records_alltime.py`
- `player_scoring_by_week.py`

---

## Arc 2: Player Performance Layer (1 commit, 8f61ef0)

Five phases that reduce fabrication by giving the model verified data to cite.

| Phase | What | Where |
|-------|------|-------|
| A | Season-to-date stats (avg, last 4w, high/low) in PLAYER HIGHLIGHTS | `player_week_context_v1.py` |
| B | Prompt hard rule: season averages must come from PLAYER HIGHLIGHTS verbatim | `creative_layer_v1.py` |
| C | FAAB ROI: total points since acquisition per pickup in Writer Room | `writer_room_context_v1.py` |
| D | Manager identity: owner first name + nickname pushed into prompt | `writer_room_context_v1.py` |
| E | Power rankings: standings renamed, PA added alongside PF | `season_context_v1.py` |

---

## Arc 3: Player Scoring Streak Claims (1 commit, 87fa592)

`verify_player_scoring_streaks()` — Category 12. Catches "fifth straight 25+
point game" type claims against WEEKLY_PLAYER_SCORE. Detects cardinal + ordinal
word forms, two pattern arms. Regression target: W8 2025 "fifth straight 25+
point game from Patrick Mahomes" (actual: correct — 5 straight W4–W8).

---

## Validation pass findings (2026-05-17)

Seven weeks of 2025 regenerated against the new verifier stack.

| Week | Before arc | After arc |
|------|-----------|-----------|
| W1 | Minor trim | Facts-only (SCORE_VERBATIM pre-existing; resolved by proximity fix) |
| W4 | Entire fabricated FAAB paragraph | **Clean pass, 1 attempt** |
| W5 | Invented "323rd time" statistic | Pass; "323rd" now flagged SOFT by Cat 11 extension |
| W8 | Approved | Pass; Mahomes streak verified correct |
| W12 | Approved with FAAB fabrication | Facts-only; Jordan Addison ($31) caught by Cat 8 |
| W13 | Approved with multiple errors | Facts-only; SCORE + SERIES + FAAB caught |
| W16 | Wrong championship count | Pass; count correct at temporal scope |
| W17 | Wrong championship count + record | Facts-only; SUPERLATIVE + STREAK caught |

### Four additional fixes from validation diagnostics

| Fix | Commit | What it addressed |
|-----|--------|-------------------|
| FAAB keyword gap (`investment`) | a7b3829 | `"$40 investment in Purdy"` evaded Cat 8 |
| Alias length threshold | f34eaed | `"KP"` (len=2) invisible to championship checker |
| Ordinal count detection | 5c3f587 | `"sixth"` not recognized as a count word |
| SCORE_VERBATIM proximity | 8bcb58a | Natural prose failing strict verbatim check |
| Precision historical ordinals | 8bcb58a | `"323rd time"` fabrication now flagged SOFT |

---

## Confirmed 2025 fabrications — status at arc close

| Fabrication | Week(s) | Category | Status |
|-------------|---------|----------|--------|
| Brian Thomas Jr. ($51, Brandon) | W4, W12 | FAAB_CLAIM | Blocked — no WAIVER_BID_AWARDED record |
| Ladd McConkey ($32, Eddie) | W4 | FAAB_CLAIM | Blocked |
| Brock Bowers ($46, Steve) | W4 | FAAB_CLAIM | Blocked |
| Justin Jefferson ($60, Michele) | W13, W14 | FAAB_CLAIM | Blocked |
| "six times" championship (actual: 7) | W16/W17 | CHAMPIONSHIP_CLAIM | Blocked — ordinal + short-alias detection added |
| "12-2 record" (actual: 15-2) | W17 | SEASON_RECORD_CLAIM | Blocked |
| "323rd time a starter zeroed out" | W5 | NUMERIC_UNANCHORED | Flagged SOFT |

---

## What is NOT in scope — remains for future work

- **Arc 2 context quality validation** — per-player season stats in PLAYER HIGHLIGHTS
  need a validation pass to confirm the model is citing them rather than
  synthesizing independently.
- **W17 SUPERLATIVE gap** — model claimed 45.60 as season high (actual: 51.85).
  Cat 2 correctly blocks this; root cause (season-high context not surfaced
  for individual players) is a separate thread.
- **Cumulative season points claims** — "228.50 total points" for Darnold (W16).
  No category currently verifies this. Candidate for Arc 4.
- **Phase 11 A1 implementation** — Hall of Fame & Shame surface. Next on the
  Phase 11 surface track per roadmap leading hypothesis.
- **E1 revision-point** — gated on NFL Week 1 ~2026-09-08.

---

## Cross-references

- Arc 1 session brief: `_observations/session_brief_commissioner_review_arc.md`
- Arc 1 A1 audit memo: `_observations/OBSERVATIONS_ARC1_A1_WRITERS_ROOM_AUDIT.md`
- Arc 1 completion memo: `_observations/OBSERVATIONS_ARC1_COMPLETION.md`
- 2025 season review: `_observations/OBSERVATIONS_2026_05_16_RECAP_REVIEW_ARC_FULL_SEASON_2025.md`
- Phase 11 roadmap: `_observations/OBSERVATIONS_2026_05_10_PHASE_11_ROADMAP.md`
