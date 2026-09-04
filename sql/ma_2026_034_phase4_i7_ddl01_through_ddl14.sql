-- MA-2026-034 PHASE 4 I7-B1
-- DDL-01 THROUGH DDL-14 CANONICAL EXTRACTION
-- STATIC ARTIFACT ONLY
-- STATEMENT COUNT: 124
-- NO DATABASE OR DDL EXECUTION AUTHORITY
-- ORDER: SEAM ORDER, THEN SOURCE LOCATION ORDER

-- BEGIN DDL-01 | app/services/market_collector_v5.py | ensure_columns
-- BEGIN STATEMENT 001
ALTER TABLE online_food_price_snapshot
ADD COLUMN IF NOT EXISTS purchase_count BIGINT
;
-- END STATEMENT 001
-- BEGIN STATEMENT 002
ALTER TABLE online_food_price_snapshot
ADD COLUMN IF NOT EXISTS market_signal_score NUMERIC
;
-- END STATEMENT 002
-- BEGIN STATEMENT 003
CREATE INDEX IF NOT EXISTS idx_online_food_market_signal_score
ON online_food_price_snapshot(market_signal_score)
;
-- END STATEMENT 003
-- BEGIN STATEMENT 004
CREATE INDEX IF NOT EXISTS idx_online_food_review_count
ON online_food_price_snapshot(review_count)
;
-- END STATEMENT 004
-- END DDL-01

-- BEGIN DDL-02 | app/services/market_collector_v51.py | ensure_columns
-- BEGIN STATEMENT 001
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS purchase_count BIGINT
;
-- END STATEMENT 001
-- BEGIN STATEMENT 002
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS market_signal_score NUMERIC
;
-- END STATEMENT 002
-- BEGIN STATEMENT 003
CREATE INDEX IF NOT EXISTS idx_online_food_market_signal_score
ON online_food_price_snapshot(market_signal_score)
;
-- END STATEMENT 003
-- BEGIN STATEMENT 004
CREATE INDEX IF NOT EXISTS idx_online_food_review_count
ON online_food_price_snapshot(review_count)
;
-- END STATEMENT 004
-- BEGIN STATEMENT 005
CREATE INDEX IF NOT EXISTS idx_online_food_rating
ON online_food_price_snapshot(rating)
;
-- END STATEMENT 005
-- END DDL-02

-- BEGIN DDL-03 | app/services/market_identity_cluster_v53.py | ensure_columns
-- BEGIN STATEMENT 001
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS market_cluster_key TEXT
;
-- END STATEMENT 001
-- BEGIN STATEMENT 002
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS market_cluster_seed TEXT
;
-- END STATEMENT 002
-- BEGIN STATEMENT 003
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS market_cluster_label TEXT
;
-- END STATEMENT 003
-- BEGIN STATEMENT 004
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS market_cluster_confidence NUMERIC
;
-- END STATEMENT 004
-- BEGIN STATEMENT 005
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS market_weight_band TEXT
;
-- END STATEMENT 005
-- BEGIN STATEMENT 006
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS market_quality_band TEXT
;
-- END STATEMENT 006
-- BEGIN STATEMENT 007
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS market_gift_band TEXT
;
-- END STATEMENT 007
-- BEGIN STATEMENT 008
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS market_attribute_band TEXT
;
-- END STATEMENT 008
-- BEGIN STATEMENT 009
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS market_variety_band TEXT
;
-- END STATEMENT 009
-- BEGIN STATEMENT 010
CREATE INDEX IF NOT EXISTS idx_online_food_market_cluster_key
ON online_food_price_snapshot(market_cluster_key)
;
-- END STATEMENT 010
-- BEGIN STATEMENT 011
CREATE INDEX IF NOT EXISTS idx_online_food_market_cluster_confidence
ON online_food_price_snapshot(market_cluster_confidence)
;
-- END STATEMENT 011
-- END DDL-03

