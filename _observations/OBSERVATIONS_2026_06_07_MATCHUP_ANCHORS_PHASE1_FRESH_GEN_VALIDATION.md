# Matchup Anchors Phase 1 - Fresh-Generation Validation

Engine HEAD: c2eaa57 (per-matchup anchors + current-streak derivation + lifecycle wiring)
Date: 2026-06-07
Type: diagnostic / validation. Derived DRAFTs only; no fact writes; no approvals.
Status: PRE-REGISTRATION (recorded before any regen; results appended post-run).

## Question
Across fresh regenerations of 2025 weeks that previously fabricated streak/series/H2H facts,
do claims of the phase-1 anchored types now MATCH the anchor value or fall SILENT, rather
than FABRICATE?

## Scope boundary
In scope (counts toward verdict): current (trailing) streak, all-time H2H series record,
season-to-date record - scoped to the week's matchups, as-of-week inclusive.
Out of scope (recorded, NOT scored): FAAB dollar claims (phase 2, not anchored),
championship-count tallies, single-game/all-time superlatives. These are not in the anchor
block; W16 championship/FAAB failures are expected to persist and are not phase-1 failures.

## Target weeks and ground-truth anchor values (2025)
Name map: 0001 Stu's Crew, 0002 Paradis' Playmakers, 0003 Purple Haze, 0004 Eddie & the
Cruisers, 0005 Weichert's Warmongers, 0006 Miller's Genuine Draft, 0007 Robb's Raiders,
0008 Ben's Gods, 0009 Italian Cavallini, 0010 Brandon Knows Ball.

W16 (2 matchups):
- Paradis' Playmakers vs Italian Cavallini: H2H Paradis leads 13-12 (25). Paradis 14-2,
  7-game W streak. Cavallini 8-8, 1-game L streak.
- Weichert's Warmongers vs Purple Haze: H2H Purple Haze leads 13-12 (25). Warmongers 11-5,
  5-game W streak. Purple Haze 10-6, 1-game L streak.

W10 (5 matchups):
- Stu's Crew vs Purple Haze: H2H Stu's leads 12-8 (20). Stu's 4-6, 1-game W. Purple Haze 8-2,
  1-game L.
- Paradis' Playmakers vs Italian Cavallini: H2H tied 12-12 (24). Paradis 8-2, 1-game W.
  Cavallini 5-5, 2-game L.
- Weichert's Warmongers vs Ben's Gods: H2H Ben's leads 16-11 (27). Warmongers 6-4, 3-game W.
  Ben's 3-7, 1-game L.
- Miller's Genuine Draft vs Eddie & the Cruisers: H2H Miller's leads 14-9 (23). Miller's 7-3,
  1-game W. Eddie's 5-5, 1-game L.
- Robb's Raiders vs Brandon Knows Ball: H2H Brandon leads 19-8 (27). Robb's 4-6, 2-game W.
  Brandon 0-10, 11-game L streak.

W13 (5 matchups):
- Paradis' Playmakers vs Brandon Knows Ball: H2H Paradis leads 13-12 (25). Paradis 11-2,
  4-game W. Brandon 0-13, 14-game L streak.
- Weichert's Warmongers vs Stu's Crew: H2H Warmongers leads 17-10 (27). Warmongers 8-5,
  2-game W. Stu's 6-7, 1-game L.
- Miller's Genuine Draft vs Ben's Gods: H2H Miller's leads 16-14 (30). Miller's 9-4, 1-game W.
  Ben's 5-8, 1-game L.
- Robb's Raiders vs Purple Haze: H2H Robb's leads 18-8-1 (27). Robb's 5-8, 1-game W.
  Purple Haze 8-5, 4-game L streak.
- Italian Cavallini vs Eddie & the Cruisers: H2H Cavallini leads 18-9 (27). Cavallini 7-6,
  2-game W. Eddie's 6-7, 2-game L.

## Claim-extraction method
For each run's narrative_draft, for each in-scope type asserted about a franchise in that
week's matchups, classify against the ground-truth value above:
- MATCH: asserted value equals anchor (streak length AND direction; series record AND leader
  incl tie component; season W-L). Phrasing may differ; number and direction must equal.
- SILENT: no claim of that type for that franchise.
- FABRICATED: a claim of that type diverging from the anchor value.
- AMBIGUOUS (excluded from rate): claim explicitly framed "entering the week / before this
  game" (anchors are through-week inclusive). Recorded, not scored.
Confirm prompt_text contains the anchor block and equals this ground truth before classifying.

