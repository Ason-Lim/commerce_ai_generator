#!/usr/bin/env bash
# launchd 가 매주 일요일 새벽 3시에 부른다 (ops/launchd/com.commerce_ai.warm_food_knowledge.plist, 2026-11-11).
# 자주 묻는 식품 답을 DeepSeek 한가한 시간에 미리 만들어 저장. 기록: var/log/warm_food_knowledge.log
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p var/log
LOG=var/log/warm_food_knowledge.log
PY=.venv/bin/python
{
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') 시작"
  if [ ! -x "$PY" ]; then
    echo ".venv 가 없어요 — 저장소에서 uv sync 를 먼저 실행해 주세요."
    exit 1
  fi
  PYTHONUNBUFFERED=1 "$PY" scripts/warm_food_knowledge.py
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') 끝 (종료 코드 $?)"
} >>"$LOG" 2>&1
