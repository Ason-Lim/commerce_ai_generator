"""기록(Evidence.usage)과 실제 통제의 경계 (2026-11-03 p30).

* explain.choose 는 Evidence.usage 를 읽지 않는다 → usage 는 기록이고, 차이는 selection_audit 경고로 드러낸다.
* OCR 근거(ocr_evidence)는 어떤 선택·응답 경로에도 연결돼 있지 않다 — 연결되면 이 테스트가 알린다.
* 외부 AI 호출 여부를 알 수 없으면(API_CALLS 없음·형식 불명) 0회로 보지 않는다.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from app.domain.commerce.requests import SearchRequest
from app.services.commerce.ocr_evidence import external_ai_calls, from_offer_result, from_region_bundle
from app.services.commerce.reselect import rechoose, to_result
from app.services.commerce.search import search_products
from tests.services.chat.conftest import FakeShopping

ROOT = Path(__file__).resolve().parents[3]
FIX = Path(__file__).parent / "fixtures"
OFFER = json.loads((FIX / "ocr_offer_example.json").read_text(encoding="utf-8"))
BUNDLE = json.loads((FIX / "ocr_bundle_example.json").read_text(encoding="utf-8"))
OCR_ONLY = {"예시몰": {"상태": "허락", "이미지 문자 판독(OCR)": "허용"}}
OCR_AND_AI = {"예시몰": dict(OCR_ONLY["예시몰"], **{"외부 AI 전송": "허용"})}
MISSING = object()


@pytest.mark.parametrize("value", [MISSING, None, "0", "2", True, False, -1, 1.5])
def test_unknown_external_ai_calls_are_not_treated_as_zero(value):
    for doc, convert in ((OFFER, from_offer_result), (BUNDLE, from_region_bundle)):
        data = {k: v for k, v in doc.items() if k != "API_CALLS"}
        if value is not MISSING:
            data["API_CALLS"] = value
        assert external_ai_calls(data) is None
        assert convert(data, partner="예시몰", permissions=OCR_ONLY)["reason"] == "no_external_ai_permission"
        ok = convert(data, partner="예시몰", permissions=OCR_AND_AI)
        assert ok["status"] == "ok" and ok["provenance"]["api_calls"] is None


def test_explicit_zero_needs_only_ocr_permission():
    for doc, convert in ((OFFER, from_offer_result), (BUNDLE, from_region_bundle)):
        res = convert(dict(doc, API_CALLS=0), partner="예시몰", permissions=OCR_ONLY)
        assert res["status"] == "ok" and res["provenance"]["api_calls"] == 0


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module)
            out |= {f"{node.module}.{a.name}" for a in node.names}
    return out


def test_ocr_evidence_is_not_wired_into_any_app_path_yet():
    users = [p.relative_to(ROOT).as_posix() for p in (ROOT / "app").rglob("*.py")
             if p.name != "ocr_evidence.py" and any("ocr_evidence" in m for m in _imports(p))]
    assert users == [], ("OCR 근거를 쓰는 경로가 생겼어요. 그 경로가 policies.usable(…) 로 용도를 검사하는지 "
                         f"확인한 뒤 이 테스트를 갱신하세요: {users}")


def test_selection_code_does_not_read_evidence_usage():
    mods = _imports(ROOT / "app/services/chat/explain.py")
    assert not any(m.startswith("app.domain") or "ocr" in m for m in mods)


def it(n, title, price, **extra):
    return {"product_name": title, "price": price, "product_url": f"https://www.coupang.com/vp/products/{n}",
            "platform_name": "쿠팡", "is_coupang": True, **extra}


def search(items, text="삼겹살 추천"):
    return search_products(SearchRequest(text=text), shopping=FakeShopping(items=items))


def weight_ev(item):
    return next((e for e in item.evidence if e.field == "weight_g"), None)


# 상위 weight_g (DB 대체 경로) 만 있는 후보 + 상품명 중량 후보
MIXED = [it(1, "국산 삼겹살 구이용", 10000, weight_g=1000), it(2, "국산 삼겹살 수육용", 9000, weight_g=500),
         it(3, "국산 삼겹살 300g", 7000), it(4, "국산 삼겹살 600g", 12600)]


def test_db_weight_is_excluded_by_default(monkeypatch):
    monkeypatch.delenv("CHAT_TRUST_UPSTREAM_WEIGHT", raising=False)
    res = search(MIXED)
    by = {i.product.title: i for i in res.items}
    assert by["국산 삼겹살 구이용"].product.weight_g is None and weight_ev(by["국산 삼겹살 구이용"]) is None
    assert by["국산 삼겹살 구이용"].offer.per100g_krw is None
    value = next(i for i in res.items if i.score.role == "value")
    assert value.product.title in ("국산 삼겹살 300g", "국산 삼겹살 600g")      # 상품명 중량끼리만 비교
    assert weight_ev(value).method == "title_parse"
    assert not [w for w in res.warnings if "중량 출처" in w]


def test_actual_source_is_recorded_not_guessed_from_equal_numbers(monkeypatch):
    """상품명과 DB 중량 숫자가 같아도, 실제로 DB 값을 썼으면 상품명 표기라고 기록하지 않는다 (GPT 재현 1)."""
    monkeypatch.setenv("CHAT_TRUST_UPSTREAM_WEIGHT", "1")
    res = search([it(1, "국산 삼겹살 500g", 9000, weight_g=500, weight_verified=True), it(2, "국산 삼겹살 1kg", 23000)])
    same = next(i for i in res.items if i.product.title == "국산 삼겹살 500g")
    assert weight_ev(same).method == "unknown" and "DB 대체 경로" in weight_ev(same).source
    other = next(i for i in res.items if i.product.title == "국산 삼겹살 1kg")
    assert weight_ev(other).method == "title_parse"


def test_audit_covers_compared_candidates_not_only_the_pick(monkeypatch):
    """고른 상품은 상품명 중량이어도, DB 중량 후보와 견줬으면 경고한다 (GPT 재현 3)."""
    monkeypatch.setenv("CHAT_TRUST_UPSTREAM_WEIGHT", "1")
    items = [it(1, "국산 삼겹살 300g", 3000), it(2, "국산 삼겹살 수육용", 9000, weight_g=500, weight_verified=True)]
    res = search(items)
    value = next(i for i in res.items if i.score.role == "value")
    assert weight_ev(value).method == "title_parse"
    assert any("중량 출처가 확인되지 않은 상품이 있어요 (국산 삼겹살 수육용)" in w for w in res.warnings)


def _web(db, items):
    from app.services.chat.service import ChatService
    from app.services.recipe_chat.service import RecipeChat

    s = ChatService(db, shopping=FakeShopping(items=items), recipe_chat=RecipeChat(statement_factory=str))
    return s.handle(None, message="삼겹살 추천")


def _notices(res):
    return [b["data"]["md"] for b in res["blocks"] if b["type"] == "notice"]


VERIFIED_MIXED = [dict(x, weight_verified=True) if x.get("weight_g") else x for x in MIXED]


def test_flag_alone_does_not_restore_unverified_db_weights(monkeypatch):
    """CHAT_TRUST_UPSTREAM_WEIGHT=1 이어도 행별 확인 표시가 없는 DB 중량은 쓰지 않는다 (p33, 일괄 복구 방지)."""
    monkeypatch.setenv("CHAT_TRUST_UPSTREAM_WEIGHT", "1")
    by = {i.product.title: i for i in search(MIXED).items}
    assert by["국산 삼겹살 구이용"].product.weight_g is None and by["국산 삼겹살 구이용"].offer.per100g_krw is None
    assert by["국산 삼겹살 수육용"].product.weight_g is None
    by = {i.product.title: i for i in search(VERIFIED_MIXED).items}
    assert by["국산 삼겹살 구이용"].product.weight_g == 1000


def test_rest_screen_gets_the_warning_and_no_title_label_on_db_weight(sqlite_db, monkeypatch):
    """REST 화면에도 경고가 가고(GPT 재현 2), DB 중량에는 '상품명 표기 기준' 설명이 붙지 않는다."""
    monkeypatch.setenv("CHAT_TRUST_UPSTREAM_WEIGHT", "1")
    on = _web(sqlite_db, VERIFIED_MIXED)
    assert any("중량 출처가 확인되지 않은" in n for n in _notices(on))
    monkeypatch.delenv("CHAT_TRUST_UPSTREAM_WEIGHT")
    off = _web(sqlite_db, MIXED)
    assert not any("중량 출처가 확인되지 않은" in n for n in _notices(off))
    from app.services.chat.explain import parse_units

    cards = [c for b in off["blocks"] if b["type"] == "product_list" for c in b["data"]["items"]]
    for c in cards:
        if "상품명 표기 기준" in " ".join(w["text"] for w in c.get("why") or []):
            assert c["weight_g"] == parse_units(c["title"])[1]   # 그 설명은 상품명에서 읽은 중량에만
        assert "weight_source" not in c                      # 서버 기록용 필드는 화면 응답에 나가지 않는다


def test_reselect_recomputes_old_cards_without_a_source():
    from app.services.chat import explain

    old = [{"key": "a", "title": "국산 삼겹살 구이용", "price": 10000, "total": 10000, "weight_g": 1000, "per100g": 1000,
            "mall": "쿠팡", "query": "삼겹살"},
           {"key": "b", "title": "국산 삼겹살 500g", "price": 9000, "total": 9000, "weight_g": 1000, "per100g": 900,
            "mall": "쿠팡", "query": "삼겹살"}]
    fixed = {c["key"]: explain.reweigh(c) for c in old}
    assert fixed["a"]["weight_g"] is None and fixed["a"]["per100g"] is None and fixed["a"]["weight_source"] is None
    assert fixed["b"]["weight_g"] == 500 and fixed["b"]["per100g"] == 1800 and fixed["b"]["weight_source"] == "title"
    res = to_result(rechoose(old, ask="삼겹살"), query="삼겹살")
    assert all((weight_ev(i) is None) or weight_ev(i).method == "title_parse" for i in res.items)


# ── p33: 비교에서 뺀 중량의 잔여 값(100g당·개당·설명)이 세 경로 모두에서 남지 않는다 ──────────────

AMBIG = [it(1, "사과 부사 가정용 5kg 10kg", 25000), it(2, "부사 사과 5kg", 30000), it(3, "부사 사과 3kg", 21000),
         it(4, "닭가슴살 섞음 100g 10개", 15000)]
UNUSABLE = ("사과 부사 가정용 5kg 10kg", "닭가슴살 섞음 100g 10개")


def _cards(res):
    return [c for b in res["blocks"] if b["type"] == "product_list" for c in b["data"]["items"]]


def _assert_no_residual(cards):
    for c in cards:
        if c["title"] in UNUSABLE:
            assert c.get("weight_g") is None and c.get("per100g") is None, c["title"]
            assert c.get("role") not in ("value", "ample")
            assert not any("100g당" in (w.get("text") if isinstance(w, dict) else str(w)) for w in c.get("why") or [])


def test_no_residual_unit_price_in_first_search_budget_reselect_and_saved_compare(sqlite_db):
    from app.services.chat.service import ChatService
    from app.services.recipe_chat.service import RecipeChat

    owner = "11111111-2222-4333-8444-666666666666"
    s = ChatService(sqlite_db, shopping=FakeShopping(items=AMBIG), recipe_chat=RecipeChat(statement_factory=str))
    first = s.handle(None, message="사과 추천", owner=owner)
    _assert_no_residual(_cards(first))
    again = s.handle(first["session_id"], message="5만원 이하요")
    assert again["stage"] == "shopping_budget"
    _assert_no_residual(_cards(again))
    for c in _cards(first)[:4]:
        s.set_saved(owner, first["session_id"], c["key"], True)
    cmp = s.handle(None, message="관심 상품 비교해줘", owner=owner)
    assert cmp["stage"] == "saved_compare"
    _assert_no_residual(_cards(cmp))


def test_stale_saved_values_and_texts_are_replaced_on_reselect():
    """예전 규칙(마지막 중량)으로 저장된 카드의 100g당·역할·설명이 다시 고를 때 남지 않는다."""
    stale = [{"key": "a", "title": "사과 부사 가정용 5kg 10kg", "price": 25000, "total": 25000, "weight_g": 10000,
              "per100g": 250, "weight_source": "title", "role": "value", "role_label": "가성비",
              "why": [{"text": "후보 2개 중 100g당 가장 저렴해요 (250원/100g)", "basis": "calc"}],
              "reason": "후보 2개 중 100g당 가장 저렴해요 (250원/100g)", "mall": "naver", "query": "사과"},
             {"key": "b", "title": "부사 사과 5kg", "price": 30000, "total": 30000, "weight_g": 5000, "per100g": 600,
              "weight_source": "title", "mall": "naver", "query": "사과"}]
    picked = rechoose(stale, ask="사과")
    cards = picked["picks"] + picked["others"]
    a = next(c for c in cards if c["key"] == "a")
    assert a["weight_g"] is None and a["per100g"] is None and a["role"] != "value"
    assert "250원/100g" not in (a.get("reason") or "") and not any("100g당" in w["text"] for w in a.get("why") or [])


def test_warning_reaches_all_three_rest_paths_when_verified_db_weight_is_used(sqlite_db, monkeypatch):
    from app.services.chat.service import ChatService
    from app.services.recipe_chat.service import RecipeChat

    monkeypatch.setenv("CHAT_TRUST_UPSTREAM_WEIGHT", "1")
    owner = "11111111-2222-4333-8444-777777777777"
    s = ChatService(sqlite_db, shopping=FakeShopping(items=VERIFIED_MIXED),
                    recipe_chat=RecipeChat(statement_factory=str))
    warn = "중량 출처가 확인되지 않은"
    first = s.handle(None, message="삼겹살 추천", owner=owner)
    assert any(warn in n for n in _notices(first))
    again = s.handle(first["session_id"], message="5만원 이하요")
    assert any(warn in n for n in _notices(again))
    for c in _cards(first)[:4]:
        s.set_saved(owner, first["session_id"], c["key"], True)
    cmp = s.handle(None, message="관심 상품 비교해줘", owner=owner)
    assert any(warn in n for n in _notices(cmp))
