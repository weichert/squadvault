-- 06_detector_co_occurrence.sql
--
-- Question: Which detectors show up together in the same attempt? Is RIVALRY
--           always paired with PLAYER_VS_OPPONENT, etc.?
--
-- Reads:  prompt_audit
-- Writes: nothing
--
-- Flattens the budgeted angle list to one (row_id, detector) per angle, then
-- self-joins to form unordered pairs. `a.detector < b.detector` ensures each
-- unordered pair is counted once and suppresses same-detector self-pairs.
--
-- "co_occurrences" = number of audit rows in which both detectors appeared
-- together. Since retries within a week typically carry the same angle set,
-- a pair that fires every week will show up 1-3x per week depending on
-- retry count. If you want a weeks-basis count, substitute:
--   COUNT(DISTINCT pa.season || '-' || pa.week_index)
-- and join pa on the flat CTE. Left simple here by design.

WITH flat AS (
    SELECT
        pa.id                                AS row_id,
        json_extract(je.value, '$.detector') AS detector
    FROM prompt_audit pa, json_each(pa.budgeted_summary_json) je
)
SELECT
    a.detector            AS det_a,
    b.detector            AS det_b,
    COUNT(*)              AS co_occurrences
FROM flat a
JOIN flat b
    ON a.row_id = b.row_id
    AND a.detector < b.detector
GROUP BY det_a, det_b
ORDER BY co_occurrences DESC
LIMIT 50;
