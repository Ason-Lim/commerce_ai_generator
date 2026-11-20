# 인계 — 예측 모델 1단계: 행사 달력 + 선행 곡선 탐색기 (2026-11-19 밤 22:30~)

프로젝트 사본 `claude/forecast_stage1_handoff_2026-11-19.md`. 함께 보기: `keyword_forecast_research_2026-11-19.md` §7-2(GPT 반영)·§8(뉴스), `period_backfill_handoff_2026-11-19.md`.
작업 폴더: `~/commerce_ai_generator_stage2` (브랜치 `ext/bc-to-registry`, 기간 조회 c6632c3 위). VM 에서 git 커밋이 안 되어(삭제 권한) **커밋은 맥에서** — 아래 명령.

## ★ 사용자가 할 일 (맥 터미널)
```bash
cd ~/food_recommend && python3 trend_pipeline/backfill_datalab_rank.py --check     # 백필 품질 먼저 ("문제 0개, 빠진 날 0개")
cd ~/commerce_ai_generator_stage2
uv run pytest tests/services/trends/test_forecast_events.py tests/admin/test_admin_trends_forecast.py -q   # 10 + 4개
git status --short                                                                   # 이번 작업 파일만 아래에 — 다른 변경이 섞였으면 빼기
git add -f data/event_calendar.csv data/past_incidents.csv      # data/ 는 .gitignore — 이 두 파일만 강제 추가
git add scripts/build_event_calendar.py \
        app/services/trends/forecast/__init__.py app/services/trends/forecast/calendar.py app/services/trends/forecast/events.py \
        app/admin/routes.py app/admin/web/trends.html \
        tests/services/trends/test_forecast_events.py tests/admin/test_admin_trends_forecast.py \
        docs/claude/keyword_forecast_research_2026-11-19.md docs/claude/forecast_stage1_handoff_2026-11-19.md
git diff --cached --stat                                                             # routes.py·trends.html 에 다른 변경이 없는지 확인
git commit -m "예측 모델 1단계: 행사 달력 csv(2024~2027, 검증 상태 열) + 행사 선행 곡선 탐색기(반복/후보 판정·as_of·행사군·네이버/쿠팡 준비 상태) + 연구 문서 GPT 1·2차 검토·뉴스 API 반영"
```
- 백필이 끝난 뒤 `/admin/trends` → **행사 선행 곡선** 에서 빼빼로데이·수능·추석·복날(초복~말복)을 골라 보면 과거 패턴이 보인다. 23:07 기준 백필은 2024-04-12 까지(1초/요청, 아침에 끝남).
- 판정 가능한 해가 2024·2025 둘이어야 '반복', 하나면 '후보'. 기준일(기본 오늘) 뒤 자료는 읽지 않으므로 2026 빼빼로데이는 11-25 이후에야 판정에 들어간다.
- **이 화면은 과거 패턴 탐색기** — 예측 성능·사업 효과는 아직 검증되지 않았다 (GPT 2차). 다음 단계 백테스트에서 잰다.

