# commerce_ai_generator 데이터 경로 인벤토리 (2026-11-02)

방식: 맥 저장소 `/Users/mom/commerce_ai_generator`를 읽기 전용으로 정적 스캔(grep·코드 열람)하고, 사용자가 맥에서 읽기 전용 조회 스크립트(check_snapshot_sources.py, check_snapshot_reviews.py)로 Postgres를 조회. 파일 수정·DB 쓰기·커밋 없음(조회 스크립트 3개 추가만). 런타임 추적이 아니므로 "경로 미발견"은 이 스캔 범위 한정. G등급 전 행 미판정·구현 승인 없음·production HOLD 유지.

## 1. 페이지 수집(스크래핑) 코드 — 존재 확인

| 파일 | 방식 | 대상 | 저장 | 호출 방식 |
|---|---|---|---|---|
| scripts/coupang_review_collector.py (git d28b787, 2026-05-06) | Selenium | `www.coupang.com/np/search` + 상품 페이지 | online_food_price_snapshot INSERT (source_type='coupang_review', 평점·리뷰 수) | 수동 실행 |
| scripts/update_reviews_ratings.py | requests, 데스크톱 Chrome UA 지정 | DB의 product_url (쿠팡·스마트스토어·컬리 판별) | snapshot UPDATE | 수동 실행 |
| scripts/update_reviews_ratings_selenium.py | Selenium | 위와 같음 | snapshot UPDATE | 수동 실행 |
| app/services/kurly_review_playwright_collector.py | Playwright, Chrome UA 지정 | smartstore.naver.com 상품 페이지 | snapshot UPDATE | `__main__` 수동 실행 |
| app/services/kurly_nmart_collector_v3.py | Playwright, Chrome UA 지정 | smartstore.naver.com 상품 페이지 | snapshot UPDATE | `__main__` 수동 실행 |
| collectors/naver_smartstore_json_collector.py (via collector_router, collector_v4_runner) | requests HTML | smartstore.naver.com | snapshot UPDATE | `python -m app.services.collector_v4_runner` |

- 스케줄러·cron·API 경로에서 이 수집기를 호출하는 코드는 발견되지 않음(B2B 입찰 수집 cron 스크립트만 존재).
- 16개 대상 몰(미트박스 등) 수집 코드는 없음. SSG·롯데는 registry 이름과 검색 링크 생성(`build_ssg_search_url`, 네트워크 요청 없음)만 있음.
- 쿠팡 robots.txt `*` Disallow:/ 확인 결과(R16)와 coupang_review_collector.py는 직접 충돌 후보. 단 DB에 쿠팡 행은 0건(§5).
- `source_type='kurly_selenium_html'`은 platform_normalization.py가 URL에 kurly.com이 있으면 붙이는 라벨이며, 그 자체로 Selenium 수집 증거는 아님.

## 2. 공식 API 경로

- 네이버 쇼핑 검색 API(`openapi.naver.com/v1/search/shop.json`): `/generate` 요청마다 `collect_naver_products` 호출 → snapshot INSERT(가격·썸네일 URL·raw_payload 포함). 저장 조건 확인 필요.
- 쿠팡 Partners 검색 API: market/collector.py, admin/shared/markets/coupang.py. 저장 코드 미발견. `record_offers`(offer_observation)는 정의만 있고 호출처 없음, core.sqlite3 파일도 없음.

## 3. 외부 AI 전송 (.env: LLM_PROVIDER=deepseek, ADMIN_LLM_PROVIDER=anthropic, RECIPE_AI_IMAGE_MODEL=gpt-image-1)

| 기능 | 대상 | 전송 데이터 | 원천 |
|---|---|---|---|
| 쇼핑 상품어 추출 (chat_routes→service.shopping_terms) | DeepSeek | 고객 문장만 | 고객 입력 |
| 레시피 상담 consult | DeepSeek | 질문 200자, 이전 요리·목표 | 고객 입력 |
| 트렌드 해석 discover.py:528 | DeepSeek | 검색 결과 제목 최대 45건 | 네이버 검색 API |
| 급상승 surge | DeepSeek | 블로그 건수·단서 요약 | 네이버 검색 API·데이터랩 |
| 쉽게 보기·보충·AI 레시피·인분 | DeepSeek | 레시피 본문·요리명 | 식품안전나라·EPIS·고객 입력 |
| 재고 대화 direct_stock_chat | DeepSeek | 고객 메시지 + 재료 목록 | 고객 입력 |
| 레시피 이미지 ai_image | OpenAI | 요리명, 재료 10개, 마지막 단계 160자 | 공공 레시피 |
| B2B 공고 해석 request_parser | Anthropic | 공고 원문 6,000자 | 나라장터·업로드 문서 |
| 제안서 다듬기 _polish | Anthropic | 요약 3~4문장(인원·단가·기한) | 공고 조건 |
| OCR 검토 commerce_ai_local_ocr/review.py | OpenAI Responses API | 문서 이미지 조각(base64) | B2B 증빙 문서로 추정, 미확인 |

