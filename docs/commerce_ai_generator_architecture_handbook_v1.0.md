# Commerce AI Generator Architecture Handbook v1.0

**문서 상태:** Stable Baseline  
**적용 대상:** Commerce AI Generator 전체 프로젝트  
**목적:** 모든 ChatGPT 작업 창과 도메인 구현이 동일한 아키텍처 원칙, 인터페이스, 명명 규칙, 테스트 규칙을 따르도록 하는 공통 기준 문서  
**변경 원칙:** 본 문서는 아키텍처 계약서다. 도메인 구현 과정에서 임의로 변경하지 않는다. 변경이 필요하면 별도 RFC와 버전 승격을 거친다.

---

## 1. 프로젝트 목표

Commerce AI Generator는 다양한 식품 카테고리와 판매 채널을 통합해 다음 기능을 제공하는 확장형 추천 시스템이다.

1. 상품명과 상세정보에서 식품 도메인 지식을 추출한다.
2. 도메인별 품질·신뢰·가격·희소성 요소를 평가한다.
3. 여러 마켓플레이스의 상품을 공통 포맷으로 정규화한다.
4. 시장 상황, 제철성, 판매 활성도, 사용자 선호를 반영해 추천한다.
5. 새로운 식품 카테고리와 판매처를 Registry 기반으로 쉽게 확장한다.

핵심 철학:

```text
Parse once
Score separately
Register declaratively
Orchestrate centrally
Integrate safely
Extend without breaking
```

---

## 2. 전체 시스템 구조

```text
External Sources
    ├── Marketplace API
    ├── Crawlers
    ├── SmartStore
    ├── Public Market Data
    └── User Input
            │
            ▼
Marketplace Engine
    ├── Adapter
    ├── Normalizer
    ├── Listing Validator
    ├── Marketplace Health
    └── Marketplace Registry
            │
            ▼
Food Resolver
            │
            ▼
Food Knowledge Engine
    ├── Parser
    ├── Scoring
    ├── Provider
    ├── Rules
    └── Knowledge Registry
            │
            ▼
Market Intelligence
    ├── Seasonality
    ├── Price Signal
    ├── Trend Signal
    ├── Freshness
    └── Availability
            │
            ▼
Recommendation Engine
    ├── Ranking
    ├── Personalization
    ├── Explanation
    └── Recommendation Type
            │
            ▼
UI / API
```

---

## 3. 프로젝트 디렉토리 기준

### 3.1 Food Knowledge Engine

```text
app/services/food/
├── __init__.py
├── category_registry.py
├── resolver.py
├── models.py
│
└── knowledge/
    ├── __init__.py
    ├── base.py
    ├── models.py
    ├── registry.py
    │
    ├── common/
    │   ├── parser_base.py
    │   ├── scoring_base.py
    │   └── validation.py
    │
    ├── fruit/
    ├── meat/
    │   ├── common.py
    │   ├── beef/
    │   ├── pork/
    │   └── chicken/
    ├── seafood/
    ├── vegetable/
    ├── cheese/
    ├── coffee/
    ├── wine/
    ├── tea/
    ├── olive_oil/
    ├── pet_food/
    └── baby_food/
```

### 3.2 Marketplace Engine

```text
app/services/marketplace/
├── __init__.py
├── models.py
├── registry.py
├── resolver.py
├── normalizer.py
├── listing_validator.py
├── health_score.py
├── market_intelligence.py
│
├── adapters/
│   ├── __init__.py
│   ├── base.py
│   ├── naver.py
│   ├── coupang.py
│   ├── ssg.py
│   ├── kurly.py
│   └── ...
│
├── crawlers/
│   ├── __init__.py
│   └── ...
│
└── policies/
    ├── general.py
    ├── specialty.py
    ├── wholesale.py
    ├── public.py
    ├── fresh_retail.py
    └── ingredient_specialty.py
```

### 3.3 Recommendation Engine

```text
app/services/recommendation/
├── __init__.py
├── models.py
├── engine.py
├── scoring.py
├── ranking.py
├── reason_builder.py
├── personalization.py
└── policies/
```

---

## 4. 절대 준수 원칙

### 4.1 Parser는 Parsing만 한다

Parser의 책임:

- 상품명과 메타데이터에서 의미 있는 속성 추출
- Registry 검색
- 정규화된 ParseResult 생성
- confidence 계산

Parser가 하면 안 되는 일:

