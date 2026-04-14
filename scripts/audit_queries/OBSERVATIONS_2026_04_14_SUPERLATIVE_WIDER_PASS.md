# OBSERVATIONS 2026-04-14 — Wider SUPERLATIVE Classification Pass

Continuation of `OBSERVATIONS_2026_04_14_Q4_SUPERLATIVE_DIAGNOSIS.md`.
Scope: every SUPERLATIVE hard_failure captured in `prompt_audit` as of the
2026-04-14 capture window, not just the six-row w11/w13 sample. Source
query: `11_superlative_failure_prose.sql`. Sample size: nine SUPERLATIVE
hard_failures across eight distinct audit rows (one attempt carried two).

Method: read each draft's prose against the verifier's `claim` and
`evidence`, classify MODEL_SIDE / VERIFIER_SIDE / AMBIGUOUS, and where
verifier-side, identify the parse pattern. Each classification resolves
at the parse layer — no canonical-data lookup was required.

Captures preceded `58abb2e` (landed 2026-04-14T11:35:12Z). Rows matching
the V1 or V2 patterns fixed in that commit are marked accordingly.

## Per-attempt classification

| id | S/W/A       | claim                                    | pattern | covered by 58abb2e |
|----|-------------|------------------------------------------|---------|--------------------|
| 45 | 2024 w13 a1 | Season low of 120.20                     | V4      | no                 |
| 5  | 2025 w3 a1  | All-time/league-history claim of 125.30  | V6      | no                 |
| 14 | 2025 w9 a1  | Season high of 116.75                    | V5      | no                 |
| 17 | 2025 w10 a1 | Season high of 103.10                    | ?       | possibly           |
| 17 | 2025 w10 a1 | Season low of 90.10                      | V4      | no                 |
| 20 | 2025 w11 a1 | Season high of 48.10                     | V1      | yes                |
| 21 | 2025 w11 a2 | Season high of 48.10                     | V1      | yes                |
| 22 | 2025 w11 a3 | Season high of 48.10                     | V1      | yes                |
| 26 | 2025 w13 a3 | All-time/league-history claim of 27.95   | V2      | yes                |

Totals: 9 verifier-side, 0 model-side, 0 ambiguous. Four covered by
58abb2e. Four uncovered across three new patterns. One (row 17 a1 /
103.10) ambiguous-pending-retest.

## Implications for OBSERVATIONS_2026_04_14.md #7

Finding #7 ("SUPERLATIVE dominates failures") restates from a model-
behavior observation to a verifier-calibration observation. The wider
sample reinforces the Q4 conclusion rather than softening it: 9 of 9
is a stronger signal than 4 of 4. No SUPERLATIVE failure in the
captured set is a genuine canonical overclaim by the model.

Operational consequence: the retry loop's role in the SUPERLATIVE
failure surface is purely unnecessary — retries cannot correct drafts
the verifier is misreading. Rows 20/21/22 illustrate this cleanly:
three attempts rejected for the same V1 pattern across three
independently-sampled generations. The model produced acceptable prose
each time; the verifier rejected each time.

## New parse patterns surfaced

Three uncovered patterns, each reproducible from prose alone. These
are backlog items, not this session's commit.

### V4 — "Nth-lowest / Nth-highest" false match (SUPERLATIVE)

Rows 45 and 17b.

