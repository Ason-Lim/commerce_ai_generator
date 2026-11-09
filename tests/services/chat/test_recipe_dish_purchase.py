"""2026-11-06 — "제철 굴로 굴전이랑 굴국밥 하려면 몇 kg 사야 해?": 요리별 필요량 + 레시피 + 상품을 한 답에 (모의 시험).

실제 화면에서는 '사야'를 요리 이름으로 읽어 "어떤 사야 요리를 만들까요?"(해초무침 …)가 나왔고 상품은 없었다.
"""
from __future__ import annotations

import json

from app.services.chat.service import ChatService
from app.services.recipe_chat import dish_shopping as DS
from app.services.recipe_chat.catalog_store import RecipeCatalog, StaticCatalog
from app.services.recipe_chat.service import RecipeChat


def rec(rid, name, servings, *ings):
    return {"id": rid, "name": name, "source": "epis", "servings": servings, "meta": [servings],
            "ingredients": [{"name": n, "amount": a} for n, a in ings], "steps": [{"text": "섞어 주세요."}] * 3}


CATALOG = RecipeCatalog([rec("e-1", "달래굴파전", "2인분", ("달래", "100g"), ("굴", "80g"), ("밀가루", "1컵")),
                         rec("e-2", "굴무침", "2인분", ("굴", "300g"), ("무", "100g")),
                         rec("e-3", "해초무침", "2인분", ("해초", "100g"))])


def md(res):
    return "\n".join(b["data"].get("md", "") for b in res["blocks"] if b["type"] in ("text", "notice"))


def test_the_sentence_is_read_without_a_model():
    assert DS.parse("제철 굴로 굴전이랑 굴국밥 하려면 몇 kg 사야 해?") == {"dishes": ["굴전", "굴국밥"], "ingredient": "굴",
                                                                 "servings": None}
    assert DS.parse("굴전이랑 굴국밥 4인분씩 하려면 굴 얼마나 사야 해?")["servings"] == 4
    assert DS.parse("소고기로 미역국 끓이려면 몇 g 사야 돼?") == {"dishes": ["미역국"], "ingredient": "소고기", "servings": None}
    assert DS.parse("김치찌개 만드는 법") is None and DS.parse("빼빼로 몇 개 사야 해?") is None


def make(sqlite_db, shopping, guesses):
    calls = []

    def estimator(text):
        calls.append(json.loads(text))
        return {"amounts": [{"dish": d, "grams_per_serving": g, "note": "깐 굴 기준"} for d, g in guesses.items()]}
    chat = RecipeChat(statement_factory=str, catalog_provider=StaticCatalog(CATALOG))
    chat.amount_estimator = estimator
    return ChatService(sqlite_db, shopping=shopping, recipe_chat=chat), calls


def test_amounts_recipes_and_products_come_together(sqlite_db, shopping):
    shopping.items = [{"product_name": "통영 깐굴 생굴, 1개, 500g", "price": 15000, "product_url": "https://shop.example.com/1"},
                      {"product_name": "통영 생굴 1kg 업소용", "price": 20000, "product_url": "https://shop.example.com/2"},
                      {"product_name": "영광 굴비 10미", "price": 30000, "product_url": "https://shop.example.com/3"},
                      {"product_name": "굴소스 500g", "price": 5000, "product_url": "https://shop.example.com/4"}]
    svc, calls = make(sqlite_db, shopping, {"굴전": 100, "굴국밥": 80})
    res = svc.handle(None, message="제철 굴로 굴전이랑 굴국밥 하려면 몇 kg 사야 해?")
    text = md(res)
    assert res["stage"] == "recipe_dish_purchase" and "사야 요리" not in text
    assert "- **굴전**: 굴 **200g** — 공공 레시피가 없어 일반 조리 기준 AI 추정 · 원문 아님 (깐 굴 기준) · 참고로 다른 요리인 " \
           "공공 레시피 달래굴파전 2인분 80g" in text                       # a different dish is a reference, never the amount
    assert "**합계 약 360g**" in text and calls[0] == {"재료": "굴", "요리": ["굴전", "굴국밥"]}
    assert [q for q, _p, _s in shopping.calls] == ["굴"]
    titles = [it["title"] for b in res["blocks"] if b["type"] == "product_list" for it in b["data"]["items"]]
    assert titles == ["통영 깐굴 생굴, 1개, 500g", "통영 생굴 1kg 업소용"]        # 굴비·굴소스 are not 굴
    assert "굴전·굴국밥 각 2인분 기준 필요량 **360g**" in text
    chips = [c for b in res["blocks"] if b["type"] == "chips" for c in b["data"]["items"]]
    assert chips == ["굴전 만드는 법", "굴국밥 만드는 법", "4인분씩으로 다시 계산"]
    # 2026-11-09 A안: 비교는 상품 목록 끝 카드로 (위 칩이 아니라)
    types = [b["type"] for b in res["blocks"]]
    cta = res["blocks"][-1]
    assert cta["type"] == "compare_cta" and types.index("compare_cta") > max(i for i, t in enumerate(types) if t == "product_list")
    assert cta["data"] == {"label": "굴 상품 2개, 한눈에 비교하기", "sub": "총가격 · 100g당 가격 · 필요량 360g 대비 · 깐굴 표기",
                           "send": "굴 상품 비교"}
    # recalculated on the same basis (no second estimate)
    res = svc.handle(res["session_id"], message="4인분씩으로 다시 계산")
    assert "굴 **400g**" in md(res) and "**합계 약 720g**" in md(res) and len(calls) == 1


