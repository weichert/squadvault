-- 11_superlative_failure_prose.sql
--
-- Question: For every SUPERLATIVE hard_failure captured in prompt_audit,
--           surface the flagged claim, the verifier's evidence, and the
--           full narrative_draft prose — so each attempt can be classified
--           MODEL_SIDE / VERIFIER_SIDE / AMBIGUOUS per the framework in
--           `OBSERVATIONS_2026_04_14_Q4_SUPERLATIVE_DIAGNOSIS.md`.
--
-- Reads:  prompt_audit
-- Writes: nothing
--
-- Shape: one row per (audit row, SUPERLATIVE hard_failure). An attempt
-- with two SUPERLATIVE failures yields two rows. Attempts with no
-- SUPERLATIVE failure do not appear. Passing attempts can in principle
-- appear if they carry a SUPERLATIVE claim under hard_failures from a
-- soft-fail path; the `passed` column makes that visible.
--
-- Columns:
--   id                prompt_audit row id — cite in classification notes
--   captured_at       ISO timestamp; compare against the 58abb2e landing
--                     time (2026-04-14 04:35:12 -0700 ≈
--                     2026-04-14T11:35:12Z) to decide whether V1/V2/V3
--                     fixes would already cover a given row
--   season, week, attempt
--   passed            verification_passed (0 or 1)
--   claim             extracted straight from verification_result_json
--   evidence          what the verifier said canonical data showed
--   narrative_draft   full model output — scan for the number in `claim`
--                     and read the surrounding sentence to classify
--
-- Classification framework (from the Q4 diagnosis doc, section
-- "Verifier-side failure patterns"):
--
--   V1  "previous season high of X" — verifier strips "previous" and
--       compares X against the post-week high. VERIFIER_SIDE. Covered
--       by 58abb2e for rows captured before 2026-04-14T11:35:12Z.
--   V2  "all-time record of N" fused with the nearest number in the
--       previous clause. VERIFIER_SIDE. Covered by 58abb2e.
--   V3  PLAYER_SCORE, not SUPERLATIVE; included in the Q4 doc for
--       cross-reference only. A player name followed by a "but" clause
--       with an unrelated number. Covered by 58abb2e. If a SUPERLATIVE
--       row turns out to be a V3-like parser fusion, note it and treat
--       it as VERIFIER_SIDE.
--
-- Anything that does not fit V1/V2 (or a V3-like fusion) and is not a
-- genuine canonical overclaim belongs in MODEL_SIDE or AMBIGUOUS.
--
-- Usage (newlines in narrative_draft render cleanly in line mode):
--
--   sqlite3 .local_squadvault.sqlite \
--       -cmd ".mode line" \
--       < scripts/audit_queries/11_superlative_failure_prose.sql \
--       > /tmp/superlative_classify.txt
--
-- Then read /tmp/superlative_classify.txt top-to-bottom and record
-- per-row classifications in a scratch markdown. If the verifier-side
-- share across the full sample matches the six-row Q4 result, Finding
-- #7 should be restated from model-behavior to verifier-calibration.

SELECT
    pa.id                                       AS id,
    pa.captured_at                              AS captured_at,
    pa.season                                   AS season,
    pa.week_index                               AS week,
    pa.attempt                                  AS attempt,
    pa.verification_passed                      AS passed,
    json_extract(je.value, '$.claim')           AS claim,
    json_extract(je.value, '$.evidence')        AS evidence,
    pa.narrative_draft                          AS narrative_draft
FROM prompt_audit AS pa,
     json_each(pa.verification_result_json, '$.hard_failures') AS je
WHERE json_extract(je.value, '$.category') = 'SUPERLATIVE'
ORDER BY pa.season, pa.week_index, pa.attempt, pa.id;
