# Customer Interaction Log

## 1. 목적

사용자의 상품 탐색, 추천 반응, 비교, 공유 및 대화 행동을 기록하여
추천 품질과 개인화를 고도화한다.

## 2. 주요 이벤트
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
## 3. 공통 로그 필드

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

## 4. 싫어요 이유 표준값
price_high
information_insufficient
not_relevant
reason_not_convincing
seller_not_preferred
other
## 5. 공유 채널
copy_link
native_share
kakao
message
email
other
## 6. 백오피스 핵심 지표
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
## 7. 사용자 반응 강도

노출
< 추천 이유 열람
< 상품 클릭
< 비교 담기
< 좋아요
< 공유

## 8. 개인정보 보호 원칙
공유 URL에 session_id를 직접 노출하지 않는다.
이메일·전화번호 등 개인정보를 이벤트 로그에 저장하지 않는다.
share_token은 예측 불가능한 임의값을 사용한다.
로그 보관 기간을 정의한다.
개인정보 처리방침과 사용자 동의를 반영한다.

<!-- V2_CONSISTENCY_START -->
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
<!-- V2_CONSISTENCY_END -->
