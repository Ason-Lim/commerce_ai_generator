# vw_ai_recommendation_final 의존 사슬과 평점·리뷰 사용 위치

- 실행: 2026-11-10T01:53:40+00:00 (읽기 전용)
- 정의 덤프: `sql/reference/<뷰>.current.sql` (19개)

## 1. 사슬 구조

| 객체 | 종류 | 읽는 객체 |
|---|---|---|
| vw_ai_recommendation_final | 뷰 | vw_ai_recommendation_with_discount(뷰), vw_price_drop_recommendation_signal(뷰), vw_product_ctr_boost(뷰) |
| vw_ai_recommendation_with_discount | 뷰 | vw_ai_adaptive_recommendation_v3(뷰), vw_product_discount_summary(뷰) |
| vw_price_drop_recommendation_signal | 뷰 | vw_valid_price_change(뷰) |
| vw_product_ctr_boost | 뷰 | vw_product_ctr_feedback(뷰) |
| vw_ai_adaptive_recommendation_v3 | 뷰 | vw_ai_adaptive_recommendation(뷰), vw_product_rank_normalized_ctr(뷰) |
| vw_product_discount_summary | 뷰 | product_master(테이블), vw_product_latest_discount(뷰) |
| vw_valid_price_change | 뷰 | vw_clean_price_change(뷰) |
| vw_product_ctr_feedback | 뷰 | product_click_log(테이블), recommendation_impression_log(테이블) |
| vw_ai_adaptive_recommendation | 뷰 | product_click_log(테이블), vw_trust_first_recommendation(뷰) |
| vw_product_rank_normalized_ctr | 뷰 | product_click_log(테이블), recommendation_impression_log(테이블), vw_rank_ctr_baseline(뷰) |
| product_master | 테이블 | - |
| vw_product_latest_discount | 뷰 | product_discount_snapshot(테이블) |
| vw_clean_price_change | 뷰 | vw_product_price_change(뷰), vw_suspicious_price_change(뷰) |
| product_click_log | 테이블 | - |
| recommendation_impression_log | 테이블 | - |
| vw_trust_first_recommendation | 뷰 | vw_recommendation_score(뷰) |
| vw_rank_ctr_baseline | 뷰 | product_click_log(테이블), recommendation_impression_log(테이블) |
| product_discount_snapshot | 테이블 | - |
| vw_product_price_change | 뷰 | platform_master(테이블), product_master(테이블), product_price_snapshot(테이블) |
| vw_suspicious_price_change | 뷰 | vw_product_price_change(뷰) |
| vw_recommendation_score | 뷰 | vw_admin_recommendable_products(뷰) |
| platform_master | 테이블 | - |
| product_price_snapshot | 테이블 | - |
| vw_admin_recommendable_products | 뷰 | vw_product_latest_price(뷰) |
| vw_product_latest_price | 뷰 | fruit_master(테이블), fruit_variety_master(테이블), platform_master(테이블), product_master(테이블), product_price_snapshot(테이블), product_quality_snapshot(테이블) |
| fruit_master | 테이블 | - |
| fruit_variety_master | 테이블 | - |
| product_quality_snapshot | 테이블 | - |

## 2. rating·review가 나오는 줄 (뷰 정의 원문)

### vw_ai_recommendation_final

```sql
  10: r.review_count,
  11: r.rating,
  69: review_count,
  70: rating,
```

### vw_ai_recommendation_with_discount

```sql
   9: r.review_count,
  10: r.rating,
```

### vw_ai_adaptive_recommendation_v3

```sql
  19: r.review_count,
  20: r.rating,
  59: review_count,
  60: rating,
```

### vw_ai_adaptive_recommendation

```sql
  19: r.rating,
  20: r.review_count,
  57: rating,
  58: review_count,
```

### vw_trust_first_recommendation

```sql
  10: rating,
  11: review_count,
  22: WHEN review_count IS NULL THEN 30
  23: WHEN review_count >= 2000 THEN 100
  24: WHEN review_count >= 1000 THEN 90
  25: WHEN review_count >= 500 THEN 80
  26: WHEN review_count >= 100 THEN 70
  27: WHEN review_count >= 30 THEN 55
  31: WHEN rating IS NULL THEN 50
  32: WHEN rating >= 4.8 THEN 100
  33: WHEN rating >= 4.5 THEN 90
  34: WHEN rating >= 4.0 THEN 80
  35: WHEN rating >= 3.5 THEN 60
  51: WHEN review_count IS NULL THEN 30
  52: WHEN review_count >= 2000 THEN 100
  53: WHEN review_count >= 1000 THEN 90
  54: WHEN review_count >= 500 THEN 80
  55: WHEN review_count >= 100 THEN 70
  56: WHEN review_count >= 30 THEN 55
  60: WHEN rating IS NULL THEN 50
  61: WHEN rating >= 4.8 THEN 100
  62: WHEN rating >= 4.5 THEN 90
  63: WHEN rating >= 4.0 THEN 80
  64: WHEN rating >= 3.5 THEN 60
  79: WHEN review_count >= 1000 AND is_high_brix = true THEN '리뷰 검증 고당도 추천'::text
  80: WHEN rating >= 4.5 AND is_high_brix = true THEN '평점 우수 고당도 추천'::text
  81: WHEN review_count >= 500 THEN '리뷰 검증 추천'::text
```

### vw_recommendation_score

```sql
  27: vw_admin_recommendable_products.review_count,
  28: vw_admin_recommendable_products.rating,
  45: WHEN vw_admin_recommendable_products.review_count IS NULL THEN 30
  46: WHEN vw_admin_recommendable_products.review_count >= 1000 THEN 100
  47: WHEN vw_admin_recommendable_products.review_count >= 500 THEN 85
  48: WHEN vw_admin_recommendable_products.review_count >= 100 THEN 70
  49: WHEN vw_admin_recommendable_products.review_count >= 30 THEN 55
  53: WHEN vw_admin_recommendable_products.rating IS NULL THEN 50
  54: WHEN vw_admin_recommendable_products.rating >= 4.8 THEN 100
  55: WHEN vw_admin_recommendable_products.rating >= 4.5 THEN 90
  56: WHEN vw_admin_recommendable_products.rating >= 4.0 THEN 75
  57: WHEN vw_admin_recommendable_products.rating >= 3.5 THEN 60
  79: rating,
  80: review_count,
```

### vw_admin_recommendable_products

```sql
  26: review_count,
  27: rating,
```

### vw_product_latest_price

```sql
  25: product_quality_snapshot.review_count,
  26: product_quality_snapshot.rating,
  57: lq.review_count,
  58: lq.rating,
```


## 3. 가격 관측 시각 범위

| 컬럼 | 최소 | 최대 | 건수 |
|---|---|---|---|
| online_food_price_snapshot.collected_at | 2026-04-24 17:23:55.593775 | 2026-07-16 19:31:46.127871 | 1123 |
| vw_ai_recommendation_final.discount_collected_at | 2026-05-15 19:18:33.090098 | 2026-05-15 19:18:33.090098 | 1 |

## 4. product_url 중복

| product_url | 행 | 판매처 | 상품명 |
|---|---|---|---|
| https://link.gmarket.co.kr/gate/pcs?item-no=1898683352&sub-i | 2 | G마켓 | 털보네사과 고당도 꿀사과 9kg   맛있는 털보네 부사 |
