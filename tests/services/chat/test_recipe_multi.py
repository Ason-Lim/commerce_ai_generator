"""여러 레시피 연결 (2026-10-30): 크림파스타 외에 단위·조리법이 다른 공공 레시피 3개가
검색 → 선택 → 인분 변경 → 재료 기록(정정) → 조리 질문을 같은 흐름으로 처리하는지.

* 계란찜 epis-337 — 찜 · 원문 2인분 · 개·g·큰술·작은술·컵
* 냉이된장찌개 epis-96 — 끓이기 · 원문 4인분 · g·컵·큰술·cm·뿌리·쪽 (모시조개를 두 번 넣음)
* 불고기찹쌀구이 epis-330 — 재우기·지지기 · 원문 2인분 · g·컵·큰술 ('고기' = 쇠고기)
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.services.chat.service import ChatService
from app.services.recipe_chat.catalog_store import StaticCatalog, load_json
from app.services.recipe_chat.service import RecipeChat

FIXTURE = Path(__file__).with_name("fixtures") / "recipe_catalog_multi.json"


@pytest.fixture
def svc(sqlite_db, shopping):
    chat = RecipeChat(statement_factory=str, catalog_provider=StaticCatalog(load_json(FIXTURE)))
    return ChatService(sqlite_db, shopping=shopping, recipe_chat=chat)


def md(res):
    return "\n".join(b["data"].get("md", "") for b in res["blocks"] if b["type"] in ("text", "notice"))


def card_of(res):
    return next(b for b in res["blocks"] if b["type"] == "recipe_card")["data"]


def options(res):
    form = next(b for b in res["blocks"] if b["type"] == "clarify_form")["data"]
    q = (form.get("questions") or [form])[0]
    return [o["value"] for o in q["options"]]


def start(svc, query, pick):
    res = svc.handle(None, message=query)
    assert res["stage"] == "recipe_clarify" and pick in options(res)          # 검색 → 선택지
    sid = res["session_id"]
    res = svc.handle(sid, answers={"recipe": pick})                            # 선택
    assert res["stage"] == "recipe_guide" and card_of(res)["recipe_id"] == pick
    return sid, (lambda m: svc.handle(sid, message=m))


def test_steamed_egg_flow(svc, shopping):
    sid, say = start(svc, "계란 요리 레시피", "epis-337")
    text = md(say("1인분으로 바꿔 줘"))
    for line in ("계란 **1개** (원문 2개)", "시금치 **5g** (원문 10g)", "당근 **1/8개** (원문 1/4개)",
                 "설탕 **1/8작은술** (원문 1/4작은술)", "물 **1/4컵** (원문 1/2컵)", "소금 약간 (원문 그대로)"):
        assert line in text, line
    assert md(say("계란 1개 있어요")) == "**계란 1개**로 기록했어요. 1인분 필요량 1개와 같아요(참고 계산)."
    assert md(say("아니, 2개예요")) == "**계란** 보유량을 1개에서 **2개**로 바꿨어요. 1인분 필요량 1개보다 1개 많아요(참고 계산)."
    assert md(say("얼마나 쪄요?")) == "원문 5단계: 깊은 냄비에 ④를 넣고 끓는 물에서 중탕하여 중불로 **15분 정도** 쪄낸다."
    assert md(say("당근은 언제 넣어요?")) == "원문 4단계 “큰 볼에 계란, 당근, 옥수수, 다진 파를 넣고”."
    card = card_of(say("계란찜 만드는 법"))
    rows = {i["name"]: i for i in card["ingredients"]}
    assert card["servings"] == "1인분" and rows["계란"]["stock"] == "2개" and rows["계란"]["status"] is None
    assert shopping.calls == []


def test_doenjang_stew_flow(svc):
    sid, say = start(svc, "된장으로 끓이는 찌개 레시피", "epis-96")
    text = md(say("2인분으로 바꿔 줘"))
    for line in ("냉이 **50g** (원문 100g)", "모시조개 **1/2컵** (원문 1컵)", "된장 **1과1/2큰술** (원문 3큰술)",
                 "다시마 **5cm** (원문 10cm)", "대파 **1/2뿌리** (원문 1뿌리)", "마늘 **1과1/2쪽** (원문 3쪽)",
                 "물 **5컵** (원문 10컵)"):
        assert line in text, line
    assert md(say("냉이 30g 있어요")) == "**냉이 30g**로 기록했어요. 2인분 필요량 50g보다 20g 적어요(참고 계산)."
    assert md(say("아니, 60g이에요")).startswith("**냉이** 보유량을 30g에서 **60g**로 바꿨어요.")
    # added twice in the source → both steps, in the source's own words
    assert md(say("모시조개는 언제 넣어요?")) == (
        "원문에서 모시조개는 2번 넣어요: 3단계 “냄비에 물 10컵과 모시조개를 넣고”, "
        "4단계 “간을 맞춘 뒤 마지막으로 모시조개를 넣는다”.")
    # no time in the source → said so, no invented minutes
    assert md(say("얼마나 끓여요?")) == (
        "원문에 정확한 시간은 없어요. 원문 3단계: “냄비에 물 10컵과 모시조개를 넣고 끓이다가 모시조개의 입이 벌어지면 "
        "건져내고 국물을 거즈에 걸러 냄비에 담고 된장에 무친 냉이를 넣고 푹 끓인다.”")   # not step 1's '끓는 물


def test_bulgogi_pan_fry_flow(svc):
    sid, say = start(svc, "양념 고기 구이 레시피", "epis-330")
    text = md(say("1인분으로 바꿔 줘"))
    for line in ("쇠고기 **100g** (원문 200g)", "찹쌀가루 **1/4컵** (원문 1/2컵)", "기름 **1/8컵** (원문 1/4컵)"):
        assert line in text, line
    # '고기' is the only ingredient ending in 고기 → 쇠고기; the evidence keeps the customer's words
    assert md(say("고기 80g 있어요")) == "**쇠고기 80g**로 기록했어요. 1인분 필요량 100g보다 20g 적어요(참고 계산)."
    assert md(say("아니, 120g이에요")).startswith("**쇠고기** 보유량을 80g에서 **120g**로 바꿨어요.")
    assert md(say("고기는 얼마나 재워요?")) == (
        "원문 1단계: 쇠고기를 얇게 저민 불고기 감으로 준비하여 다진 파, 마늘, 깨소금, 후춧가루, 설탕, 참기름, 간장을 넣고 "
        "양념하여 **1시간 정도** 재운다.")
    card = card_of(say("불고기찹쌀구이 만드는 법"))
    assert {i["name"]: i["stock"] for i in card["ingredients"]}["쇠고기"] == "120g"


def test_switching_recipes_resets_servings_and_keeps_each_recipes_stock(svc):
    sid, say = start(svc, "계란 요리 레시피", "epis-337")
    say("1인분으로 바꿔 줘")
    say("계란 2개 있어요")
    card = card_of(say("된장찌개 만드는 법"))          # another recipe
    assert card["recipe_id"] == "epis-445" and card["servings"] == "2인분"   # servings back to the source
    card = card_of(say("계란찜 만드는 법"))
    assert card["servings"] == "2인분"                  # the choice belonged to the previous view
    assert {i["name"]: i["stock"] for i in card["ingredients"]}["계란"] == "2개"   # stock stays with its recipe


@pytest.mark.parametrize("question,expected", [
    ("두부는 언제 넣어요?", "**애호박을 넣고 끓으면** 두부를 넣어요. (원문 5단계)"),
    ("다진마늘은 언제 넣어요?", "**두부를 넣어 더 끓인후** 청고추, 홍고추, 대파, 다진 마늘, 참기름을 넣어요. (원문 5단계)"),
])
def test_when_to_add_reads_the_clause_before_the_addition(svc, question, expected):
    sid = svc.handle(None, message="된장찌개 만드는 법")["session_id"]
    assert md(svc.handle(sid, message=question)) == expected


def test_choice_question_names_a_dish_not_an_ingredient(svc):
    res = svc.handle(None, message="계란 요리 레시피")
    assert md(res).startswith("어떤 계란 요리를 만들까요? 지금 원문 레시피가 확보된 계란 요리는 ")
    form = next(b for b in res["blocks"] if b["type"] == "clarify_form")["data"]
    assert form["submit"] == "이 레시피 보기"
    res = svc.handle(None, message="된장으로 끓이는 찌개 레시피")
    assert md(res).startswith("어떤 찌개를 만들까요?")


def test_cup_stock_is_recorded_corrected_and_shown_without_a_comparison(svc):
    sid, say = start(svc, "된장으로 끓이는 찌개 레시피", "epis-96")
    say("2인분으로 바꿔 줘")
    assert md(say("모시조개 1컵 있어요")) == (
        "**모시조개 1컵**으로 기록했어요. 2인분 필요량은 1/2컵이에요. 컵 크기 기준이 없어 정확한 비교는 보류했어요.")
    assert md(say("아니, 반 컵이에요")) == (
        "**모시조개** 보유량을 1컵에서 **반 컵**으로 바꿨어요. 2인분 필요량은 1/2컵이에요. 컵 크기 기준이 없어 정확한 비교는 보류했어요.")
    assert md(say("된장 2큰술 있어요")).startswith("**된장 2큰술**로 기록했어요. 2인분 필요량은 1과1/2큰술이에요. 숟가락 크기")
    card = card_of(say("냉이된장찌개 만드는 법"))
    rows = {i["name"]: i for i in card["ingredients"]}
    assert rows["모시조개"]["stock"] == "반 컵" and rows["모시조개"]["status"] is None
    assert rows["된장"]["stock"] == "2큰술"


def test_core_condition_keeps_fish_out_of_a_meat_search(svc):
    res = svc.handle(None, message="양념 고기 구이 레시피")
    assert md(res).startswith("어떤 고기 구이를 만들까요?")
    assert set(options(res)) == {"epis-330", "fs-490", "other"}         # 고등어·꽁치 are not meat
    text = md(res)
    assert "참고로 생선 구이는 따로 있어요: 고등어양념구이, 꽁치 양념구이" in text
    chips = [i for b in res["blocks"] if b["type"] == "chips" for i in b["data"]["items"]]
    assert chips == ["고등어양념구이 만드는 법", "꽁치 양념구이 만드는 법"]
    res = svc.handle(None, message="생선 구이 레시피")
    assert set(options(res)) == {"epis-428", "fs-878", "other"}


def test_words_the_rules_cannot_read_go_to_the_stock_interpreter_and_are_validated(sqlite_db, shopping):
    """Mock of the DeepSeek stock interpreter: '삼백 그램' is not parsed by the rules; the proposal is still
    checked by validate_proposal before anything is saved."""
    from app.services.recipe_session.direct_stock_chat import validate_proposal

    calls = []

    def fake(message, materials):
        calls.append(message)
        return validate_proposal({"operation": "set", "ingredient": "쇠고기", "amount": "300", "unit": "g"},
                                 materials, message)

    chat = RecipeChat(statement_factory=str, catalog_provider=StaticCatalog(load_json(FIXTURE)), stock_interpreter=fake)
    svc = ChatService(sqlite_db, shopping=shopping, recipe_chat=chat)
    sid, say = start(svc, "양념 고기 구이 레시피", "epis-330")
    assert md(say("쇠고기 삼백 그램 남았어요")) == "**쇠고기 300g**로 기록했어요. 2인분 필요량 200g보다 100g 많아요(참고 계산)."
    assert calls == ["쇠고기 삼백 그램 남았어요"]
    assert md(say("아니, 1컵이에요")).startswith("**쇠고기** 보유량을 300g에서 **1컵**으로 바꿨어요.")
    assert len(calls) == 1                       # the rules handled the correction


@pytest.mark.parametrize("query,expected", [
    ("갈비구이 만드는 법", ["갈비구이"]), ("계란말이 레시피", ["계란말이"]), ("떡볶이 만드는 법", ["떡볶이"]),
    ("고기가 들어간 구이", ["고기", "들어간", "구이"]),
])
def test_dish_names_ending_in_i_are_not_cut_as_particles(query, expected):
    from app.services.recipe_chat.catalog_store import terms
    assert terms(query) == expected


def test_a_dish_named_in_full_opens_its_card(svc):
    res = svc.handle(None, message="계란말이 만드는 법")
    assert res["stage"] == "recipe_guide" and card_of(res)["recipe_id"] == "epis-97"


def test_without_the_interpreter_a_stock_sentence_stays_in_the_recipe(svc, shopping):
    sid, say = start(svc, "된장으로 끓이는 찌개 레시피", "epis-96")
    res = say("냉이 오십 그램 있어요")
    assert res["stage"] == "recipe_stock_unclear" and shopping.calls == []
    assert md(res).startswith("**냉이** 남은 양을 숫자로 알려 주시면 기록할게요. 예: **냉이 ")
