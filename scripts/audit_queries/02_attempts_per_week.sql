-- 02_attempts_per_week.sql
--
-- Question: How often does a week settle on attempt 1 vs needing 2 or 3 retries?
--
-- Reads:  prompt_audit
-- Writes: nothing
--
-- For each (league_id, season, week_index) tuple, finds the maximum attempt
-- recorded (= the final attempt in the loop) and whether that final attempt
-- passed (MAX(verification_passed) is 1 iff the loop ever broke on a pass,
-- which only happens on the last attempt because of how the loop is wired).
--
-- Then rolls those weeks up by (final_attempt, ever_passed) so you can read:
--
--   final_attempt=1, ever_passed=1  → clean on first try
--   final_attempt=2, ever_passed=1  → passed after one retry
--   final_attempt=3, ever_passed=1  → passed on the last allowed retry
--   final_attempt=N, ever_passed=0  → exhausted retries; lifecycle then falls
--                                     through to the facts-only fallback
--
-- The per-week detail is in the lower SELECT for the cases worth eyeballing.

WITH per_week AS (
    SELECT
        league_id,
        season,
        week_index,
        MAX(attempt)              AS final_attempt,
        MAX(verification_passed)  AS ever_passed
    FROM prompt_audit
    GROUP BY league_id, season, week_index
)
SELECT
    final_attempt,
    ever_passed,
    COUNT(*) AS week_count
FROM per_week
GROUP BY final_attempt, ever_passed
ORDER BY final_attempt, ever_passed;

-- Detail: every week that needed more than one attempt, listed.
WITH per_week AS (
    SELECT
        league_id,
        season,
        week_index,
        MAX(attempt)              AS final_attempt,
        MAX(verification_passed)  AS ever_passed
    FROM prompt_audit
    GROUP BY league_id, season, week_index
)
SELECT
    season,
    week_index,
    final_attempt,
    ever_passed
FROM per_week
WHERE final_attempt > 1
ORDER BY season, week_index;
