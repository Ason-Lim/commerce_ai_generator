"""가격 우위 문구 제한 (2026-11-10) — 순서·역할은 그대로, 오래된·시각 없는 가격의 우위 문구만 바뀐다."""
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone

from app.services.commerce import price_claims as pc

NOW = datetime(2026, 11, 10, 6, 0, tzinfo=timezone.utc)
OLD = (NOW - timedelta(days=190)).replace(tzinfo=None)
FRESH = NOW - timedelta(days=3)


def _picked():
    picks = [
        {"key": "a", "rank": 1, "role": "value", "role_label": "가성비",
         "why": [{"text": "후보 5개 중 100g당 가장 저렴해요 (1,000원/100g)", "basis": "calc"},
                 {"text": "예산 3만원 이하 안이에요 (배송비 포함 20,000원)", "basis": "you"}]},
        {"key": "b", "rank": 2, "role": "fast", "role_label": "빠른 배송",
         "why": [{"text": "쿠팡이 로켓배송으로 표시한 상품 중 가장 저렴해요", "basis": "mall"},
                 {"text": "2kg, 100g당 1,200원 (상품명 표기 기준)", "basis": "calc"}]},
        {"key": "c", "rank": 3, "role": "alt", "role_label": "다른 선택",
         "why": [{"text": "100g당 1,500원으로 가성비 상품보다 100g당 500원 비싸요", "basis": "calc"}]},
    ]
    others = [{"key": "d", "rank": 4, "role": None, "role_label": None, "why": []}]
    return {"picks": picks, "others": others, "budget_miss": False}


def _raw(t):
    return {k: {"db_sale_price": 1000, "db_price_collected_at": t} for k in "abcd"}


def test_stale_db_prices_lose_advantage_wording_but_keep_order():
    picked = _picked()
    before = [(c["key"], c["rank"], c["role"]) for c in picked["picks"] + picked["others"]]
    n = pc.restrict(picked, _raw(OLD), "db_fallback", now=NOW)
    assert n == 4
    assert [(c["key"], c["rank"], c["role"]) for c in picked["picks"] + picked["others"]] == before
    a, b, c = picked["picks"]
    assert a["role_label"] == "과거 확인 가격" and b["role_label"] == "빠른 배송" and c["role_label"] == "다른 선택"
    assert a["seen_at"] == "2026-05-04" and a["price_claims_restricted"] == "stale"
    texts = " ".join(w["text"] for x in picked["picks"] for w in x["why"])
    for word in ("가장 저렴", "가성비", "비싸요", "예산 3만원 이하 안이에요", "100g당 1,200원"):
        assert word not in texts
    assert a["why"][0]["text"].startswith("2026-05-04 확인 가격이에요")
    assert any(w["text"] == "쿠팡이 로켓배송으로 표시한 상품이에요" for w in b["why"])
    assert any(w["text"] == "2kg (상품명 표기 기준)" for w in b["why"])
    assert a["reason"] == a["why"][0]["text"]


def test_missing_time_on_db_path_is_labelled():
    picked = _picked()
    raw = {k: {"db_sale_price": None} for k in "abcd"}
    pc.restrict(picked, raw, "db_fallback", now=NOW)
    a = picked["picks"][0]
    assert a["role_label"] == "확인 시각 없는 가격" and "seen_at" not in a
    assert a["why"][0]["text"].startswith("가격 확인 시각이 없어요")


def test_live_fresh_and_unknown_prices_are_untouched():
    for raw, path in ((_raw(OLD), "canonical_provider"), (_raw(FRESH), "db_fallback"), ({}, None)):
        picked = _picked()
        snapshot = copy.deepcopy(picked)
        assert pc.restrict(picked, raw, path, now=NOW) == 0
        assert picked == snapshot


def test_partner_card_uses_its_own_seen_at():
    picked = {"picks": [{"key": "p", "rank": 1, "role": "lowest", "role_label": "최저가", "partner": "온브릭스",
                         "seen_at": (NOW - timedelta(days=40)).isoformat(),
                         "why": [{"text": "후보 3개 중 가격이 가장 낮아요", "basis": "calc"}]}],
              "others": [], "budget_miss": False}
    assert pc.restrict(picked, {}, "canonical_provider", now=NOW) == 1
    assert picked["picks"][0]["role_label"] == "과거 확인 가격"


def test_criteria_note():
    picked = _picked()
    assert pc.criteria_note(picked["picks"]) is None
    pc.restrict(picked, _raw(OLD), "db_fallback", now=NOW)
    assert "참고만" in pc.criteria_note(picked["picks"])
