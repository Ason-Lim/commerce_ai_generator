"""원문에 핵심 조리 단계가 빠진 레시피 (2026-10-30 사용자 결정) — 모의 시험 (DeepSeek 호출 없음).

* 갈비구이(EPIS 48)는 원문이 '양념장 섞기'에서 끝나 굽는 단계가 없다 → 카드에 "원문에 굽는 단계가 없어요."
* AI 보충 단계는 '일반 조리 제안 · 원문 아님 (AI)'으로 원문 단계 뒤에 따로 붙고, 검증을 통과해야만 보인다.
* 같은 조건이면 완결된 원문 레시피를 먼저 보여 준다.
* 카드 팁은 그 레시피에서 실제로 하는 동작일 때만 ('마늘 볶기'는 마늘을 볶는 단계가 있어야).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.services.chat.service import ChatService
from app.services.recipe_chat import advice, supplement as S
from app.services.recipe_chat.catalog_store import StaticCatalog, load_json
from app.services.recipe_chat.recipes import catalog_recipe
from app.services.recipe_chat.service import RecipeChat

FIXTURE = Path(__file__).with_name("fixtures") / "recipe_catalog_gap.json"
GOOD = {"needed": True, "steps": [
    {"title": "갈비 굽기", "text": "달군 팬에 재운 갈비를 올려 중약불에서 앞뒤로 3~4분씩 구워 주세요."},
    {"title": "양념 바르기", "text": "거의 익으면 6단계 양념장을 발라 타지 않게 한 번 더 구워 주세요."}]}


def galbi():
    return catalog_recipe(load_json(FIXTURE).get("epis-48"))


@pytest.mark.parametrize("title,steps,label", [
    ("갈비구이", ["양념장을 섞는다."], "굽기"),
    ("아귀찜", ["양념장을 만든다."], "찌기"),
    ("해물파전", ["반죽을 만든다."], "부치기"),
    ("떡갈비구이", ["석쇠에 올려 뒤집어 가며 굽는다."], None),
    ("다시마냉국", ["차게 담는다."], None),          # cold soup — nothing to boil
    ("크림소스파스타", ["담는다."], None),            # no core action for this dish name
])
def test_missing_core_action(title, steps, label):
    found = S.missing_action(title, steps)
    assert (found["label"] if found else None) == label


def test_validation_accepts_a_short_labelled_step_and_rejects_amounts_new_ingredients_and_off_topic():
    recipe, missing = galbi(), S.missing_action("갈비구이", galbi().step_texts())
    vocab = frozenset({"식용유", "갈비", "버터", "간장"})
    view, problems = S.validate(GOOD, recipe, missing, vocab)
    assert problems == [] and view["label"] == "일반 조리 제안 · 원문 아님 (AI)" and len(view["steps"]) == 2
    bad = {"needed": True, "steps": [{"title": "굽기", "text": "식용유 1큰술을 두르고 갈비를 구워 주세요."}]}
    view, problems = S.validate(bad, recipe, missing, vocab)
    assert view is None and any("분량" in p for p in problems) and any("식용유" in p for p in problems)
    view, problems = S.validate({"needed": True, "steps": [{"title": "담기", "text": "접시에 담아 주세요."}]},
                                recipe, missing, vocab)
    assert view is None and problems == ["빠진 동작(굽기) 없음"]
    view, problems = S.validate({"needed": False, "steps": []}, recipe, missing, vocab)
    assert view == {"needed": False, "action": "굽기", "steps": []}


@pytest.fixture
def svc_with(sqlite_db, shopping):
    def make(draft):
        calls = []

        def fake(text):
            calls.append(text)
            return draft
        supps = S.Supplements(fake, statement_factory=str, background=False)
        chat = RecipeChat(statement_factory=str, catalog_provider=StaticCatalog(load_json(FIXTURE)), supplements=supps)
        return ChatService(sqlite_db, shopping=shopping, recipe_chat=chat), calls
    return make


def card_of(res):
    return next(b for b in res["blocks"] if b["type"] == "recipe_card")["data"]


def open_galbi(svc):
    """'갈비구이' asks which kind first (LA갈비·돼지갈비 …); the plain 갈비구이 is EPIS 48."""
    res = svc.handle(None, message="갈비구이 만드는 법")
    return card_of(svc.handle(res["session_id"], answers={"recipe": "epis-48"}))


def test_card_says_the_source_misses_grilling_and_adds_the_labelled_ai_step(svc_with):
    svc, calls = svc_with(GOOD)
    card = open_galbi(svc)
    assert card["source_gap"] == "원문에 굽는 단계가 없어요."
    assert card["supplement"]["label"] == "일반 조리 제안 · 원문 아님 (AI)"
    assert [s["title"] for s in card["supplement"]["steps"]] == ["갈비 굽기", "양념 바르기"]
    assert len(card["steps"]) == 6                         # the source steps are untouched
    assert len(calls) == 1 and '"빠진 동작": "굽기"' in calls[0]
    polled = svc.recipe_easy("epis-48", card["easy_key"])     # polling never starts a job, but returns it
    assert polled["supplement"]["steps"][0]["title"] == "갈비 굽기" and len(calls) == 1


def test_a_rejected_draft_shows_only_the_gap_notice(svc_with):
    svc, _calls = svc_with({"needed": True, "steps": [{"title": "굽기", "text": "식용유 2큰술에 구워 주세요."}]})
    card = open_galbi(svc)
    assert card["source_gap"] == "원문에 굽는 단계가 없어요." and card["supplement"] is None
    assert card["supplement_status"] == "unavailable"


def test_a_complete_source_never_calls_the_model(svc_with):
    svc, calls = svc_with(GOOD)
    card = card_of(svc.handle(None, message="떡갈비구이 만드는 법"))
    assert card["source_gap"] is None and card["supplement"] is None and calls == []


def test_complete_sources_come_first_in_search_but_the_dish_named_exactly_wins():
    catalog = load_json(FIXTURE)
    found = [r["id"] for r in catalog.search("갈비 레시피", limit=10)]
    assert found.index("epis-128") < found.index("epis-48") and found[-1] == "epis-48"   # the incomplete one last
    assert [r["id"] for r in catalog.search("갈비구이 만드는 법")][0] == "epis-48"


@pytest.mark.parametrize("rid,expected", [
    ("epis-48", ["타지 않게 굽기", "재우는 시간"]),        # no '마늘 볶기': the garlic is boiled, never fried
])
def test_card_tips_follow_what_the_recipe_actually_does(rid, expected):
    r = load_json(FIXTURE).get(rid)
    tips = advice.card_tips([i["name"] for i in r["ingredients"]], [s["text"] for s in r["steps"]], r["name"])
    assert [t["title"] for t in tips] == expected


# ── '갈비구이' → which kind first (2026-10-30 사용자 결정) ─────────────────────────
def test_a_dish_made_from_different_meats_asks_which_one_first(svc_with):
    svc, calls = svc_with(GOOD)
    res = svc.handle(None, message="갈비구이 만드는 법")
    assert res["stage"] == "recipe_clarify"
    texts = [b["data"]["md"] for b in res["blocks"] if b["type"] == "text"]
    assert texts[0] == "갈비구이는 주재료(고기 종류·부위)에 따라 양념과 조리법이 달라요. 어떤 갈비구이를 만들까요?"
    form = next(b for b in res["blocks"] if b["type"] == "clarify_form")["data"]
    assert form["layout"] == "cards"
    opts = form["questions"][0]["options"]
    assert [o["value"] for o in opts] == ["epis-48", "fs-468", "epis-109", "fs-485", "other"]
    assert [o["label"] for o in opts][:3] == ["갈비구이", "LA갈비구이", "돼지갈비구이"]     # 'L..A' cleaned for display
    assert opts[2]["desc"] == "돼지갈비를 양념에 잘 재워 채소에 싸 드셔보세요" and opts[2]["meta"] == "4인분 · 50분"
    assert opts[1]["image"].startswith("http") and opts[1]["meta"] == "굽기"
    assert calls == []                                           # nothing generated before a choice
    card = card_of(svc.handle(res["session_id"], answers={"recipe": "epis-109"}))
    assert card["recipe_id"] == "epis-109" and card["source_gap"] is None


def test_a_specific_kind_opens_directly(svc_with):
    svc, _calls = svc_with(GOOD)
    assert card_of(svc.handle(None, message="돼지갈비구이 만드는 법"))["recipe_id"] == "epis-109"
    assert card_of(svc.handle(None, message="떡갈비구이 만드는 법"))["recipe_id"] == "epis-128"   # another dish


@pytest.mark.parametrize("dish,names,expected", [
    ("갈비구이", ["갈비구이", "돼지갈비구이", "떡갈비구이", "유자등갈비구이", "레몬등갈비구이"], ["돼지갈비구이", "유자등갈비구이"]),
    ("계란찜", ["계란찜", "토마토 채소 계란찜"], []),           # 채소 is not 소(beef)
    ("파전", ["파전", "양파전", "해물파전"], ["해물파전"]),        # 양파 is not 양(lamb)
])
def test_variants_are_meat_or_cut_words_only(dish, names, expected):
    from app.services.recipe_chat.catalog_store import RecipeCatalog, variants_of
    catalog = RecipeCatalog([{"id": f"r{n}", "name": x, "steps": [{"text": "굽는다"}]} for n, x in enumerate(names)])
    assert [r["name"] for r in variants_of(catalog, dish)] == expected