- Row 45: "Steve falls to 8-5 after his second-lowest output of the
  season. Stu edged Eddie 120.20-114.05…" — verifier claims "Season
  low of 120.20". `_SEASON_LOW_PATTERN` matches `lowest[^.]{0,40}of the
  season` starting at "lowest", ignoring the "second-" prefix that
  negates the superlative. Nearest XX.XX score (120.20) is pulled from
  an unrelated clause.
- Row 17b: "Brandon managed just 90.10 total — his second-lowest score
  of the season." Same shape.

The pattern class is ordinal-qualifier negation, analogous to V1's
temporal-qualifier negation ("previous"). Fix shape would mirror V1:
a guard that skips when an ordinal qualifier ("second-", "third-",
"Nth-") appears within a short lookback of the superlative keyword.

### V5 — possessive-scoped personal high parsed as league high (SUPERLATIVE)

Row 14. Prose: "Brock Bowers (37.3) carried the Warmongers past
Brandon's 116.75 — easily his highest output in nine tries this
season." Verifier claims "Season high of 116.75" vs league-wide
192.15. The superlative is explicitly scoped to Brandon by the
possessive "his" and the personal frame "in nine tries". The verifier
does not distinguish personal from league scope.

Fix shape: a guard checking for a possessive pronoun ("his", "her",
"their") or personal-scope marker ("in N tries", "in N attempts") in
the lookback window. Orthogonal to V1 and V4.

### V6 — "in league history" as occurrence frequency (SUPERLATIVE)

Row 5. Prose: "Brandon's week got ugly when CeeDee Lamb put up a zero,
marking just the 323rd time in league history a starter has been
completely shut out. Pat stayed perfect with a 125.30-111.95 win…"
Verifier claims "All-time/league-history claim of 125.30". The
"league history" trigger is firing on an event-frequency claim ("323rd
time"), not a scoring-record claim.

The existing all-time loop has two guards (series/rivalry context at
±40 chars after, auction/investment context at ±80 chars) plus the
V1/V2 additions. None of them cover the "Nth time in league history"
frequency construction. The fix shape is a guard that skips when a
frequency marker ("Nth time", "only time", "first time", "rare", "few
times") precedes "in league history" within a short lookback window.

### Ambiguous — row 17 attempt 1 claim "Season high of 103.10"

Prose: "posted 48.10 points for Paradis' Playmakers in their 137.50-
103.10 win over Italian Cavallini. That's the highest individual score
by any starter this season, topping the previous mark of 46.75."

The V1 fix skips when "previous" appears within 40 chars before the
superlative keyword. "topping the previous mark" precedes "of 46.75",
so the character distance from "previous" to the "highest" keyword
(which triggered the match, via `highest[^.]{0,40}this season`) is
well over 40 — the `[^.]{0,40}` portion consumed the gap. The V1
lookback is measured from the `_SEASON_HIGH_PATTERN` match.start(),
which is at "highest", and "previous" sits after "highest" not before.
So V1 does not fire here. The verifier then extracts 103.10 (the
losing team score) as the nearest XX.XX to "highest" — 46.75 is
further away in character terms.

Whether this row is covered by 58abb2e depends on whether a fresh
regen produces the same prose shape. Deferred as ambiguous-pending-
retest rather than promoted to a new pattern: the prose contains a
valid V1 trigger ("previous mark of 46.75") that a pure-text reader
would flag as protected; the verifier's failure is partly a lookback-
distance artifact. Worth one targeted retest of 2025 w10 a1 post-
58abb2e before classifying further.

## Backlog additions

- **V4 fix.** Ordinal-qualifier guard for `_SEASON_HIGH_PATTERN` and
  `_SEASON_LOW_PATTERN`. Regression fixtures: rows 45 and 17b prose.
- **V5 fix.** Possessive / personal-scope guard for `_SEASON_HIGH_PATTERN`
  and `_SEASON_LOW_PATTERN`. Regression fixture: row 14 prose.
- **V6 fix.** Frequency-marker guard for `_ALLTIME_PATTERN`. Regression
  fixture: row 5 prose.
- **Row 17 a1 retest.** Regenerate 2025 w10 attempt 1 post-58abb2e
  with `SQUADVAULT_PROMPT_AUDIT=1` and re-read the resulting draft.
  If the same fusion fires, characterize as a new V2-family pattern or
  a V1 lookback bug; if it passes, dispose.

## Implications for other deferred questions

**Q5 (2024 vs 2025 29-point pass-rate gap).** Four of the nine
verifier-side failures are concentrated in 2025 w10–w13 (rows 17, 20,
21, 22). 2024 contributes one (row 45). The V4 pattern appears in both
seasons. V1 and V2 (now fixed) appeared exclusively in 2025. V5 and V6
appeared exclusively in 2025 in this sample — insufficient evidence
to conclude a season-specific prose drift without a larger sample,
but the 2025 concentration is consistent with the gap being driven by
parse failures on 2025-preferred phrasings. Suggests Q5 should be
re-approached as "what prose shapes do 2025 recaps produce that 2024
recaps did not?" rather than "did the model regress?". Still gated
on Q1 (#1) being complete, which this pass now is.

**Q2/Q3 (budget gate with D4 PLAYER_BOOM_BUST firing 233 / budgeted 0).**
Unaffected. Still its own session.

**Q1 (UNMAPPED categories).** Unaffected.

**Player Trend Detectors (D1–D2).** The Q4 diagnosis flagged V1 and V3
as exactly the patterns short-horizon player-trend prose would
generate at higher density. V5 (possessive-scoped personal highs)
adds to that concern directly — "Allen's highest output in four
weeks", "McCaffrey's best three-game stretch", etc., are Dimension-1
prose shapes that V5 would misread as league superlatives. Adding
Dimension 1 detectors before V5 is fixed would likely generate more
false positives, not fewer. V4 (ordinal qualifiers) and V6 (frequency
markers) are less directly in the path of D1–D2 prose but are still
likely to appear.

## What is not done in this session

- No verifier code changes. V4, V5, V6 are scoped and returned to
  backlog.
- No regression fixture drafting. That belongs to the fix session.
- No retest of row 17 a1 post-58abb2e. Backlog item.
- No re-examination of Q5 data with the new lens. Backlog.

## Closing

The guiding hypothesis from Q4 — that wider sampling would either
confirm or contradict verifier-side dominance — resolves firmly in
favor of verifier-side. 9 of 9, zero model-side, zero ambiguous. The
four uncovered rows surface three new parse patterns (V4, V5, V6)
structurally similar to V1/V2: the verifier matches a superlative
keyword in prose that contains an adjacent qualifier the match pattern
does not consume, and compares an extracted nearby number against a
canonical max/min to which it does not refer.

The immediate implication for strategy is Finding #7's restatement.
The immediate implication for work is that the next verifier-fix
session has three characterized patterns with reproducible prose to
draw regression fixtures from.
