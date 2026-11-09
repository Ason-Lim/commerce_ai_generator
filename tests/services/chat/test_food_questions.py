"""식품 상담 (2026-11-04): 홈 화면 예시 질문이 레시피 고르기로 가서 '어떤 보관해 요리', '어떤 거 요리'가 나왔다."""
from __future__ import annotations

from app.services.chat import food_tips as F
from app.services.chat.service import ChatService
from app.services.recipe_chat.service import RecipeChat
from tests.services.chat.conftest import FakeShopping

HONGSI = "대봉감 홍시 만들려면 며칠 두고 어떻게 보관해?"
GWAMEGI = "과메기 처음 사보는데 비린내 없이 먹는 법이랑 같이 살 거 알려줘"


class RecipeNLU:
    """실제 화면에서 이 질문들을 '레시피'로 분류한 NLU 를 흉내 낸다."""
    def parse(self, text):
        return {"action_intent": "recipe"}


def md(res):
    return "\n".join(b["data"].get("md", "") for b in res["blocks"] if b["type"] in ("text", "notice"))


def test_food_questions_are_recognised_and_recipes_are_not():
    assert F.is_food_question(HONGSI) and F.is_food_question(GWAMEGI)
    assert F.is_food_question("귤 냉장 보관해도 돼?") and F.is_food_question("굴 세척 어떻게 해?")
    assert not F.is_food_question("크림파스타 만드는 법") and not F.is_food_question("홍시 레시피 알려줘")
    assert not F.is_food_question("사과 추천해줘")
    assert F.wants_companions(GWAMEGI) and not F.wants_companions(HONGSI)


def test_answers_are_validated():
    got = F.validated({"tips": ["상온에서 5~7일 두면 말랑해져요", "1kg 9,900원이 적당해요", "면역력에 좋아요", "x"],
                       "buy_with": ["쌈배추", "김", "초고추장", "http://x", "아주아주긴이름의곁들이식품세트"]}, GWAMEGI)
    assert got == {"tips": ["상온에서 5~7일 두면 말랑해져요"], "buy_with": ["쌈배추", "김", "초고추장"]}
    assert F.validated({"tips": ["a b c d"], "buy_with": ["김"]}, HONGSI)["buy_with"] == []   # 묻지 않았으면 빼기
    assert F.validated(None, HONGSI) == {"tips": [], "buy_with": []}


def _svc(sqlite_db, items, tips=None):
    return ChatService(sqlite_db, shopping=FakeShopping(items=items), nlu_loader=lambda: RecipeNLU(),
                       recipe_chat=RecipeChat(statement_factory=str), food_tips=tips)


def test_hongsi_question_gets_tips_and_products_not_a_recipe_choice(sqlite_db):
    persimmon = [{"product_name": "청도 대봉감 5kg", "price": 29900, "product_url": "https://www.coupang.com/p",
                  "platform_name": "coupang", "is_coupang": True}]
    shop = FakeShopping(items=persimmon)
    svc = ChatService(sqlite_db, shopping=shop, nlu_loader=lambda: RecipeNLU(), recipe_chat=RecipeChat(statement_factory=str),
                      food_tips=lambda t: {"food": "대봉감", "tips": ["상온에서 꼭지를 아래로 두고 1~2주 익혀요", "말랑해지면 냉동해 두고 먹어요"],
                                           "buy_with": ["곶감"]})
    res = svc.handle(None, message=HONGSI)
    text = md(res)
    assert "요리를 만들까요" not in text and "보관해 요리" not in text
    assert "**대봉감** 질문에 대한 일반 정보예요." in text and "- 상온에서 꼭지를 아래로 두고 1~2주 익혀요" in text
    assert F.LABEL in text
    assert "같이 사면 좋은 것" not in text                     # 묻지 않았다
    assert shop.calls[0][0] == "대봉감"
    assert any(b["type"] == "product_list" for b in res["blocks"])
    assert res["blocks"][0]["data"].get("affiliate") is True     # 제휴 고지는 여전히 맨 위


def test_gwamegi_question_lists_companions_as_chips(sqlite_db):
    svc = _svc(sqlite_db, [], tips=lambda t: {"food": "과메기", "tips": ["껍질을 벗기고 키친타월로 기름을 닦아요"],
                                              "buy_with": ["쌈배추", "김", "초고추장"]})
    res = svc.handle(None, message=GWAMEGI)
    assert "어떤 거 요리" not in md(res) and "요리를 만들까요" not in md(res)
    chips = next(b for b in res["blocks"] if b["type"] == "chips")["data"]["items"]
    assert chips == ["쌈배추 추천해줘", "김 추천해줘", "초고추장 추천해줘"]
    assert any(b["type"] == "search_links" for b in res["blocks"])   # 상품이 없어도 네이버 찾아보기


def test_without_a_model_it_says_so_and_still_shows_products(sqlite_db):
    persimmon = [{"product_name": "대봉감 5kg", "price": 29900, "product_url": "https://www.coupang.com/p", "platform_name": "coupang"}]
    res = _svc(sqlite_db, persimmon).handle(None, message=HONGSI)
    assert "일반 정보는 지금 답하지 못했어요" in md(res)
    assert any(b["type"] == "product_list" for b in res["blocks"])


def test_a_model_food_name_not_in_the_sentence_is_ignored(sqlite_db):
    shop = FakeShopping(items=[])
    svc = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str),
                      food_tips=lambda t: {"food": "한우", "tips": ["보통 냉장 보관해요"]})
    svc.handle(None, message="귤 냉장 보관해도 돼?")
    assert shop.calls[0][0] != "한우"


def test_recipe_requests_still_go_to_recipes(sqlite_db):
    res = _svc(sqlite_db, []).handle(None, message="크림파스타 만드는 법")
    assert any(b["type"] in ("recipe_card", "clarify_form") for b in res["blocks"])


def test_predicates_are_never_the_dish_name():
    from app.services.recipe_chat.service import _NOT_DISH_WORD

    assert all(_NOT_DISH_WORD.search(w) for w in ("보관해", "거", "두고", "알려줘", "없이", "며칠"))
    assert not any(_NOT_DISH_WORD.search(w) for w in ("홍시", "김치찌개", "과메기", "된장국", "파스타", "갈비구이", "라면"))
