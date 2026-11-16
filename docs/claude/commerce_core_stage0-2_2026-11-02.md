# commerce_ai 공통 계약·서비스 경계 (0~2단계) — 2026-11-02

설계서: "commerce_ai 프로토콜 연계 설계서 (UCP·MCP)" (GPT 검토 반영본). 기존 파일 수정 없음, 새 파일만 추가. 커밋하지 않음.

## 0단계: 확인한 호출 관계
- `POST /api/chat` (app/api/chat_routes.py) → `ChatService.handle` (app/services/chat/service.py)
- 쇼핑 턴 `_shopping_turn`: `parse_budget/strip_budget` → `shopping_terms` → `default_shopping` = `app.main.natural_language_recommendations` (run_recommendation_pipeline v8, 실패 시 DB fallback) → `item_to_card` + `explain.enrich` → `relevant` 필터 → 업체 제공(partners.feed, compare/list) → 쇼핑커넥트 등록부(`connect_links`, 주류 질문 제외) → **`explain.choose`(역할별 선택이 순위를 정함)** → `kamis.annotate`(시세 참고, 순위 무관)
- 레시피: `RecipeChat` → `RecipeResolver.get(id)` / `.find(text)` (Finding: card/choose/none), `catalog_recipe` / `ai_suggested_recipe`(source_level=ai_suggestion)
- 링크: `/go/{sid}/k/{key}` (세션에 보여 준 카드만), 쇼핑커넥트는 발급 링크 직접 이동 + `/api/click` 기록

## 1~2단계: 추가한 파일
| 파일 | 내용 |
|---|---|
| app/domain/commerce/models.py | Product · Offer(platform/merchant/product_url 분리, 배송비 미확인=None) · Evidence(method·status·usable_for_score) · ScoreDetail(rank·role·reasons·engine_score 있을 때만) · Disclosure · RecipeItem · Followup · CommerceResult(schema_version commerce.v1, status ok/empty/needs_followup/held/partial/error) |
| app/domain/commerce/requests.py | SearchRequest · RecipeRequest |
| app/domain/commerce/policies.py | 쿠팡·쇼핑커넥트 고지 + 운영 문구, 주류 규칙(기존 함수 위임), safe_url, score_usable(html·ocr 값은 점수 불가) |
| app/services/commerce/search.py | `collect()`: 쇼핑 턴과 같은 함수·순서 / `search_products()` → CommerceResult |
| app/services/commerce/recipes.py | `get_recipe()` — id 또는 요리명, 여러 후보면 needs_followup |
| tests/services/chat/test_commerce_contract.py | 20개 계약 테스트 |

## 필드 매핑 (기존 카드 → 공통 모델)
mall→Offer.platform · source/seller_name→merchant(mall과 같거나 '판매처'면 None) · url→product_url(safe_url) · price/shipping_fee/total→*_krw · per100g/per_unit · rocket/free_shipping · affiliate/affiliate_program/direct→link_type·opens_directly · key/pid/title/image/weight_g/unit_count/seller_claims→Product · rank/role/role_label/why→ScoreDetail · market_ref→price_reference · rating/review_count→Evidence(method=unknown, 점수 불가) · 파이프라인 final_score→engine_score(있을 때만)

## 검증
- 계약 테스트 20 passed (5개 문장에서 웹과 상품·순위·역할·사유 일치, 제휴 여부를 뒤집어도 순위 동일, 주류 시 쇼핑커넥트 없음, 판매처 장애 시 error, 레시피 id·이름 조회, domain이 fastapi/mcp를 import하지 않음)
- 일부러 순서를 뒤집으면 5개 실패 → 테스트가 실제로 잡아냄 확인
- 전체 5,033 passed / 8 failed — 8개 모두 이번 작업과 무관(이전부터 실패: .env 개발 추적, 작업 트리 상태 검사, seafood·f2a·i5b, 그리고 test_surge가 실제 var/blog_drafts 파일 삭제를 시도하다 차단됨)
- 실행 환경: 맥 .venv가 아닌 별도 Linux Python 3.10 + requirements.txt

## 다음
- 3단계: `_shopping_turn`이 `services/commerce/search.collect()`를 쓰도록 교체 (기존 파일 수정 → 승인 후)
- 4단계: `/mcp` + 테스트 키 + 1차 도구 2개(food_search_products, food_get_recipe)
- 확인 필요: 평점·후기 값의 출처(API/페이지 수집), 제휴 링크의 AI 에이전트 경유 허용 여부

---

## 검토·OCR 상세 보완 — 2026-11-02

### A. 검토 결론과 증거 범위

앞부분은 클로드가 작성한 구현 보고 원문이다. 이번 검토는 첨부된 요약 문서를 대상으로 하며, 저장소 소스·diff·실행 로그·테스트 산출물은 제공되지 않았다. 따라서 파일 존재, 실제 호출 관계, 20개 계약 테스트 및 5,033개 통과 수치는 **클로드 보고값**으로 기록한다. 이번 검토에서 해당 결과를 재실행하거나 독립 확인한 것은 아니다. 다음 OCR 내용은 **추가 설계·작업 요구사항**이며 구현 완료 보고가 아니다.

| 검토 항목 | 판정·보완 요구 |
|---|---|
| 공통 모델·기존 서비스 wrapper 방향 | 타당한 방향. 다만 기존 동작 보존은 실제 diff와 비교 실행으로 확인해야 한다. |
| 최종 순위 | 보고된 경로상 `explain.choose`가 역할별 선택과 최종 노출 순서를 정한다. 엔진 final_score와 최종 표시 rank를 같은 의미로 취급하면 안 된다. 필터·파트너 병합·역할 선택 전후의 상품 식별자와 순서를 비교해야 한다. |
| 단계 0~2 완료 | 구현 보고 접수 수준. 기존 versioned envelope와의 호환성 및 소스 검증이 남아 있어 최종 계약 확정으로 확대하지 않는다. |
| `commerce.v1`·상태 6종 | 현재 구현안으로 표시한다. 기존 READY/EMPTY/HELD 제안과 의미·변환 규칙을 대조한 뒤 공개 계약을 결정한다. 내부 이름만으로 기존 설계가 채택·폐기되었다고 해석하지 않는다. |
| Product·Offer | 로컬 key/pid를 canonical Product/Offer ID로 승격하지 않는다. 플랫폼·입점 판매자·옵션·판매조건 식별과 실제 발급 책임은 별도 확인 대상이다. |
| `Evidence.usable_for_score` | bool 하나만으로 사용 범위를 결정하기 부족하다. 원문 상태, 필드별 검증, 표시·필터·점수 사용 목적, 적용 정책 버전을 구분한다. |
| `score_usable(html·ocr 값은 점수 불가)` | 현재 단계의 보수적 차단 정책으로 유지한다. OCR 성공을 점수 허용으로 연결하지 않는다. 향후 검증된 필드의 허용은 별도 정책 변경과 회귀 검증이 필요하다. |
| rating/review_count 출처 unknown | 점수 차단은 타당하나 기존 엔진이 같은 값을 이미 사용하는지 추적해야 한다. 새 Evidence 표시만으로 기존 소비가 차단되었다고 주장할 수 없다. |
| 제휴 여부 뒤집기 테스트 | 해당 fixture의 순위 불변 근거다. 전체 경로의 제휴 영향 부재나 모든 후보의 동일성을 입증하지는 않는다. |
| 웹·서비스 일치 | 5문장 비교 범위를 넘는 전체 동등성은 미확인이다. 상품·옵션·가격·링크·점수·고지·후속 질문·부분 실패를 확장 비교한다. |
| 판매처 장애 시 error | 전체 판매처 실패와 일부 실패를 구분한다. 쓸 수 있는 결과가 있으면 partial을 검토하고 실패한 출처·누락 범위를 명시한다. |
| 기존 실패 8개 | 작업 무관이라는 판정은 동일 환경의 변경 전/후 실행으로 확인한다. Linux 결과를 Mac 운영 환경 통과로 대체하지 않는다. 파일 삭제를 시도하는 테스트는 임시 디렉터리에서 격리한다. |
| 링크·클릭 | 링크 생성, 서버 경유, 클라이언트 클릭 신고, 실제 화면 노출, 구매를 별도 사건으로 유지한다. 직접 링크는 집계 누락 가능성이 있다. |

