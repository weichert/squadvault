-- 07_angle_set_stability_across_retries.sql
--
-- Question: For weeks with multiple attempts: did the angle set change
--           between attempts, or stay constant while only the prose changed?
--
-- Reads:  prompt_audit
-- Writes: nothing
--
-- The hypothesis (from how the retry loop is wired) is that angles are
-- derived once per week and do not change across retries; only the prose
-- varies because temperature + feedback varies. If the data shows otherwise,
-- that is a real architectural finding — angles would then be re-derived on
-- each attempt, which is not what the current lifecycle intends.
--
-- Because `_serialize` uses `sort_keys=True`, byte-identical angle sets
-- produce byte-identical JSON strings, so `COUNT(DISTINCT <json>)` is a
-- clean equality check.
--
-- Expected for a multi-attempt week:
--   distinct_angle_sets    = 1   (surfaced set did not change)
--   distinct_budgeted_sets = 1   (budget gate produced the same subset)
--   distinct_drafts        = attempts   (each retry's prose is unique)
--
-- A week where distinct_angle_sets > 1 is worth investigating.

WITH per_week AS (
    SELECT
        league_id,
        season,
        week_index,
        COUNT(*)                                AS attempts,
        COUNT(DISTINCT angles_summary_json)     AS distinct_angle_sets,
        COUNT(DISTINCT budgeted_summary_json)   AS distinct_budgeted_sets,
        COUNT(DISTINCT narrative_draft)         AS distinct_drafts
    FROM prompt_audit
    GROUP BY league_id, season, week_index
    HAVING COUNT(*) > 1
)
SELECT *
FROM per_week
ORDER BY
    (distinct_angle_sets > 1) DESC,    -- anomalies first
    (distinct_budgeted_sets > 1) DESC,
    season,
    week_index;
