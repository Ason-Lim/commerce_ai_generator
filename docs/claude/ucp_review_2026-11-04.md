# UCP 활용 검토 — 네이버 쇼핑 API 종료 이후 여러 쇼핑몰 연결 (2026-11-04)

배경: 네이버 쇼핑 검색 API 종료(2026-07-31, naver_shopping_api_end_2026-11-04.md) → '감귤'에 SSG·컬리·롯데마트·홈플러스·GS fresh 상품을 함께 보여 줄 공식 경로가 없음. UCP 로 가능한지 검토.

## UCP 확인 사항 (공식 사양·발표)
- Google 이 2026-01-11 NRF 에서 공개한 개방형 표준. 공동 개발 Shopify·Etsy·Wayfair·Target·Walmart, 결제 Visa·Mastercard·Stripe 등 지지.
- 사양 버전: 2026-04-08, 2026-08-25 (ucp.dev/specification/overview).
- 역할: Platform(에이전트 — commerce_ai 자리) · Business(판매자, Merchant of Record) · Payment Credential Provider.
- 발견: 판매자가 `https://<몰>/.well-known/ucp` 에 프로필 게시 → 플랫폼이 capability 교집합·버전 협상.
- 플랫폼도 자기 프로필 URI 를 모든 요청에 보내야 함 (HTTP `UCP-Agent` 헤더 / MCP meta `ucp-agent.profile`) → 공개 HTTPS 주소에 플랫폼 프로필 필요.
- 기본은 사전 등록 없는(permissionless) 참여지만, 판매자는 승인된 플랫폼만 허용하는 등 접근 정책을 완전히 통제.
- 전송: REST(OpenAPI) · MCP(OpenRPC/JSON-RPC) · A2A · Embedded.
- capability: catalog(search·lookup) · cart · checkout · identity linking · order · (초안) booking·food.
- **catalog 는 판매자 단위** — 한 Business 의 카탈로그 검색. 여러 몰 통합 검색 기능은 사양에 없음 (Google 은 Merchant Center 로 자체 수집).
- catalog 규칙: "checkout is authoritative"(카탈로그 가격은 확약 아님), 세션 간 재검증 없이 재사용하지 말 것(SHOULD NOT), `unit_price.amount` 는 플랫폼이 다시 계산하면 안 됨(MUST NOT), `presentation: "disclosure"`(알레르기·안전 고지)는 숨기면 안 됨.
- 상용: UCP 결제는 미국만 운영 중(2026-05 기준), 캐나다·호주·영국 예정. 한국 언급 없음. 2026-03 업데이트에서 cart·catalog·identity linking 추가, Merchant Center UCP 온보딩 간소화.

## 직접 확인 — 국내 몰 UCP 프로필 (2026-11-04 21:5x, check_ucp_profiles.py)
- **이 주소·접근 방식(`https://<호스트>/.well-known/ucp` GET 1회)에서 유효 프로필 미확인** — 미지원 확정이 아님 (p41 보정). 404: ssg.com, emart.ssg.com, kurly.com, oasis.co.kr, coupang.com · 403(접근 차단, 판단 불가): lotteon.com, gsfresh.com, gmarket.co.kr · 405: gsshop.com · HTML 응답: homeplus, 11st.co.kr(오류 페이지).
- 비교: allbirds.com(Shopify) 프로필 있음 — 버전 2026-08-25, catalog.search·lookup·cart·checkout·order·identity_linking·permalink 등. (walmart·target·etsy 는 이 주소에 없음 — 다른 방식으로 Google 과 연동하는 것으로 보임, 미확인.)

## 결론
- **이번 조사에서 UCP 로 즉시 연결 가능한 국내 몰은 확인하지 못했다** — 위 주소에서 유효 프로필이 없었고, UCP 는 몰 단위 프로토콜이라 통합 검색 창구도 없다.
- UCP 는 '몰이 공개한 공식 창구'를 표준 방식으로 쓰는 길이라, 스크래핑 제외 원칙과 맞는 장기 경로. 국내 몰이 참여하면 **공통 어댑터를 재사용**할 수 있다 — 다만 판매자별 인증·접근 조건·지원 capability·오류 처리 확인은 몰마다 남는다.

