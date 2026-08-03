from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

NEW_DOCUMENTS = {
    DOCS / "AI" / "RECOMMENDATION_SCORING.md": r"""# Recommendation Scoring V2

## 1. 목적

이 문서는 Food Commerce AI Agent의 추천점수 계산, Hero 선정, 점수 구성요소,
신뢰도 및 설명가능성 연결 규칙을 정의한다.

추천 순위는 규칙 기반의 결정적 계산으로 확정한다.
LLM은 사용자 의도·슬롯 추출과 확정된 근거의 자연어 표현에만 사용한다.

---

## 2. 핵심 원칙

1. 모든 점수 구성요소는 0~100 범위로 정규화한다.
2. 추천 모드별 가중치 프리셋을 사용한다.
3. 데이터가 없는 구성요소는 0점 감점이 아니라 가중치 재정규화 대상으로 처리한다.
4. Hard Filter를 통과하지 못한 상품은 점수 계산 전에 후보에서 제외한다.
5. Hero는 최고점 상품을 그대로 선택하지 않고 Hero Guard를 통과한 최고점 상품으로 선정한다.
6. 점수 계산과 추천 설명은 동일한 ScoreResult와 Evidence를 사용한다.
7. 동일 입력과 동일 scoring_version에서는 동일 순위가 나와야 한다.

---

## 3. 추천 모드

```python
PRIORITIES = {
    "mix",
    "quality",
    "price",
    "trust",
    "exploration",
}
```

- `mix`: 품질·가격·신뢰·적합도를 균형 있게 반영
- `quality`: 카테고리 핵심 품질 신호 우선
- `price`: 구매 기준가와 단위가격 경쟁력 우선
- `trust`: 정보 출처·상품 식별·가격 일관성 우선
- `exploration`: 신뢰 하한을 통과한 신규·발견 후보를 보조적으로 우선

---

## 4. 점수 구성요소

```python
COMPONENTS = {
    "quality",
    "price_value",
    "trust",
    "review",
    "fit",
    "market",
}
```

### 4.1 quality

카테고리별 핵심 품질 신호를 사용한다.

- 과일: Brix, 품종, 산지, 인증, 신선도
- 육류: 등급, BMS, 부위, 냉장·냉동, 이력
- 수산물: 자연산·양식, 상태, 손질, 원산지, 이력
- 가공식품: 원재료, 소비기한, 영양, 알레르기, 인증
- 커피: 산지, 품종, 가공, 로스팅, 향미
- 와인: 산지, 품종, 빈티지, 당도, 산도, 바디, 탄닌
- 건강기능식품: 기능성 원료, 인정 여부, 함량, 섭취 주의

### 4.2 price_value

- 구매 기준가
- 동일 규격 내 상대 가격
- 신뢰 가능한 단위가격
- 할인율과 할인 금액
- 쿠폰·회원가의 실제 적용 가능성

### 4.3 trust

- 상품 식별 신뢰도
- 가격 정보 일관성
- 단위가격 파싱 신뢰도
- 품질 속성 출처
- 공식 조회·구조화 데이터 여부

### 4.4 review

- 평점과 리뷰 수를 함께 사용
- 리뷰 정보가 없으면 0점 감점하지 않고 해당 가중치를 제외
- 비정상적으로 많은 리뷰나 플랫폼 간 혼합 가능성은 신뢰도에서 감점

### 4.5 fit

- 구매 목적
- 예산
- 수량
- 사용자 선호
- 세션의 priority
- 용도 적합성

### 4.6 market

- 검색 관심도
- 관심 방향
- 시즌성
- 탐색·발견 추천 보정

시장 신호는 상품 품질의 대체 근거로 사용하지 않는다.

---

## 5. 모드별 기본 가중치

```python
SCORE_WEIGHTS = {
    "mix": {
        "quality": 0.30,
        "price_value": 0.25,
        "trust": 0.20,
        "review": 0.10,
        "fit": 0.10,
        "market": 0.05,
    },
    "quality": {
        "quality": 0.50,
        "price_value": 0.10,
        "trust": 0.20,
        "review": 0.10,
        "fit": 0.10,
        "market": 0.00,
    },
    "price": {
        "quality": 0.10,
        "price_value": 0.50,
        "trust": 0.15,
        "review": 0.05,
        "fit": 0.15,
        "market": 0.05,
    },
    "trust": {
        "quality": 0.15,
        "price_value": 0.10,
        "trust": 0.50,
        "review": 0.10,
        "fit": 0.10,
        "market": 0.05,
    },
    "exploration": {
        "quality": 0.20,
        "price_value": 0.15,
        "trust": 0.25,
        "review": 0.05,
        "fit": 0.15,
        "market": 0.20,
    },
}
```

가중치는 초기값이며 오프라인 평가와 A/B 테스트로 조정한다.

---

## 6. 누락 신호 재정규화

구성요소가 없을 때 0점으로 간주하지 않는다.

```python
def calculate_weighted_score(signals, weights):
    available = {
        key: weight
        for key, weight in weights.items()
        if signals.get(key) is not None
    }

    weight_sum = sum(available.values())

    if weight_sum <= 0:
        return 0.0

    return sum(
        float(signals[key]) * weight
        for key, weight in available.items()
    ) / weight_sum
```

단, 필수 신호가 없는 경우에는 Hero Guard에서 제한할 수 있다.

---

## 7. ScoreResult 표준 스키마

```python
from pydantic import BaseModel, Field
from typing import Any

class ScoreEvidence(BaseModel):
    type: str
    label: str
    value: Any = None
    unit: str | None = None
    source_level: str
    confidence: float
    verified: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

class ScoreResult(BaseModel):
    scoring_version: str
    priority: str
    final_score: float
    confidence: float
    components: dict[str, float | None] = Field(default_factory=dict)
    weights_used: dict[str, float] = Field(default_factory=dict)
    evidence: list[ScoreEvidence] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    hard_filter_failed: bool = False
    hard_filter_reasons: list[str] = Field(default_factory=list)
```

---

## 8. Evidence 신뢰도 기준

| source_level | 기본 confidence | primary reason 사용 |
|---|---:|---|
| official | 95 | 가능 |
| verified_detail | 85 | 가능 |
| structured_source | 70 | 가능 |
| product_text | 50 | 조건부 가능 |
| inferred | 30 | 불가 |
| unknown | 0 | 불가 |

전체 confidence는 실제 사용된 evidence의 중요도 가중 평균으로 계산한다.

`inferred` 또는 `unknown`만 있는 근거는 Hero의 핵심 추천 이유로 승격하지 않는다.

---

## 9. Hard Filter

다음은 점수 감점이 아니라 후보 제거 또는 명시적 차단으로 처리한다.

- 사용자가 제외한 알레르기 성분이 포함된 상품
- 미성년 사용자에게 노출되는 주류
- 필수 가격이 없고 판매처 이동도 불가능한 상품
- 상품 식별에 실패한 후보
- 요청 카테고리와 명백히 다른 상품
- 건강기능식품 안전 조건을 위반하는 표현 또는 데이터

알레르기 정보가 미확인인 상품은 서비스 정책에 따라:

1. 후보 제외
2. 또는 `알레르기 정보 확인 필요` 표시 후 Hero 제외

중 하나로 일관되게 처리한다.

---

## 10. Hero Guard

```python
def passes_hero_guard(item, score_result, priority):
    if score_result.hard_filter_failed:
        return False

    if score_result.final_score < 50:
        return False

    if score_result.confidence < 55:
        return False

    if not item.get("_product_identity_key"):
        return False

    if priority == "price":
        unit_confidence = item.get("unit_price_confidence", 0)
        if unit_confidence < 60:
            return False

    return True
```

Hero 후보가 모두 Guard를 통과하지 못하면:

- 차순위 자동 승격을 하지 않고
- `hero_guard_fallback` 이벤트를 기록하고
- `비교가 필요한 추천 후보` UI로 표시한다.

---

## 11. 설명가능성 연결

추천 설명은 ScoreResult의 evidence만 사용한다.

```text
점수 계산 데이터
= 추천 설명 근거
= 백오피스 디버깅 데이터
```

설명 우선순위:

1. 높은 기여도의 구성요소
2. confidence 50 이상
3. 고객이 이해할 수 있는 구체적 차이
4. 중복되지 않는 최대 3개 이유

설명에 없는 데이터 또는 evidence에 없는 숫자·등급을 생성하지 않는다.

---

## 12. 추천 라벨

초기 기준:

| 점수 | 라벨 |
|---:|---|
| 80 이상 | 강력추천 |
| 65 이상 | 추천 |
| 50 이상 | 비교추천 |
| 50 미만 | 비교필요 |

confidence가 낮으면 점수 라벨을 한 단계 낮출 수 있다.

---

## 13. 버전·로그

모든 추천 이벤트에 다음을 기록한다.

```python
{
    "scoring_version": "v2.0.0",
    "priority": "quality",
    "final_score": 82.4,
    "confidence": 76.0,
    "components": {},
    "weights_used": {},
}
```

점수 로직 변경 시 반드시 `scoring_version`을 올린다.

---

## 14. 테스트

필수 테스트:

- 같은 입력의 반복 계산 결과 동일
- 누락 review가 전체 점수를 부당하게 낮추지 않음
- priority 변경 시 기대한 구성요소가 우선됨
- Hard Filter 상품이 순위에서 제외됨
- Hero Guard 실패 시 fallback 이벤트 발생
- 설명의 숫자·등급이 evidence에 존재함
""",

    DOCS / "AI" / "UNIT_PRICE_NORMALIZATION.md": r"""# Unit Price Normalization V2

## 1. 목적

상품 가격을 공정하게 비교하기 위해 중량·수량·옵션을 표준화하고,
100g당·kg당·개당·마리당 가격을 신뢰도와 함께 계산한다.

잘못 계산된 단위가격은 표시하지 않는다.

---

## 2. 핵심 원칙

1. 단위가격은 동일한 비교 기준끼리만 비교한다.
2. 상품명·옵션·상세 데이터의 우선순위를 정의한다.
3. 파싱 결과에는 반드시 confidence와 evidence를 저장한다.
4. 옵션형 상품은 선택된 옵션 기준으로 계산한다.
5. 단위가격 파싱 실패 시 가격 추천 이유에서 제외한다.
6. 명시 단가와 계산 단가가 충돌하면 신뢰도가 높은 출처를 우선한다.
7. 수량과 중량을 혼동하지 않는다.

---

## 3. 표준 단위

### 중량

```text
mg
g
kg
```

내부 표준은 gram으로 통일한다.

```python
1 kg = 1000 g
1 g = 1000 mg
```

### 용량

```text
ml
L
```

내부 표준은 ml로 통일한다.

### 개수

```text
개
입
팩
봉
병
캔
박스
마리
```

개수 단위는 상품군별 비교 가능 여부를 별도로 판단한다.

---

## 4. 결과 스키마

```python
from pydantic import BaseModel, Field
from typing import Any

class UnitPriceResult(BaseModel):
    basis_type: str
    basis_quantity: float
    basis_unit: str
    total_quantity: float | None = None
    total_unit: str | None = None
    effective_price: float | None = None
    unit_price: float | None = None
    confidence: float = 0
    source_level: str = "unknown"
    calculation_method: str = ""
    selected_option: str | None = None
    warnings: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)
```

예:

```python
{
    "basis_type": "weight",
    "basis_quantity": 100,
    "basis_unit": "g",
    "total_quantity": 2000,
    "total_unit": "g",
    "effective_price": 8990,
    "unit_price": 449.5,
    "confidence": 90,
    "source_level": "verified_detail",
    "calculation_method": "price_divided_by_selected_option_weight",
}
```

---

## 5. 데이터 우선순위

1. 선택된 옵션의 구조화된 단가
2. 선택된 옵션의 구조화된 중량 + 실구매가
3. 상세 페이지에 명시된 단가
4. 구조화된 상품 중량 + 실구매가
5. 상품명·옵션 텍스트 파싱
6. 추론
7. 미확인

`추론` 단계 결과는 고객에게 핵심 추천 근거로 사용하지 않는다.

---

## 6. 가격 우선순위

```text
쿠폰 적용가
→ 회원가
→ 최대 혜택가
→ 판매가
```

단, 실제 적용 조건이 확인되지 않은 쿠폰은 `쿠폰 가능` 신호로만 저장하고
실구매가 계산에 자동 반영하지 않는다.

---

## 7. 중량·수량 파싱 규칙

### 단일 중량

```text
사과 2kg
닭가슴살 500g
커피 200g
```

### 묶음 중량

```text
500g x 2팩 = 1000g
200g × 3봉 = 600g
1kg 2개 = 2000g
```

### 중량 + 개수

```text
사과 5kg 12~16과
```

총 중량 비교는 5kg을 사용한다.
개당 가격은 과수 범위 때문에 단일 값으로 확정하지 않는다.

### 개수 상품

```text
계란 30구
생수 2L x 6병
요거트 80g x 8개
```

용량·중량이 있으면 해당 총량 기준을 우선한다.
없으면 개당 가격만 계산한다.

### 옵션형 상품

```text
2kg 8,990원
3kg 13,800원
5kg 18,900원
```

현재 선택 옵션을 식별하지 못하면 임의로 최저 단가 옵션을 선택하지 않는다.

---

## 8. 정규식 예시

```python
WEIGHT_PATTERN = r"(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>kg|g|mg)"
MULTIPACK_PATTERN = (
    r"(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>kg|g|ml|l)"
    r"\s*[x×*]\s*(?P<count>\d+)"
)
COUNT_PATTERN = r"(?P<count>\d+)\s*(개|입|팩|봉|병|캔|마리|구)"
```

정규식만으로 확정하지 않고 원본 텍스트와 상품 카테고리를 함께 검증한다.

---

## 9. 계산식

### 100g당 가격

```python
unit_price_100g = effective_price / (total_weight_g / 100)
```

### kg당 가격

```python
unit_price_kg = effective_price / (total_weight_g / 1000)
```

### 100ml당 가격

```python
unit_price_100ml = effective_price / (total_volume_ml / 100)
```

### 개당 가격

```python
unit_price_each = effective_price / total_count
```

계산 전 모든 값이 양수인지 확인한다.

---

## 10. Confidence 기준

| 조건 | confidence 예시 |
|---|---:|
| 상세 페이지 선택 옵션 단가 직접 확인 | 95 |
| 구조화 옵션 중량과 가격으로 계산 | 90 |
| 구조화 상품 중량과 가격으로 계산 | 80 |
| 상품명 텍스트에서 명확히 파싱 | 65 |
| 범위·옵션 혼재 | 40 |
| 추론 | 30 |
| 실패 | 0 |

다음 경우 confidence를 낮춘다.

- 여러 옵션 가격이 한 상품에 혼재
- 상품명과 상세 중량 불일치
- 검색 결과 URL
- 묶음 수량이 불명확
- 총 중량과 개당 중량의 구분 불명확
- 판매가와 쿠폰가 조건이 불명확

---

## 11. 표시 규칙

### 표시 가능

```text
100g당 450원
단가 신뢰도 높음
```

### 조건부 표시

```text
100g당 약 450원
상품명 기준 계산
```

### 표시 금지

```text
단가 계산 불가
```

confidence가 기준 미만이면 비교표에는 `단가 정보 확인 필요`로 표시하고,
추천 이유에는 포함하지 않는다.

초기 기준:

```python
UNIT_PRICE_DISPLAY_THRESHOLD = 60
UNIT_PRICE_PRIMARY_REASON_THRESHOLD = 70
```

---

## 12. 카테고리별 기준

- 과일·육류·수산물·나물: 100g당 또는 kg당
- 음료·소스: 100ml당 또는 L당
- 계란: 개당 또는 10개당
- 생선: 100g당과 마리당을 구분
- 커피: 100g당
- 와인: 100ml당 또는 병당
- 건강기능식품: 1일 섭취량당 또는 1회 섭취량당

서로 다른 basis_type은 직접 순위를 비교하지 않는다.

---

## 13. 오류 방지

- `2kg × 1박스`를 2g 또는 1kg으로 해석하지 않는다.
- `12~16과` 평균값으로 개당 가격을 확정하지 않는다.
- 쿠폰 금액을 판매가로 오인하지 않는다.
- 정상가를 실구매가로 사용하지 않는다.
- 최저 단가 옵션을 현재 선택 옵션으로 오인하지 않는다.
- 검색 결과의 다른 상품 단가를 혼합하지 않는다.

---

## 14. 로그

```python
{
    "event_type": "unit_price_parsed",
    "product_identity": "",
    "unit_price": 450,
    "basis_unit": "100g",
    "confidence": 90,
    "source_level": "verified_detail",
    "calculation_method": "",
    "warnings": [],
}
```

파싱 실패는 `unit_price_parse_failed`로 기록한다.

---

## 15. 테스트 케이스

1. `2kg, 8,990원` → 100g당 449.5원
2. `500g x 2팩, 12,000원` → 100g당 1,200원
3. `5kg 12~16과` → 총 중량 계산 가능, 개당 가격 확정 금지
4. 다중 옵션이며 선택 옵션 없음 → 단가 핵심 이유 사용 금지
5. 명시 단가와 계산 단가가 10% 이상 차이 → warning과 신뢰도 하향
6. 가격 또는 중량 0 → 계산 실패
""",

    DOCS / "Architecture" / "CONVERSATION_STATE_MACHINE.md": r"""# Conversation State Machine V2

## 1. 목적

Food Commerce AI Agent의 멀티턴 대화를 재현 가능하고 디버깅 가능한
상태 머신으로 관리한다.

추천 먼저, 조정은 대화로 진행하며 불필요한 질문을 최소화한다.

---

## 2. Stage

```python
from enum import Enum

class Stage(str, Enum):
    UNDERSTAND = "understand"
    CLARIFY = "clarify"
    RECOMMEND = "recommend"
    COMPARE = "compare"
    REFINE = "refine"
    DECIDE = "decide"
    SHARE = "share"
```

---

## 3. 전이 규칙

```python
TRANSITIONS = {
    Stage.UNDERSTAND: [
        Stage.CLARIFY,
        Stage.RECOMMEND,
    ],
    Stage.CLARIFY: [
        Stage.CLARIFY,
        Stage.RECOMMEND,
    ],
    Stage.RECOMMEND: [
        Stage.COMPARE,
        Stage.REFINE,
        Stage.DECIDE,
    ],
    Stage.COMPARE: [
        Stage.REFINE,
        Stage.DECIDE,
        Stage.RECOMMEND,
    ],
    Stage.REFINE: [
        Stage.RECOMMEND,
    ],
    Stage.DECIDE: [
        Stage.SHARE,
        Stage.REFINE,
    ],
    Stage.SHARE: [
        Stage.UNDERSTAND,
    ],
}
```

---

## 4. 핵심 대화 규칙

1. clarify 질문은 한 턴에 1개만 한다.
2. 세션당 clarify는 기본 최대 2회, 절대 최대 3회로 제한한다.
3. 필수 슬롯이 채워졌으면 즉시 recommend로 이동한다.
4. 이미 채워진 슬롯을 다시 묻지 않는다.
5. 질문보다 추천을 우선하고 부족한 조건은 후속 질문 칩으로 조정한다.
6. Hard Filter 관련 조건은 추천 전에 확인한다.
7. 사용자가 명시적으로 비교·수정·공유를 요청하면 해당 Stage로 바로 이동할 수 있다.
8. 모든 Stage 전이는 로그로 남긴다.

---

## 5. 필수 슬롯

기본 필수 슬롯:

```text
food_category
purchase_goal 또는 usage
```

상황별 필수 슬롯:

- 건강기능식품: 기능성 목적, 주의 안내 확인
- 와인: 성인 인증
- 알레르기 언급: exclusions
- 선물: 예산 또는 수량 중 하나
- 레시피: 인원수 또는 기본 인원 적용 동의

필수 슬롯 외 조건은 기본값으로 추천한 뒤 수정할 수 있다.

---

## 6. ConversationState

```python
from datetime import datetime
from pydantic import BaseModel, Field

class ConversationState(BaseModel):
    session_id: str
    anonymous_user_id: str | None = None
    user_id: str | None = None

    stage: Stage = Stage.UNDERSTAND
    stage_history: list[str] = Field(default_factory=list)

    query: str = ""
    query_history: list[str] = Field(default_factory=list)

    intent: str = ""
    food_category: str = ""
    food_subcategory: str = ""
    purchase_goal: str = ""
    usage: str = ""

    budget_min: int | None = None
    budget_max: int | None = None
    quantity: int | None = None

    priority: str = ""
    preferences: dict = Field(default_factory=dict)
    exclusions: list[str] = Field(default_factory=list)
    dietary_profile: list[str] = Field(default_factory=list)

    selected_products: list[str] = Field(default_factory=list)
    compare_items: list[str] = Field(default_factory=list)

    clarify_count: int = 0
    max_clarify_count: int = 2

    locale: str = "ko-KR"
    experiment_id: str = ""
    variant: str = ""

    created_at: datetime | None = None
    updated_at: datetime | None = None
```

가변 필드는 반드시 `Field(default_factory=...)`를 사용한다.

---

## 7. Intent

```text
search_product
recommend_product
compare_product
refine_request
share_request
recipe_shopping
price_tracking
health_caution
out_of_scope
```

### health_caution

건강·질병·의약품과 관련된 주의가 필요한 요청.

### out_of_scope

식품 쇼핑 범위를 벗어난 요청.

---

## 8. 슬롯 추출 원칙

- 발화에 없는 값을 추측하지 않는다.
- 불명확한 값은 null 또는 빈 값으로 유지한다.
- 이전 상태의 슬롯을 보존한다.
- 사용자가 수정한 슬롯은 최신 값으로 덮어쓴다.
- `더 싼 것`, `아까 두 번째`와 같은 참조 발화는 query_history와 selected_products로 해석한다.
- 알레르기·제외 조건은 exclusions에 저장하고 Hard Filter로 전달한다.
- 민감한 건강정보는 장기 프로필에 저장하지 않는다.

---

## 9. Clarify 정책

```python
def should_clarify(state):
    if state.clarify_count >= state.max_clarify_count:
        return False

    return missing_required_slots(state)
```

질문 우선순위:

1. 안전·제외 조건
2. 카테고리 또는 용도
3. 예산
4. 수량
5. 취향

한 번에 질문 하나와 Quick Reply를 제공한다.

예:

```text
구이용과 국거리 중 어떤 용도인가요?

[구이용] [국거리] [불고기] [상관없음]
```

---

## 10. 추천 먼저 원칙

필수 슬롯이 충분하면 clarify를 생략한다.

```text
UNDERSTAND
→ RECOMMEND
```

추천 후 조정 칩:

```text
[더 저렴하게]
[품질 정보 확인 상품만]
[선물용으로]
[냉장 상품만]
[비교해줘]
```

---

## 11. Stage별 출력

### understand

- 의도·카테고리·참조 해석
- 슬롯 추출
- 안전 분류

### clarify

- 질문 1개
- Quick Reply
- clarify_count 증가

### recommend

- Hero
- 보조 후보
- ScoreResult
- 후속 질문 칩

### compare

- 최대 3개 비교
- 차이와 확인할 점
- 카테고리별 동적 항목

### refine

- 조건 변경
- query_history 보존
- 재검색 또는 재랭킹

### decide

- 최종 후보 요약
- 판매처 이동
- 구매 전 확인

### share

- 공유 스냅샷
- share_token
- 공유 이벤트

---

## 12. 이벤트 매핑

| Stage | 이벤트 |
|---|---|
| understand | conversation_understand |
| clarify | conversation_clarify |
| recommend | conversation_recommend |
| compare | conversation_compare |
| refine | conversation_refine |
| decide | conversation_decide |
| share | conversation_share |

추가 이벤트:

```text
session_start
session_end
quick_reply_click
followup_question_click
recommendation_empty
hero_guard_fallback
error
```

모든 이벤트에 현재 `stage`를 기록한다.

---

## 13. 저장 정책

초기:

- Streamlit session_state 또는 PostgreSQL 세션 테이블
- 세션 종료 시 요약만 사용자 선호 프로필에 반영

확장:

- Redis TTL 세션
- PostgreSQL 장기 프로필
- 이벤트 웨어하우스

민감정보는 세션 종료 후 장기 저장하지 않는다.

---

## 14. 상태 전이 함수

```python
def transition(state, target):
    allowed = TRANSITIONS.get(state.stage, [])

    if target not in allowed:
        raise ValueError(
            f"invalid transition: {state.stage} -> {target}"
        )

    state.stage_history.append(state.stage.value)
    state.stage = target
    return state
```

특수 사용자 명령은 정책 검증 후 직접 전이를 허용할 수 있다.

---

## 15. 테스트

- 필수 슬롯이 충분하면 clarify 생략
- clarify 최대 횟수 초과 시 recommend
- 기존 슬롯 재질문 금지
- refine 후 query_history 유지
- compare에서 선택 상품 참조 정상 처리
- 허용되지 않은 Stage 전이 차단
- 모든 Stage 이벤트 로그 기록
- exclusions가 Hard Filter에 전달됨
""",
}

