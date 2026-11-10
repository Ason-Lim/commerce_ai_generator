-- vw_price_drop_recommendation_signal 현재 DB 정의 덤프 (참고용, 실행용 아님)
-- 추출: 2026-11-10T01:53:40+00:00
-- 의존 객체: vw_valid_price_change

CREATE OR REPLACE VIEW vw_price_drop_recommendation_signal AS
 SELECT product_id,
    product_name,
    seller_name,
    platform_name,
    product_url,
    prev_price,
    current_price,
    price_diff,
    price_change_pct,
        CASE
            WHEN price_change_pct <= '-30'::integer::numeric THEN 15
            WHEN price_change_pct <= '-20'::integer::numeric THEN 10
            WHEN price_change_pct <= '-10'::integer::numeric THEN 5
            ELSE 0
        END AS price_drop_boost,
        CASE
            WHEN price_change_pct <= '-30'::integer::numeric THEN '가격 급락 추천'::text
            WHEN price_change_pct <= '-20'::integer::numeric THEN '가격 하락 추천'::text
            WHEN price_change_pct <= '-10'::integer::numeric THEN '소폭 할인 추천'::text
            ELSE '가격 변화 미미'::text
        END AS price_drop_label,
    collected_at
   FROM vw_valid_price_change
  WHERE price_signal = 'PRICE_DOWN'::text;
