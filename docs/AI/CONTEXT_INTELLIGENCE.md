# Context Intelligence

날씨·시즌·검색 트렌드·정책 신호를 추천 시스템에 반영하기 위한 설계 문서입니다.

## 1. 핵심 원칙

- 추천지수의 품질·가격·신뢰 점수는 Context-Free로 유지한다.
- 날씨와 시즌은 질의 확장, 후보 검색, 별도 노출 섹션에 우선 사용한다.
- 정책 혜택은 상품 품질점수가 아니라 가격·혜택 계층에서 처리한다.
- Context는 추천의 보조 설명으로만 사용한다.
- 같은 수요 원인의 신호는 `cause_group`으로 묶어 중복 반영을 막는다.
- 메인 랭킹 보정은 기본 비활성화하고 A/B 실험에서만 최대 ±5점으로 제한한다.

## 2. 신호 역할

| 계층 | 역할 | 기본 추천점수 영향 |
|---|---|---:|
| 의도 해석 | 복날·비·폭염 등 상황 질의 이해 | 없음 |
| 후보 검색 | 관련 카테고리와 키워드 확장 | 없음 |
| 노출 구성 | 별도 Context 섹션 생성 | 없음 |
| 대화 | 선택 칩과 확인 질문 우선순위 조정 | 없음 |
| 설명 | `context_reason`과 evidence 표시 | 없음 |
| 정책 | 조건부 혜택 배지 표시 | 없음 |
| 랭킹 | 실험 설정에서만 제한 적용 | 기본 0 |

## 3. ContextSignal

```python
ContextSignal(
    signal_id="boknal-2026-chobok",
    signal_type="season_event",
    key="chobok",
    signal_role="predictive",
    cause_group="summer_health_food",
    strength=0.95,
    confidence=0.95,
    related_keywords=["삼계탕", "닭고기", "장어", "전복"],
    source="calendar_registry",
)
```

## 4. ContextResult

```python
{
    "active": True,
    "primary_context": {
        "signal_type": "season_event",
        "key": "chobok",
        "display_name": "초복 준비",
        "strength": 0.91,
        "confidence": 0.95,
        "cause_group": "summer_health_food",
    },
    "related_keywords": ["삼계탕", "닭고기", "장어", "전복"],
    "related_categories": ["meat", "seafood", "processed_food"],
    "context_reason": "초복이 가까워 여름 보양식 후보를 함께 살펴보기 좋은 시기예요.",
    "section_title": "☀️ 초복 준비",
    "ranking_adjustment": 0.0,
    "ranking_adjustment_enabled": False,
    "evidence": [],
    "policy_benefits": [],
    "engine_version": "context-intelligence-v1",
}
```

## 5. 중복 제거

- 날씨·시즌·검색 트렌드가 같은 수요 원인을 가리키면 하나의 `cause_group`으로 묶는다.
- 관측 신호가 충분하면 예측 신호보다 우선한다.
- 각 신호를 모두 점수에 더하지 않고 대표 신호 하나와 보조 evidence만 선택한다.

## 6. 정책 혜택

- 누구나 자동 적용되는 플랫폼 쿠폰만 AI 실구매가 후보에 포함할 수 있다.
- 지역·소득·결제수단·가맹점 조건이 있는 정책은 구매 기준가에 포함하지 않는다.
- 조건부 정책은 배지와 위험 안내로만 표시한다.
- `valid_to`, `verified_at`, 공식 출처가 없는 정책은 노출하지 않는다.

## 7. 로그 이벤트

- `context_section_impression`
- `context_section_click`
- `context_query_expand`
- `context_quick_reply_click`
- `policy_badge_impression`
- `policy_badge_click`
- `policy_store_check`
- `context_ranking_experiment`

## 8. 구현 로드맵

### Context V1
1. 시즌 캘린더
2. 수동 시즌·기념일 매핑
3. 중복 제거 엔진
4. Context 섹션 데이터 생성
5. 로그 이벤트

### Context V1.1
1. 정책 Registry
2. 공식 출처·기간 검증
3. 조건부 정책 혜택 배지
4. 만료 정책 자동 비활성화

### Context V1.2
1. 기상청 API
2. 지역별 당일 날씨 Context
3. 날씨 섹션 성과 검증

### Context V2
1. 네이버 쇼핑인사이트 배치
2. 세부 키워드 추세
3. 자사 로그 결합
4. 계절 조정
5. Context 랭킹 A/B 테스트

## 9. 문서 동기화 원칙

`app/design/context_intelligence_design.py`를 단일 원본으로 사용하고,
`scripts/sync_context_intelligence_docs.py`를 실행해 이 Markdown 문서를 다시 생성한다.

```bash
python scripts/sync_context_intelligence_docs.py
```
