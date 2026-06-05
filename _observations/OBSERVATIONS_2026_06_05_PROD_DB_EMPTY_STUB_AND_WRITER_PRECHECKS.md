# OBSERVATIONS 2026-06-05 -- production engine DB is an empty stub; voice-live blocked; writer prechecks shipped

Summary: the curated PFL voice now has a governed write path and all three engine
voice/recap writers fail honestly on an unbuilt DB, but the original goal --
PFL recaps actually rendering in the curated voice -- remains blocked, because
the production engine DB has no data to recap. This memo records the discovery
and the hardening so the next session starts from here.

## Discovery: production .local_squadvault.sqlite is a hollow stub

While attempting the one-time PFL voice write, set_pfl_voice crashed at the
underlying set_voice_profile with "no such table: league_voice_profiles". A
read-only diagnostic against ~/projects/squadvault/.local_squadvault.sqlite
showed the file exists but carries no engine data:

    has league_voice_profiles : False
    has _schema_migrations    : False
    canonical_events          : MISSING
    franchise_directory       : MISSING
    recap_artifacts           : MISSING
    memory_events             : MISSING

This is not a DB that is merely behind on migrations; it is essentially empty.
apply_migrations would create the tables, but there would still be nothing to
recap. The real precondition is a built, populated engine DB for league 70985.

Build path: scripts/run_weekly_ingest.sh -> run_ingest_then_canonicalize.py
ingests ONE season at a time (it is the Tuesday scheduler wrapper), needs
MFL_SERVER / MFL_USERNAME / MFL_PASSWORD in .env.local, and talks to MFL over
the network. A real PFL DB means multi-season ingest plus canonicalization
across the 8-league history chain under 70985 -- its own session, local-only,
not reproducible in the sandbox.

## Voice mechanism is ready (only the populated DB is missing)

- set_pfl_voice.py (a261dc2) installs the curated PFL_BUDDIES_VOICE_PROFILE as
  the live league_voice_profiles row for 70985, approved_by="commissioner".
- The recap read path is already wired: weekly_recap_lifecycle.py loads
  get_voice_profile(db, league_id) or "" (line ~1048). A row flips PFL from the
  graceful default tone to the curated voice with no further code change.
- Proven end-to-end against a throwaway copy of fixtures/ci_squadvault.sqlite
  (real 70985 data): before = default tone, after = 3938-char curated voice.

So once a populated production DB exists, voice-live is a single governed write.

## Writer prechecks shipped this session (the "fail honestly" arc)

The empty stub exposed a shared defect class: a swallowed sqlite OperationalError
let a MISSING table read as "no row", so --dry-run lied ("would INSTALL"/"would
write") and a live run crashed mid-write (the bridge would even leave an orphan
empty DB file). Fixed in all three engine writers with non-creating
table-existence prechecks, clear actionable messages, distinct exit codes, and
hermetic tests:

- set_pfl_voice.py            -- bee8524 (precheck: league_voice_profiles; exit 5)
- sync_voice_from_supabase.py -- 4cd5966 (precheck: league_voice_profiles; EXIT_NOT_BUILT=6; bridge's first test)
- sync_to_supabase.py         -- 6cb8e9b (precheck: recap_artifacts; returns 1; script's first test)

The forward sync (6cb8e9b) had no integrity defect -- it already failed closed
(read-only engine open, no orphan, no false dry-run); that change was a
message-clarity consistency fix only.

Convention set along the way: operator-script preconditions get small hermetic
tests; full Supabase-flow coverage stays deferred until a mocking approach is
chosen. sync_to_supabase imports supabase at top level (undeclared dependency),
so its test uses pytest.importorskip("supabase"): runs where the dep is present,
skips cleanly where it is not, so it cannot break prove_ci.

The fix lives in the operator scripts, never in get_voice_profile /
read_engine_voice_row: their swallow is intentional graceful degradation so
recap generation falls back to default tone rather than crashing.

## Next session

Voice-live is blocked only on a populated 70985 engine DB. Two ways forward:

- (B) Build the real engine DB: multi-season MFL ingest + canonicalization,
  local-only, needs MFL creds in .env.local. Its own session.
- (C) Fixture-copy demo: cp fixtures/ci_squadvault.sqlite .local_squadvault.sqlite
  (real 70985 data, 2024 subset), then set_pfl_voice + a recap run with
  ANTHROPIC_API_KEY set, to see the curated voice end-to-end. Reversible; a demo
  DB, not the historical build.

Cross-refs: OBSERVATIONS_2026_06_05_VOICE_BRIDGE_SHIPPED.md (finding #2),
OBSERVATIONS_2026_06_05_PFL_VOICE_LIVE.md (mechanism + the parked
"Miller's Genuine Draft" curly-apostrophe data/profile cosmetic drift).
