#!/usr/bin/env bash
# launchd 가 매일 새벽 4시 40분에 부른다 (ops/launchd/com.commerce_ai.dataset_daily.plist, 2026-11-21).
# 로컬 모델 학습 데이터셋: 임시 칸 → 학습 칸 승격(클릭 신호), 90일 지난 임시 칸·보관 기간 지난 예시 지우기.
# 기록: var/log/dataset_daily.log
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p var/log
LOG=var/log/dataset_daily.log
PY=.venv/bin/python
{
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') 시작"
  if [ ! -x "$PY" ]; then
    echo ".venv 가 없어요 — 저장소에서 uv sync 를 먼저 실행해 주세요."
    exit 1
  fi
  PYTHONUNBUFFERED=1 "$PY" scripts/dataset_daily.py
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') 끝 (종료 코드 $?)"
} >>"$LOG" 2>&1
