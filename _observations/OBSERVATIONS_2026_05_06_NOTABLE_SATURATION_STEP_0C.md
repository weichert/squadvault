# OBSERVATIONS — NOTABLE-saturation Step 0c — probe findings and direction implications

**Date:** 2026-05-06
**Thread:** Standing backlog item 6 — NOTABLE-pass alphabetical lockout investigation
**Brief:** `_observations/session_brief_notable_saturation.md` (`67aca15`)
**Predecessors:** `100ac83` (Step 0a), `fa880f6` (Step 0b), `c1891a3` (probe)

## What this memo is

This is the Step 0c probe-output memo. The probe at
`scripts/notable_saturation_probe.py` (`c1891a3`) ran against
the 2024-2025 corpus and produced bucket counts per the brief's
Step 0 design, scoped per Step 0b Findings 4-6 (current draft-
pipeline behavior, not historical publication).

This memo records what the probe found, what those findings
support and don't support, and what they imply for the brief's
direction-choice question. No source-code changes. No commits
beyond this memo and the probe at `c1891a3`.

## Probe results

34 weeks analyzed (2024 W1-W17, 2025 W1-W17). Bucket totals:

- NOTABLE_SATURATED_WITH_STREAK_EVICTED: 14 (41%)
- NOTABLE_SATURATED_NO_STREAK_EVICTED: 19 (56%)
- NOTABLE_NOT_SATURATED: 1 (3%)

NOTABLE saturation (n_count == 6) is the norm: 33 of 34 weeks
hit the cap. Only 2025 W3 was unsaturated.

Brief's editorial-tier evidence gate: PASS by wide margin (14
distinct weeks vs threshold of 2).

## The most-evicted-categories table — and what it changes

Top 10 categories present in `angles_summary_json` but absent
from `budgeted_summary_json` across the corpus:

```
REVENGE_GAME:                31 weeks
FAAB_FRANCHISE_EFFICIENCY:   30 weeks
POSITIONAL_STRENGTH:         29 weeks
FRANCHISE_ALLTIME_SCORING:   29 weeks
RIVALRY:                     27 weeks
SCHEDULE_STRENGTH:           26 weeks
SEASON_TRAJECTORY_MATCH:     26 weeks
ZERO_POINT_STARTER:          23 weeks
SCORING_VOLATILITY:          23 weeks
PLAYER_BREAKOUT:             22 weeks
```

STREAK is not in the top 10. The brief's specimen evidence
(id=142) framed STREAK as the canonical victim of the failure
mode. The probe shows STREAK is one of many late-alphabet
categories losing systematically — REVENGE_GAME, FAAB_FRANCHISE_
EFFICIENCY, POSITIONAL_STRENGTH, FRANCHISE_ALLTIME_SCORING,
RIVALRY, SCHEDULE_STRENGTH, SEASON_TRAJECTORY_MATCH, ZERO_POINT_
STARTER, SCORING_VOLATILITY, and PLAYER_BREAKOUT all evict more
frequently than STREAK does.

This is a meaningful reframe. The brief's Direction C (STREAK
reservation) was justified by "STREAK is the load-bearing
category for fabrication prevention." Empirically, STREAK is
*one of many* late-alphabet categories suffering the same
alphabetical-tiebreak mechanism. A STREAK-only reservation
helps STREAK alone; the other 9+ categories continue to lose
under the same mechanism.

## Strength-disaggregation gap (load-bearing caveat)

The eviction counts in the table above are category-set
differences: a category appearing in `angles_summary_json` but
absent from `budgeted_summary_json`. This conflates:

1. **Strength-2 evicted at NOTABLE** — the brief's named failure
   mode at line 781.
2. **Strength-1 evicted at MINOR via 1-per-category cap** — once
   a category lands in MINOR, the cap at line 821-823 prevents
   a second from same category. Other angles in that category
   appear "evicted" even though one did render.
3. **Strength-1 evicted by MINOR pool overflow** — pool cap=4;
   excess candidates get dropped.

Without re-running detectors to recover per-angle strength, the
probe cannot distinguish these tiers. The most-evicted-categories
totals are therefore upper bounds on NOTABLE-tier evictions
specifically; some unknown fraction is MINOR-tier.

A second-order signal in the probe output partially addresses
this. Of the 14 NOTABLE_SATURATED_WITH_STREAK_EVICTED weeks:

