# 노출·클릭 기록 조사 (1단계)

- 실행: 2026-11-10T06:32:08+00:00 (읽기 전용)

## 1. 테이블별 기록 양과 기간

| 테이블 | 행 | 처음 | 마지막 | 최근 30일 |
|---|---|---|---|---|
| recommendation_impression_log | 1102 | 2026-05-14 16:34:22.918680 | 2026-05-30 00:28:32.006052 | 0 |
| impression_log | 3589 | 2026-06-01 20:07:09.859371 | 2026-07-16 19:31:51.779640 | 0 |
| product_click_log | 582 | 2026-05-13 18:40:53.613007 | 2026-07-16 19:33:01.198947 | 0 |
| search_log | 494 | 2026-05-13 18:40:53.601556 | 2026-07-16 19:31:51.800148 | 0 |

## 2. 클릭 기록 — 출처별 (selected_section · query)

| section | query_kind | clicks | sessions | first | last |
|---|---|---|---|---|---|
| hero | 그 밖 | 234 | 13 | 2026-05-20 | 2026-07-16 |
| main | 그 밖 | 209 | 1 | 2026-06-05 | 2026-07-16 |
| revisit | 그 밖 | 103 | 1 | 2026-06-19 | 2026-07-16 |
| (없음) | 그 밖 | 36 | 11 | 2026-05-13 | 2026-05-20 |

## 3. recommendation_impression_log — 월별

| month | impressions | sessions | products |
|---|---|---|---|
| 2026-05 | 1102 | 133 | 69 |

## 4. 추천 뷰가 쓰는 노출·클릭 신호 (vw_ai_recommendation_final)

| products | with_impressions | with_clicks | clicks_gt_impressions | impressions_ge_10 | ctr_boost_nonzero | rank_ctr_boost_nonzero | ctr_feedback_nonzero | click_boost_nonzero | impressions_total | clicks_total |
|---|---|---|---|---|---|---|---|---|---|---|
| 294 | 70 | 10 | 0 | 48 | 0 | 44 | 15 | 16 | 1114 | 27 |

## 5. 채팅 클릭이 추천 뷰 상품과 겹치는가 (product_url 일치)

| chat_click_urls | in_view |
|---|---|
| 0 | 0 |

## 해석 메모 (2026-11-10 수정 — 처음 메모의 오류 정정)

- **모든 행동 기록이 2026-07-16 이후 없음** (표 1 '최근 30일' 모두 0). 가격 스냅샷 마지막 수집(2026-07-16)과 같은 날 — Streamlit 시절 기록이 멈춘 것
- 클릭 기록 582건은 전부 Streamlit 출처(hero·main·revisit·없음). **채팅(query='chat') 클릭은 0건** (표 2·5). 채팅의 /go·/api/click 기록이 실제로 쌓이는지 따로 확인 필요 — 기록 실패는 경고 로그만 남김
- CTR 계열 가산점(ctr_boost·rank_ctr_boost·ctr_feedback_boost)의 분모 `recommendation_impression_log`는 **2026-05-30이 마지막**이고 앱 코드에 쓰는 곳이 없음
- **정정**: 처음 메모의 "`impression_log`는 어떤 점수 뷰도 읽지 않음"은 틀림. `main.py`가 붙이는 `vw_product_boost`(← `vw_product_performance`)와 `vw_recommendation_mode_boost`(← `vw_recommendation_feedback`)가 `impression_log`를 읽음 → 행동 기반 가점은 **6종**: click·ctr·rank_ctr·ctr_feedback(뷰) + product·mode(main.py). mode_boost는 같은 모드 전 상품에 같은 값이라 순서에는 영향 없음
- **정정**: "클릭 URL이 DB 뷰 상품과 대부분 다름"은 근거 없음 — 비교할 채팅 클릭이 0건
- `clicks_gt_impressions` 0행 — 클릭이 노출을 넘는 사례는 관측되지 않음. 다만 노출 원본 1,102행 vs 뷰 합계 1,114회로 조인 과정에서 같은 노출이 여러 행에 합산되는지 추적 필요 (URL 중복 1건 확인됨)
- 현재 상태: 가점 적용 행 — click 16, rank_ctr 44, ctr_feedback 15, ctr 0 (표 4). 내부 화면 표기: **과거 행동 가점 적용 · 실제 노출 미검증**. 기존 `EXPOSURE_UNVERIFIED` 판정 유지
- 행동 가점이 순위에 주는 영향: `scripts/stage1_behavior_counterfactual.py` 결과 참고
