# 2단계 첫 PR — 트렌드 글 게시 뼈대 (2026-11-16)

로드맵 2단계(트렌드 콘텐츠)의 첫 묶음. 브랜치 `stage2/trend-posts-pr1` (main `eb40305` 기준).
작업 중 다른 창의 레시피 커밋 `46d76c3`이 공유 작업 폴더의 `stage2/trend-posts`에 함께 올라가, 2단계 커밋만 `eb40305` 위에 다시 쌓은 브랜치를 PR 용으로 씀(사용자 결정). 레시피 커밋은 그 창에서 따로 PR.
급상승 리포트 → 글 초안 → 검토 대기열 → 운영자 승인(정책 검사 통과 시) → 서버가 그리는 `/trends/...` 게시.

## 0. 시작 전 대조 (2026-11-16 17:30 KST)
| 항목 | 결과 |
|---|---|
| main | `eb40305` = origin/main. 1단계 마무리(PR #5 `1943227`, PR #6 `182035a`) 반영, `ebc542f` 이후는 문서 5개만 |
| 미커밋 | `var/`·`_to_delete/`·`Claude outputs/`·`docs/claude/식품 상담 AI 비교.html` — 1단계 마무리 문서의 '커밋하지 않을 것'과 같음 |
| 전체 테스트 (main) | 5,743 통과 · 5 건너뜀 · 실패 0 — 1단계 마무리와 같음 |
| 순위·표시 기준점 | 이 창의 Linux 환경은 Mac DB(localhost:5432)에 닿지 않음 → 기준점은 `s9_r3`·`d9_r3`(R3 ④ 뒤) 그대로 사용 |
| 로드맵 문서 | '진행 현황'·'다음 창'이 11-10 시점(PR #5 대기·R0 진행 중) — 실제는 `stage1_close_2026-11-16.md` 기준 모두 끝남. **설계 창에서 갱신 필요** |
| 설계 v2 | Claude Docs 원본(rev 160)이 저장소 사본(`commerce_ai_system_design_v2.md`, 11-09)보다 새 버전. 2단계에 '에이전트 브라우저 화면 시험(우리 사이트만)', Q&A '문장별 근거는 확인 가능할 때만'·'기록 전 이용 동의·보존기간' 추가됨 → 원본 기준으로 진행 |

## 1. 사용자 결정 (이 창)
| 질문 | 결정 |
|---|---|
| 글 저장소 | **파일 저장 먼저** — `TREND_POSTS_DIR`(기본 `var/trends/posts`, git 제외). 저장소 인터페이스만 쓰므로 3단계 운영 배치 때 DB로 옮김 |
| 작업 나누기 | **게시 뼈대 먼저** — PR1 게시 뼈대 → PR2 Q&A·원문 보기 → PR3 구조화 데이터·사이트맵·브라우저 화면 시험 → PR4 MCP 도구(선택) |
| 상품 링크 | **`/trends/{글}/go/{번호}` 경유 + 클릭 기록** (고객이 누를 때만 이동) |
| 가격 표시 | **확인 시각과 함께, 30일 뒤 숨김** (`price_claims.STALE_DAYS` 와 같은 30일) |

## 2. 한 일
| 위치 | 내용 |
|---|---|
| `app/services/trend_posts/model.py` | 글 모양·상태(초안·검토 대기·게시됨·반려·내림)·이력, 주소 `{데이터 기준일}-{주제}` |
| `.../store.py` | 파일 저장소 (글 1편 = JSON 1개, 이름은 id 해시, 임시 파일에 쓴 뒤 바꿔 끼움, 깨진 파일은 건너뜀) |
| `.../policy.py` | 게시 차단 검사 10가지 (아래 3절) |
| `.../draft.py` | 급상승 리포트 항목 → 초안. 이유는 리포트 사실만(배수·시작일·순위·블로그 글 수), 원인은 공개 가능·'불명' 아님일 때만 '추정'으로. 외부 블로그·영상은 글 수만(링크·본문 없음). 상품은 공통 검색(`search_products`) picks 순서 그대로 쿠팡 https 만 최대 4개. 레시피는 공공(source) + 이름이 주제로 끝날 때만 |
| `.../service.py` | 초안 만들기(30일 안 같은 주제면 그 글을 엶) · 고치기(초안·반려만, [광고]·고지를 상품에 맞춰 자동) · 가격 다시 확인 · 검토 요청 · 승인(정책 검사 통과 시만) · 반려(사유 필수) · 내림 · 다시 초안 |
| `.../render.py` | 공개 페이지. 모든 칸 이스케이프, 스크립트·자동 이동 없음, 고지를 상품보다 먼저, `rel="sponsored nofollow"`, 가격은 그릴 때마다 지금 시각으로 30일 판단 |
| `.../wiring.py` | 서버 설정의 공통 검색·레시피 (웹 대화·MCP 와 같은 서비스, 미리 보기 상품 제외) |
| `app/api/trend_routes.py` + `main.py` | `GET /trends` · `GET /trends/{글}` (승인 글만, 나머지 404) · `GET /trends/{글}/go/{번호}` (클릭 기록 `query=trend`, 관리자 브라우저는 `trend_internal`, 기록 실패해도 이동) |
| `app/admin/routes.py` + `web/trend_posts.html` | `/admin/trend-posts` 검토 대기열 화면, API(목록·한 편·초안·고치기·가격 다시 확인·검토 요청·승인·반려·내림·다시 초안), 미리 보기(관리자만, `X-Robots-Tag: noindex`). 트렌드 탭 옆 메뉴에 '글 검토 대기열' |

## 3. 게시 차단 검사 (승인 시 통과 필수)
`ad_label`(제휴 상품 → 제목 [광고] + 맨 위 대가성·운영 문구) · `link`(상품 쿠팡 https만, 출처 http(s)만) · `html`(글 칸 HTML·스크립트 금지) · `alcohol`(주류 주제 상품 없음) · `recipe_source`(출처 + '원문 그대로가 아님') · `numbers`(가격·평점 숫자는 상품 칸에만) · `price_claim`('최저가'·'가성비' 등 — 판매처 상품 이름은 제외) · `price_time`(가격엔 확인 시각) · `stale_price`(승인 시점 30일 초과 가격) · `duplicate`(30일 안 같은 주제 게시 글)

## 4. 로드맵 넘어가는 기준과 테스트 (이 PR 범위)
| 기준 | 테스트 |
|---|---|
| 미승인 인용 차단 | 초안·검토 대기·반려·내림 글이 공개 조회·목록·클릭 이동에 나가지 않음 (`test_unapproved_posts_never_reach_the_public_side` ×4, `test_index_and_post_show_only_approved`, `test_go_redirects_only_for_published_products_and_logs_the_click`) |
| 오래된 가격 차단 | 30일 초과 가격은 승인 불가 → 다시 확인 후 승인 (`test_stale_price_blocks_approval_until_rechecked`), 게시 후 30일 지나면 페이지에서 숫자 사라짐 (`test_published_price_hides_itself_after_30_days`, `test_page_hides_price_after_30_days`), 시각 없는 가격 차단 |
| 광고 표시 누락 차단 | [광고]·고지 빠지면 승인 불가 (`test_missing_ad_label_or_disclosure_blocks_approval`), 고칠 때 자동 유지, 페이지에서 고지가 첫 상품 링크보다 앞 |
| (Q&A·MCP) | 다음 PR — 같은 검사를 Q&A 답변·MCP 도구 응답에도 |

새 테스트 36개: `tests/services/trend_posts/` 24 · `tests/web/test_trend_pages.py` 6 · `tests/admin/test_admin_trend_posts.py` 5 (+ 기존 탭 검사 통과).

## 5. 전체 테스트·검사
| 시점 | 결과 |
|---|---|
| main `eb40305` | 5,743 통과 · 5 건너뜀 · 실패 0 |
| 이 브랜치 `stage2/trend-posts-pr1` (eb40305 + 2단계만) | **5,778 통과 · 5 건너뜀 · 실패 0** |
| (참고) 작업 폴더 `stage2/trend-posts` (다른 창 레시피 커밋 46d76c3 포함) | 5,779 통과 · 5 건너뜀 · 실패 0 |

- 실행 환경: Mac 안 Claude 작업용 Linux 환경, Python 3.14.8, `uv.lock` 그대로(`uv run --frozen`). 가상환경은 연결 폴더 밖(`/tmp`)에 따로 — Mac `.venv` 는 건드리지 않음
- ruff: 새 파일 경고 0. `app/admin/routes.py`·`app/main.py` 경고 8건(B008 6·F401·F841)은 이번 변경 전부터 있던 줄
- 실제 리포트(`surge_2026-11-16.json`) 상위 8개 단어로 초안 → 모두 정책 검사 통과, 한 편 승인 후 페이지 그림 확인(상품은 테스트 데이터)
- **순위·표시 불변**: 추천·채팅 코드는 바꾸지 않음(새 모듈·새 경로만). Mac 에서 `bash var/stage1_close_check.sh stage2` 로 s8·d8 대비 확인 필요

## 6. 남은 일
- **Mac 확인** (이 창에서 못 함): ① `bash var/stage1_close_check.sh stage2` 순위·표시 불변 ② 서버 재시작 후 `/admin/trend-posts`에서 실제 쿠팡 상품으로 초안 한 편 → 승인 → `/trends` 확인
- 2단계 다음 PR: Q&A·원문 보기(승인 글만 색인, 근거 없으면 '관련 트렌드 글이 아직 없습니다', 기록은 이용 동의·보존기간 결정 뒤) → 구조화 데이터(Article)·사이트맵·브라우저 화면 시험 → MCP 도구(선택)
- 결정 필요(설계 창): 글 저장소 백업 방식(git 제외라 Mac 백업에 포함 필요), 자동 게시 전환 기준(설계 v2 '결정이 필요한 사항'), 로드맵 문서 '진행 현황' 갱신
- 공개 범위: `/trends`는 `PUBLIC_MODE` 보호 대상이 아님(요청 수 제한 없이 열림 — 서버 렌더 페이지라 유료 API 호출 없음). 트렌드글 초안 만들기만 쿠팡·DeepSeek 를 부르고 관리자 전용
