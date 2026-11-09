"""상품 검색·선택 서비스 — /api/chat 쇼핑 턴(ChatService._shopping_turn)과 같은 순서·같은 함수.

화면 블록·대화 상태 저장은 하지 않는다 (그건 REST 어댑터의 일).  반환은 CommerceResult.
기존 경로와 상품·순위·역할·사유가 같은지는 tests/services/chat/test_commerce_contract.py 가 고정한다.
"""
from __future__ import annotations

import logging
import math
import uuid
from collections.abc import Callable

from app.domain.commerce import policies
from app.domain.commerce.models import (
    CommerceError, CommerceResult, Evidence, Followup, Offer, Product, Provenance, ScoreDetail, ScoreReason,
    ShoppingItem,
)
from app.domain.commerce.requests import SearchRequest

log = logging.getLogger(__name__)

ENGINE = "chat.explain.choose"


def _priority(text: str, nlu_parse: Callable | None) -> str:
    """ChatService._priority 와 같은 판정 (규칙 먼저, 그다음 NLU, 없으면 ranking)."""
    from app.services.chat.service import NLU_PRIORITY, PRIORITY_RULES

    for name, pattern in PRIORITY_RULES:
        if pattern.search(text):
            return name
    parsed = None
    if nlu_parse is not None:
        try:
            parsed = nlu_parse(text)
        except Exception:  # noqa: BLE001
            parsed = None
    if parsed:
        return NLU_PRIORITY.get(parsed.get("action_intent") or "", "ranking")
    return "ranking"


def collect(req: SearchRequest, *, shopping: Callable, keyword_extractor: Callable | None = None,
            nlu_parse: Callable | None = None, annotate_prices: bool = True) -> dict:
    """기존 함수들로 카드 묶음을 만든다 (dict 그대로 — 어댑터가 화면용·공통 모델용으로 각각 투영).

    Returns {"query", "label", "terms", "priority", "budget", "picked", "partner_list", "connect", "raw", "error",
             "preview"}
    """
    from app.services.chat import explain
    from app.services.chat.budget import parse_budget, strip_budget
    from app.services.chat.service import (
        ChatService, _content_tokens, _label, connect_links, item_to_card, relevant, shopping_terms,
    )
    from app.services.partners import feed as partner_feed
    from app.services.public_price import kamis

    text = req.text.strip()
    priority = req.priority or _priority(text, nlu_parse)
    budget = parse_budget(text)
    search_text = strip_budget(text) if budget and not budget.get("none") else text
    query, terms = shopping_terms(search_text, keyword_extractor)
    label = _label(query)

    raw: dict[str, dict] = {}
    error = None
    recommendation_path = None
    try:
        result = shopping(query, priority, req.session_id) or {}
        recommendation_path = result.get("recommendation_path")
        if not isinstance(recommendation_path, str):
            recommendation_path = None
        cards = []
        for it in (result.get("items") or [])[:req.limit]:
            card = dict(explain.enrich(item_to_card(it, 0), it), _q=query)
            raw[card["key"]] = it
            cards.append(card)
    except Exception as e:  # noqa: BLE001 — 같은 상황에서 웹은 '불러오지 못했어요' 안내
        log.exception("shopping provider failed")
        cards, error = [], CommerceError(code="source_unavailable", message=f"'{query}' 상품을 불러오지 못했어요.",
                                         scope="source", source="shopping")
    if terms:
        cards = [c for c in cards if relevant(c["title"], terms)]

    partner_terms = terms or _content_tokens(label)
    partner_cards = [ChatService._partner_card(it, query) for it in
                     (partner_feed.offers(lambda t: relevant(t, partner_terms)) if partner_terms else [])]
    cards = cards + [c for c in partner_cards if c["partner_mode"] == "compare"]
    partner_list = [c for c in partner_cards if c["partner_mode"] == "list"]
    preview = any(c.get("partner_preview") for c in partner_cards)

    connect_terms = terms or _content_tokens(label)
    connect = (connect_links(connect_terms)
               if connect_terms and not policies.is_alcohol_request(text) else [])

    picked = None
    if cards:
        picked = explain.choose(cards, budget=budget, ask=text)
        if annotate_prices:                     # _result_blocks 와 같은 순서: 고른 뒤 시세 참고 한 줄
            kamis.annotate(picked["picks"] + picked["others"])
        for c in picked["picks"] + picked["others"]:
            if c.get("partner_note") and c["partner_note"] not in (c.get("why") or []):
                c["why"] = (c.get("why") or []) + [c["partner_note"]]
        start = max([c["rank"] for c in picked["picks"] + picked["others"]] or [0])
        partner_list = [dict(c, rank=start + n, why=[c["partner_note"]]) for n, c in enumerate(partner_list, 1)]
        start = max([start] + [c["rank"] for c in partner_list])
        connect = [dict(c, rank=start + n) for n, c in enumerate(connect, 1)]
    else:
        partner_list = []                       # 웹도 쿠팡 결과가 없으면 업체 목록을 보여 주지 않는다
        connect = [dict(c, rank=n) for n, c in enumerate(connect, 1)]
    return dict(query=query, label=label, terms=terms, priority=priority, budget=budget, picked=picked,
                partner_list=partner_list, connect=connect, raw=raw, error=error, preview=preview, recommendation_path=recommendation_path)


