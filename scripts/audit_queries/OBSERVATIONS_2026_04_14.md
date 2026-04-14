# Phase 10 Observation — 2024/2025 first pass

*Session date: 2026-04-14. Data: 51 audit rows across 2024 and 2025 regular
seasons, 17 weeks each (week 18 does not produce a draft in either season).
Queries: `scripts/audit_queries/`.*

The session brief called for 3–7 things we didn't already know about the
model's behavior inside the retry loop. Below are seven, ranked loosely by
how much they surprised me. Nothing here is acted upon. Phase 10 is
observation; these are candidates for later phases to consider, not
instructions.

---

## 1. Retry helps on attempt 2, but not again on attempt 3

Combined across both seasons:

| attempt | attempts | pass_pct |
|---------|----------|----------|
| 1       | 35       | 68.6%    |
| 2       | 11       | 54.5%    |
| 3       | 5        | 60.0%    |

The drop from attempt 1 to attempt 2 is expected — only weeks that failed
attempt 1 appear at attempt 2, so conditional-on-failing pass rate of ~55%
is the real comparison. What's notable is that attempt 3 doesn't improve
over attempt 2. If the correction feedback were landing progressively,
attempt 3 should pass more often than attempt 2. It doesn't. Retries earn
their keep mostly at attempt 2; attempt 3 looks close to a coin flip. N is
small (5 rows at attempt 3), but the pattern is consistent with "retry
gives you one more shot at the answer, not a ladder."

## 2. The budget gate is effectively a fixed cap at 12 angles

Q04 against 2025 alone: of 30 attempts, 27 had exactly 12 budgeted angles,
2 had 9, and 1 had 11. Surfaced counts range wildly — 42 to 175 — but
the gate collapses everything to 12 regardless. It's not a soft target
shaped by quality; it's a hard cap. Pass rate at 12 is 51.9%, which is
within a rounding error of the overall pass rate. Conclusion: outcome is
not meaningfully a function of angle count within the budgeted range. The
question "does the model do better with more angles or fewer?" has the
answer "the model sees the same number either way."

## 3. Two distinct modes of detector silence, not one

Some detectors surface constantly but never reach the prompt. Others
don't surface at all. Both look like "I never see this detector in the
drafts" from the outside, but they are different problems. From Q03 on
2025:

- **D13 REVENGE_GAME**: 292 surfaced appearances across 17 weeks, **0 budgeted**
- **D37 SEASON_TRAJECTORY_MATCH**: 235 surfaced, **0 budgeted**
- **D4 PLAYER_BOOM_BUST**: 233 surfaced, **0 budgeted**
- **D15 TRADE_OUTCOME**: 40 surfaced, **0 budgeted** (notable given the
  recent trade-loader rewrite specifically targeted D4 TRADE_OUTCOME silence
  — the detector now emits, but the budget gate drops it)
- **D12 PLAYER_VS_OPPONENT**: does not appear in surfaced at all

The first four are candidates for "budget prioritizer is deprioritizing
whole classes of angle." The fifth is a candidate for "detector isn't
firing in the first place." Different diagnostics.

## 4. 11 runtime categories fall outside CATEGORY_TO_DETECTOR

`prompt_audit_v1.py` says the map "covers all 50 D-attributable categories"
and a drift-detector test backs that claim at CI time. Q09 against the
runtime data shows 11 categories firing that the map labels `UNMAPPED`:

- Matchup flavor: `BLOWOUT`, `NAIL_BITER`, `UPSET`, `RIVALRY`
- Bye-week family: `BYE_WEEK_IMPACT`, `BYE_WEEK_CONFLICT`, `FRANCHISE_BYE_WEEK_RECORD`
- Scoring patterns: `STREAK`, `SCORING_ANOMALY`, `SCORING_RECORD`,
  `SCORING_STRUCTURE_CONTEXT`

Two plausible readings:

