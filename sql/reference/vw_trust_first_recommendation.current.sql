-- vw_trust_first_recommendation 현재 DB 정의 덤프 (참고용, 실행용 아님)
-- 추출: 2026-11-10T01:53:40+00:00
-- 의존 객체: vw_recommendation_score

CREATE OR REPLACE VIEW vw_trust_first_recommendation AS
 SELECT product_id,
    fruit_name,
    platform_name,
    product_name,
    seller_name,
    price,
    unit_price_per_kg,
    discount_rate,
    is_high_brix,
    rating,
    review_count,
    product_url,
    price_score,
    unit_price_score,
    brix_score,
    review_score,
    rating_score,
    discount_score,
    recommendation_score,
    recommendation_label,
        CASE
            WHEN review_count IS NULL THEN 30
            WHEN review_count >= 2000 THEN 100
            WHEN review_count >= 1000 THEN 90
            WHEN review_count >= 500 THEN 80
            WHEN review_count >= 100 THEN 70
            WHEN review_count >= 30 THEN 55
            ELSE 40
        END AS trust_review_score,
        CASE
            WHEN rating IS NULL THEN 50
            WHEN rating >= 4.8 THEN 100
            WHEN rating >= 4.5 THEN 90
            WHEN rating >= 4.0 THEN 80
            WHEN rating >= 3.5 THEN 60
            ELSE 40
        END AS trust_rating_score,
        CASE
            WHEN is_high_brix = true THEN 85
            ELSE 50
        END AS trust_quality_score,
        CASE
            WHEN platform_name ~~* '%컬리%'::text THEN 80
            WHEN platform_name ~~* '%네이버%'::text THEN 70
            WHEN platform_name ~~* '%쿠팡%'::text THEN 70
            WHEN platform_name ~~* '%우체국%'::text THEN 75
            ELSE 60
        END AS trust_platform_score,
    round(
        CASE
            WHEN review_count IS NULL THEN 30
            WHEN review_count >= 2000 THEN 100
            WHEN review_count >= 1000 THEN 90
            WHEN review_count >= 500 THEN 80
            WHEN review_count >= 100 THEN 70
            WHEN review_count >= 30 THEN 55
            ELSE 40
        END::numeric * 0.35 +
        CASE
            WHEN rating IS NULL THEN 50
            WHEN rating >= 4.8 THEN 100
            WHEN rating >= 4.5 THEN 90
            WHEN rating >= 4.0 THEN 80
            WHEN rating >= 3.5 THEN 60
            ELSE 40
        END::numeric * 0.25 +
        CASE
            WHEN is_high_brix = true THEN 85
            ELSE 50
        END::numeric * 0.25 +
        CASE
            WHEN platform_name ~~* '%컬리%'::text THEN 80
            WHEN platform_name ~~* '%네이버%'::text THEN 70
            WHEN platform_name ~~* '%쿠팡%'::text THEN 70
            WHEN platform_name ~~* '%우체국%'::text THEN 75
            ELSE 60
        END::numeric * 0.15, 1) AS trust_first_score,
        CASE
            WHEN review_count >= 1000 AND is_high_brix = true THEN '리뷰 검증 고당도 추천'::text
            WHEN rating >= 4.5 AND is_high_brix = true THEN '평점 우수 고당도 추천'::text
            WHEN review_count >= 500 THEN '리뷰 검증 추천'::text
            WHEN is_high_brix = true THEN '고당도 신뢰 추천'::text
            ELSE '신뢰 기반 추천'::text
        END AS trust_recommendation_label
   FROM vw_recommendation_score;