- 추천 점수 계산
- 마켓플레이스 선택
- 가격 비교
- 사용자 선호 반영
- DB 저장
- API 호출
- UI 문구 생성

### 4.2 Scoring은 Score만 계산한다

Scoring의 책임:

- ParseResult와 상품 메타데이터를 입력받아 점수 계산
- 점수 구성 요소와 근거 반환
- 결정론적이고 테스트 가능한 계산 수행

Scoring이 하면 안 되는 일:

- 상품명 재파싱
- Registry 수정
- 외부 API 호출
- 판매처 탐색
- UI 렌더링

### 4.3 Provider는 Orchestration만 한다

Provider의 책임:

```text
Parser
  ↓
Validation
  ↓
Scoring
  ↓
KnowledgeResult
```

Provider가 하면 안 되는 일:

- 파싱 규칙 직접 구현
- 점수 공식을 직접 구현
- Registry 데이터 직접 하드코딩
- 마켓플레이스 호출
- UI 의존

### 4.4 Registry는 데이터만 보관한다

Registry의 책임:

- canonical id
- display name
- alias
- metadata
- category mapping
- capability mapping

Registry가 하면 안 되는 일:

- 네트워크 호출
- 점수 계산
- 사용자별 분기
- 비즈니스 프로세스 실행
- DB 세션 제어

### 4.5 Marketplace Engine은 식품 의미를 해석하지 않는다

Marketplace Engine은 다음만 처리한다.

- 상품 수집
- 정규화
- 가격
- 배송
- 리뷰
- 재고
- 판매 상태
- 판매처 신뢰도

소고기 등급, 치즈 숙성, 커피 가공방식 같은 도메인 해석은 Food Knowledge Engine이 담당한다.

---

## 5. 핵심 공통 계약

### 5.1 BaseParseResult

모든 도메인 ParseResult는 공통 BaseParseResult를 상속한다.

```python
@dataclass(frozen=True)
class BaseParseResult:
    product_name: str
    category_id: str
    detected_keywords: tuple[str, ...]
    confidence: float
    warnings: tuple[str, ...] = ()
```

도메인별 확장 예:

```python
@dataclass(frozen=True)
class BeefParseResult(BaseParseResult):
    origin: str | None = None
    breed: str | None = None
    grade: str | None = None
    cut: str | None = None
    weight_grams: float | None = None
```

규칙:

- `frozen=True`
- mutable list 대신 tuple 권장
- confidence 범위는 `0.0 ~ 1.0`
- 필드명은 도메인 간 최대한 통일
- 직렬화 가능해야 함
- Optional 필드는 명시적으로 `None`

### 5.2 RegistryMatch

```python
@dataclass(frozen=True)
class RegistryMatch:
    canonical_id: str
    display_name: str
    matched_alias: str
    confidence: float
    metadata: Mapping[str, Any]
```

Registry 검색 결과는 문자열 하나가 아니라 RegistryMatch로 반환하는 것을 원칙으로 한다.

### 5.3 ScoreResult

```python
@dataclass(frozen=True)
class ScoreResult:
    total_score: float
    components: Mapping[str, float]
    reasons: tuple[str, ...]
    warnings: tuple[str, ...] = ()
```

규칙:

- `total_score`는 기본적으로 0~100
- component 이름은 snake_case
- 같은 입력이면 항상 같은 결과
- 계산 근거가 reasons에 남아야 함

### 5.4 KnowledgeProvider

```python
class KnowledgeProvider(ABC):
    category_id: str

    @abstractmethod
    def parse(self, product: ProductInput) -> BaseParseResult:
        ...

    @abstractmethod
    def score(
        self,
        product: ProductInput,
        parsed: BaseParseResult,
    ) -> ScoreResult:
        ...

    @abstractmethod
    def analyze(self, product: ProductInput) -> KnowledgeResult:
        ...
```

### 5.5 MarketplaceProduct

```python
@dataclass(frozen=True)
class MarketplaceProduct:
    marketplace_id: str
    external_product_id: str
    product_name: str
    product_url: str | None

    list_price: int | None
    sale_price: int | None
    shipping_fee: int | None

    weight_grams: float | None
    volume_ml: float | None
    package_count: int | None

    rating: float | None
    review_count: int | None

    sold_out: bool
    purchasable: bool

    seller_name: str | None
    brand_name: str | None
    origin: str | None

    raw_data: Mapping[str, Any]
```