## 만든 것
| 파일 | 내용 |
|---|---|
| `scripts/build_event_calendar.py` | 달력 생성기. 고정일 21종, 음력 5종(korean_lunar_calendar, 설·추석은 연휴 시작/끝 행도), 24절기(태양 황경 Meeus 저정밀, KST), 복날(하지·입추 뒤 경일 — 2024-07-15 경일 기준 10일 주기), 수능(11월 셋째 주 목요일), 성년의날, 기간 행사 8종('대략'). **KNOWN 21건 대조** 통과해야 저장. 열 `source`·`verification_status`(official/fixed/computed/approx)·`verified_at` |
| `data/event_calendar.csv` | 268행 2024~2027. official 21 · fixed 84 · computed 131 · approx 32. 2027 수능만 '예정'. **computed(2026·2027 절기·복날·음력)는 기상청·천문연 발표와 대조 필요** |
| `data/past_incidents.csv` | 2024·2025 돌발 사건 9건. confidence '확인/대략' — 대략 건은 기상청 특보 자료로 교정 필요 |
| `app/services/trends/forecast/calendar.py` | 달력 읽기: `events()`, `occurrences(name)`, `upcoming(today, days)`, `incidents()` |
| `app/services/trends/forecast/events.py` | **선행 곡선 탐색기**. 상태 셋(순위 / 'out'=순위 밖으로 사용 / None=누락 제외). 판정: 기준(−35…−29) 대체로 100위 밖 → 진입(−28…행사 끝) 100위 안 → 이탈(끝+3…+14) 대체로 100위 밖, 구간별 최소 관측일 4·20·8. 등급 **반복**(판정 가능 해 ≥2 모두 만족) / **후보** / **씨앗**. `as_of` 로 기준일 뒤 자료 차단. 정점 peak_best(최고 순위 연속)·peak_top(20위 안 연속). `GROUPS` 행사군(복날·설/추석 연휴). `forecast_from_report` → 예보 재료 |
| `GET /admin/api/trends/forecast/events` | 행사 목록(행사군 포함) + 다가오는 행사(D-day) + 자료 있는 연도 |
| `GET /admin/api/trends/forecast/event?event=&years=&as_of=&seeds=&coupang=` | 리포트 + `next`(다음 행사·예보 재료) + **네이버 등록부 링크 유무 + 쿠팡 파트너스 상품 후보 수**(coupang=1, 쿠팡 호출) |
| `trends.html` '행사 선행 곡선' | 행사·씨앗·기준일 입력, '쿠팡 상품 확인' 버튼, 해마다 상대일 곡선(−35…+14, 행사 시작·끝 점선), 등급·선행일·최고 순위 구간(+20위 안 구간)·해별 판정(만족/아님/자료 부족 + 이유)·예보 재료·네이버 링크·쿠팡 상품. 줄 클릭 → 키워드 관심 이력 |
| 테스트 | `tests/services/trends/test_forecast_events.py` **10개**(VM 통과: 상태 셋·2개 해 규칙·정점 구간·as_of·자료 부족·복날 행사군·예보 재료), `tests/admin/test_admin_trends_forecast.py` **4개**(맥에서 실행 — VM 디스크 부족) |

## 설계 메모
- '대체로(100위 안 관측일 ≤1/3)'와 최소 관측일 4·20·8, 20위 기준은 **첫 값** — 실제 자료에서 빼빼로(11-13 26위)·삼계탕 같은 사례로 다시 본다.
- 쿠팡: 예보 키워드의 파트너스 상품 후보는 `_coupang_links`(주류 제외, 제휴 링크만) 재사용. 다음 단계에서 쿠팡용 사이트 글 초안을 예보에서 만들어 `/admin/trend-posts` 대기열에 넣는다(사용자 2026-11-19 23:08).
- 음력 패키지는 생성 스크립트에만 필요(pyproject 에 넣지 않음, csv 를 저장소에 둠). 2028 이후 연도는 `YEARS` 에 더하고 다시 실행.
- 24절기 계산은 저정밀(분 단위 오차)이라 경계일(자정 ±수분)에서 하루 어긋날 수 있음 — KNOWN 대조로 2024·2025 는 확인, 2026·2027 은 기상청·천문연 발표와 한 번 맞춰 볼 것.

## 다음 (연구 §6, GPT 2차 순서)
1. 백필 품질 확인(`--check`) → 실제 자료로 빼빼로·수능·추석·복날 패턴 확인, 임계 재조정.
2. API 테스트 4개 맥에서 실행.
3. 기준선 3종(최근 유지·전년 반복·행사 상대일) + 백테스트 틀 `forecast/backtest.py` — as_of 기준, Q1 정의, §4 지표 7종. 탐색기 화면이 잘 나오는 것과 예측 성능은 별도로 판정.
4. 시즌 비교(작년 같은 주) 칸 → 태그 규칙표 → 리포트 생성기 + 쿠팡용 사이트 글 초안 연동 → (별도 단계) 뉴스 수집·광고 필터(§8).