## 제안 (커밋·배포 없음, 결정 필요)
1. **UCP 카탈로그 읽기 어댑터 (구매자 쪽, 읽기 전용)** — `CatalogSource` 하나로 `/.well-known/ucp` 발견 → catalog.search 호출 → 공통 모델(Offer·Evidence) 변환. 대상 몰은 등록부(호스트·허락 상태)에 적힌 곳만, 기본 꺼짐. checkout·cart·identity linking 은 쓰지 않고 지금처럼 판매처 이동(permalink/상품 url)만. 근거 method=`ucp_catalog`, 가격은 '확인 시점 값'·세션 간 재사용 금지, 판매자가 준 unit_price 는 재계산하지 않고 그대로 표시, disclosure 는 그대로 노출. 시험 대상은 프로필이 있는 해외 Shopify 몰(예: allbirds) — 실제 화면에는 안 씀.
2. **업체 상품 제공 형식을 UCP 카탈로그 응답 형식으로도 받기** — 온브릭스 등 의향 문의 업체에 "UCP catalog 형식(또는 CSV)" 을 선택지로 제시. Shopify 쓰는 업체도 개별 상점의 프로필·catalog 지원과 우리 플랫폼 접근 허용을 확인해야 함, 업체 허락 기록부(permissions.csv) 절차는 그대로.
3. **국내 몰 UCP 참여 주기 확인** — check_ucp_profiles.py 를 월 1회 실행(예약 작업 가능), 프로필이 생기면 알림 → 그때 몰과 이용 조건 확인 후 등록부에 추가.
4. 필요 조건: 공개 HTTPS 도메인에 commerce_ai 플랫폼 프로필 게시(UCP-Agent), 판매자별 이용 조건·호출 한도 확인. 국내 몰(SSG·컬리·롯데ON·홈플러스·GS)과는 UCP 와 별도로 제휴·상품 데이터 제공 문의가 여전히 현실적인 경로.

## 출처
- https://ucp.dev · https://ucp.dev/specification/overview/ · https://ucp.dev/specification/shopping/catalog/
- https://blog.google/products-and-platforms/products/shopping/ucp-updates/ (2026-03-19)
- https://ppc.land/google-expands-ucp-to-hotels-food-delivery-and-three-new-countries/ (2026-05-20)
- https://byline.network/2026/01/12-514/ (2026-01-12)

---

## 사용자 결정·사업 구조 (2026-11-04 22:13)
- 1번(UCP 카탈로그 읽기 어댑터)부터 진행. 미리 준비.
- 기존 사업 모델: 오프라인 매장·온라인 스토어를 열려는 판매자에게 상세페이지 제작 모듈 제공 + commerce_ai 플랫폼에서 판매.
- 향후: 성수동·홍대 등에서 쇼핑한 내국인·외국인의 짐을 우체국·택배사·포워딩 업체와 연계해 국내외 배송.
- 도메인: trendguide.co.kr, trendguide.kr (구매 완료). 2026-11-04 확인: trendguide.kr → 121.254.178.253 (HTTPS 없음, 등록 업체 기본 연결로 보임), trendguide.co.kr → DNS 없음.
- UCP 역할은 **별도 설계로 구분**: ① 외부 몰을 조회할 때 commerce_ai = **Platform** (p40·p41 어댑터) ② 입점 판매자 상품을 외부 AI 에 제공할 때 commerce_ai(또는 판매자) = **Business**. Business 쪽은 Shopify 처럼 판매자별 프로필을 대신 내는 구조가 가능하나, 판매 책임(Merchant of Record)·결제·환불 책임은 프로필 게시만으로 정해지지 않음 — 계약·사업자 구조로 따로 정해야 함.
- 배송: UCP fulfillment 는 배송 조건(방식·예정일·비용 등)을 **표현하는 확장**이지 우체국·택배·포워더의 접수·운임·통관 연계를 제공하지 않음 — 배송 사업은 별도 단계(각 사업자 API·계약).

