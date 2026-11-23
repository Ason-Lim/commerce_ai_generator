#!/usr/bin/env bash
# launchd 가 매주 일요일 23:30 에 부른다 (ops/launchd/com.commerce_ai.weekly_improve.plist, 2026-11-23 — 월요일 오전에 봄).
# 주간 개선 지표: var/improve/YYYY-Www.md · .json (scripts/weekly_improve.py). 기록: var/log/weekly_improve.log
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p var/log
LOG=var/log/weekly_improve.log
PY=.venv/bin/python
{
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') 시작"
  if [ ! -x "$PY" ]; then
    echo ".venv 가 없어요 — 저장소에서 uv sync 를 먼저 실행해 주세요."
    exit 1
  fi
  # 일요일 밤에 돌므로 그 주 일요일(오늘)까지 — 기본값(어제)이 아니라 오늘 날짜를 끝으로
  PYTHONUNBUFFERED=1 "$PY" scripts/weekly_improve.py --end "$(date '+%Y-%m-%d')"
  CODE=$?
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') 끝 (종료 코드 $CODE)"
  echo "$(date '+%Y-%m-%d %H:%M:%S') $CODE" > var/log/weekly_improve.status
  if [ "$CODE" -ne 0 ] && command -v osascript >/dev/null 2>&1; then
    osascript -e 'display notification "var/log/weekly_improve.log 를 확인해 주세요" with title "commerce_ai 주간 개선 지표 실패"' || true
  fi
} >>"$LOG" 2>&1
