# 창 3-A — 2단계 마무리 (2026-11-22)

로드맵 `claude/roadmap_stages_2026-11-09.md` '3-A. 2단계 마무리' 항목을 저장소(main `3831a82`, PR #56 병합 뒤)와 대조한 결과.

## 0. 정리
| 항목 | 결과 |
|---|---|
| ① 헤더 B안 | 완료 — PR #12 (`stage2/header-b` main 대비 남은 커밋 0) |
| ② 스테이징 4개 파일(`adapt.ts`·`ProductDetail.tsx`·`coupang_report_probe.py`·`coupang_search_probe.py`) | 모두 main 에 있음 (#32·#37·#47 등으로 들어감) — 넘길 것 없음 |
| ③ `stage2/trend-posts` (main 대비 8커밋) | 8개 모두 다른 PR 로 병합된 내용: 레시피 분량 = #8, 트렌드 글 게시 뼈대 = #11, B2B 제안서 5개 = #9, 목차 = #15. **브랜치 지워도 됨**(운영자: `git push origin --delete stage2/trend-posts`) |
| 그 밖 `stage2/*` (`bc-finder`·`connect`·`bc-issued`·`e2e-url-fix`) | 남은 커밋 0 — #13·#14·#17·#16 |
| ④ 8001 = main | 완료 (11-20) |

## 1. 기준점
- 11-22 17:23 운영(main `13d2c97`, #49 뒤): 순위 s8 → s9_main **같음 63/63**, 화면 d8 → d9_main **순서·후보 같음 11**(배지 문구만 다름 1).
- 그 뒤 #50~#56 (용량 검색어·비슷한 말·다른 후보/냉동 펼침·검색 결과 저장·6개 미만 더 찾기·옵션 근거 줄·상품어 고침)이 들어감 → 운영에서 다시 확인 후 **s10·d10 고정**:
  ```
  bash var/stage1_close_check.sh main            # s8/d8 대비 (s10 없으면 자동)
  uv run python scripts/stage1_ranking_snapshot.py capture s10
  uv run python scripts/stage1_display_snapshot.py capture d10
  ```
  분류(외부 검토 3): 기존 추천 영역 후보·순서 유지 / 추가 탐색 영역 신설(추가 후보·등급 확인 필요 칸) / 전체 표시 상품 집합 변경. 기존 추천 영역이 같아야 고정.
- `var/stage1_close_check.sh`: `s10.json`·`display_d10.json` 이 있으면 그것과 비교(없으면 s8/d8, `S_BASE`·`D_BASE` 로 지정).

## 2. 화면 연결 (11-20 결정 — 트렌드 글은 메뉴에서만)
- 홈·지금 뜨는 식품에 트렌드 글 줄·'트렌드 글 읽기' 없음 — 브라우저 테스트로 확인(`test_home_header_and_todays_trends`, `test_hot_page_has_no_trend_posts`).

## 3. 구조화 데이터·사이트맵 — 완료(#14)
- 글 페이지 Article JSON-LD(가격 없음, `<` 이스케이프)·canonical, `/sitemap.xml`(승인 글만), `/robots.txt`.

## 4. 화면 시험 — Playwright 로 고정
- `tests/e2e/test_site_browser.py` 7개 통과(리눅스, Chromium headless shell · `frontend/dist` 빌드 후):
  기존 4 + **새 3** — ① 홈·지금 뜨는 식품·트렌드 글 목록·글 페이지에 **이름 없는 버튼·링크·입력 0** ② 검토 대기·반려·내린 글은 주소로 들어가도 **404**, 목록에 링크 없음 ③ **사이트맵에 승인 글만**.
- 맥: `uv run playwright install chromium` → `npm --prefix frontend run build` → `uv run pytest tests/e2e -q`.

## 5. 트렌드 리포트 MCP 도구 — 완료(#14) `food_trend_posts`·`food_get_trend_post`.

## 넘어가는 기준
2단계 기준 ✅ · 화면 시험 통과·이름 없는 버튼 0 ✅ · 사이트맵 미승인 글 0 ✅ · 순위·화면 불변 — **운영 확인 후 s10·d10 고정 남음** · 전체 테스트 실패 0 — 기존 실패 9(관리자 번들 파일 없음 8 등, main 에서도 같음).

## 다음
3-B '내 보관함'(`ui/my-shelf`) → 3-C '지금 순위'(+ 홈 예시 카드 20개 묶음·하루 4장, 레시피 포함 — 11-22 논의).
