# p40·p41(·p42) UCP 카탈로그 어댑터 — 구현 검토 자료 (2026-11-05)

대상: `app/services/ucp/` (p40 새 파일, p41 검토 반영), 점검 스크립트 3개, `make_ucp_profile.py`(p42 보완), 생성 프로필 `Claude outputs/ucp_site/`. 모두 **미커밋·미연결·기본 꺼짐**.
이번 묶음은 **읽기 전용 확인**입니다. 검토 의견 3항목과 단위가격 소비 경로를 코드에서 실제로 재현했고, 고칠 내용은 6장 설계안에만 적었습니다(코드 변경 없음).

## 1. 판정 요약

| 항목 | 지금 코드 | 검토 의견과 일치 |
|---|---|---|
| 검증기 없음 | `schema_valid=None`이어도 `ok=True` → 카드 변환까지 진행. `jsonschema`·`referencing`은 `requirements.txt`에 없음 | 예 — 결과 제공 보류 필요 |
| 스키마 확보 시점 | 응답을 받은 **뒤** 스키마를 가져와 검증 | 사양 "Platforms MUST fetch and compose schemas … before making requests" 와 순서가 다름 |
| 프로필 캐시 | `max(60, min(max-age, 86400))`, `no-store`·`private`·`no-cache` 무시, 헤더 없으면 3,600초. 스키마 캐시는 TTL 없음 | 예 — 60초 하한은 판매자가 **플랫폼** 프로필을 가져올 때 규칙. 플랫폼이 판매자 프로필을 가져올 때는 "cache according to HTTP cache-control directives"(SHOULD) |
| 게시 조건 | `check_published_profile`: 우리 프로필에 `public`+`max-age≥60`, `private/no-store/no-cache` 금지 | 별개 로직으로 이미 분리돼 있음. 사양 Hosting 규정과 일치 — 유지 |
| 판매 단위 | `sold_each` = unit `C62`이고 scale 0/없음. **increment 무시** → "C62, increment 6"도 한 개 가격 카드 | 예 — 코드 주석·문서의 "0.25 lb 단위 판매" 설명은 scale을 주문 간격처럼 씀. 사양: scale = 한 단계가 10^-scale 단위, 주문 간격 = increment (예: scale 2 + increment 25 → 0.25 배수) |
| 단위가격 → 비교 입력 | 카드에 `per100g`(판매자 값)과 `score_use='block'`. `score_use`를 읽는 코드 없음. `explain.choose`는 `per100g`로 '가성비' 역할 선택, `explain.enrich`는 `per100g`를 상품명 중량으로 **재계산하거나 None으로 덮어씀** | 예 — 보존과 비교 입력은 별도 결정. 지금은 공통 검색에 연결돼 있지 않아 실제 영향 없음 |
| 테스트 | ucp 77 passed. ucp·chat·mcp 609 passed / 1 failed(기존 dev-trace) | 보고값과 같음 (2026-11-05 재실행) |
| 생성 프로필 | 보관된 ucp.dev 2026-08-25 schema로 `platform_schema` 오프라인 검증 0 오류. `.well-known/ucp` = `ucp-profile.json` 동일 | 스키마 통과 ≠ 실제 협상·검색 성공 (게시 후 확인) |

## 2. 재현 결과 (`findings/probe_p41_findings.txt`)

`findings/probe_p41_findings.py`를 저장소 루트에서 실행. 저장소 파일을 바꾸지 않음.

- 검증기 없을 때: `validate_search_response` → `(None, ['jsonschema 없음 — 응답 스키마 검증 안 함'])`. `client.search`는 None이면 `ok`를 바꾸지 않음(client.py 103~110행). `check_ucp_catalog.py`는 "검증 안 함" 출력 후 `mapping.to_cards` 진행.
- 프로필 캐시: `max-age=10`→60초, `public, max-age=30`→60초, `private, max-age=5`→60초, `no-store`→3,600초, `no-cache`→3,600초, 헤더 없음→3,600초, `max-age=600`→600초.
- 판매 단위(`mapping.sold_each`): 없음→카드, C62→카드, **C62+increment 6→카드**, LBR scale 2 (+increment 25 유무)→제외, KGM→제외.
- 단위가격: `explain.enrich` 후 `per100g` 500 → None(상품명 중량 없음) / 1,000(상품명 "1kg", 재계산). enrich 없이 `choose`에 넣으면 `per100g` 낮은 쪽이 'value' 역할 — `score_use='block'`과 무관.

## 3. 사양 원문 확인 (ucp.dev/2026-08-25/specification/overview, 2026-11-05)

- Negotiation › Platform Requirements: "Platforms MAY fetch the business profile … If fetched, platforms SHOULD cache the profile according to HTTP cache-control directives." / "Platforms MUST fetch and compose schemas for negotiated capabilities before making requests."
- Profile Requirements › Hosting(게시하는 쪽): "MUST include a Cache-Control header with public and max-age of at least 60 seconds … MUST NOT be served with private, no-store, or no-cache"
- Profile Requirements › Fetching("Businesses fetch platform profiles …"): "Implementations SHOULD cache profiles with a minimum TTL floor of 60 seconds, regardless of the origin's Cache-Control headers." — p41의 "최소 60초"는 이 절을 플랫폼 쪽에 옮겨 적용한 것.
- Schema Composition: "Platforms MUST resolve schemas client-side by fetching and composing base schemas with active extension schemas." Resolution Flow: Fetch → Version Compatibility → Compose → Validate.
- shopping/types/variant.json · common/types/unit.json · quantity_unit.json(보관 fixture): price = `quantity_unit.unit` 한 단위당 가격. scale = "One step equals 10^-scale of unit" (C62면 0). increment = "Ordering granularity, denominated in steps … Advisory merchandising policy".

