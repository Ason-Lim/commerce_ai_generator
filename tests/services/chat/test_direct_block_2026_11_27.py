"""2026-11-27 대화 결과 아래 해외 직구 칸 — 추천 후보·순서는 그대로."""

from __future__ import annotations


def test_chat_result_gets_direct_block_after_products_without_changing_them(sqlite_db, monkeypatch):
    from app.services.chat.service import ChatService
    from app.services.recipe_chat.service import RecipeChat
    from tests.services.chat.conftest import FakeShopping

    class NLU:
        def parse(self, text):
            return {"action_intent": "shopping"}

    item = [{"product_name": "엑스트라버진 올리브유 500ml", "price": 12900, "product_url": "https://www.coupang.com/vp/products/1",
             "platform_name": "coupang", "is_coupang": True}]

    def run(on):
        monkeypatch.setenv("DIRECT_IN_CHAT", "1" if on else "0")
        svc = ChatService(sqlite_db, shopping=FakeShopping(items=item), nlu_loader=lambda: NLU(),
                          recipe_chat=RecipeChat(statement_factory=str))
        return svc.handle(None, message="올리브유 추천해줘")["blocks"]

    on, off = run(True), run(False)
    kinds = [b["type"] for b in on]
    assert "direct_buy" in kinds and kinds.index("direct_buy") > kinds.index("product_list")
    strip = lambda bs: [b for b in bs if b["type"] == "product_list"]  # noqa: E731
    assert [[i.get("title") for i in b["data"]["items"]] for b in strip(on)] == \
           [[i.get("title") for i in b["data"]["items"]] for b in strip(off)]           # 추천 후보·순서 그대로
