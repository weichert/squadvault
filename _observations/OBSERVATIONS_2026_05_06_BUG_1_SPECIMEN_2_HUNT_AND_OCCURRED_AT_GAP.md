# Bug 1 specimen #2 hunt — closure with infrastructure-gap finding

**Date:** 2026-05-06
**Thread context:** §10 Q1 Bug 1 follow-on (HEADLINE budget eviction at strength=2)
**Specimen #1:** id=142 W14 2025 Brandon Knows Ball, captured at `a5c5c1b`
**Predecessor closure:** `_observations/OBSERVATIONS_2026_05_06_T9_LOSS_POST_FIX_REVERIFY.md`
**Thread head:** `fdd06fa` (Step 1.5 predicate retirement)

## Summary

The specimen #2 hunt produced two findings:

1. **Bug 1 structural recurrence is established.** Cross-franchise
   candidate scan across 16 seasons (2010–2025) identified 19
   distinct (season, week, franchise) tuples where T9-LOSS or
   T9-WIN streak-shape arithmetic is satisfied, spanning 7
   distinct franchises beyond Brandon Knows Ball. The structural
   pattern §10 Q1 Bug 1 describes is not Brandon-specific.

2. **Literal specimen #2 regen is unreachable.** All 19 candidates
   are in pre-2024 seasons. The `WEEKLY_MATCHUP_RESULT.occurred_at`
   column is universally NULL for canonical events from 2010–2023
   (and 1 of 78 rows in 2024). The selection layer's window-filter
   `occurred_at >= window_start AND occurred_at < window_end`
   excludes NULL rows, so streak detection cannot fire in the
   recap pipeline for any pre-2024 (season, week). Specimen #2
   would require either an `occurred_at` backfill or a different
   probe vector that bypasses the selection layer.

