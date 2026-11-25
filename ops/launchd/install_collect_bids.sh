#!/usr/bin/env bash
# 매일 새벽 4시 '나라장터 입찰 공고 수집'을 launchd 에 등록 (다시 실행하면 새 설정으로 바꿔 등록).
#   ./ops/launchd/install_collect_bids.sh            → 등록
#   ./ops/launchd/install_collect_bids.sh --now      → 등록 + 지금 한 번 30일치 수집 (밀린 공고 채우기)
#   ./ops/launchd/install_collect_bids.sh --remove   → 해제
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
LABEL=com.commerce_ai.collect_bids
DEST="$HOME/Library/LaunchAgents/$LABEL.plist"
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
if [ "${1:-}" = "--remove" ]; then
  rm -f "$DEST"
  echo "해제했어요."
  exit 0
fi
mkdir -p "$HOME/Library/LaunchAgents" "$REPO/var/log"
sed "s#__REPO__#$REPO#g" "$REPO/ops/launchd/$LABEL.plist" > "$DEST"
plutil -lint "$DEST" >/dev/null
launchctl bootstrap "gui/$(id -u)" "$DEST"
echo "등록했어요: 매일 04:00 — 최근 3일 공고 수집 (맥이 잠들어 있었으면 깨어난 뒤 한 번)"
echo "기록: $REPO/var/log/collect_bids.log"
launchctl print "gui/$(id -u)/$LABEL" | grep -E "state|path" | head -3 || true
if [ "${1:-}" = "--now" ]; then
  echo "지금 30일치를 한 번 수집해요…"
  COLLECT_DAYS=30 /bin/bash "$REPO/scripts/run_collect_bids.sh"
  tail -n 6 "$REPO/var/log/collect_bids.log"
fi
