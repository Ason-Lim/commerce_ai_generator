#!/bin/bash
# 매일 10:00 launchd 실행: 홈 화면 예시 질문 JSON 생성 (표준 라이브러리만 쓰므로 파이썬 버전 변경과 무관)
# 2026-11-04 integrated_system 에서 옮김 → frontend/src/data 에 저장, 화면은 /api/trend-examples 로 그날 파일을 읽는다
cd "$(dirname "$0")/.." || exit 1
mkdir -p var/logs
LOG="var/logs/trend_examples_$(date +%Y%m%d).log"
PY=/usr/bin/python3
[ -x "$PY" ] || PY="$(command -v python3)"
# 2026-11-22: 어제 하루 순위가 아직 없으면 먼저 받는다 (순위 수집기 실행 시각과 상관없이 그날 순위로 예시를 만들게)
RANK_DIR="${NAVER_DAILY_RANK_DIR:-$HOME/food_recommend/daily_food_rank}"
BACKFILL="$HOME/food_recommend/trend_pipeline/backfill_datalab_rank.py"
YESTERDAY="$(date -v-1d +%F 2>/dev/null || date -d yesterday +%F)"
{
  echo "== $(date '+%F %T') 시작 ($PY)"
  if [ -f "$BACKFILL" ] && [ ! -f "$RANK_DIR/food_$YESTERDAY.csv" ]; then
    echo "-- 어제($YESTERDAY) 하루 순위 받기"; "$PY" "$BACKFILL" --daily || echo "-- 하루 순위 받기 실패 (있는 자료로 계속)"
  fi
  "$PY" scripts/update_trend_examples.py
  # 2026-11-22: 올리기 전에 예시를 실제로 검색해 보고 엉뚱한 결과·메인에 맞지 않는 예시는 다음 후보로 (uv 필요)
  UV="$(command -v uv || echo "$HOME/.local/bin/uv")"
  if [ -x "$UV" ]; then
    "$UV" run python scripts/verify_trend_examples.py || echo "-- 검증 실패 또는 통과 3개 미만 (원래 예시 유지)"
  else
    echo "-- uv 없음: 예시 검증 건너뜀"
  fi
  echo "== 종료 exit=$?"
} >> "$LOG" 2>&1
