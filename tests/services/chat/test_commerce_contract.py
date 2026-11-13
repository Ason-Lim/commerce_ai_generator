"""계약 테스트 (설계서 2단계 완료 기준): 같은 입력 → /api/chat 과 서비스 경계의 상품·순위·역할·사유·고지가 같다.

새 서비스(app/services/commerce)는 기존 함수를 감싸기만 하므로, 여기서 어긋나면 서비스 쪽이 틀린 것이다.
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

from app.domain.commerce import policies
from app.domain.commerce.models import CommerceResult
from app.domain.commerce.requests import RecipeRequest, SearchRequest
from app.services.chat.service import ChatService
from app.services.commerce.recipes import get_recipe
from app.services.commerce.search import search_products
from app.services.recipe_chat.catalog import RecipeResolver
from app.services.recipe_chat.service import RecipeChat

from .conftest import FakeShopping

ITEMS = [
    {"product_name": "꿀사과 3kg 가정용", "price": 21000, "shipping_fee": 3000, "product_url": "https://shop.example.com/1",
     "platform_name": "coupang", "is_coupang": True, "is_rocket": True},
    {"product_name": "부사 사과 5kg", "price": 29000, "product_url": "https://shop.example.com/2",
     "platform_name": "coupang", "is_coupang": True, "is_free_shipping": True},
    {"product_name": "사과 선물세트 2kg", "price": 35000, "shipping_fee": 0, "product_url": "https://shop.example.com/3",
     "platform_name": "naver", "seller_name": "과수원A", "rating": 4.8, "review_count": 31},
    {"product_name": "못난이 사과 10kg", "price": 32000, "product_url": "https://shop.example.com/4",
     "platform_name": "naver", "final_score": 71.5},
    {"product_name": "사과즙 30포", "price": 18900, "product_url": "https://shop.example.com/5",
     "platform_name": "coupang", "is_coupang": True},
]


def _web(db, items, text, error=None):
    svc = ChatService(db, shopping=FakeShopping(items=items, error=error), recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message=text)
    return res, [it for b in res["blocks"] if b["type"] == "product_list" for it in b["data"]["items"]]


def _svc(items, text, error=None) -> CommerceResult:
    return search_products(SearchRequest(text=text), shopping=FakeShopping(items=items, error=error))


def _why(entries):
    return [w["text"] if isinstance(w, dict) else str(w) for w in entries or []]


def web_sig(items):
    return [(i["rank"], i.get("key"), i["title"], i["price"], i.get("total"), i.get("role"), _why(i.get("why")))
            for i in items if i.get("mall") != "네이버 (쇼핑커넥트)"]


def svc_sig(result):
    return [(i.score.rank, i.product.key, i.product.title, i.offer.price_krw, i.offer.total_krw, i.score.role,
             [r.text for r in i.score.reasons]) for i in result.items if i.section != "connect"]


@pytest.mark.parametrize("text", ["사과 추천해줘", "3만원 이하 사과 추천해줘", "사과 가성비 좋은 거", "부모님 선물용 사과",
                                  "1만원 이하 사과"])
def test_same_products_ranks_roles_and_reasons_as_api_chat(sqlite_db, text):
    _res, web_items = _web(sqlite_db, ITEMS, text)
    result = _svc(ITEMS, text)
    assert web_items, "fixture should produce cards"
    assert svc_sig(result) == web_sig(web_items)


def test_prices_stay_integer_won_and_unknown_shipping_stays_unknown(sqlite_db):
    result = _svc(ITEMS, "사과 추천해줘")
    by_title = {i.product.title: i.offer for i in result.items}
    assert by_title["못난이 사과 10kg"].shipping_krw is None and by_title["못난이 사과 10kg"].total_krw is None
    # 2026-11-13 (S5): 배송비는 상태로만 — 적힌 금액·무료 표시는 총액으로 확정하지 않는다
    assert by_title["꿀사과 3kg 가정용"].total_krw is None and by_title["꿀사과 3kg 가정용"].shipping_krw == 3000
    assert by_title["꿀사과 3kg 가정용"].shipping_status == "fee_label"
    assert by_title["부사 사과 5kg"].total_krw is None and by_title["부사 사과 5kg"].shipping_krw is None
    assert by_title["부사 사과 5kg"].shipping_status == "free_label"
    assert by_title["사과 선물세트 2kg"].shipping_status == "free_label"     # 출처의 0원도 '무료 표시'로
    assert by_title["못난이 사과 10kg"].shipping_status == "unknown"


def test_platform_merchant_and_url_are_separate(sqlite_db):
    result = _svc(ITEMS, "사과 추천해줘")
    gift = next(i for i in result.items if i.product.title == "사과 선물세트 2kg")
    assert (gift.offer.platform, gift.offer.merchant, gift.offer.product_url) == (
        "naver", "과수원A", "https://shop.example.com/3")


def test_affiliate_flag_never_changes_the_order(sqlite_db):
    flipped = [dict(it, is_coupang=not it.get("is_coupang")) for it in ITEMS]
    a = [(i.product.title, i.score.rank, i.score.role) for i in _svc(ITEMS, "사과 추천해줘").items]
    b = [(i.product.title, i.score.rank, i.score.role) for i in _svc(flipped, "사과 추천해줘").items]
    assert a == b


def test_disclosure_names_programs_and_operation_line(sqlite_db):
    result = _svc(ITEMS, "사과 추천해줘")
    assert result.disclosure.has_affiliate and result.disclosure.programs == [policies.COUPANG_PROGRAM]
    assert policies.COUPANG_DISCLOSURE in result.disclosure.text_ko
    assert policies.OPERATION_LINE in result.disclosure.text_ko
    plain = _svc([dict(it, is_coupang=False) for it in ITEMS], "사과 추천해줘")
    assert plain.disclosure.has_affiliate is False


def test_unsafe_url_is_dropped_like_go(sqlite_db):
    items = [dict(ITEMS[0], product_url="javascript:alert(1)")]
    result = _svc(items, "사과 추천해줘")
    assert result.items[0].offer.product_url is None


def test_rating_is_kept_as_unverified_evidence_not_score(sqlite_db):
    gift = next(i for i in _svc(ITEMS, "사과 추천해줘").items if i.product.title == "사과 선물세트 2kg")
    ev = {e.field: e for e in gift.evidence}
    assert ev["rating"].method == "unknown" and ev["rating"].usable_for_score is False
    assert not policies.score_usable(ev["rating"])


def test_engine_score_is_passed_through_only_when_present(sqlite_db):
    items = {i.product.title: i for i in _svc(ITEMS, "사과 추천해줘").items}
    assert items["못난이 사과 10kg"].score.engine_score == 71.5
    assert items["꿀사과 3kg 가정용"].score.engine_score is None


def test_budget_followup_only_without_budget(sqlite_db):
    assert _svc(ITEMS, "사과 추천해줘").followup.kind == "budget"
    assert _svc(ITEMS, "3만원 이하 사과").followup is None


def test_provider_failure_is_an_error_not_an_empty_list(sqlite_db):
    res, web_items = _web(sqlite_db, ITEMS, "사과 추천해줘", error=RuntimeError("down"))
    result = _svc(ITEMS, "사과 추천해줘", error=RuntimeError("down"))
    assert not web_items and any("불러오지 못했어요" in json.dumps(b, ensure_ascii=False) for b in res["blocks"])
    assert result.status == "error" and result.errors[0].code == "source_unavailable"


def _registry(tmp_path: Path) -> str:
    path = tmp_path / "connect.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["상품명", "쇼핑커넥트 링크", "키워드", "판매가", "스토어명", "링크 확인일"])
        w.writeheader()
        w.writerow({"상품명": "청송 사과 3kg", "쇼핑커넥트 링크": "https://naver.me/apple", "키워드": "사과",
                    "판매가": "25,000", "스토어명": "청송농원", "링크 확인일": "2026-11-02"})
        w.writerow({"상품명": "칠레 레드 와인 750ml", "쇼핑커넥트 링크": "https://naver.me/wine", "키워드": "와인",
                    "판매가": "15,000", "스토어명": "와인샵", "링크 확인일": "2026-11-02"})
    return str(path)


def test_connect_links_match_web_and_open_directly(sqlite_db, tmp_path, monkeypatch):
    monkeypatch.setenv("NAVER_CONNECT_REGISTRY_CSV", _registry(tmp_path))
    _res, web_items = _web(sqlite_db, ITEMS, "사과 추천해줘")
    result = _svc(ITEMS, "사과 추천해줘")
    web_connect = [(i["rank"], i["title"], i["url"]) for i in web_items if i.get("mall") == "네이버 (쇼핑커넥트)"]
    svc_connect = [(i.score.rank, i.product.title, i.offer.product_url) for i in result.items if i.section == "connect"]
    assert web_connect == svc_connect == [(len(ITEMS) + 1, "청송 사과 3kg", "https://naver.me/apple")]
    connect = next(i for i in result.items if i.section == "connect")
    assert connect.offer.opens_directly and connect.offer.affiliate_program == policies.CONNECT_PROGRAM
    assert policies.connect_disclosure() in result.disclosure.text_ko


def test_no_connect_links_for_alcohol(sqlite_db, tmp_path, monkeypatch):
    monkeypatch.setenv("NAVER_CONNECT_REGISTRY_CSV", _registry(tmp_path))
    wine = [{"product_name": "칠레 레드 와인 750ml", "price": 15000, "product_url": "https://shop.example.com/w",
             "platform_name": "coupang"}]
    _res, web_items = _web(sqlite_db, wine, "와인 추천해줘")
    result = _svc(wine, "와인 추천해줘")
    assert not [i for i in web_items if i.get("mall") == "네이버 (쇼핑커넥트)"]
    assert not [i for i in result.items if i.section == "connect"]
    assert svc_sig(result) == web_sig(web_items)


def test_recipe_by_id_matches_the_chat_card(sqlite_db):
    resolver = RecipeResolver()
    result = get_recipe(RecipeRequest(recipe_id="EPIS:467"), resolver=resolver)
    assert result.status == "ok"
    recipe = result.items[0]
    assert recipe.source_level == "source" and recipe.citation.startswith("출처:")
    assert recipe.content_hash == resolver.get("EPIS:467").content_hash()
    svc = ChatService(sqlite_db, shopping=FakeShopping(), recipe_chat=RecipeChat(statement_factory=str))
    sid = svc.handle(None, message="파스타 요리방법")["session_id"]
    web = svc.handle(sid, answers={"recipe": "EPIS:467"})
    assert web["stage"] == "recipe_guide" and recipe.title in json.dumps(web, ensure_ascii=False)


def test_recipe_by_name_card_or_followup():
    resolver = RecipeResolver()
    one = get_recipe(RecipeRequest(dish_name="크림파스타"), resolver=resolver)
    assert one.status == "ok" and one.items[0].recipe_id == resolver.get("EPIS:467").recipe_id
    many = get_recipe(RecipeRequest(dish_name="파스타"), resolver=resolver)
    assert many.status == "needs_followup" and many.followup.kind == "choose_recipe" and many.followup.options
    assert get_recipe(RecipeRequest(), resolver=resolver).status == "error"


def test_domain_does_not_import_web_or_protocol_packages():
    code = ("import sys, app.domain.commerce, app.domain.commerce.policies, app.domain.commerce.requests;"
            "print([m for m in ('fastapi', 'mcp', 'starlette') if m in sys.modules])")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                         cwd=Path(__file__).resolve().parents[3], check=True)
    assert out.stdout.strip() == "[]"


def test_result_is_json_serialisable_for_adapters(sqlite_db):
    data = _svc(ITEMS, "사과 추천해줘").model_dump(mode="json")
    assert data["schema_version"] == "commerce.v1" and data["status"] == "ok"
    json.dumps(data, ensure_ascii=False)
