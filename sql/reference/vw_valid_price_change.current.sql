-- vw_valid_price_change 현재 DB 정의 덤프 (참고용, 실행용 아님)
-- 추출: 2026-11-10T01:53:40+00:00
-- 의존 객체: vw_clean_price_change

CREATE OR REPLACE VIEW vw_valid_price_change AS
 SELECT price_snapshot_id,
    product_id,
    product_name,
    seller_name,
    platform_name,
    product_url,
    prev_price,
    current_price,
    original_price,
    discount_rate,
    unit_price_per_kg,
    price_diff,
    price_change_pct,
    price_signal,
    collected_at,
    collect_date
   FROM vw_clean_price_change
  WHERE current_price IS NOT NULL AND prev_price IS NOT NULL AND current_price > 0::numeric AND prev_price > 0::numeric AND abs(price_change_pct) <= 50::numeric;