V2_LINK_SECTIONS = {
    DOCS / "UX" / "AI_SHOPPING_EXPERIENCE.md": r"""
## V2 문서 정합성

이 문서는 다음 V2 명세를 기준으로 구현한다.

- 추천점수·Hero 선정: `../AI/RECOMMENDATION_SCORING.md`
- 단위가격·중량·옵션 표준화: `../AI/UNIT_PRICE_NORMALIZATION.md`
- 대화 상태 전이: `../Architecture/CONVERSATION_STATE_MACHINE.md`
- 추천 설명: `../AI/RECOMMENDATION_EXPLAINABILITY.md`
- 고객 행동 로그: `../Analytics/CUSTOMER_INTERACTION_LOG.md`

### V2 UI 반영사항

- Hero에 추천 신뢰도와 데이터 기준 시각을 표시한다.
- Hero 점수는 ScoreResult의 `final_score`만 사용한다.
- 비교표 단위가격은 UnitPriceResult의 confidence 기준을 통과한 값만 표시한다.
- 싫어요 이유에 `기타(직접 입력)`을 추가하고 텍스트는 metadata에 저장한다.
- Quick Reply와 후속 질문 칩의 클릭을 이벤트로 기록한다.
""",

    DOCS / "AI" / "CONVERSATIONAL_SHOPPING_AGENT.md": r"""
## V2 문서 정합성

대화 단계와 전이 규칙은 `../Architecture/CONVERSATION_STATE_MACHINE.md`를
단일 기준으로 사용한다.

### V2 규칙

- Stage는 understand, clarify, recommend, compare, refine, decide, share로 고정한다.
- clarify는 한 턴에 1개, 기본 최대 2회로 제한한다.
- 필수 슬롯이 충분하면 추천을 먼저 제공한다.
- `exclusions`는 점수 감점이 아니라 Hard Filter로 전달한다.
- Quick Reply는 `quick_reply_click` 이벤트로 기록한다.
- 건강·질병 관련 요청은 `health_caution` intent로 분류한다.
- 복용 의약품과 같은 민감정보는 장기 프로필에 저장하지 않는다.
""",

    DOCS / "AI" / "RECOMMENDATION_EXPLAINABILITY.md": r"""
## V2 문서 정합성

추천 설명은 `RECOMMENDATION_SCORING.md`의 ScoreResult와 Evidence만 사용한다.
단위가격 설명은 `UNIT_PRICE_NORMALIZATION.md`의 confidence 기준을 통과한 경우에만
생성한다.

### V2 설명 계약

- 점수 구성요소와 설명 근거는 동일한 구조화 데이터를 사용한다.
- evidence에 없는 숫자·등급·인증을 문장에 추가하지 않는다.
- `inferred`와 `unknown` 근거는 primary reason으로 사용하지 않는다.
- Hero에는 전체 confidence를 표시한다.
- 장점과 확인할 점을 분리한다.
- 가격 정보에는 기준 시각 또는 수집 시각을 표시한다.
""",

    DOCS / "Analytics" / "CUSTOMER_INTERACTION_LOG.md": r"""
## V2 문서 정합성

대화 Stage는 `../Architecture/CONVERSATION_STATE_MACHINE.md`,
추천 점수는 `../AI/RECOMMENDATION_SCORING.md`의 값을 사용한다.

### V2 추가 이벤트

- session_start
- session_end
- conversation_understand
- conversation_clarify
- conversation_recommend
- conversation_compare
- conversation_refine
- conversation_decide
- conversation_share
- quick_reply_click
- followup_question_click
- recommendation_empty
- hero_guard_fallback
- dislike_reason_submit
- purchase_feedback
- error

### V2 공통 필드

```python
{
    "experiment_id": "",
    "variant": "",
    "stage": "",
    "latency_ms": None,
    "device": "",
    "anonymous_user_id": "",
    "model_version": "",
    "scoring_version": "",
    "data_sources": [],
}
```

### V2 핵심 지표

- 세션 성공률
- Hero 채택률
- 추천 → 판매처 클릭 전환율
- clarify 질문 수별 이탈률
- 추천 이유 열람 후 좋아요율
- 추천 이유 유형별 클릭률
- 재방문율·재질문율

싫어요 한 번으로 budget_max를 직접 변경하지 않는다.
반복 신호를 누적해 가격 민감도를 점진적으로 조정한다.
""",
}

