# D39 playoff_appearances - Dead Over-Count Removed

Engine HEAD at diagnosis: 5b11d2e
Date: 2026-06-08
Type: defect disposition. Code change in the preceding commit; this memo records
the diagnostic finding. No fact writes; no approvals.

## Standing item
Roadmap v2 section 7.3 lists D39 (detect_championship_history): playoff_appearances
dict over-counts per-matchup rather than per-season; the over-counting is silent
(no verifier catches it; no surface surfaces the raw count); recorded for
visibility, no action until a surface consumes the raw count. This memo resolves
it.

## Diagnostic (read-only)
detect_championship_history declared an internal playoff_appearances dict and
incremented it once per playoff matchup (per game), so a franchise that played N
playoff games in a season tallied +N rather than +1 - the per-matchup over-count.
But the dict was dead: never read after population. The emitted CHAMPIONSHIP_HISTORY
angles ("appeared in the championship matchup N times" / "never appeared") are
built entirely from a separate champ_appearances dict. Grepping the function
confirmed playoff_appearances appeared only at its declaration and two increments.

Blast radius was zero. The natural consumer, A3's Championship Timeline, computes
playoff-season appearances independently with per-season set semantics
(compute_cross_season_playoff_records) and its docstring explicitly stated it does
not consume D39's playoff_appearances dict, precisely to avoid inheriting the
over-count. So the correct version already existed and nothing read the buggy one.
The consumed champ_appearances path is separately guarded by the CHAMPIONSHIP_CLAIM
verifier.

D39 was therefore not a live output defect; it was an inert over-counting landmine
in unused code.

## Disposition
D3 option (a), founder-ratified: DELETE. The dead playoff_appearances declaration
and its populating loop are removed from detect_championship_history; the
playoff_weeks list it shared with championship-week detection is retained. The A3
docstring is updated to past tense (the dict was removed) so its maintainer warning
does not dangle. Removing the logic at the source is more robust than relying on a
cross-file docstring to deter a future lift.

Behavior-safe (the dict was never consumed; output unchanged) and reversible.

## Constitutional compliance
The dict was derived, unused intermediate state, not facts. Removal deletes no
facts (canonical_events / memory_events untouched), changes no output, and
eliminates a latent derived-fabrication risk (a per-matchup playoff-appearance
count the substrate would not support per-season).

## Closure relevance
Resolves the Roadmap v2 section 7.3 D39 standing item. With D50 (unwired), the two
detector fitness/defect standing items flagged toward Closure Memo certification
C6 (no open P0/P1 defects) are now cleared.

## Provenance
Read-only diagnostic over the source plus the franchise_deep_angles and
championship_timeline aggregation unit tests (95 passing). Code change in the
immediately preceding commit. No DB writes; no narrative generation; no API; no
approvals.