def test_a_public_recipe_of_the_same_name_gives_the_amount(sqlite_db, shopping):
    svc, calls = make(sqlite_db, shopping, {})
    res = svc.handle(None, message="굴로 굴무침 하려면 몇 g 사야 해?")
    assert "- **굴무침**: 굴 **300g** — 공공 레시피 '굴무침' 2인분 300g 기준" in md(res) and calls == []


def test_shown_products_are_compared_in_one_table(sqlite_db, shopping):
    """2026-11-06 p35: 레시피 후보 비교처럼 추천 상품도 비교 — 새 검색 없이, 같은 기준으로."""
    shopping.items = [{"product_name": "통영 생굴 최상급 1kg 버블세척", "price": 13350, "shipping_fee": 0, "is_coupang": True,
                       "product_url": "https://shop.example.com/1"},
                      {"product_name": "통영 산지직송 최상급 세척 깐 대굴, 2개, 1kg", "price": 33780, "shipping_fee": 0,
                       "is_coupang": True, "product_url": "https://shop.example.com/2"},
                      {"product_name": "통영 깐굴 생굴, 1개, 500g", "price": 9000, "shipping_fee": 0, "is_coupang": True,
                       "product_url": "https://shop.example.com/3"},
                      {"product_name": "통영 생굴 최상급 당일발송", "price": 17500, "shipping_fee": 0, "is_coupang": True,
                       "product_url": "https://shop.example.com/4"},
                      {"product_name": "굴소스 500g", "price": 5000, "product_url": "https://shop.example.com/5"}]
    svc, _calls = make(sqlite_db, shopping, {"굴전": 100, "굴국밥": 100})
    res = svc.handle(None, message="제철 굴로 굴전이랑 굴국밥 하려면 몇 kg 사야 해?")
    sid = res["session_id"]
    n_calls = len(shopping.calls)
    res = svc.handle(sid, chip="굴 상품 비교")
    assert res["stage"] == "product_compare" and len(shopping.calls) == n_calls          # no new search
    assert res["blocks"][0]["type"] == "notice" and "쿠팡 파트너스" in res["blocks"][0]["data"]["md"]   # disclosure on top
    table = next(b["data"] for b in res["blocks"] if b["type"] == "product_compare")
    rows = {r["title"]: r for r in table["rows"]}
    assert "굴소스 500g" not in rows                                                   # not the same ingredient
    assert table["need"]["display"] == "400g"
    a, b, c = rows["통영 생굴 최상급 1kg 버블세척"], rows["통영 산지직송 최상급 세척 깐 대굴, 2개, 1kg"], rows["통영 깐굴 생굴, 1개, 500g"]
    assert (a["pack"], a["per100g"], a["fit"], a["prep"]) == ("1kg", 1335, "fits", "손질 상태 미표기")
    assert (b["pack"], b["per100g"], b["fit"], b["prep"]) == ("1kg×2 (총 2kg)", 1689, "bulk", "깐굴 표기")
    assert (c["per100g"], c["prep"]) == (1800, "깐굴 표기")
    unknown = rows["통영 생굴 최상급 당일발송"]
    assert unknown["pack"] is None and unknown["per100g"] is None and unknown["fit"] == "unknown"
    assert table["best_total"] == c["key"] and table["best_per100g"] == a["key"]   # lowest total among packs that fit
    assert all(r["go"].startswith(f"/go/{sid}/k/") and r["affiliate"] for r in table["rows"])
    assert any("껍질 무게" in n for n in table["notes"]) and any("판매자 주장" in n for n in table["notes"])


def test_compare_without_shown_products_falls_through(sqlite_db, shopping):
    svc, _calls = make(sqlite_db, shopping, {})
    res = svc.handle(None, message="굴 상품 비교")
    assert res["stage"] != "product_compare"


def test_square_brackets_in_a_title_do_not_break_the_link():
    """2026-11-09: '[생방송 다시보기] 굴전…' 제목 때문에 링크가 깨져 주소가 그대로 보였다."""
    from app.services.recipe_chat.service import md_label

    assert md_label("[생방송 다시보기] 굴전 맛있게") == "(생방송 다시보기) 굴전 맛있게"