# ── 공통 모델로 투영 ───────────────────────────────────────

def _int(v) -> int | None:
    try:
        return None if v is None else int(round(float(v)))
    except (TypeError, ValueError):
        return None


def _reasons(card: dict) -> list[ScoreReason]:
    out = []
    for w in card.get("why") or []:
        if isinstance(w, dict) and w.get("text"):
            out.append(ScoreReason(text=str(w["text"]), basis=str(w.get("basis") or "")))
        elif isinstance(w, str) and w:
            out.append(ScoreReason(text=w, basis=""))
    if not out and card.get("reason"):
        out.append(ScoreReason(text=str(card["reason"]), basis="source"))
    return out


def _evidence(card: dict, item: dict | None) -> list[Evidence]:
    ev: list[Evidence] = []
    mall = card.get("mall") or None
    if card.get("weight_g"):
        ev.append(Evidence(field="weight_g", value=f"{card['weight_g']:g}", unit="g", method="title_parse",
                           source="상품명 표기"))
    if card.get("unit_count"):
        ev.append(Evidence(field="unit_count", value=str(card["unit_count"]), unit="개", method="title_parse",
                           source="상품명 표기"))
    if card.get("rocket") is not None:
        ev.append(Evidence(field="rocket", value=str(card["rocket"]).lower(), method="api", source=mall))
    if card.get("free_shipping") is not None:
        ev.append(Evidence(field="free_shipping", value=str(card["free_shipping"]).lower(), method="api", source=mall))
    # 출처 미확인. 상위 순서/DB fallback의 간접 소비 여부는 별도이며 이 projection은 차단을 보장하지 않는다.
    item = item or {}
    for name in ("rating", "review_count"):
        if item.get(name) not in (None, "", 0):
            ev.append(Evidence(field=name, value=str(item[name]), method="unknown", source=mall))
    if card.get("partner"):
        ev.append(Evidence(field="price", value=str(card.get("price")), unit="원", method="partner_feed",
                           source=card["partner"], collected_at=card.get("seen_at")))
    if card.get("affiliate_program") == policies.CONNECT_PROGRAM:
        ev.append(Evidence(field="price", value=str(card.get("price")), unit="원", method="registry",
                           source="쇼핑커넥트 등록부"))
    return ev


UPSTREAM_SCORE_FIELDS = ("score", "final_score", "v8_final_score", "v7_final_score",
                         "final_recommendation_score", "adaptive_score")


