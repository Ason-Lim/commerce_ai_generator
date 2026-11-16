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


YUJA = {"title": "유자청", "summary": "유자와 설탕을 같은 무게로 버무려 숙성하는 청이에요.", "servings": "약 2kg 분량",
        "ingredients": [{"name": "유자", "amount": "1kg"}, {"name": "설탕", "amount": "1kg"}, {"name": "소금", "amount": "1큰술"}],
        "tools": ["유리병", "칼", "도마", "볼"],
        "steps": ["유자는 소금으로 껍질을 문질러 씻고 물기를 닦아 주세요.", "도마 위에서 칼로 유자를 반으로 갈라 씨를 빼고 얇게 채 썰어 주세요.",
                  "볼에 유자와 설탕을 넣고 고루 버무려 주세요.", "열탕 소독한 유리병에 담아 실온에 하루 둔 뒤 냉장 보관해 주세요."],
        "tips": ["씨를 뺀 뒤 무게를 재서 설탕을 맞춰 주세요."]}


def test_an_amount_question_gets_a_short_answer_above_the_recipe(make_ai):
    """2026-11-13 유자청: '몇 kg·얼마나'를 물으면 레시피 카드 위에 비율과 1·2·3배 분량 표 (우리 레시피 분량에서 계산)."""
    from app.services.recipe_chat.service import RecipeChat as R

    assert R._dish_from("유자청 만드는 법 설탕은 얼마나 넣어?") == "유자청"
    assert R._dish_from("유자청 담그려면 유자 몇 kg 사야 해?") == "유자청"
    svc, _calls = make_ai(YUJA, known=True, core=["유자", "설탕"])
    turn = svc.recipe.handle("유자청 만들려면 몇 kg 필요해?", None, {}, "x", None)
    types = [b["type"] for b in turn.blocks]
    first_text = next(b for b in turn.blocks if b["type"] == "text")["data"]["md"]
    assert types.index("text") < types.index("recipe_card")                     # 답이 카드보다 위
    assert "**유자 1kg에 설탕 1kg** 비율이에요 (설탕은 같은 무게)" in first_text
    assert "- 유자 **2kg** + 설탕 **2kg**" in first_text and "- 유자 **3kg** + 설탕 **3kg**" in first_text
    assert "|" not in first_text and "소금" not in first_text                    # 채팅 글에는 표가 그려지지 않는다
    plain = svc.recipe.handle("유자청 만드는 법", None, {}, "y", None)            # 분량을 묻지 않으면 표 없음
    assert not any("비율이에요" in (b["data"].get("md") or "") for b in plain.blocks if b["type"] == "text")


def test_public_reference_is_only_the_same_dish(make_ai):
    """2026-11-13 화면: 유자청 아래 '도라지 유자청생채·유자등갈비구이·유자삼치구이'가 참고로 붙었다 — 다른 요리다."""
    from types import SimpleNamespace

    svc, _calls = make_ai(known=True)
    recs = {t: SimpleNamespace(recipe_id=t, title=t, provider="식품안전나라", meta=[], ingredients=[], source_level="public")
            for t in ("도라지 유자청생채", "유자등갈비구이", "참치김치찌개", "김치찌개")}
    svc.recipe.resolver.get = lambda rid: recs.get(rid)
    choose = SimpleNamespace(kind="choose", recipe=None, alternatives=[("도라지 유자청생채", ""), ("유자등갈비구이", "")])
    assert svc.recipe._public_reference("유자청", choose) == (None, [])
    kimchi = SimpleNamespace(kind="choose", recipe=None, alternatives=[("참치김치찌개", ""), ("김치찌개", "")])
    _pub, blocks = svc.recipe._public_reference("김치찌개", kimchi)
    assert "「참치김치찌개」" in blocks[0]["data"]["md"] and "「김치찌개」" in blocks[0]["data"]["md"]


def test_a_recipe_named_after_a_person_shows_the_originals_not_a_copy(make_ai):
    """2026-11-16 실제 화면: '최강록 라면 레시피' → 기본 라면 레시피(같은 사진)가 나왔다.
    사람·가게 이름이 붙은 레시피는 그대로 옮기지 않고 원문(유튜브·블로그)을 보여 주고, 우리 기본 요리 레시피는 칩으로."""
    assert I.read(lambda _t: {"dish": "최강록 라면", "wants_recipe": True, "named_after": "최강록", "base_dish": "라면"},
                  "최강록 라면 레시피를 알려주세요.")["named_after"] == "최강록"
    assert I.read(lambda _t: {"dish": "라면", "wants_recipe": True, "named_after": "백종원"},
                  "라면 레시피 알려줘")["named_after"] is None                     # 문장에 없는 이름은 붙이지 않는다
    svc, calls = make_ai(known=True)
    svc.recipe.intent_reader = lambda _t: {"dish": "최강록 라면", "wants_recipe": True, "wants_products": False,
                                          "named_after": "최강록", "base_dish": "라면"}
    turn = svc.recipe.handle("최강록 라면 레시피를 알려주세요.", None, {}, "x", None)
    text = "\n".join(b["data"].get("md", "") for b in turn.blocks if b["type"] == "text")
    assert turn.stage == "recipe_other" and "**최강록 라면**은 최강록 님의 레시피라 그대로 옮기지 않아요" in text, text  # '라면는' 아님
    assert not any(b["type"] == "recipe_card" for b in turn.blocks)
    assert "라면 추천 레시피 보기" in [c for b in turn.blocks if b["type"] == "chips" for c in b["data"]["items"]]
    assert [c for c in calls if not isinstance(c, tuple)] == []                     # 레시피를 만들지 않았다


