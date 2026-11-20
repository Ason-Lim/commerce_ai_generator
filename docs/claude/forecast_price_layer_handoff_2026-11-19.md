# 인계 — 예측 모델 가격 레이어: 시즌 가격·매수 시점·직구 비교 (2026-11-19 밤 23:22~)

프로젝트 사본 `claude/forecast_price_layer_handoff_2026-11-19.md`. 설계는 `keyword_forecast_research_2026-11-19.md` **§9**. 1단계(행사 선행 곡선) 인계는 `forecast_stage1_handoff_2026-11-19.md` — 그 커밋 명령 뒤에 이 작업을 이어서 커밋.
작업 폴더 `~/commerce_ai_generator_stage2`. 이번엔 맥 폴더를 직접 고쳤고(클로드 데스크톱 연결), 테스트는 **클라우드 사본에서 36개 통과**(새 22 + 기존 행사 14 — 맥 VM 은 디스크 부족으로 못 돌림).

## ★ 사용자가 할 일 (맥 터미널)
```bash
cd ~/commerce_ai_generator_stage2
uv run pytest tests/services/trends/test_forecast_prices.py tests/services/trends/test_forecast_overseas.py tests/admin/test_admin_trends_prices.py -q   # 22개
uv run python scripts/backfill_kamis_history.py --probe                         # 응답 형식·코드 확인 (평일 하루 식량작물 1건)
nohup uv run python scripts/backfill_kamis_history.py --start 2024-01-01 --end 2026-11-19 > var/backfill_kamis.log 2>&1 &   # 약 4,500 요청·80분, 이어받기 됨
tail -f var/backfill_kamis.log                                                   # 50건마다 진행 표시 · 연속 5번 실패면 스스로 멈춤(같은 명령으로 재개)
uv run python scripts/backfill_kamis_history.py --check                          # 끝난 뒤: 관측일·빠진 평일·성긴 품목
git add scripts/backfill_kamis_history.py app/services/trends/forecast/prices.py app/services/trends/forecast/overseas.py \
        app/admin/routes.py app/admin/web/trends.html \
        tests/services/trends/test_forecast_prices.py tests/services/trends/test_forecast_overseas.py tests/admin/test_admin_trends_prices.py \
        docs/claude/keyword_forecast_research_2026-11-19.md docs/claude/forecast_price_layer_handoff_2026-11-19.md
git add -f data/price_watchlist.csv data/price_drivers.csv data/driver_signals.csv     # data/ 는 .gitignore — 이 셋만 (history.csv·raw 는 넣지 않음)
git diff --cached --stat
git commit -m "예측 모델 가격 레이어: 감시 품목 37·동인 가설 29·KAMIS 백필 스크립트 + 시즌 가격·52주 위치·전년 전망·매수 시점 판정 + UCP 외화 상품 직구 견적(면세 한도·검역 차단·참고용) + /admin/trends 가격 전망 화면"
```
- **11-20 아침 첫 실행에서 전부 타임아웃**(맥, 10:31) → 같은 시각 VM 에선 2.6초 응답. KAMIS 가 아침 시세 갱신 시간대(10~11시)에 느려지는 것으로 보여 스크립트에 **재시도(3·10·30초)·타임아웃 40초·연속 5번 실패 시 멈춤·진행 로그 즉시 출력** 을 넣었고 VM 에서 13건 받아 `--build`·`--check` 까지 확인(`data/kamis/history/raw/01_1101/` 에 2024-01-01~03 남아 있음 — 이어받기 됨). 테스트 22개는 맥에서 통과.
- history.csv 는 품종·등급이 **열로 나뉘어** 옴(계란 kind 'XL30구'·rank '일반란', 한우 kind '등심'·rank '1등급') → `prices._kind_ok` 를 괄호 토큰 방식으로 바꿔 daily 파일('XL30구(일반란)')과 history 둘 다 맞게 함. 배추·무는 품종(봄·고랭지·가을·월동)을 잇는 한 줄 시세로(kamis_kind 비움).
- `var/claude_test_snapshot.tgz` 는 테스트용 임시 묶음 — 지워도 됨 (VM 에서 삭제 권한 없어 남김).
- 백필 전에는 화면이 거의 다 **'보류'**(52주 관측 6일 < 20) — 정상. 일별 파일 네 점만으로도 1년 대비는 보임: 11-19 기준 새우젓 +43%·한우 등심 +17%·오징어 +15% / 사과 −31%·배추 −23%(2024 폭등의 기저).
- 직구 견적을 실제로 보려면 `data/ucp/merchants.csv`(이 작업 트리엔 없음 — 원본 저장소 `data/ucp/merchants_template.csv` 참고)와 플랫폼 프로필(`UCP_PLATFORM_PROFILE_URL`), 환율(`FX_USD_KRW` 또는 질의 `fx_usd`)이 필요.

