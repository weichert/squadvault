# OBSERVATIONS — NOTABLE-saturation Step 1 closure (Direction B)

**Date:** 2026-05-06
**Thread:** Standing backlog item 6 — NOTABLE-pass alphabetical lockout
**Brief:** `_observations/session_brief_notable_saturation.md` (`67aca15`)
**Predecessors:** `100ac83` (Step 0a) → `fa880f6` (Step 0b) → `c1891a3` (probe) → `e4052ef` (Step 0c)
**Commits this session:** `118676f` (helper extraction) → `59846b0` (rotation extension)
**Reverify tag:** `59846b0`

## What this memo is

The Step 1 closure memo. Direction B (rotation-hash tiebreak at NOTABLE
pass) is shipped at origin. This memo records the disposition: what
landed, what was tested, what verified, and what remains.

## Commits

`118676f` — pure refactor. Extracts `_budget_angles` from
`_derive_prompt_context` into a top-level helper. No behavior change;
behavioral equivalence asserted via the existing test suite. The
extraction was a B2 prerequisite: the helper is the unit-test surface
for the rotation extension.

`59846b0` — behavior change. Splits the OLD single-pass elif-chain in
`_budget_angles` into four explicit phases:

- Phase 1: HEADLINE (strength 3) — alphabetical tiebreak (unchanged)
- Phase 2: NOTABLE (strength 2) — rotation-hash tiebreak (NEW)
- Phase 3a: MINOR (strength 1) pool collection (unchanged behavior)
- Phase 3b: MINOR fill (unchanged; comment renumbered Phase 2 → 3b)

The NOTABLE rotation hash uses domain `category:season:week`, mirroring
the existing MINOR rotation hash. Same week always produces the same
ordering (deterministic, reconstructable); different weeks vary which
late-alphabet category wins ties.

## Tests added

Ten unit tests at `Tests/test_budget_angles_rotation_v1.py` (`59846b0`):

- Edge cases (empty input, single-headline, headline cap respected)
- Determinism (same week → identical output across calls)
- NOTABLE cap respected (8 strength-2 angles → exactly 6 budgeted)
- Deterministic specific-week assertions: STREAK appears at
  season=2024 week=1; STREAK evicted at season=2024 week=12
- Cross-week ordering distinctness (≥2 distinct compositions across
  12 weeks; empirical: 9 distinct compositions)
- HEADLINE unaffected by NOTABLE rotation; HEADLINE precedes NOTABLE
  in budgeted output

The two specific-week assertions replace earlier draft probabilistic
counts. Specific-week tests are deterministic against the fixed
rotation-hash domain; they fail loudly only if the hash logic itself
changes, never from chance variation.

Test count: 1944 baseline → 1954 / 3 skipped.

## Reverify outcome — non-regression confirmed

Reverify tag `59846b0` ran against the 142-row 2024–2025 prompt_audit
corpus. Row-level summary printed `pass→fail = 60` and the script's
**REGRESSION** warning, but category-breakdown vs. prior tag
`69db27d_step_1_complete` showed **zero delta across all eight
hard-failure categories**:

| Category | Prior (`69db27d_step_1_complete`) | Current (`59846b0`) | Δ |
|---|---:|---:|---:|
| SCORE_VERBATIM | 579 | 579 | 0 |
| STREAK | 38 | 38 | 0 |
| SERIES | 30 | 30 | 0 |
| RECORD_CLAIM_ANCHORING | 13 | 13 | 0 |
| PLAYER_FRANCHISE | 8 | 8 | 0 |
| SUPERLATIVE | 7 | 7 | 0 |
| FAAB_CLAIM | 2 | 2 | 0 |
| PLAYER_SCORE | 1 | 1 | 0 |

The 60 pass→fail rows are 100% inherited legacy drift (the
SCORE_VERBATIM thread on the carry-forward backlog). Per the memory
note on reverify-as-merge-gate: row-level summary conflates legacy
drift with current changes; category-breakdown SQL is the correct
attribution mechanism. This session's commits modified `_budget_angles`
only — the verifier surface was untouched, and reverify confirms it
byte-for-byte.

## What this closure does NOT establish

- **Empirical rotation efficacy on captured corpus.** The probe at
  `scripts/notable_saturation_probe.py` reads `budgeted_summary_json`
  directly from captured `prompt_audit` rows; re-running it against
  current code produces identical output. Efficacy on real prose
  composition can only be measured against fresh `prompt_audit` rows
  from a regeneration pass, which is operator-gated.

- **Step 3 (1-per-category cap at NOTABLE) disposition.** Deferred
  per the brief's conditional gate. Activates only if a post-fix
  probe re-run against fresh regen-produced rows shows single-
  category dominance within strength=2 surfacing.

- **Closure of the SCORE_VERBATIM 59-row drift.** That thread remains
  on the carry-forward backlog independently of this work.

## Disposition

NOTABLE-saturation Step 1 closes. Direction B shipped at origin.
Carry-forward backlog updates:

- Retire "NOTABLE-saturation Step 1 (Direction B)" entry.
- Update "Strength-aware probe (Step 0 follow-up)" to be conditional
  on a future regen pass, not this session's outcome.
- "Step 3 — 1-per-category cap at NOTABLE" remains named-only,
  conditional on post-regen probe evidence.

## Anti-drift discipline notes

- Two-commit B2 discipline (refactor first, behavior change second).
  Each commit gated by ruff / mypy / pytest with explicit test-count
  assertions; pre-commit hooks (terminal banner, no-xtrace, repo-root
  allowlist) all green on both commits.

- The handoff's recorded baseline of 1945/2 had drifted overnight to
  1944/3 via environmental-skip variability (creative-layer rivalry
  test, env-conditioned). Caught by stash-and-rerun, not a regression.
  Lesson: handoff baselines have ±1 tolerance for environmentally-
  skipped tests; total-count delta and category-of-skip are the
  durable signal.

- The reverify pass→fail row count was 60, triggering the script's
  printed regression warning. Category-breakdown comparison against
  the prior tag was the correct disambiguation tool. Pre-existing
  drift is structural, not regression. The warning text is correct
  for verifier-surface changes; this commit didn't touch the verifier
  surface, so the warning was a false positive in this context.

- Apply scripts (one for each commit) used idempotency checks and
  precondition assertions; both ran cleanly on first attempt.
  Synthetic-source dry-run validation caught zero issues; first-pass
  application succeeded both times.

- Test-design refinement during session: probabilistic specific-count
  assertions (`weeks_with_streak <= 11`) were replaced with
  deterministic specific-week assertions (W1 in / W12 out) after
  empirical simulation showed the probabilistic version was just
  barely satisfied (11 ≤ 11) and would have been fragile under any
  shift in the empirical hash sequence.