## p40 — UCP 카탈로그 읽기 어댑터 (2026-11-04, 새 파일만, 미연결·기본 꺼짐)
백업 `recipe_chat_api_backups/20261104_p40_ucp_catalog_client/` (새 파일 목록·diff·전체 테스트 로그). 커밋하지 않음.
- `app/services/ucp/`: platform(우리 프로필·사용 여부: UCP_CATALOG=1 + UCP_PLATFORM_PROFILE_URL https) · discovery(/.well-known/ucp, 판·capability·전송 협상, REST 우선 없으면 MCP, https endpoint 만, Cache-Control 캐시, 호스트 형식 검사) · client(REST POST {endpoint}/catalog/search + UCP-Agent·Request-Id / MCP tools/call search_catalog + meta.ucp-agent, 오류 코드·continue_url, 429, 응답 크기 제한, 판매자별 실패 격리) · mapping(옵션마다 카드 1개, KRW 최소 단위=원, 원화 아니면·품절이면 뺌, 판매자 unit_price 는 기준 100g 일 때만 per100g 로 그대로 — 다른 기준은 환산하지 않고 문구만, https 링크·이미지만, disclosure 경고 보존, seen_at·'카탈로그 가격은 확약 아님') · registry(data/ucp/merchants.csv, 상태 사용/시험/중지; 템플릿에 allbirds.com 시험용).
- 실제 확인: allbirds.com 협상 가능(2026-08-25, MCP, search·lookup). 우리 프로필 없이 검색하면 422 `profile_unreachable` + continue_url (fixture 로 고정).
- `make_ucp_profile.py` → `Claude outputs/ucp_site/`(.well-known/ucp, _headers, .nojekyll, index.html). 공식 스키마 ucp.json#/$defs/platform_schema 로 검증 0 오류. **스키마 통과 ≠ 실제 협상·검색 성공** — 게시 후 실제 판매자 검색으로 따로 확인해야 함.
- `check_ucp_catalog.py` — 프로필 접근·협상·검색 1회·카드 변환 결과 출력 (읽기 전용).
- 테스트 38개 (tests/services/ucp). Linux 사본 전체 7 failed / 5,267 passed (실패 목록 p39 와 동일). 맥 원본 ucp·chat·mcp 570 passed / 1 failed(기존 dev-trace).
- 다음: trendguide.kr 에 HTTPS 정적 호스팅으로 프로필 게시 → .env UCP_PLATFORM_PROFILE_URL → check_ucp_catalog.py 로 allbirds 실제 검색 확인 → 공통 검색(collect) 연결 여부 결정(근거 method 추가·화면 표시 규칙 포함).

