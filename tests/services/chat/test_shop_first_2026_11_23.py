"""장보기 질문 다듬기 (2026-11-23 — 사용자·지인 의견): 백숙은 닭/오리를 먼저 묻기 · 장보기 질문이면 재료 먼저(만드는 순서 접힘) ·
'○○으로'라고 짚은 재료 상품을 맨 먼저."""
from __future__ import annotations

import json

from app.services.recipe_chat import shop_first as SF
from tests.services.chat.test_recipe_discover import make_ai  # noqa: F401  (fixture)

Q = "가을 능이버섯으로 백숙 하려면 재료 뭐 사야 해?"
SENT = {
    Q: {"dish": "백숙", "wants_recipe": True, "wants_products": True, "product_query": None, "servings": None},
    "가을 능이버섯으로 닭백숙 하려면 재료 뭐 사야 해?": {"dish": "닭백숙", "wants_recipe": True, "wants_products": True,
                                                "product_query": None, "servings": None},
    "닭백숙 만드는 법 알려줘": {"dish": "닭백숙", "wants_recipe": True, "wants_products": False, "product_query": None, "servings": None},
}


def _reader(text):
    return SENT.get(json.loads(text)["문장"], {"dish": None, "wants_recipe": False, "wants_products": True})


def test_helpers():
    assert SF.ambiguous("백숙", Q) == ("백숙", ("닭백숙", "오리백숙"))
    assert SF.ambiguous("능이백숙", "능이백숙 재료") is not None
    assert SF.ambiguous("닭백숙", "닭백숙 재료") is None and SF.ambiguous("백숙", "오리로 백숙 할래") is None
    assert SF.ambiguous("김치찌개", "김치찌개 재료") is None
    assert SF.option_texts(Q, "백숙", ("닭백숙", "오리백숙"))[0] == "가을 능이버섯으로 닭백숙 하려면 재료 뭐 사야 해?"
    assert SF.is_shopping_question(Q) and not SF.is_shopping_question("닭백숙 만드는 법 알려줘")
    assert SF.named_ingredient(Q) == "능이버섯"
    assert SF.named_ingredient("에어프라이어로 감자 요리") is None and SF.named_ingredient("선물로 뭐 사지") is None
    assert SF.ro("백숙") == "으로" and SF.ro("갈비찜") == "으로" and SF.ro("오리") == "로" and SF.ro("물") == "로"


def test_baeksuk_asks_chicken_or_duck_first(make_ai):
    svc, calls = make_ai(known=True)
    svc.recipe.intent_reader = _reader
    turn = svc.recipe.handle(Q, None, {}, "x", None, force_recipe=True)   # 운영: food_nlu 가 recipe 로 읽을 때
    assert turn.stage == "recipe_which_dish" and not any(b["type"] == "recipe_card" for b in turn.blocks)
    chips = next(b for b in turn.blocks if b["type"] == "chips")["data"]["items"]
    assert chips == ["가을 능이버섯으로 닭백숙 하려면 재료 뭐 사야 해?", "가을 능이버섯으로 오리백숙 하려면 재료 뭐 사야 해?"]
    assert "어떤 **백숙**으로" in json.dumps(turn.blocks, ensure_ascii=False)
    assert not any(isinstance(c, str) for c in calls)                     # 레시피를 만들지 않았다(AI 생성 호출 없음)


def test_shopping_question_puts_ingredients_first_and_named_ingredient_products_first(make_ai):
    svc, _calls = make_ai(known=True)
    svc.recipe.intent_reader = _reader
    turn = svc.recipe.handle("가을 능이버섯으로 닭백숙 하려면 재료 뭐 사야 해?", None, {}, "x", None, force_recipe=True)   # 운영: food_nlu 가 recipe 로 읽을 때
    card = next(b for b in turn.blocks if b["type"] == "recipe_card")["data"]
    assert card["layout"] == "shopping"
    assert turn.shopping and turn.shopping[0] == "능이버섯"
    assert "찾으신 **능이버섯** 상품" in json.dumps(turn.blocks, ensure_ascii=False)


def test_recipe_question_keeps_steps_first(make_ai):
    svc, _calls = make_ai(known=True)
    svc.recipe.intent_reader = _reader
    turn = svc.recipe.handle("닭백숙 만드는 법 알려줘", None, {}, "x", None, force_recipe=True)   # 운영: food_nlu 가 recipe 로 읽을 때
    card = next(b for b in turn.blocks if b["type"] == "recipe_card")["data"]
    assert card.get("layout") != "shopping"


def test_dish_with_named_ingredient():
    assert SF.dish_with("닭백숙", "능이버섯") == "능이버섯 닭백숙"
    assert SF.dish_with("능이백숙", "능이버섯") == "능이백숙" and SF.dish_with("능이버섯 닭백숙", "능이버섯") == "능이버섯 닭백숙"
    assert SF.dish_with("볶음밥", "밥") == "볶음밥" and SF.dish_with("닭백숙", None) == "닭백숙"
    assert SF.named_ingredient("냉장고 재료로 김치찌개 하려면 뭐 사야 해?") is None
    assert SF.named_ingredient("프라이팬으로 스테이크 하려면 뭐 사야 해?") is None


def test_named_ingredient_goes_into_the_recipe(make_ai):
    """2026-11-23 사용자 확인: '능이버섯으로 닭백숙' 레시피에 능이가 없었다 → 레시피를 '능이버섯 닭백숙'으로 만든다."""
    svc, calls = make_ai(known=True)
    svc.recipe.intent_reader = _reader
    turn = svc.recipe.handle("가을 능이버섯으로 닭백숙 하려면 재료 뭐 사야 해?", None, {}, "x", None, force_recipe=True)
    asked = [c for c in calls if isinstance(c, str)]
    assert asked and "능이버섯 닭백숙" in asked[0]
    assert turn.state["pending"] == {"type": "other_recipes", "dish": "능이버섯 닭백숙"}
    assert turn.shopping and turn.shopping[0] == "능이버섯"
