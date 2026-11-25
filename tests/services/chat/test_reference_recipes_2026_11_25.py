"""공개 레시피 참고본 (2026-11-25) — 사용자가 준 공개 레시피 3권을 AI 제안 레시피의 참고 자료로 쓴다.

레시피코리아 업소용 무료 공개 77 · 이금기 한식 레시피북 50 · 고베한국교육원 「한국요리 20선」 20.
작성 AI(Claude·GPT·Ollama)에게 같은 참고본이 들어가고, AI 가 가정용 분량·자기 문장으로 다시 편집한다. 출처는 카드 설명에 밝힌다.
"""

from __future__ import annotations

import copy
import json
import re

import pytest

from app.services.recipe_chat import ai_recipe as AI
from app.services.recipe_chat import reference_recipes as R
from tests.services.chat.test_recipe_discover import AI_DRAFT, CORE, make_ai, md  # noqa: F401 — make_ai 는 fixture

JJIMDAK = {
    "title": "안동찜닭",
    "summary": "간장 양념에 닭과 채소, 당면을 졸인 찜닭이에요.",
    "servings": "2인분",
    "ingredients": [
        {"name": "닭", "amount": "600g"},
        {"name": "감자", "amount": "1개"},
        {"name": "당근", "amount": "1/2개"},
        {"name": "양파", "amount": "1개"},
        {"name": "당면", "amount": "50g"},
        {"name": "진간장", "amount": "4큰술"},
        {"name": "설탕", "amount": "2큰술"},
        {"name": "다진 마늘", "amount": "1큰술"},
        {"name": "물", "amount": "400mL"},
    ],
    "tools": ["냄비", "볼"],
    "steps": [
        "당면은 볼에 찬물을 부어 30분 불려 주세요.",
        "닭은 끓는 물에 2분 데쳐 헹궈 주세요.",
        "냄비에 닭, 물, 진간장, 설탕, 다진 마늘을 넣고 센불에서 10분 끓여 주세요.",
        "감자, 당근, 양파를 넣고 중불에서 15분 졸여 주세요. 닭 속살이 하얗게 익었는지 확인해 주세요.",
        "불린 당면을 넣고 3분 더 졸여 주세요.",
    ],
    "tips": ["당면은 마지막에 넣어야 불지 않아요."],
}


def test_the_file_holds_the_three_books_with_their_sources():
    d = R.data()
    recipes = d["recipes"]
    assert len(recipes) == 147
    counts = {s: sum(r["src"] == s for r in recipes) for s in d["sources"]}
    assert counts == {"recipekorea_free77": 77, "lkk_korean50": 50, "kobe_korean20": 20}
    assert all(d["sources"][s].get("short") and d["sources"][s].get("terms") for s in d["sources"])
    assert len({r["id"] for r in recipes}) == 147
    for r in recipes:
        assert r["title"] and r["groups"] and r["scale"] in ("가정용", "업소용")
        assert all(i["name"] for g in r["groups"] for i in g["items"])


def test_brand_names_phone_numbers_and_authors_are_not_in_the_reference_text():
    for r in R.data()["recipes"]:
        body = json.dumps({k: v for k, v in r.items() if k != "groups"}, ensure_ascii=False) + json.dumps(
            [[{k: v for k, v in i.items() if k != "brand"} for i in g["items"]] for g in r["groups"]],
            ensure_ascii=False,
        )
        assert "이금기" not in body, r["id"]  # 원래 이름은 brand 칸에만
        assert not re.search(r"\d{2,3}[-.]\d{3,4}[-.]\d{4}", body), r["id"]  # 원문 속 구입처 전화번호는 옮기지 않았다
        assert "쉐프케이" not in body and "대령숙수" not in body  # 작성자 별명은 남기지 않는다


def test_find_matches_the_dish_and_drops_far_matches():
    assert [r["id"] for r in R.find("안동찜닭")] == ["kobe-007", "lkk-050"]
    assert [r["id"] for r in R.find("김치")] == ["kobe-018"]  # '김치 삼겹살찜'은 붙이지 않는다
    assert [r["title"] for r in R.find("닭개장")] == ["닭개장"]
    assert R.find("감바스") == [] and R.find("닭") == []  # 없는 요리 · 한 글자
    assert all(r["src"] for r in R.find("떡볶이"))


def test_brief_tells_the_writer_to_scale_down_business_recipes():
    rk = next(r for r in R.data()["recipes"] if r["id"] == "rk-031")  # 홍합탕 (업소용 10kg)
    b = R.brief(rk)
    assert b["출처"].startswith("레시피코리아") and b["규모"] == "업소용" and "가정용" in b["주의"]
    assert b["재료"][0].startswith("손질홍합 10kg") and len(b["만드는 순서"]) >= 3
    home = R.brief(next(r for r in R.data()["recipes"] if r["id"] == "lkk-006"))
    assert "주의" not in home and any(x.startswith("[양념장] 굴소스") for x in home["재료"])