도메인 특화 필드는 MarketplaceProduct에 계속 추가하지 않는다. 도메인 특화 정보는 ParseResult 또는 별도 도메인 모델에 둔다.

---

## 6. Registry 체계

프로젝트는 다음 Registry를 사용한다.

```text
Food Category Registry
Knowledge Registry
Marketplace Registry
Marketplace Capability Registry
Ingredient Registry
Cuisine Registry
Recommendation Registry
```

### 6.1 Food Category Registry

역할:

- 검색어와 상품을 최상위 식품 도메인으로 분류
- Provider 선택
- 하위 카테고리 매핑

예:

```text
fruit
vegetable
meat.beef
meat.pork
seafood
cheese
coffee
wine
tea
olive_oil
pet_food
baby_food
```

### 6.2 Knowledge Registry

역할:

- category_id와 Provider 연결
- Provider 자동 탐색
- 미등록 도메인 차단

```python
knowledge_registry.register(
    category_id="meat.beef",
    provider=BeefProvider(),
)
```

### 6.3 Marketplace Registry

Marketplace는 이름이 아니라 안정적인 `marketplace_id`로 식별한다.

예:

```text
naver
coupang
ssg
kurly
costco
meatbox
geumcheon_meat
cheese_queen
coffee_libre
momos
```

### 6.4 Capability Registry

Capability는 bool 필드를 계속 늘리는 대신 표준화된 코드로 관리한다.

예:

```text
bulk_purchase
restaurant_supply
cafe_supply
subscription
same_day_shipping
dawn_delivery
gift_set
organic
vegan
fresh_herb
import_food
single_origin
wine_pairing
```

### 6.5 Ingredient Registry

식재료의 canonical mapping을 담당한다.

예:

```text
herb.rosemary
herb.thyme
herb.parsley
spice.cardamom
spice.cumin
cheese.burrata
coffee.ethiopia_yirgacheffe
```

### 6.6 Cuisine Registry

요리 유형과 필요한 식재료를 연결한다.

예:

```text
italian
indian
french
mexican
thai
japanese
korean
middle_eastern
cafe
bakery
```

---

## 7. 도메인 표준 디렉토리

새 도메인은 아래 구조를 기본으로 한다.

```text
knowledge/<domain>/
├── __init__.py
├── parser_models.py
├── parser.py
├── scoring.py
├── rules.py
├── provider.py
├── registries.py
└── tests/
```

Registry가 커지면 분리한다.

예: Cheese

```text
knowledge/cheese/
├── parser_models.py
├── parser.py
├── scoring.py
├── rules.py
├── provider.py
├── milk_registry.py
├── style_registry.py
├── aging_registry.py
├── origin_registry.py
└── tests/
```

예: Coffee

```text
knowledge/coffee/
├── parser_models.py
├── parser.py
├── scoring.py
├── rules.py
├── provider.py
├── origin_registry.py
├── process_registry.py
├── roast_registry.py
├── brew_registry.py
└── tests/
```

---

## 8. 도메인 구현 절차

새 도메인은 반드시 다음 순서로 구현한다.

```text
1. Domain Scope 정의
2. Parser Model
3. Registry Data
4. Parser
5. Scoring
6. Provider
7. Knowledge Registry 등록
8. Unit Tests
9. Integration Tests
10. Marketplace 호환성 테스트
```

중간 단계를 건너뛰지 않는다.

---

## 9. Parser 설계 규칙

### 9.1 입력

Parser는 공통 ProductInput을 받는다.

```python
@dataclass(frozen=True)
class ProductInput:
    product_name: str
    description: str | None = None
    category_hint: str | None = None
    marketplace_id: str | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)
```

### 9.2 우선순위

```text
명시적 구조화 속성
→ 상품명
→ 상세설명
→ category hint
→ fallback
```

### 9.3 파싱 원칙

- alias는 Registry에서 관리
- regex는 rules.py에 정의
- parser.py에 대규모 상수 하드코딩 금지
- 충돌 시 confidence 하향
- 불명확한 값은 추측하지 않고 None
- 원문 keyword를 detected_keywords에 기록

### 9.4 Confidence

권장 기준:

```text
0.95 이상: 구조화 데이터와 상품명 일치
0.85 이상: 명확한 alias 직접 일치
0.70 이상: 복합 규칙으로 높은 확률
0.50 이상: 일부 단서만 존재
0.50 미만: 결과 사용 주의
```

---

## 10. Scoring 설계 규칙

