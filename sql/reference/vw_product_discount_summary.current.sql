-- vw_product_discount_summary 현재 DB 정의 덤프 (참고용, 실행용 아님)
-- 추출: 2026-11-10T01:53:40+00:00
-- 의존 객체: product_master, vw_product_latest_discount

CREATE OR REPLACE VIEW vw_product_discount_summary AS
 SELECT p.product_id,
    p.product_name,
    p.seller_name,
    p.product_url,
    d.list_price,
    d.sale_price,
    d.coupon_name,
    d.coupon_amount,
    d.coupon_rate,
    d.final_price,
    d.final_discount_rate,
    d.coupon_expire_at,
    d.is_coupon_available,
    d.collected_at AS discount_collected_at,
        CASE
            WHEN d.collected_at IS NULL THEN '할인정보 없음'::text
            WHEN d.collected_at < (now() - '06:00:00'::interval) THEN '할인정보 오래됨'::text
            ELSE '할인정보 최신'::text
        END AS discount_freshness_status
   FROM product_master p
     LEFT JOIN vw_product_latest_discount d ON p.product_id = d.product_id;
