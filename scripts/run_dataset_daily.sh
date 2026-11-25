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
  CODE=$?
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') 끝 (종료 코드 $CODE)"
  # 2026-11-22: 실패하면 상태 파일 + 맥 알림 — 다음 날 같은 시각에 다시 돈다(남은 것부터 이어서 처리)
  echo "$(date '+%Y-%m-%d %H:%M:%S') $CODE" > var/log/dataset_daily.status
  if [ "$CODE" -ne 0 ] && command -v osascript >/dev/null 2>&1; then
    osascript -e 'display notification "var/log/dataset_daily.log 를 확인해 주세요" with title "trendguide 학습 데이터 정리 실패"' || true
  fi
} >>"$LOG" 2>&1
