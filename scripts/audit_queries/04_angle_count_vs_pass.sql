-- 04_angle_count_vs_pass.sql
--
-- Question: Correlation between angle count and verification_passed. Does the
--           model do better with more angles or fewer?
--
-- Reads:  prompt_audit
-- Writes: nothing
--
-- Two rollups:
--   1. Pass rate by budgeted-angle count (the number the model actually saw)
--   2. Pass rate by surfaced-angle count (the number before budget gate)
--
-- Interpret cautiously. Angle count is not a free variable — harder weeks
-- likely surface more angles because there is more to say, so a drop in
-- pass_pct at higher counts could mean "more angles confuse the model" OR
-- "weeks with more angles are harder weeks." Observation, not causation.

-- Rollup by budgeted (what the model saw).
SELECT
    json_array_length(budgeted_summary_json)              AS n_budgeted,
    COUNT(*)                                              AS attempts,
    SUM(verification_passed)                              AS passed,
    ROUND(100.0 * SUM(verification_passed) / COUNT(*), 1) AS pass_pct
FROM prompt_audit
GROUP BY n_budgeted
ORDER BY n_budgeted;

-- Rollup by surfaced (what the detectors produced, pre-budget).
SELECT
    json_array_length(angles_summary_json)                AS n_surfaced,
    COUNT(*)                                              AS attempts,
    SUM(verification_passed)                              AS passed,
    ROUND(100.0 * SUM(verification_passed) / COUNT(*), 1) AS pass_pct
FROM prompt_audit
GROUP BY n_surfaced
ORDER BY n_surfaced;