- 쿠팡 상품 데이터(상품명·가격)가 LLM 요청 본문에 들어가는 경로는 이번 정적 스캔에서 발견되지 않음. chat/explain.py는 LLM import 없음.

## 4. 목적별 근거 매트릭스 (현재 상태)

| 원천 | 수집 | 저장 | 상업 표시 | 이미지 | 외부 AI 전송 | 학습 |
|---|---|---|---|---|---|---|
| 쿠팡 페이지 | 코드 존재(R16 차단과 충돌 후보) | DB 0건 | 없음 | 해당없음 | 경로 미발견 | 경로 미발견 |
| 쿠팡 Partners API | 사용 중 | 코드 미발견 | 사용 중, 약관 미확보 | 미확보 | 경로 미발견 | 경로 미발견 |
| 네이버 쇼핑 API | 사용 중 | 사용 중(raw_payload 포함), 약관 미확보 | 사용 중, 약관 미확보 | 썸네일 URL 저장 | 경로 미발견 | 경로 미발견 |
| 스마트스토어 페이지 | 코드 존재 | 평점 1행 | 레거시 경로 | — | 경로 미발견 | 경로 미발견 |
| 컬리 페이지 | 코드 존재(update_reviews_ratings*) | 리뷰 수 25행 추정 | 레거시 경로 | — | 경로 미발견 | 경로 미발견 |
| 온브릭스 페이지 | 전용 코드 없음, 범용 보강 스크립트 추정 | 평점·리뷰 6행 | 레거시 경로 | — | 경로 미발견 | 경로 미발견 |
| 네이버 검색 API(블로그 등) | 사용 중 | 미확인 | 일부 | — | DeepSeek(제목) 약관 미확보 | 미확인 |
| 공공 레시피 | 사용 중 | 사용 중 | 사용 중 | AI 생성 | DeepSeek·OpenAI 이용조건 미확보 | — |
| 나라장터 공고 | API 승인 | 사용 중 | 내부용 | — | Anthropic | — |
| 16개 몰(온브릭스 외) | 코드 없음 | 네이버 API 경유 행만 | 레거시 경로 | — | 없음 | 없음 |

## 5. Postgres online_food_price_snapshot 조회 결과 (2026-11-02, 사용자 실행)

- 전체 1,123행. 쿠팡 관련 행(URL·몰명·source_type) 0건.
- 평점 또는 리뷰 수가 있는 행 33건, collected_at 2026-04-24 ~ 2026-05-06:
  - 마켓컬리 www.kurly.com 24행(리뷰 수 24), 2026-04-24~27
  - 네이버/온브릭스 www.onbrix.co.kr 6행(평점 4, 리뷰 6), 2026-04-27
  - 화려한우 smartstore 1행(평점), 네이버/컬리 redirect.kurly.com 1행, 네이버/G마켓 link.gmarket.co.kr 1행
  - 네이버 쇼핑 API는 평점·리뷰 수를 반환하지 않으므로 이 값들은 페이지 보강 스크립트로 채워진 것으로 추정. 보강 시각은 updated_at 컬럼이 없어 미확인.
- 16개 대상 몰 이름이 들어간 행(모두 네이버 API 경유): 온브릭스 49, 롯데ON 15, SSG닷컴 5, 이마트몰 1, 홈플러스 1.
- 사용처: 평점·리뷰 수는 레거시 `/generate`(main.py, vw_ai_recommendation_final)와 Streamlit·score_engine 점수에 쓰임. 소비자 채팅 `/api/chat`·recipe_chat 코드는 이 테이블을 읽지 않음(정적 스캔 기준).
