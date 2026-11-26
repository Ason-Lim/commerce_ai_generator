#!/usr/bin/env bash
# 운영 서버 준비 점검 (맥미니 운영 전환, 2026-11-26) — 맥북·맥미니 어디서나 읽기만 한다. 키 값은 보여 주지 않는다(있는지만).
#   bash scripts/check_server_ready.sh                       → 항목마다 ✔ / ✘ / ! (주의)
#   EXPECTED_PUBLIC_IP=1.2.3.4 bash scripts/check_server_ready.sh   → 고정 IP 와 같은지도 확인
set -uo pipefail
cd "$(dirname "$0")/.."
BAD=0; WARN=0
ok(){ printf '✔ %s\n' "$1"; }
no(){ printf '✘ %s\n' "$1"; BAD=$((BAD + 1)); }
warn(){ printf '! %s\n' "$1"; WARN=$((WARN + 1)); }
has(){ command -v "$1" >/dev/null 2>&1; }

echo "── 이 컴퓨터"
echo "  $(sw_vers -productName 2>/dev/null) $(sw_vers -productVersion 2>/dev/null) · $(uname -m) · $(sysctl -n hw.memsize 2>/dev/null | awk '{printf "%.0fGB", $1/1073741824}')"
[ "$(readlink /etc/localtime 2>/dev/null | sed 's#.*zoneinfo/##')" = "Asia/Seoul" ] && ok "시간대 Asia/Seoul" || warn "시간대가 Asia/Seoul 이 아니에요 (예약 작업 시각이 어긋남)"
FREE_GB=$(df -g . 2>/dev/null | awk 'NR==2{print $4}')
[ -n "$FREE_GB" ] && { [ "$FREE_GB" -ge 20 ] && ok "남은 디스크 ${FREE_GB}GB" || warn "남은 디스크 ${FREE_GB}GB (20GB 이상 권장)"; }

echo "── 잠자기·정전"
SLEEP=$(pmset -g 2>/dev/null | awk '$1=="sleep"{print $2}')
[ "${SLEEP:-1}" = "0" ] && ok "시스템 잠자기 꺼짐" || no "시스템 잠자기 ${SLEEP:-?}분 — sudo pmset -a sleep 0 (서버가 멈춤)"
[ "$(pmset -g 2>/dev/null | awk '$1=="autorestart"{print $2}')" = "1" ] && ok "정전 뒤 자동 켜짐" || warn "정전 뒤 자동 켜짐 꺼짐 — sudo pmset -a autorestart 1"
[ "$(pmset -g 2>/dev/null | awk '$1=="womp"{print $2}')" = "1" ] && ok "네트워크로 깨우기 켜짐" || warn "네트워크로 깨우기 꺼짐 — sudo pmset -a womp 1"

echo "── 프로그램"
for t in git uv node npm sqlite3 cloudflared; do has "$t" && ok "$t" || no "$t 없음 — brew install $t"; done
if has tesseract; then
  tesseract --list-langs 2>/dev/null | grep -qx kor && ok "tesseract + 한국어" || no "tesseract 한국어 없음 — brew install tesseract-lang"
else no "tesseract 없음 — brew install tesseract tesseract-lang"; fi

echo "── 저장소·설정"
[ -f .env ] && ok ".env 있음" || no ".env 없음 — 기존 서버에서 안전하게 옮겨 주세요(메신저·메일 금지)"
for k in ADMIN_ACCESS_TOKEN CORPMALL_KEY PRIVACY_PSEUDO_KEY ANTHROPIC_API_KEY OPENAI_API_KEY COUPANG_ACCESS_KEY COUPANG_SECRET_KEY \
         KAMIS_API_KEY KAMIS_CERT_ID NTS_SERVICE_KEY NAVER_CLIENT_ID NAVER_COMMERCE_CLIENT_ID; do
  grep -qE "^$k=.+" .env 2>/dev/null && ok "키 $k" || { [ "$k" = CORPMALL_KEY ] && [ -f data/admin/corpmall.key ] && ok "키 $k (data/admin/corpmall.key)" || warn "키 $k 없음"; }