이 보완은 O1 owner 미확립, O3 exposure 미검증, O4 배포 계보 미확인 및 기존 고정 보류 경계를 해소하지 않는다. 문서 보완을 REST 교체·MCP 공개·Tier A 구현 승인으로 해석하지 않는다.

### B. OCR의 목적과 현재 상태

OCR의 목적은 **상품 상세페이지에서 API·HTML 텍스트로 확보하지 못한 필요한 정보만 이미지에서 읽고, 원문 증거와 연결해 보존하는 것**이다. 상세페이지 전체를 무조건 OCR하거나 읽은 문구를 즉시 사실로 확정하는 기능이 아니다.

기존 대화에서 상세페이지 확인과 필요한 영역 OCR은 필수 요구사항이었다. 그러나 이 첨부 문서에는 실제 수집기, OCR 엔진, 이미지 영역 추출, 증거 저장소, 충돌 처리 및 테스트의 구현 근거가 없다. 현재 확인 가능한 것은 Evidence 필드와 HTML/OCR 점수 차단 정책을 추가했다는 보고뿐이다. **OCR 미구현 확정도, 구현 완료 확정도 하지 않으며 소스 확인이 필요하다.**

우선 추출 대상은 상품 비교와 구매 판단에 필요한 다음 필드로 한정한다.

| 정보 | 추출·검증 시 주의점 |
|---|---|
| 순중량·내용량·팩 수·입수 | 1팩 용량, 총중량, 고형량, 용기 포함 무게를 구별한다. `500g × 2팩`과 `총 500g, 2팩`을 혼동하지 않는다. |
| 판매 옵션 | 상세페이지 공통 이미지가 현재 선택 옵션을 설명하는지 확인한다. 옵션 미연결이면 가격·단위가격 계산을 보류한다. |
| 원재료·함량 | 원재료 전체 목록과 홍보용 강조 문구를 구분하고, 포함 관계·괄호·백분율을 보존한다. |
| 알레르기 표시 | 함유, 같은 제조시설, 미표시, 판독불가를 구분한다. 표시가 없거나 읽지 못한 경우를 알레르기 없음으로 바꾸지 않는다. |
| 원산지·제조사·판매원 | 상품명·브랜드·판매자와 구별하고 적용 원재료와 범위를 보존한다. |
| 보관·해동·조리 조건 | 냉장·냉동·실온, 개봉 전후 조건을 구분한다. 광고 문구로 실제 배송 온도를 추정하지 않는다. |
| 소비기한·제조일 | 예시 사진의 날짜와 실제 출고분의 보장 정보를 구별한다. `제조일로부터 N개월`은 실제 제조일 없이는 만료일로 확정하지 않는다. |
| 배송비·도서산간·배송일 조건 | 지역·수량·금액·회원조건·기준 시각을 연결한다. 이미지 안내만으로 실시간 결제 총액을 확정하지 않는다. |
| 인증·등급·영양정보 | 인증 표시를 읽었다는 사실과 유효성 조회를 구분한다. 영양값은 100g/1회/총내용량 기준을 보존한다. |

### C. 상세페이지 → OCR → 서비스의 처리 순서

1. **대상 고정:** 요청의 상품 URL, 플랫폼, 판매자, 옵션, 수집 목적과 필요한 필드를 기록한다. 기존 Product/Offer 연결은 확인된 로컬 참조를 쓰며 canonical 발급을 새로 가정하지 않는다.
2. **접근 가능 조건 확인:** 이용 조건·수집 허용 범위·인증 필요 여부를 확인한다. 차단·로그인·캡차를 우회하지 않는다. 수집 불가와 상품 정보 없음은 별도 상태다.
3. **HTML 우선:** API 필드, 구조화 데이터, HTML 텍스트, 이미지 설명을 확인한다. 같은 정보가 이미지에 반복되어 있어도 OCR을 중복 실행하지 않는다. 동적 로딩이나 옵션 변경으로 누락되는 내용은 구별해 기록한다.
4. **필요 이미지 선택:** 상세 이미지 중 내용량·원재료표·배송 안내 등 필요한 영역을 선택한다. 이미지 URL·순번·원본 크기·해시와 현재 옵션 연결 근거를 남긴다.
5. **영역 처리:** 긴 이미지 분할, 회전·확대 등 전처리를 수행하면 원본과 변환 관계를 기록한다. OCR의 bbox를 원본 이미지 좌표로 되돌릴 수 있어야 한다. 표의 행·열과 단위가 끊기지 않도록 인접 영역도 확인한다.
6. **텍스트 추출:** 원문 텍스트·줄/표 구조·좌표를 저장한다. 엔진명·버전·처리 시각을 남긴다. 엔진이 신뢰도를 제공하지 않으면 null로 두며 임의 점수를 만들지 않는다. 비전 LLM을 쓰면 모델·프롬프트 버전과 비용도 기록하고 전사와 해석을 구분한다.
7. **필드 해석:** OCR 원문에서 값·단위·적용 옵션·조건을 구조화한다. `O/0`, `1/l`, `g/kg`, 소수점, 곱셈 기호 오류를 검토한다. 원문을 정규화값으로 덮어쓰지 않는다.
8. **대조·판정:** API·HTML·다른 이미지와 비교한다. 출처가 다르다는 이유만으로 최신값이나 우선값을 자동 확정하지 않는다. 옵션 불일치·시점 차이·모순을 conflict로 남긴다.
9. **파생값 계산:** 동일 옵션의 검증된 수치만 사용한다. 계산식, 입력 evidence 참조, 단위·반올림 규칙을 기록한다. 총액은 배송비·조건이 확인된 범위에서만 계산한다.
10. **사용 정책 적용:** 표시, 구매 필터, 알레르기 판단, 단위가격 비교, 추천 점수별 허용 여부를 각각 판정한다. 현 단계에서는 HTML/OCR의 점수 입력 차단을 유지한다.
11. **응답·후속 질문:** 검증된 값과 미확인·충돌 값을 분리해 REST/MCP projection에 전달한다. 필수 조건을 판단할 수 없으면 이유를 설명하고 옵션·용량 등의 확인 질문 또는 보류 결과를 반환한다.

상세페이지·이미지·OCR 문구는 외부 데이터다. 문구 안의 명령이나 링크 지시가 서비스 정책·도구 호출·시스템 지침을 바꾸지 못하도록 한다.

### D. 증거 모델 보완안

아래는 제안 필드다. 기존 모델의 필드명·타입·저장 방식과 대조한 뒤 additive하게 반영하며 공개 wire 계약으로 바로 확정하지 않는다.

| 구분 | 필드 예시 | 목적 |
|---|---|---|
| 연결 | evidence_id, local_product_ref, local_offer_ref, selected_option_ref | 어떤 상품·옵션의 증거인지 추적 |
| 출처 | page_url, image_url, image_index, collected_at | 원문 위치와 수집 시점 |
| 재현 | asset_hash, snapshot_ref, original_dimensions, bbox, coordinate_space | 원본과 읽은 영역 재확인 |
| 추출 | method, engine_version, extracted_at, preprocessing, confidence | 추출 방식과 한계 기록 |
| 원문 | raw_text, raw_field_text | 정규화 이전 내용 유지 |
| 정규화 | field_name, normalized_value, unit, scope, parser_version | 값·단위·적용 범위 분리 |
| 검증 | extraction_status, validation_status, validation_method, conflict_refs, reviewed_at | 추출 성공과 사실 검증 구분 |
| 사용 정책 | usage_decisions, policy_version, reason_codes | display/filter/price_compare/score 등의 허용·보류·차단 사유 |
| 파생값 | derived_value, formula_version, input_evidence_refs | 단위가격 등 계산 근거 |

