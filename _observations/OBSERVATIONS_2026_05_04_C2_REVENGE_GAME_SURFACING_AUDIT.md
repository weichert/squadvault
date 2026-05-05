# OBSERVATIONS — C2 surfacing audit (REVENGE_GAME / TRADE_OUTCOME)

**Date:** 2026-05-04 (evening session)
**HEAD:** `523666c`
**Status:** Diagnosis complete. C2 follow-up from the 2026-04-16 audit closed.

## What this session set out to answer

The 2026-04-16 surfacing audit
(`_observations/OBSERVATIONS_2026_04_16_WRITING_ROOM_SURFACING_AUDIT.md`)
logged Finding C2 as a deferred candidate:

> **C2 — REVENGE_GAME near-void.** 658 detections → 3 budgeted (0.5%).
> Highest detection volume of any MINOR category not in the void list.
> Doesn't appear in the d>5 and b==0 void cutoff because b=3, but
> functionally a void. Pair-scoped, matchup-specific — not obviously
> the same coverage-breadth mechanism. Worth its own audit pass.

The April note flagged "pair-scoped, matchup-specific — not obviously
the same coverage-breadth mechanism" as the open question. This
session investigates that hypothesis with a full reconstruction of
the detector + budget pass against the current corpus (141
prompt_audit rows across 34 distinct (season, week) combinations).

## Probe shape

A first-pass probe (`/tmp/probe_revenge_game_audit.py`) read the
persisted `angles_summary_json` / `budgeted_summary_json` columns and
got `franchise_ids=()` everywhere — the persisted summary strips
franchise_ids during persistence
(`prompt_audit_v1.py::_angles_summary`, line 174: "*we do not store
full angle bodies*"). The persisted summary tells us *which detectors
fired*, not *who they concerned*. Insufficient for testing the
pair-scope hypothesis.

The replacement probe (`/tmp/probe_revenge_game_audit_v3.py`)
reconstructs the detector pipeline by re-running all six detector
entrypoints for every distinct `(season, week)` in the corpus, then
applies the budget pass byte-for-byte from
`weekly_recap_lifecycle.py:760-826`. Output: per-category detection
volume, budgeted count, surfacing rate, `is_covered=1` rate, and
average franchise_ids tuple length, sorted by detection volume.

This reconstruction approach is reusable for future surfacing audits
where the persisted summary's stripped fields hide the question.

## Findings

### 1. The pair-scope hypothesis is partially refuted

April's framing — "REVENGE_GAME's pair-scoped, matchup-specific shape
is not the same coverage-breadth mechanism" — implied pair-scope is a
distinct dropper from the volume mechanism that affected single-
franchise categories. The data does not support that.

| Category                          | Det | Bud | Surf%  | cov=1% | fids | pair? |
| :-------------------------------- | --: | --: | -----: | -----: | ---: | :---: |
| **REVENGE_GAME**                  | 296 |   8 |  2.70% | 49.66% | 2.00 | yes   |
| CHRONIC_BENCH_MISMANAGEMENT       | 296 |   8 |  2.70% | 64.53% | 1.00 | no    |
| SEASON_TRAJECTORY_MATCH           | 264 |   6 |  2.27% | 65.15% | 1.00 | no    |
| PLAYER_BOOM_BUST                  | 231 |   7 |  3.03% | 72.73% | 1.00 | no    |
| THE_ONE_THAT_GOT_AWAY             | 147 |   4 |  2.72% | 71.43% | 1.00 | no    |
| RIVALRY                           |  62 |   7 | 11.29% | 43.55% | 2.00 | yes   |

REVENGE_GAME surfaces at 2.70% — **identical to CHRONIC_BENCH_MISMANAGEMENT
at the same detection volume**, despite CHRONIC_BENCH being single-
franchise. Other pair-scoped categories sit at typical-or-above-
average rates: RIVALRY at 11.29%, PLAYER_DUEL at 4.11%. Pair-scope
itself is not a structural disadvantage.

The aggregate pair-vs-single rollup confirms the same: pair-scoped
categories surface at 2.82%; single-franchise categories at 5.52%.
About 2× worse, not 20× worse. Pair-scope is a *minor* amplifier of
the surfacing disadvantage, not the dominant mechanism.

### 2. The dominant mechanism is volume-vs-cap

The cleaner pattern, visible across the full table:

| Detection volume | Categories at that volume       | Surf%    |
| ---------------: | :------------------------------ | -------: |
| 296              | REVENGE_GAME, CHRONIC_BENCH     | 2.70%    |
| 264              | SEASON_TRAJECTORY_MATCH         | 2.27%    |
| 231              | PLAYER_BOOM_BUST                | 3.03%    |
| 147              | THE_ONE_THAT_GOT_AWAY           | 2.72%    |
| 73               | PLAYER_DUEL (pair)              | 4.11%    |
| 62               | RIVALRY (pair)                  | 11.29%   |
| 39               | STREAK                          | 20.51%   |
| 14               | SCORING_MOMENTUM_IN_STREAK      | 7.14%    |

A clean inverse relationship: **higher detection volume → lower
per-firing surfacing rate**. This is exactly what the 1-per-category
cap predicts. With 34 weeks × 1 slot per category per week = 34 max
surfacings per category. A category at 296 detections has a ceiling
surfacing rate of 34/296 ≈ 11.5%. Most surface lower because the
rotation hash + breadth-coverage selection distributes the available
slot across competing categories that week.

The mechanism is the same as April's Finding A (six categories
losing the 4-slot MINOR cap to AUCTION_BUST + BENCH_COST_GAME), now
observed through a different lens. April measured at the slot-cap
level (4 MINOR slots, taken by other categories). C2 measures at the
category-cap level (1 slot per category, repeating the same pattern
within REVENGE_GAME's own slot budget).

### 3. is_covered shows a real but modest pair-scope effect

Pair-scoped categories average **lower** `cov=1` rate than single-
franchise (49.66% REVENGE_GAME, 50.00% TRADE_OUTCOME vs. 65-75% for
high-volume single-franchise categories). This is the expected
directional effect: `fids.issubset(_covered_fids)` requires *all*
franchise_ids to be covered, which is harder to satisfy with two
than with one.

But this advantage is small and is offset by losses on the rotation
hash tiebreak. Net: pair-scope is a 1.5-2× modifier on surfacing rate
(seen in the aggregate rollup), not the explanatory mechanism for
0-3% rates.

### 4. Three special-case categories worth naming

**PLAYER_JOURNEY** at 221 detections → 0 surfaced is a clean
anomaly. avg fids = 5.18 (multi-franchise — players who've been on
many franchises). cov=1% = 53.85%. The category fires at extreme
volume on W1 only and consistently loses to other W1-only categories.
This matches April's Finding B (W1-deluge detectors compressed by
1-per-category to 1 candidate slot, then losing the rotation hash to
specific competitors). C2 confirms April's diagnosis here without
adding new evidence.

