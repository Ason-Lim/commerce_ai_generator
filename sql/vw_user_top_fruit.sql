CREATE OR REPLACE VIEW vw_user_top_fruit AS
SELECT
    session_id,
    fruit_name,
    preference_score,
    click_count,
    last_clicked_at,
    ROW_NUMBER() OVER (
        PARTITION BY session_id
        ORDER BY preference_score DESC, last_clicked_at DESC
    ) AS fruit_rank
FROM user_fruit_preference;