- 11 weeks: minor_count=3 (MINOR pool had room and STREAK
  didn't take it). Suggests STREAK was strength-2 and lost
  at NOTABLE specifically.
- 3 weeks: minor_count=4 (MINOR was full). STREAK could have
  been strength-1 lost to MINOR cap rather than strength-2
  lost at NOTABLE.

So at minimum, 11 of 14 STREAK evictions appear NOTABLE-tier.
For the broader most-evicted-categories totals (REVENGE_GAME,
etc.), no per-week MINOR pool data is in the probe output, so
this disambiguation is unavailable for those.

## What the findings support

1. **The brief's failure mode is real and broad.** The
   alphabetical-tiebreak mechanism systematically evicts
   late-alphabet categories. The shape isn't STREAK-specific.

2. **The brief's editorial-tier gate passes.** 14 distinct
   weeks of NOTABLE_SATURATED_WITH_STREAK_EVICTED across
   2024-2025 is well above the brief's >= 2 threshold.

3. **Direction B (rotation hash) is empirically the
   better-fit response.** The brief's Direction B argument 1
   ("other categories may have their own constitutional weight
   that hasn't been audited yet") is now empirically grounded:
   nine other late-alphabet categories evict more frequently
   than STREAK. A category-agnostic rotation addresses all of
   them; a STREAK-only reservation addresses only STREAK.

4. **The probe corroborates Step 0b's framing.** Probe
   results describe current draft-pipeline behavior. They do
   not validate whether any specific 2024-2025 publication
   actually lost any specific angle (Step 0b Finding 5
   establishes this is unknowable). The probe characterizes
   what the pipeline *currently does*, which is the
   intervention surface for Direction B/C.

## What the findings do NOT support

1. **A claim about historical-publication editorial loss.**
   Pre-instrumentation publications cannot be retrospectively
   analyzed; per Step 0b Finding 5, the published recap drafts
   are unrecoverable.

2. **A precise count of NOTABLE-tier vs MINOR-tier evictions.**
   The strength-disaggregation gap means the most-evicted
   counts are upper bounds, not precise NOTABLE-tier eviction
   counts. A follow-up strength-aware probe could resolve this
   if precision matters before direction-commit.

3. **A NOTABLE-cap-raise argument.** The brief explicitly
   rejected Direction D (cap raise) as out-of-scope. The probe
   shows 33 of 34 weeks saturate, which makes the cap pressure
   visible, but the brief's reasoning (cap raise treats symptom
   not mechanism; shifts other budget constraints) is not
   addressed by probe data. Direction D remains out-of-scope
   regardless of saturation frequency.

## An observation worth naming (not a recommendation)

NOTABLE saturation in 33 of 34 weeks is consistent with the
brief's framing (the budget loop is constantly making
prioritization decisions) but also with a less-discussed
possibility: angle-generation richness exceeds NOTABLE
capacity systematically, not occasionally. The brief's
mechanism analysis assumes saturation is the failure-triggering
condition; the probe shows it is the steady state.

This does not change the direction-choice analysis. Direction B
addresses systematic saturation as well as occasional
saturation; the rotation distributes across categories whether
the cap binds 50% of weeks or 97% of weeks. But the steady-
state observation is a feature of the system worth knowing,
even if the brief's scope correctly limits intervention to
the budget-loop tiebreak.

## Implications for direction-choice

The probe shifts the empirical case for Direction B from
"recommended on architectural grounds" to "recommended on
architectural and empirical grounds." Specifically:

- Direction B's argument 1 ("category-agnostic future-proofs
  against load-bearing-ness in other categories") was
  speculative when the brief was written. The probe confirms
  9+ other categories suffer the same mechanism.

- Direction C's argument ("STREAK is uniquely load-bearing")
  is weakened. STREAK is constitutionally important for
  fabrication prevention (Cat 3/Cat 3c verifier surface), but
  the budget-loop loss is structurally identical to losses
  affecting REVENGE_GAME, FAAB_FRANCHISE_EFFICIENCY, etc.
  STREAK's verifier-surface importance is a separate concern
  from its budget-loop position.

The brief's ordering "Mechanism first. Direction second.
Step 0 third. Production fourth." is intact. Step 0a, 0b, and
this Step 0c complete the third stage. Direction commitment
is the next decision; it can be made with the probe evidence
and these three memos as input.

## Disposition

Steve elects in-session whether to:

1. Confirm Direction B and proceed to Step 1 (production
   path) in this session.
2. Confirm Direction B but defer Step 1 to a fresh session.
3. Run a follow-up strength-aware probe before direction-
   commit (resolves the strength-disaggregation gap; would
   require detector re-execution).
4. Park the thread; the four memos at `100ac83`, `fa880f6`,
   this commit, plus the probe at `c1891a3` are sufficient
   context for any future activation.

The session has now produced four sequential durable artifacts
(Step 0a memo, Step 0b memo, probe script, this memo). Each
extended the prior without overturning. Step 0a-0c collectively
constitute the Step 0 deliverable per the brief.

## What this memo does NOT do

- Does not change the brief.
- Does not change source code.
- Does not commit to a direction. The probe evidence supports
  Direction B; the commit to Direction B remains Steve's
  in-session election.
- Does not run Step 1 or any production-path code.
- Does not propose changes to NOTABLE cap, MINOR pool, or
  any other budget structure outside the brief's scope.

## Anti-drift discipline notes

- The probe ran against scoping framing established in Step
  0b. Output explicitly disclaims historical-publication
  inference. The framing held throughout result interpretation.
- The strength-disaggregation gap was named openly rather than
  glossed. Direction-implication analysis was conditioned on
  the gap.
- The "observation worth naming" about steady-state saturation
  was deliberately not promoted to a recommendation. The
  brief's scope on cap-raise rejection holds; the observation
  is a feature of the system, not a thread to open.
- Four-stage pattern (recon -> transform investigation -> probe
  -> findings memo) produced incrementally durable artifacts
  rather than committed errors. The session held to read-only
  discipline through the entire investigation phase.