START_MARKER = "<!-- V2_CONSISTENCY_START -->"
END_MARKER = "<!-- V2_CONSISTENCY_END -->"


def write_new_documents() -> None:
    for path, content in NEW_DOCUMENTS.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.strip() + "\n", encoding="utf-8")
        print(f"created: {path.relative_to(ROOT)}")


def upsert_v2_section(path: Path, section: str) -> None:
    if not path.exists():
        print(f"missing: {path.relative_to(ROOT)}", file=sys.stderr)
        return

    text = path.read_text(encoding="utf-8")
    block = f"\n\n{START_MARKER}\n{section.strip()}\n{END_MARKER}\n"

    if START_MARKER in text and END_MARKER in text:
        before = text.split(START_MARKER, 1)[0].rstrip()
        after = text.split(END_MARKER, 1)[1].lstrip()
        updated = before + block
        if after:
            updated += "\n" + after
    else:
        updated = text.rstrip() + block

    path.write_text(updated.rstrip() + "\n", encoding="utf-8")
    print(f"updated: {path.relative_to(ROOT)}")


def main() -> None:
    write_new_documents()

    for path, section in V2_LINK_SECTIONS.items():
        upsert_v2_section(path, section)

    print("\nV2 documentation update complete.")


if __name__ == "__main__":
    main()
