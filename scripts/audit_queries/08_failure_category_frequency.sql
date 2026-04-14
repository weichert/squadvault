-- 08_failure_category_frequency.sql
--
-- Question: Which verifier categories (SCORE, SUPERLATIVE, STREAK, SERIES,
--           BANNED_PHRASE, PLAYER_SCORE) actually fail? What does the model
--           most often get wrong?
--
-- Reads:  prompt_audit
-- Writes: nothing
--
-- Flattens hard_failures and soft_failures out of verification_result_json
-- and counts by category.
--
-- Useful context when reading results:
--   * A high SCORE / PLAYER_SCORE failure rate across cleanly-validated
--     seasons is more likely a verifier false positive than a model error.
--     (The established workflow: diagnose the draft, read the prose, then
--     decide which layer is at fault. This query surfaces the pattern; it
--     does not diagnose it.)
--   * A high BANNED_PHRASE rate would suggest the model is reaching for
--     vocabulary the EAL / voice profile is trying to suppress.
--   * Concentration in one category across many weeks is the signal. A
--     spread across all six is harder to act on.

SELECT * FROM (
    SELECT
        'hard'                                       AS severity,
        json_extract(je.value, '$.category')         AS verifier_category,
        COUNT(*)                                     AS failure_count,
        COUNT(DISTINCT pa.id)                        AS attempts_with_failure,
        COUNT(DISTINCT pa.season || '-' || pa.week_index) AS weeks_with_failure
    FROM prompt_audit pa, json_each(pa.verification_result_json, '$.hard_failures') je
    GROUP BY 2
    UNION ALL
    SELECT
        'soft',
        json_extract(je.value, '$.category'),
        COUNT(*),
        COUNT(DISTINCT pa.id),
        COUNT(DISTINCT pa.season || '-' || pa.week_index)
    FROM prompt_audit pa, json_each(pa.verification_result_json, '$.soft_failures') je
    GROUP BY 2
)
ORDER BY severity, failure_count DESC;
