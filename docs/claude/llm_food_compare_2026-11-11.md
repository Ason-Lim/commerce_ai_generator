# 식품 상담 AI 비교 — DeepSeek · GPT · Claude (2026-11-11)

채팅의 식품 상담(제철·품종·손질·보관·먹는 법)에 어떤 모델을 쓸지 정하기 위한 비교.
결과 화면(아티팩트): "식품 상담 AI 비교" — 질문별 세 답 나란히, 블라인드 보기, 답 고르기 집계.

## 스크립트
`scripts/llm_food_compare.py`

- 서비스와 같은 조건: 시스템 프롬프트 `app/services/chat/food_tips.PROMPT`, 결과는 `food_tips.validated` 로 같은 검증
  → 화면에 실제로 나갈 답만 비교한다 (금지 내용·형식 오류는 서비스처럼 버려짐).
- 질문 20개: 품종·제철 12 · 손질·보관·먹는 법 8 (`QUESTIONS` 목록 — 바꾸거나 늘려서 다시 돌릴 수 있다).
- 기록: 답(원문·검증 후), 응답 시간, 입력·출력 토큰. 품종 이름은 국립종자원 목록(`data/reference/seed_varieties.json`)이 있으면 대조.
- 키는 `.env` 에서 읽고 결과 파일에는 남기지 않는다.

```
uv run python scripts/llm_food_compare.py                         # .env 의 모델 3개
uv run python scripts/llm_food_compare.py --gpt-model gpt-4.1     # GPT 모델 바꾸기 (--deepseek-model, --claude-model 도 있음)
uv run python scripts/llm_food_compare.py --only deepseek,claude  # 일부 모델만
```
결과: `var/llm_compare/food_compare_<시각>.json`. 60번 호출(20 × 3)에 몇 분·수백 원 수준.

주의: 최신 Claude 모델(claude-sonnet-5-5)은 `temperature` 를 받지 않는다(400 오류) — 스크립트는 빼고 호출한다.
관리자 LLM 연결(`app/admin/shared/llm.py`)은 anthropic 에도 temperature 를 넘기므로 LLM_PROVIDER=anthropic 으로 바꾸면 같은 오류가 난다 (지금은 deepseek 사용 중이라 영향 없음).

## 2026-11-11 결과 (`var/llm_compare/food_compare_merged.json`)

| | DeepSeek `deepseek-v4-flash` | GPT `gpt-4.1-mini` | Claude `claude-sonnet-5-5` |
|---|---|---|---|
| 응답 시간 중앙값 | 3.7초 | 1.8초 | 3.4초 |
| 토큰 입력 / 출력 (20문항 합) | 9,662 / 10,227 | 7,885 / 2,382 | 12,568 / 6,408 |
| 보여 준 팁 / 품종 설명 | 78줄 / 39개 | 66줄 / 34개 | 73줄 / 39개 |
| 확인 필요 | 2건 | 7건 | 3건 |

- GPT 는 .env 에 있던 작은 모델(4.1-mini)이라 같은 급 비교가 아니다.
- "확인 필요"는 Claude(Opus, 이 비교를 만든 세션)가 자기 지식으로 단 표시다. 출처로 확인한 것이 아니고, Claude 답에 너그러울 수 있다.
- 세 모델 모두 품종 특징(단단함·무름, 분질·점질)에서 틀린 곳이 있었다 → 품종 설명은 'AI 정리' 표시와 국립종자원 이름 대조를 유지한다.

확인 필요 목록
- 딸기: DeepSeek 매향 '부드러운 편' · GPT 금실 '부드러운 식감' · Claude 금실 '과육이 부드러움' (매향·금실은 단단한 편으로 알려짐)
- 사과: GPT 부사·후지를 다른 품종으로 나열 (같은 품종)
- 포도: DeepSeek 캠벨얼리 '껍질째 먹기 좋다' · Claude '캠벨얼'(이름 잘림)
- 감자: GPT 대지 '전분 함량 높음'·'참감자'(품종 아님) · Claude 대지마 '분질'·두백 '점질에 가까움' (반대로 적힘)
- 복숭아: GPT 백도·황도를 품종으로 (과육 색 구분)
- 쌀: GPT 추청 '찹쌀에 가까운 찰기' (과장)
- 대봉감: GPT 홍시 '3~5일' (보통 1~2주)
- 굴: GPT '소금물에 해감' (해감은 조개류)

## 비용 (답 1개 평균, 이번 실행 토큰 기준)
요금은 2026-11-11 확인한 공개 자료 기준 — 바뀔 수 있다.
- DeepSeek V4 Flash: 입력 $0.14 / 출력 $0.28 (100만 토큰당, 캐시 미적중) → 답 1개 약 $0.0002 (약 0.3원)
- Claude Sonnet 5.5: 입력 $2 / 출력 $10 → 답 1개 약 $0.0045 (약 6원), DeepSeek 의 약 20배
- 1만 건: DeepSeek 약 $2 · Claude 약 $45. 제철·품종 답을 식품별로 한 번 만들어 저장해 다시 쓰면 Claude 도 1회 비용만 든다.

## 결정 (2026-11-11)
- 식품 상담은 DeepSeek 로 계속 쓴다 (사용자 판단: "딥시크만 써도 될 듯").
