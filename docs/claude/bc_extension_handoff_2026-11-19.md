# 인계 — 브랜드커넥트 화면에 '등록부에 저장' 버튼 (크롬 확장, 2026-11-19)

창 2(2단계 트렌드 콘텐츠)에서 넘김. 사용자 결정: 링크 **발급은 사람이 브랜드커넥트 화면에서**, 발급 직후 **같은 화면에서 버튼 하나로 commerce_ai 등록부(naver_connect_links.csv)에 저장** (2번 방식). '나란히 창 + 돌아오면 자동 다시 읽기'(1번)는 써 보니 불편하다고 함.

이 문서는 같은 내용으로 claude.ai 프로젝트 'commerce_ai 추천 시스템'의 claude/bc_extension_handoff_2026-11-19.md 에도 있다.

## 시작 상태 (2026-11-19 11:25)
- GitHub main = `7b7ddce` (PR #17 `stage2/bc-issued` 병합까지). `~/commerce_ai_generator`(8001 운영 폴더)도 main `7b7ddce`.
- 작업 폴더 권장: `~/commerce_ai_generator_stage2` (git worktree, 지금 `stage2/bc-issued` 브랜치) → main 에서 새 브랜치(예: `ext/bc-to-registry`)로 시작.
- **git 쓰는 법 (중요)**: stage2 는 worktree 라 `.git` 이 `/Users/mom/commerce_ai_generator/.git/worktrees/commerce_ai_generator_stage2` 를 가리킨다. Claude 작업 VM 에서는 두 폴더를 **모두 연결**하고 이렇게 부른다:
  `R=$HOME/mnt/commerce_ai_generator/.git; W=$HOME/mnt/commerce_ai_generator_stage2; G="git --git-dir=$R/worktrees/commerce_ai_generator_stage2 --work-tree=$W"; $G status`
  커밋·브랜치 전환에는 `~/commerce_ai_generator` 폴더의 삭제 허락이 필요하다(git 잠금 파일). VM 에서 `git worktree prune` 은 하지 말 것(맥 경로를 못 찾아 worktree 를 지워 버림). push 는 맥 터미널에서 사용자가 한다.
- 테스트: VM 에서는 stage2 의 일부 파일이 맥 절대경로 심볼릭 링크라, `git archive HEAD | tar -x -C /tmp/wB` 로 사본을 만들고 바뀐 파일을 복사한 뒤
  `UV_CACHE_DIR=/tmp/uvc UV_PROJECT_ENVIRONMENT=/tmp/venv uv run --frozen pytest -q -p no:cacheprovider tests/services/affiliate tests/admin`
  (B2B 테스트는 `app/admin/b2b/data/*.json` 을 원본 폴더에서 복사해야 함). 프런트는 `node node_modules/typescript/bin/tsc --noEmit`.
- 식품 모니터링(`~/food_recommend/shop_monitor`, **git 밖**): `collectors/brandconnect_web.py` 가 리뷰 수·평점 저장(11-18), `tools/bc_refresh.py <키워드>` = 키워드 하나 다시 읽기(읽기 전용, `tools/bc_browser.py` 로 연 9222 브라우저 우선). 매일 수집이 11-17~18 로그인 만료로 실패했었고 11-19 다시 로그인함.

## 이미 있는 것 (재사용)
- 등록 API: `POST /admin/api/connect/links` body `{rows:[{keyword, product_name, store_name, price, discount_price, commission_rate, link, memo}], request_id?}` — 헤더 `X-Access-Token`(관리자 토큰). 중복 링크 거부, 링크 형식 검사(naver.me·brandconnect), 수집분이 다른 상품 것으로 아는 링크 거부(`brandconnect_finder.link_owner`), .bak 백업. `price` = 할인 전 판매가, `discount_price` = 할인가.
- 등록부 열: 상품명·스토어명·판매가(=할인가가 있으면 할인가)·정가·수수료율(%)·링크 발급일·쇼핑커넥트 링크·키워드·링크 확인일·사용처(블로그)·메모.
- 관리자 화면: 트렌드 → 네이버 탭(`/admin/trends#naver`)에 블로그 초안·발급 요청·브랜드커넥트 상품 찾기·등록된 링크('발급한 링크 불러오기', '다시 읽고 불러오기'). 코드 `app/admin/web/trends.html`, `app/admin/routes.py`, `app/services/affiliate/{brandconnect_finder,connect_registry}.py`.
- 브랜드커넥트 내부 API (bc_fields_probe 로 확인): 검색 `GET https://gw-brandconnect.naver.com/affiliate/query/affiliate-products/search-by-query?query=&limit=&cursor=` (헤더 x-space-id = 채널 971564859961248) → 상품 필드 `id, productName, storeName, salePrice, discountedSalePrice, discountedRate, commissionRate, reviewInfo{totalReviewCount, averageReviewScore}, shortenUrl, urlCreatedAt, productStatus` 등. 발급은 `.../affiliate/command/affiliate-urls?affiliateProductId=` (POST — **우리 확장은 호출하지 않음**).
- `~/food_recommend/shop_monitor/tools/bc_extension/` 는 남이 만든 '쇼핑 커넥트 상품 검색' 확장 사본(발급 POST 를 직접 함) — 참고만, 그대로 쓰지 않음.

## 만들 것 (제안 설계 — 새 창에서 사용자와 확인)
1. MV3 크롬 확장 `extensions/bc-to-registry/` (commerce_ai 저장소 안, 테스트 가능하게).
2. 콘텐츠 스크립트(brandconnect.naver.com/*/affiliate/products): 페이지의 fetch/XHR 응답을 **읽기만** 해서 검색 결과(상품 정보)와 사람이 누른 발급 응답(shortenUrl)을 잡는다. 발급된 상품 카드 옆에 '등록부에 저장' 버튼(이미 등록된 링크면 '저장됨').
3. 버튼 → 백그라운드(service worker)가 `http://localhost:8001/admin/api/connect/links` 로 POST (host_permissions 로 CORS 우회). 키워드 = 브랜드커넥트 검색창의 검색어(수정 가능). 정가·할인가·수수료는 응답 값 그대로 — 손으로 붙여 넣을 일 없음.
4. 옵션 화면: 서버 주소(기본 localhost:8001, 공개 주소 금지 권장), 관리자 토큰 → chrome.storage.local. 토큰은 화면·로그에 보이지 않게.
5. 정책 선: 발급·검색 API 를 확장이 스스로 부르지 않음(사람이 한 동작의 응답만 읽음), 자동 대량 저장 없음(버튼 한 번 = 한 상품).
6. 확인: 순수 함수(응답 → 등록부 행 변환)는 node 테스트, 등록 API 는 기존 pytest(`tests/services/affiliate/test_connect_registry.py`)에 확장이 보내는 모양 그대로 1건 추가. 실제 화면은 맥 Chrome 에서 '압축해제된 확장 로드'로 사용자 확인.
7. 확장이 잘 되면 1번(상품 찾기의 '발급하러 가기'·자동 다시 읽기) 버튼은 지울지 사용자에게 물어보기.

## 창 2 에 남은 것
- Google Trends API 승인 대기 (메일 오면 연결).
- 고객 화면(내 보관함·설정·로그인, UI/UX 연구)은 창 3 으로 (프로젝트 문서 claude/stage2_trend_posts_2026-11-16.md '사용자 결정' 참고).
