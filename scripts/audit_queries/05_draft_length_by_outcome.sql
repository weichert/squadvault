-- 05_draft_length_by_outcome.sql
--
-- Question: Do passing drafts cluster at a different length than failing ones?
--
-- Reads:  prompt_audit
-- Writes: nothing
--
-- Two views:
--   1. Summary stats (min / avg / max chars) split by verification_passed
--   2. Bucketed histogram to see the shape rather than just the averages
--
-- Why this is interesting: a model that produces longer drafts when it is
-- about to fail (verbose hedging, over-padding, hallucinating supporting
-- detail) would show a clear length skew between 0-rows and 1-rows. No
-- skew suggests length is not a signal. This is an observation; do not
-- derive a length cap from it.

-- Summary stats by outcome.
SELECT
    verification_passed,
    COUNT(*)                                 AS attempts,
    MIN(length(narrative_draft))             AS min_chars,
    ROUND(AVG(length(narrative_draft)))      AS avg_chars,
    MAX(length(narrative_draft))             AS max_chars
FROM prompt_audit
GROUP BY verification_passed
ORDER BY verification_passed;

-- Bucketed histogram.
SELECT
    CASE
        WHEN length(narrative_draft) <  1000 THEN 'a: <1000'
        WHEN length(narrative_draft) <  1500 THEN 'b: 1000-1499'
        WHEN length(narrative_draft) <  2000 THEN 'c: 1500-1999'
        WHEN length(narrative_draft) <  2500 THEN 'd: 2000-2499'
        WHEN length(narrative_draft) <  3000 THEN 'e: 2500-2999'
        ELSE                                      'f: >=3000'
    END                           AS length_bucket,
    verification_passed,
    COUNT(*)                      AS attempts
FROM prompt_audit
GROUP BY length_bucket, verification_passed
ORDER BY length_bucket, verification_passed;
