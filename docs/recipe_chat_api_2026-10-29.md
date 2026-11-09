# 대화 API(/api/chat) — 쇼핑·레시피 통합 (2026-10-29)

## 흐름
React `integrated_system/ui_ux` ChatWindow → `sendChat` → **commerce_ai_generator `POST /api/chat`** → `{session_id, stage, blocks}` → BlockRenderer
(이전에는 integrated_system `consumer/app.py :8000` 이 응답. 인트로·컴포넌트는 변경 없음, 프록시 대상만 `.env.commerce`)

- 쇼핑: 기존 `/recommendations/nl` 함수를 그대로 호출 → `product_list` 블록. `/go/{sid}/{rank}` 는 그 세션이 보여 준 http(s) URL 로만 이동
- 레시피: `app/services/recipe_chat` → 기존 `recipe_session` (EPIS 467 스냅샷, store·flow·save_direct·resume) 재사용
- NLU: `app/services/nlu` (food-nlu 의 LLMClient·사전 프롬프트·validate 이식). 외부 폴더 로딩·sys.path·`/Users/...` 경로 제거

## 실행
```bash
cp .env.example .env   # 값 채우기 (DeepSeek 키는 서버 .env 에만)
python -m scripts.recipe_chat_db check        # 읽기 전용: 기존 recipe 테이블 확인
python -m scripts.recipe_chat_db init         # recipe_chat_session 생성 (IF NOT EXISTS)
python -m scripts.migrate_nlu_dictionary --source-url postgresql+psycopg2://mom@localhost:5432/postgres          # dry run
python -m scripts.migrate_nlu_dictionary --source-url postgresql+psycopg2://mom@localhost:5432/postgres --apply  # 충돌 없을 때만
./run_api.sh                                  # :8001
cd ../integrated_system/ui_ux && npm run dev:commerce
```

## 테스트
`pip install -r requirements-dev.txt && python -m pytest -q tests/services/chat tests/services/nlu`
실 DB 종단 확인(별도 DB): `createdb recipe_chat_verify && python -m scripts.recipe_chat_db verify --database-url postgresql+psycopg2://mom@localhost:5432/recipe_chat_verify`

변경 전 파일 백업: `recipe_chat_api_backups/20261029_1100/`
