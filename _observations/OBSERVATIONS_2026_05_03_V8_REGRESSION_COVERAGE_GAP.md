# OBSERVATIONS_2026_05_03_V8_REGRESSION_COVERAGE_GAP

Discipline finding surfaced during the V8 "to"-form follow-up commit
(`c1b1eb0`). The three pre-existing rows in
`TestRegressionV8SuperlativeMatchupLine`, originally added to pin
OBSERVATIONS_2026_04_15 Finding 3 (FP-SUPERLATIVE-MATCHUP-LINE), did
not exercise the V8 matchup-line guard's positive-skip code path.
The class was load-bearing in name only.

The brief for the V8 follow-up instructed mirroring those rows in
"to" form and verifying that the mirror failed at HEAD as a
diagnostic-first proof-of-bug. The mirror passed at HEAD. That
should not have been possible if the originals were real coverage,
which prompted the audit below. Resolution: option 2 of three —
add genuinely-triggering rows alongside the originals, leave the
originals untouched in this commit, write this memo. The originals'
fate is open.

## Evidence

### `test_v8_matchup_line_not_flagged_as_season_high` — vacuous

Prose:

```
F3 cruised to a 137.50-103.10 win over F4. It was the best output
of the season for F3.
```

Pattern:

```
_SEASON_HIGH_PATTERN = (?:season[- ]?high|highest[^.]{0,40}(?:this season|of the season|season))
```

Branch 1 (`season[- ]?high`) requires literal "season high" /
"season-high" — not in prose.
Branch 2 (`highest[^.]{0,40}(?:this season|of the season|season)`)
requires literal "highest" — not in prose. "best" is not in the
regex.

Result: `_SEASON_HIGH_PATTERN.finditer(text)` yields zero matches.
The `for match in _SEASON_HIGH_PATTERN.finditer(...)` loop in
`verify_superlatives` never iterates. `_extract_nearby_score` is
never called. V8 guard is never reached. `failures == []` is
trivially true.

The test passes regardless of whether V8 recognizes hyphen form,
"to" form, both, or neither.

### `test_v8_matchup_line_not_flagged_as_season_low` — bypassed

Prose:

```
F4 managed just 90.10 in the 137.50-90.10 rout. It was the
second-lowest output of the season.
```

`_SEASON_LOW_PATTERN`'s branch 2 matches "lowest output of the
season" at offset corresponding to the "lowest" anchor. But
`_has_ordinal_qualifier(text, match.start())` returns True on
"second-" (lookback 15 chars; ordinal pattern matches with `[- ]+$`
trailing). The `continue` in `verify_superlatives` skips this match
before `_extract_nearby_score` is called.

Result: V8 guard is never reached because Fix V4 (the ordinal-
qualifier guard) intercepts first. The test docstring acknowledges
this — "matchup-line AND has an ordinal qualifier" — but the
"matchup-line" half is decorative; only the ordinal-qualifier half
does work.

The test passes regardless of V8 state, for a different reason than
the season-high case.

### `test_v8_standalone_season_high_still_flagged` — real, but not V8 positive-path

This row is real regression coverage. Prose `"F4 set a new
season-high with 103.10 points."` triggers `_SEASON_HIGH_PATTERN`
branch 1, no qualifier guard fires, `_extract_nearby_score` is
called and returns 103.10, comparison against actual season-high
(145.30 in the synthetic `matchups`) fails, and the test asserts
that failure. It pins V8's negative case ("V8 must not over-skip
standalone false claims").

It does not exercise V8's positive case ("V8 must skip scores in a
matchup-line pair"), which is the class's stated purpose.

## Class total before `c1b1eb0`

Rows exercising V8's positive-skip path: **zero**.
Rows trivially passing because no superlative check fires: 1.
Rows trivially passing because Fix V4 intercepts first: 1.
Rows pinning V8's negative case: 1.

A regression in V8's hyphen-form handling between the original
commit and `c1b1eb0` would not have been caught by any of these
rows.

## What `c1b1eb0` added

Three new rows in the same class, with prose that:

- Triggers `_SEASON_HIGH_PATTERN` or `_SEASON_LOW_PATTERN` directly
  ("set a new season high mark", "team-wide season high collapse",
  "marked the season low for the league").