done
# 암호화 키 파일 — 없으면 셀러 연락처·서류·폐쇄몰 명단 등 암호화된 칸을 못 읽는다. 반드시 옛 서버에서 함께 옮긴다.
grep -qE "^CORPMALL_KEY=.+" .env 2>/dev/null || [ -f data/admin/corpmall.key ] || no "암호화 키(CORPMALL_KEY 또는 data/admin/corpmall.key) 없음 — 옛 서버에서 옮겨야 암호화된 자료를 읽어요"
[ -f var/measure/measure.key ] && ok "측정 키 var/measure/measure.key" || warn "측정 키 없음(새로 만들어지면 전날과 같은 방문을 잇지 못함 — 옛 서버에서 옮기기)"
[ -d frontend/dist ] && ok "화면 빌드 있음 (frontend/dist)" || no "화면 빌드 없음 — ./run_prod.sh 또는 ./ops/launchd/install_api.sh --rebuild"
git fetch -q origin main 2>/dev/null && { [ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" ] && ok "main 최신 ($(git rev-parse --short HEAD))" || warn "main 과 다름 — git pull"; }
[ -z "$(git status --porcelain --untracked-files=no 2>/dev/null)" ] && ok "고친 채 남은 파일 없음" || warn "커밋 안 된 수정이 있어요: git status"
N_DB=$(find data var -name '*.sqlite3' 2>/dev/null | wc -l | tr -d ' ')
ok "DB 파일 ${N_DB}개 (data·var)"

echo "── 예약 작업 (launchd)"
for p in ops/launchd/com.commerce_ai.*.plist; do
  L=$(basename "$p" .plist)
  launchctl print "gui/$(id -u)/$L" >/dev/null 2>&1 && ok "$L" || warn "$L 등록 안 됨 — ops/launchd/install_*.sh"
done

echo "── 서버·공개 주소"
CODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 http://127.0.0.1:${API_PORT:-8001}/ || true)
[ "$CODE" = "200" ] && ok "운영 서버 :${API_PORT:-8001} 응답" || no "운영 서버 :${API_PORT:-8001} 응답 없음 ($CODE)"
pgrep -x cloudflared >/dev/null && ok "Cloudflare 터널 실행 중" || no "Cloudflare 터널 꺼짐 — sudo cloudflared service install 또는 cloudflared tunnel run"
PUB=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 https://app.trendguide.kr/ || true)
[ "$PUB" = "200" ] && ok "https://app.trendguide.kr 응답" || warn "https://app.trendguide.kr 응답 $PUB (터널이 다른 컴퓨터를 가리킬 수 있음)"
IP=$(curl -s --max-time 5 https://api.ipify.org || true)
if [ -n "${EXPECTED_PUBLIC_IP:-}" ]; then
  [ "$IP" = "$EXPECTED_PUBLIC_IP" ] && ok "공인 IP $IP = 고정 IP" || no "공인 IP $IP ≠ 고정 IP $EXPECTED_PUBLIC_IP (커머스API 호출 IP 가 막힘)"
else
  warn "공인 IP $IP — 네이버 커머스API '호출 IP'에 이 값을 등록 (고정 IP 회선이면 EXPECTED_PUBLIC_IP 로 확인)"
fi

echo "── 백업"
LAST=$(ls -1d "${BACKUP_DIR:-$HOME/commerce_ai_backups}"/20* 2>/dev/null | tail -1)
if [ -n "$LAST" ]; then
  AGE=$(( ( $(date +%s) - $(stat -f %m "$LAST") ) / 3600 ))
  [ "$AGE" -le 26 ] && ok "최근 백업 ${AGE}시간 전 ($LAST)" || warn "최근 백업 ${AGE}시간 전 — bash scripts/backup_data.sh"
else no "백업 없음 — bash scripts/backup_data.sh, 매일: ./ops/launchd/install_backup.sh"; fi

echo
echo "결과: 문제 $BAD · 주의 $WARN"
exit $BAD
