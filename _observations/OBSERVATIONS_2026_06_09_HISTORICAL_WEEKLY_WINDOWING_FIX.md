# Historical weekly-windowing fix (D-W1 Option B) - unblocks E1.4

Date: 2026-06-09
Code commit: abd5c3c
Brief: session_brief_historical_weekly_windowing_fix.md (D-W1=B, founder)
Motivated by: OBSERVATIONS_2026_06_09_E1_4_SUBSTRATE_READINESS_BLOCKER.md

## Problem

Weekly selection windows each week as [lock[N-1], lock[N]) from
TRANSACTION_LOCK_ALL_PLAYERS events and keeps canonical_events whose occurred_at
falls inside. Two historical failure modes left 28 of E1.4's 32 protocol weeks
without matchups:
- 2010-2016: zero lock events -> UNSAFE window -> 0 events.
- 2017-2023: locks exist, but WEEKLY_MATCHUP_RESULT events have NULL occurred_at,
  so they match no window.
Matchup data is present for all 16 seasons; the gap is the windowing, and every
matchup carries an explicit payload_json.week.

## Fix (Option B - week-field selection)

Added a second selection path: allowlisted week-keyed event types
(WEEK_KEYED_EVENT_TYPES = {WEEKLY_MATCHUP_RESULT}) whose occurred_at IS NULL are
selected by CAST(json_extract(payload_json,'$.week') AS INTEGER) = week_index
(join canonical_events -> memory_events). Results are unioned with the timestamp
path, deduped by canonical_id, and ordered by the same keys (occurred_at,
event_type, action_fingerprint); NULL occurred_at sorts first.

### Per-season gate (the determinism guarantee)

The week-field path runs ONLY for a week-keyed type that has ZERO timestamped
events in that season. Any season the timestamp window already handles (2024-2025,
whose matchups are timestamped) is skipped entirely, so its selections are
byte-identical. Consequence by design: a lone un-timestamped matchup inside an
otherwise-timestamped season (observed: 2024 has exactly one, payload week 18,
in the empty/WITHHELD W18) is left unreached - preserving byte-identity is the
priority; that single stray is a separate data-cleanliness item, out of scope.

## Verification

Full before/after selection diff across all 288 week-slots (16 seasons x 18 weeks),
league 70985, working DB:
- 2024-2025 (the only currently-working seasons): 0 of their week-slots changed -
  selection_fingerprint + canonical_ids byte-identical.
- 230 historical week-slots (2010-2023) gained matchups.
- All 32 E1.4 protocol weeks now select WEEKLY_MATCHUP_RESULT > 0, including the
  2010-2016 UNSAFE-window seasons (matchups supplied by the week-field path).

Tests: Tests/test_weekly_selection_weekfield_v1.py (3) - historical fallback,
deterministic ordering, stray-untimestamped-matchup-not-added. ruff zero; mypy
clean; existing selection/determinism suite green; full suite 2378 passed, 2
skipped (3.11); prove_ci clean on a clean tree.

## Effect on E1.4

E1.4's substrate blocker is resolved: selection now yields matchups for all 32
protocol weeks. The E1.4 pre-registration (95daa09) is UNCHANGED. Re-running E1.4
is now feasible (selection -> generation under the $15 cap -> classification),
pending the founder's go for the paid generation. Note: window_mode remains UNSAFE
for 2010-2016 in recap_runs (honest - no locks); generation reads canonical_ids,
which are now populated. The E1.4 execution session should confirm generation
proceeds on UNSAFE-window weeks (canonical_ids present) as part of its run.
