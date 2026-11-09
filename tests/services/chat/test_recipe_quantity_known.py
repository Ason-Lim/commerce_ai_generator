"""재료 분량 '적당량'·'약간'은 정량이 아니다 (2026-11-03 p39) — MCP 레시피 응답과 대화 서비스가 같은 규칙."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services.commerce.recipes import to_item
from app.services.recipe_chat.recipes import amount_known


@pytest.mark.parametrize("amount, known", [
    ("적당량", False), ("(적당량)", False), ("약간", False), ("조금", False), ("기호에 따라", False), ("", False),
    (None, False), ("250g", True), ("2큰술", True), ("(가슴살, 100g)", True), ("(1/4개)", True),
])
def test_amount_known(amount, known):
    assert amount_known(amount) is known


def test_mcp_recipe_keeps_the_text_but_marks_vague_amounts_unknown():
    recipe = SimpleNamespace(
        source_level="source", provider="농식품정보누리", source_name="농식품정보누리 레시피", recipe_id="epis-318",
        title="버섯파스타", summary="", meta=[], steps=[], tips=[], extras=lambda: [],
        ingredients=[{"name": "파스타", "amount": "250g"}, {"name": "올리브오일", "amount": "적당량"}],
        content_hash=lambda: "x")
    got = {i.name: i for i in to_item(recipe).ingredients}
    assert got["파스타"].quantity_known is True
    assert got["올리브오일"].quantity_known is False and got["올리브오일"].amount == "적당량"