`collected_at`은 판매자가 해당 정보를 갱신한 시각이 아니다. 엔진 confidence는 사실의 정확성·최신성·법적 유효성을 보장하지 않는다. Evidence ID 역시 canonical Product/Offer ID 발급 책임을 대신하지 않는다.

추출 상태 예: NOT_ATTEMPTED / EXTRACTED / UNREADABLE / FAILED / ACCESS_BLOCKED.
검증 상태 예: UNVERIFIED / VALIDATED / CONFLICT / REVIEW_REQUIRED / STALE.
이 명칭은 내부 설계 제안이며 기존 CommerceResult.status와 별도다. VALIDATED를 부여할 검증 절차·담당 책임·정책 버전이 먼저 필요하다.

### E. 정규화·계산 예시

**예시 1: `500g × 2팩`, 선택 옵션과 일치**

- OCR 원문은 그대로 보존한다.
- 1팩 500g, 수량 2, 총내용량 1,000g은 입력 증거와 계산식 `500 × 2`를 연결한다.
- 동일 옵션 상품가가 12,000원으로 확인되면 상품가 기준 100g당 1,200원이다.
- 배송비 미확인이면 배송 포함 총액과 배송 포함 단위가격은 미확인으로 둔다. 무료배송으로 간주하지 않는다.
- 현재 정책에서는 이 OCR 값의 점수 사용은 차단한다. 표시·비교 사용도 검증 및 해당 용도의 정책 허용이 선행되어야 한다.

**예시 2: API `1kg`, 이미지 `500g`, 옵션 연결 불명**

- 값 둘을 모두 보존하고 CONFLICT 또는 REVIEW_REQUIRED로 둔다.
- 더 유리한 단위가격을 만들기 위해 임의로 1kg을 선택하지 않는다.
- 구매 비교에서 해당 단위가격을 보류하고 옵션을 확인한다. 기존 엔진 점수는 별도 provenance로 유지한다.

**예시 3: 알레르기 표의 일부 글자가 판독 불가**

- 원문 영역과 판독 불가 부분을 남긴다.
- 누락을 `없음`으로 바꾸지 않는다. 알레르기 조건 충족 여부는 판단불가로 반환한다.
- 기존 알레르기 정책과 실제 소비 경로를 조사하기 전 새 필터가 적용되었다고 보고하지 않는다.

### F. 공통 서비스·REST·MCP 연결 요구

OCR은 transport 바깥의 공통 처리로 두고, REST와 MCP가 각자 추출하거나 충돌을 다르게 해결하지 않도록 한다. 기존 `/api/chat`을 교체하기 전에 공통 결과를 생성해 기존 화면 결과와 비교하는 검증 경로를 마련한다.

권장 책임 분리(파일명은 제안):

- 상세페이지 접근·HTML 추출: 수집 어댑터.
- 이미지 영역 선택·OCR 호출: 추출 서비스.
- 수치·단위 정규화: 정규화 서비스.
- 증거·원문·충돌 보존: evidence 저장소.
- 필드별 사용 판정: 확인된 공통 정책.
- 공통 서비스: 허용된 증거와 기존 추천·레시피 기능 조합.
- REST/MCP projection: 동일한 의미를 각 응답 형식에 투영.

검색 후보마다 무조건 OCR을 실행하지 않는다. 필요한 비교 필드가 누락된 후보를 대상으로 예산·시간 제한 안에서 처리한다. 같은 이미지 해시·영역·엔진·설정의 결과는 재사용하되, 정책이 바뀌면 사용 판정을 다시 한다. 가격·배송·옵션과 정적 원재료 이미지의 갱신 기준을 동일하게 가정하지 않는다.

동기 호출에서 제한을 넘으면 확인된 검색 결과와 미완료 증거 상태를 반환하는 방식을 검토한다. 비동기 작업·job ID는 기존 계약과 저장 구조를 확인한 뒤 결정한다. OCR timeout이 기존 추천 전체를 반드시 실패시키게 하지 않는다.

최종 화면에 설명을 붙이더라도 OCR 성공이나 추천 응답 생성을 실제 노출·클릭 사건으로 기록하지 않는다. 외부 에이전트에 고지를 제공한 사실과 최종 사용자에게 표시된 사실도 구분한다.

### G. 검증 시나리오와 완료 기준

실제 수집 없이 재현 가능한 HTML·이미지 fixture로 우선 검증하고, 허용된 실제 페이지에서 별도 통합 검증한다.

| 시나리오 | 통과 기준 |
|---|---|
| HTML에 필요한 값 존재 | 해당 필드 때문에 OCR을 중복 호출하지 않음 |
| `500g × 2팩` / `총500g 2팩` | 각각 총1,000g / 총500g으로 구분하며 근거 보존 |
| 옵션 공통 이미지 | 선택 옵션과 연결 불가하면 단위가격 계산 보류 |
| API·HTML·OCR 충돌 | 값·증거를 보존하고 임의 덮어쓰기 없음 |
| 작은 글씨·회전·분할 표 | 원문 좌표 복원 가능, 판독불가를 정상값으로 채우지 않음 |
| 알레르기 함유/시설/미표시 | 세 상태를 구분하고 미표시를 안전 판정으로 변환하지 않음 |
| 배송비 미확인 | total을 상품가와 같게 확정하지 않음 |
| 오래된 가격·예시 날짜 | 수집 시각과 유효 기준 구분, 필요 시 재검증 |
| OCR 실패·호출 제한·접근 차단 | 원인 구분, 가능한 기존 결과 유지, partial/held 등의 매핑 확인 |
| 재요청·캐시 | 동일 자산의 불필요한 재호출 방지, 옵션·정책 변경 시 오용 없음 |
| 점수 차단 | 미검증 HTML/OCR 값이 실제 엔진 입력·필터·역할 선택을 통해 우회 반영되지 않음 |
| 기존 순위 보존 | 엔진 결과와 `explain.choose` 이후 표시 순서를 각각 비교 |
| REST/MCP | 동일 증거·상태·수치·고지의 의미 일치 |
| 비용·시간 | 이미지 수·처리량·엔진 버전·실측 사용량 기록. 미제공 토큰·비용은 추정값으로 분리 |

OCR 1차 완료 조건은 ① 실제 구현 경로 확인, ② 원문과 영역 추적, ③ 필드별 검증·충돌 보존, ④ 점수 차단 유지, ⑤ 위 핵심 fixture 통과, ⑥ 기존 추천·레시피·저장·링크 흐름의 회귀 확인이다. 정확도 수치나 자동화 범위를 주장하려면 별도의 정답셋과 측정 범위를 제시해야 한다.

### H. 클로드에 전달할 다음 작업

1. 이번 보고에 언급한 추가 파일 diff, 실제 호출 함수 위치, 변경 전/후 테스트 결과를 제출한다. 비밀키·개인 세션 데이터는 포함하지 않는다.
2. OCR·상세페이지 수집 관련 기존 코드를 읽기 전용으로 찾아 구현 여부와 호출 경로, 저장 구조, 엔진·비용 계측을 보고한다. 검색 범위에서 못 찾은 사실을 전체 미존재로 일반화하지 않는다.
3. 기존 Evidence와 위 제안의 필드 대응표 및 빠진 항목을 만든다. 기존 envelope·Product/Offer·score provenance의 고정 보류 항목을 임의 확정하지 않는다.
4. 기존 OCR 경로가 있으면 먼저 wrapper와 fixture로 검증한다. 없다면 필요한 필드와 허용된 소스 하나를 대상으로 추출→원문 보존→정규화→검증까지 범위를 좁혀 구현안을 제시한다.
5. 현재 `html·ocr` 점수 차단은 유지하고 표시·비교 사용도 용도별 근거를 기록한다. 검증되지 않은 값으로 필터·역할 선택·순위가 우회 변경되는지 확인한다.
6. 위 결과를 검토한 뒤 REST 호출 교체와 MCP 도구 두 개 연결을 진행한다. 이번 문서 보완만으로 코드 변경·배포·공개가 승인되었다고 기록하지 않는다.

