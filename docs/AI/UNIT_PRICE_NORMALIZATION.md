# Unit Price Normalization V2

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
