CREATE OR REPLACE VIEW vw_recommendation_feedback AS
SELECT
    recommendation_mode,
    COUNT(*) AS impression_count,
    ROUND(
        COUNT(*)::numeric
        /
        SUM(COUNT(*)) OVER ()
        * 100,
        2
    ) AS usage_pct
FROM impression_log
GROUP BY recommendation_mode;