모든 도메인은 점수를 구성 요소로 분해한다.

예:

```text
quality_score
trust_score
specificity_score
freshness_score
value_score
rarity_score
```

원칙:

- 총점 계산식 명시
- 가중치 합은 1.0 권장
- 누락값 처리 규칙 명시
- 상한/하한 적용
- 이유 문구는 계산과 분리 가능하도록 구성
- 도메인별 점수와 추천 점수를 혼합하지 않음

---

## 11. Marketplace Engine 설계 규칙

### 11.1 MarketplaceType

```python
class MarketplaceType(str, Enum):
    GENERAL = "general"
    SPECIALTY = "specialty"
    WHOLESALE = "wholesale"
    PUBLIC = "public"
    FRESH_RETAIL = "fresh_retail"
    INGREDIENT_SPECIALTY = "ingredient_specialty"
```

### 11.2 Adapter Contract

```python
class MarketplaceAdapter(ABC):
    marketplace_id: str

    @abstractmethod
    def search(self, query: SearchQuery) -> Sequence[RawMarketplaceItem]:
        ...

    @abstractmethod
    def normalize(self, item: RawMarketplaceItem) -> MarketplaceProduct:
        ...

    @abstractmethod
    def health(self) -> MarketplaceHealth:
        ...
```

원칙:

- Adapter는 도메인 파싱 금지
- `search()`와 `normalize()` 분리
- raw_data 보존
- 실패는 명확한 예외 타입으로 반환
- 크롤러와 API를 동일한 Adapter 인터페이스로 추상화

### 11.3 Listing Validator

검증 항목:

```text
상품명 존재
가격 유효성
URL 유효성
판매 가능 상태
중량·단위 정보
배송 정보
리뷰 수 이상값
중복 상품
광고성/비상품 페이지
```

### 11.4 Marketplace Health

마켓플레이스 유형별 정책을 사용한다.

```text
GENERAL
- 리뷰
- 배송
- 가격
- 품절 안정성

SPECIALTY
- 전문성
- 품질 정보
- 카테고리 깊이

WHOLESALE
- MOQ
- 거래 활성도
- 단가 투명성
- 재고 신뢰성

PUBLIC
- 생산자
- 원산지
- 인증
- 예약판매

FRESH_RETAIL
- 신선배송
- 상품 회전
- 산지 정보

INGREDIENT_SPECIALTY
- 전문 품목
- 포장 선택
- 보관 정보
- 업소용 지원
```

---

## 12. Market Intelligence 설계 규칙

Market Intelligence는 상품 자체의 품질과 분리한다.

입력:

- 검색량
- 가격 변화
- 판매처 수
- 최근 상품 등록
- 품절률
- 리뷰 증가
- 제철 정보
- 수입 시즌
- 산지 정보

출력 예:

```python
@dataclass(frozen=True)
class MarketIntelligence:
    market_stage: str
    trend_score: float | None
    trend_direction: str | None
    season_status: str | None
    availability_score: float | None
    price_signal: str | None
    buy_timing: str | None
    message: str | None
```

금지:

- Market Intelligence가 Parser 결과를 수정
- 시장 관심도가 품질 점수를 직접 대체
- 검색량만으로 품질이 높다고 판단

---

## 13. Recommendation Engine 설계 규칙

추천 점수는 서로 다른 축을 조합한다.

```text
Domain Quality
Marketplace Health
Listing Integrity
Price Value
Freshness
Seasonality
User Preference
Novelty / Discovery
```

권장 원칙:

- 개인화 가중치 과대 적용 금지
- 구매 이력은 판매처 Registry에 저장하지 않음
- 설명 가능한 구성 요소 유지
- 점수 캐시 가능
- tie-breaker 규칙 명시
- 추천 타입과 점수 분리

추천 타입 예:

```text
popular
premium
value
discovery
exploration
revisit
```

---

## 14. 사용자 선호와 공용 지식의 분리

공용 Registry에 저장:

- 판매처 정보
- 상품 카테고리
- 원산지
- 품종
- 등급
- 로스팅 방식
- 치즈 종류
- Capability

User Preference Profile에 저장:

- 선호 판매처
- 반복 구매 카테고리
- 선호 가격대
- 품질/가격/신뢰 성향
- 선호 포장 크기
- 최근 검색
- 클릭 이력

개인화 데이터와 공용 도메인 지식을 섞지 않는다.

---

## 15. 명명 규칙

