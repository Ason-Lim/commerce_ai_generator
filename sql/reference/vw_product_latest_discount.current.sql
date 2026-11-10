-- vw_product_latest_discount 현재 DB 정의 덤프 (참고용, 실행용 아님)
-- 추출: 2026-11-10T01:53:40+00:00
-- 의존 객체: product_discount_snapshot

CREATE OR REPLACE VIEW vw_product_latest_discount AS
 SELECT id,
    product_id,
    collected_at,
    list_price,
    sale_price,
    coupon_name,
    coupon_amount,
    coupon_rate,
    final_price,
    final_discount_rate,
    coupon_expire_at,
    source_url,
    is_coupon_available,
    rn
   FROM ( SELECT d.id,
            d.product_id,
            d.collected_at,
            d.list_price,
            d.sale_price,
            d.coupon_name,
            d.coupon_amount,
            d.coupon_rate,
            d.final_price,
            d.final_discount_rate,
            d.coupon_expire_at,
            d.source_url,
            d.is_coupon_available,
            row_number() OVER (PARTITION BY d.product_id ORDER BY d.collected_at DESC) AS rn
           FROM product_discount_snapshot d) t
  WHERE rn = 1;
