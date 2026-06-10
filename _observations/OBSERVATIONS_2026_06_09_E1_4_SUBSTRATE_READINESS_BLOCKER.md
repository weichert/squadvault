# E1.4 Substrate-Readiness Blocker - execution halted PRE-RUN

Date: 2026-06-09
Engine HEAD: 95daa09 (E1.4 pre-registration protocol commit)
Session: E1.4 execution (Claude Code / Opus, diagnose-only).
Relates to: OBSERVATIONS_2026_06_09_E1_4_FRESH_GEN_FABRICATION_BASELINE_PREREG.md
Disposition: E1.4 NOT executed; NO generations run; ZERO API spend. This memo is the
session's finding. Per charter section 6 the pre-registration memo is not edited; this is
the dated finding that records why the run did not proceed.

## Summary

The pre-registered 32-week fabrication baseline is NOT executable against the current
pipeline + working DB. The blocker is a weekly-windowing/selection gap, not a data gap or
a generation problem. Only 4 of the 32 protocol weeks (all 2024-2025) are selectable with
matchup results. Fixing it requires changing the windowing/selection layer, which is
forbidden in this diagnose-only session. Halted before any paid generation, as agreed.

## What was verified GREEN before the blocker

- Freeze: HEAD 95daa09 (code identical to b4bb6ce); model claude-sonnet-4-20250514 and
  max_tokens=1500 in creative_layer_v1.py - exact match to the protocol / D-B.
- ANTHROPIC_API_KEY present; instrument scripts/recap_artifact_regenerate.py present.
- canonical_events present for all 16 seasons 2010-2025 (38,983 rows), INCLUDING
  WEEKLY_MATCHUP_RESULT for every season (72/season 2010-2020; 78/season 2021-2025).

## The blocker

generate_weekly_recap_draft requires a recap_runs row (raises RecapNotFoundError
otherwise). Only the 4 sentinel weeks (2024 W2/W13, 2025 W10/W13) had one; the other 28
required the selection step. A free, deterministic selection sweep
(select_weekly_recap_events_v1, no API) across all 32 protocol weeks found:

  Seasons 2010-2016 (14 wk): window mode UNSAFE -> 0 events selected. No safe weekly
                             boundary computes for these seasons.
  Seasons 2017-2023 (14 wk): window mode LOCK_TO_LOCK (safe), transactions selected, but
                             0 WEEKLY_MATCHUP_RESULT captured - matchup events fall
                             OUTSIDE the computed window.
  Seasons 2024-2025 ( 4 wk): window aligns -> 5 matchups each. Usable.

  Result: OK=4, QUIET(no matchup)=14, UNSAFE/EMPTY=14.

## Root cause: windowing, not ingest

WEEKLY_MATCHUP_RESULT events EXIST for all 16 seasons (verified by direct
canonical_events count). The live weekly-windowing layer (weekly_windows_v1.py) only
produces windows that capture those matchup events for the operationally-processed
2024-2025 seasons. For 2017-2023 the LOCK_TO_LOCK window selects transactions but misses
the matchup-result timestamps; for 2010-2016 no safe window computes at all. The data is
present; the selection windowing does not reach it for historical weeks.

## Why the run did not proceed

- Diagnose-only boundary: making historical weeks selectable means changing the
  windowing/selection logic - a pipeline change the protocol forbids in this session.
- Generating only the 4 usable weeks (all 2024-2025) would defeat the protocol's entire
  design: the pre/post-2021 substrate split and 2-weeks-per-digital-season historical
  depth. A 4-week 2024-2025-only run is not the pre-registered baseline; it would be a
  meaningless partial, not a smaller-but-valid one.

## Recommendation

1. PREFERRED: a separate engineering unit to make historical weekly-windowing capture
   matchup results (the data is all present; this is a windowing fix, real pipeline work,
   NOT diagnose-only). Then re-run the UNCHANGED E1.4 protocol - keeps the pre-registration
   and cert-6 evidence clean.
2. ALTERNATIVELY: a Fable protocol-revision if historical windowing will not be fixed
   pre-season (rescope the week-set, or defer the historical-depth ambition). Changing the
   week-set changes the pre-registration, so it is a chat/Fable call, not an Opus one.

E1.4 remains OPEN/blocked (not discharged). cert-6 evidence is deferred until the baseline
can actually be measured; that this measurement could not run on historical substrate is
itself an honest finding for the closure record.

## Session hygiene

The sweep upserted 28 ELIGIBLE recap_runs rows to the LOCAL working DB (never committed,
per the protocol's local-only discipline); they were deleted at session end (recap_runs
restored to its pre-sweep state: 36 rows, seasons 2024-2025 only). No facts written, no
approvals, no distribution, no pipeline/verifier/prompt changes. The committed artifact of
this session is this memo plus the STATE.md update.
