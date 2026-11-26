# 맥미니 운영 전환 안내 (2026-11-26)

지금 운영 서버는 맥북(:8001 → Cloudflare 터널 → app.trendguide.kr)입니다. 맥미니로 옮길 때 이 순서대로 합니다.
같은 데이터를 두 컴퓨터가 동시에 내보내지 않게, **맥북을 끈 뒤 맥미니를 켜는 것**이 핵심입니다.

## 0. 미리 준비 (전환 전날까지)
| 할 일 | 왜 |
|---|---|
| **고정 IP 유선 회선** 연결 | 네이버 커머스API 는 등록한 호출 IP 에서만 응답 — 휴대폰 데이터망은 IP 가 자주 바뀜 |
| 맥미니 macOS 업데이트, 시간대 서울, 관리자 계정 로그인 자동화(시스템 설정 → 사용자 → 자동 로그인) | launchd 작업은 로그인한 사용자로 돈다 |
| `sudo pmset -a sleep 0 disksleep 0 autorestart 1 womp 1` | 잠자기 없음 · 정전 뒤 자동 켜짐 · 네트워크로 깨우기 |
| `brew install git uv node sqlite cloudflared tesseract tesseract-lang` | 서버·빌드·백업·터널·상세 이미지 글자 읽기 |
| 맥미니에서 `git clone https://github.com/Ason-Lim/commerce_ai_generator.git ~/commerce_ai_generator` → `cd ~/commerce_ai_generator && uv sync && (cd frontend && npm ci && npm run build)` | 코드·패키지·화면 |
| 네이버 커머스API센터 → 애플리케이션 → **API 호출 IP 에 맥미니 고정 IP 추가** (맥북 IP 는 전환 뒤 지움) | 스마트스토어 가져오기 |

## 1. 옮기기 (서버가 잠깐 멈춤 — 손님이 적은 새벽 권장)
맥북에서:
```bash
cd ~/commerce_ai_generator
./stop_api.sh                       # 운영 서버 끄기 (launchd 로 켰다면 ./ops/launchd/install_api.sh --remove)
bash scripts/backup_data.sh         # 마지막 백업 (~/commerce_ai_backups/날짜)
```
맥북 → 맥미니로 **같이 옮길 것** (외장 디스크·AirDrop·같은 망 rsync — 메신저·메일 금지):
- `.env`
- **암호화 키** `data/admin/corpmall.key` (`.env` 에 `CORPMALL_KEY` 가 없을 때) — 없으면 셀러 연락처·입점 서류·폐쇄몰 명단을 못 읽음
- 측정 키 `var/measure/measure.key`
- 데이터 폴더 `data/` · `var/` 통째로 (또는 방금 만든 백업 폴더를 맥미니 저장소 위치에 풀기)
- 맥북 `~/food_recommend/daily_food_rank` 같이 `.env` 가 가리키는 바깥 폴더(예: `NAVER_DAILY_RANK_DIR`) — 맥미니 경로에 맞게 `.env` 고치기

같은 망 rsync 예 (맥미니에서 '원격 로그인' 켠 뒤, 맥북에서):
```bash
rsync -a --exclude node_modules --exclude .venv --exclude frontend/dist \
  ~/commerce_ai_generator/{.env,data,var} 맥미니사용자@맥미니.local:~/commerce_ai_generator/
```

## 2. 맥미니에서 켜기
```bash
cd ~/commerce_ai_generator
./ops/launchd/install_api.sh        # 운영 서버: 지금 켜고, 로그인할 때마다·꺼지면 다시 켬
./ops/launchd/install_backup.sh     # 매일 03:20 백업
./ops/launchd/install_collect_bids.sh  # 04:00 입찰 수집 (그 밖의 install_*.sh 도 맥북과 같게)
./ops/launchd/install_dataset_daily.sh; ./ops/launchd/install_privacy_retention.sh
./ops/launchd/install_warm_food.sh; ./ops/launchd/install_weekly_improve.sh
```
맥북의 예약 작업은 끕니다(같은 일을 두 번 하지 않게): 맥북에서 각 `install_*.sh --remove`.

## 3. 터널 옮기기
Cloudflare 대시보드 → Zero Trust → Networks → Tunnels → 지금 터널 → **맥북 커넥터를 먼저 멈추고**(맥북에서 `sudo cloudflared service uninstall` 또는 실행 중인 `cloudflared` 끄기)
→ 같은 터널의 '커넥터 설치' 명령(토큰)을 맥미니에서 실행: `sudo cloudflared service install <토큰>`.
- 공개 주소(app.trendguide.kr → http://localhost:8001)는 터널 설정이라 그대로.
- 두 컴퓨터의 커넥터가 동시에 켜져 있으면 요청이 나뉘어 들어가요 — 반드시 하나만.

## 4. 확인
```bash
EXPECTED_PUBLIC_IP=고정IP bash scripts/check_server_ready.sh   # ✘ 가 0 이어야 함
bash scripts/run_load_test.sh                                 # 부하 시험 (시험 서버 :8011, 쿠팡 끔)
bash var/stage1_close_check.sh main                           # 순위 63/63 · 화면 11/11
```
그리고 브라우저로: app.trendguide.kr 홈 · 대화 한 번 · /admin 로그인 · /seller 테스트 셀러센터 열기(관리자 › 셀러 › 미니숍 실험실) · 스마트스토어 미리보기(커머스API IP 확인).

## 5. 되돌리기 (문제가 있으면)
맥미니: `./ops/launchd/install_api.sh --remove` · `sudo cloudflared service uninstall` →
맥북: `./run_prod.sh` · 맥북 커넥터 다시 켜기. 맥미니에서 새로 쌓인 자료는 그 사이 것만 — 오래 걸렸다면 맥미니 백업을 맥북으로 되돌려 옮깁니다.

## 기준 (오픈 판단 초안)
- 부하 시험 동시 20 에서 p95 < 1,000ms · 오류 0 (2026-11-26 리눅스 2코어 기준: 동시 20 p95 최대 102ms · 동시 100 p95 최대 436ms · 오류 0)
- 점검 스크립트 ✘ 0, 매일 백업 26시간 안