**Recommendation: promote Bug 1 to actionable thread on the
combined weight of specimen #1's confirmed end-to-end failure
chain plus the structural-recurrence evidence from the candidate
scan.** The original diversity trigger ("≥2 franchises × ≥2
weeks") was designed in a world where specimen #2 was assumed
reachable; the discovered infrastructure gap reveals it is not,
without unrelated infrastructure work.

The `occurred_at` backfill is a separate backlog item, not a
prerequisite for Bug 1 work. Its own brief should scope the
canonical-event-ledger migration and document any side-effects
on streak/verifier paths (which are `occurred_at`-tolerant per
this finding's verification probe).

## Probe sequence

### Probe 1 — Cross-franchise candidate scan

Extended Probe E from §10 Q1 Step 1.4 to scan all 16 seasons
of corpus coverage (2010–2025), filter out fid=0010 (specimen
#1), include both T9-LOSS and T9-WIN shapes (Bug 1 is
direction-agnostic at the eviction layer).

Result: **19 candidates across 7 distinct franchises and 17
distinct (season, week) pairs.**

| Year span | T9-WIN | T9-LOSS | Total |
| :--- | :---: | :---: | :---: |
| 2010–2019 | 6 | 13 | 19 |
| 2020–2024 | 0 | 0 | 0 |
| 2025 (Brandon) | — | 8 | (specimen #1, excluded from new count) |

Distinct franchises with at least one cross-franchise candidate:
0002, 0003, 0005, 0006, 0007, 0008, 0009. Largest streak
magnitude: fid=0006 in 2019 W9 at -9 vs record 10. Multi-week
runs: fid=0006 hit T9-LOSS twice (2011 W5–W6), twice (2019 W8–W9).

### Probe 2 — recap_runs precondition for fresh regen

Selected 2019 W9 fid=0006 (Miller's Genuine Draft) as primary
candidate. Found:

- `recap_artifacts` for (2019, W9): zero rows. Clean slot.
- `prompt_audit` for (2019, W9): zero rows. Never processed.
- `WEEKLY_MATCHUP_RESULT` events for 2019 W9: 5 rows present,
  including fid=0006 vs fid=0007.

Direct invocation of `recap_artifact_regenerate.py`:

```
RecapNotFoundError: No recap_runs row found for that week.
```

Lifecycle requires `recap_runs` row before regen. Pre-2024
seasons have no `recap_runs` rows because they were never
processed through the recap pipeline.

### Probe 3 — reprocess_full_season dry-run

`scripts/reprocess_full_season.py --start-week 9 --end-week 9
--season 2019` (dry-run mode, no `--execute`):

```
week  9: DRAFT events= 18 types={'TRANSACTION_TRADE': 1,
         'TRANSACTION_WAIVER': 3, 'TRANSACTION_FREE_AGENT': 14}
```

**Zero `WEEKLY_MATCHUP_RESULT` events selected**, despite 5
existing in the canonical event ledger for that week. This is
the core finding's surfacing.

### Probe 4 — `occurred_at` population audit

```sql
SELECT season, event_type, COUNT(*) AS total,
       SUM(CASE WHEN occurred_at IS NULL THEN 1 ELSE 0 END) AS nullq
FROM canonical_events
WHERE league_id = '70985'
  AND event_type IN ('WEEKLY_MATCHUP_RESULT', 'TRANSACTION_FREE_AGENT')
GROUP BY season, event_type;
```

| Season | Event type | Total | NULL |
| :--- | :--- | ---: | ---: |
| 2010–2022 | WEEKLY_MATCHUP_RESULT | 72/year | 100% |
| 2023 | WEEKLY_MATCHUP_RESULT | 78 | 100% |
| 2024 | WEEKLY_MATCHUP_RESULT | 78 | 1 (1.3%) |
| 2025 | WEEKLY_MATCHUP_RESULT | 78 | 0 |
| 2017–2025 | TRANSACTION_FREE_AGENT | varies | 0% |
| 2010–2025 | TRANSACTION_TRADE | varies | 0% |

Step-function discontinuity at 2024. **2010–2023:
`WEEKLY_MATCHUP_RESULT.occurred_at` is universally NULL.**
2024 onwards: populated. Other event types (TRANSACTION_*)
are populated across all seasons — gap is `WEEKLY_MATCHUP_RESULT`-
specific.

The 2024 single-row anomaly (1/78 NULL) is a side-finding,
not a load-bearing observation.

### Probe 5 — Selection vs streak-detection contract divergence

`select_weekly_recap_events_v1` at line 156–158 of
`src/squadvault/core/recaps/selection/weekly_selection_v1.py`
applies strict NULL-rejection:

```python
WHERE ... occurred_at IS NOT NULL
      AND occurred_at >= ?
      AND occurred_at <  ?
```

`_load_season_matchups` at line 88 of
`src/squadvault/core/recaps/verification/recap_verifier_v1.py`
applies NULL-tolerant ordering:

```python
ORDER BY occurred_at ASC NULLS LAST
```

(no `WHERE occurred_at IS NOT NULL` clause).

Two divergent contracts on the same column. Streak detection
works on pre-2024 data when invoked directly (Probe E itself
exercised this — `_compute_streaks` produced correct streaks
for 2010–2025 despite the universal NULL). Selection layer
silently drops every `WEEKLY_MATCHUP_RESULT` for pre-2024
seasons.

## Why specimen #2 is unreachable without backfill

Three paths considered, all blocked by the gap:

1. **Direct regen via `recap_artifact_regenerate.py`** —
   blocked at `recap_runs` precondition (Probe 2).
2. **Reprocess via `reprocess_full_season.py`** — selection
   produces a recap_runs row but with zero matchup events
   (Probe 3). A regen against this would fail to detect any
   streaks, T9-LOSS or otherwise. Even with the helper +
   detector + verifier all working, the input set lacks the
   streak signal.
3. **Synthetic injection of matchup events into selection** —
   would require either patching `select_weekly_recap_events_v1`
   to accept NULL `occurred_at` or backfilling the column. Both
   are infrastructure changes outside Bug 1's scope.

The structural-recurrence evidence from Probe 1 is the
strongest available substitute. **It demonstrates the failure
mode is structural (not Brandon-specific) without requiring
empirical confirmation per (season, franchise).**

## Bug 1 promotion decision

Original §10 Q1 Step 1.4 closure memo trigger:
> "Diversity trigger (≥2 franchises × ≥2 weeks) requires one
> more cross-franchise specimen before thread promotion."

Trigger intent was "verify Bug 1 is structural, not
Brandon-specific." Trigger letter required "specimen" =
empirical regen.

Trigger intent is satisfied by:
- **Specimen #1** confirms full failure chain on one franchise.
- **Probe 1's candidate scan** confirms the streak-shape
  arithmetic recurs across 7 other franchises and 16 seasons.
- The Bug 1 mechanism (HEADLINE/NOTABLE budget evicting
  strength=2 STREAK angles) is direction-agnostic and
  franchise-agnostic at the budget layer; specimen #1 already
  exercised the mechanism in full.

Trigger letter cannot be satisfied without infrastructure work
unrelated to Bug 1 (the `occurred_at` backfill). Pursuing the
letter at the cost of an inline data-migration would couple
Bug 1's design work to an unrelated infrastructure thread,
violating one-topic-per-commit discipline at the thread level.

**Promote Bug 1 to actionable thread.**

## Bug 1 actionable scope (forward-looking, not in this memo)

A separate brief will scope the HEADLINE-budget-policy work.
Notes for the brief author:

- **Mechanism specifics**: id=142's angles block contained
  3 HEADLINE + 6 NOTABLE + 3 visible MINOR + "112 minor angles
  omitted". The strength-2 T9-LOSS angle was among the omitted.
  The eviction is a budget-cap interaction, not a
  silence-fallback or filter rule.
- **Direction-agnostic**: T9-WIN at strength=2 suffers identical
  eviction pressure. The fix should not be loss-side-only.
- **Path B rejection in §10 Q1 stands**: editorial-weight
  asymmetry (T9-LOSS at strength=3) is constitutionally wrong.
  The constitutional path is to address the budget policy, not
  re-rank by editorial preference.
- **Possible directions** (not commitments): MINOR-cap raise
  for STREAK-record-anchor angles; per-category strength floors
  ensuring at least one record-anchor angle per franchise
  surfaces if any exists; MINOR carve-out for direction-aware
  record-claim anchors. Each has tradeoffs the brief should
  enumerate.

## Side-finding: `occurred_at` backfill as separate thread

**Recommended brief title:** "WEEKLY_MATCHUP_RESULT.occurred_at
backfill for pre-2024 canonical events"

**Scope shape (high level):**

- 12+ seasons × 72-78 rows/season = ~900+ rows requiring
  `occurred_at` population.
- Source data: MFL `weeklyResults` API includes `start` field
  (game kickoff time). Memory adapter likely has the data;
  ingest may have skipped the field. Investigate before any
  re-ingestion approach.
- Streak/verifier path is `occurred_at`-tolerant — backfill
  has no risk of disrupting current correctness on those code
  paths.
- Selection layer is `occurred_at`-strict — backfill *will*
  enable historical-recap generation for pre-2024 seasons,
  which is a meaningful capability addition with its own
  governance implications (do we want to retroactively recap
  the 2010 season? probably not without explicit
  human-in-the-loop discussion).
- The 2024 single-row NULL anomaly should be investigated as
  part of the backfill scope (probably trivial, possibly an
  ingest race condition worth understanding).

**Triggering condition:** Promote when any of the following
becomes priority:
- Historical-recap generation becomes a stated league use case
- A future thread requires Bug 1 specimen-N from pre-2024 data
- Any other selection-layer windowing question requires
  pre-2024 `WEEKLY_MATCHUP_RESULT` participation

## Methodological notes

Two lessons from this hunt:

1. **Trigger phrasing should anticipate infrastructure
   reachability.** The §10 Q1 Step 1.4 closure trigger
   ("≥2 franchises × ≥2 weeks") implicitly assumed historical
   weeks were reachable for regen. They aren't. Future
   triggers in similar shapes should explicitly flag the
   reachability assumption: "specimen-N regen requires
   recap_runs row exists OR can be created without
   infrastructure changes."

2. **Probe-driven discovery beats memo-confirming.** The
   alternative path (Path C in the session: skip the hunt,
   declare Bug 1 promotable on specimen-1 alone) would have
   missed the `occurred_at` gap finding entirely. Path A's
   diagnostic discipline produced both Bug 1 closure *and*
   an independently-valuable infrastructure observation.
   The cost was modest (5 probes, ~15 minutes); the
   reusable-finding rate justifies the discipline.

## Next thread actions

- **Bug 1 actionable thread brief**: scope HEADLINE-budget-
  policy work per the notes above. Single-author at session
  start; reuse the §10 Q1 Step 1 brief structure as template.
- **`occurred_at` backfill thread**: separate brief, separate
  triggering. Not required for Bug 1 progress.
- **2024 single-row NULL anomaly**: trivial follow-up; bundle
  into the backfill brief or address as a one-line correction
  if the offending row is identifiable.
