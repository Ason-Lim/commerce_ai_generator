CREATE OR REPLACE VIEW vw_adaptive_score_impact AS
SELECT
    recommendation_mode,
    mode_boost,
    COUNT(*) AS product_count,
    AVG(final_recommendation_score) AS avg_score,
    AVG(
        final_recommendation_score
        + mode_boost
    ) AS avg_adaptive_score
FROM (
    SELECT
        r.final_recommendation_score,
        COALESCE(mb.mode_boost, 0) AS mode_boost,
        mb.recommendation_mode
    FROM vw_ai_recommendation_final r
    CROSS JOIN vw_recommendation_mode_boost mb
) x
GROUP BY
    recommendation_mode,
    mode_boost
ORDER BY
    avg_adaptive_score DESC;