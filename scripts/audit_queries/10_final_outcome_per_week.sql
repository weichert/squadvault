-- 10_final_outcome_per_week.sql
--
-- Question: Per (season, week), what was the final outcome? First-try clean,
--           passed-after-retry, or exhausted-retries-fell-through-to-facts?
--
-- Reads:  prompt_audit
-- Writes: nothing
--
-- Uses a window function to pick the last row for each (league, season, week)
-- by attempt, then rolls those finals up by (season, final_attempt, final_passed).
--
-- Outcome legend:
--   final_attempt=1, final_passed=1 → clean on first try
--   final_attempt=2, final_passed=1 → passed after one retry
--   final_attempt=3, final_passed=1 → passed on the last allowed retry
--   final_attempt=*, final_passed=0 → retries exhausted; lifecycle fell
--                                     through to the facts-only fallback
--
-- Reading the result:
--   * A high first-try-clean rate is the desired steady state.
--   * Any "final_passed=0" rows are weeks where the model could not satisfy
--     the verifier at all. Worth cross-referencing with Q08 to see which
--     category was failing, and then with diagnose_draft.py to decide
--     whether the failures were model-side or verifier-false-positives.

WITH ranked AS (
    SELECT
        league_id,
        season,
        week_index,
        attempt,
        verification_passed,
        ROW_NUMBER() OVER (
            PARTITION BY league_id, season, week_index
            ORDER BY attempt DESC
        ) AS rn
    FROM prompt_audit
),
finals AS (
    SELECT
        league_id,
        season,
        week_index,
        attempt             AS final_attempt,
        verification_passed AS final_passed
    FROM ranked
    WHERE rn = 1
)
SELECT
    season,
    final_attempt,
    final_passed,
    COUNT(*) AS week_count
FROM finals
GROUP BY season, final_attempt, final_passed
ORDER BY season, final_attempt, final_passed;

-- Per-week detail of any week that did not end in a pass.
WITH ranked AS (
    SELECT
        league_id,
        season,
        week_index,
        attempt,
        verification_passed,
        ROW_NUMBER() OVER (
            PARTITION BY league_id, season, week_index
            ORDER BY attempt DESC
        ) AS rn
    FROM prompt_audit
)
SELECT
    season,
    week_index,
    attempt              AS final_attempt,
    verification_passed  AS final_passed
FROM ranked
WHERE rn = 1 AND verification_passed = 0
ORDER BY season, week_index;
