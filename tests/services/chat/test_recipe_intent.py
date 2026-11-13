"""2026-11-12 — 손님 문장의 뜻을 LLM 이 먼저 읽는다. 규칙만으로는 '끓이는 방법', '보여주세요', '맛있게 라면'에서 연달아 샜다.
꾸밈말이 상품 이름·조건인 경우('맛있는라면', '매운 라면')는 상품 검색어에 남긴다 (사용자)."""
from __future__ import annotations

import json

from app.services.recipe_chat import intent as I
from tests.services.chat.test_recipe_discover import chips, md  # noqa: F401  (fixtures below)
from tests.services.chat.test_recipe_discover import make_ai  # noqa: F401

# 실제로 샜던 문장들 — 바꿀 때마다 다시 본다
REAL_SENTENCES = {
    "김치찌개 끓이는 방법과 상품을 추천해 주세요.": {"dish": "김치찌개", "wants_recipe": True, "wants_products": True,
                                         "product_query": None, "servings": None},
    "맛있게 라면 끓이는 방법": {"dish": "라면", "wants_recipe": True, "wants_products": False, "product_query": None,
                         "servings": None},
    "라면 맛있게 끓이는 법이랑 매운 라면 상품도 보여줘": {"dish": "라면", "wants_recipe": True, "wants_products": True,
                                           "product_query": "매운 라면", "servings": None},
    "맛있는라면 끓이는 방법 알려줘": {"dish": "라면", "wants_recipe": True, "wants_products": False,
                            "product_query": None, "servings": None},
    "된장찌개 어떻게 하는지 알려줘": {"dish": "된장찌개", "wants_recipe": True, "wants_products": False,
                             "product_query": None, "servings": None},
}


def reader(calls):
    def ask(text):
        sentence = json.loads(text)["문장"]
        calls.append(sentence)
        return REAL_SENTENCES.get(sentence, {"dish": None, "wants_recipe": False, "wants_products": True,
                                             "product_query": sentence, "servings": None})
    return ask


def test_answers_are_validated():
    assert I.read(lambda _t: {"dish": "라면 상품", "wants_recipe": True}, "x")["dish"] is None   # 요청 말이 섞인 이름은 버린다
    assert I.read(lambda _t: {"dish": "김치찌개", "wants_recipe": True, "servings": 99}, "x")["servings"] is None
    assert I.read(lambda _t: (_ for _ in ()).throw(TimeoutError()), "x") is None             # 응답 없음 → 규칙
    assert I.read(None, "x") is None
    assert not I.CUE_RE.search("매운 라면 추천해 줘")                                           # 단서 없는 상품 문장은 묻지 않는다


def test_a_phrasing_the_rules_miss_is_read_by_the_llm(make_ai):
    svc, _calls = make_ai(known=True)
    seen = []
    svc.recipe.intent_reader = reader(seen)
    res = svc.handle(None, message="된장찌개 어떻게 하는지 알려줘")                     # 규칙에는 없는 말투
    assert seen == ["된장찌개 어떻게 하는지 알려줘"] and any(b["type"] == "recipe_card" for b in res["blocks"])


def test_product_modifiers_stay_in_the_product_query(make_ai):
    svc, _calls = make_ai(known=True)
    svc.recipe.intent_reader = reader([])
    turn = svc.recipe.handle("라면 맛있게 끓이는 법이랑 매운 라면 상품도 보여줘", None, {}, "x", None)
    assert any(b["type"] == "recipe_card" for b in turn.blocks)
    assert turn.shopping[0] == "매운 라면"                                          # 맛 조건은 상품 검색어에 그대로
    assert "찾으신 **매운 라면** 상품" in "\n".join(b["data"].get("md", "") for b in turn.blocks if b["type"] == "text")


def test_a_product_sentence_without_cooking_cues_does_not_call_the_llm(make_ai):
    svc, _calls = make_ai(known=True)
    seen = []
    svc.recipe.intent_reader = reader(seen)
    svc.recipe.handle("매운 라면 추천해 줘", None, {}, "x", None)
    assert seen == []