### 15.1 Python

```text
파일명            snake_case.py
클래스명          PascalCase
함수명            snake_case
상수              UPPER_SNAKE_CASE
Registry ID       lowercase.dot.notation
Marketplace ID    lowercase_snake_case
```

### 15.2 필드명

권장 공통 필드:

```text
product_name
category_id
origin
brand_name
weight_grams
volume_ml
package_count
confidence
detected_keywords
warnings
```

같은 의미에 여러 이름을 쓰지 않는다.

표준 예:

```text
weight_grams
```

---

## 16. 예외 처리

```text
FoodKnowledgeError
├── ParseError
├── RegistryLookupError
├── ScoringError
└── ProviderError

MarketplaceError
├── MarketplaceConnectionError
├── MarketplaceRateLimitError
├── MarketplaceNormalizationError
└── ListingValidationError
```

원칙:

- bare `except Exception` 금지
- 외부 오류는 내부 예외로 래핑
- 사용자 메시지와 로그 메시지 분리
- 실패한 원본 데이터 보존
- silent fallback 금지

---

## 17. 테스트 규칙

### 17.1 필수 테스트

```text
Parser 단위 테스트
Registry alias 테스트
Scoring 경계값 테스트
Provider 통합 테스트
Serialization 테스트
Backward compatibility 테스트
MarketplaceProduct 연계 테스트
```

### 17.2 테스트 명명

```python
def test_beef_parser_detects_hanwoo_grade_1pp():
    ...
```

### 17.3 필수 케이스

- 정상 상품명
- 필드 누락
- 충돌 alias
- 오타
- 한글/영문 혼합
- 과도한 광고 문구
- 중량 포함/미포함
- 동일 입력 반복
- 기존 도메인 회귀 테스트

### 17.4 완료 조건

```text
compileall 성공
unit tests 성공
integration tests 성공
registry 등록 확인
serialization 성공
기존 도메인 테스트 영향 없음
```

---

## 18. 코드 품질 규칙

- Python type hint 필수
- dataclass 적극 사용
- public 함수 docstring 권장
- 함수는 한 가지 책임
- 100줄을 넘는 함수는 분리 검토
- 숨은 전역 상태 금지
- 순환 import 금지
- 도메인 간 직접 import 최소화
- 공통 인터페이스는 common/base 모듈 사용
- magic number는 상수 또는 policy로 이동

---

## 19. 금지사항

1. Parser에서 점수 계산
2. Scoring에서 재파싱
3. Provider에 alias 데이터 하드코딩
4. Registry에서 API 호출
5. Marketplace Adapter에서 소고기 등급 해석
6. UI가 Parser를 직접 호출
7. 도메인별로 별도 MarketplaceProduct 생성
8. 공통 모델을 도메인 창에서 임의 수정
9. 테스트 없이 Registry 항목 추가
10. 불명확한 값을 확정적으로 추론
11. 기존 도메인 회귀 테스트 없이 병합
12. 사용자 선호를 공용 Registry에 저장

---

## 20. ChatGPT 창 운영 규칙

각 도메인 창은 처음에 다음 정보를 반드시 공유받아야 한다.

```text
1. Architecture Handbook 버전
2. 현재 프로젝트 디렉토리 구조
3. 공통 모델 코드
4. Base Provider 계약
5. Registry 계약
6. 기존 구현 예시
7. 담당 범위
8. 수정 금지 파일
9. 테스트 명령
10. 완료 기준
```

각 창은 자신의 도메인 외 파일을 임의 수정하지 않는다.

---

## 21. 새 ChatGPT 창 시작 프롬프트 템플릿