def build(draft=JJIMDAK, refs=None):
    seen = []

    def gen(text):
        seen.append(json.loads(text))
        return copy.deepcopy(draft)

    return AI.AiRecipes(gen, model="claude-sonnet-5-5", references=refs), seen


def test_the_writer_gets_the_references_and_the_record_cites_them():
    ai, seen = build()
    rec, problems = ai.create("안동찜닭", basis={"core": ["닭", "당면"], "method": "졸이기"})
    assert problems == []
    refs = seen[0]["참고 레시피 (공개 레시피 — 가정용으로 다시 편집해서 쓸 것)"]
    assert [r["요리"] for r in refs] == ["안동찜닭", "안동찜닭"]
    assert {r["출처"] for r in refs} == {
        "간단하게 만들 수 있는 한국요리 20선 (2019)",
        "이금기 소스를 이용한 한식 레시피북 (2020, 50품)",
    }
    assert rec["generated"]["references"] == [
        {"id": "kobe-007", "title": "안동찜닭", "source": "고베한국교육원 「한국요리 20선」"},
        {"id": "lkk-050", "title": "안동찜닭", "source": "이금기 한식 레시피북"},
    ]
    assert "참고 레시피" in AI.PROMPT and "문장은 그대로 옮기지 말고" in AI.PROMPT


def test_a_dish_without_references_records_an_empty_list():
    ai, seen = build(draft=AI_DRAFT)
    rec, _ = ai.create("두쫀쿠", basis={"core": CORE, "method": "굽지 않고 냉장 굳히기"})
    assert not any(k.startswith("참고 레시피") for k in seen[0])
    assert rec["generated"]["references"] == []


def test_reference_ingredients_confirm_the_core_ingredients():
    def identify(text):
        payload = json.loads(text)
        assert "당면" in payload["공개 레시피 재료"]
        return {"known": True, "what": "간장 찜닭", "core_ingredients": ["닭", "당면", "감자"], "method": "졸이기"}

    ai = AI.AiRecipes(lambda t: JJIMDAK, identifier=identify)
    out = ai.identify("안동찜닭")
    assert out["confirmed"] is True
    assert set(out["basis"]["core"]) >= {"당면", "감자"} and "공개 레시피 재료" in out["basis"]["core_from"]


def test_old_records_are_made_again_once_when_references_exist():
    ai, _seen = build()
    old = {"name": "안동찜닭", "generated": {"version": "ai-recipe-v3"}}
    assert ai.needs_refresh(old) is True
    assert ai.needs_refresh(dict(old, generated={"references": []})) is False
    assert ai.needs_refresh({"name": "두쫀쿠", "generated": {}}) is False
    assert ai.needs_refresh(None) is False


def test_a_broken_reference_source_never_blocks_the_recipe():
    def boom(_dish):
        raise OSError("file gone")

    ai, seen = build(refs=boom)
    rec, problems = ai.create("안동찜닭", basis={"core": ["닭"], "method": "졸이기"})
    assert problems == [] and rec["generated"]["references"] == []


@pytest.mark.parametrize(
    "env, provider_model",
    [
        ({"ANTHROPIC_API_KEY": "a"}, "claude-sonnet-5-5"),
        (
            {"OPENAI_API_KEY": "o", "RECIPE_AI_PROVIDER": "openai", "RECIPE_AI_MODEL": "gpt-6.1-sol"},
            "openai:gpt-6.1-sol",
        ),
        ({"RECIPE_AI_PROVIDER": "ollama", "OLLAMA_MODEL": "qwen2.5:7b"}, "ollama:qwen2.5:7b"),
    ],
)
def test_the_writer_can_be_claude_gpt_or_ollama(env, provider_model):
    ai = AI.from_env(env)
    assert ai.generator is not None and ai.model == provider_model


def test_the_card_note_names_the_references(make_ai, monkeypatch):  # noqa: F811
    ref = {
        "id": "lkk-900",
        "src": "lkk_korean50",
        "title": "두쫀쿠",
        "scale": "가정용",
        "groups": [{"name": "재료", "items": [{"name": "카다이프", "amount": "100g"}]}],
        "steps": ["볶는다."],
    }
    monkeypatch.setattr(R, "find", lambda dish, limit=2: [ref] if "두쫀쿠" in dish else [])
    svc, _calls = make_ai(known=True)
    res = svc.handle(None, message="두쫀쿠 만드는 법")
    assert (
        "참고한 공개 레시피: 「두쫀쿠」(이금기 한식 레시피북) — 그대로 옮기지 않고 AI가 가정용 분량·순서로 다시 정리했어요."
        in md(res)
    )
