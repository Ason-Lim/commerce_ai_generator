"""대화창 '입점하고 싶어요' → 입점 신청 안내 (쇼핑 검색 없음). 쇼핑 질문은 그대로 (2026-11-25)."""

from __future__ import annotations

from app.services.chat.service import ChatService
from app.services.recipe_chat.service import RecipeChat
from tests.services.chat.conftest import FakeShopping


class NLU:
    def parse(self, text):
        return {"action_intent": "shopping"}


def _svc(db, shop):
    return ChatService(db, shopping=shop, nlu_loader=lambda: NLU(), recipe_chat=RecipeChat(statement_factory=str))


def test_join_question_gets_link_not_products(sqlite_db):
    shop = FakeShopping(items=[{"product_name": "감귤 5kg", "price": 19900, "product_url": "https://www.coupang.com/p",
                                "platform_name": "coupang", "is_coupang": True}])  # fmt: skip
    res = _svc(sqlite_db, shop).handle(None, message="스마트스토어 셀러인데 여기 입점하고 싶어요")
    assert res["stage"] == "seller_join" and shop.calls == []
    md = "\n".join(b["data"].get("md", "") for b in res["blocks"] if b["type"] in ("text", "notice"))
    assert "(/join)" in md and "체험 코드" in md and "AI 가 승인하지 않아요" in md