**TRADE_OUTCOME** at 12 detections → 0 surfaced is the
remaining-question case. Sample size is small enough (12) that the
0% rate may be coincident — `is_covered=1` rate of 50% means 6 of 12
were ranked-disadvantaged at sort time, and the remaining 6 still
needed to win the rotation hash against competing single-franchise
categories with `is_covered=0`. The dataset cannot distinguish
"systematic deprioritization" from "small sample with adverse
rotation draws." Worth naming; not load-bearing.

**RIVALRY** at 62 detections → 11.29% surfaced is the most
interesting positive case for pair-scope. Pair-scoped, lower
detection volume than the void-rate categories, surfaces *above*
single-franchise average. Suggests that when a pair-scoped category
fires at moderate volume, it competes successfully. RIVALRY's lower
volume puts it in a band where the 1-per-category cap doesn't
saturate.

## Implications for the governance framings

The April audit named three framings for the surfacing void:

1. **Accept and name it.** The current MINOR fill is breadth-over-
   depth by design.
2. **Re-tier specific angle classes.** Move TRADE_OUTCOME (especially
   at gap ≥ 40 strength=2) and SCORING_MOMENTUM_IN_STREAK to NOTABLE.
3. **Question AUCTION_BUST volume.** AUCTION_BUST consumes a
   disproportionate share of MINOR fill.

C2 evidence does not change the case for any of these three. It does
make a fourth framing visible:

