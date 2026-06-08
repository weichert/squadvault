# D50 detect_the_almost - Unfit for Purpose, Unwired

Engine HEAD at diagnosis: a5d27dd
Date: 2026-06-08
Type: detector disposition. Code change in the preceding commit; this memo
records the diagnostic finding. No fact writes; no approvals.

## Standing item
Roadmap v2 section 7.3 lists D50 (detect_the_almost) as a standing finding:
never fired in production across 16 seasons; min_times=3 produces zero angles;
candidate for calibration revisit or unfit-for-purpose finding at the Phase 11
Closure Memo. This memo resolves it.

## Diagnostic (read-only, no API)
A faithful reproduction of the detector's internal cutoff logic was run over the
full matchup history (league 70985, 2010-2025, 16 seasons) via load_all_matchups,
with the real detector cross-checked on the latest playoff week. The zero-fire is
NOT a legitimate null; the detector cannot measure its target phenomenon. Three
structural defects:

1. Wrong playoff cutoff. The detector hardcodes playoff_cutoff = num_teams // 2 =
   top 5. Every season's first playoff week has 4 matchups (8 teams active), so
   the real qualification line is not the 5th/6th win-rank boundary it evaluates.

2. Tiebreaker-blind. It ranks by wins only. In 11 of 16 seasons the 5th/6th
   boundary is a win-total tie (gap 0), decided in reality by points-for, which
   this ranking does not consider. In those seasons it is silent not because
   nobody just-missed but because it cannot represent a tiebreaker-decided bubble.

3. Threshold never reached, and fragile. The strict one-win-gap condition fired
   in 5 seasons (2014, 2016, 2018, 2020, 2022) spread across 4 franchises; the
   max for any one franchise is 2 (Weichert's Warmongers, 0005, in 2018 and 2020).
   min_times=3 is never reached. The silence is one data point from a false claim:
   a future season landing 0005 one win behind the 5th win-rank would publish
   "finished one game out of the playoffs 3 times" - an unverified
   playoff-qualification assertion the substrate does not support (in 2018, 0005
   sat behind a four-way 7-win cluster in a league that plays 8 teams into round
   1; the claim would almost certainly be false).

Fidelity check: real detect_the_almost(current_season=2025, target_week=15)
returned 0 angles, matching the reproduction.

## Disposition
D2 option (a), founder-ratified: UNWIRE. The detect_the_almost call is removed
from detect_franchise_deep_angles_v1; the function is retained inert and its
direct unit tests are unchanged and passing. This mirrors the established D41
(TRANSACTION_VOLUME_IDENTITY) disabled-detector pattern: CATEGORY_TO_DETECTOR
keeps the THE_ALMOST entry, annotated "detector unwired; category still
attested." Behavior-safe (output unchanged today) and reversible (re-add the
call).

Recalibration was rejected: firing correctly would require modeling the real
playoff field and the points-for tiebreaker - playoff-qualification modeling the
substrate does not perform - which is new-foundation work against the frozen
architecture, and the path most likely to manufacture false claims. Silence over
speculation is the tie-breaker.

## Constitutional compliance
A narrative-angle detector is derived context, not facts. Unwiring deletes no
facts (canonical_events / memory_events untouched), changes no current output,
and is reversible. It removes a latent derived-fabrication risk
(playoff-qualification claims the substrate cannot support), aligning with
silence over speculation and the no-new-foundations scope freeze.

## Closure relevance
Resolves the Roadmap v2 section 7.3 D50 standing item and removes a latent risk
against Closure Memo certification C6 (no open P0/P1 defects).

## Provenance
Read-only diagnostic over load_all_matchups plus the detector's own logic; no DB
writes. Code change in the immediately preceding commit. No narrative generation;
no API; no approvals.
