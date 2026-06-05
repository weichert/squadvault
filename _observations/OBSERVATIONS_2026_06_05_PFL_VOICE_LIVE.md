# OBSERVATIONS 2026-06-05 -- PFL curated voice goes live

Closes finding #2 of `OBSERVATIONS_2026_06_05_VOICE_BRIDGE_SHIPPED.md`.

## The gap

`PFL_BUDDIES_VOICE_PROFILE` lived in `voice_profile_v1.py` as a commissioner-
approved module constant with zero non-test references. No standard path ever
wrote it into `league_voice_profiles`, so the canonical PFL league (70985) ran
on the engine's graceful default tone. The read side was already wired --
`weekly_recap_lifecycle.py:1048` loads `get_voice_profile(db, league_id) or ""`
-- so the only missing piece was a governed write.

The voice bridge (`sync_voice_from_supabase.py`) wires *founded* leagues' voices
from the frontend founding session. By design it refuses to touch 70985: its
non-clobber guard (D5a) protects rows whose `approved_by` is not
`founding-session`, and its engine-authoritative guard (D7b) treats 70985 as
ENGINE_AUTHORITATIVE. The bridge therefore *defers* to an engine-side curated
PFL voice -- which did not yet exist. This memo records its creation.

## Decision recorded (finding 2a)

Disposition of the constant: **persist as the live row** (option A), not annotate
as a reference-sample exemplar (option B). The read path is wired, the profile is
already commissioner-approved, and leaving it orphaned was precisely the gap.

## What shipped

- `scripts/set_pfl_voice.py` -- operator script. Single governed write to
  `league_voice_profiles` only; touches no facts, no `recap_artifacts`, no
  approval/audit state. The operator running it is the commissioner approving;
  the row is stamped `approved_by="commissioner"`.
  - `approved_by="commissioner"` (not `founding-session`) is load-bearing: it
    keeps the bridge's D5a / D7b guards correct so the bridge continues to refuse
    to overwrite this row.
  - Non-clobber by default: a differing existing row is refused unless `--force`.
  - Idempotent: re-running when the row already matches is a clean no-op (exit 0).
  - `--dry-run` reports the planned action and writes nothing.
- `Tests/test_set_pfl_voice.py` -- pins install, idempotency, non-clobber,
  `--force`, `--dry-run`, missing-DB, and the `approved_by` invariant.

This is the engine-side counterpart to the Supabase bridge: that wires founded
leagues, this wires the home league, which has no founding session.

## In-sandbox proof against real PFL data

Exercised against a throwaway copy of `fixtures/ci_squadvault.sqlite` -- a real
70985-keyed engine DB carrying all ten PFL franchises by name. This is the first
time the curated voice has been run end-to-end against a real PFL-keyed engine
DB; the bridge memo noted that path had never been exercised.

- Before: lifecycle would load `""` -> default tone.
- After install: lifecycle loads the 3,938-char curated profile -> voice active.
  Round-trip exact match; persisted row `(70985, commissioner, ..., 3938)`.
- Idempotent re-run: "Already current. No-op." (one row, unchanged).
- Non-clobber: a seeded differing row is refused (exit 3); `--force` replaces it.

## Operator-pending

The live effect on PFL recaps requires running the script against the production
engine DB:

    ./scripts/py scripts/set_pfl_voice.py --dry-run
    ./scripts/py scripts/set_pfl_voice.py

This checkout has no built `.local_squadvault.sqlite`; the production write is a
one-time operator step against a current production DB.

## Parked (not in scope)

The fixture stores "Miller's Genuine Draft" with a curly apostrophe while the
voice profile uses a straight one. Cosmetic data-vs-profile drift in franchise
naming, noted for a future pass; does not affect the voice write.
