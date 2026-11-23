#!/usr/bin/env bash
# 매주 일요일 23:30 '주간 개선 지표'를 launchd 에 등록 (다시 실행하면 새 설정으로 바꿔 등록).
#   ./ops/launchd/install_weekly_improve.sh            → 등록
#   ./ops/launchd/install_weekly_improve.sh --remove   → 해제
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
LABEL=com.commerce_ai.weekly_improve
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
echo "등록했어요: 매주 일요일 23:30 — $REPO/scripts/run_weekly_improve.sh"
echo "기록: $REPO/var/log/weekly_improve.log"
launchctl print "gui/$(id -u)/$LABEL" | grep -E "state|path" | head -3 || true
