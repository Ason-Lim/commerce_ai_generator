"""Server-driven UI blocks — same contract the React ui_ux BlockRenderer reads.

Only block types the existing front end already renders are produced:
text · notice · verdict · chips · clarify_form · product_list, plus recipe_card
(rendered by components/RecipeCard.tsx).
"""
from __future__ import annotations


def text(md: str) -> dict:
    return {"type": "text", "data": {"md": md}}


def notice(md: str, tone: str = "info") -> dict:
    return {"type": "notice", "data": {"md": md, "tone": tone}}


def affiliate_notice(md: str) -> dict:
    """경제적 이해관계 표시 — 응답 맨 위, 본문보다 눈에 띄게 (쿠팡 파트너스 가이드 #160, 2026-11-04 확인)."""
    return {"type": "notice", "data": {"md": md, "tone": "info", "affiliate": True}}


def verdict(md: str) -> dict:
    return {"type": "verdict", "data": {"md": md}}


def chips(items: list, mode: str = "message") -> dict:
    return {"type": "chips", "data": {"items": list(items), "mode": mode}}


def clarify(question_id: str, label: str, options: list[dict], *, why: str | None = None,
            skippable: bool = False, submit: str = "선택", layout: str = "sequential") -> dict:
    """layout 'cards' (recipe choices): one row per option with photo · one line · '레시피 보기' button."""
    q = {"id": question_id, "label": label, "options": options, "skippable": skippable}
    if why:
        q["why"] = why
    return {"type": "clarify_form", "data": {"questions": [q], "submit": submit, "layout": layout}}


def product_list(items: list[dict], *, title: str | None = None, note: str | None = None,
                 collapsed: bool = False) -> dict:
    """title/note: 목록 머리말 (예: '다른 후보 6개').  collapsed: 처음에는 접어 둔다 (2026-11-01)."""
    data: dict = {"items": items}
    if title:
        data["title"] = title
    if note:
        data["note"] = note
    if collapsed:
        data["collapsed"] = True
    return {"type": "product_list", "data": data}


def search_links(links: list[dict], *, title: str, badge: str | None = None, note: str | None = None) -> dict:
    """네이버쇼핑 검색 링크 (2026-11-04) — 추천 카드보다 조용한 보조 영역 (components/SearchLinks.tsx).
    links: [{query, url, check}] · 상품이 아니라 검색 화면으로만 연결, 제휴 아님."""
    data: dict = {"title": title, "links": list(links)}
    if badge:
        data["badge"] = badge
    if note:
        data["note"] = note
    return {"type": "search_links", "data": data}


def trend_list(items: list[dict], *, data_until: str | None, title: str, note: str | None = None) -> dict:
    """지금 검색이 늘어난 식품 목록 (2026-11-06, components/TrendList.tsx).
    items: surge.public_view 항목 (keyword·times·onset·rank·cross·youtube·clues·cause·ask·spark)."""
    data: dict = {"title": title, "data_until": data_until, "items": list(items)}
    if note:
        data["note"] = note
    return {"type": "trend_list", "data": data}


def recipe_card(card: dict) -> dict:
    """Source recipe card: photo, source badge, meta, ingredient checklist, steps, tips."""
    return {"type": "recipe_card", "data": card}


def compare_cta(label: str, sub: str, send: str) -> dict:
    """상품 목록 끝의 비교 카드 (2026-11-09 A안): 누르면 ``send`` 를 메시지로 보낸다 (예: '굴 상품 비교')."""
    return {"type": "compare_cta", "data": {"label": label, "sub": sub, "send": send}}
