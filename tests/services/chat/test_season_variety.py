"""2026-11-11: "딸기 언제부터 맛있어? 품종별 차이 알려줘" — 제철·품종 답을 먼저, 상품은 품종별로."""
from __future__ import annotations

from app.services.chat import food_tips as F
from app.services.chat.service import ChatService
from app.services.recipe_chat.service import RecipeChat

Q = "딸기 언제부터 맛있어? 품종별 차이 알려줘"


class ByQuery:
    """검색어에 맞는 상품만 돌려주는 쇼핑 흉내."""
    def __init__(self, table):
        self.table, self.calls = table, []

    def __call__(self, query, priority, session_id):
        self.calls.append(query)
        for key, items in self.table.items():
            if key in query:
                return {"items": items}
        return {"items": []}


def it(name, price):
    return {"product_name": name, "price": price, "shipping_fee": 0, "is_coupang": True,
            "product_url": f"https://www.coupang.com/vp/products/{abs(hash(name)) % 100000}"}


TIPS = {"food": "딸기", "tips": [], "season": "보통 12월부터 이듬해 5월까지, 1~3월이 가장 맛있어요",
        "varieties": [{"name": "설향", "note": "과즙이 많고 부드러워요"},
                      {"name": "금실", "note": "단단하고 당도가 높은 편이에요"},
                      {"name": "가짜품종", "note": "지어낸 품종이에요"}]}


def _svc(sqlite_db, shop, tips=TIPS):
    return ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str),
                       food_tips=lambda t: tips)


def md(res):
    return "\n".join(b["data"].get("md", "") for b in res["blocks"] if b["type"] in ("text", "notice"))


def test_season_and_variety_questions_are_food_questions():
    assert F.is_food_question(Q) and F.asks_season(Q) and F.asks_varieties(Q)
    assert F.is_food_question("사과 제철이 언제야") and F.is_food_question("사과 종류 알려줘")
    assert F.is_food_question("딸기 제철 알려줘") and F.is_food_question("귤 제철은 언제예요?")
    for t in ("딸기 추천해줘", "언제 배송돼?", "귤 10kg 박스로 사려는데 크기별로 뭐가 맛있어?",
              "제철 굴로 굴전이랑 굴국밥 하려면 몇 kg 사야 해?", "제철 과일 추천해줘"):
        assert not F.is_food_question(t), t


def test_season_and_varieties_are_validated_and_only_when_asked():
    raw = {"tips": [], "season": "12월~5월", "varieties": [{"name": "설 향", "note": "과즙이 많아요"},
                                                            {"name": "<b>", "note": "x"}, "금실"]}
    got = F.validated(raw, Q)
    assert got["season"] == "12월~5월" and got["varieties"] == [{"name": "설향", "note": "과즙이 많아요"}]
    assert "season" not in F.validated(raw, "귤 냉장 보관해도 돼?")


def test_answer_comes_first_then_products_by_variety(sqlite_db):
    shop = ByQuery({"설향": [it("논산 설향 딸기 500g", 15900), it("설향딸기 1kg", 28900), it("딸기 1kg", 9900)],
                    "금실": [it("금실 딸기 500g", 19900)]})
    res = _svc(sqlite_db, shop).handle(None, message=Q)
    text = md(res)
    # 답이 먼저
    first_list = next(i for i, b in enumerate(res["blocks"]) if b["type"] == "product_list")
    answer = next(i for i, b in enumerate(res["blocks"]) if "제철" in (b["data"].get("md") or ""))
    assert answer < first_list
    assert "1~3월이 가장 맛있어요" in text and "- **설향**: 과즙이 많고 부드러워요" in text and F.LABEL in text
    lists = {b["data"]["title"]: [i["title"] for i in b["data"]["items"]]
             for b in res["blocks"] if b["type"] == "product_list"}
    assert set(lists) == {"설향 상품 2개", "금실 상품 1개"}
    assert "딸기 1kg" not in lists["설향 상품 2개"]                 # 품종 이름이 없는 상품은 빼기
    assert "가짜품종 품종은 상품명에 품종이 적힌 상품을 찾지 못해" in text   # 지어낸 품종은 상품 묶음 없음
    assert sorted(shop.calls) == sorted(["설향 딸기", "금실 딸기", "가짜품종 딸기"])
    assert res["blocks"][0]["data"].get("affiliate") is True        # 제휴 고지 맨 위
    for b in res["blocks"]:
        for i in (b["data"].get("items") or []) if b["type"] == "product_list" else []:
            assert all(isinstance(w, dict) and w.get("text") for w in i.get("why") or [])


def test_no_variety_products_falls_back_to_the_usual_list(sqlite_db):
    shop = ByQuery({"딸기": [it("딸기 1kg", 9900), it("딸기 500g", 6900)]})
    tips = dict(TIPS, varieties=[{"name": "없는품종", "note": "상품이 없어요"}])
    res = _svc(sqlite_db, shop, tips).handle(None, message=Q)
    titles = [b["data"].get("title") for b in res["blocks"] if b["type"] == "product_list"]
    assert not any((t or "").endswith("상품 1개") and "없는품종" in t for t in titles)
    assert any(b["type"] == "product_list" for b in res["blocks"])   # 평소 목록
    assert "1~3월이 가장 맛있어요" in md(res)