이 문서는 프로토콜 버전·SDK 지원 조합·사이트별 수집 허용 여부를 새로 검증한 보고서가 아니다. 해당 사항은 실제 연결·수집 대상이 정해지는 시점에 공식 자료와 현재 환경으로 확인한다.

---

## 클로드 응답 — H.1~H.3 1차 제출 (2026-11-02 21:46)

코드 패키지 `commerce_ai_generator_review_2026-11-02.zip`(사용자 맥 `commerce_ai_generator/Claude outputs/`)에 diff·호출 위치·전/후 테스트를 넣었다. 상세는 패키지의 `_review/README_REVIEW.md`.

- **변경 전/후 동일 환경 실행:** Linux VM 복사본에서 before 11 failed / 5,010 passed → after 11 failed / 5,030 passed. 실패 목록 동일, 증가분 20개 = 계약 테스트. 맥 운영 환경(.venv)은 미실행.
- **test_surge 위험:** 원래 폴더에서 실제 `var/blog_drafts` 파일 삭제를 시도함(VM 권한으로 차단). 맥에서 실행하면 실제 파일이 지워질 수 있음 → 임시 디렉터리 격리 필요.
- **OCR:** `commerce_ai_local_ocr/`는 Tesseract CLI + 영역 검출 + 선택적 OpenAI 검토로 된 오프라인 도구. app/·scripts/ 어디서도 import 하지 않음(grep 기준), OCR 테스트 없음 → 존재하지만 추천 경로와 미연결.
- **OCR 대상 한정:** 페이지 수집기는 2026-11-02 결정으로 보관·미사용. 상세페이지 OCR은 허락 기록이 있는 출처(업체 제공 이미지 등)로 한정해야 하며, 쿠팡·네이버 페이지를 새로 수집하는 설계가 아님.
- **평점·후기:** 정식 경로 어댑터 3곳은 raw rating을 계산에서 명시적으로 제외. 상위 popularity_score 생성 경로와 DB fallback(score_engine.py)은 미추적. choose의 남은 자리는 입력 순서를 따르므로 간접 영향 가능성은 남음.
- **wrapper 미포함 경로:** 예산 답변 턴(service.py:370)·관심 상품 비교(:340)도 `explain.choose`를 부름 → 3단계 REST 교체 때 함께 처리.
- **기존 versioned envelope(READY/EMPTY/HELD):** 위치 미확인 → 알려 주면 대조표 작성.
- 이 응답은 REST 교체·MCP 연결 승인이 아님.

---

## p28 — GPT 검증본(Commerce-Core-Stage0-2-Verified) 맥 반영 (2026-11-03)

백업: `recipe_chat_api_backups/20261103_p28_gpt_stage0-2/` (반영 전 models.py·policies.py·search.py, SHA256, 전체 테스트 전/후 로그). GPT 원본 파일: `Claude outputs/gpt_stage0-2_overlay/`. 커밋하지 않음.

**반영 내용(GPT 패치)**
- `ScoreDetail.upstream_scores`(score·final_score·v8/v7_final_score·final_recommendation_score·adaptive_score 중 실제 유한 숫자만, 원래 이름 그대로), `upstream_rank`(상위 item.rank), `fallback_used` 를 bool → Optional(None = 미확인/해당 없음).
- `Provenance.recommendation_path` — main.py 의 실제 분기 태그(canonical_provider / db_fallback; not_called·UNKNOWN 은 fallback_used=None).
- `score_usable` 수정: 기존 함수는 `usable_for_score` 플래그를 보지 않았고 method=unknown 도 verified 면 통과시켰음 → 플래그 + verified + html/ocr/unknown 제외를 모두 요구. (현재 이 함수는 추천 엔진 입력 gate로 호출되지 않음)
- 새 회귀 테스트 `tests/services/chat/test_commerce_provenance.py` 16개.

**병합:** GPT 패치는 p26 이전 판을 기준으로 함. models.py·policies.py 는 GPT 기준 SHA 와 맥 현재가 같아 그대로 적용. search.py 는 p26 의 `found` 와 GPT 의 `recommendation_path` 가 같은 return 줄에 추가되어 3자 병합으로 둘 다 유지.

**검증(Linux VM 복사본, 맥 현재 저장소 기준):** 적용 전 11 failed / 5,044 passed → 적용 후 같은 11 failed / 5,060 passed (+16). 맥 원본 반영 후 관련 테스트(계약·provenance·shopping_reasons·relevance·partner·mcp) 73 passed, 1 skipped. 맥 .venv 미실행.

**GPT 보고서에서 낡은 부분:** "REST ChatService 는 아직 공통 검색 wrapper 를 호출하지 않는다" → p26(11-02 밤)에서 `_shopping_turn` 이 `collect()` 를 쓰도록 이미 교체됨. MCP 로컬 도구 2개도 p26 에서 추가됨(원격 공개 안 함).

**남은 일:** 예산 답변·관심 상품 비교의 choose 경로, provider warnings·engine_version 매핑, Evidence 용도별 판정(display/filter/price_compare/score), OCR bundle → Evidence 연결(허락 출처 fixture 1개부터), 맥 .venv 전체 테스트.

---

## p29 — 재선택 경로 · 근거 용도별 판정 · OCR→근거 연결 (2026-11-03)

백업: `recipe_chat_api_backups/20261103_p29_reselect_evidence_ocr/` (변경 전 원본, SHA256, 작업별 diff, 전체 테스트 로그). 커밋하지 않음.
검증(Linux VM 복사본, 같은 환경): p28 적용 후 기준 11 failed / 5,060 passed (provenance 16개 포함; 처음 기록한 '5,044'는 p28 적용 전 수치를 잘못 옮긴 오기, p30에서 정정) → 작업 1 후 5,065 → 작업 2 후 5,077 → 작업 3 후 **5,087 passed, 실패 11개 목록 동일**. 맥 반영 후 chat·partners 테스트 377 passed (실패 1 = 기존 .env 개발 추적). 맥 .venv 미실행.

### 1. 예산 답변·관심 상품 비교 → 공통 서비스
- 새 `app/services/commerce/reselect.py`: `rechoose()`(저장 후보 사본으로 explain.choose), `compare_saved()`(같은 검색끼리 묶어 2개 이상만 비교), `to_result()`(공통 모델 투영 — recommendation_path·upstream 점수는 재호출 안 하므로 None, "새로 검색하지 않음" 경고).
- `service.py` `_budget_turn`·`_compare_saved_turn` 이 위 함수를 부름 (화면 블록·상태 저장은 그대로).
- **골든 비교** `test_reselect_golden.py` + `fixtures/golden_reselect.json`: 변경 전 코드로 만든 화면 블록 6개 시나리오(예산 5만원·예산 밖·예산 없음·10만원대·관심 비교·빈 보관함)가 변경 후 글자 그대로 같음. 시각(MM/DD hh:mm)만 정규화. 해시 시드 3가지로 안정성 확인.
- 관심 상품(owner 보관함)은 개인 보관 데이터라 MCP·UCP 도구로 열지 않음.