-- BEGIN DDL-04 | app/services/market_representative_price_v54.py | ensure_columns
-- BEGIN STATEMENT 001
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS market_price_count INTEGER
;
-- END STATEMENT 001
-- BEGIN STATEMENT 002
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS market_min_price NUMERIC
;
-- END STATEMENT 002
-- BEGIN STATEMENT 003
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS market_max_price NUMERIC
;
-- END STATEMENT 003
-- BEGIN STATEMENT 004
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS market_avg_price NUMERIC
;
-- END STATEMENT 004
-- BEGIN STATEMENT 005
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS market_median_price NUMERIC
;
-- END STATEMENT 005
-- BEGIN STATEMENT 006
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS market_p25_price NUMERIC
;
-- END STATEMENT 006
-- BEGIN STATEMENT 007
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS market_p75_price NUMERIC
;
-- END STATEMENT 007
-- BEGIN STATEMENT 008
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS market_price_percentile NUMERIC
;
-- END STATEMENT 008
-- BEGIN STATEMENT 009
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS market_price_score NUMERIC
;
-- END STATEMENT 009
-- BEGIN STATEMENT 010
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS market_price_position_label TEXT
;
-- END STATEMENT 010
-- BEGIN STATEMENT 011
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS price_vs_market_avg_pct NUMERIC
;
-- END STATEMENT 011
-- BEGIN STATEMENT 012
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS price_vs_market_median_pct NUMERIC
;
-- END STATEMENT 012
-- BEGIN STATEMENT 013
CREATE INDEX IF NOT EXISTS idx_online_food_market_price_score
ON online_food_price_snapshot(market_price_score)
;
-- END STATEMENT 013
-- BEGIN STATEMENT 014
CREATE INDEX IF NOT EXISTS idx_online_food_market_price_percentile
ON online_food_price_snapshot(market_price_percentile)
;
-- END STATEMENT 014
-- END DDL-04

-- BEGIN DDL-05 | app/services/market_signal_propagation_v52.py | ensure_columns
-- BEGIN STATEMENT 001
ALTER TABLE online_food_price_snapshot
ADD COLUMN IF NOT EXISTS propagated_rating NUMERIC
;
-- END STATEMENT 001
-- BEGIN STATEMENT 002
ALTER TABLE online_food_price_snapshot
ADD COLUMN IF NOT EXISTS propagated_review_count BIGINT
;
-- END STATEMENT 002
-- BEGIN STATEMENT 003
ALTER TABLE online_food_price_snapshot
ADD COLUMN IF NOT EXISTS propagated_market_signal_score NUMERIC
;
-- END STATEMENT 003
-- BEGIN STATEMENT 004
ALTER TABLE online_food_price_snapshot
ADD COLUMN IF NOT EXISTS market_signal_source_id BIGINT
;
-- END STATEMENT 004
-- BEGIN STATEMENT 005
ALTER TABLE online_food_price_snapshot
ADD COLUMN IF NOT EXISTS market_signal_propagation_key TEXT
;
-- END STATEMENT 005
-- BEGIN STATEMENT 006
CREATE INDEX IF NOT EXISTS idx_online_food_market_signal_propagation_key
ON online_food_price_snapshot(market_signal_propagation_key)
;
-- END STATEMENT 006
-- BEGIN STATEMENT 007
CREATE INDEX IF NOT EXISTS idx_online_food_propagated_market_signal_score
ON online_food_price_snapshot(propagated_market_signal_score)
;
-- END STATEMENT 007
-- END DDL-05

-- BEGIN DDL-06 | app/services/naver_shopping_api_collector.py | ensure_collector_v2_columns
-- BEGIN STATEMENT 001
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS raw_link TEXT
;
-- END STATEMENT 001
-- BEGIN STATEMENT 002
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS redirect_url TEXT
;
-- END STATEMENT 002
-- BEGIN STATEMENT 003
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS search_url TEXT
;
-- END STATEMENT 003
-- BEGIN STATEMENT 004
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS thumbnail_url TEXT
;
-- END STATEMENT 004
-- BEGIN STATEMENT 005
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS brand TEXT
;
-- END STATEMENT 005
-- BEGIN STATEMENT 006
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS maker TEXT
;
-- END STATEMENT 006
-- BEGIN STATEMENT 007
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS category1 TEXT
;
-- END STATEMENT 007
-- BEGIN STATEMENT 008
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS category2 TEXT
;
-- END STATEMENT 008
-- BEGIN STATEMENT 009
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS category3 TEXT
;
-- END STATEMENT 009
-- BEGIN STATEMENT 010
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS category4 TEXT
;
-- END STATEMENT 010
-- BEGIN STATEMENT 011
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS mall_product_id TEXT
;
-- END STATEMENT 011
-- BEGIN STATEMENT 012
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS product_identity_key TEXT
;
-- END STATEMENT 012
-- BEGIN STATEMENT 013
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS weight_g INTEGER
;
-- END STATEMENT 013
-- BEGIN STATEMENT 014
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS price_per_100g NUMERIC
;
-- END STATEMENT 014
-- BEGIN STATEMENT 015
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS member_price INTEGER
;
-- END STATEMENT 015
-- BEGIN STATEMENT 016
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS benefit_price INTEGER
;
-- END STATEMENT 016
-- BEGIN STATEMENT 017
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS max_benefit_price INTEGER
;
-- END STATEMENT 017
-- BEGIN STATEMENT 018
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS raw_payload JSONB
;
-- END STATEMENT 018
-- END DDL-06

