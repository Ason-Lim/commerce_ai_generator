# R0 통제 검증 — 추천 경로 저장 · 관리자 클릭 저장

- 실행: 2026-11-10T13:01:43+00:00

- 주 경로 요청의 기록 path: ['canonical_provider'] → 통과
- 예비 경로 강제 요청의 기록 path: ['db_fallback'] → 통과
- 관리자 토큰 /go 클릭: 응답 307, 상품으로 이동 True
- 저장된 클릭: [{'query': 'chat_internal', 'product_name': '주왕산 털보네 고당도 사과 가정용 흠과 8kg 맛있는 털보네 부사', 'rank': 1, 'selected_section': 'chat'}] → 통과
- 정리: 검증 세션 2개의 행 삭제 {'product_click_log': 1, 'user_preference_profile': 1, 'user_product_preference': 1, 'user_session_context': 1, 'recipe_chat_session': 2}

※ 실행 중인 서버(run_prod.sh 등)는 코드를 다시 읽어야 새 기록 방식이 적용됨 — 서버 재시작 필요
