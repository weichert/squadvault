# SESSION BRIEF - Historical weekly-windowing fix (unblocks E1.4)

**Status: SCOPED + D-W1 ADJUDICATED (Option B, week-field selection; founder 2026-06-09).
Ready to execute.**
**Type:** engine / pipeline (NOT diagnose-only). New unit - not in the Document of Record;
emerged from the E1.4 substrate-readiness finding (`685e0bc`).
**Tool/model:** Claude Code / Opus 4.8.
**Authored against HEAD:** `685e0bc`.
**Goal:** make all 32 E1.4 protocol weeks select their matchup results, so the UNCHANGED
E1.4 pre-registration (`95daa09`) can re-run and produce the fabrication baseline.

## Root-cause diagnosis (verified against the working DB)

Selection windows a week as `[lock[N-1], lock[N])` from `TRANSACTION_LOCK_ALL_PLAYERS`
events and selects `canonical_events` whose `occurred_at` falls inside. Two failure modes:

1. **2010-2016 (14 wk): zero lock events.** `TRANSACTION_LOCK_ALL_PLAYERS` count = 0 for
   these seasons (locks begin 2017). No locks -> no window -> UNSAFE / 0 events.
2. **2017-2023 (14 wk): matchup `occurred_at` is NULL.** Locks exist (windows compute),
   but `WEEKLY_MATCHUP_RESULT` events have `occurred_at = NULL`, so they match no window.
   2024-2025 work only because their matchups WERE timestamped (to lock times).

**Key enabling fact:** every matchup event (all seasons) carries `payload_json.week`
(values 1-16, complete). The week identity is explicit and reliable. There is NO
date/time signal in the matchup payload (raw MFL has franchise/regularSeason only) - so
pre-2017 weeks have ONLY the week number, no derivable timestamp.

## D-W1 - ADJUDICATED: Option B (week-field selection). Founder 2026-06-09.

**Option A - occurred_at backfill (data migration; keep timestamp-windowing).**
Backfill `occurred_at` on matchup events: 2017-2023 from `locks[week-1]`. But 2010-2016
have no locks and no dates, so this option must SYNTHESIZE week timestamps for them -
fabricating a date scheme the source never had. Smaller change to selection; brittle and
slightly fabrication-flavored for pre-2017.

**Option B - week-field selection (architectural; RECOMMENDED).**
Selection keys week membership off the explicit `payload_json.week` for week-carrying
event types, instead of reconstructing it from lock-derived timestamp windows. Uniform fix
for all 32 weeks, no synthetic dates, uses the real week identity already present. Larger
change to the selection layer; the timestamp window can remain as a fallback / for
non-week-carrying events.

**Recommendation: B.** The events already state their week; windowing by timestamp is a
proxy that breaks wherever the timestamp substrate is thin. B is the honest, uniform fix
and avoids inventing dates. A's pre-2017 half forces synthetic timestamps, which is the
exact fabrication posture the engine rejects.

## HARD constraint (either option)

**2024-2025 selections must be byte-identical after the fix** - same `selection_fingerprint`,
same `canonical_ids`, same `counts_by_type` for every currently-working week. Those are the
only weeks with shipped artifacts; the fix must not perturb them. Prove via the existing
determinism / golden-path tests plus a before/after fingerprint diff on 2024-2025.

## Acceptance criteria (binary)

1. All 32 protocol weeks (applying the protocol's quiet-week substitution rule) select
   `WEEKLY_MATCHUP_RESULT > 0`. (2010-2016 and 2017-2023 included.)
2. 2024-2025 selection fingerprints / canonical_ids unchanged (before/after diff committed
   in the memo).
3. ruff / mypy / full suite green; prove_ci clean on a clean tree (3.11 interpreter).
4. Observation memo + STATE.md update; E1.4 deferred-entry trigger flips to "ready to re-run".

## Sequencing -> E1.4

On completion, E1.4 re-runs UNCHANGED against the frozen prereg (`95daa09`): selection now
yields matchups for all 32 weeks, generation proceeds under the $15 cap, classification per
the frozen query method. The pre-registration is untouched by this fix (this unit changes
selection substrate, not the measurement).

## OUT OF SCOPE

- Running E1.4 itself (separate; this only unblocks it).
- Creative layer / verifier (untouched).
- Any change to the E1.4 pre-registration (it stays frozen).
- FAAB-era backfill beyond what matchup windowing needs (note if the fix naturally helps
  other event types, but do not expand scope to chase them).

## Known sub-questions for the implementer

- If Option A: where do 2010-2016 synthetic timestamps come from, and is that acceptable?
  (This is why B is recommended.)
- If Option B: enumerate which event types carry a reliable `payload.week` and which must
  stay timestamp-windowed; confirm the selection allowlist + ordering are preserved.