### 2. 근거 값의 용도별 판정 (policy_version `evidence-usage/2026-11-03`)
- `Evidence.usage`: display / filter / price_compare / score 마다 allow · allow_labelled(출처 표기 붙여 사용) · hold · block + 사유 코드. 규칙은 `policies.decide_usage` 한 곳, 검색 결과의 모든 근거에 부착.
- 점수는 허용/차단 둘뿐이며 `score_usable`(p28 의미)과 같은 규칙: 허가 플래그 + 검증 + html·ocr·unknown 아님.
- **현재 동작을 그대로 기록한 것(바꾸지 않음)**: 상품명에서 읽은 중량으로 100g당 비교(explain.choose 가성비)는 price_compare=allow_labelled('상품명 표기 기준') — 미검증 판매자 표기가 역할 선택에 쓰이고 있다는 뜻. 평점·후기(출처 미확인)는 기존 배지 표시만 allow_labelled, 거르기·비교·점수 차단. 쇼핑커넥트 등록부 가격은 비교 차단(별도 목록). 업체 가격 비교는 허락 기록부의 '가격 비교·순위 계산' 허락 때만.
- 우회 검사: 평점·후기를 붙였다 떼도 공통 서비스의 상품·순위·역할 동일 (상위 추천 엔진 내부 소비는 범위 밖).

### 3. OCR 결과 → 근거 연결
- 새 `app/services/commerce/ocr_evidence.py`: commerce_ai_local_ocr 가 만든 `options.json`(옵션별 가격·중량·포장 수량 후보)·`bundle.json`(영역별 원문)을 Evidence 로 변환. OCR 실행·이미지 열기·네트워크 없음.
- **허락 출처만**: 허락 기록부 상태='허락' + 새 열 **'이미지 문자 판독(OCR)'='허용'** 일 때만. '이미지 표시' 허락으로 추론하지 않음. 외부 AI 검토(API_CALLS>0)가 있으면 '외부 AI 전송' 허락도 필요. `feed.FIELDS` 에 ocr 추가 — 열이 없으면 허락 없음. 실제 `data/partners/permissions.csv` 는 수정하지 않음.
- 값은 읽은 그대로(문자열) + 원문(raw_text)·원본 해시·원본 좌표·도구/스키마 기록. 읽지 못한 값은 missing, 도구가 충돌로 표시한 값은 conflict — 채우거나 고치지 않음. 도구 경고(옵션 미확정·가격 역전·부분 영역)는 그대로 전달.
- 판정: 미검증 OCR 값은 표시·거르기·비교 모두 hold, 점수는 검증해도 block.
- 테스트 fixture 는 가상 업체 '예시몰'의 지어낸 값(실제 업체·상품 아님).
- 수정: 충돌 값의 점수 판정이 'hold' 로 나오던 것을 'block' 으로 (점수는 허용/차단만).

### 남은 일
- 사람 확인(검증) 절차: 누가 어떤 근거로 unverified → verified 로 바꾸는지, 기록 위치 — 정해지기 전에는 OCR 값이 화면에 나가지 않음.
- 허락 기록부에 'OCR' 열 추가 여부 결정 및 업체 문의 문구에 포함.
- 상품명 중량 기반 가성비 선택을 유지할지 (현재 '상품명 표기 기준'으로 표기).
- 맥 .venv 전체 테스트.

---

## p30 — GPT 검토(11-03 11:11) 반영: 수치 정정 · 중량 출처 · 기록과 통제 · API_CALLS (2026-11-03)

백업: `recipe_chat_api_backups/20261103_p30_usage_audit_api_calls/`. 검토 패키지: `Claude outputs/commerce_ai_p29_p30_review_2026-11-03.zip` (코드·diff·단계별 테스트 로그). 커밋하지 않음.

- **수치 정정**: p29 기준은 5,060 (p28 적용 후). 단계별 5,060 → 5,065(+5) → 5,077(+12) → 5,087(+10) → p30 5,105. 실패 목록은 p29까지 11개 동일. p30 실행에서는 복사본에서만 실패하던 관리자 테스트 4개가 통과(맥 app/·tests/ 는 p29 이후 변경 없음, 원인 미확인, p30 은 관리자 코드 무수정) → 7 failed.
- **중량 출처 오기 수정**: `explain._amount` 는 상위 결과 `weight_g`(DB 대체 경로 `online_food_price_snapshot.weight_g` 에서만 채워짐)를 먼저 쓰고, 없을 때만 상품명에서 읽음. p29 는 모두 '상품명 표기'로 기록했었음 → 상품명에서 같은 값이 읽히면 title_parse, 아니면 unknown(price_compare=block).
- **기록과 통제**: `Evidence.usage` 를 읽는 선택 코드는 없음(기록일 뿐). `selection_audit()` 가 가성비·넉넉한 양 역할에 비교 허용 전 중량이 쓰이면 경고 — 선택은 그대로(제외 여부는 사용자 결정). OCR 근거는 어떤 app 경로에도 import 되지 않음을 AST 가드 테스트로 고정.
- **API_CALLS**: 정수 0 이상만 신뢰. 키 없음·None·문자열·bool·음수·소수는 '알 수 없음' → '외부 AI 전송' 허락 필요. provenance 에도 0 대신 None.
- **설계서(Claude Docs) 갱신**: 진행 현황 표, 모델 표(upstream_scores·upstream_rank·fallback_used None·recommendation_path, Offer platform/merchant/product_url), OCR 은 검증해도 점수 차단, 기록과 통제의 경계, MCP 로컬만, policies 경로 정정.
- 테스트: test_usage_enforcement 14개 추가. 맥 원본 폴더 커머스 테스트 77 passed. 맥 .venv 미실행.

### 사용자 결정 필요
- DB 대체 경로 중량(출처 미확인)을 가성비·넉넉한 양 선택에서 뺄지
- 사람 검증 절차, 허락 기록부 OCR 열

---

## p31 — 중량 실제 출처 보존 · 비교 후보 감사 · REST 경고 · 미확인 중량 잠정 제외 (2026-11-03)

GPT 검토(13:40) 재현 3건 반영 + GPT·클로드 공통 권고(잠정 제외). 백업 `recipe_chat_api_backups/20261103_p31_weight_source/` (원본 6개, diff, 전후 비교 JSON, 전체 테스트 로그). 커밋하지 않음.

- **실제 출처 보존**: `explain._amount` 가 중량과 함께 출처('title'·'upstream'·None)를 돌려주고 `enrich` 가 카드에 `weight_source` 로 기록. 화면 응답(`_public`)에서는 빼고, 저장 후보(`saved.KEEP`)에는 남김. `search._evidence` 는 숫자 비교 대신 이 기록을 씀 → 상품명과 숫자가 같아도 DB 값을 썼으면 unknown.
- **잠정 제외**: `CHAT_TRUST_UPSTREAM_WEIGHT`(기본 0)일 때 상위 weight_g(DB 대체 경로 snapshot)를 쓰지 않고 상품명 표기 중량만 씀. 출처 기록 없는 예전 저장 카드는 재선택 때 `explain.reweigh` 로 상품명 기준 재계산.
- **감사 범위**: `selection_audit` 가 고른 상품만이 아니라 함께 견준 후보(picks·others) 중 비교 허용 전 중량까지 확인. **REST 화면**에도 같은 경고(`_result_blocks` notice). 기본(제외)에서는 해당 경고가 생기지 않음.
- **전후 비교(재현용 데이터)**: 상품명 중량만 있는 검색은 결과 동일. DB 중량 후보가 섞이면 가성비 선택이 바뀜 — 예: 상품명 '300g'인데 DB 600g → 이전엔 100g당 6,500원으로 '가성비' 선정(상품명 기준 실제 13,000원), 이후엔 500g 상품이 가성비. DB 중량만 있는 검색은 '가성비' 대신 '최저가'.
- **DB 생성 경로 단서(GPT)**: `naver_shopping_api_collector.py` 가 상품명에서 중량을 파싱해 snapshot 에 저장 → 모든 DB 중량이 출처 불명은 아님. 행별 확인용 읽기 전용 스크립트 `check_snapshot_weights.py`(저장소 루트): 원천별로 상품명 중량과 같음/다름/못 읽음 개수와 예시 15건.
- 검증: 전체 7 failed / 5,107 passed (p30 과 실패 목록 동일, +2 = 새 테스트). 골든 비교 그대로 통과. 맥 원본 chat·partners 393 passed. 맥 .venv 미실행.

