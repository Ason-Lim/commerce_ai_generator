CREATE TABLE IF NOT EXISTS user_product_preference (
    session_id TEXT NOT NULL,
    product_name TEXT NOT NULL,
    seller_name TEXT,
    platform_name TEXT,
    preference_score NUMERIC DEFAULT 0,
    click_count INTEGER DEFAULT 0,
    last_clicked_at TIMESTAMP DEFAULT now(),
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    PRIMARY KEY (session_id, product_name)
);

CREATE INDEX IF NOT EXISTS idx_user_product_preference_session
ON user_product_preference(session_id);

CREATE INDEX IF NOT EXISTS idx_user_product_preference_score
ON user_product_preference(preference_score DESC);