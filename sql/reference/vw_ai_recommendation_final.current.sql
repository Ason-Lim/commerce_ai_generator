-- vw_ai_recommendation_final 현재 DB 정의 덤프 (참고용, 실행용 아님)
-- 추출: 2026-11-10T01:53:40+00:00
-- 의존 객체: vw_ai_recommendation_with_discount, vw_price_drop_recommendation_signal, vw_product_ctr_boost

CREATE OR REPLACE VIEW vw_ai_recommendation_final AS
 WITH base AS (
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
            r.list_price,
            r.sale_price,
            r.coupon_name,
            r.coupon_amount,
            r.coupon_rate,
            r.final_price,
            r.final_discount_rate,
            r.coupon_expire_at,
            r.is_coupon_available,
            r.discount_collected_at,
            r.discount_freshness_status,
            r.effective_price,
            r.has_discount_info,
            COALESCE(c.ctr_feedback_boost, 0) AS ctr_feedback_boost,
            COALESCE(c.ctr_feedback_label, 'CTR 데이터 없음'::text) AS ctr_feedback_label,
            c.ctr_pct AS feedback_ctr_pct,
            COALESCE(p.price_drop_boost, 0) AS price_drop_boost,
            COALESCE(p.price_drop_label, '가격 변화 정보 없음'::text) AS price_drop_label,
            p.prev_price,
            p.current_price AS latest_price,
            p.price_change_pct,
            round(LEAST(100::numeric, COALESCE(r.adaptive_score_v3, r.adaptive_score, r.recommendation_score, 0::numeric) + COALESCE(p.price_drop_boost, 0)::numeric + COALESCE(c.ctr_feedback_boost, 0)::numeric), 1) AS final_recommendation_score,
                CASE
                    WHEN COALESCE(p.price_drop_boost, 0) >= 15 THEN '가격 급락 + AI 추천'::text
                    WHEN COALESCE(p.price_drop_boost, 0) >= 5 THEN '가격 하락 + AI 추천'::text
                    WHEN COALESCE(c.ctr_feedback_boost, 0) >= 7 THEN '사용자 반응 우수 추천'::text
                    ELSE COALESCE(r.adaptive_label_v3, r.recommendation_label)
                END AS final_recommendation_label
           FROM vw_ai_recommendation_with_discount r
             LEFT JOIN vw_price_drop_recommendation_signal p ON r.product_url = p.product_url
             LEFT JOIN vw_product_ctr_boost c ON r.product_url = c.product_url
        )
 SELECT fruit_name,
    product_name,
    seller_name,
    platform_name,
    price,
    unit_price_per_kg,
    discount_rate,
    is_high_brix,
    review_count,
    rating,
    recommendation_score,
    trust_first_score,
    adaptive_score,
    recommendation_label,
    trust_recommendation_label,
    adaptive_recommendation_label,
    product_url,
    impression_count,
    click_count,
    ctr_pct,
    expected_ctr_pct,
    rank_normalized_ctr_ratio,
    rank_ctr_label,
    ctr_boost,
    rank_ctr_boost,
    adaptive_score_v3,
    adaptive_label_v3,
    list_price,
    sale_price,
    coupon_name,
    coupon_amount,
    coupon_rate,
    final_price,
    final_discount_rate,
    coupon_expire_at,
    is_coupon_available,
    discount_collected_at,
    discount_freshness_status,
    effective_price,
    has_discount_info,
    ctr_feedback_boost,
    ctr_feedback_label,
    feedback_ctr_pct,
    price_drop_boost,
    price_drop_label,
    prev_price,
    latest_price,
    price_change_pct,
    final_recommendation_score,
    final_recommendation_label,
        CASE
            WHEN final_recommendation_score >= 85::numeric THEN 'CTR 반응과 가격 경쟁력이 모두 우수'::text
            WHEN price_drop_boost >= 15 THEN '최근 가격 급락으로 구매 매력 상승'::text
            WHEN price_drop_boost >= 5 THEN '최근 가격 하락으로 구매 매력 상승'::text
            WHEN ctr_feedback_boost >= 7 THEN '사용자 클릭 반응이 우수한 상품'::text
            WHEN is_coupon_available = true THEN '쿠폰 적용 가능 상품'::text
            WHEN ctr_pct >= 20::numeric THEN '사용자 반응이 높은 상품'::text
            WHEN is_high_brix = true THEN '고당도 품질 추천 상품'::text
            ELSE 'AI 종합 추천 상품'::text
        END AS recommendation_reason
   FROM base;