-- BEGIN DDL-07 | app/services/product_attribute_engine_v8.py | ensure_columns
-- BEGIN STATEMENT 001
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS product_attributes TEXT
;
-- END STATEMENT 001
-- BEGIN STATEMENT 002
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS product_attribute_signature TEXT
;
-- END STATEMENT 002
-- BEGIN STATEMENT 003
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS product_attribute_confidence NUMERIC
;
-- END STATEMENT 003
-- BEGIN STATEMENT 004
CREATE INDEX IF NOT EXISTS idx_online_food_product_attribute_signature
ON online_food_price_snapshot(product_attribute_signature)
;
-- END STATEMENT 004
-- END DDL-07

-- BEGIN DDL-08 | app/services/product_cluster_representative_v5.py | ensure_representative_columns
-- BEGIN STATEMENT 001
ALTER TABLE online_food_price_snapshot
ADD COLUMN IF NOT EXISTS cluster_representative_score NUMERIC
;
-- END STATEMENT 001
-- BEGIN STATEMENT 002
ALTER TABLE online_food_price_snapshot
ADD COLUMN IF NOT EXISTS is_cluster_representative BOOLEAN DEFAULT FALSE
;
-- END STATEMENT 002
-- BEGIN STATEMENT 003
ALTER TABLE online_food_price_snapshot
ADD COLUMN IF NOT EXISTS cluster_best_price_flag BOOLEAN DEFAULT FALSE
;
-- END STATEMENT 003
-- BEGIN STATEMENT 004
ALTER TABLE online_food_price_snapshot
ADD COLUMN IF NOT EXISTS cluster_best_quality_flag BOOLEAN DEFAULT FALSE
;
-- END STATEMENT 004
-- BEGIN STATEMENT 005
ALTER TABLE online_food_price_snapshot
ADD COLUMN IF NOT EXISTS cluster_best_review_flag BOOLEAN DEFAULT FALSE
;
-- END STATEMENT 005
-- BEGIN STATEMENT 006
CREATE INDEX IF NOT EXISTS idx_online_food_cluster_representative
ON online_food_price_snapshot(identity_cluster_key, is_cluster_representative)
;
-- END STATEMENT 006
-- END DDL-08

-- BEGIN DDL-09 | app/services/product_family_variant_v6.py | ensure_columns
-- BEGIN STATEMENT 001
ALTER TABLE online_food_price_snapshot
ADD COLUMN IF NOT EXISTS product_family_key TEXT
;
-- END STATEMENT 001
-- BEGIN STATEMENT 002
ALTER TABLE online_food_price_snapshot
ADD COLUMN IF NOT EXISTS product_family_seed TEXT
;
-- END STATEMENT 002
-- BEGIN STATEMENT 003
ALTER TABLE online_food_price_snapshot
ADD COLUMN IF NOT EXISTS product_family_confidence NUMERIC
;
-- END STATEMENT 003
-- BEGIN STATEMENT 004
ALTER TABLE online_food_price_snapshot
ADD COLUMN IF NOT EXISTS product_variant_key TEXT
;
-- END STATEMENT 004
-- BEGIN STATEMENT 005
ALTER TABLE online_food_price_snapshot
ADD COLUMN IF NOT EXISTS product_variant_seed TEXT
;
-- END STATEMENT 005
-- BEGIN STATEMENT 006
ALTER TABLE online_food_price_snapshot
ADD COLUMN IF NOT EXISTS product_variant_confidence NUMERIC
;
-- END STATEMENT 006
-- BEGIN STATEMENT 007
CREATE INDEX IF NOT EXISTS idx_online_food_product_family_key
ON online_food_price_snapshot(product_family_key)
;
-- END STATEMENT 007
-- BEGIN STATEMENT 008
CREATE INDEX IF NOT EXISTS idx_online_food_product_variant_key
ON online_food_price_snapshot(product_variant_key)
;
-- END STATEMENT 008
-- END DDL-09

