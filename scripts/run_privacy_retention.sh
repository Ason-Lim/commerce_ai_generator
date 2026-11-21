#!/usr/bin/env bash
# launchd 가 매일 새벽 4시 20분에 부른다 (ops/launchd/com.commerce_ai.privacy_retention.plist, 2026-11-21).
# 보존 기간 작업: 일별 집계로 접기 → 1년 지난 세션 값 가명 처리 → 90일 지난 대화·1년 지난 보관함 지우기 → 실수 신호 정리.
# 기록: var/log/privacy_retention.log
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p var/log
LOG=var/log/privacy_retention.log
PY=.venv/bin/python
{
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') 시작"
  if [ ! -x "$PY" ]; then
    echo ".venv 가 없어요 — 저장소에서 uv sync 를 먼저 실행해 주세요."
    exit 1
  fi
  PYTHONUNBUFFERED=1 "$PY" scripts/privacy_retention.py
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') 끝 (종료 코드 $?)"
} >>"$LOG" 2>&1
