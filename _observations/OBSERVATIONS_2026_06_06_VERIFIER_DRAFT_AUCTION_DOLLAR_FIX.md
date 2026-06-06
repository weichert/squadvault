# OBSERVATIONS 2026-06-06 - Verifier draft/auction dollar gap: FIX (Remedy A)

FIX session (one phase, code-adjacent). Implements the remedy decided in
OBSERVATIONS_2026_06_06_...REMEDY_DECISION.md (commit a5a2d60): one
self-contained verifier category that anchors voiced draft/auction dollar and
positional-spend claims against canonical DRAFT_PICK. Single topic, single
commit. Engine HEAD at entry: a5a2d60, clean tree.

## What shipped

One new check category in recap_verifier_v1.py:

- `verify_draft_auction_dollars(recap_text, *, db_path, league_id, season,
  reverse_name_map)` - inserted before the `# -- Orchestrator --` divider.
- Orchestrator hookup as Category 13 (`checks_run += 1` +
  `all_failures.extend(...)`) before the `hard = tuple(...)` reduction.
- Module-level regexes: dollar, draft/auction context gate, top-pick and
  cheapest role keywords, and a nominal-budget suppression pattern.
- Tests/test_recap_verifier_v1.py: `_insert_draft_pick` +
  `_insert_player_directory` helpers and `TestDraftAuctionDollarVerification`
  (8 cases), plus the import and the lockstep checks_run bump (see below).

## Tiering (S4, as decided)

- HARD when a covered (season, franchise) figure CONTRADICTS the re-derived
  ground truth (role-tagged top/cheapest != max/min) or matches NO derivation
  (generic figure not in the defensible set = fabrication).
- SOFT / flag-for-review when there is NO DRAFT_PICK coverage for the
  (season, franchise) scope - a data hole (e.g. the 2021 gap). Silence over
  speculation preserved: we surface, we do not assert wrong.

## Refinements honored (R1, R2 from a5a2d60)

- R1 VERIFIER-ONLY: no prompt-assembly or evidence-block change. The category
  re-derives ground truth itself from canonical DRAFT_PICK and consumes no
  NarrativeAngle output. The loader `load_all_auction_picks` is reused via a
  function-local lazy import - the established pattern (verify_record_claim_
  anchoring lazily imports league_history_v1 the same way), not a new
  cross-package edge.
- R2 DOLLARS IN DRAFT_PICK ONLY: TRANSACTION_AUCTION_WON is never queried for
  dollars (it carries none). Derivation reads DRAFT_PICK.bid_amount + position
  from player_directory.

## D1-D5 resolutions (as built)

- D1 reuse loader via function-local import (precedent confirmed). Verifier
  re-derives aggregates itself; does not trust angle outputs.
- D2 two shapes. Shape 1 (top-pick/cheapest): role-aware, sharp max/min
  contradiction. Shape 2 (any other draft/auction figure for a franchise):
  set-membership against {max, min} U {per-position sums}. The canonical live
  shape-2 instance voices the position generically ("into the position") with
  no parseable position token, so a sharp per-position comparison cannot fire
  on it; set-membership is the robust v1 floor. Deferred: explicit
  position-word resolution (tightens membership -> sharp) and the "half his
  draft capital" ratio clause.
- D3 exact integer match (detectors emit :.0f; comparison via round()).
- D4 no-coverage = SOFT; scope = recap season; coverage = >=1 DRAFT_PICK row
  for (season, franchise).
- D5 unresolved franchise name -> skip (continue), silence over
  misattribution.

## Nominal-budget suppression (load-bearing addition)

The "$200 budget" figure is the league's nominal auction cap, not a derived
spend; a naive sweep would HARD-fail it as fabrication. `_DRAFT_NOMINAL_
BUDGET_PATTERN` matches at the dollar's start position, so only a figure
IMMEDIATELY followed by a cap keyword ("$200 budget") is suppressed - a
derived spend that merely precedes the word ("$99 of his $200 budget") is
not. Mirrors FAAB's draft-suppression seam.

## Real PFL instance behavior (committed fixture, season 2024, league 70985)

Demonstrated read-only against fixtures/ci_squadvault.sqlite (fixture
unmodified, verified via git):

- Italian Cavallini (fid 0009), canonical max=$70 / min=$1:
  - "$70 on his top pick ... cheapest ... $1" -> PASS (anchored clean).
  - "$75 on his top pick" -> HARD (canonical max $70).
- Ben's Gods (fid 0008), canonical WR sum=$99:
  - "$99 of his $200 budget into the position" -> PASS ($200 suppressed,
    $99 is a member of the defensible set {1,16,20,58,63,99}).
  - "$130 ... on the position" -> HARD (no matching derivation; ladder cited).

These are the two robust instances the gap let through at aa020dd; they now
anchor or HARD-fail as appropriate.

## Gates

- ruff (src): clean. mypy (changed src file): clean. (mypy initially caught a
  str|None reuse of `fid` between the derivation loop and the resolver;
  fixed by renaming the derivation-loop variable to `pick_fid`.)
- Full suite: 2337 passed, 4 skipped (baseline 2329 + 8 new). Working tree
  clean except the two intended files.
- prove_ci and the reverify category-breakdown merge gate run on the
  developer machine post-commit/pre-merge (no API key needed for this fix;
  reverify needs the production audit DB). Expected reverify signal: a NEW
  category label DRAFT_AUCTION_DOLLAR appears; existing categories'
  pass/fail are not perturbed (use category-breakdown SQL on
  prompt_audit_reverify.result_json, not row-level pass->fail counts).

## Brief corrections (stale-brief findings, recorded)

- P5's "no test pins checks_run" was STALE. Five pipeline tests assert
  `result.checks_run == 15`. Adding Category 13 makes the orchestrator run 16
  passes, so those five assertions were bumped to 16 in lockstep (the
  mechanical completion of adding a real category - same topic). The
  empty-text path (`checks_run == 0`) is intentionally untouched.
- Live full-suite baseline at HEAD a5a2d60 is 2329 passed / 4 skipped (the
  brief's ~2314 / 2 figure was stale, as the brief itself warned).

## Deferred follow-ons (tracked; NOT in this commit)

- Shape-2 tightening: explicit position-word -> canonical-position resolution
  to move from set-membership to sharp per-position contradiction. Residual
  v1 risk: a drifted dollar that coincidentally collides with a different
  position's sum passes (narrow, documented).
- The "half his draft capital" / nominal-budget RATIO clause characterization.
- C: the waiver aggregate-dollar sub-check ("totaling $N"), a distinct data
  source (WAIVER_BID_AWARDED sum) and claim shape - its own commit.

## Constitutional check

Adds a category that anchors figures against canonical DRAFT_PICK facts;
loosens no existing check. SOFT no-coverage tier preserves silence over
speculation. Facts immutable/append-only; narrative derived; AI assists,
humans approve. No analytics/optimization/engagement/prediction.
