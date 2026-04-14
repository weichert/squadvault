# Candidate Question 4 — 2025 SUPERLATIVE Retry-Exhaustions

Continuation of `OBSERVATIONS_2026_04_14.md`. Scope: the two 2025 regular-season
weeks that retry-exhausted on SUPERLATIVE failures — week 11 and week 13. Six
audit rows total (three attempts each). Goal: classify each rejected attempt
as MODEL_SIDE, VERIFIER_SIDE, or AMBIGUOUS, then decide whether the failure
pattern is predominantly model- or verifier-driven.

Method: read each draft's prose, locate the sentence carrying the flagged
claim, and compare the verifier's stated claim/evidence against the actual
text. No canonical-data lookup was required — all seven flagged claims
resolved at the parse layer (either the verifier misread the prose, or the
prose contradicted itself independent of any canonical check).

## Per-attempt classification

| Week/Attempt | Category      | Classification  |
|--------------|---------------|-----------------|
| w11 a1       | SUPERLATIVE   | VERIFIER_SIDE   |
| w11 a1       | STREAK        | MODEL_SIDE      |
| w11 a2       | SUPERLATIVE   | VERIFIER_SIDE   |
| w11 a3       | SUPERLATIVE   | VERIFIER_SIDE   |
| w13 a1       | PLAYER_SCORE  | VERIFIER_SIDE   |
| w13 a2       | STREAK        | MODEL_SIDE      |
| w13 a3       | SUPERLATIVE   | VERIFIER_SIDE   |

Totals: 5 verifier-side, 2 model-side, 0 ambiguous. All four SUPERLATIVE
failures are verifier-side. Both STREAK failures are model-side.

## Verifier-side failure patterns

Three distinct parse bugs, each reproducible from prose alone.

### Pattern V1 — "previous high" stripped to "high" (SUPERLATIVE)

Seen in all three w11 attempts. The model's prose in each case:

- a1: "That 51.85 breaks the previous season high of 48.10"
- a2: "breaking the previous season high of 48.10"
- a3: "Allen's massive day topped the previous season high of 48.10"

Each draft positions 51.85 as the new high and 48.10 as the prior high. The
verifier records the claim as `"Season high of 48.10"` and compares it
against "actual season-high player score: 51.85" — which is Josh Allen's
week-11 score itself. The verifier appears to extract the numeric object
of "high" without checking for the "previous" qualifier, then compares
against a full-season (current-week-inclusive) maximum. A claim about the
pre-week-N high is not a claim about the post-week-N high.

Ground-truth check against `WEEKLY_PLAYER_SCORE` canonical events
confirms the model's claim was factually correct: the top pre-week-11
2025 starter scores were 48.10 (Jonathan Taylor, W10), 46.75 (Bo Nix,
W7), and 46.70 (Josh Allen, W1). Allen's Week 11 score of 51.85 did
break the prior high of 48.10. The model was right in every particular;
the verifier rejected a true statement.

### Pattern V2 — "all-time record of X" fused with nearest nearby number (SUPERLATIVE)

Seen in w13 a3. The prose:

> "Brandon's historic futility continues — 13 straight losses to start the
> season, with Trevor Lawrence's 27.95 points watching from the bench as
> the streak marches toward the all-time record of 15."

The "all-time record of 15" refers to the losing-streak record (15 games).
The 27.95 is Trevor Lawrence's bench score. The two numbers belong to
different clauses with different referents. The verifier records the claim
as `"All-time/league-history claim of 27.95"` and rejects it against
actual all-time high team/player scores (198.80 / 77.00). The verifier
appears to attach "all-time record" to the nearest prior number in the
sentence rather than to the syntactic object of "of."

### Pattern V3 — player name fused with nearby non-player number (PLAYER_SCORE)

Seen in w13 a1. The prose:

> "The Warmongers got 20.30 from Brock Bowers but left 53.90 on the bench,
> including Jared Goff's 27.20."

