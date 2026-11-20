#!/bin/bash
# 1단계 마무리 확인 (2026-11-16) — Mac 에서 실행: bash var/stage1_close_check.sh [브랜치이름표]
# DB(localhost:5432)를 읽기 전용으로 써서 순위·표시 스냅샷을 찍고 s8·d8 과 비교, R0 집계, 쿠팡 채널 ID 링크 확인
set -u
cd "$(dirname "$0")/.."
TAG=${1:-close}
echo "== HEAD: $(git rev-parse --short HEAD) ($(git branch --show-current))"
uv run python scripts/stage1_ranking_snapshot.py capture "s9_$TAG" >/dev/null && \
uv run python scripts/stage1_ranking_snapshot.py compare s8 "s9_$TAG" >/dev/null
uv run python scripts/stage1_display_snapshot.py capture "d9_$TAG" >/dev/null && \
uv run python scripts/stage1_display_snapshot.py compare d8 "d9_$TAG" >/dev/null
echo "== 순위 s8 → s9_$TAG";  grep -E "^- 같음" "docs/claude/stage1_ranking_compare_s8_vs_s9_$TAG.md"
echo "== 화면 d8 → d9_$TAG";  grep -E "^- 순서" "docs/claude/stage1_display_d8_vs_d9_$TAG.md"
if [ "$TAG" = close ]; then
  echo "== R0";  uv run python scripts/r0_path_click_report.py >/dev/null; sed -n '/추천 경로/,/행동 신호/p' "$(ls -t docs/claude/r0_path_click_report_*.md | head -1)" | head -30
  echo "== 쿠팡 채널 ID"; uv run python scripts/check_coupang_subid.py 사과 | sed -E 's/(subId=)[^&]*/\1(값 있음)/'
fi
