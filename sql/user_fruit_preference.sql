CREATE TABLE IF NOT EXISTS user_fruit_preference (
    session_id TEXT NOT NULL,
    fruit_name TEXT NOT NULL,
    preference_score NUMERIC DEFAULT 0,
    click_count INTEGER DEFAULT 0,
    last_clicked_at TIMESTAMP DEFAULT now(),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    PRIMARY KEY (session_id, fruit_name)
);

CREATE INDEX IF NOT EXISTS idx_user_fruit_preference_session
ON user_fruit_preference(session_id);

CREATE INDEX IF NOT EXISTS idx_user_fruit_preference_score
ON user_fruit_preference(preference_score DESC);