4. **Relax the 1-per-category cap for high-volume categories.**
   REVENGE_GAME at 296 detections fits 8 slots across 34 weeks (one
   every ~4 weeks on average via rotation). With 2 slots per week
   for that category, surfacing would roughly double. Tradeoff: the
   coverage-breadth design is a 4-slot ceiling on MINOR with
   1-per-category as the breadth mechanism; raising any per-category
   ceiling either reduces total category diversity per week or
   requires raising the 4-slot MINOR cap (which has its own
   downstream effects). Not a free move.

Framing 4 is structurally different from framings 2 and 3:

- Framing 2 (re-tier) **moves the disadvantaged categories out of
  MINOR**, bypassing the cap. Closest to a defect-fix shape.
- Framing 4 (cap relax) **changes the cap rules**, affecting every
  category that competes for MINOR slots. Larger blast radius.

If a re-tier of REVENGE_GAME / TRADE_OUTCOME / SCORING_MOMENTUM is on
the table (framing 2), C2 supports that move because pair-scope itself
isn't the issue — the issue is the 1-per-category cap interacting
with high-volume categories. Re-tiering these to NOTABLE would
remove them from the cap-bound competition entirely.

But it's a governance call. C2's job is to clarify the mechanism, not
to make the call.

## What C2 changes about how we'd talk about the surfacing question

April: "Pair-scoped angles get systematically deprioritized."

After C2: "High-volume MINOR categories surface at low per-firing
rates because the 1-per-category cap saturates. Pair-scope is a
minor amplifier of this effect, not the cause. PLAYER_JOURNEY
remains a separate W1-deluge case. TRADE_OUTCOME's 0% is small-
sample with adverse rotation."

The corrected framing matters because the wrong fix follows from the
wrong mechanism:

- "Pair-scope causes the void" → fix the pair-scope handling
- "Volume vs cap causes the void" → fix the cap or re-tier the
  high-volume categories

The first fix would be ineffective (RIVALRY is pair-scoped and
surfaces fine; pair-scope handling isn't broken). The second fix
addresses the real mechanism.

## What this memo does NOT do

- **Does not propose a code change.** Read-only diagnostic session.
- **Does not pick a governance framing.** Surfaces the four; the
  call is the commissioner's.
- **Does not action April's Findings A or B.** Those remain in the
  same governance-question state.
- **Does not action C3 (UNMAPPED drift).** Logged in April; not
  pursued this session.
- **Does not re-investigate D4/D49 specifically.** Those were the
  original audit targets; the C2 thread is downstream of them.

## Memory edits

- Memory #17 will drop "Writing Room surfacing void D4/D49" — the
  thread is closed at the diagnosis level; remaining work is a
  governance call, not an investigation.
- This memo is the canonical artifact for that closure.

## Closure

C2 is closed. The hypothesis ("pair-scope causes the void") is
partially refuted. The dominant mechanism is detection-volume vs
1-per-category cap, same root as April's Finding A measured through
a different category. Four governance framings remain open
(commissioner call); none gates further code work.

If the commissioner wants to pursue framing 2 (re-tier specific
categories), the candidate set with C2 evidence is:

- TRADE_OUTCOME (already strength=2 at gap ≥ 40 per detector;
  could be unconditionally NOTABLE)
- REVENGE_GAME (currently MINOR at 296 detections; would benefit
  most from re-tier)
- SCORING_MOMENTUM_IN_STREAK (April-named; C2 confirms 14 → 1 = 7%
  rate, low surfacing but small sample)

Re-tier is a detector-side strength change, the same shape as the
NAv2 normal→rare reclassifications. Single-line edits per category.
Not investigated as scope this session.

## Files referenced

- `_observations/OBSERVATIONS_2026_04_16_WRITING_ROOM_SURFACING_AUDIT.md`
  — predecessor audit (Findings A, B, C1–C3)
- `src/squadvault/recaps/weekly_recap_lifecycle.py` lines 760-826
  — budget pass logic
- `src/squadvault/recaps/writing_room/prompt_audit_v1.py` line 174
  — `_angles_summary` (explains why persisted summary strips fids)
- `src/squadvault/core/recaps/context/player_narrative_angles_v1.py`
  - line 1497 — `detect_revenge_game`
  - line 1773 — `detect_trade_outcome`
- `src/squadvault/core/recaps/context/franchise_deep_angles_v1.py`
  - line 870 — `detect_scoring_momentum_in_streak`