## p41 — GPT 검토(22:31) 반영 (2026-11-04)
백업 `recipe_chat_api_backups/20261104_p41_ucp_review_fixes/` (수정 전 7개 파일, SHA256, p41.diff, 전체 테스트 로그). 커밋하지 않음.
- **판매 단위**: 사양상 price 는 `quantity_unit` 1단위당 가격 → quantity_unit 이 '개(C62, scale 0)'가 아니면(kg당·0.25 lb 단위 판매 등) 카드로 만들지 않고 skipped("단위 판매 — 한 팩 가격 아님", 원문 보존).
- **100g 판정**: 단위는 UN/ECE Rec20 코드(GRM·KGM·C62…), 수치는 value×10^-scale. per100g 는 reference = GRM 이고 value×10^-scale = 100 (정수 비교)일 때만 판매자 unit_price.amount 그대로. unit_price 통화 = price 통화, measure·reference 단위 같아야 함(사양) — 아니면 unit_price 를 쓰지 않음. 다른 기준(1kg 등)은 환산하지 않고 표시 문구만.
- **출처 보존**: 카드 ucp = 호스트·product/variant ID·선택 옵션(variant.options)·응답 시각·협상 판·전송·unit_price 원본·disclosure, `score_use='block'`(근거 용도 판정 연결 전까지 점수 불가).
- **규범 구분**: 세션 간 재검증 없는 재사용 제한 = 사양 SHOULD NOT(권고), 프로젝트 정책은 연결 단계에서 정함 — 코드 주석 수정.
- **적합성**: ① 프로필·schema·검색 모두 리다이렉트 따라가지 않음(MUST NOT follow 3xx) ② capability·service schema URL 출처 = namespace(dev.ucp.* → ucp.dev, 라벨 경계) — 안 맞으면 그 항목 버림(MUST reject) ③ 협상한 catalog.search schema(판매자가 밝힌 URL, 없으면 사양 기본)를 가져와 응답 검증 — 위반이면 검색 실패(schema_invalid), 검증기 없으면 '검증 안 함'으로 표시(통과로 치지 않음). 확장(extension)은 활성화하지 않으므로 합성 = 기본 schema. ④ 캐시 TTL 최소 60초.
- **게시 점검** `schemas.check_published_profile`: https · 3xx 없음 · Cache-Control public + max-age≥60 · private/no-store/no-cache 없음 · JSON · platform_schema 적합. (GitHub Pages 기본 헤더 'max-age=600'은 public 이 없어 불합격 → Cloudflare Pages 등 헤더 지정 가능한 곳 권장.) 프로필 주소는 리다이렉트 금지 → trendguide.kr 로 바로 응답해야 함(trendguide.co.kr → .kr 리다이렉트 주소를 프로필 URL 로 쓰면 안 됨).
- 테스트: 오프라인용 ucp.dev 공식 schema 25개 보관(tests/services/ucp/fixtures/schemas_2026-08-25, 2026-11-04 내려받음). fixture 검색 응답도 공식 schema 적합으로 수정(description·price_range 필수). ucp 테스트 77개(+39). Linux 사본 전체 7 failed / 5,306 passed (실패 목록 동일). 맥 원본 ucp·chat·mcp 609 passed / 1 failed(기존 dev-trace).

## 프로필 게시 준비 (2026-11-05)
- 비용: Cloudflare Free(DNS·Pages) 로 0원 — 도메인 갱신비(가비아)만. 루트 도메인을 Pages 에 붙이려면 가비아에서 네임서버를 Cloudflare 로 변경(무료). CNAME(partial) 연결은 Business 이상 유료.
- 가비아 현황(2026-11-05 확인): trendguide.kr NS = ns.gabia.net/ns.gabia.co.kr/ns1.gabia.co.kr, A = 121.254.178.253(가비아 기본 연결), 메일(MX) 없음 → 옮겨도 잃을 설정 없음. trendguide.co.kr 은 DNS 응답 없음(등록 처리 상태 확인 필요).
- make_ucp_profile.py 보완(p42): 맥 Finder 가 숨기는 `.well-known` 폴더가 업로드에서 빠질 때를 대비해 `ucp-profile.json` + `_redirects`(`/.well-known/ucp /ucp-profile.json 200` — 3xx 아닌 재작성) 추가.

## 첫 실제 검색 성공 (2026-11-05 21:4x)
- Cloudflare Pages 프로젝트 `trendguide` 배포(직접 업로드, legacy Pages 흐름 'Continue to Pages'). 프로필 https://trendguide.pages.dev/.well-known/ucp — HTTP 200, application/json, `public, max-age=3600`, 리다이렉트 없음 → check_published_profile 통과(platform_schema 포함).
- .kr 레지스트리 NS 가 Cloudflare(indie·venkat.ns.cloudflare.com)로 바뀐 것 확인. trendguide.kr Custom domain 연결은 Cloudflare 활성(Active) 후 진행.
- `UCP_PLATFORM_PROFILE_URL=https://trendguide.pages.dev/.well-known/ucp` 로 check_ucp_catalog.py "wool runner" 실행: allbirds.com(MCP, 2026-08-25)이 우리 프로필을 받아들임 → 상품 5개 응답, **응답 스키마 검증 통과**. 옵션 41개 모두 USD 라 원화 카드 0개(설계대로 제외 — context 에 KR/KRW 를 보냈지만 USD 로 응답).
- 의미: 발견→협상→우리 프로필 검증(판매자 측)→검색→스키마 검증→카드 변환까지 실제 판매자와 끝까지 동작 확인. 국내(원화) 판매자는 아직 없음.

