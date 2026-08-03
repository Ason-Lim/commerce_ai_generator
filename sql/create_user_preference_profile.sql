CREATE TABLE IF NOT EXISTS user_preference_profile (
    session_id TEXT PRIMARY KEY,

    price_affinity NUMERIC DEFAULT 0,
    quality_affinity NUMERIC DEFAULT 0,
    trust_affinity NUMERIC DEFAULT 0,
    exploration_affinity NUMERIC DEFAULT 0,

    search_count INTEGER DEFAULT 0,
    click_count INTEGER DEFAULT 0,

    last_query TEXT,
    last_priority TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_preference_profile_updated_at
ON user_preference_profile(updated_at);
