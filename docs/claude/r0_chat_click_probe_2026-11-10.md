# R0 진단 — 채팅 클릭 기록 · 채팅 쇼핑 대화

- 실행: 2026-11-10T07:06:21+00:00

## 1. 채팅 세션 (recipe_chat_session, 읽기만)

- sessions: 63
- shopping_sessions: 16
- shopping_turns_kept: 34
- sessions_with_last_items: 18
- first_update: 2026-10-29 11:06:36.829791+09:00
- last_update: 2026-11-10 10:50:04.467464+09:00
- shopping_turn_paths: {'(기록 없음)': 34}

## 2. 채팅 /go 클릭 기록 재현 (끝에 되돌림)

- **실패**: IntegrityError: (psycopg2.errors.NotNullViolation) null value in column "product_name" of relation "user_product_preference" violates not-null constraint
- 위치: analytics_logger.py:157 log_product_click
- 채팅 /go·/api/click 은 이 예외를 잡아 경고 로그만 남기므로 클릭이 조용히 사라짐
- 되돌림 확인: 진단 세션 행 0개 남음 (0이어야 함)

## 3. 추천 경로 기록

- `recommendation_path`(canonical_provider / db_fallback)는 지금 어디에도 저장되지 않음 → 과거 fallback 비율은 셀 수 없음
- 2026-11-10부터 채팅 쇼핑 대화 기록(turns)에 경로를 남김 → 이후 대화부터 비율 집계 가능
