#!/usr/bin/env bash
# 운영 서버를 launchd 로 (로그인하면 켜지고, 꺼지면 15초 뒤 다시 켜짐) — 맥미니 운영 전환 준비 (2026-11-26).
#   ./ops/launchd/install_api.sh            → 등록하고 켬 (지금 ./run_prod.sh 로 켜 둔 서버는 먼저 ./stop_api.sh 로 꺼 주세요)
#   ./ops/launchd/install_api.sh --rebuild  → git pull 뒤: 화면 빌드 → 다시 켬
#   ./ops/launchd/install_api.sh --remove   → 해제(서버 꺼짐)
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
LABEL=com.commerce_ai.api
DEST="$HOME/Library/LaunchAgents/$LABEL.plist"
if [ "${1:-}" = "--rebuild" ]; then
  (cd "$REPO/frontend" && { [ -d node_modules ] && [ ! package-lock.json -nt node_modules ] || npm ci; } && npm run build)
  launchctl kickstart -k "gui/$(id -u)/$LABEL" && echo "화면을 빌드하고 서버를 다시 켰어요." && exit 0
fi
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
if [ "${1:-}" = "--remove" ]; then
  rm -f "$DEST"; echo "해제했어요(서버 꺼짐)."; exit 0
fi
if lsof -nP -iTCP:"${API_PORT:-8001}" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "포트 ${API_PORT:-8001} 에 이미 서버가 있어요 — ./stop_api.sh 로 끈 뒤 다시 실행해 주세요."; exit 1
fi
mkdir -p "$HOME/Library/LaunchAgents" "$REPO/var/log"
sed -e "s#__REPO__#$REPO#g" -e "s#__HOME__#$HOME#g" "$REPO/ops/launchd/$LABEL.plist" > "$DEST"
plutil -lint "$DEST" >/dev/null
launchctl bootstrap "gui/$(id -u)" "$DEST"
echo "등록했어요: 운영 서버가 지금 켜지고, 로그인할 때마다 켜져요(꺼지면 다시 켬)."
echo "기록: $REPO/var/log/api.launchd.log · 상태: launchctl print gui/$(id -u)/$LABEL | grep state"
