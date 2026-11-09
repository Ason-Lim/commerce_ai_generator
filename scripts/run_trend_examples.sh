#!/bin/bash
# 매일 10:00 launchd 실행: 홈 화면 예시 질문 JSON 생성 (표준 라이브러리만 쓰므로 파이썬 버전 변경과 무관)
# 2026-11-04 integrated_system 에서 옮김 → frontend/src/data 에 저장, 화면은 /api/trend-examples 로 그날 파일을 읽는다
cd "$(dirname "$0")/.." || exit 1
mkdir -p var/logs
LOG="var/logs/trend_examples_$(date +%Y%m%d).log"
PY=/usr/bin/python3
[ -x "$PY" ] || PY="$(command -v python3)"
{ echo "== $(date '+%F %T') 시작 ($PY)"; "$PY" scripts/update_trend_examples.py; echo "== 종료 exit=$?"; } >> "$LOG" 2>&1