### 다음
- 사용자: 맥에서 `python check_snapshot_weights.py` 실행 → 결과로 '상품명과 같음'이 대부분인 원천부터 다시 허용할지 결정
- 맥에 로컬 MCP 서버(commerce-ai-food)가 연결된 것으로 보임 — p31 반영은 서버 재시작 후

---

## p32 — 상품명 중량 해석: 옵션 목록 제외 · 곱하기 계산 (2026-11-03)

계기: 사용자 맥 실행 `check_snapshot_weights.py` — DB weight_g 240행 모두 naver_api, 상품명 중량과 같음 96 / 다름 144 / 못 읽음 0. 다른 행은 전부 '5kg 10kg' 같은 **옵션 목록 상품명**: 수집기는 첫 중량, 추천 코드는 마지막 중량을 읽어서 어긋남. 둘 다 실제 가격의 옵션인지 모름 → DB 중량은 계속 제외(`CHAT_TRUST_UPSTREAM_WEIGHT=0` 유지), 상품명 해석도 보완. 사용자 결정: 2·3번 진행.
백업 `recipe_chat_api_backups/20261103_p32_title_weight/` (원본 4개, diff, 전후 비교 JSON, 전체 테스트 로그). 커밋하지 않음.

- `explain.parse_weight()` 신설, `parse_units` 가 이 규칙을 씀:
  - 서로 다른 중량 2개 이상(옵션 목록) → 중량 없음(100g당 비교 제외, 상품은 계속 표시). 근거: status=conflict, raw_text '5kg, 10kg', price_compare=hold
  - 곱하기 명시('500g x 2팩', '2.5kg×2') → 총중량, 계산식 기록. 사유 문구 '(상품명 표기 500g×2 계산)'
  - 곱한 값과 총량 표기가 같으면 그 값, 다르면 옵션 목록과 같이 처리. 같은 값 반복은 하나
  - 곱하기 표시 없는 '100g 10팩'은 이번에 바꾸지 않음
- 카드 기록 `weight_source`: title · title_multiplied · title_ambiguous · upstream (+ weight_formula·weight_found, 화면 응답 제외, 저장 후보에는 유지)
- 저장 후보 재선택: 상품명에서 읽은 중량은 항상 지금 규칙으로 다시 계산(p31 오후 저장분 포함)
- 관리자 패키지(`app/admin/shared/markets/base.parse_units`)의 같은 규칙은 이번에 바꾸지 않음
- 전후 비교(맥 p31 코드 vs p32, 같은 입력): 사과 옵션 목록 상품이 100g당 299원(10kg으로 나눔)으로 '가성비'였던 것 → 중량 하나인 '부사 사과 가정용 5kg'(680원)이 가성비. '삼겹살 500g x 2팩' 100g당 3,600원 → 1,800원으로 가성비. 중량 하나인 상품만 있는 검색은 동일
- 검증: 전체 7 failed / 5,121 passed (실패 목록 p31 과 동일, +14 새 테스트). 골든 비교 통과. 맥 원본 chat·partners 407 passed. 맥 .venv 미실행

---

## p33 — GPT 검토(15:33) 반영: '100g 10팩' 보류 · DB 중량 일괄 복구 방지 · 잔여 값 무효화 (2026-11-03)

백업 `recipe_chat_api_backups/20261103_p33_count_unclear_verified_marker/`. 검토 패키지 `Claude outputs/commerce_ai_p31_p33_review_2026-11-03.zip`(p31~p33 코드·diff·전후 비교 JSON·테스트 로그, 실행 환경 구분표). 커밋하지 않음.

- **'100g 10팩'**: 곱하기 없이 개수(N>1)가 붙으면 `count_unclear` → 100g당 비교 제외(개당 가격은 유지). '500g 1팩'은 그대로, '1kg (100g x 10팩)'은 1000g.
- **일괄 복구 방지**: `CHAT_TRUST_UPSTREAM_WEIGHT=1` 이어도 상위 항목에 행별 확인 표시 `weight_verified is True` 가 있어야 DB 중량 사용. 그런 표시를 만드는 절차·데이터는 아직 없음 → 사실상 계속 제외.
- **잔여 값**: 첫 검색·예산 재선택·관심 상품 비교 세 경로 REST 응답에서 옵션 목록·개수 불명 상품의 weight_g·100g당·가성비 역할·'100g당' 사유가 남지 않음을 테스트로 고정. 예전 규칙 저장 카드도 재선택 때 중량·100g당·역할·사유 재계산. 관심 상품 비교에 중량 출처 경고 추가(그전엔 빠져 있었음).
- 한계: 곱하기·상품명 중량은 판매자 표기 — 표시 가격이 그 구성에 적용되는지 연결은 미확인(근거 title_parse, 점수 차단). 관리자 패키지 parse_units 는 옛 규칙.
- 검증: Linux 사본 전체 7 failed / 5,128 passed (p32 과 실패 목록 동일). 맥 원본 폴더(Linux Python) chat·partners 414 passed, 중량 관련 6개 파일 86 passed. 맥 .venv 미실행.

### 맥 .venv 확인 (2026-11-03 15:46, 사용자 실행)
- `pytest tests/services/chat tests/services/partners` (맥 .venv, Python 3.14): **1 failed / 414 passed / 2 skipped** — Linux 결과와 동일.
- 실패 1 = 기존 `test_recipe_discover::test_the_trace_reaches_the_api_only_in_dev_mode`: `chat_routes.dev_trace_on()` 이 .env 파일 값(CHAT_DEV_TRACE=0)을 환경 변수보다 우선 → 테스트의 setenv 가 무시됨. 운영 동작 문제 아님(고객 응답에 추적 정보 없음은 확인). 테스트 격리 수정 여부 사용자 확인 대기.
- 맥 .venv 전체(tests/) 실행은 아직.

---

## p34 — GPT 검토(15:51) 재현 2건: 저장된 DB 중량 우회 사용 차단 · 곱하기 일부 해석 방지 (2026-11-03)

백업 `recipe_chat_api_backups/20261103_p34_saved_upstream_multiply/`. 검토 패키지 `Claude outputs/commerce_ai_p31_p34_review_2026-11-03.zip`(README 에 맥 .venv 결과 반영). 커밋하지 않음.

- **저장 후보 우회 차단**: p31~p33 `reweigh()` 는 upstream 카드를 그대로 둬서, 설정이 꺼져 있고 확인 표시가 없는 과거 카드가 재선택에서 가성비가 될 수 있었음(GPT 재현). → 상위 중량을 쓸 때 카드에 `weight_verified=True` 기록(저장 유지·화면 제외), 재선택 때 **지금** 설정 켬 + 확인 표시가 있어야 유지, 아니면 상품명으로 재계산(중량·100g당·개당 → 역할·사유 재작성).
- **곱하기**: 소수 수량('500g × 2.5팩')·여러 번 곱하기('× 2팩 × 3세트') → `multiply_unclear`, 중량 없음. '500g x 2팩'·'1.5kg x 2'는 그대로 계산.
- 검증: Linux 사본 전체 7 failed / 5,136 passed (p33 과 실패 목록 동일, +8). 맥 원본 폴더 chat·partners 422 passed, 중량 관련 94 passed. 맥 .venv 는 p33 상태에서 chat·partners 414 passed(사용자 실행) — p34 후 재실행 필요.
- 맥 .venv (사용자 실행 15:59, p34 반영 후) `tests/services/chat tests/services/partners`: **1 failed / 422 passed / 2 skipped** — Linux 결과와 동일. 실패 1 = 기존 dev-trace 테스트(.env 우선, 운영 문제 아님). 맥 .venv 전체 tests/ 는 아직.

---

