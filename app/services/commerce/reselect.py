"""저장된 후보 다시 고르기 (2026-11-03 p29) — 새 검색 없이 explain.choose 로 다시 견준다.

쓰는 곳 (REST): 예산 답변 턴(ChatService._budget_turn) · 관심 상품 비교(ChatService._compare_saved_turn).
첫 쇼핑 턴의 search.collect() 와 같은 선택 함수(explain.choose)를 쓰고, 상위 추천 엔진은 다시 부르지 않는다.
따라서 재선택 결과의 recommendation_path·upstream 점수는 '이번 호출에서 확인한 값'이 아니다 (None 으로 둔다).

관심 상품(owner 보관함)은 개인 보관 데이터라 MCP·UCP 도구로 열지 않는다 — to_result() 는 내부 projection 용.
"""
from __future__ import annotations

import uuid

from app.domain.commerce import policies
from app.domain.commerce.models import CommerceResult, Provenance

ENGINE = "chat.explain.choose"


def rechoose(cards: list[dict], *, budget: dict | None = None, ask: str = "") -> dict:
    """저장된 카드(사본)로 역할별 선택을 다시 한다.  반환은 explain.choose 와 같다."""
    from app.services.chat import explain

    # 2026-11-03 p31: 중량 출처 기록이 없는 저장 카드는 상품명 표기 중량으로 다시 계산해서 견준다
    return explain.choose([explain.reweigh(dict(c)) for c in cards], budget=budget, ask=ask)


def compare_saved(items: list[dict]) -> dict:
    """관심 상품을 '같은 검색에서 담은 것'끼리 묶어 2개 이상인 묶음만 견준다 (종류가 다르면 100g당 비교 안 함).

    Returns {"total": n, "groups": [{"query", "count", "picked", "seen_at": [..]}], "singles": [card, ...]}
    """
    groups: dict[str, list[dict]] = {}
    for c in items:
        groups.setdefault(c.get("query") or "기타", []).append(c)
    compared, singles = [], []
    for query, cards in groups.items():
        if len(cards) < 2:
            singles += cards
            continue
        compared.append({"query": query, "count": len(cards), "picked": rechoose(cards, ask=query),
                         "seen_at": sorted({c.get("seen_at") for c in cards if c.get("seen_at")})})
    return {"total": len(items), "groups": compared, "singles": singles}


def to_result(picked: dict, *, query: str, budget: dict | None = None, source: str = "seen",
              request_id: str | None = None) -> CommerceResult:
    """재선택 결과 → 공통 모델.  source: 'seen'(직전 검색 후보) | 'saved'(관심 상품)."""
    from app.services.commerce.search import to_item

    items = ([to_item(c, "picks") for c in picked["picks"]] + [to_item(c, "others") for c in picked["others"]])
    warnings = ["새로 검색하지 않고 앞서 확인한 후보로 다시 골랐어요. 가격은 확인 시점 값이라 지금은 다를 수 있어요."]
    from app.services.commerce.search import selection_audit

    warnings += selection_audit(items)
    if picked.get("budget_miss") and budget:
        warnings.append(f"예산 {budget['label']} 안에 드는 후보가 없어 가격이 낮은 순으로 보여 줍니다.")
    programs = [i.offer.affiliate_program for i in items if i.offer.link_type == "affiliate"]
    return CommerceResult(
        request_id=request_id or str(uuid.uuid4()), status="ok" if items else "empty", items=items,
        warnings=warnings if items else [], disclosure=policies.disclosure_for(programs),
        provenance=Provenance(sources=sorted({i.offer.platform for i in items if i.offer.platform}),
                              engine=f"{ENGINE} (reselect:{source})", query=query))