53.90 is the Warmongers' total bench points. Bowers is correctly given
20.30, and the verifier's evidence confirms 20.30 as Bowers' actual score.
The verifier nonetheless records the claim as `"Player score 53.90
attributed to Brock Bowers"`. The parser appears to have crossed a "but"
clause boundary to attach a subsequent number to a prior player name.

## Model-side failure patterns

Both STREAK failures are the same error: using "snapped" for a losing
streak when the team in question lost the game in question.

- w11 a1: "Ben snapped Brandon's 11-game losing streak with a
  111.60-104.15 victory" — Brandon lost; streak extended to 11.
  The draft itself immediately contradicts the lede: "Brandon remains
  winless at 0-11."
- w13 a2: "Robb snapped Purple Haze's modest momentum with a 101-97
  victory, ending Pat's four-game losing streak" — Pat lost; streak
  extended to 4.

In both cases the verb "snapped" / "ending" is wrong for the direction
of the result. The correct verb would have been "extended." These are
small semantic errors, not canonical-data fabrications. No fact was
invented — only the streak-termination predicate was inverted.

## Implications for OBSERVATIONS_2026_04_14.md #7

Finding #7 ("SUPERLATIVE dominates failures") survives numerically but
changes character substantially. In this sample, SUPERLATIVE's dominance
is entirely verifier-driven: four of four SUPERLATIVE failures are parse
bugs in two distinct patterns (V1 and V2 above). The "the model keeps
overclaiming superlatives" reading is not supported by the data in these
six attempts. The more accurate reading is: the SUPERLATIVE verifier has
at least two parser patterns that misread natural prose, and retry loops
cannot correct what is not actually wrong.

Whether this generalizes beyond w11/w13 is not yet established. Before
treating the generalization as confirmed, the same classification should
be applied to a handful of other SUPERLATIVE failures from the 51-row
audit set. If the pattern holds, Finding #7 should be restated from a
model-behavior observation to a verifier-calibration observation.

## Implications for the remaining deferred questions

Question 5 (2024 vs 2025 29-point pass-rate gap): the gap may be partially
or wholly explained by verifier parse bugs that fire more often on 2025
prose patterns than 2024 prose patterns. Before investigating model-side
drift or prompt drift, it would be worth establishing the verifier-false-
positive rate on both seasons. If the 2025 gap is largely verifier-
driven, there may be no model-side regression to explain.

Question 2/3 (budget gate with D4 PLAYER_BOOM_BUST firing 233 times,
budgeted 0 times): unaffected by this finding. Still its own session.

Question 1 (UNMAPPED categories in source): unaffected. Still tangential.

Player Trend Detectors (D1–D2): the pre-question about adding Dimension 1
detectors before understanding the budget gate still stands. This finding
adds a second pre-question — whether the verifier can correctly handle
the kinds of prose Dimension 1 detectors would generate. V1 (previous-vs-
current) and V3 (player name adjacent to bench total) are exactly the
patterns that short-horizon player-trend prose would generate at higher
density.

## What is not done in this session

- No verifier code changes. Three parse bugs are surfaced (V1, V2, V3);
  fixes belong to their own session.
- No generalization beyond the six w11/w13 attempts. A wider
  classification pass across other SUPERLATIVE failures would upgrade
  or downgrade Finding #7 but is deferred.

## Closing

The session's guiding hypothesis — "if SUPERLATIVE dominance is largely
verifier-side, the strategic picture shifts" — resolves in favor of
verifier-side for this sample. Two-thirds of the failure surface in
w11/w13 is parser-level misreading of prose the model produced correctly.
The remaining third is a small, consistent verb-choice error in STREAK
that the model makes when a franchise loses a game that ends (in the
model's head) a prior trend.

The immediate next session, if this finding is accepted, is a verifier
fix pass against V1, V2, and V3 — one per pattern, with regression tests
drawn from the six drafts in this sample.
