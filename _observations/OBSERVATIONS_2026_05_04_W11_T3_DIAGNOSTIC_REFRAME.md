# OBSERVATIONS — W11 2025 T3 Detector Investigation

**Date:** 2026-05-04
**HEAD:** `e4c2df8`
**Status:** Diagnosis complete. Original framing was wrong; reframed as paired §10 Q1 thread.

## Original framing (memory #17)

> "W11 2025 T3 detector miss (Brandon at -11 streak should fire HEADLINE
> T3 but didn't in id=140 angles block) — 1-session investigation, could
> be 1-line fix or deeper rework."

The premise was that `_detect_streaks` was failing to produce a
strength-3 angle for Brandon at -11 in W11 2025, and that one fix would
solve the id=140 fabrication ("matching the league's all-time record
for futility").

## Diagnostic findings

**The detector is not the problem.** Probing W11 2025 inputs through
`_detect_streaks` with the same `season_ctx` / `history_ctx` the
production pipeline saw:

```
ctx.standings:
  ...
  0010 Brandon Knows Ball  W=0 L=11 streak=-11

_detect_streaks output:
  - cat=STREAK strength=3 fids=('0010',)
    headline: Brandon Knows Ball on 11-game losing streak
    detail:   Record: 0-11. Lost to Ben's Gods this week — streak extended, not snapped.
```

Detector hits. Strength-3. Correct franchise. Correct headline. The
angle reaches `_all_angles` and survives `detect_narrative_angles_v1`.

**Two distinct bugs cause the production fabrication, not one.**

### Bug 1 — Budget evicts strength-3 STREAK angles

The HEADLINE budget cap is 3. In W11 2025, three other strength-3
angles claim those slots:

- Stu's Crew blowout (FRANCHISE_DEEP)
- Paradis' Packers under 8 points in 4 straight starts (PLAYER_NARRATIVE)
- Allen 51.85 season high (PLAYER_SUPERLATIVE)

Brandon's strength-3 STREAK angle is the 4th HEADLINE. The current
sort key:

```python
_all_angles.sort(key=lambda a: (-a.strength, a.category, a.headline))
```

is `(-strength, category alphabetical, headline alphabetical)`. STREAK
loses every alphabetical tiebreak against `FRANCHISE_DEEP`,
`PLAYER_NARRATIVE`, `PLAYER_SUPERLATIVE` — STREAK is later in the
alphabet than all three.

The result: Brandon's STREAK headline is dropped from the prompt
entirely. The model receives no streak context for Brandon as a
HEADLINE and only sees Brandon mentioned in NOTABLE/MINOR angles
(FAAB, h2h duels) which provide no streak framing.

**This bug is not specific to W11 2025.** Any week where 4+ strength-3
angles compete will evict whichever loses the alphabetical tiebreak.
STREAK will lose every time against FRANCHISE_*, PLAYER_*, and
SUPERLATIVE-category competitors.

### Bug 2 — No T9-LOSS form (§10 Q1)

`_detect_streak_records` produces 0 angles for W11 2025. Why:

- Brandon: `streak = -11`, `history.longest_loss_streak.length = 12`
- T10 condition: `abs(streak) >= record_length` → `11 >= 12` → False
- T9-WIN condition: only fires for win-side streaks
- **No T9-LOSS form exists** by design (memo §10 Q1, see
  `streak_strings_v1.format_streak_record` lines 226-236)

So even if Bug 1 were fixed and the budget kept Brandon's T3 streak
angle, the model would still see *no record-anchor angle*. It would
still have STANDINGS data showing Brandon at 0-11 plus
LEAGUE_HISTORY data showing the 12-game record, and still be capable
of inferring "matching the all-time record for futility" without a
prompt-block citation to anchor against.

The verifier (`RECORD_CLAIM_ANCHORING`, post-`e4c2df8`) catches this
fabrication output-side. But the goal of the angle layer is to
*prevent* the fabrication by giving the model verified phrasing to
copy. T9-LOSS is the missing piece.

## Reframing

The original "1-session detector miss investigation" framing was
incorrect. What's actually true:

1. The streak detector is correct as-is.
2. **Two coupled budget/render bugs are needed for id=140 to be
   prevented at the angle layer.** Either bug alone leaves the
   fabrication possible.
3. Bug 2 (T9-LOSS form) is already named as the §10 Q1 follow-up
   thread. It deserves the standard 4-step playbook: helper, consumer
   refactor, prompt instruction + diagnostic, verifier extension.
4. Bug 1 (budget eviction) is properly part of the §10 Q1 thread's
   *render* step, since adding T9-LOSS as a strength-3 angle (along
   with the existing T3 streak angle) doubles down on the budget
   pressure — both new and existing strength-3 STREAK milestones
   need a reservation strategy or they'll continue to lose
   tiebreaks.

## Proposed budget reservation strategy (for §10 Q1 thread)

Two options, ranked:

**(a) Categorical reservation.** Within the strength-3 sort, reserve
1 of 3 HEADLINE slots for STREAK category if any exists. Other
HEADLINEs compete for the remaining 2 slots.

**(b) Sort key change.** Make STREAK rank higher in the alphabetical
tiebreak by prefix-tagging or moving it to a special sort group.
Less invasive but more fragile.

Decision deferred to the §10 Q1 thread; either is acceptable
prima facie.

## Memory edits performed

- Memory #17 updated: replace "W11 2025 T3 detector miss
  (1-session)" with the more accurate "W11 2025 budget eviction +
  §10 Q1 T9-LOSS form (paired)" framing.
- The W11 2025 row remains a real fabrication but moves from
  "named horizon item" to "test fixture for §10 Q1 thread."

## Closure

This investigation is complete. No code change. The §10 Q1 thread
absorbs the W11 2025 case as additional fixture motivation alongside
the original 5/13 W13 2025 evidence. When that thread starts, this
memo is the canonical pre-read.

## Files referenced

- `src/squadvault/core/recaps/context/narrative_angles_v1.py`
  - `_detect_streaks` (line 142)
  - `_detect_streak_records` (line 539)
- `src/squadvault/core/recaps/render/streak_strings_v1.py`
  - `format_streak_record` (line 176, asymmetric T9 design)
- `src/squadvault/recaps/weekly_recap_lifecycle.py`
  - Budget pass (lines 760-826)
- `_observations/OBSERVATIONS_2026_05_04_STREAK_PROMPT_POST_FIX_OBSERVATION.md`
  - §10 Q1 origin
- `_observations/OBSERVATIONS_2026_05_04_STREAK_VERB_PRE_COMPUTATION_SCOPE.md`
  - Original audit memo with §10 Q1 first surfaced
