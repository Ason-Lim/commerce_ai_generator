#!/usr/bin/env bash
# commerce_ai_generator FastAPI (POST /api/chat · GET /go · /recommendations/*)
# 설정은 .env 또는 환경변수로만 읽는다 (.env.example 참고). 경로는 이 스크립트 위치 기준.
set -euo pipefail
cd "$(dirname "$0")"
# uv 가 있으면 uv.lock 과 같은 패키지로 맞춘 뒤 실행 (없는 패키지만 설치, 기존 패키지는 지우지 않음 · 2026-11-11)
#   uv 가 없으면 예전처럼 현재 python 으로 실행한다.
if command -v uv >/dev/null 2>&1 && [ -f uv.lock ]; then
  exec uv run --locked python -m uvicorn app.main:app --host "${API_HOST:-127.0.0.1}" --port "${API_PORT:-8001}" ${API_RELOAD:+--reload}
fi
exec python -m uvicorn app.main:app --host "${API_HOST:-127.0.0.1}" --port "${API_PORT:-8001}" ${API_RELOAD:+--reload}