## 만든 것
| 파일 | 내용 |
|---|---|
| `data/price_watchlist.csv` | 감시 품목 37: item·group·kamis_item·kamis_kind·anchor_event(김장 시즌·추석·복날)·drivers·overseas(no/quote)·overseas_note(검역)·keywords(쿠팡 검색어)·note |
| `data/price_drivers.csv` | 동인 29 — 전부 **가설**. affects·direction·lag_days·signal_source·note |
| `data/driver_signals.csv` | 동인 켜짐/꺼짐 수동 입력 (지금 kimjang on 한 줄) |
| `scripts/backfill_kamis_history.py` | dailyPriceByCategoryList 로 부류 6 × 평일 수집 → `data/kamis/history/raw/` 원본 + `history.csv`. `--probe/--build/--check`, 이어받기, 1초/요청 |
| `app/services/trends/forecast/prices.py` | 시계열(history.csv, 없으면 daily 네 점)·`position`(52주 중간 순위 백분위)·`outlook`(해별 +7/14/28일)·`relative_curve`·`buy_timing`(지금/기다리기/분할/보류, 첫 값)·`active_drivers`·`item_report`·`summary` |
| `app/services/trends/forecast/overseas.py` | UCP 외화 옵션 추출·`quote`(환율·배송 추정·면세 150/200달러·관부가세·검역 차단·식품 참고 꼬리표)·`compare`(100g당) |
| `GET /admin/api/trends/forecast/prices?as_of=` | 전체 요약 + 자료 상태(백필 여부·일수) + 신호 + 임계값 |
| `GET /admin/api/trends/forecast/price?item=&as_of=&coupang=&ucp=&fx_usd=&fx_eur=&origin=` | 품목 리포트 + 국내 쿠팡 상품 + 직구 견적 + 비교 (ucp=1 이면 국내도 같이) |
| `trends.html` '가격 전망·매수 시점' | 표 + 상세(이유·1년 선·지평별 해별 전망·상대일 곡선·동인·상품 비교) |
| 테스트 | `test_forecast_prices.py` 11 · `test_forecast_overseas.py` 6 · `test_admin_trends_prices.py` 5 |

## 설계 메모
- 임계(하위/상위 30%, ±5%, 해 ≥2, 52주 관측 ≥20)는 첫 값. 백필 뒤 배추(2024 폭등)·계란(AI 겨울)·새우젓(김장) 사례로 다시 본다.
- 동인은 판정 수치에 안 들어간다 — 지연 일수(엘니뇨 90~360일, 사료→계란 30~90일 …)가 검증 전이라 가중치를 줄 수 없음. 백테스트에서 '동인 on 이었던 기간의 상승 적중'을 따로 센 뒤 결정.
- 직구: 추천 카드 경로(mapping.cards_from 원화만)와 분리. 견적은 모두 추정(estimate=True)이고 식품 구매대행 영업등록 확인 전엔 참고. cross_border(landed_cost) 근거 틀과 연결은 다음.
- GPT 지적 6항목(사용자 붙여 넣음 23:23)은 2차 검토 때 이미 코드·본문에 반영됨 — GPT 에 줄 파일은 인계가 아니라 연구 문서 최신본 + `events.py`.

## 다음
1. 백필 → `--check` → 화면에서 배추·새우젓·계란·쌀·사과 패턴 확인, 임계 재조정.
2. 환율 자동(한은 ECOS) + 동인 신호 수집기(환율→ENSO→곡물→AI→사료) → `driver_signals.csv` 자동 추가(사람 확인 뒤 on).
3. 가격 백테스트를 `forecast/backtest.py` 에 함께(순위 Q1 과 가격 방향·절약률).
4. UCP 등록부·프로필 둔 뒤 올리브유·커피로 실제 직구 견적 1회 확인 → 리포트·사이트 글에 '싸게 사는 시점 + 국내/직구 비교' 칸.
