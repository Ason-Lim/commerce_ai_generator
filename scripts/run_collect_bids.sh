#!/usr/bin/env bash
# launchd 가 매일 새벽 4시에 부른다 (ops/launchd/com.commerce_ai.collect_bids.plist, 2026-11-25).
# 나라장터 입찰 공고 수집 — 기본 최근 3일(겹쳐도 같은 공고는 한 번만 저장). 밀린 기간은 COLLECT_DAYS=30 처럼.
# 성공하면 B2B 콘솔 '입찰 트렌드'의 '최종 추출' 시각이 바뀐다. 기록: var/log/collect_bids.log
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p var/log
LOG=var/log/collect_bids.log
PY=.venv/bin/python
DAYS="${COLLECT_DAYS:-3}"
{
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') 시작 (최근 ${DAYS}일)"
  if [ ! -x "$PY" ]; then
    echo ".venv 가 없어요 — 저장소에서 uv sync 를 먼저 실행해 주세요."
    exit 1
  fi
  PYTHONUNBUFFERED=1 "$PY" -m scripts.admin.collect_bids --days "$DAYS"
  CODE=$?
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') 끝 (종료 코드 $CODE)"
  echo "$(date '+%Y-%m-%d %H:%M:%S') $CODE" > var/log/collect_bids.status
  if [ "$CODE" -ne 0 ] && command -v osascript >/dev/null 2>&1; then
    osascript -e 'display notification "var/log/collect_bids.log 를 확인해 주세요 (나라장터 키·인터넷)" with title "trendguide 입찰 공고 수집 실패"' || true
  fi
} >>"$LOG" 2>&1
