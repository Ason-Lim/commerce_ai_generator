"""화면 시험: 장보기 질문('…하려면 재료 뭐 사야 해?')의 레시피 카드는 재료가 먼저, 만드는 순서는 접혀 있다 (2026-11-23 사용자 확인).

서버 답(tests/e2e/fixtures/shopping_recipe_turn.json)은 시험용 대화 흐름으로 만든 실제 답 — layout=shopping.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("playwright.sync_api")

from tests.e2e.test_site_browser import browser, page, site  # noqa: E402,F401

TURN = json.loads((Path(__file__).parent / "fixtures" / "shopping_recipe_turn.json").read_text(encoding="utf-8"))
Q = "가을 능이버섯으로 닭백숙 하려면 재료 뭐 사야 해?"


def _ask(site, page, turn):
    site = site[0]
    page.route("**/api/chat", lambda route: route.fulfill(status=200, content_type="application/json",
                                                          body=json.dumps(turn, ensure_ascii=False)))
    page.goto(site + "/#")
    box = page.get_by_role("textbox").first
    box.fill(Q)
    box.press("Enter")
    card = page.get_by_role("article", name=f"{turn['blocks'][0]['data']['title']} 레시피")
    card.wait_for()
    return card


def test_shopping_question_shows_ingredients_first_and_folds_steps(site, page):
    assert TURN["blocks"][0]["data"]["layout"] == "shopping"
    card = _ask(site, page, TURN)
    fold = card.get_by_role("region", name="만드는 순서 펼치기")
    ingredients = card.get_by_role("region", name="재료", exact=True)
    assert ingredients.bounding_box()["y"] < fold.bounding_box()["y"]          # 재료가 위
    first_step = TURN["blocks"][0]["data"]["steps"][0]
    step_text = (first_step.get("text") if isinstance(first_step, dict) else str(first_step))[:12]
    assert card.get_by_text(step_text).count() == 0                              # 순서는 접힘
    btn = fold.get_by_role("button").first
    assert btn.get_attribute("aria-expanded") == "false"
    btn.click()
    assert btn.get_attribute("aria-expanded") == "true" and card.get_by_text(step_text).count() >= 1
    btn.click()
    page.set_viewport_size({"width": 390, "height": 1500})
    page.wait_for_timeout(300)
    card.screenshot(path=str(Path("/tmp") / "shopping_layout_mobile.png"))


def test_recipe_question_keeps_steps_first(site, page):
    turn = json.loads(json.dumps(TURN))
    turn["blocks"][0]["data"].pop("layout")
    card = _ask(site, page, turn)
    assert card.get_by_role("region", name="만드는 순서 펼치기").count() == 0
