# vw_ai_recommendation_final 상품 식별·100g당 가격·확인 시각 진단

- 실행: 2026-11-10T01:18:27+00:00 (읽기 전용) · 뷰 행 수: **294**
- 뷰 정의 덤프: `sql/reference/vw_ai_recommendation_final.current.sql` (저장소에 생성 SQL이 없었음)
- 뷰가 읽는 객체: vw_ai_recommendation_with_discount, vw_price_drop_recommendation_signal, vw_product_ctr_boost

## 1. 상품 식별

- 뷰 컬럼 51개 중 id류 컬럼: **없음**

| 후보 키 | NULL | 고유 값 | 중복 행 |
|---|---|---|---|
| product_url | 0 | 293 | 1 |
| product_name | 0 | 282 | 12 |
| product_name+seller_name | 0 | 291 | 3 |
| product_url+seller_name | 0 | 293 | 1 |

## 2. 스냅샷 결합 (main.py /recommendations/nl 과 같은 조건)

- 스냅샷이 붙은 행: 294 (100%)
  - URL 일치로 붙음: 282 (96%)
  - **상품명만 일치로 붙음**(URL 다름): 12 (4%) — 다른 판매처 상품이 붙을 수 있음
- 같은 URL·상품명 후보에 서로 다른 URL이 2개 이상: 22 (7%)
- 스냅샷 테이블에 collected_at 컬럼: 있음 · id 컬럼: 있음

## 3. price_per_100g 출처 (main.py 규칙 재현)

| 출처 | 행 |
|---|---|
| 스냅샷 price_per_100g | 12 (4%) |
| 뷰 unit_price_per_kg ÷ 10 | 145 (49%) |
| 상품명 중량 추정 (마지막 중량 사용) | 33 (11%) |
| 없음 — 가격은 있으나 중량 모름 | 104 (35%) |
| 없음 — 가격 없음 | 0 (0%) |

## 4. 가격 확인 시각

- main.py SELECT 목록에 `s.collected_at` 없음 → 현재 API 응답에 확인 시각이 실리지 않음 (코드 확인)
- 결합된 스냅샷 중 collected_at 있음: 294 (100%)

| 확인 시점 | 행 |
|---|---|
| 24시간 이내 | 0 |
| 7일 이내 | 0 |
| 30일 이내 | 0 |
| 30일 초과 | 294 |

## 5. 상품명만으로 붙은 예 (최대 15건)

| 뷰 상품명 | 뷰 판매처 | 스냅샷 몰 | URL 같음 |
|---|---|---|---|
| 고당도 샤인머스켓 2kg 3 4 5송이 안전포장 | 네이버/수수스토어 | 네이버/광주서부농수산시장 김은경 | 아니오 |
| 고당도샤인머스켓 수출용 프리미엄 선물용 샤인머스캣 망고포도 2kg 4kg | 네이버/경북영천 권춘화 | 네이버/민현농장 | 아니오 |
| 프리미엄 /배+사과 혼합7kg/명절 과일 선물 세트 | 네이버/옥션 | 네이버/G마켓 | 아니오 |
| 신고배 신고 배 15kg(13-20과) (특) 고당도배 나주배 | 네이버/롯데ON | 네이버/롯데ON | 아니오 |
| 신고배 신고 배 가정용 15kg(26-30과) 고당도배 나주배 | 네이버/롯데ON | 네이버/G마켓 | 아니오 |
| 나주배 신고배 특품 가정용 고당도 배 산지직송 5kg 7.5kg 15kg | 네이버/롯데ON | 네이버/G마켓 | 아니오 |
| 나주배 신고배 특품 가정용 고당도 배 산지직송 5kg 7.5kg 15kg | 네이버/옥션 | 네이버/G마켓 | 아니오 |
| 신고배 신고 배 가정용 15kg(26-30과) 고당도배 나주배 (S432 | 네이버/신세계몰 | 네이버/SSG닷컴 | 아니오 |
| 몽프루이 고당도 배 3kg (대과/3-4입) | 네이버/신세계몰 | 네이버/SSG닷컴 | 아니오 |
| 신고배 신고 배 가정용 15kg(26-30과) 고당도배 나주배 (S432 | 네이버/이마트몰 | 네이버/SSG닷컴 | 아니오 |
| +3천원쿠폰 담기 샛별배송 [KF365] 머스크멜론 1.6kg (후숙 필 | 마켓컬리 | 마켓컬리 | 아니오 |
| +3천원쿠폰 담기 샛별배송 [KF365] 머스크멜론 1.6kg (후숙 필 | 마켓컬리 | 마켓컬리 | 아니오 |

## 부록: 뷰 컬럼

fruit_name, product_name, seller_name, platform_name, price, unit_price_per_kg, discount_rate, is_high_brix, review_count, rating, recommendation_score, trust_first_score, adaptive_score, recommendation_label, trust_recommendation_label, adaptive_recommendation_label, product_url, impression_count, click_count, ctr_pct, expected_ctr_pct, rank_normalized_ctr_ratio, rank_ctr_label, ctr_boost, rank_ctr_boost, adaptive_score_v3, adaptive_label_v3, list_price, sale_price, coupon_name, coupon_amount, coupon_rate, final_price, final_discount_rate, coupon_expire_at, is_coupon_available, discount_collected_at, discount_freshness_status, effective_price, has_discount_info, ctr_feedback_boost, ctr_feedback_label, feedback_ctr_pct, price_drop_boost, price_drop_label, prev_price, latest_price, price_change_pct, final_recommendation_score, final_recommendation_label, recommendation_reason
