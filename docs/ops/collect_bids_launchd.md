# 입찰 공고 매일 자동 수집 (맥 launchd) — 2026-11-25

B2B 콘솔 '입찰 트렌드'는 저장된 공고로만 집계합니다. 수집을 돌리지 않으면 공고가 멈춰 있습니다
(11-25 확인: 마지막 공고 10-29, '최종 추출 기록 없음'). 맥이 매일 **새벽 4시**에 나라장터 공고를 모읍니다.

## 처음 한 번 (맥 터미널)
```
cd ~/commerce_ai_generator
git pull && uv sync
./ops/launchd/install_collect_bids.sh --now
```
- `--now`: 등록하면서 **지금 30일치를 한 번** 수집해 밀린 공고(10-29 이후)를 채웁니다. 몇 분 걸릴 수 있어요.
- 끝에 `신규 N건 / 조회 M건`이 보이면 성공입니다. B2B 콘솔 '입찰 트렌드'에서 '최종 추출' 시각이 바뀝니다.

## 그 뒤로
- 매일 04:00 최근 3일을 수집합니다(겹쳐도 같은 공고는 한 번만 저장).
- 맥이 4시에 잠들어 있었으면 **깨어난 뒤 한 번** 돌아요. 꺼져 있었던 날이 길면 아래 '밀린 기간 채우기'.
- 실패하면 맥 알림 '입찰 공고 수집 실패'가 뜹니다.

## 확인·관리
| 하고 싶은 것 | 명령 |
|---|---|
| 기록 보기 | `tail -n 20 var/log/collect_bids.log` |
| 마지막 결과 (시각 · 종료 코드 0=성공) | `cat var/log/collect_bids.status` |
| 지금 한 번 돌리기 | `bash scripts/run_collect_bids.sh` |
| 밀린 기간 채우기 (예: 30일) | `COLLECT_DAYS=30 bash scripts/run_collect_bids.sh` |
| 등록 상태 보기 | `launchctl print gui/$(id -u)/com.commerce_ai.collect_bids \| grep state` |
| 시각 바꾸기 | `ops/launchd/com.commerce_ai.collect_bids.plist`의 Hour·Minute 수정 → `./ops/launchd/install_collect_bids.sh` 다시 실행 |
| 끄기 | `./ops/launchd/install_collect_bids.sh --remove` |

## 실패할 때
- **`.venv 가 없어요`** → `uv sync`
- **나라장터 키 오류** → `.env`의 `G2B_SERVICE_KEY` 확인 (공공데이터포털 '조달청_나라장터 입찰공고정보서비스' 활용신청 키)
- **인터넷 연결 오류** → 다음 날 자동으로 다시 돌아요. 바로 채우려면 '지금 한 번 돌리기'
- 같은 시각대의 다른 예약 작업: 04:20 보존 기간 작업 — 서로 영향 없음

## 수집 범위
- 나라장터 OpenAPI: 물품·용역 공고, 선물·상품권 관련 검색어 (scripts/admin/collect_bids.py · collectors.py)
- `B2B_BID_SOURCE_URL`이 있으면 smallbiz-monitor 공고도 함께(지금은 비어 있음)
- 수집한 공고는 '원문 대조 전'으로 저장 — 입찰 전 원문 확인은 그대로 사람이