def test_a_trend_question_shows_recent_posts_first(make_ai):
    """'최신 유행 ○○ 레시피' → 요즘 화제가 된 글·영상(최근 것부터), 우리 추천 레시피는 칩으로."""
    svc, _calls = make_ai(known=True)
    turn = svc.recipe.handle("최신 유행 두쫀쿠 레시피를 알려주세요.", None, {}, "x", None)
    text = "\n".join(b["data"].get("md", "") for b in turn.blocks if b["type"] == "text")
    assert turn.stage == "recipe_other" and "요즘 화제가 된 **두쫀쿠** 레시피" in text, text
    assert "두쫀쿠 추천 레시피 보기" in [c for b in turn.blocks if b["type"] == "chips" for c in b["data"]["items"]]
    nxt = svc.recipe.handle("두쫀쿠 추천 레시피 보기", None, turn.state, "x", None)
    assert any(b["type"] == "recipe_card" for b in nxt.blocks)


def test_the_ramyeon_photo_hint_is_only_for_plain_ramyeon():
    """로제·볶음·짜장 라면은 국물이 다르다 — 빨간 국물 안내는 기본 라면에만 (종류가 바뀌면 사진도 그 요리대로)."""
    from app.services.recipe_chat import cook_knowledge as K

    assert "red-orange spicy broth" in K.image_hint("라면")
    for d in ("로제 라면", "볶음라면", "짜장라면", "최강록 라면"):
        assert "red-orange spicy broth" not in K.image_hint(d), d



def test_a_named_recipe_shows_only_posts_with_that_name(make_ai):
    """2026-11-16 실제 화면: '최강록 라면' 원문 목록에 '김호윤 셰프님 계란코팅진라면'이 섞였다 — 다른 사람의 레시피."""
    from tests.services.chat.test_recipe_discover import blog

    svc, _calls = make_ai(known=True, blog_titles=[
        blog("최강록 셰프 라면 레시피 따라해본 안성탕면 계란라면", "https://blog.naver.com/a/1", "식객", "20261115"),
        blog("김호윤 셰프님 계란코팅진라면 레시피 / 진라면 맛있게 끓이는법", "https://blog.naver.com/b/2", "슝슝", "20260918")])
    state = {"discover": {"dish": "최강록 라면", "results": [
        {"title": "최강록 셰프 라면 레시피 따라해본 안성탕면 계란라면", "link": "https://blog.naver.com/a/1", "kind": "blog"},
        {"title": "김호윤 셰프님 계란코팅진라면 레시피 / 진라면 맛있게 끓이는법", "link": "https://blog.naver.com/b/2", "kind": "blog"}]}}
    turn = svc.recipe._other_recipes("최강록 라면", state, base="라면", require="최강록", lead="원문을 보여 드릴게요.")
    form = next(b for b in turn.blocks if b["type"] == "clarify_form")["data"]
    hrefs = [o["href"] for o in form["questions"][0]["options"]]
    assert hrefs == ["https://blog.naver.com/a/1"]


def test_tapping_a_weight_row_rescales_the_whole_recipe(make_ai):
    """2026-11-16 분량 줄 누르기: '유자 2kg 기준으로 바꿔 줘' → 모든 재료를 2배로 (숟가락 단위도 수치는 곱함 · '약간'은 그대로).
    카드와 남은 양 기록은 원래 분량 그대로. 레시피에 무게로 없는 재료면 이 처리를 하지 않는다."""
    svc, _calls = make_ai(YUJA, known=True, core=["유자", "설탕"])
    turn = svc.recipe.handle("유자청 만들려면 몇 kg 필요해?", None, {}, "x", None)
    chips = [c for b in turn.blocks if b["type"] == "chips" for c in b["data"]["items"]]
    assert "유자 2kg 기준으로 바꿔 줘" in chips and "유자 3kg 기준으로 바꿔 줘" in chips
    nxt = svc.recipe.handle("유자 2kg 기준으로 바꿔 줘", None, turn.state, "x", None)
    md = next(b for b in nxt.blocks if b["type"] == "text")["data"]["md"]
    assert nxt.stage == "recipe_weight_scale" and "**유자 2kg** 기준 재료예요. 레시피 분량에 **2배**" in md, md
    assert "- 유자 **2kg** (레시피 1kg)" in md and "- 설탕 **2kg** (레시피 1kg)" in md
    half = svc.recipe.handle("유자 1.5kg으로 맞춰 줘", None, turn.state, "x", None)
    assert "**1.5배**" in next(b for b in half.blocks if b["type"] == "text")["data"]["md"]
    back = svc.recipe.handle("유자 1kg 기준으로 바꿔 줘", None, turn.state, "x", None)
    assert "레시피 분량 그대로예요" in back.blocks[0]["data"]["md"]
    other = svc.recipe.handle("사과 2kg 기준으로 바꿔 줘", None, turn.state, "x", None)   # 레시피에 없는 재료
    assert other is None or other.stage != "recipe_weight_scale"
