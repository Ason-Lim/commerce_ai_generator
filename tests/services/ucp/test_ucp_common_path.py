"""p47 (GPT 검토 11-06 17:25): 원화 UCP 응답 → 카드 → 공통 collect → enrich → choose → 공통 모델까지 연결 검증.

앱 경로에는 연결하지 않는다 — collect(extra_cards=...) 는 이 검증용 입구이고 앱 코드는 넘기지 않는다 (마지막 테스트로 고정).
확인: 카드 key 보존 · seller_unit_price 보존(표시만) · 가격 비교 차단이 choose·KAMIS 시세·공통 모델 근거까지 유지.
"""
from __future__ import annotations

import pathlib
import re

import pytest

from app.domain.commerce import policies
from app.domain.commerce.requests import SearchRequest
from app.services.commerce import search
from app.services.public_price import kamis
from app.services.ucp import client, discovery, mapping
from tests.services.chat.conftest import FakeShopping
from tests.services.ucp.test_ucp_catalog import PROFILE, Http, Resp, fx

COUPANG = [{"product_name": "제주 감귤 3kg", "price": 21000, "shipping_fee": 0, "platform_name": "쿠팡",
            "product_url": "https://www.coupang.com/vp/products/1"},
           {"product_name": "제주 감귤 5kg", "price": 30000, "shipping_fee": 0, "platform_name": "쿠팡",
            "product_url": "https://www.coupang.com/vp/products/2"}]


def _ucp_source(resp=None, *, fail=False):
    """검증을 통과한 실제 client.search 결과로 카드를 만드는 출처 (질의어는 기록만)."""
    seen = []

    def source(query, terms):
        seen.append((query, list(terms or [])))
        if fail:
            raise RuntimeError("판매자 응답 없음")
        m = discovery.negotiate("mall.example.kr", fx("profile_rest.json"))
        out = client.search(m, query, http=Http(post=Resp(200, resp or fx("search_krw.json"))), profile_url=PROFILE)
        cards, _ = mapping.cards_from(out, m, "예시몰")
        return cards

    source.seen = seen
    return source


def _run(source, text="감귤 추천해줘"):
    return search.search_products(SearchRequest(text=text), shopping=FakeShopping(items=COUPANG),
                                  annotate_prices=False, allow_preview=False, extra_cards=source)


def _ucp_items(res):
    return [i for i in res.items if i.offer.platform == "예시몰"]


def _usage(ev, use):
    return next(d.verdict for d in ev.usage if d.use == use)


def test_krw_ucp_cards_flow_through_collect_choose_and_projection():
    source = _ucp_source()
    res = _run(source)
    assert source.seen and source.seen[0][0]                               # 공통 검색어가 출처로 전달됨
    ucp = _ucp_items(res)
    expected = {c["key"] for c in mapping.cards_from(
        client.search(discovery.negotiate("mall.example.kr", fx("profile_rest.json")), "감귤",
                      http=Http(post=Resp(200, fx("search_krw.json"))), profile_url=PROFILE),
        discovery.negotiate("mall.example.kr", fx("profile_rest.json")), "예시몰")[0]}
    assert ucp and {i.product.key for i in ucp} <= expected                # 변환 key == 공통 모델 key
    for i in ucp:
        assert i.section in ("picks", "others")
        assert i.offer.per100g_krw is None and i.offer.per_unit_krw is None
        assert i.product.weight_g is None and i.product.unit_count is None
        assert i.offer.link_type == "direct"
        assert not any(e.field in ("weight_g", "unit_count") for e in i.evidence)
        price = next(e for e in i.evidence if e.field == "price")
        assert price.method == "ucp_catalog" and price.source == "mall.example.kr"
        assert _usage(price, "price_compare") == "block" and _usage(price, "score") == "block"


def test_seller_unit_price_is_preserved_for_display_only():
    res = _run(_ucp_source())
    item = next(i for i in _ucp_items(res) if i.product.title.endswith("3kg"))
    sup = next(e for e in item.evidence if e.field == "seller_unit_price")
    assert sup.value == "630" and sup.raw_text == "100g당 630원 (판매자 표시)"   # 판매자 값 그대로 (다시 계산 안 함)
    assert _usage(sup, "display") == "allow_labelled"
    assert _usage(sup, "price_compare") == "block" and _usage(sup, "score") == "block"
    assert sup.policy_version == policies.POLICY_VERSION
    assert any("UCP 판매처 가격은 카탈로그 값" in w for w in res.warnings)
    assert not any("중량 출처가 확인되지 않은" in w for w in res.warnings)   # 선택 감사에 걸리지 않음


