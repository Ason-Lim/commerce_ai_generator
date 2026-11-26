#!/usr/bin/env bash
# 매일 03:20 데이터 백업을 launchd 에 등록 (다시 실행하면 새 설정으로 바꿔 등록).
#   ./ops/launchd/install_backup.sh            → 등록
#   ./ops/launchd/install_backup.sh --remove   → 해제
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
LABEL=com.commerce_ai.backup
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
echo "등록했어요: 매일 03:20 — $REPO/scripts/backup_data.sh (백업 위치 ~/commerce_ai_backups)"
echo "기록: $REPO/var/log/backup.launchd.log"
launchctl print "gui/$(id -u)/$LABEL" | grep -E "state|path" | head -3 || true