def _finite_score(value) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        number = float(value)
    except (ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def to_item(card: dict, section: str, item: dict | None = None,
            recommendation_path: str | None = None) -> ShoppingItem:
    from app.services.chat import explain

    key = card.get("key") or explain.card_key(card)
    merchant = card.get("source")
    if merchant in (None, "", "판매처", card.get("mall")):
        merchant = None
    if card.get("partner"):
        link_type = "partner"
    elif card.get("affiliate"):
        link_type = "affiliate"
    else:
        link_type = "direct"
    item = item or {}
    engine_score = item.get("final_score", item.get("v8_final_score"))
    upstream_scores = {name: number for name in UPSTREAM_SCORE_FIELDS
                       if (number := _finite_score(item.get(name))) is not None}
    fallback_used = ({"canonical_provider": False, "db_fallback": True}.get(recommendation_path)
                     if item else None)
    upstream_rank = item.get("rank")
    if isinstance(upstream_rank, bool) or not isinstance(upstream_rank, int):
        upstream_rank = None
    return ShoppingItem(
        section=section,
        product=Product(product_id=card.get("pid"), key=key, title=card.get("title") or "",
                        image_url=policies.safe_url(card.get("image")), weight_g=card.get("weight_g"),
                        unit_count=card.get("unit_count"), seller_claims=list(card.get("seller_claims") or [])),
        offer=Offer(platform=str(card.get("mall") or ""), merchant=merchant,
                    product_url=policies.safe_url(card.get("url")), price_krw=_int(card.get("price")) or 0,
                    shipping_krw=_int(card.get("shipping_fee")), total_krw=_int(card.get("total")),
                    per100g_krw=_int(card.get("per100g")), per_unit_krw=_int(card.get("per_unit")),
                    rocket=card.get("rocket"), free_shipping=card.get("free_shipping"), link_type=link_type,
                    affiliate_program=card.get("affiliate_program"), opens_directly=bool(card.get("direct")),
                    seen_at=card.get("seen_at")),
        score=ScoreDetail(rank=int(card.get("rank") or 0), role=card.get("role"), role_label=card.get("role_label"),
                          reasons=_reasons(card), engine=ENGINE if section in ("picks", "others") else section,
                          engine_score=_finite_score(engine_score), upstream_scores=upstream_scores,
                          upstream_rank=upstream_rank, fallback_used=fallback_used),
        evidence=_evidence(card, item),
        price_reference=card.get("market_ref"),
    )


def search_products(req: SearchRequest, *, shopping: Callable, keyword_extractor: Callable | None = None,
                    nlu_parse: Callable | None = None, annotate_prices: bool = True,
                    request_id: str | None = None) -> CommerceResult:
    got = collect(req, shopping=shopping, keyword_extractor=keyword_extractor, nlu_parse=nlu_parse,
                  annotate_prices=annotate_prices)
    raw, picked = got["raw"], got["picked"]
    items: list[ShoppingItem] = []
    if picked:
        items += [to_item(c, "picks", raw.get(c["key"]), got["recommendation_path"]) for c in picked["picks"]]
        items += [to_item(c, "others", raw.get(c["key"]), got["recommendation_path"]) for c in picked["others"]]
    items += [to_item(c, "partner_list") for c in got["partner_list"]]
    items += [to_item(c, "connect") for c in got["connect"]]

    warnings = ["평점·후기·도착일은 쿠팡·네이버 검색 API가 제공하지 않아요. 판매처 페이지에서 확인해 주세요."]
    if picked and picked["budget_miss"]:
        warnings.append(f"예산 {got['budget']['label']} 안에 드는 후보가 없어 가격이 낮은 순으로 보여 줍니다.")
    if got["preview"]:
        warnings.append("미리 보기: 업체 상품은 허락 전 예시 데이터예요. 실제 상품·가격이 아니에요.")
    if got["connect"]:
        warnings.append("쇼핑커넥트 등록 상품은 위 후보와 같은 기준으로 견주지 않았고, 가격은 등록 시점 값이에요.")

    followup = None
    if picked and not got["budget"]:
        followup = Followup(kind="budget", question="예산이 있으면 알려 주세요. 예: 3만원 이하, 5만원 정도, 10만원대")

    errors = [got["error"]] if got["error"] else []
    if errors and items:
        status = "partial"
    elif errors:
        status = "error"
    elif items:
        status = "ok"
    else:
        status = "empty"
    programs = [i.offer.affiliate_program for i in items if i.offer.link_type == "affiliate"]
    return CommerceResult(
        request_id=request_id or str(uuid.uuid4()), status=status, items=items, followup=followup,
        warnings=warnings if items else [], disclosure=policies.disclosure_for(programs),
        provenance=Provenance(sources=sorted({i.offer.platform for i in items if i.offer.platform}), engine=ENGINE,
                              recommendation_path=got["recommendation_path"],
                              query=got["query"], terms=got["terms"]),
        errors=errors)