(a) These are legitimate non-D-attributable detectors (matchup flavor
helpers, bye-week helpers) that exist outside the D1–D50 scheme. If so,
`UNMAPPED` is a misleading label — the real meaning is `NON_D`.

(b) The drift-detector test is scanning a narrower set of source files
than actually produce categories. If so, the map is genuinely incomplete
and CI has a gap.

The diagnostic that separates them is "grep for these category strings
in source and see where they originate." Not doing that this session.

## 5. First-try pass rate differs by 29 points between 2024 and 2025

- 2024: 14/17 weeks clean on first attempt (82%)
- 2025: 9/17 weeks clean on first attempt (53%)

Too large to be noise on a 17-week sample. Something material changed
between the two seasons' data as far as the model is concerned. Candidate
explanations I cannot rule out from the audit table alone: detectors
added between the seasons' ingest dates, voice profile evolution,
verifier tightening, or the 2025 season genuinely being "busier" in a way
that gives the model more to trip on. The audit table doesn't carry
enough history to distinguish these; the git log and the detector
registry do.

## 6. When the model fails, it tends to fail on multiple things at once

2025: 14 failing attempts, 18 hard-failure entries across them — an
average of 1.29 failures per failing draft. 2024: similar ratio. The
model doesn't make independent single mistakes at a low rate; when a
draft fails, it often fails on both a SUPERLATIVE claim and a STREAK
claim (or SERIES, or PLAYER_SCORE) in the same draft. Reaching for one
unverifiable claim correlates with reaching for others. Failures cluster.

## 7. Zero SCORE failures across 51 attempts

SCORE is the simplest verifier category: did franchise X really score Y
this week? Never fired in either season's audit data. Two readings,
neither confirmable from this data:

(a) The model is bulletproof on basic score citations.
(b) The SCORE verifier is calibrated tightly enough that it effectively
    doesn't exercise in normal operation.

The same is true of `BANNED_PHRASE`: zero failures across 51 attempts.
Either the EAL/voice profile successfully suppresses the forbidden
vocabulary upstream, or the banned-phrase list is narrow enough that
drafts rarely touch it. The silence is informative; its cause is not.

---

## Confirmations (not surprises, but worth having empirical evidence for)

- **Angle-set stability across retries** (Q07). All nine multi-attempt
  weeks in 2025 showed `distinct_angle_sets=1` and `distinct_budgeted_sets=1`,
  with `distinct_drafts=attempts`. The architectural assumption — angles
  are derived once per week, only prose varies across retries — is now
  supported by data, not just inspection of the lifecycle code.

- **SUPERLATIVE is the dominant failure category.** 17 of 25 hard failures
  across both seasons are SUPERLATIVE (68%). Both retry-exhausted weeks
  in 2025 exhausted on SUPERLATIVE. Consistent with the longstanding
  understanding that cross-season "most ever / first ever" claims are the
  hardest to verify.

- **PLAYER_SCORE is the steady #2 failure category** (11 of 25, 44%).
  Roughly stable between seasons.

## Candidate next questions, explicitly deferred

Listed here so they don't get forgotten, not as a to-do list:

1. Where do the 11 UNMAPPED categories originate in source? (Answers #4.)
2. What's the budget gate's priority ordering that zeroes out D13, D37,
   D4, D15? (Answers the surfaces-but-dropped half of #3.)
3. Does D12 PLAYER_VS_OPPONENT have a data dependency that isn't being
   met? (Answers the doesn't-surface half of #3.)
4. Are the two 2025 SUPERLATIVE retry-exhaustions model fabrications or
   verifier false positives? (`scripts/diagnose_draft.py` on
   2025-w11 and 2025-w13.)
5. What changed in detectors/data between 2024 and 2025 that could
   account for a 29-point first-try pass gap? (Answers #5.)

The discipline for now: these are candidates, not assignments. The next
phase gets to look at this list and decide what matters.
