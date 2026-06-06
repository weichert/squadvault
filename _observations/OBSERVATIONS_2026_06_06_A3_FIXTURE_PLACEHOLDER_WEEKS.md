# OBSERVATIONS 2026-06-06 - A3: Fixture recap_runs Placeholder Weeks Are Intentional

Status: A3 note (companion to the A1a re-stamp). Doc-only.

## Purpose

The A1a re-stamp (sibling commit) repaired recap_runs weeks 1-4 in
fixtures/ci_squadvault.sqlite to the action-fingerprint id-space. This note
exists so no one later 'fixes' the remaining weeks (6 / 17 / 18) by mistake:
those three are INTENTIONAL state fixtures, not defects. They were deliberately
seeded to exercise non-DRAFTED recap_runs states and the empty-selection path.

## The three placeholder weeks (season 2024, league 70985) - DO NOT 'repair'

Week 6  - state REVIEW_REQUIRED. selection_fingerprint = 'test-fingerprint';
          canonical_ids_json empty; editorial_attunement_v1 = LOW_CONFIDENCE_RESTRAINT.
          Exercises the review-required state and a real EAL restraint directive.
          A re-stamp would destroy the only EAL-carrying fixture row.

Week 17 - state APPROVED. selection_fingerprint = SHA-256 of the empty string
          (e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855);
          canonical_ids empty. Exercises the approved + empty-selection path.

Week 18 - state APPROVED. Same empty-string-hash fingerprint and empty ids as W17.

## Provenance (evidence these are intentional, not the weeks-1-4 defect)

Seeded by archived patches, retained in-tree as the audit record:
  scripts/_archive/patches/_patch_ci_fixture_seed_weekly_recap_approved_v2.py
      -> seeds week 6 (REVIEW_REQUIRED).
  scripts/_archive/patches/_patch_ci_fixture_seed_weekly_recap_approved_v3.py
      -> seeds weeks 17/18 (APPROVED, empty-string SHA-256).

These differ from weeks 1-4, whose defect was NUMERIC row-ids in a slot the loader
matches by action_fingerprint. Weeks 6/17/18 were never meant to hold a real
selection; their empty/sentinel ids are the point of the fixture.

## Probe coverage (from the A1a decision; P2/P3)

No test pins these weeks' selection ids. test_writer_room_enrichments_v1 reads
week 6 (score delta) and week 18 (FAAB) from the scores/FAAB tables, NOT from
recap_runs selection; test_playoff_detection_v1's week-17 reference is a logic
constant. Re-stamping any of 6/17/18 would change fixture intent for zero gain.

## Rule

If a future creative-recap demo or validation needs a real selection on weeks
6/17/18, derive it on a disposable working COPY (the demo-recovery method in
OBSERVATIONS_2026_06_05_VOICE_LIVE_DEMO_AND_FIXTURE_FINGERPRINT_DEFECT.md) - do
NOT mutate the committed fixture's placeholder rows.
