-- vw_product_price_change 현재 DB 정의 덤프 (참고용, 실행용 아님)
-- 추출: 2026-11-10T01:53:40+00:00
-- 의존 객체: platform_master, product_master, product_price_snapshot

CREATE OR REPLACE VIEW vw_product_price_change AS
 WITH ordered AS (
         SELECT p.price_snapshot_id,
            p.product_id,
            m.product_name,
            m.seller_name,
            m.product_url,
            pf.platform_name,
            p.price,
            p.original_price,
            p.discount_rate,
            p.unit_price_per_kg,
            p.collected_at,
            p.collect_date,
            lag(p.price) OVER (PARTITION BY p.product_id ORDER BY p.collected_at, p.price_snapshot_id) AS prev_price
           FROM product_price_snapshot p
             LEFT JOIN product_master m ON p.product_id = m.product_id
             LEFT JOIN platform_master pf ON m.platform_id = pf.platform_id
        )
 SELECT price_snapshot_id,
    product_id,
    product_name,
    seller_name,
    platform_name,
    product_url,
    prev_price,
    price AS current_price,
    original_price,
    discount_rate,
    unit_price_per_kg,
    price - prev_price AS price_diff,
    round(
        CASE
            WHEN prev_price IS NULL OR prev_price = 0::numeric THEN NULL::numeric
            ELSE (price - prev_price) / prev_price * 100::numeric
        END, 1) AS price_change_pct,
        CASE
            WHEN prev_price IS NULL THEN 'NEW'::text
            WHEN price < prev_price THEN 'PRICE_DOWN'::text
            WHEN price > prev_price THEN 'PRICE_UP'::text
            ELSE 'UNCHANGED'::text
        END AS price_signal,
    collected_at,
    collect_date
   FROM ordered;
