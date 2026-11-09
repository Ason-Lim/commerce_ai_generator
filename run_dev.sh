#!/usr/bin/env bash
# 개발용 (2026-11-02): 백엔드 :8001 (코드를 고치면 자동 재시작) + 화면 개발 서버 :5173 (화면을 고치면 바로 반영)
#   ./run_dev.sh   → 브라우저에서 http://localhost:5173
#   끄기: Ctrl+C 한 번 (두 서버 모두 꺼짐)
set -euo pipefail
cd "$(dirname "$0")"
# 이 저장소의 가상환경이 있으면 그것으로 실행 (source .venv/bin/activate 를 따로 하지 않아도 된다)
if [ -f .venv/bin/activate ]; then set +u; source .venv/bin/activate; set -u; fi

for port in 8001 5173; do
  if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "포트 $port 를 이미 쓰는 프로그램이 있어요. 먼저 ./stop_api.sh 로 끄거나 그 창에서 Ctrl+C 해 주세요."
    lsof -nP -iTCP:"$port" -sTCP:LISTEN
    exit 1
  fi
done

if [ ! -d frontend/node_modules ]; then
  echo "화면 패키지를 처음 설치합니다 (1회)…"
  (cd frontend && npm ci)
fi

API_RELOAD=1 ./run_api.sh &
API_PID=$!
trap 'kill "$API_PID" 2>/dev/null || true' EXIT INT TERM

cd frontend
npm run dev
