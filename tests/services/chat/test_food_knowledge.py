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
    assert "- **금실**: 과육이 부드러워요 _(Claude 의견: 금실은 과육이 단단한 편이에요)_" in text
    assert "- **설향**: 과즙이 많고 부드러워요\n" in text
    assert "DeepSeek 가 정리하고 Claude 가 한 번 더 검토했어요 — 두 AI 의 생각이 다른 1곳은 그 줄에 Claude 의견을 함께 적었어요" in text
    text2 = md(svc.handle(None, message="딸기 제철 언제야? 품종 차이도 알려줘"))
    assert gen.calls == 1 and "에 정리해 저장한 정보예요" in text2


def test_answers_reviewed_by_an_older_rule_are_reviewed_again_once():
    from app.services.ai import cache as C

    key, label = K.key_of("딸기", "딸기 품종 알려줘")
    C.put(K.TASK, key, dict(ANSWER, _food="딸기"), days=1, label=label, review={"by": "claude", "flags": []})   # 예전 기준
    got = K.answer("딸기 품종 알려줘", "딸기", Gen(), review_flagging_geumsil)
    assert got["review"]["v"] == K.REVIEW_VERSION and got["review"]["flags"][0]["note"].startswith("금실은")
    calls = []
    K.answer("딸기 품종 알려줘", "딸기", Gen(), lambda c, items: calls.append(1) or [])
    assert calls == []                                                   # 새 기준으로 검토한 뒤로는 다시 부르지 않는다


def test_verified_facts_replace_ai_lines_and_show_their_source(sqlite_db, tmp_path, monkeypatch):
    import json

    from app.services.ai import facts

    f = tmp_path / "facts.json"
    f.write_text(json.dumps({"facts": [
        {"id": "g", "food": "딸기", "subject": "금실", "attribute": "특성", "kind": "intrinsic",
         "statement": "과육이 단단하고 저장성이 좋아요.", "source_name": "경남도농업기술원", "source_url": "https://x",
         "method": "source", "verified_at": "2026-11-11", "review_after": None},
        {"id": "s", "food": "딸기", "subject": "", "attribute": "제철", "kind": "seasonal",
         "statement": "옛 제철 정보", "source_name": "옛 자료", "review_after": "2020-01-01"}]}, ensure_ascii=False),
        encoding="utf-8")
    monkeypatch.setenv("VERIFIED_FACTS_FILE", str(f))
    assert facts.find("딸기", "금 실", "특성")["id"] == "g" and facts.find("딸기", "", "제철") is None   # 재확인일 지남

    items = [{"product_name": "금실 딸기 500g", "price": 19900, "product_url": "https://www.coupang.com/g", "is_coupang": True}]
    svc = ChatService(sqlite_db, shopping=FakeShopping(items=items), recipe_chat=RecipeChat(statement_factory=str),
                      food_tips=Gen(), food_review=review_flagging_geumsil)
    res = svc.handle(None, message="딸기 언제부터 맛있어? 품종별 차이 알려줘")
    text = md(res)
    assert "- **금실**: 과육이 단단하고 저장성이 좋아요. _(출처 확인 · 경남도농업기술원)_" in text
    assert "Claude 의견" not in text                          # 확인된 줄에는 Claude 의견 대신 출처
    assert "1곳은 출처로 확인한 내용이라 출처를 함께 적었어요" in text and "보통 12월부터" in text
    notes = [b["data"].get("note") or "" for b in res["blocks"] if b["type"] == "product_list"]
    assert any(n.startswith("과육이 단단하고 저장성이 좋아요.") for n in notes)   # 품종별 상품 안내도 확인된 내용
