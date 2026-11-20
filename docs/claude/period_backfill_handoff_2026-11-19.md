# 인계 — 급상승 키워드 기간 조회 개발 + 하루 단위 순위 백필 (2026-11-19 밤, 창 4 이어서)

이 문서는 claude.ai 프로젝트 'commerce_ai 추천 시스템'의 claude/period_backfill_handoff_2026-11-19.md. 저장소 사본 `docs/claude/`.
함께 보기: `claude/trend_report_blog_research_2026-11-19.md`(리포트·블로그 연구), `claude/trend_period_report_design_2026-11-19.md`(오후 설계), GPT 검토(사용자 첨부, 반영함).

## ★ 사용자가 할 일
1. **백필 시작** (맥 터미널, 약 7~10시간 — 밤새):
   ```bash
   cd ~/food_recommend
   nohup python3 trend_pipeline/backfill_datalab_rank.py > /tmp/backfill.log 2>&1 &
   tail -f /tmp/backfill.log
   ```
   - 2024-01-01~어제를 `~/food_recommend/daily_food_rank/food_YYYY-MM-DD.csv` 에 **하루 단위 상위 500**으로 저장. 이미 받아 검증된 날은 건너뜀(끊기면 다시 실행).
   - 확인: `python3 trend_pipeline/backfill_datalab_rank.py --check` → "문제 0개, 빠진 날 0개"면 끝.
   - 1초/요청(하루 25요청). `--pause 0.7` 로 조금 빠르게 가능하나 429 가 잦아지면 자동으로 60초↑ 쉼.
2. 백필이 어느 정도 차면 **운영 `.env`** 에 한 줄: `NAVER_DAILY_RANK_DIR=/Users/mom/food_recommend/daily_food_rank` (기존 `NAVER_DAILY_DIR` 는 그대로 둠). 화면의 빨간 주의 문구가 사라짐.
3. 매일 수집 교체: cron/런처의 `collect_datalab_popular.py` 대신 `python3 trend_pipeline/backfill_datalab_rank.py --daily` (어제 하루). 기존 수집기는 7-09부터 '30일 묶음' 순위를 저장하고 있었음.
4. 브랜치 `ext/bc-to-registry` 커밋 `c6632c3` **push·PR** (앞 커밋 3개와 함께). PR 제목 제안: "급상승 키워드 기간 조회 · 키워드 관심 이력 (하루 단위 순위 폴더 NAVER_DAILY_RANK_DIR)".
5. 병합 뒤 운영 pull → `/admin/trends` '기간별 식품 키워드 순위 변화' 확인.

## 한 것
- **데이터 점검** (GPT 검토 5-1): `daily_food_data` 214개 파일(4-15~11-19, 219일 중 5일 누락: 10-14·10-15·10-18·10-24·11-09), 중복 키워드 파일 13개(11-08은 400위까지). **4-15~7-08 = 하루 순위, 7-09~ = 최근 30일 묶음 순위**(8-08·9-02·10-10 제외) — 데이터랩 서버 응답과 상위 20 비교로 확인.
- **백필 스크립트** `~/food_recommend/trend_pipeline/backfill_datalab_rank.py` (표준 라이브러리, 서버 주소 `getCategoryKeywordRank.naver` 직접 호출, cid 50000006 식품, timeUnit=date). 검증(500건·순위 1~500·중복 없음), `_manifest.jsonl`, 이어받기, 429 백오프. 2024-01-03 하루 맥에서 확인.
  - 클라우드 쪽에서 2026-04-15~ 일부를 미리 받아 같은 폴더에 넣어 둠 (manifest 에 fetched_at 로 구분). 맥 실행이 나머지를 채움.
- **코드 (stage2, 커밋 c6632c3)**
  - `app/services/trends/period.py` — 날짜 상태 구분(관측/500위 밖/누락), change(시작→종료)와 max_gain(최대 개선폭) 분리, 급상승 파일은 종료일 이하만, 그룹 ranked/entered/exited/transient, 정렬 5종, `keyword_history`(전체 순위·감지일·흐름 단계·함께 움직인 키워드), `coverage`, `rank_dir_from_env`(NAVER_DAILY_RANK_DIR → NAVER_DAILY_DIR 대체 + 주의 문구).
  - `GET /admin/api/trends/period?preset=1w|1m|3m | start&end, sort, limit, min_days` · `GET /admin/api/trends/keyword?keyword&start&end` (guest 읽기 허용). 운영 자료로 0.2초.
  - `trends.html` — '기간별 식품 키워드 순위 변화' 섹션 + '키워드 관심 이력' 섹션, 왼쪽 메뉴 2개 추가. 미리보기 렌더 확인(헤드리스 크롬).
  - 테스트 20개 (`tests/services/trends/test_period.py`, `tests/admin/test_admin_trends_period.py`) 통과. tests/admin 의 다른 실패 8개는 HEAD 에서도 같음(번들 파일 없음) — 이번 변경과 무관.
- 연구 문서(리포트 다각 분석 틀·상품 중심 블로그) 작성 — 위 참고.

## 설계 대비 바뀐 점
- 표 칸: '순위 오름폭' → **시작→종료 / 최대 개선폭 두 칸**, '새로' → **상위 500 진입**(별도 그룹), '급상승 감지 일수' → **급상승 목록 포함 일수 + 기간 내 첫 기록일**, '지금 상태' → **종료일 기준 감지 상태 + 최근 방향(7관측일 평균 비교)**.
- 기본 정렬 = 시작→종료 개선폭(양끝 순위 있는 것끼리), 진입 그룹은 종료 순위 순 (GPT 권장). 기본 '2일 이상 500위 안' 필터로 잠깐 등장 노이즈 숨김.
- 데이터 범위: 216일 → 백필 뒤 **2024-01-01~** (전년 동기 비교 가능).

## 겪은 문제 (같은 일 생기면)
- 데이터랩 순위 주소는 `count` 가 20 고정(25쪽), 오늘 날짜는 비어 있음(전날까지). 짧은 간격 연속 호출 시 429.
- VM(device_bash)·클라우드 백그라운드 프로세스는 호출이 끝나면 죽음 → 긴 작업은 맥 터미널 nohup.
- 한글 쿼리 curl 은 `-G --data-urlencode`.
- 미리보기: Claude 내장 브라우저는 claude.ai 로그인이 없어 아티팩트를 못 봄 → 클라우드의 google-chrome + playwright 로 스크린샷.

## 다음 단계 (연구 문서 3절)
시즌 비교(작년 같은 주) → 태그 규칙표 → 리포트 생성기 → 상품 중심 블로그 초안 v2.
