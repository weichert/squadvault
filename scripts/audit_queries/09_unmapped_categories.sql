-- 09_unmapped_categories.sql
--
-- Question: Drift-detector cross-check. Are there any angle categories in
--           the wild that the CATEGORY_TO_DETECTOR map labels as UNMAPPED?
--
-- Reads:  prompt_audit
-- Writes: nothing
--
-- Expected result: empty.
--
-- The test_category_to_detector_drift_detector test is supposed to catch
-- drift at CI time by scanning source. This query catches drift in the
-- *runtime* angle feed — if a new category slips into production without
-- the map being updated, it shows up here as "UNMAPPED" even though the
-- static test would have caught it. Defense in depth; useful as a smoke
-- check after any detector changes.
--
-- If this returns rows, the finding is real: the map is out of date and
-- the drift test has a gap. That is a bug, not an observation — surface
-- it before writing any corrective code.

SELECT * FROM (
    SELECT
        'surfaced'                              AS source,
        json_extract(je.value, '$.category')    AS category,
        COUNT(*)                                AS appearances,
        COUNT(DISTINCT pa.id)                   AS attempts,
        COUNT(DISTINCT pa.season || '-' || pa.week_index) AS weeks
    FROM prompt_audit pa, json_each(pa.angles_summary_json) je
    WHERE json_extract(je.value, '$.detector') = 'UNMAPPED'
    GROUP BY 2
    UNION ALL
    SELECT
        'budgeted',
        json_extract(je.value, '$.category'),
        COUNT(*),
        COUNT(DISTINCT pa.id),
        COUNT(DISTINCT pa.season || '-' || pa.week_index)
    FROM prompt_audit pa, json_each(pa.budgeted_summary_json) je
    WHERE json_extract(je.value, '$.detector') = 'UNMAPPED'
    GROUP BY 2
)
ORDER BY source, appearances DESC;
