-- 03_detector_frequency.sql
--
-- Question: Which detector categories appear most/least often, and how does
--           the budget gate filter them?
--
-- Reads:  prompt_audit
-- Writes: nothing
--
-- Two passes:
--   * 'surfaced'  — every detector category that fired into all_angles
--   * 'budgeted'  — only those that survived the budget gate into the prompt
--
-- Comparing the two gives a sense of the budget gate's cut profile: which
-- detectors routinely surface but get dropped before the model sees them.
--
-- "weeks_present" counts distinct (season, week) tuples — this is what you
-- want for "how often does this detector fire across the dataset," because
-- counting raw rows would inflate by the number of retries on each week.
-- "attempt_appearances" is the raw row count for reference.

SELECT * FROM (
    SELECT
        'surfaced'                                            AS source,
        json_extract(je.value, '$.detector')                  AS detector,
        json_extract(je.value, '$.category')                  AS category,
        COUNT(DISTINCT pa.season || '-' || pa.week_index)     AS weeks_present,
        COUNT(*)                                              AS attempt_appearances
    FROM prompt_audit pa, json_each(pa.angles_summary_json) je
    GROUP BY 2, 3
    UNION ALL
    SELECT
        'budgeted',
        json_extract(je.value, '$.detector'),
        json_extract(je.value, '$.category'),
        COUNT(DISTINCT pa.season || '-' || pa.week_index),
        COUNT(*)
    FROM prompt_audit pa, json_each(pa.budgeted_summary_json) je
    GROUP BY 2, 3
)
ORDER BY source, weeks_present DESC, attempt_appearances DESC;