- Threads the V1/V4/V5/V6/V7 qualifier guards (no "previous"/"prior",
  no ordinal prefix, no possessive pronoun within lookback, no
  personal-scope marker, no frequency marker).
- Places matchup-line scores closer to the keyword than any
  standalone claim score (so V8's job is to skip them; otherwise
  proximity tiebreaker would extract a matchup-line value and the
  comparison against actual high/low would fail).

All three FAIL at HEAD `2fe75b2` without the V8 "to"-form fix and
PASS after. Verified by `git stash`-ing the source change before
commit.

The new rows cover the "to"-form path. None of them cover the
hyphen-form positive path — which the original three rows were
meant to pin and didn't.

## Open question — fate of the original three rows

The originals stay in the file as of `c1b1eb0`; their disposition
is open. Three options:

**Option A — leave as-is.** Historical record; this memo is the
audit trail. Cost: future readers of the class may believe the
rows pin V8 hyphen-form positive-path coverage that they don't.

**Option B — rewrite with triggering prose.** Each original row
gets prose that genuinely fires the relevant superlative pattern
and reaches `_extract_nearby_score` for a hyphen-form matchup line.
Adds real hyphen-form positive-path coverage to complement the
"to"-form coverage from `c1b1eb0`. Cost: redundancy with the
"to"-form rows (same V8 logic exercised twice, once per separator).

**Option C — delete.** Audit trail of the bug class lives in
`_observations/OBSERVATIONS_2026_04_15.md` and the original
finding-fix commit. The class becomes a "to"-form-only suite.
Cost: hyphen-form V8 positive-path has no regression coverage at
all — relies on the V8 logic being symmetric across separators,
which it currently is, but a future hyphen-only regression would
go uncaught.

Recommended: **B**, on the grounds that hyphen-form V8 positive-path
coverage is a real gap and not a hypothetical one, and the
redundancy is per-separator (cheap) rather than per-pattern. But
it's a judgment call about coverage cost and Steve's call to make.

If B is chosen, the rewrite is mechanical — same prose templates as
the new "to"-form rows, with hyphen-form matchup lines substituted
in. One commit, ~30 lines net.

## Discipline lesson

The "diagnostic instrumentation tracks data-layer contracts" lesson
from `be76817` (Step 4 correction memo) generalizes one rung
further:

> **Regression tests must verify they exercise the code path they
> claim to pin.**

A test that asserts an absence-of-failure ("expected no SUPERLATIVE
failures, got `[]`") is structurally indistinguishable from a test
that fails to invoke the check at all. Both produce `[]`. The
difference is whether the assertion is informative.

Defensive moves that would have caught this earlier:

1. **Pin a positive case before the negative.** When the class's
   purpose is "V8 must skip X", the canonical first row is "without
   V8, X would be flagged" (a fail-then-fix proof). Then "with V8,
   X is correctly skipped." The first row instruments that the
   second row's silence is meaningful.

2. **Cite line/column of the code path under test in the test
   docstring.** Forces the author to articulate "this test reaches
   `_extract_nearby_score` line N" — and reveals when it doesn't.

3. **Coverage-of-V8-guard assertion.** A test could mock or
   instrument `_extract_nearby_score` to confirm it was called
   during the test, separate from the assertion on output. Heavy
   for this codebase's style; mentioned for completeness.

Move 1 is the cheap one and would have been sufficient. Move 2 is
the lightest tooling change.

## Closed / open / superseded

**Closed:**
- V8 "to"-form follow-up thread (`c1b1eb0` shipped, pushed to
  origin).
- Brief deviation rationale (option 2 of three, captured in
  `c1b1eb0`'s commit body).

**Open:**
- Disposition of the original three
  `TestRegressionV8SuperlativeMatchupLine` rows (this memo).

**Superseded:**
- The brief's Preamble check 3 ("narrowed test is the right restore
  target") — true only because the narrowing was placeholder
  language for the V8 bug; restored at `c1b1eb0`.

## History intact

`c1b1eb0` and predecessor commits stay in the log unmodified. The
audit trail of finding-and-correcting the V8 separator drift, plus
this memo's documentation of the regression-coverage gap, is
preserved.

No source changes. Doc-only.