## 맥 공개 운영 결정·준비 (2026-11-05 22:1x)
- 사용자 결정: commerce_ai 는 Cloudflare Tunnel 로 trendguide.kr 에 연결해 **맥이 켜져 있는 동안만** 공개(시험 운영). Render 정리: smallbiz-monitor·gift-bid-trend-analyzer·food_recommend 중단, food-recommend-web 삭제, smallbiz-db 백업(2026-11-05T13_05Z.dir.tar.gz, DB 3개·표 10개 확인) 후 삭제 예정. food-monitor-dashboard 는 DB 미사용(맥 shop_monitor → GitHub data/*.json.gz → Render 자동 배포)이라 유지.
- trendguide.kr Cloudflare 활성 확인(NS indie·venkat, A 가 Cloudflare 프록시 IP).
- UCP 프로필 주소는 맥이 꺼져도 응답하도록 Pages(https://trendguide.pages.dev/.well-known/ucp) 유지 — trendguide.kr 루트는 Tunnel(commerce_ai)에 씀.
- p43 공개 보호 `app/public_guard.py` (PUBLIC_MODE=1, Cloudflare 헤더 CF-Connecting-IP 있는 요청만): 예전 API(/generate·/track-click 열린 이동·/recommendations/*)와 API 문서(/docs·/openapi.json) 404, /api/chat·/api/recipe/* 방문자별 분당 12·하루 200회(429). 관리자 화면은 기존 32자 토큰. 실제 앱으로 확인(외부 404·401, 맥 직접은 그대로). 테스트 9개, 전체 7 failed / 5,315 passed(실패 목록 동일). 백업 recipe_chat_api_backups/20261105_p43_public_guard/.
- 공개 전 .env 권고: PUBLIC_MODE=1, ADMIN_GUEST_TRENDS=0(지금 1 — 트렌드 보고서가 로그인 없이 보임), PARTNER_PREVIEW=0(지금 1 — 예시 업체 데이터가 고객 화면에 보임).
- **주소 구성 확정 (2026-11-05 22:2x, 사용자 선택)**: trendguide.kr = Cloudflare Pages(안내 페이지 + UCP 프로필, 항상 열림 — Custom domain Active, 프로필 게시 점검 통과), 서비스 = **app.trendguide.kr** (Cloudflare Tunnel → 맥 localhost:8001, 맥이 켜져 있을 때만). .env UCP_PLATFORM_PROFILE_URL=https://trendguide.kr/.well-known/ucp. make_ucp_profile.py 안내 페이지를 한국어 랜딩('서비스 열기' → app.trendguide.kr)으로 바꿈(p44) — Pages 재배포 필요.
- **app.trendguide.kr 공개 확인 (2026-11-05 22:5x, 바깥에서 접속)**: Tunnel commerce-ai(c5cc1a4b-…) · cloudflared 2026.10.7. / 200(화면), /docs·/openapi.json·/track-click·/generate·/recommendations/nl 404, /admin·/admin/trends 303(로그인으로), /admin/api/clicks·/admin/api/trends 401(손님 트렌드 꺼짐), POST /api/chat 200 — 맨 위 '광고' 쿠팡 파트너스 표시 블록, 예시(업체 미리보기) 데이터 없음, 개발 추적(trace) 없음('traceid'는 쿠팡 제휴 링크 주소의 일부). UCP 프로필 trendguide.kr 주소로 allbirds 검색 수락 확인. check_ucp_catalog.py 에 원본 상품(통화 그대로) 목록 출력 추가.

## p45 — GPT 검토(11-06 15:14, p40~p42 코드 검토) 반영 (2026-11-06)
백업 `recipe_chat_api_backups/20261106_p45_ucp_validation_cache_unitprice/` (before/·p45.diff·README·전체 테스트 로그). 커밋하지 않음.
- **검증기 필수**: requirements.txt 에 jsonschema·referencing 추가. `schemas.prepare()` 가 협상 catalog.search schema 와 **모든 참조**(현재 49개)를 판매자 요청 전에 확보 — 검증기 없음·참조 하나 실패면 판매자 POST 0회(REST·MCP 테스트). 검증은 확보한 것만으로(검증 중 조회 없음). `client.search(validate=...)` 옵션 제거, 위반이면 response 를 비우고 실패. 카드는 `mapping.cards_from(outcome)` — 검증 통과 결과로만.
- **판매자 프로필 캐시**: Cache-Control 그대로 — 헤더 없음 0초(매번 조회), max-age=N → N초(최대 1일), no-store·no-cache·private → 보관 안 함. 우리 프로필 게시 검사(public·max-age≥60)는 별개로 유지.
- **판매자 단위가격 분리**: `seller_unit_price`(원본·표시)만 두고 UCP 카드의 weight_g·per100g·per_unit 은 비움 + `price_compare_blocked`. explain.enrich·reweigh 가 상품명으로 다시 채우지 않고, choose 의 가성비·넉넉한 양·개당 비교에서 제외. 회귀: 판매자 단위가격·상품명 중량만 바꿔도 역할·순서 동일(보호를 끄면 5개 테스트 실패 확인). 통화 일치·measure/reference 단위 일치 검사는 스키마 밖 규칙으로 유지.
- **C62 + increment>1**: "N개 단위 주문 · 현재 카드에서 주문 조건 표시 불가" 로 보류, 가격은 1개 기준 그대로(묶음 가격으로 바꾸지 않음).
- **라이브 확인**: https://trendguide.kr/.well-known/ucp 직접 200, application/json, public max-age=3600, 리다이렉트 없음.
- **사고·복구**: 반영 중 explain.py 를 오래된 작업 사본으로 덮어써 11-05 이후 다른 작업이 잠시 빠짐 → 맥 테스트 3개 실패로 발견, before/ 원본으로 복구(SHA256 일치) 후 p45 변경만 재적용. p39·p41·p43 은 덮어쓰기 없었음을 diff 로 확인. 작업 사본을 맥 최신으로 동기화.
- 검증(맥 최신 기준): 전체 7 failed / 5,411 passed(실패 목록 동일), UCP 99 passed, ucp·chat·mcp·공개보호 645 passed / 1 failed(기존 dev-trace).

## p46 — GPT 검토(11-06 17:11) 반영 (2026-11-06)
백업 `recipe_chat_api_backups/20261106_p46_ucp_schema_prepare_cache_age/` (before/·p46.diff·README·전체 테스트 로그). 커밋하지 않음.
- **요청 전 검증 준비 완결**: `schemas.prepare()` → `Prepared` — 문서 수집 시 중첩 `$id` 를 기준 주소로 반영(sub/base.json 의 'leaf.json' = sub/leaf.json), Registry 구성·crawl, 모든 `$ref` 해석 확인(lookup), check_schema, `search_response` 검증기 생성까지 판매자 요청 전에. `$dynamicRef`·`$recursiveRef` 등 지원하지 않는 구조, 해석 실패, search_response 없음 → 요청 전 보류(POST 0회, REST·MCP).
- **조회 예외**: 스키마 GET 의 타임아웃·연결 실패 → SchemaError → `schema_unavailable` 결과(예외가 호출부로 새지 않음), POST 0회.
- **캐시 남은 시간**: `cache_seconds(headers, now)` = max-age − max(Age, 지금−Date) (RFC 9111). 예: max-age=10·Age 9 → 1초. 미래 Date·잘못된 Date 는 나이 0.
- **카드 key 안정화**: `explain.card_key` — UCP 카드는 호스트·상품·옵션 ID 로, 상품명이 바뀌어도 같은 key, 변환 key == enrich 뒤 key, 차단 표시도 보존(테스트).
- 반영 전 안전 확인: 맥 파일 mtime 이 p45 직후 그대로, diff 삭제 줄은 모두 의도한 교체.
- 검증: UCP 122 passed(+23), 전체 7 failed / 5,434 passed(실패 목록 동일), 맥 ucp·chat·mcp·공개보호 668 passed / 1 failed(기존 dev-trace).
- **판매자 실제 검색 (2026-11-06 17:3x)**: 프로필 https://trendguide.kr/.well-known/ucp 게시 점검 통과 → allbirds.com(MCP, 2026-08-25) 협상·검색 성공, 응답 스키마 검증 통과(요청 전 준비한 검증기), 상품 5개(USD) → 원화 카드 0개(설계대로). 로그 `Claude outputs/ucp_live_search_p46_20261106.txt`.
- 다음: 공통 검색(collect) 연결 검토 — 국내 원화 UCP 판매자가 없어 화면 효과는 없음.

## p47 — GPT 검토(11-06 17:25) 반영: 포함 리소스 · 원화 공통 경로 연결 검증 (2026-11-06)
백업 `recipe_chat_api_backups/20261106_p47_ucp_embedded_common_path/` (before/·p47.diff·README.md·테스트 로그·mutation_check). 커밋하지 않음. **앱 경로는 계속 미연결.**
- **스키마 포함 리소스**: 받은 문서 안의 `$id`(중첩 포함) 주소를 가리키는 참조는 외부 GET 하지 않음(`embedded_ids`). 받은 문서를 모두 훑은 뒤 외부 후보를 가져오고, GET 실패는 끝까지 본 뒤 판정(뒤 문서에 포함된 리소스면 실패 아님). 포함 리소스를 절대 주소로 registry 등록(`_subresources`). GPT 재현(`nested.json#x`, 별도 주소 404) 통과 · GET 은 루트 1회. 진짜 외부 누락은 그대로 보류(POST 0회).
- **원화 공통 경로 검증**: `collect(extra_cards=...)` 검증용 입구(앱 코드는 넘기지 않음 — 테스트로 고정) → 실제 client.search·cards_from 결과가 쿠팡 결과와 함께 enrich·관련성 필터·choose·공통 모델(to_item)까지 지남. 연결해 보며 막은 곳 3곳: ① KAMIS 시세가 상품명 수량('30구')으로 UCP 카드와 견줄 수 있음 → 차단 카드 제외 ② 상품명 개수('10입')가 unit_count 로 남아 '상품명 표기 기준 비교 허용' 근거로 나감 → 비움 ③ 공통 모델 변환에서 seller_unit_price·판매자 고지·출처가 사라짐 → `method="ucp_catalog"` 근거로 보존.
- **근거 정책 ucp_catalog**: 표시 allow_labelled('판매자 표시 (UCP 카탈로그)') · 거르기 hold · 가격 비교 block · 점수 block. 기존 판정 그대로, POLICY_VERSION → evidence-usage/2026-11-06. UCP 카드가 있으면 경고 한 줄(카탈로그 가격·결제 화면 기준·단위가격 미비교).
- 확인: key 변환 == 공통 모델, 판매자 단위가격 '100g당 630원 (판매자 표시)' 그대로, 가성비·넉넉한 양은 쿠팡 카드끼리, 단위가격·상품명 숫자를 바꿔도 역할·순서 동일, 출처 실패 시 쿠팡 결과 그대로, extra_cards 없으면 결과 완전 동일.
- 검증: UCP 139 passed(+17), 맥 ucp·chat·public_price·mcp·공개보호 693 passed / 1 failed(기존 dev-trace), 전체 5,450 passed / 기존 7 failed(+ 실행 사본에 .git 이 없어 생긴 1개 — 맥 원본에서 통과). 수정 하나씩 되돌리기로 각 테스트가 잡는지 확인(unit_count 는 처음에 놓쳐 사례 추가). allbirds 실제 검색 다시 통과.
- **연결 전 남은 결정**: UCP 카드는 배송비 미상(total 없음) — 비교 가능한 중량 후보가 2개 미만이면 '최저가'를 상품 가격으로 고르는 기존 규칙이 UCP 카드에도 적용됨. 배송비 미상 판매처를 최저가 후보에 둘지 결정 필요. 원화 국내 UCP 판매자 확보.
