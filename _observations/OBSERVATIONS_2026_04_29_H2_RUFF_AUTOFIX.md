# Observations — H2 Tests/ ruff auto-fix shipped (2026-04-29)

## Summary

H2 from `_observations/PRIORITY_LIST_2026_04_28.md` shipped:
mechanical ruff auto-fix across `Tests/`, eliminating 206 of the
229 auto-fixable lint errors. The remaining 23 are manual-only
and deferred to a future H2b session.

The fix is locally-generated rather than apply-script-delivered
because `ruff check Tests/ --fix` is fully deterministic against a
fixed source tree and ruff version. Generating the diff in a
delivery sandbox and on the canonical clone produces identical
output. Shipping 88 file replacements in an apply script would have
been heavyweight for no benefit; the runbook (`h2_runbook.md`) makes
the local generation followable.

## What shipped

Single commit modifying 88 files in `Tests/`:

- **103 I001 (unsorted-imports)** — alphabetical reordering only.
  Style change, zero behavior impact.
- **89 F401 (unused-import)** — deletion of imports not referenced
  anywhere in the file. Safety audited before applying:
  - 50 stdlib imports (pytest x24, json x9, os x4, tempfile x4,
    sqlite3 x2, unittest.mock.patch x2, warnings x1, sys x1,
    ast x1, pathlib.Path x1, unittest.mock.MagicMock x1). All
    are pure-API stdlib modules with no import-time side effects.
  - 39 own-project `squadvault.*` imports. Safe by construction:
    deleting an unused own-project import cannot change behavior
    unless the name is used somewhere, and ruff's F401 verifies
    it isn't.
  - **Zero third-party imports deleted.** No risk of removing a
    side-effect import from a library that registers something
    on import.
- **13 F541 (f-string-missing-placeholders)** — `f"foo"` →
  `"foo"`. Behavior identical; one less character per occurrence.
- **1 F811 (redefined-while-unused)** — single duplicate-import
  cleanup.
- **~22 cascade fixes** surfaced after the first batch landed
  (e.g., F541 on a line that also needed I001 reordering).

Total: 88 files, +296/-399 lines, net -103 lines.

## What remains

23 manual-only errors deferred to H2b:

| Rule | Count | Description |
|---|---|---|
| E702 | 9 | multiple-statements-on-one-line-semicolon |
| E731 | 7 | lambda-assignment |
| E741 | 4 | ambiguous-variable-name |
| F841 | 3 | unused-variable |

Each requires per-occurrence judgment:

- **E731 (lambda → def)** is sometimes the right call and sometimes
  not, depending on whether the lambda is being passed as a callback
  vs. assigned to a name for re-use.
- **E741 (ambiguous variable names like `l`, `I`, `O`)** in test
  fixtures may be intentional (matching a domain spec); needs eyes.
- **E702 (multiple statements with `;`)** is usually a refactor
  candidate but occasionally appropriate for tight test setups.
- **F841 (unused variable)** sometimes flags intentionally-discarded
  return values that should become `_ = expr` rather than be deleted.

H2b's effort estimate: 1 session of focused review.

## Why locally-generated rather than apply-shipped

Standard delivery pattern in this project is:

```
present_files → cp from ~/Downloads → validate → commit
```

This works well for 1–10 files. For 88 files it adds friction (88
separate `cp` invocations, 88 separate `apply_one` calls in a shell
script) without adding correctness. The fix itself is pure
deterministic ruff output; it does not need to be generated in a
delivery sandbox to be applied. The runbook (`h2_runbook.md`) makes
the local generation a single-command task.

This is a one-off for H2. Future deliveries continue to use the
canonical apply-script pattern.

## Findings

### F1 — H2's "auto-fixable" count had upstream drift

The priority list memo carried H2 as **229 errors / 206 auto-
fixable**. After applying `ruff check --fix`, ruff reported 228
fixed (not 206) — a net of 22 cascade fixes that surfaced once
the first batch had landed.

The mechanism: ruff's `--statistics` flag shows the count per rule
*as detected in one pass*. Once fixes apply, lines that were
previously masked by other lint errors become visible to ruff as
new lint errors and get fixed in the same `--fix` pass. The
priority list's "206" was correct at the time of measurement; the
"228" is correct at the time of application; both are honest
counts of different snapshots.

Lesson for future ruff-cleanup planning: the auto-fixable count
reported by `--statistics` is a lower bound on actual fixes a
`--fix` pass will produce, not an exact predictor.

### F2 — F401 audit methodology is reusable

The audit pattern used here (categorize unused imports as stdlib
vs. own-project vs. third-party; flag any third-party as
side-effect risk; spot-check stdlib for `filterwarnings`-style
patterns) is the right shape for any future F401 cleanup pass. It
took ~10 minutes and produced a defensible "safe to auto-fix"
declaration.

For H2b's manual review: a similar pre-audit pattern won't apply
because the remaining rules (E702/E731/E741/F841) are inherently
per-occurrence judgments, not categorical safety decisions.

## Current state

- HEAD on `origin/main`: this commit.
- `ruff check Tests/`: 23 errors remaining (down from 229).
- `ruff check src/`: clean (unchanged, not in scope).
- `pytest Tests/`: full suite passes.

## Priority list update needed

`_observations/PRIORITY_LIST_2026_04_28.md` should be amended in a
future session (along with the H1+H4+H3 closure already pending) to:

- Mark H2 mostly-CLOSED (the auto-fixable subset).
- Promote the manual-only 23 to a new H2b entry with the per-rule
  count.

## Cross-references

- `_observations/PRIORITY_LIST_2026_04_28.md` item H2.
- `_observations/OBSERVATIONS_2026_04_28_TRACK_A_FIRST_DISTRIBUTION.md`
  through to today's other observation memos for the larger session
  context.
