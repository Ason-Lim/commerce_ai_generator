#!/usr/bin/env bash
# 운영용 (2026-11-02): 화면을 빌드한 뒤 서버 하나(:8001)에서 화면과 API를 함께 보여 준다. 자동 재시작 없음.
#   ./run_prod.sh               → 브라우저에서 http://localhost:8001
#   ./run_prod.sh --skip-build  → 이미 빌드한 화면(frontend/dist)으로 바로 실행
#   클라우드: API_HOST=0.0.0.0 ./run_prod.sh   (앞단에 HTTPS 프록시를 두는 것을 전제로)
set -euo pipefail
cd "$(dirname "$0")"
# 이 저장소의 가상환경이 있으면 그것으로 실행 (source .venv/bin/activate 를 따로 하지 않아도 된다)
if [ -f .venv/bin/activate ]; then set +u; source .venv/bin/activate; set -u; fi

if lsof -nP -iTCP:"${API_PORT:-8001}" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "포트 ${API_PORT:-8001} 를 이미 쓰는 프로그램이 있어요. 먼저 ./stop_api.sh 로 꺼 주세요."
  lsof -nP -iTCP:"${API_PORT:-8001}" -sTCP:LISTEN
  exit 1
fi

if [ "${1:-}" != "--skip-build" ]; then
  echo "화면 빌드 중…"
  (
    cd frontend
    if [ ! -d node_modules ] || [ package-lock.json -nt node_modules ]; then npm ci; fi
    npm run build
  )
fi

unset API_RELOAD
exec ./run_api.sh