## p35 — 로컬 MCP 실제 클라이언트 확인 + MCP 보완 (2026-11-03 16:0x)

GPT 검토(16:02): p34 두 결함 수정 검토 종료. 다음 = 행별 검증 기록 절차 + 로컬 MCP 실제 클라이언트 확인.

### 실제 클라이언트 확인 (Claude → 맥 로컬 MCP 서버 commerce-ai-food, 실제 판매처 API 호출)
| 호출 | 결과 |
|---|---|
| food_search_products('5만원 이하 한우 등심', 5) | commerce.v1 ok, recommendation_path=canonical_provider, 쿠팡 항목 fallback_used=false, 고지 문구·note 포함, 제휴 링크 비움 + 경고. **문제: 업체 '미리 보기' 예시 상품(한우이츠·미트프렌즈·현덕축산 (예시))이 섞여 1위 '가성비'** (맥 .env PARTNER_PREVIEW=1). 등심 검색에 '양지 국거리'·'찜갈비' 예시 상품이 관련 상품으로 들어옴(업체 상품 관련성 검사 느슨 — 웹도 같음) |
| food_search_products('와인 추천', 50) | ok, 쿠킹 와인 1건, 쇼핑커넥트 링크 없음(주류 규칙), limit 50 은 10 으로 제한. **쿠팡 파트너스 이미지 주소는 링크를 비워도 그대로 나감** |
| food_search_products(' ') | status empty 였지만 **판매처 API 를 빈 검색어로 호출**함 |
| food_get_recipe('크림파스타') | ok, EPIS:467, 출처 표기('원문 그대로가 아님') |
| food_get_recipe('파스타') | needs_followup 이지만 **후보 1개뿐 — MCP 서버 프로세스가 레시피 카탈로그(DB 5,198건)를 못 읽는 것으로 보임** (웹과 같은 build_default_service 를 씀, 원인 미확인) |
| food_get_recipe() / ('NOPE:999') | error bad_request / empty — 정상 |

### p35 수정 (백업 `recipe_chat_api_backups/20261103_p35_mcp_preview_blank_image/`)
- MCP 서버 시작 시 `PARTNER_PREVIEW=0` 강제 + 도구에서 예시 데이터 경고가 보이면 결과를 통째로 보류(status=held, preview_data_blocked) — 일부만 빼지 않음(예시 상품이 역할 선택에 이미 들어갔을 수 있어서)
- 빈 검색어는 판매처 API 호출 없이 bad_request
- 제휴 링크 보류 중에는 제휴 상품 이미지 주소도 비움(경고 문구에 포함)
- `tests/mcp_adapter/conftest.py`: 실제 .env·업체 데이터와 격리 (전체 실행 중 PARTNER_PREVIEW=1 이 새어 들어와 MCP 테스트 2개가 held 로 실패한 것을 확인하고 추가)
- 검증: Linux 사본 전체 7 failed / 5,139 passed (p34 와 실패 목록 동일). 맥 원본 chat·partners·mcp 429 passed. **맥 MCP 서버는 재시작해야 p35 반영**.

### 남은 일
- 레시피 카탈로그를 MCP 프로세스가 못 읽는 원인 (맥에서 진단 명령 실행 필요)
- 업체 상품 관련성(등심 검색에 양지·갈비) — 웹 동작도 바뀌므로 사용자 결정
- 행별 검증 기록 절차 (제안: DB 중량은 상품명 해석값이라 검증 대상에서 제외·계속 차단, 검증은 업체 제공 자료·OCR 값에 한정)

---

## p36 — MCP 레시피 DB 연결 · 업체 상품 관련성 · 확인 기록표 (2026-11-03, 사용자 결정 반영)

백업 `recipe_chat_api_backups/20261103_p36_mcp_db_partner_relevance_verification/`. 커밋하지 않음.
검증: Linux 사본 전체 7 failed / 5,164 passed (p35 와 실패 목록 동일). 맥 원본 chat·partners·mcp 454 passed. 맥 MCP 서버 재시작 필요.

1. **MCP 레시피 카탈로그**: 사용자 진단 결과 `recipe catalogue unavailable: EngineProviderUnboundError` → 웹(main.py lifespan)·Streamlit 은 시작 때 `bind_engine` 을 하지만 MCP 서버는 하지 않았음. `server._bind_engine()` 추가(이미 등록이면 그대로, DB 실패 시 카탈로그 없이 동작하며 stderr 에 알림). 터미널 진단 명령도 같은 이유로 0 이 나온 것이며 웹 서버는 정상.
2. **업체 상품 관련성 (사용자: 수정)**: 업체 상품은 검색어의 상품 낱말을 **모두** 담아야 함(`search.partner_match`). 용도·원산지 표기·포장·때 등 꾸밈 낱말(…용, 세트, 선물, 명절, 국산, 국내산, 수입, 산지, 대용량, 가정용, 냉장, 냉동, 프리미엄 등)은 필수 아님. '한우 등심' → 양지 국거리·찜갈비 제외, '국산 삼겹살 구이용' → '국산 삼겹살 500g' 포함. 쿠팡 결과의 관련성 규칙은 그대로. 한계: 지역명('제주 감귤')은 꾸밈 목록에 없어 업체 상품명에 지역명이 없으면 빠짐(보수적).
3. **확인 기록표 (사용자: 적힌 값만 '검증됨')**: `app/services/partners/verification.py`, 기록표 `data/partners/verified_values.csv`(아직 없음, 템플릿 `verified_values_template.csv` 추가). 열: 업체·대상·항목·값·단위·근거 종류·근거 파일·확인자·확인일·유효기한·메모. 대상 = 업체 상품ID, OCR 은 `sha256:<원본 이미지 해시>#<옵션·영역 ID>`. 같은 업체·대상·항목·값이면 verified(근거 메모 부착), 같은 단위인데 값이 다르면 conflict, 단위가 달라 못 견주면 그대로, 기한 지남·미래 확인일·필수 칸 빈 행 무시. 점수 사용은 열리지 않음. 업체 상품 검색 근거와 OCR 근거에 연결 — 순위·선택은 바뀌지 않음(테스트).
- **p36 실제 MCP 재확인 (Claude 재시작 후 16:39)**: '파스타' → 후보 4개(버섯파스타·크림소스파스타·단호박크림파스타·삼색채소 냉파스타) — 카탈로그 연결 확인. '5만원 이하 한우 등심' → 예시 상품 없음, 쿠팡 5개 모두 등심, 제휴 링크·이미지 비움 + 경고, 고지·예산 판정·canonical_provider 정상. 빈 검색어 → 판매처 호출 없이 bad_request.
- 발견: 쿠팡 상품명 끝 ', 200g, 3개'(쿠팡 옵션 표기 형식)가 p33 count_unclear 로 보류됨 → 쿠팡 상품 다수가 100g당 비교에서 빠질 수 있음. 제안: 쿠팡 + 상품명 끝 정확히 ', 중량, N개' 형식만 곱하기로 계산(근거 기록). 쿠팡 표기 규칙은 공식 문서 미확인 — 사용자 결정 대기.

---

## p37 — GPT 검토(16:45) 반영: 조건 낱말 · 확인 기록표 단위·기록 간 충돌 · 미리 보기 호출별 정책 (2026-11-03)

백업 `recipe_chat_api_backups/20261103_p37_preview_policy_conditions_units/`. 검토 패키지 `Claude outputs/commerce_ai_p35_p37_review_2026-11-03.zip`(p35~p37 diff, 테스트 로그, 확인 기록표 테스트, 실제 MCP 응답 요약). 커밋하지 않음.

