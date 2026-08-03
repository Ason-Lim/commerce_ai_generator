CREATE TABLE IF NOT EXISTS impression_log (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),

    session_id TEXT,
    query TEXT,

    product_id TEXT,
    product_name TEXT,
    product_url TEXT,

    rank INTEGER,
    recommendation_mode TEXT,
    selected_priority TEXT,
    selected_section TEXT,

    platform TEXT,
    mall_name TEXT,
    price NUMERIC
);

CREATE INDEX IF NOT EXISTS idx_impression_log_mode
ON impression_log(recommendation_mode);

CREATE INDEX IF NOT EXISTS idx_impression_log_created_at
ON impression_log(created_at);

CREATE INDEX IF NOT EXISTS idx_impression_log_product_name
ON impression_log(product_name);
