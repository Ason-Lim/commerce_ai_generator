CREATE OR REPLACE VIEW vw_recommendation_mode_boost AS
SELECT
    recommendation_mode,
    impression_count,
    usage_pct,
    CASE
        WHEN usage_pct >= 40 THEN 5
        WHEN usage_pct >= 25 THEN 3
        WHEN usage_pct >= 10 THEN 1
        ELSE 0
    END AS mode_boost
FROM vw_recommendation_feedback
ORDER BY usage_pct DESC;
