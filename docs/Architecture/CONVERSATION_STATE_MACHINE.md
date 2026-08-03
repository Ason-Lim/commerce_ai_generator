# Conversation State Machine V2

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
