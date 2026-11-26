#!/usr/bin/env bash
# 부하 시험 한 번에 (창 6 오픈 준비, 2026-11-26) — 맥에서 시험 서버(:8011)를 따로 띄워 읽기 전용 주소에 동시 20·50·100 요청.
#   bash scripts/run_load_test.sh            → var/load_test/날짜_c20.json 등, 화면에 표
# 운영 서버(:8001)는 건드리지 않는다. 시험 서버는 쿠팡 호출을 끄고(COUPANG_API_ENABLED=false) 띄운다 — 쿠팡 한도 보호.
# 읽기만 하므로 운영 DB 를 그대로 읽어도 바뀌는 것은 없다. 끝나면 시험 서버를 끈다.
# 오픈 판단 기준(초안): 동시 20 에서 p95 < 1,000ms · 오류 0.
set -euo pipefail
cd "$(dirname "$0")/.."
PORT="${LOAD_PORT:-8011}"
if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "포트 $PORT 를 이미 쓰고 있어요 — 다른 번호로: LOAD_PORT=8012 bash scripts/run_load_test.sh"; exit 1
fi
DAY="$(date +%Y-%m-%d_%H%M)"
OUT="var/load_test"; mkdir -p "$OUT"
COUPANG_API_ENABLED=false API_PORT="$PORT" API_HOST=127.0.0.1 nohup ./run_api.sh > "$OUT/server_$DAY.log" 2>&1 &
SRV=$!
trap 'kill $SRV 2>/dev/null || true; pkill -f "uvicorn app.main:app --host 127.0.0.1 --port $PORT" 2>/dev/null || true' EXIT
for i in $(seq 1 60); do
  curl -s -o /dev/null "http://127.0.0.1:$PORT/" && break; sleep 1
done
FAIL=0
echo "── 켠 직후 첫 요청 (동시 20, 미리 부르지 않음) ──"
uv run python scripts/load_test.py --base "http://127.0.0.1:$PORT" --concurrency 20 --requests 160 --no-warm \
  --out "$OUT/${DAY}_cold.json" || FAIL=1
for C in 20 50 100; do
  echo "── 동시 $C ──"
  uv run python scripts/load_test.py --base "http://127.0.0.1:$PORT" --concurrency "$C" --requests $((C * 40)) \
    --out "$OUT/${DAY}_c$C.json" || FAIL=1
done
echo
echo "결과 파일: $OUT/${DAY}_c*.json · 서버 기록: $OUT/server_$DAY.log"
grep -c Traceback "$OUT/server_$DAY.log" >/dev/null && echo "서버 오류(Traceback) $(grep -c Traceback "$OUT/server_$DAY.log")건 — 기록을 확인해 주세요" || echo "서버 오류 없음"
exit $FAIL