## Pre-registered success criterion (falsifiable)
VALIDATED if anchored claim types are MATCH or SILENT and their FABRICATED rate is materially
lower anchors-on than anchors-off (Step 3 control) and the calibration baseline.
NOT VALIDATED if anchored claims FABRICATE at roughly the anchors-off / baseline rate (the
model is not consuming the block). Either outcome is a real finding; a null is not a pass.

## Runs (appended post-regen)
TBD

## Classification (appended post-regen)
TBD

## Verdict and FAAB phase-2 implication (appended post-regen)
TBD

## Provenance
Derived DRAFT versions appended (REVIEW_REQUIRED); no APPROVED rows edited; no
canonical_events / memory_events writes. Version list TBD post-regen.


---

## RESULTS (appended 2026-06-07, post-control)

### Runs
- Anchors-ON: 9 derived DRAFTs on the live DB (W16 v24-26, W10 v28-30, W13 v26-28),
  REVIEW_REQUIRED, none approved. anchor_in_prompt=True confirmed on all (prompt_text
  anchor block equals Step-0 ground truth).
- Anchors-OFF control: lifecycle reverted to a4934d0 (working-tree only, restored after).
  Control regens written ONLY to /tmp copies, never the live DB. First control batch
  (W16 x3) completed; W10/W13 first batch credit-died to facts-only and is discarded.
  Second control batch (W10 x3, W13 x3) completed on /tmp/sv_anchors_off2.sqlite.
  anchor_in_prompt=False confirmed on all OFF rows.

### Comparative grid (cleaned in-scope: streak / H2H series / season record)
Tie-blindness false-positives (renderer 18-8-1 vs verifier 18-9) removed from both arms.
FAAB, superlative, player-score, draft-dollar excluded as out-of-scope (not anchored).
Counted by final per-run verdict.

  Week   anchors-ON   anchors-OFF
  W16        0/3          0/3       (non-discriminating; both clean)
  W10        3/3          1/3
  W13        3/3          1/3
  TOTAL      6/6          2/6       (discriminating weeks)

### Classification / mechanism
- Streak anchor INDUCES claims. Purple Haze streak: OFF arm silent in 2/3 W10 runs;
  ON arm claimed it every run and fabricated 5/6 across W10+W13 (7/8-game "winning
  streak"; "snapped" for a streak that extended). Surfacing a "cite this" streak
  converted silence into wrong speech - against "silence over speculation".
- Override unfixed. Brandon reads "10 games" in BOTH arms (season loss count 0-10),
  ignoring the anchor's 11-game value.
- Series flavor-shift, not prevention. W10 Paradis-Cavallini: OFF invented 8-2
  (season record as H2H); ON took the anchor's correct "tied 12-12" and re-applied
  the week's win to produce 13-12 (inclusive-H2H double-count).

### Verdict
NOT VALIDATED - inverted. Surfacing verified streak/series/record facts as a parallel
"cite these exactly" block increased in-scope fabrication (6/6 vs 2/6 on discriminating
weeks) by inducing claims the model then mishandled, rather than reducing it.
Caveats: n=3 per week (6 discriminating runs/arm); attempt-level counting (pre-retry)
narrows the gap toward 6/6 vs 3/6 but preserves the direction.

### FAAB phase 2 implication
Contraindicated as a parallel anchor block. The induce-then-mishandle mechanism applies
at least as strongly to FAAB dollars (more numerous, more arbitrary than streaks);
surfacing them as "cite this" facts is likely to raise FAAB fabrication. Pre-registered
"reconsider or redesign before building" branch is triggered. Do not build phase 2 as a
parallel anchor block without addressing the silence-vs-induced-speech problem.

### Carry-forward to verifier-consistency thread (not this session)
- Tie-blindness: renderer compute_head_to_head emits W-L-T (18-8-1); verifier
  verify_series_records computes W-L only (18-9). Confirmed generating false SERIES
  failures on correct output in BOTH arms. A model citing the anchor verbatim is
  penalized.
- Inclusive-H2H double-count: model treats the as-of-week-inclusive H2H anchor as
  pre-week and adds the current result (12-12 -> 13-12).

### Provenance
Live DB: 9 anchors-on derived DRAFTs (REVIEW_REQUIRED), no approvals, no
canonical_events / memory_events writes. Only live-DB write was PRAGMA
wal_checkpoint(TRUNCATE) before the /tmp copy. Control drafts confined to
/tmp/sv_anchors_off.sqlite and /tmp/sv_anchors_off2.sqlite (discarded). Lifecycle
revert was working-tree only and restored to HEAD.