-- BEGIN DDL-10 | app/services/product_identity_cluster_v4.py | ensure_cluster_columns
-- BEGIN STATEMENT 001
ALTER TABLE online_food_price_snapshot
ADD COLUMN IF NOT EXISTS identity_cluster_key TEXT
;
-- END STATEMENT 001
-- BEGIN STATEMENT 002
ALTER TABLE online_food_price_snapshot
ADD COLUMN IF NOT EXISTS identity_cluster_seed TEXT
;
-- END STATEMENT 002
-- BEGIN STATEMENT 003
ALTER TABLE online_food_price_snapshot
ADD COLUMN IF NOT EXISTS identity_cluster_confidence NUMERIC
;
-- END STATEMENT 003
-- BEGIN STATEMENT 004
CREATE INDEX IF NOT EXISTS idx_online_food_identity_cluster_key
ON online_food_price_snapshot(identity_cluster_key)
;
-- END STATEMENT 004
-- END DDL-10

-- BEGIN DDL-11 | app/services/product_quality_engine_v9.py | ensure_columns
-- BEGIN STATEMENT 001
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS ai_product_quality_score NUMERIC
;
-- END STATEMENT 001
-- BEGIN STATEMENT 002
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS ai_product_quality_label TEXT
;
-- END STATEMENT 002
-- BEGIN STATEMENT 003
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS ai_product_quality_grade TEXT
;
-- END STATEMENT 003
-- BEGIN STATEMENT 004
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS ai_product_quality_reasons TEXT
;
-- END STATEMENT 004
-- BEGIN STATEMENT 005
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS quality_component_brix NUMERIC
;
-- END STATEMENT 005
-- BEGIN STATEMENT 006
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS quality_component_attribute NUMERIC
;
-- END STATEMENT 006
-- BEGIN STATEMENT 007
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS quality_component_identity NUMERIC
;
-- END STATEMENT 007
-- BEGIN STATEMENT 008
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS quality_component_review NUMERIC
;
-- END STATEMENT 008
-- BEGIN STATEMENT 009
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS quality_component_price NUMERIC
;
-- END STATEMENT 009
-- BEGIN STATEMENT 010
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS quality_component_representative NUMERIC
;
-- END STATEMENT 010
-- BEGIN STATEMENT 011
CREATE INDEX IF NOT EXISTS idx_online_food_ai_quality_score
ON online_food_price_snapshot(ai_product_quality_score)
;
-- END STATEMENT 011
-- END DDL-11

-- BEGIN DDL-12 | app/services/product_quality_engine_v10_runner.py | ensure_columns
-- BEGIN STATEMENT 001
ALTER TABLE online_food_price_snapshot
ADD COLUMN IF NOT EXISTS product_quality_score NUMERIC
;
-- END STATEMENT 001
-- BEGIN STATEMENT 002
ALTER TABLE online_food_price_snapshot
ADD COLUMN IF NOT EXISTS market_quality_score NUMERIC
;
-- END STATEMENT 002
-- BEGIN STATEMENT 003
ALTER TABLE online_food_price_snapshot
ADD COLUMN IF NOT EXISTS recommendation_base_score NUMERIC
;
-- END STATEMENT 003
-- BEGIN STATEMENT 004
CREATE INDEX IF NOT EXISTS idx_online_food_product_quality_score
ON online_food_price_snapshot(product_quality_score)
;
-- END STATEMENT 004
-- BEGIN STATEMENT 005
CREATE INDEX IF NOT EXISTS idx_online_food_market_quality_score
ON online_food_price_snapshot(market_quality_score)
;
-- END STATEMENT 005
-- BEGIN STATEMENT 006
CREATE INDEX IF NOT EXISTS idx_online_food_recommendation_base_score
ON online_food_price_snapshot(recommendation_base_score)
;
-- END STATEMENT 006
-- END DDL-12

