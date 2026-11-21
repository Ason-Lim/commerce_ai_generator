#!/usr/bin/env bash
# 매일 새벽 4시 40분 '학습 데이터셋 승격·정리'를 launchd 에 등록 (다시 실행하면 새 설정으로 바꿔 등록).
#   ./ops/launchd/install_dataset_daily.sh            → 등록
#   ./ops/launchd/install_dataset_daily.sh --remove   → 해제
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
LABEL=com.commerce_ai.dataset_daily
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
echo "등록했어요: 매일 04:40 — $REPO/scripts/run_dataset_daily.sh"
echo "기록: $REPO/var/log/dataset_daily.log"
launchctl print "gui/$(id -u)/$LABEL" | grep -E "state|path" | head -3 || true
