# Finding 1 Resolution: W10 + W14 D12 PLAYER_VS_OPPONENT Prose Investigation

**Date:** 2026-04-15
**Predecessor:** OBSERVATIONS_2026_04_15 Finding 1
**Commit under test:** 643b670 (prompt_text capture) + 7d4cbc6 (D12 tuning)
**Method:** Regenerated W10 and W14 with `SQUADVAULT_PROMPT_AUDIT=1`,
then queried `prompt_audit` columns (`angles_summary_json`,
`budgeted_summary_json`, `narrative_angles_text`, `prompt_text`)
to classify behavior as (a) model-side, (b) budget-side, or
(c) detector-side.

## Results

### W10 — Case (c): Detector did not fire

D12 `PLAYER_VS_OPPONENT` produced zero angles for Week 10.  No player
in any starting lineup met all three gates simultaneously:

1. This-week score ≥ 25
2. ≥ 2 prior career starts vs. the same opponent on the same franchise
3. ALL prior starts ≥ 25

This is correct silence.  The 7d4cbc6 sweep estimated ~7 fires per
36 weeks (~1-in-5 weeks); no fire in any given week is the expected
null result, not a defect.

### W14 — Case (b): Detector fired, budgeting dropped it

D12 produced 2 angles.  Both appeared in `angles_summary_json`
(the "all detected angles" snapshot) but neither appeared in
`budgeted_summary_json`, `narrative_angles_text`, or `prompt_text`.

Root cause: the coverage-aware MINOR fill (84457a8) correctly
prioritized franchise coverage breadth.  The budget consumed
9 HEADLINE+NOTABLE slots, leaving `min(4, 12−9) = 3` MINOR slots.
Those 3 slots went to angles about franchises not yet covered by
HEADLINE/NOTABLE (Ben's Gods, Miller's Genuine Draft).  The 2 D12
angles were about franchises already covered, sorting to
`is_covered=1` and falling after the MINOR cap filled.

This is the budget working as designed: breadth over depth in
MINOR fill ensures every franchise gets at least some narrative
presence before any franchise gets a second angle from a different
dimension.

## Disposition

**No code change required.**  Both weeks show correct behavior —
genuine detector silence (W10) and correct budget prioritization
(W14).  The prompt_text capture from 643b670 resolved the
investigation on first use; the four-column diagnostic
(`angles_summary_json` → `budgeted_summary_json` →
`narrative_angles_text` → `prompt_text`) provides a deterministic
a/b/c classification for any future prose-reading observation.

## Diagnostic artifacts

- `scripts/diagnose_d12_finding1.py` — single-purpose script used
  for this investigation.  Not a permanent tool; can be removed
  after this observation is committed.
- Regenerated drafts (W10 v21, W14 v23) are in the database under
  reason "Finding 1: D12 prose investigation" with
  `REVIEW_REQUIRED` state.  These are diagnostic artifacts, not
  production drafts — clean up or leave as audit history per
  preference.