-- BEGIN DDL-13 | app/services/product_variety_engine_v7.py | ensure_columns
-- BEGIN STATEMENT 001
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS product_variety TEXT
;
-- END STATEMENT 001
-- BEGIN STATEMENT 002
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS product_variety_confidence NUMERIC
;
-- END STATEMENT 002
-- BEGIN STATEMENT 003
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS product_family_key_v7 TEXT
;
-- END STATEMENT 003
-- BEGIN STATEMENT 004
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS product_family_seed_v7 TEXT
;
-- END STATEMENT 004
-- BEGIN STATEMENT 005
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS product_family_confidence_v7 NUMERIC
;
-- END STATEMENT 005
-- BEGIN STATEMENT 006
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS product_variant_key_v7 TEXT
;
-- END STATEMENT 006
-- BEGIN STATEMENT 007
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS product_variant_seed_v7 TEXT
;
-- END STATEMENT 007
-- BEGIN STATEMENT 008
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS product_variant_confidence_v7 NUMERIC
;
-- END STATEMENT 008
-- BEGIN STATEMENT 009
CREATE INDEX IF NOT EXISTS idx_online_food_product_family_key_v7
ON online_food_price_snapshot(product_family_key_v7)
;
-- END STATEMENT 009
-- BEGIN STATEMENT 010
CREATE INDEX IF NOT EXISTS idx_online_food_product_variant_key_v7
ON online_food_price_snapshot(product_variant_key_v7)
;
-- END STATEMENT 010
-- BEGIN STATEMENT 011
CREATE INDEX IF NOT EXISTS idx_online_food_product_variety
ON online_food_price_snapshot(product_variety)
;
-- END STATEMENT 011
-- END DDL-13

-- BEGIN DDL-14 | app/services/recommendation_intelligence_v55.py | ensure_columns
-- BEGIN STATEMENT 001
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS recommendation_value_score NUMERIC
;
-- END STATEMENT 001
-- BEGIN STATEMENT 002
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS price_advantage_score NUMERIC
;
-- END STATEMENT 002
-- BEGIN STATEMENT 003
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS quality_advantage_score NUMERIC
;
-- END STATEMENT 003
-- BEGIN STATEMENT 004
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS market_signal_score_final NUMERIC
;
-- END STATEMENT 004
-- BEGIN STATEMENT 005
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS trust_score_final NUMERIC
;
-- END STATEMENT 005
-- BEGIN STATEMENT 006
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS scarcity_score NUMERIC
;
-- END STATEMENT 006
-- BEGIN STATEMENT 007
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS representative_bonus NUMERIC
;
-- END STATEMENT 007
-- BEGIN STATEMENT 008
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS ai_suitability_score NUMERIC
;
-- END STATEMENT 008
-- BEGIN STATEMENT 009
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS recommendation_grade TEXT
;
-- END STATEMENT 009
-- BEGIN STATEMENT 010
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS recommendation_reason_1 TEXT
;
-- END STATEMENT 010
-- BEGIN STATEMENT 011
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS recommendation_reason_2 TEXT
;
-- END STATEMENT 011
-- BEGIN STATEMENT 012
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS recommendation_reason_3 TEXT
;
-- END STATEMENT 012
-- BEGIN STATEMENT 013
ALTER TABLE online_food_price_snapshot ADD COLUMN IF NOT EXISTS recommendation_rank_score NUMERIC
;
-- END STATEMENT 013
-- BEGIN STATEMENT 014
CREATE INDEX IF NOT EXISTS idx_online_food_recommendation_value_score
ON online_food_price_snapshot(recommendation_value_score)
;
-- END STATEMENT 014
-- BEGIN STATEMENT 015
CREATE INDEX IF NOT EXISTS idx_online_food_recommendation_rank_score
ON online_food_price_snapshot(recommendation_rank_score)
;
-- END STATEMENT 015
-- END DDL-14