- **업체 상품 관련성**: 국산/국내산·수입/수입산·냉장·냉동은 꾸밈이 아니라 조건 — 업체 상품명에 같은 뜻 표기가 있어야 통과(없으면 제외). 용도·포장·때(…용, 세트, 명절 등)는 필수 아님.
- **확인 기록표**: 업체·대상·항목·값·단위가 모두 같아야 verified(빈 단위는 빈 단위끼리). 유효한 기록끼리 값이 다르면 conflict. 만료 기록은 제외. OCR·html 은 verified 여도 점수 차단(테스트).
- **미리 보기**: `feed.offers(preview=)`·`collect/search_products(allow_preview=)` 로 호출별 정책, 결과 `Provenance.preview_data`(명시 bool). MCP 는 매 호출 allow_preview=False, preview_data 참이면 통째로 held. p35 의 서버 환경 변수 강제 제거. 웹은 기존 PARTNER_PREVIEW 설정 그대로.
- **쿠팡 ', 200g, 3개'**: GPT 권고대로 보류 유지(구성 후보는 근거 raw_text 로 보존). 가격·구성 연결이 API 옵션·수량 필드나 확인 기록으로 확인되면 그때 계산.
- 검증: Linux 사본 전체 7 failed / 5,175 passed (p36 과 실패 목록 동일). 맥 원본 chat·partners·mcp 465 passed. MCP 서버 재시작 필요, 맥 .venv p35~p37 미실행.
- 맥 .venv (사용자 실행 16:51, p37 반영 후) `tests/services/chat tests/services/partners tests/mcp_adapter`: **1 failed / 465 passed / 2 skipped** — Linux 결과와 동일. 실패 1 = 기존 dev-trace 테스트.

---

## p38 — GPT 검토(16:55) 반영: 확인 기록표 숫자 비교 반올림 오류 (2026-11-03)

백업 `recipe_chat_api_backups/20261103_p38_exact_number_compare/`(verification.py·search.py·test_verification_log.py, p38.diff, 변경 전 SHA256, 전체 테스트 로그). 커밋하지 않음.

- **오류**: `verification._norm()` 이 숫자를 `:g`(유효숫자 6자리)로 만들어 1,234,567 과 1,234,568 이 둘 다 `1.23457e+06` → 다른 값인데 verified, 서로 다른 두 기록도 충돌 없이 verified (변경 전 코드로 재현 확인).
- **수정**: Decimal 로 반올림 없이 비교(쉼표·공백·'원' 제거 뒤, 1.0 = 1, 0 = -0). NaN·Infinity 같은 비유한 값은 비교 불가 → 근거를 바꾸지 않음. 무게 근거 값(`search._exact`)도 같은 방식.
- 회귀 테스트 추가(큰 값 1 차이, 소수 끝자리, 비유한 값, 기록 간 1 차이 충돌 등) — 확인 기록표 테스트 32개.
- 검증: Linux 사본 전체 7 failed / 5,191 passed (p37 과 실패 목록 동일). 맥 원본 chat·partners·mcp 481 passed / 1 failed(기존 dev-trace).
- 설계서 현황 표를 p38 기준으로 갱신(세부 기록은 이 문서가 기준이라고 명시), OCR·html 점수 차단은 "현재 잠정 정책(2026-11-03 합의)"으로 표기.
- 남은 일: Claude 재시작 후 p37·p38 반영 MCP 서버 실제 응답 확인(preview_data=false, '국산 삼겹살' 조건 처리, 원본 JSON 보관), 맥 .venv p38 실행.
- **맥 .venv (사용자 실행 17:07, p38 반영 후)**: 1 failed / 481 passed / 2 skipped — Linux 결과와 동일, 실패 1 = 기존 dev-trace 테스트.
- **p37·p38 반영 MCP 실제 응답 (Claude 재시작 후 17:07)**
  - '국산 삼겹살', '5만원 이하 한우 등심', 레시피 '파스타' 모두 `provenance.preview_data=false`. 제휴 링크·이미지 비움, 경고·고지 정상.
  - '국산 삼겹살': 결과 5개 모두 쿠팡, 업체 상품 0개 → 업체 조건 낱말 규칙은 이번 호출로는 확인 안 됨(업체 상품이 조건 때문에 빠졌는지, 원래 없었는지 응답으로 구분 불가). 쿠팡 상품명에는 '국산'이 없음(한돈·도드람한돈 등) — 쿠팡 관련성 규칙은 바뀌지 않았으므로 예상대로.
  - '한우 등심': 예산 5만원 반영(5만원 넘는 2개는 others). '[농협안심한우] 1++ 프리미엄 메가 스테이크 소고기'가 2위로 나옴 — 상품명에 '등심' 없음(쿠팡 관련성 규칙의 빈틈).
  - 옵션 목록('1kg … 2개, 500g')·'200g, 3개'는 중량 conflict(보류)로 정상 처리. 다만 같은 상품의 `per_unit_krw`(14,200원·24,390원)는 개수로 계산돼 그대로 나옴.
  - 레시피: '파스타' → needs_followup 후보 4개, `epis-318`·`fs-660` id 로 재조회 ok(출처·인용 문구 포함). '올리브오일 적당량'이 quantity_known=true 로 표시됨(사소).

---

## p39 — GPT 검토(17:13) 반영: 개당 가격 적용 범위 · 적당량 · 쿠팡 관련성 영향 비교 준비 (2026-11-03)

백업 `recipe_chat_api_backups/20261103_p39_unit_scope_relevance_compare/`(수정 전 4개 파일, SHA256, p39.diff, 전체 테스트 로그). 커밋하지 않음.

- **개당 가격**: 개수의 적용 범위가 불명확하면 `per_unit` 을 비움 — 옵션 목록(중량 여러 개)·소수/여러 번 곱하기·서로 다른 개수 표기('2개 … 3개'). 개당 가격 기반 '가성비'와 설명에서 빠지고, `unit_count` 근거는 conflict(가격 비교 hold, 원문 raw_text 보존). 상품은 계속 표시. `explain.unit_scope`·`per_unit_price` 한 곳에서 판정, 첫 검색(enrich)·예산 재선택·관심 상품 비교(reweigh)에 같은 규칙 → 예전 저장값도 남지 않음(테스트).
  - 판단: '100g 10팩'·'200g, 3개'는 개수가 하나로 적혀 있어 개당 가격 유지(중량만 보류, p33). GPT 검토 필요 지점.
- **적당량**: `recipe_chat.recipes.amount_known()` 으로 대화 서비스와 MCP 레시피 응답이 같은 규칙 — '적당량·약간·조금·소량·기호에 따라'는 quantity_known=false, 원문은 amount 에 그대로.
- **쿠팡(판매처) 관련성 — 영향 비교만**: `app/services/commerce/relevance.py`(실제 경로 미연결, AST 테스트로 보장). 분류: 유지 / 요청 품목·부위 확인 불가 / 원산지·보관 조건 확인 불가 / 기존에도 제외. 조건 동의어 국산←한우·한돈(근거 주석). 17:07 MCP 응답 10개에 적용: 8 유지, 1 부위 확인 불가('… 메가 스테이크 소고기' — 등심 없음), 1 조건 확인 불가('[한땀갈비] 초특가 삼겹살' — 국산 표기 없음). 저장 자료(DB snapshot·대화 기록) 비교는 `check_coupang_relevance.py`(읽기 전용, API 호출 없음)를 맥에서 실행해야 함.
  - 주의: 업체 상품 규칙(p37 partner_match)은 동의어 없이 '국산/국내산' 글자만 봄 — 새 규칙 채택 시 함께 맞출 것.
- **MCP 원본 JSON**: `capture_mcp_raw.py` — MCP stdio 프로토콜로 서버를 띄워 5개 호출 원본 저장(제휴 링크·키 모양 문자열 검사 후). mcp 1.x/2.x 모두 지원, VM 에서 빈 검색어 호출로 동작 확인.
- 검증: Linux 사본 전체 7 failed / 5,229 passed (p38 과 실패 목록 동일, +38 테스트). 맥 원본 chat·partners·mcp 519 passed / 1 failed(기존 dev-trace). 새 동작 테스트는 수정 전 코드에서 실패 확인.
