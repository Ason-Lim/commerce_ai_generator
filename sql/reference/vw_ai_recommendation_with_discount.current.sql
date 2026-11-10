-- vw_ai_recommendation_with_discount 현재 DB 정의 덤프 (참고용, 실행용 아님)
-- 추출: 2026-11-10T01:53:40+00:00
-- 의존 객체: vw_ai_adaptive_recommendation_v3, vw_product_discount_summary

CREATE OR REPLACE VIEW vw_ai_recommendation_with_discount AS
 SELECT r.fruit_name,
    r.product_name,
    r.seller_name,
    r.platform_name,
    r.price,
    r.unit_price_per_kg,
    r.discount_rate,
    r.is_high_brix,
    r.review_count,
    r.rating,
    r.recommendation_score,
    r.trust_first_score,
    r.adaptive_score,
    r.recommendation_label,
    r.trust_recommendation_label,
    r.adaptive_recommendation_label,
    r.product_url,
    r.impression_count,
    r.click_count,
    r.ctr_pct,
    r.expected_ctr_pct,
    r.rank_normalized_ctr_ratio,
    r.rank_ctr_label,
    r.ctr_boost,
    r.rank_ctr_boost,
    r.adaptive_score_v3,
    r.adaptive_label_v3,
    d.list_price,
    d.sale_price,
    d.coupon_name,
    d.coupon_amount,
    d.coupon_rate,
    d.final_price,
    d.final_discount_rate,
    d.coupon_expire_at,
    d.is_coupon_available,
    d.discount_collected_at,
    d.discount_freshness_status,
    COALESCE(d.final_price, r.price) AS effective_price,
        CASE
            WHEN d.final_price IS NOT NULL THEN true
            ELSE false
        END AS has_discount_info
   FROM vw_ai_adaptive_recommendation_v3 r
     LEFT JOIN vw_product_discount_summary d ON r.product_url = d.product_url;
