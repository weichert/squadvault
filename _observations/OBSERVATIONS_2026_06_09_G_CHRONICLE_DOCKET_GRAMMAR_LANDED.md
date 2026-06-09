# OBSERVATIONS 2026-06-09 - (g) Chronicle docket grammar landed in the engine

## Summary

The prior session closed (d) "F1 Rivalry Chronicle docket integrity" on the premise
that the engine grammar fix was *already shipped and present at HEAD `3a9cfd3`* - a
two-branch `docket_id` using `_SYNTHETIC_CHRONICLE_WEEK_FLOOR = 100` to drop the W-token
for multi-season chronicles, with regression tests in `Tests/test_sync_to_supabase.py`.

That premise did not hold. Verified this session from the repo of record (origin/main)
and from the local working tree:

- `scripts/sync_to_supabase.py` `EngineArtifact.docket_id` at `3a9cfd3` used the
  *pre-fix* grammar: `f"SV-{season}-W{week_index:02d}-CHRONICLE-V{version:02d}"`. For a
  multi-season chronicle, `week_index = end_season*100 + start_season` (e.g.
  `2025*100 + 2010 = 204510`), so this renders `W204510`.
- `_SYNTHETIC_CHRONICLE_WEEK_FLOOR` did not exist anywhere in the repo.
- `Tests/test_sync_to_supabase.py` contained only `TestEngineRecapsReady` and
  `TestSyncPreflight`; no `TestDocketIdGrammar`, no 204510 case, no oversized-token guard.
- Local disambiguation confirmed it was not merely unpushed: `HEAD = 3a9cfd3`, clean tree,
  and `git show HEAD:scripts/sync_to_supabase.py | grep FLOOR` returned nothing.

The four live rows backfilled last session in Supabase are correct and unaffected -
`/league/70985/archive/rivalries` still reads `SV-2025-CHRONICLE-V03/04/06/07` and the
2024 entry stays `SV-2024-W17-CHRONICLE-V01`. The display data was fixed. The *engine code
path that mints dockets* was not. A multi-season chronicle generated and synced from a
clean tree would have re-leaked `W204510`.

## What landed

`fix(scripts)`: in `scripts/sync_to_supabase.py`

- New module constant `_SYNTHETIC_CHRONICLE_WEEK_FLOOR = 100`. Real weeks max at ~18 and
  multi-season synthetic keys are always >= 201000, so the floor separates them cleanly.
- `EngineArtifact.docket_id` chronicle branch is now two-branch: at/above the floor the
  W-token is dropped (`SV-{season}-CHRONICLE-V{version:02d}`); below it the real-week form
  is kept (`SV-{season}-W{week:02d}-CHRONICLE-V{version:02d}`). The docstring documents both
  forms.

`fix(scripts)` (same commit): in `Tests/test_sync_to_supabase.py`

- `TestDocketIdGrammar`: 204510 -> `SV-2025-CHRONICLE-V03` (asserts no `204510` and no
  `-W`); single-season W17 -> `SV-2024-W17-CHRONICLE-V01`; floor boundary (99 keeps token,
  100 drops it); weekly recap unaffected.

This is display/derived-layer only. Facts and the immutable `week_index` synthetic key are
untouched - the same boundary the backfill respected (it corrected only the display docket,
never `week_index`). The grammar reproduces the backfill's deterministic value exactly, so
re-sync remains a no-op on the four corrected rows.

## Verification (sandbox, against a fresh clone of `3a9cfd3`)

- `docket_id` exercised directly for all five cases - all pass.
- Apply script is anchor-asserting and idempotent (second pass is a no-op).
- Patched `Tests/test_sync_to_supabase.py` is ruff-clean (`scripts/` is ruff-excluded per
  `pyproject.toml`, so the sync file is out of ruff scope; its pre-existing `I001` is not a
  gate concern and was not touched).

## Flagged, NOT actioned (architecture is frozen)

- **Version-as-discriminator smell.** Multi-season chronicles share
  `(season, week_index) = (2025, 204510)` and are distinguished only by version. Carried
  forward from last session; still not biting. A future multi-season rivalry ending in 2025
  would land as the next version in the same slot. Same root structure; nothing to act on.
- **OG/social card.** `api/og/route.tsx` renders `docket_id`. Any card scraped and cached
  upstream before last session's backfill would show the old string until re-scraped.
  Cosmetic, and only if a chronicle card was ever shared.

## Process note - stale-brief hazard (recurrence)

An item the brief marked CLOSED ("engine grammar fix already shipped") was, at the repo of
record, open. The lesson is sharper than "verify before proposing": **data correct on prod
is not the same as the code path being guarded in the repo.** (d)'s Supabase backfill was
real and verified, which made the closure feel complete; the engine composer that mints the
string was never checked against source. The cheap, decisive check was reading the property
at HEAD and executing it. Treat "fixed" claims as scoped to the layer actually verified.