## 4. 묶음 내용

| 폴더 | 내용 |
|---|---|
| `code/` | 현재 소스: `app/services/ucp/*.py`, `check_ucp_catalog.py`, `check_ucp_profiles.py`, `make_ucp_profile.py`, `tests/services/ucp/`(fixture·보관 schema 25개 포함) |
| `diffs/` | `p40.diff`(새 파일), `p41.diff`(p40→p41), `p42_make_ucp_profile.diff`(p41→p42), `p41_before/`(p41 수정 전 파일), `file_hashes.txt` |
| `test_logs/` | p40·p41 당시 전체 테스트 로그(백업 원본), 2026-11-05 재실행: ucp 77개(-v, junit), ucp·chat·mcp(junit). 같은 날 전체 실행 로그는 Brix 검토 묶음(`commerce_ai_brix_review_2026-11-05.zip`) 참고 — 같은 작업 폴더 상태 |
| `profile/` | 생성 프로필 사이트 사본(`ucp_site/`), 오프라인 schema 검증 스크립트·결과 |
| `findings/` | 재현 스크립트·결과 |

## 5. 그대로 둔 것

- 게시 조건 검사(`check_published_profile`)의 `public`+`max-age≥60` — 우리 프로필 게시 규정으로 맞음.
- `quantity_unit`이 C62가 아닌 상품을 카드에서 빼는 보수적 처리 — 유지.
- 검색 응답은 지금 캐시하지 않음(가격 재사용 없음) — 연결 단계에서 정책 결정.

## 6. 수정 설계안 (미적용, 결정 후 반영)

### 6-1. 검증기 없음 → 결과 제공 보류
- 스키마 확보·합성을 **요청 전에** 수행: 협상한 catalog.search schema(판매자 선언 URL 또는 사양 기본)를 가져와 검증기 준비. 실패하면 검색하지 않음(`schema_unavailable`).
- 검증기 자체가 없으면(`ImportError`) `ok=False`, `code='schema_unverified'`. 원문 응답은 진단용 필드(`diagnostic_response`)에만 남기고 `response`는 비움 → `to_cards`가 호출되지 않음. `check_ucp_catalog.py`는 진단 출력만.
- `requirements.txt`에 `jsonschema`·`referencing` 추가(버전 고정) — 결정 필요.

### 6-2. 캐시 구분
- 판매자 프로필 캐시: 원본 Cache-Control 준수. `no-store` → 저장 안 함, `no-cache`·`private` → 매번 다시 가져옴(또는 ETag 재검증), `max-age` → 그대로(늘리지 않음, 상한 86,400 유지), 헤더 없음 → 기본값 결정 필요(제안: 저장 안 함 또는 짧게).
- 스키마 캐시: 판 경로가 고정된 `ucp.dev/<판>/` 은 길게, 판매자 호스트 schema는 Cache-Control 준수 + TTL.
- 게시 조건 검사는 지금 그대로(별개 함수).
- 가격 응답 재사용 금지·재검증 규칙은 연결 단계에서 따로.

### 6-3. 판매 단위 설명·판정
- 주석·문서: "scale = 수량 표현 정밀도(한 단계 = 10^-scale 단위), increment = 주문 간격(단계 수의 배수)"로 고침. "0.25 lb 단위 판매"는 "lb당 가격, scale 2·increment 25면 0.25 lb 배수로 주문"으로.
- `sold_each`: unit C62 + 유효 scale 0 + **유효 increment 1**일 때만 한 개 가격 카드. C62 + increment>1은 지금처럼 제외(사유 "N개 단위 주문 — 한 개 가격 아님", 원문 보존).

### 6-4. 판매자 단위가격 보존 ≠ 비교 입력
- 카드 필드 분리: `seller_unit_price`(원문 그대로, 표시 전용) / `per100g`(비교 입력). UCP 카드는 결정 전까지 `per100g = None`.
- 연결 단계에서: `explain.enrich`가 UCP 카드의 단위가격을 재계산·덮어쓰지 않도록 분기, `explain.choose`가 `score_use='block'` 카드를 역할 선택(가성비·넉넉한 양) 비교에서 빼거나 표시만 하도록.
- 연결 전 테스트: UCP 카드를 섞은 `collect`→`choose` 결과에서 역할·순서가 UCP 카드 단위가격에 영향받지 않음을 고정.

## 7. 다음 순서 제안

6장 결정 → 반영·테스트 → 묶음 재제출 → HTTPS 게시(trendguide.kr, Cloudflare Pages) → `check_published_profile` → `check_ucp_catalog.py`로 allbirds 실제 검색 확인 → 공통 검색 연결 여부 결정.
