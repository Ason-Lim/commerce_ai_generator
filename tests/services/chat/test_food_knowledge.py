"""2026-11-11: 식품 지식은 '식품 + 질문 종류'로 저장해 다시 쓰고, 새 답은 Claude 가 검토(교차 확인)한다."""
from __future__ import annotations

from app.services.ai import cache as ai_cache
from app.services.chat import food_knowledge as K
from app.services.chat.service import ChatService
from app.services.recipe_chat.service import RecipeChat
from tests.services.chat.conftest import FakeShopping

ANSWER = {"food": "딸기", "tips": [], "season": "보통 12월부터 이듬해 5월까지",
          "varieties": [{"name": "설향", "note": "과즙이 많고 부드러워요"}, {"name": "금실", "note": "과육이 부드러워요"}]}


class Gen:
    def __init__(self, answer=ANSWER):
        self.answer, self.calls = answer, 0

    def __call__(self, text):
        self.calls += 1
        return self.answer


def review_flagging_geumsil(context, items):
    return [{"ok": "금실" not in t, "note": "" if "금실" not in t else "금실은 과육이 단단한 편이에요"} for t in items]


def md(res):
    return "\n".join(b["data"].get("md", "") for b in res["blocks"] if b["type"] in ("text", "notice"))


def test_same_food_and_question_kind_share_one_saved_answer():
    assert K.key_of("딸기", "딸기 제철 언제야?")[0] == K.key_of("딸기", "딸기 언제부터 맛있어?")[0]
    assert K.key_of("딸기", "딸기 제철 언제야?")[0] != K.key_of("딸기", "딸기 품종별 차이 알려줘")[0]
    assert K.topics("귤 냉장 보관해도 돼?") == ["보관"]


def test_second_question_reuses_the_saved_answer_and_review():
    gen = Gen()
    first = K.answer("딸기 언제부터 맛있어? 품종별 차이 알려줘", "딸기", gen, review_flagging_geumsil)
    assert not first["from_cache"] and first["review"]["flags"] == [
        {"kind": "variety", "i": 1, "note": "금실은 과육이 단단한 편이에요"}]
    again = K.answer("딸기 제철이 언제야? 품종 차이도 알려줘", "딸기", gen, None)
    assert again["from_cache"] and gen.calls == 1 and again["got"]["season"].startswith("보통 12월")
    assert again["review"]["flags"][0]["i"] == 1 and again["food"] == "딸기"
    assert ai_cache.stats() and ai_cache.stats()[0]["task"] == "food_knowledge"


def test_answer_saved_without_review_gets_reviewed_later():
    gen = Gen()
    K.answer("딸기 언제부터 맛있어? 품종별 차이 알려줘", "딸기", gen, None)           # 검토 없이 저장
    later = K.answer("딸기 언제부터 맛있어? 품종별 차이 알려줘", "딸기", gen, review_flagging_geumsil)
    assert later["from_cache"] and later["review"]["flags"] and gen.calls == 1
    assert K.answer("딸기 언제부터 맛있어? 품종별 차이 알려줘", "딸기", gen, None)["review"]["flags"]


def test_nothing_is_saved_when_the_ai_gives_nothing():
    gen = Gen({"food": "딸기", "tips": []})
    K.answer("딸기 보관 어떻게 해?", "딸기", gen, None)
    K.answer("딸기 보관 어떻게 해?", "딸기", gen, None)
    assert gen.calls == 2


def test_chat_shows_review_notes_and_where_the_answer_came_from(sqlite_db):
    items = [{"product_name": "설향 딸기 500g", "price": 15900, "product_url": "https://www.coupang.com/a", "is_coupang": True}]
    gen = Gen()
    svc = ChatService(sqlite_db, shopping=FakeShopping(items=items), recipe_chat=RecipeChat(statement_factory=str),
                      food_tips=gen, food_review=review_flagging_geumsil)
    text = md(svc.handle(None, message="딸기 언제부터 맛있어? 품종별 차이 알려줘"))
    assert "- **금실**: 과육이 부드러워요 _(검토 AI 의견: 금실은 과육이 단단한 편이에요)_" in text
    assert "- **설향**: 과즙이 많고 부드러워요\n" in text
    assert "DeepSeek 가 정리하고 Claude 가 한 번 더 검토했어요 (검토 의견 1건은 해당 줄에 적었어요)" in text
    text2 = md(svc.handle(None, message="딸기 제철 언제야? 품종 차이도 알려줘"))
    assert gen.calls == 1 and "에 정리해 저장한 정보예요" in text2
