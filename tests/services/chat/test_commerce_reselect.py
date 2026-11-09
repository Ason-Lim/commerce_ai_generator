"""services/commerce/reselect (2026-11-03 p29): 저장 후보 재선택의 공통 결과."""
from __future__ import annotations

from app.services.chat import explain
from app.services.chat.budget import parse_budget
from app.services.chat.service import item_to_card
from app.services.commerce.reselect import compare_saved, rechoose, to_result


def card(n, title, price, query="소고기 등심", **extra):
    item = {"product_name": title, "price": price, "product_url": f"https://www.coupang.com/vp/products/{n}",
            "platform_name": "쿠팡", "is_coupang": True, **extra}
    return dict(explain.enrich(item_to_card(item, 0), item), query=query, seen_at="11/02 21:00")


CARDS = [card(1, "한우 등심 300g", 39000, is_rocket=True), card(2, "한우 등심 500g", 52000),
         card(3, "호주산 등심 1kg", 45000, is_free_shipping=True)]


def test_rechoose_equals_choose_and_does_not_touch_inputs():
    before = [dict(c) for c in CARDS]
    budget = parse_budget("5만원 이하")
    a = rechoose(CARDS, budget=budget, ask="소고기 등심")
    b = explain.choose([dict(c) for c in CARDS], budget=budget, ask="소고기 등심")
    assert [(c["key"], c["rank"], c["role"]) for c in a["picks"] + a["others"]] == \
           [(c["key"], c["rank"], c["role"]) for c in b["picks"] + b["others"]]
    assert CARDS == before


def test_compare_saved_groups_only_same_search():
    apple = card(9, "부사 사과 5kg", 30000, query="사과")
    got = compare_saved(CARDS + [apple])
    assert got["total"] == 4 and [g["query"] for g in got["groups"]] == ["소고기 등심"]
    assert got["groups"][0]["count"] == 3 and got["groups"][0]["seen_at"] == ["11/02 21:00"]
    assert [c["key"] for c in got["singles"]] == [apple["key"]]


def test_to_result_marks_reselect_and_keeps_upstream_unknown():
    budget = parse_budget("1만원 이하")
    picked = rechoose(CARDS, budget=budget, ask="소고기 등심")
    res = to_result(picked, query="소고기 등심", budget=budget, source="seen")
    assert res.status == "ok" and res.provenance.engine.endswith("(reselect:seen)")
    assert res.provenance.recommendation_path is None
    assert all(i.score.fallback_used is None and i.score.upstream_scores == {} for i in res.items)
    assert "새로 검색하지 않고" in res.warnings[0] and any("1만원 이하" in w for w in res.warnings)
    assert res.disclosure.has_affiliate
    assert [i.score.rank for i in res.items] == sorted(i.score.rank for i in res.items)


def test_empty_compare():
    assert compare_saved([]) == {"total": 0, "groups": [], "singles": []}
    assert to_result({"picks": [], "others": []}, query="x").status == "empty"