```text
이 프로젝트는 Commerce AI Generator입니다.

기준 문서:
- Commerce AI Generator Architecture Handbook v1.0

담당 도메인:
- <DOMAIN_NAME>

프로젝트 원칙:
1. Parser는 parsing만 담당합니다.
2. Scoring은 scoring만 담당합니다.
3. Provider는 orchestration만 담당합니다.
4. Registry는 데이터만 보관합니다.
5. Marketplace Engine은 식품 의미를 해석하지 않습니다.
6. 모든 ParseResult는 BaseParseResult를 상속합니다.
7. 모든 Provider는 KnowledgeProvider 계약을 따릅니다.
8. 공통 모델과 공통 인터페이스는 임의 수정하지 않습니다.
9. 새로운 필드가 필요하면 먼저 호환성 검토안을 제시합니다.
10. 코드 제공 전에 기존 파일 구조와 import 경로를 확인합니다.

수정 가능 범위:
- app/services/food/knowledge/<DOMAIN_NAME>/
- 해당 도메인 테스트
- 명시적으로 허용된 Registry 등록부

수정 금지:
- 공통 Base 모델
- MarketplaceProduct
- 다른 도메인의 parser/scoring/provider
- UI
- Recommendation Engine
- DB schema
- 기존 Registry 계약

구현 순서:
1. parser_models.py
2. registry files
3. parser.py
4. scoring.py
5. provider.py
6. registry integration
7. unit tests
8. integration tests

완료 조건:
- python -m compileall -q app 성공
- 해당 도메인 테스트 성공
- 기존 Fruit/Beef 호환성 유지
- serialization 성공
- Registry 등록 확인

먼저 현재 구조를 요약하고, 변경 대상 파일 목록과 구현 단계를 제안한 뒤 진행하세요.
```

---

## 22. 창별 권장 역할

```text
Master Architecture 창
- 공통 모델
- 공통 인터페이스
- 구조 변경
- RFC 승인

Marketplace Core 창
- Marketplace 공통 모델
- Adapter 계약
- Health 정책
- Listing Validator

Cheese 창
- 치즈 파싱·점수·Registry

Coffee 창
- 원두 파싱·점수·Registry

Wine 창
- 와인 파싱·점수·Registry

Tea 창
- 차 파싱·점수·Registry

Olive Oil 창
- 올리브오일 파싱·점수·Registry

Herb/Spice 창
- 허브·향신료 파싱·점수·Registry
```

---

## 23. 공통 지식 동기화 방식

모든 창이 동일한 지식을 유지하도록 다음 파일을 단일 진실 공급원으로 사용한다.

```text
docs/
├── architecture/
│   ├── 00_project_overview.md
│   ├── 01_architecture_handbook.md
│   ├── 02_common_contracts.md
│   ├── 03_registry_rules.md
│   ├── 04_marketplace_rules.md
│   ├── 05_testing_rules.md
│   └── CHANGELOG.md
│
└── domains/
    ├── fruit.md
    ├── beef.md
    ├── cheese.md
    ├── coffee.md
    ├── wine.md
    ├── tea.md
    └── olive_oil.md
```

각 도메인 창 시작 시 최신 문서를 붙여 넣거나 업로드한다.

---

## 24. 변경 관리

공통 계약 변경은 즉시 코드에 반영하지 않는다.

```text
1. 변경 요청 작성
2. 영향 범위 분석
3. 하위 호환성 검토
4. Migration Plan 작성
5. Master Architecture 창 승인
6. Handbook 버전 상승
7. 공통 코드 수정
8. 전체 회귀 테스트
```

버전 정책:

```text
PATCH
- 오탈자
- 설명 개선
- 동작 변화 없음

MINOR
- 하위 호환 가능한 필드/인터페이스 추가

MAJOR
- 기존 계약 변경
- Migration 필요
```

---

## 25. 현재 권장 개발 순서

```text
1. Beef 완료
2. Beef 통합 테스트
3. Architecture Handbook v1.0 고정
4. Marketplace Core 구현
5. 공통 인터페이스 동결
6. Cheese 기준 도메인 구현
7. Cheese 패턴 검증
8. Coffee / Wine 분리 구현
9. Tea / Olive Oil / Herb 확장
10. 전체 Registry 통합
11. Recommendation Engine 연계
```

---

## 26. Definition of Done

```text
Architecture Handbook 준수
도메인 디렉토리 분리
BaseParseResult 상속
RegistryMatch 사용
Parser/Scoring/Provider 책임 분리
Knowledge Registry 등록
MarketplaceProduct 호환
단위 테스트 통과
통합 테스트 통과
기존 도메인 회귀 없음
직렬화 가능
문서 업데이트
```

---

## 27. 최종 원칙

```text
공통 계약은 중앙에서 관리한다.
도메인 지식은 도메인 내부에 둔다.
판매처 정보와 식품 의미를 분리한다.
파싱과 점수를 분리한다.
개인화와 공용 지식을 분리한다.
새 기능은 Registry 기반으로 확장한다.
공통 모델은 합의 없이 변경하지 않는다.
테스트 없는 확장은 완료로 간주하지 않는다.
```

---

**Commerce AI Generator Architecture Handbook v1.0 종료**
