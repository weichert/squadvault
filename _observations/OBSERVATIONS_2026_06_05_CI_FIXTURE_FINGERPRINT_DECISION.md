# OBSERVATIONS 2026-06-05 - CI Fixture Fingerprint Defect: Decision Recorded (A1a + A3)

Status: DECISION-READINESS phase COMPLETE. Decision made and recorded. Execution
is a SEPARATE, gated follow-on phase (NOT done in this session). No mutation of the
committed fixture occurred; tree clean at HEAD aa020dd throughout.

## Decision

Chose Option A, sub-form A1a + A3:
  - A1a: a one-time, anchor-asserting, idempotent re-stamp of recap_runs weeks 1-4
    to the action-fingerprint id-space, then re-commit the fixture. (NOT A1b: do not
    extend regenerate_fixture_db.py this phase - deferred optional follow-on.)
  - A2 (scope): weeks 1-4 only. No other real-selection weeks exist.
  - A3: add a doc note marking weeks 6 / 17 / 18 as intentional state fixtures so no
    one 'fixes' them by mistake. Ships in the execution phase (own commit if separate).
  - Option B rejected: it leaves the silent facts-only degradation in place as a trap.

## Source

Supersedes the deferred 'decision needed' note in:
  _observations/OBSERVATIONS_2026_06_05_VOICE_LIVE_DEMO_AND_FIXTURE_FINGERPRINT_DEFECT.md
Root cause (FIXTURE_SIDE id-space mismatch) is chased there; not re-walked here.

## Probe results (read-only / copy-only; committed fixture never touched)

P1 - Provenance. scripts/regenerate_fixture_db.py is a VERBATIM schema-migration
  copier: rebuilds from schema.sql and copies every row column-for-column
  (INSERT OR IGNORE), preserving whatever canonical_ids_json already holds. It
  PROPAGATES the defect; it does not create or cure it. The brief's hypothesis that
  'the durable form of A is fixing the build script' does NOT hold - there is no
  selection-deriving seeder to repair. Placeholder weeks were deliberately seeded by
  archived _patch_ci_fixture_seed_weekly_recap_approved_v2 (week 6 REVIEW_REQUIRED)
  and _v3 (weeks 17/18 APPROVED, empty-string SHA-256) - so 6/17/18 are provably
  intentional. CONSEQUENCE: A1a (one-time re-stamp) is the minimal durable fix,
  because once the fixture holds correct fingerprints, a future regenerate run copies
  them forward. A1b (self-healing regenerate) is real but a separate, deferred topic.

P2 - Dependency surface. CLEAN. No test pins any weeks-1-4 numeric selection id, nor
  any of the four weeks-1-4 selection_fingerprint prefixes (b8638e5d / d5d5815e /
  e3047450 / c9359cd4), nor the empty-string hash. The only 'test-fingerprint' hits
  are a test setting its OWN value and a prove_golden_path.sh normalization step -
  neither asserts a fixture row.

P3 - Blast radius. CLEAN; conditional satisfied.
  (a) A is non-breaking for weeks 1-4: test_golden_path_lock_v1 and
      test_integration_pipeline_v1 BUILD their own selection at runtime on fresh DBs,
      independent of the fixture's stored ids. No test's green status depends on
      weeks 1-4 resolving to zero events - every facts-only / 'Events selected: 0'
      assertion runs on constructed input (selection=None, never-played teams,
      FAAB hard-fail), not a stored fixture week.
  (b) Leave 6/17/18 untouched: test_writer_room_enrichments_v1 reads week 6 (score
      delta) and week 18 (FAAB) from the scores/FAAB tables, NOT recap_runs selection,
      and those weeks are out of A's scope anyway. test_playoff_detection_v1's week-17
      reference is a logic constant, not the recap_runs row.

P4 - Mechanics proven on a disposable copy (.local_squadvault.sqlite, gitignored,
  since removed). Re-stamping weeks 1-4 via select_weekly_recap_events_v1 +
  upsert_recap_run persisted action-fingerprint strings
  (e.g. TRANSACTION_BBID_WAIVER:70985:2024:MEMORY_EVENT_ID:351), and the loader's
  exact WHERE action_fingerprint IN (...) resolved 100%: W1=26, W2=20, W3=16, W4=21
  events. (These are pre-render EVENTS; the defect memo's 19/15/11/14 were post-filter
  BULLETS - consistent, different pipeline stages.) No API key needed. Committed
  fixture untouched; tree clean after rm of the copy.

## Execution plan (NEXT phase - gated; NOT this session)

1. Capture the CURRENT green baseline FIRST (run full pytest; record passed/skipped).
   MEASURE - do not trust any older baseline number from briefs/memory.
2. Apply the re-stamp via a downloaded, anchor-asserting, idempotent apply script
   (NOT pasted). It must: assert HEAD aa020dd + clean tree; re-stamp ONLY weeks 1-4;
   leave weeks 6/17/18 untouched; leave memory_events untouched (facts immutable);
   re-derive selection via select_weekly_recap_events_v1 + upsert_recap_run.
3. Prove the FULL suite green (pytest), then ruff, then mypy - SEPARATE paste turns,
   never &&-chained. A fixture change is exactly the case where the WHOLE suite must
   be re-proven, not a subset.
4. Commit the fixture change as its own topic (one-topic-per-commit). A fixture change
   is CODE-adjacent: run prove_ci post-commit, pre-push (NOT doc-only).
5. A3 doc note: mark weeks 6/17/18 as intentional state fixtures (own commit if a
   separate concern). Cite the archived v2/v3 seed patches as provenance.
6. Cross-link: a repaired fixture also unblocks validating the draft/auction dollar
   gap fix (memo aa020dd) end-to-end on CI data.

## Constitution note

The repair re-derives the SELECTION id-space only (the fingerprints it should have
held all along). It does NOT alter memory_events. Facts remain immutable and
append-only; narratives derived, never fact-creating. The fixture is TEST DATA, not
the facts ledger.

## State at session end

- Engine HEAD aa020dd, tree clean. This memo is the only artifact of the session.
- Decision recorded: A1a + A3. Execution gated to the next session.
- This is a doc-only commit when landed: SKIP prove_ci.
