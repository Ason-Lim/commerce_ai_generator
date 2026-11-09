#!/bin/bash
# 매일 오전 10시 홈 화면 예시 질문 생성 예약 등록 (한 번만 실행) — 2026-11-04 commerce_ai_generator 로 옮김
# 옛 예약(kr.integrated.trendexamples, integrated_system/ui_ux 에 저장)은 끄고 새 예약으로 바꾼다.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LABEL=kr.commerceai.trendexamples
OLD=kr.integrated.trendexamples
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
OLD_PLIST="$HOME/Library/LaunchAgents/$OLD.plist"
if [ -f "$OLD_PLIST" ]; then
  launchctl bootout "gui/$(id -u)" "$OLD_PLIST" 2>/dev/null || true
  mv "$OLD_PLIST" "$OLD_PLIST.disabled"
  echo "옛 예약 끔: $OLD (파일은 $OLD_PLIST.disabled 로 남김)"
fi
chmod +x "$ROOT/scripts/run_trend_examples.sh"
mkdir -p "$HOME/Library/LaunchAgents" "$ROOT/var/logs"
cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key><array><string>/bin/bash</string><string>$ROOT/scripts/run_trend_examples.sh</string></array>
  <key>StartCalendarInterval</key><dict><key>Hour</key><integer>10</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardOutPath</key><string>$ROOT/var/logs/trend_examples_launchd.out</string>
  <key>StandardErrorPath</key><string>$ROOT/var/logs/trend_examples_launchd.err</string>
</dict></plist>
PL
launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "등록 완료: 매일 10:00 → $ROOT/frontend/src/data/trend_examples_YYYY-MM-DD.json"
echo "시험 실행 중..."
launchctl kickstart -k "gui/$(id -u)/$LABEL"; sleep 3
tail -3 "$ROOT/var/logs/trend_examples_$(date +%Y%m%d).log"
