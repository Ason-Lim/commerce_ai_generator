-- =========================================
-- 추천 노출 로그
-- =========================================

CREATE TABLE IF NOT EXISTS recommendation_impression_log (
    id BIGSERIAL PRIMARY KEY,

    created_at TIMESTAMP DEFAULT NOW(),

    session_id TEXT,
    query TEXT,

    product_name TEXT,
    seller_name TEXT,

    product_url TEXT,

    rank_position INTEGER,
    score NUMERIC,
    recommendation_mode TEXT
);


-- =========================================
-- 검색 로그
-- =========================================

CREATE TABLE IF NOT EXISTS search_log (
    id BIGSERIAL PRIMARY KEY,

    created_at TIMESTAMP DEFAULT NOW(),

    session_id TEXT,
    query TEXT,
    priority TEXT,

    result_count INTEGER,

    top_product_name TEXT,
    top_product_score NUMERIC
);


-- =========================================
-- 상품 클릭 로그
-- =========================================

CREATE TABLE IF NOT EXISTS product_click_log (
    id BIGSERIAL PRIMARY KEY,

    created_at TIMESTAMP DEFAULT NOW(),

    session_id TEXT,
    query TEXT,

    product_name TEXT,
    seller_name TEXT,

    product_url TEXT,

    score NUMERIC,
    recommendation_mode TEXT
);


-- =========================================
-- 사용자 의도 로그
-- =========================================

CREATE TABLE IF NOT EXISTS user_context_log (
    id BIGSERIAL PRIMARY KEY,

    created_at TIMESTAMP DEFAULT NOW(),

    session_id TEXT,

    normalized_keyword TEXT,
    intent_type TEXT,

    gift_target TEXT,

    budget_min NUMERIC,
    budget_max NUMERIC,

    priority TEXT,

    raw_json JSONB,
    recommendation_mode TEXT
);