def test_seller_disclosure_survives_to_the_common_model():
    res = _run(_ucp_source())
    gift = next((i for i in _ucp_items(res) if "선물세트" in i.product.title), None)
    if gift is None:
        pytest.skip("관련성 필터에서 선물세트가 빠짐")
    texts = [e.value for e in gift.evidence if e.field == "disclosure"]
    assert texts == ["이 상품은 견과류를 사용하는 시설에서 포장합니다."]


@pytest.mark.parametrize("unit_amount, suffix", [(1, " 10kg"), (99999, " 100g x 50팩"), (5, " 30구")])
def test_roles_and_order_do_not_move_with_seller_unit_price_or_title_numbers(unit_amount, suffix):
    def sig(res):
        return [(i.product.key, i.score.role) for i in res.items if i.section in ("picks", "others")]

    resp = fx("search_krw.json")
    for prod in resp["products"]:
        prod["title"] += suffix
        for v in prod["variants"]:
            if v.get("unit_price"):
                v["unit_price"]["amount"] = unit_amount
    base, changed = _run(_ucp_source()), _run(_ucp_source(resp))
    assert sig(base) == sig(changed)                                       # key 가 같으므로 key 로 바로 비교
    value = [i for i in changed.items if i.score.role in ("value", "ample")]
    assert value and all(i.offer.platform == "쿠팡" for i in value)        # 가성비·넉넉한 양은 비교 가능한 카드끼리만


def test_ucp_cards_never_get_a_public_price_comparison():
    rows = kamis.parse({"error_code": "000", "price": [
        {"product_cls_code": "01", "category_name": "축산물", "productName": "계란/XL30구(일반란)", "unit": "30구",
         "dpr1": "6,664", "lastest_day": "2026-10-29"}]})
    card = {"title": "무항생제 특란 30구", "price": 9900, "weight_g": None}
    assert kamis.reference(card, rows) is not None                          # 일반 카드는 상품명 '30구'로 견줌
    assert kamis.reference(dict(card, price_compare_blocked="ucp_seller_unit_price"), rows) is None


def test_annotate_prices_on_keeps_ucp_cards_without_market_ref(monkeypatch):
    monkeypatch.setattr(kamis, "entries", lambda *a, **k: kamis.parse({"error_code": "000", "price": [
        {"product_cls_code": "01", "category_name": "과일류", "productName": "감귤/노지", "unit": "10kg",
         "dpr1": "30,000", "lastest_day": "2026-10-29"}]}))
    monkeypatch.setenv("KAMIS_REFERENCE", "1")
    got = search.collect(SearchRequest(text="감귤 추천해줘"), shopping=FakeShopping(items=COUPANG),
                         allow_preview=False, extra_cards=_ucp_source())
    cards = got["picked"]["picks"] + got["picked"]["others"]
    assert any(c.get("ucp") for c in cards)
    assert all("market_ref" not in c for c in cards if c.get("ucp"))


def test_a_failing_extra_source_leaves_shopping_results_intact():
    res = _run(_ucp_source(fail=True))
    assert res.status == "ok" and res.items and not _ucp_items(res)
    assert [i.product.title for i in res.items if i.section in ("picks", "others")] == \
        [i.product.title for i in _run(None).items if i.section in ("picks", "others")]


def test_without_extra_cards_the_result_is_unchanged():
    a = _run(None).model_dump(mode="json")
    b = search.search_products(SearchRequest(text="감귤 추천해줘"), shopping=FakeShopping(items=COUPANG),
                               annotate_prices=False, allow_preview=False).model_dump(mode="json")
    a.pop("request_id"), b.pop("request_id")
    assert a == b


def test_app_code_never_passes_extra_cards():
    """연결 검증용 입구 — 앱 경로(어댑터·서비스)는 넘기지 않는다 (공통 검색 미연결 유지)."""
    root = pathlib.Path(__file__).resolve().parents[3] / "app"
    users = [p for p in root.rglob("*.py")
             if re.search(r"extra_cards\s*=", p.read_text(encoding="utf-8"))
             and p.as_posix().endswith("app/services/commerce/search.py") is False]
    assert users == []
    src = (root / "services/commerce/search.py").read_text(encoding="utf-8")
    assert re.findall(r"extra_cards\s*=\s*(\w+)", src) == ["extra_cards"]  # search_products → collect 전달만


def test_title_counts_on_ucp_cards_are_not_projected_as_comparable_evidence():
    """상품명에 '10입'이 있어도 UCP 카드는 개수를 '상품명 표기 기준 비교 허용' 근거로 내보내지 않는다."""
    resp = fx("search_krw.json")
    for prod in resp["products"]:
        prod["title"] += " 10입"
    res = _run(_ucp_source(resp))
    ucp = _ucp_items(res)
    assert ucp and all(i.product.unit_count is None for i in ucp)
    assert not any(e.field == "unit_count" for i in ucp for e in i.evidence)
