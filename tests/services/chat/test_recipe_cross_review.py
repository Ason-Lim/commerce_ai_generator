"""2026-11-12 — AI 제안 레시피 교차 검토: Claude 가 쓰고 GPT 가 본다 (같은 회사 모델이 자기 글을 검토하지 않게)."""
from __future__ import annotations

import copy
import json

from app.services.recipe_chat import ai_recipe as AI
from tests.services.chat.test_recipe_discover import AI_DRAFT, CORE

BASIS = {"core": CORE, "method": "굽지 않고 냉장 굳히기"}


def build(reviews, drafts=None):
    seen, gens = [], []
    queue = list(drafts or [])

    def gen(text):
        gens.append(json.loads(text))
        return copy.deepcopy(queue.pop(0) if queue else AI_DRAFT)

    def review(text):
        seen.append(json.loads(text))
        r = reviews.pop(0)
        if isinstance(r, Exception):
            raise r
        return r
    return AI.AiRecipes(gen, model="claude-sonnet-5-5", reviewer=review, reviewer_model="openai:gpt-6.1-sol"), seen, gens


def test_clean_review_is_recorded():
    ai, seen, gens = build([{"ok": True, "problems": []}])
    rec, problems = ai.create("두쫀쿠", basis=BASIS)
    assert problems == [] and len(gens) == 1
    assert rec["generated"]["review"] == {"by": "openai:gpt-6.1-sol", "status": "ok", "notes": []}
    assert "교차 검토(openai:gpt-6.1-sol)" in rec["generated"]["checks"]
    assert seen[0]["요리"] == "두쫀쿠" and seen[0]["재료"][0] == "마시멜로 200g"


def test_notes_send_the_draft_back_once_then_remaining_notes_are_shown():
    ai, _seen, gens = build([{"ok": False, "problems": ["마시멜로 200g은 2인분에 많음"]},
                             {"ok": False, "problems": ["냉장 30분은 짧을 수 있음"]}])
    rec, problems = ai.create("두쫀쿠", basis=BASIS)
    assert problems == [] and len(gens) == 2
    assert gens[1]["이전 초안의 문제(고쳐서 다시)"] == ["교차 검토: 마시멜로 200g은 2인분에 많음"]
    assert rec["generated"]["review"]["status"] == "notes"
    assert rec["generated"]["review"]["notes"] == ["냉장 30분은 짧을 수 있음"]
    assert rec["generated"]["attempts"] == 2


def test_a_rewrite_that_breaks_the_rules_falls_back_to_the_first_draft_with_its_notes():
    broken = dict(AI_DRAFT, ingredients=[])
    ai, _seen, _gens = build([{"ok": False, "problems": ["분량 과다"]}], drafts=[AI_DRAFT, broken])
    rec, problems = ai.create("두쫀쿠", basis=BASIS)
    assert problems == [] and rec["generated"]["review"]["notes"] == ["분량 과다"]


def test_a_failed_review_never_blocks_the_recipe():
    ai, _seen, _gens = build([TimeoutError()])
    rec, _p = ai.create("두쫀쿠", basis=BASIS)
    assert rec["generated"]["review"]["status"] == "failed"
    assert not any(c.startswith("교차 검토") for c in rec["generated"]["checks"])


def test_env_picks_gpt_and_never_the_writer_itself():
    env = {"ANTHROPIC_API_KEY": "a", "OPENAI_API_KEY": "o"}
    fn, name = AI.review_from_env(env, writer="anthropic")
    assert fn is not None and name == "openai:gpt-6.1-sol"
    assert AI.review_from_env(dict(env, RECIPE_REVIEW_MODEL="gpt-6-astra"), writer="anthropic")[1] == "openai:gpt-6-astra"
    assert AI.review_from_env(dict(env, RECIPE_REVIEW_PROVIDER="anthropic"), writer="anthropic") == (None, None)
    assert AI.review_from_env(dict(env, RECIPE_REVIEW_PROVIDER="off"), writer="anthropic") == (None, None)
    assert AI.review_from_env({"ANTHROPIC_API_KEY": "a"}, writer="anthropic") == (None, None)   # GPT 키 없음
