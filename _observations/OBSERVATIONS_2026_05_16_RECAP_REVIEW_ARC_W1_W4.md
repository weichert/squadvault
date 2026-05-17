# OBSERVATIONS_2026_05_16_RECAP_REVIEW_ARC_W1_W4.md
## SquadVault | Phase 11 | 2025 Season Recap Review Arc — W1-W4 Findings

**Date:** 2026-05-16
**Session type:** Editorial review - first real pass against 2025 season recaps
**HEAD:** 4946733
**Reviewed weeks:** W1, W2, W3, W4

---

## Context

All 18 weeks of 2025 have APPROVED artifacts in the DB, but those approvals
were made during development, not editorial review. W7 is the only recap
that has been distributed to the league. This session is the first real
editorial pass -- applying the Recap Review Heuristic with distribution
intent -- against the current generation of the system.

Prior to this session, no JSON artifact files existed on disk. All prior
approvals were DB-only. Each week requires regeneration before the review
script can run.

---

## Week-by-week verdicts

### W1 - APPROVED FOR DISTRIBUTION (with edits)
- Passed all five Heuristic steps.
- One editorial trim: closing line "and better lineup decisions" cut as
  mildly condescending.
- Cross-window claim "$165 between draft and FAAB" for Robb's RBs:
  verified correct via data query ($115 auction + $50 FAAB = $165.00 exact).
  The claim was accurate; the verification tooling did not previously exist.
- Series record (Warmongers/Raiders 21-7, 28 meetings): commissioner judgment,
  not data-verified. Accepted as editorial call.

### W2 - WITHHELD (verifier correctly blocked all 3 attempts)
- Hard failures on all three attempts.
- Attempt 1: Two fabricated series records (Brandon/Warmongers 17-9 vs actual
  9-18; Eddie/Miller 9-3 vs actual 9-14).
- Attempt 2: One fabricated series record (Ben/Playmakers 16-12-1 vs actual
  12-17); two player-franchise misattributions (Goff to Brandon, Allen to Eddie).
- Attempt 3: Two fabricated series records; Jonathan Taylor attributed to
  Ben's Gods when he was on Playmakers.
- Verifier held correctly. No distribution path.

### W3 - APPROVED FOR DISTRIBUTION (with edits)
- Passed verifier. Two fabricated claims identified during editorial review:
  1. "just the 323rd time a starter has put up a goose egg in available
     records" -- no goose egg tracking exists anywhere in the DB. Entirely
     invented. Hard cut.
  2. "Brandon's now 0-3 and showing why he went winless last season" --
     Brandon's 2024 RESULT events returned 0W-0L (data not available to
     verify). Claim unverifiable; cut.
- Robb FAAB claim ("$40, most in the league") verified correct via query.
- Remainder of recap clean. Approved with edits noted for pre-distribution.

### W4 - APPROVED FOR DISTRIBUTION (with edits)
- Passed verifier. Entire final paragraph fabricated:
  - "Brandon dropped $51 on Brian Thomas Jr." -- no WAIVER_BID_AWARDED for
    Brian Thomas Jr. in season data.
  - "Eddie spent $32 on Ladd McConkey" -- no WAIVER_BID_AWARDED for Ladd
    McConkey in season data.
  - "Steve invested $46 in Brock Bowers" -- no WAIVER_BID_AWARDED for Brock
    Bowers in season data.
  - Associated scoring averages (7.5, 6.3, 8.5 points) -- no player scoring
    average tracking exists in DB. Fabricated.
- Final paragraph cut entirely. Recap ends at "Brandon remains winless at
  0-4, though his 98.60 was actually his best output of the season."
- Remainder of recap clean.

---

## Primary finding: Verifier coverage gap for cross-week claims

The verifier correctly blocked W2. It did not catch fabrications in W3 and W4
because its coverage is scoped to:
- Series records (H2H)
- Player-franchise attribution (current week)
- Scores and margins
- Streaks

It does not cover:
- Statistics with no DB counterpart (invented counts, "Nth time" claims)
- FAAB figures for players not in the current week's Signal Scout trace
- Scoring averages across weeks
- Any cross-week claim not explicitly surfaced by the Signal Scout

The fabrications in W3 and W4 are in precisely these uncovered categories.
The Writer's Room is given contextual data and fills gaps where data is absent
with plausible-sounding specifics. This is expected LLM behavior. The
architectural principle holds: give the model verified data and it cites
verified data; withhold and it invents.

---

## Root cause analysis

The W3 and W4 fabrications share a common structure: the Writer's Room
was given matchup context (scores, players, outcomes) but no explicit
data for the specific claim it made. It synthesized rather than derived.

- "323rd time" (W3): No goose egg tracking exists -- invented a count
- FAAB figures (W4): No W4-scoped FAAB summary per franchise -- invented
  season-to-date figures with wrong players

These are not close calls or rounding errors. They are wholesale inventions
dressed in the system's data-driven tone.

---

## Recommended actions (not in scope this session -- characterize first)

1. Verifier extension: Add coverage for cross-week numeric claims. Any
   specific figure (dollar amount, count, average) not anchored to a
   canonical Signal Scout signal should be flagged as UNANCHORED and either
   blocked or escalated for human review.

2. Writer's Room prompt constraint: Explicit instruction that no statistic
   may appear in a recap unless it was surfaced by the Signal Scout in the
   current week's selection. If it is not in the context, it cannot be in
   the recap.

3. Reusable verification queries: The ad-hoc scripts built during this
   session (FAAB spend by franchise through a given week, player bid lookup)
   should be formalized as a standing verification toolkit for editorial
   review.

---

## Emerging patterns (to watch in W5+)

- Series record fabrication is the most frequent failure mode. Appears on
  every week attempted. W2 was caught; W3 and W4 did not include series
  records in the problematic sections.
- Cross-week FAAB figures are high-risk. Current-week bids surface cleanly;
  cumulative or comparative FAAB figures are fabrication-prone.
- Invented statistics with false precision ("323rd time", "$51", "$32", "$46")
  are particularly dangerous because they read as authoritative.
- The human editorial pass is currently load-bearing. The verifier is
  necessary but not sufficient for distribution-safe recaps.

---

## Session state at memo filing

- W1: APPROVED (DB v32) -- pre-distribution edit: trim closing line
- W2: WITHHELD (no approval -- verifier blocked)
- W3: APPROVED (DB v19) -- pre-distribution edits documented above
- W4: APPROVED (DB v22) -- pre-distribution edits documented above
- W5-W18: not yet reviewed this session
