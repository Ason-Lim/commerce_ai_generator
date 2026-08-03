python - <<'PY'
from pathlib import Path

documents = {
    "docs/UX/AI_SHOPPING_EXPERIENCE.md": r"""# Commerce AI 쇼핑 경험 개선 로드맵

## 1. 목표

Commerce AI는 상품 목록을 단순히 나열하는 서비스가 아니라,
고객의 구매 결정을 돕는 대화형 식품 쇼핑 도우미를 목표로 한다.

고객이 다음 질문을 쉽게 해결할 수 있어야 한다.

- 왜 이 상품이 가장 좋은가?
- 다른 상품과 어떤 차이가 있는가?
- 내 목적에 맞는 상품인가?
- 가격과 품질 중 무엇이 더 유리한가?
- 구매 전에 무엇을 확인해야 하는가?
- 다른 사람에게 추천하거나 공유할 만한가?

## 2. 핵심 사용자 흐름

사용자 질문  
→ AI 의도·식품 카테고리 분석  
→ 상품 검색 및 표준화  
→ 추천지수 계산  
→ Hero 대표 추천  
→ 2위 이하 및 함께 보면 좋은 상품  
→ 비교 담기  
→ AI 비교 결론  
→ 상품 이동·좋아요·공유  
→ 행동 로그 및 개인화 학습

## 3. Hero UX

Hero는 단순히 점수가 가장 높은 상품이 아니라,
AI가 고객에게 가장 먼저 보여주는 대표 추천이어야 한다.

### 필수 표시 항목

- 상품 이미지
- 상품명
- 판매처
- 추천지수
- 추천 판단
- 구매 기준가
- 정상가
- 할인율
- 할인 금액
- 단위당 가격
- 카테고리 핵심 품질 신호
- AI 추천 요약
- 다른 상품과의 차이
- 구매 전 확인 사항
- 비교 담기
- 좋아요·싫어요
- 공유

## 4. 전체 상품 비교

다음 모든 영역의 상품을 하나의 비교함에 담을 수 있어야 한다.

- Hero 상품
- 2위 이하 추천 상품
- 함께 보면 좋은 상품
- 탐색·발견 추천 상품

비교 상품은 최대 3개로 제한한다.

### 공통 비교 항목

- 상품 이미지
- 상품명
- 판매처
- 구매 기준가
- 정상가
- 단위당 가격
- 할인율
- 쿠폰
- 원산지
- 보관 정보
- 배송 정보
- 인증
- 추천지수
- 상품 정보 신뢰도

### 카테고리별 비교 항목

- 과일: Brix, 품종, 산지, 크기, 인증
- 육류: 축종, 등급, BMS, 부위, 냉장·냉동, 이력 정보
- 수산물: 자연산·양식, 활어·생물·냉동, 손질 여부, 원산지
- 가공식품: 제조일, 소비기한, 주원료, 영양, 알레르기, HACCP
- 커피: 원산지, 품종, 로스팅, 가공 방식, 향미, 로스팅일
- 와인: 국가, 산지, 빈티지, 품종, 당도, 산도, 바디, 탄닌
- 건강기능식품: 기능성 원료, 함량, 섭취 방법, 주의사항

## 5. Sticky Compare Bar

비교 상품을 하나 이상 선택하면 화면 하단에 고정 비교 바를 표시한다.

예시:

[썸네일] [썸네일] [+]  
비교 2/3 담김 · 비교하기

### 동작 원칙

- 스크롤 위치와 관계없이 표시
- 선택 개수 즉시 갱신
- 비교 상품 썸네일 표시
- 비교하기 클릭 시 비교 영역으로 이동
- 3개 초과 선택 방지
- 상품별 삭제
- 전체 초기화
- 모바일 대응

## 6. 상품 반응 기능

각 상품 카드에 다음 기능을 제공한다.

- 👍 도움됐어요
- 👎 아쉬워요
- 🔗 공유
- 📊 비교 담기

싫어요 이유 예시:

- 가격이 비싸요
- 정보가 부족해요
- 원하는 상품이 아니에요
- 추천 이유가 납득되지 않아요
- 판매처가 마음에 들지 않아요

## 7. 공유

판매처 링크를 직접 공유하지 않고 Commerce AI 공유 페이지를 제공한다.

`/recommend/shared/{share_token}`

공유 페이지에는 상품 이미지, 추천 이유, 가격, 품질 정보,
비교 후보와 판매처 이동 버튼을 제공한다.

## 8. 상품 이미지

이미지는 다음 영역에 일관되게 표시한다.

- Hero
- 일반 상품 카드
- 함께 보면 좋은 상품
- 비교표
- Sticky Compare Bar
- 공유 페이지

## 9. 로딩 경험

단순 spinner 대신 실제 카드와 유사한 Skeleton UI를 사용한다.

- Hero Skeleton
- Product Card Skeleton
- Related Product Skeleton
- Compare Skeleton

## 10. 대화형 AI 연결

추천 결과 아래에 다음과 같은 후속 질문을 제공한다.

- 가격이 더 낮은 상품만 다시 볼까요?
- 품질 정보가 확인된 상품만 볼까요?
- 이 세 상품의 차이를 쉽게 설명해 드릴까요?
- 선물용 상품만 다시 골라드릴까요?

## 11. 구현 우선순위

### Phase 1 — 안정화

1. Hero 추천지수 정상화
2. Price Intelligence 통일
3. Compare Snapshot 안정화
4. Food Quality Engine 구조 확정

### Phase 2 — 비교 UX

1. Hero 비교 담기
2. Sticky Compare Bar
3. 비교 상품 이미지
4. 카테고리별 동적 비교 항목

### Phase 3 — 추천 설명

1. 추천 이유 우선순위화
2. 추천 근거와 위험 신호 분리
3. 비교 후보와 차이 설명
4. 근거 신뢰도 표시

### Phase 4 — 대화형 AI

1. 추천 결과 후속 질문
2. 조건 변경 대화
3. 비교 결과 질의응답
4. 사용자 선호 학습
5. 카테고리별 전문 질문

### Phase 5 — Growth & Analytics

1. 좋아요·싫어요
2. 공유 링크
3. 행동 로그
4. 백오피스 분석
5. 개인화 점수 반영
""",

    "docs/AI/RECOMMENDATION_EXPLAINABILITY.md": r"""# Recommendation Explainability

## 1. 목적

추천지수 숫자만 보여주는 것이 아니라 고객이 다음 내용을 쉽게 이해하도록 한다.

- 왜 이 상품을 추천했는가?
- 다른 상품보다 무엇이 좋은가?
- 어떤 데이터를 근거로 판단했는가?
- 정보가 얼마나 신뢰할 만한가?
- 구매 전에 무엇을 확인해야 하는가?

## 2. 설명 결과 구조

```python
{
    "headline": "",
    "primary_reasons": [],
    "comparison_reasons": [],
    "risk_notices": [],
    "evidence": [],
    "confidence": 0,
}

3. 설명 생성 원칙
실제 데이터가 있는 이유만 표시한다.
확인되지 않은 값을 추정하지 않는다.
홍보 문구와 검증 데이터를 구분한다.
같은 이유를 반복하지 않는다.
플랫폼 이름만으로 상품 우수성을 설명하지 않는다.
장점과 확인할 점을 함께 표시한다.
고객이 이해하기 쉬운 표현을 사용한다.
카테고리별 핵심 품질 신호를 사용한다.
핵심 이유는 최대 3개를 우선 표시한다.
상세 근거는 확장 영역에 제공한다.
4. 좋은 추천 이유
16Brix 수치가 확인됩니다.
100g당 가격이 비교 후보 중 가장 낮습니다.
GAP 인증 정보가 확인됩니다.
국내산 한우 1++(9)로 표시된 상품입니다.
비교 후보보다 나트륨 함량이 낮습니다.
5. 사용하지 않을 추천 이유
네이버 판매처 상품입니다.
인기 플랫폼에서 판매합니다.
AI가 종합적으로 추천했습니다.
6. 비교 설명 예시
2위 상품보다 구매 기준가가 4,000원 낮습니다.
3위 상품보다 단위당 가격은 높지만 품질 정보가 더 구체적입니다.
비교 후보 중 유일하게 Brix 수치가 명시되어 있습니다.
7. 구매 전 확인 예시
리뷰 데이터가 부족합니다.
등급 정보가 상품명에만 표시되어 있습니다.
정확한 옵션별 가격은 판매처에서 확인해야 합니다.
소비기한 정보가 확인되지 않았습니다.
8. 근거 수준
official
verified_detail
structured_source
product_text
inferred
unknown

예시:
{
    "label": "한우 1++(9)",
    "source_level": "product_text",
    "verified": False,
    "confidence": 70,
}
9. UI 구조

추천 핵심 한 문장
→ 가장 중요한 이유 3개
→ 다른 상품과의 차이
→ 구매 전 확인
→ 상세 근거 펼치기
""",

"docs/AI/CONVERSATIONAL_SHOPPING_AGENT.md": r"""# Conversational Shopping Agent

1. 목적

사용자가 검색어를 입력하고 결과를 받는 일회성 구조를 넘어,
AI가 질문하고 조건을 조정하며 구매 결정을 돕는 쇼핑 에이전트를 구현한다.

2. 대화 단계
understand
clarify
recommend
compare
refine
decide
share
3. 공통 질문
예산은 어느 정도인가요?
몇 명이 드실 예정인가요?
선물용인가요, 직접 드실 상품인가요?
가격과 품질 중 무엇을 더 중요하게 보시나요?
원하는 중량이나 수량이 있나요?
냉장·냉동 중 선호가 있나요?
제외해야 하는 성분이나 알레르기가 있나요?
4. 카테고리별 질문
과일
단맛을 가장 중요하게 보시나요?
크기보다 당도를 우선할까요?
선물용 포장이 필요한가요?
육류
구이·국거리·불고기 중 어떤 용도인가요?
마블링과 담백함 중 어느 쪽을 선호하시나요?
냉장 상품만 찾으시나요?
수산물
회·구이·조림 중 어떤 용도인가요?
손질된 상품을 원하시나요?
생물과 냉동 중 선호가 있나요?
가공식품
당류·나트륨·단백질 중 중요하게 보는 항목이 있나요?
알레르기 성분을 제외해야 하나요?
소비기한이 긴 상품을 원하시나요?
커피
산미와 고소함 중 어느 쪽을 선호하시나요?
핸드드립·에스프레소·캡슐 중 어떤 방식인가요?
로스팅 선호가 있나요?
와인
함께 드실 음식이 있나요?
드라이와 스위트 중 어느 쪽을 선호하시나요?
원하는 가격대와 바디감이 있나요?
건강기능식품
찾고 있는 기능성 목적은 무엇인가요?
현재 복용 중인 의약품이나 건강기능식품이 있나요?
알레르기나 섭취 제한 성분이 있나요?

건강 관련 답변은 의료 진단이나 치료를 대신하지 않는다.

5. 대화 상태 구조
{
    "session_id": "",
    "query": "",
    "food_category": "",
    "food_subcategory": "",
    "purchase_goal": "",
    "budget_min": None,
    "budget_max": None,
    "quantity": None,
    "priority": "",
    "preferences": {},
    "exclusions": [],
    "selected_products": [],
    "compare_items": [],
    "conversation_stage": "",
}
6. 추천 결과 후속 질문
가격이 더 낮은 상품만 다시 볼까요?
품질 정보가 확인된 상품만 볼까요?
이 세 상품의 차이를 쉽게 설명해 드릴까요?
선물용 상품만 다시 골라드릴까요?
냉장 상품만 다시 찾아볼까요?
7. 능동형 AI

장기적으로 AI가 먼저 대화를 시작할 수 있다.

예:

최근 당도가 높은 사과를 자주 보셨어요.
이번에는 100g당 가격이 더 낮은 상품도 함께 비교해볼까요?

8. 안전 원칙
건강기능식품을 의약품처럼 설명하지 않는다.
질병 치료 효과를 단정하지 않는다.
알레르기 정보가 불확실하면 확인 필요를 표시한다.
소비기한이 확인되지 않은 상품을 안전하다고 단정하지 않는다.
등급·인증·이력은 표시 정보와 공식 검증 정보를 구분한다.
""",
"docs/Analytics/CUSTOMER_INTERACTION_LOG.md": r"""# Customer Interaction Log

1. 목적

사용자의 상품 탐색, 추천 반응, 비교, 공유 및 대화 행동을 기록하여
추천 품질과 개인화를 고도화한다.

2. 주요 이벤트
recommendation_impression
hero_impression
product_card_impression
reason_expand
compare_add
compare_remove
compare_open
compare_reset
product_click
reaction_like
reaction_dislike
share_create
share_open
shared_product_click
conversation_question
conversation_clarify
conversation_refine
conversation_compare
conversation_decide
3. 공통 로그 필드

{
    "event_id": "",
    "session_id": "",
    "event_type": "",
    "product_identity": "",
    "food_category": "",
    "food_subcategory": "",
    "query": "",
    "priority": "",
    "section": "",
    "display_rank": None,
    "recommendation_score": None,
    "metadata": {},
    "created_at": None,
}

4. 싫어요 이유 표준값
price_high
information_insufficient
not_relevant
reason_not_convincing
seller_not_preferred
other
5. 공유 채널
copy_link
native_share
kakao
message
email
other
6. 백오피스 핵심 지표
노출 대비 상품 클릭률
추천 이유 열람률
비교담기율
비교 제거율
비교 후 상품 클릭률
좋아요율
싫어요율 및 이유
공유율
공유 링크 유입률
공유 후 판매처 클릭률
카테고리별 선호
가격·품질·신뢰 우선 성향
대화 후 추천 전환율
7. 사용자 반응 강도

노출
< 추천 이유 열람
< 상품 클릭
< 비교 담기
< 좋아요
< 공유

8. 개인정보 보호 원칙
공유 URL에 session_id를 직접 노출하지 않는다.
이메일·전화번호 등 개인정보를 이벤트 로그에 저장하지 않는다.
share_token은 예측 불가능한 임의값을 사용한다.
로그 보관 기간을 정의한다.
개인정보 처리방침과 사용자 동의를 반영한다.
""",
}

for filename, content in documents.items():
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"created: {path} ({len(content.splitlines())} lines)")
PY


for filename, content in documents.items():
    path = Path(filename)
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    path.write_text(
        content.strip() + "\n",
        encoding="utf-8",
    )
    print(
        f"created: {path}"
    )