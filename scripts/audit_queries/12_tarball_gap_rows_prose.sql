-- 12_tarball_gap_rows_prose.sql
--
-- Question: Dump the five prompt_audit rows (10, 35, 42, 56, 105)
--           that were present in .local_squadvault.sqlite but missing
--           from the /tmp/sv_digit_prefix/ scan tarball captured
--           during the 2026-04-19 STREAK_SPELLED_COUNT_READOUT work.
--           The rows themselves remain intact in the DB; the recovery
--           is purely about re-producing the scan-output prose that
--           the tarball gap lost.
--
-- Reads:  prompt_audit
-- Writes: nothing
--
-- Shape: exactly 5 rows when all five ids exist. Fewer is a signal
-- worth investigating, not silently accepting — prompt_audit is
-- append-only by contract, so a missing row would indicate either a
-- schema migration truncation or direct mutation of the table, both
-- of which contradict the "audit table is observation-only" discipline
-- documented in this directory's README.
--
-- Columns:
--   id                prompt_audit row id (∈ {10, 35, 42, 56, 105})
--   captured_at       ISO timestamp of the attempt
--   season, week, attempt
--   passed            verification_passed (0 or 1)
--   narrative_draft   full model output — the payload the tarball
--                     was supposed to preserve and didn't
--
-- Source context (why these five rows specifically):
--
--   1. The 2026-04-18 session brief
--      (session_brief_streak_pattern_count_gap.txt) enumerated
--      candidate prompt_audit rows containing spelled-out game-count
--      prose: 9, 10, 24, 25, 35, 36, 47, 53, 56, 105, 112, 113, 114,
--      plus the Miller-specific cluster 40/41/42.
--
--   2. The 2026-04-19 STREAK_SPELLED_COUNT_READOUT memo classified
--      16 rows from this candidate set against the prompt_audit
--      corpus (distinct from the APPROVED-artifact corpus classified
--      in OBSERVATIONS_2026_04_20_APPROVED_STREAK_PROSE_CLASSIFICATION.md).
--
--   3. Rows 10, 35, 42, 56, 105 were in the scan script's raw output
--      but were not preserved in the tarball archived under
--      /tmp/sv_digit_prefix/. This query reproduces the lost portion
--      of the scan directly from prompt_audit, bypassing any
--      dependency on the tarball or the original scan script.
--
-- Why this lives in audit_queries/ rather than /tmp/:
-- tarball gaps have surfaced twice now in the 04-19 scan history. A
-- committed recovery path means future sessions do not depend on
-- local scan-script visibility or on the original tarball still
-- being present in /tmp/ on some particular machine.
--
-- Usage (line mode preserves the narrative_draft newlines that make
-- the prose readable):
--
--   sqlite3 .local_squadvault.sqlite \
--       -cmd ".mode line" \
--       < scripts/audit_queries/12_tarball_gap_rows_prose.sql \
--       > /tmp/tarball_gap_rows_recovered.txt
--
-- Count check:
--
--   grep -c '^         id = ' /tmp/tarball_gap_rows_recovered.txt
--   # should print 5

SELECT
    pa.id                       AS id,
    pa.captured_at              AS captured_at,
    pa.season                   AS season,
    pa.week_index               AS week,
    pa.attempt                  AS attempt,
    pa.verification_passed      AS passed,
    pa.narrative_draft          AS narrative_draft
FROM prompt_audit AS pa
WHERE pa.id IN (10, 35, 42, 56, 105)
ORDER BY pa.id;
