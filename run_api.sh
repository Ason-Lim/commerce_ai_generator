#!/usr/bin/env bash
# commerce_ai_generator FastAPI (POST /api/chat · GET /go · /recommendations/*)
# 설정은 .env 또는 환경변수로만 읽는다 (.env.example 참고). 경로는 이 스크립트 위치 기준.
set -euo pipefail
cd "$(dirname "$0")"
exec python -m uvicorn app.main:app --host "${API_HOST:-127.0.0.1}" --port "${API_PORT:-8001}" ${API_RELOAD:+--reload}
