# OBSERVATIONS 2026-06-05 — Voice Bridge shipped (closes the 2026-06-04 gap)

**Status:** Shipped to `main` at commit `7ee2c2d`. prove_ci green (full gate
suite; 2313 passed / 3 skipped; golden-path determinism stable across CWD and
rerun; worktree clean at entry and exit). Closes the gap recorded in
`_observations/OBSERVATIONS_2026_06_04_VOICE_BRIDGE_GAP.md`.

## What shipped

`scripts/sync_voice_from_supabase.py` — the Supabase -> engine direction for
founding voice, the reverse of `scripts/sync_to_supabase.py`. It reads a
league's commissioner-approved founding Voice Profile from Supabase and writes
it into the engine `league_voice_profiles` table via the existing
`set_voice_profile`, so a voice chosen in the frontend founding session reaches
recap generation (consumed by `creative_layer_v1` through `get_voice_profile`).

Design decisions, as built:

- **D1a — payload.** The frontend `voice_profiles.prose` is authored (by
  `buildVoiceProfilePrompt`) as instruction-grade voice directive, i.e. the
  same artifact-kind as the engine `profile_text`. It is bridged verbatim.
  No per-key translation layer. The register `profile_key` rides in
  `approved_by` (`founding-session:<KEY>`) for provenance; no schema change.
- **D2a — mechanism.** A new operator-run engine script mirroring the forward
  sync (supabase client via `_env_bootstrap`, read-only on Supabase, one
  `sync_log` row, per-row failure isolation). No always-on coupling; the recap
  path is unchanged and still reads `league_voice_profiles` offline.
- **D3a — cadence.** Operator-run, same cadence as recaps-up.
- **D4a — authority gate.** Bridges only when `leagues.first_approval_completed`
  is true (the commissioner approved the founding outputs). `voice_profile_id`
  is set at generate time, before approval, so the gate is the approval flag,
  not mere existence of the row.
- **D5a — non-clobber.** Refuses to overwrite an engine row whose `approved_by`
  does not start `founding-session` (i.e. hand-curated) unless `--force`.
- **D6a — skip / MIXED.** A null `voice_profile_id` is a clean no-op; the
  engine's graceful default tone holds. A MIXED register chosen through the full
  founding flow has prose and bridges normally; only a true skip is the no-op.
- **D7b — engine-authoritative skip-list.** `ENGINE_AUTHORITATIVE = {"70985"}`.
  Such leagues are refused **before any I/O** (no Supabase, no DB) unless
  `--force`. Added after the dry-run revealed the demo-seed hazard (below).
- **D8a — non-creating read.** `read_engine_voice_row` treats a missing DB file
  as "no row" rather than materializing an empty SQLite file; writes still
  create as needed.

CLI: `--league-id` (required, no all-leagues default), `--db`, `--dry-run`,
`--force`. Run via `./scripts/py scripts/sync_voice_from_supabase.py
--league-id <canonical> --dry-run`.

## Validation status — important caveat

The bridge is **validated but never yet exercised against a real engine DB.**

- The **Supabase read** path is live-confirmed against staging
  (`qcaxemuydxlzpzgnnnoa`): a `--dry-run` for 70985 (pre-D7b) returned two 200s
  and a correct decision.
- The **engine write** path is proven only against a sandbox temp DB (the real
  `set_voice_profile` upsert, idempotent, one row, stable text/approved_by) and
  the pure decision core (`decide_bridge_action`, `is_engine_authoritative`,
  all branches).
- It has **not** run against a populated production DB, because the
  `~/projects/squadvault` checkout has no built `.local_squadvault.sqlite`
  (see findings). First real-world run requires: (1) an engine environment with
  the production DB present, and (2) a genuinely frontend-founded league past
  first approval. For 70985 the bridge correctly refuses. So it is correct and
  inert until that first real founding — the intended "build only when
  deliberately designed" shape.

## Session diagnostic findings

1. **This checkout has no built engine DB.** `.local_squadvault.sqlite` did not
   exist; the first dry-run's `read_engine_voice_row` connected and so created a
   0-byte file (pre-D8a behavior). That empty file was removed. The populated
   production DB lives elsewhere / must be rebuilt via ingest. Not a bug — a
   clean clone that never ran its pipeline.
2. **PFL has no `league_voice_profiles` row anywhere observed.** The curated
   `PFL_BUDDIES_VOICE_PROFILE` is a module constant with **zero references** in
   `src/` — a dangling reference artifact, not the live source. It was only ever
   inserted by the separate Phase 10 chat-export step, not by standard ingest.
   Implication: on any freshly built real DB, 70985 starts with no voice row and
   recaps run on default tone until that step is re-run.
3. **PFL is falsely bridge-eligible via the demo seed.** The frontend seed
   (`supabase/seed/001_pfl_buddies_demo.sql`) gives 70985 a `voice_profile_id`
   (`...010`), `first_approval_completed = true`, and thin placeholder prose.
   Without D7b the bridge would establish PFL's engine voice from that demo
   prose on a fresh real DB. D7b now refuses it structurally. (No silent clobber
   was ever possible regardless: `set_voice_profile` has no error-swallowing, so
   the missing table would have raised, not written.)

## Parked items (none blocking)

1. **Frontend seed hygiene.** PFL's demo row carries
   `first_approval_completed = true`, which is what makes it falsely
   bridge-eligible. Now guarded engine-side via D7b, but a tidy fix
   (seed `false`, or drop the demo `voice_profile_id`) is frontend-repo work.
2. **Two stale docs.** (a) The dangling `PFL_BUDDIES_VOICE_PROFILE` constant in
   `src/squadvault/core/tone/voice_profile_v1.py` — decide whether to wire it as
   the canonical PFL row (via `set_voice_profile`) or annotate it as a reference
   sample. (b) Frontend `src/lib/founding/actions.ts` (~line 217) skip-path
   comment still repeats the disproved "MIXED at the engine" claim; the engine
   does not consult `voice_profile_id`, so a skipped null is inert engine-side.
3. **Test coverage.** The decision core is pure and trivially testable, but no
   test was added: the forward sync (`sync_to_supabase.py`) carries no test and
   no repo test imports `supabase`, so adding one would invent a new convention.
   Decide deliberately rather than by default.

## Environment note

The engine `.env.local` now needs `SUPABASE_URL` and
`SUPABASE_SERVICE_ROLE_KEY` (added this session; pointed at the same staging
project as the frontend). Both the voice bridge and the forward sync read them
via `_env_bootstrap`. `.env.local` is gitignored (`.env.*`), so it is never
committed.

## Pointers

- Code: `scripts/sync_voice_from_supabase.py` (commit `7ee2c2d`)
- Predecessor gap note: `_observations/OBSERVATIONS_2026_06_04_VOICE_BRIDGE_GAP.md`
- Engine consumer: `src/squadvault/core/tone/voice_profile_v1.py`
  (`get_voice_profile` / `set_voice_profile`), `src/squadvault/ai/creative_layer_v1.py`
- Frontend producer: `src/app/api/founding/[sessionId]/generate/route.ts`,
  `src/lib/founding/generators.ts` (`buildVoiceProfilePrompt`)
