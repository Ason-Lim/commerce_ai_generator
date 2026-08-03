# Recommendation Scoring V2

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