def test_without_the_llm_the_rules_still_work(make_ai):
    svc, _calls = make_ai(known=True)
    svc.recipe.intent_reader = lambda _t: (_ for _ in ()).throw(TimeoutError())
    turn = svc.recipe.handle("맛있게 라면 끓이는 방법", None, {}, "x", None)
    assert turn is not None and turn.stage != "recipe_ai_question"


def test_the_dish_itself_is_not_the_product_query():
    """'김치찌개 끓이는 방법과 상품' → 검색어 '김치찌개'면 완제품(밀키트)만 나왔다 — 레시피 재료로 찾게 비운다."""
    got = I.read(lambda _t: {"dish": "김치찌개", "wants_recipe": True, "wants_products": True,
                             "product_query": "김치찌개"}, "x")
    assert got["product_query"] is None and got["wants_products"]


def test_shop_terms_fit_the_dish_and_are_checked():
    ask = lambda _t: {"검색어": {"돼지고기": "찌개용 돼지고기 앞다리살", "두부": "찌개용 두부",  # noqa: E731
                                "김치": "비비고 포기김치 상품 추천"}}
    terms = I.shop_terms(ask, "김치찌개", ["돼지고기", "두부", "김치"])
    assert terms == {"돼지고기": "찌개용 돼지고기 앞다리살", "두부": "찌개용 두부"}        # 요청 말이 섞인 검색어는 버린다
    assert I.shop_terms(lambda _t: {"검색어": {"두부": "콩물"}}, "김치찌개", ["두부"]) == {}   # 재료 낱말이 없으면 버린다
    assert I.shop_terms(None, "김치찌개", ["두부"]) == {}


def test_ingredient_products_use_dish_fitting_terms_and_keep_the_customers_query_apart(make_ai):
    """실제 화면: '김치찌개' 완제품 목록 위에 '돼지고기 — 필요량 200g' 머리말이 붙었다(제목에 돼지고기가 있어 짝이 틀림)."""
    from app.services.recipe_chat import pack_fit

    svc, _calls = make_ai(known=True)
    svc.recipe.intent_reader = lambda _t: {"dish": "두쫀쿠", "wants_recipe": True, "wants_products": True,
                                          "product_query": "피스타치오 쿠키", "servings": None}
    svc.recipe.shop_terms = lambda _t: {"검색어": {"카다이프": "카다이프 면"}}
    turn = svc.recipe.handle("두쫀쿠 만드는 법이랑 피스타치오 쿠키 상품도", None, {}, "x", None)
    assert turn.shopping[0] == "피스타치오 쿠키" and "카다이프 면" in turn.shopping
    assert turn.shopping_needs["피스타치오 쿠키"]["skip"]                               # 손님 검색어에는 필요량 머리말 없음
    blocks = [{"type": "product_list", "data": {"items": [{"title": "피스타치오 쿠키 카다이프 맛", "reason": "", "why": []}]}}
              for _ in turn.shopping]
    out = pack_fit.apply(blocks, turn.shopping_needs)
    first = next(b for b in out if b["type"] == "product_list")
    assert out[0] is blocks[0] and first["data"]["items"][0]["title"].startswith("피스타치오 쿠키")


def test_instant_ramyeon_names_its_soup():
    """'라면 끓이는 방법' 재료에 '스프'만 있었다 — 봉지라면(면·스프 포함)으로 쓰고, 사리면이면 무슨 스프인지 밝힌다."""
    from app.services.recipe_chat import cook_knowledge as K

    assert any("봉지라면 1봉지" in g for g in K.guidance("라면"))
    assert not any("봉지라면" in g for g in K.guidance("돈코츠라멘"))
    bad = {"ingredients": [{"name": "라면 사리", "amount": "1개"}, {"name": "스프", "amount": "1개"}], "steps": ["끓여 주세요."]}
    good = {"ingredients": [{"name": "봉지라면", "amount": "1봉지"}, {"name": "달걀", "amount": "1개"}], "steps": ["끓여 주세요."]}
    assert any("스프" in p for p in K.problems(bad, "라면"))
    assert not any("스프" in p for p in K.problems(good, "라면"))
