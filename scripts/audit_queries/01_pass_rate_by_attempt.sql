-- 01_pass_rate_by_attempt.sql
--
-- Question: Does retry actually help, or does the model converge / diverge / churn?
--
-- Reads:  prompt_audit
-- Writes: nothing
--
-- One row per attempt-position (1, 2, 3). Each row reports how many audit
-- rows captured at that attempt position passed verification vs failed.
--
-- How to read the result:
--   * attempt=1 pass_pct is the model's first-shot accuracy
--   * attempt=2 pass_pct is the post-correction accuracy (only weeks that
--     failed attempt 1 reach attempt 2, so this is conditional on prior fail)
--   * attempt=3 pass_pct is the final-shot accuracy (only weeks that failed
--     attempts 1 and 2 reach attempt 3)
--
-- A high attempt-1 pass_pct with a low attempt-2 pass_pct would suggest the
-- correction feedback is not landing — the model is failing the same way
-- twice. A rising pass_pct across attempts suggests retries are productive.

SELECT
    attempt,
    COUNT(*)                                                  AS rows_at_this_attempt,
    SUM(verification_passed)                                  AS passed,
    COUNT(*) - SUM(verification_passed)                       AS failed,
    ROUND(100.0 * SUM(verification_passed) / COUNT(*), 1)     AS pass_pct
FROM prompt_audit
GROUP BY attempt
ORDER BY attempt;
