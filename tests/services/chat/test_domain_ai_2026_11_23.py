"""분야 판단 ② — 규칙이 모르고 0건일 때만 AI (2026-11-23, 창 4). claude/stage4_design_2026-11-23.md §2·§9."""
from __future__ import annotations

import pytest

from app.services.chat import domain as D
from app.services.chat.service import ChatService
from app.services.recipe_chat.service import RecipeChat
from tests.services.chat.conftest import FakeShopping


class _NLU:
    def parse(self, text):
        return {"action_intent": "shopping"}


class _Reader:
    def __init__(self, answer=None, error=None):
        self.calls, self.answer, self.error = [], answer, error

    def __call__(self, text):
        self.calls.append(text)
        if self.error:
            raise self.error
        return self.answer


APPLE = [{"product_name": "부사 사과 2kg", "price": 19900, "product_url": "https://www.coupang.com/p",
          "platform_name": "coupang", "is_coupang": True}]


def _svc(sqlite_db, items, reader):
    return ChatService(sqlite_db, shopping=FakeShopping(items=items), nlu_loader=lambda: _NLU(),
                       recipe_chat=RecipeChat(statement_factory=str), domain_reader=reader)


def test_read_ai_accepts_only_allowed_high_confidence():
    ask = lambda d, c="high": (lambda _t: {"domain": d, "confidence": c})  # noqa: E731
    assert D.read_ai(ask("not_food"), "드론 추천").domain == "not_food"
    assert D.read_ai(ask("not_food", "low"), "드론 추천").domain == "food"          # 낮은 확신 → 지금 답
    assert D.read_ai(ask("shopping"), "드론 추천").domain == "food"                 # 허용 목록 밖
    assert D.read_ai(ask("privacy"), "내 거 없애 줘").domain == "food"              # 개인정보는 규칙으로만
    assert D.read_ai(lambda _t: "x", "드론").by == "fallback"
    assert D.read_ai(None, "드론") is None


def test_food_turn_with_products_never_calls_ai(sqlite_db):
    reader = _Reader({"domain": "not_food", "confidence": "high"})
    res = _svc(sqlite_db, APPLE, reader).handle(None, message="사과 추천해줘")
    assert reader.calls == [] and not res["stage"].startswith("domain_")


def test_zero_results_with_non_food_answer_becomes_domain_answer(sqlite_db):
    reader = _Reader({"domain": "not_food", "confidence": "high"})
    res = _svc(sqlite_db, [], reader).handle(None, message="드론 추천해줘")
    assert reader.calls == ['{"문장": "드론 추천해줘"}']
    assert res["stage"] == "domain_not_food"
    assert not any(b["type"] in ("product_list", "search_links") for b in res["blocks"])


def test_zero_results_judged_food_keeps_original_answer(sqlite_db):
    reader = _Reader({"domain": "food", "confidence": "high"})
    res = _svc(sqlite_db, [], reader).handle(None, message="두바이쫀득쿠키 추천해줘")
    assert reader.calls and not res["stage"].startswith("domain_")


def test_ai_error_keeps_original_answer(sqlite_db):
    reader = _Reader(error=TimeoutError())
    res = _svc(sqlite_db, [], reader).handle(None, message="드론 추천해줘")
    assert not res["stage"].startswith("domain_")


def test_coupang_outage_does_not_call_ai(sqlite_db):
    reader = _Reader({"domain": "not_food", "confidence": "high"})
    svc = ChatService(sqlite_db, shopping=FakeShopping(error=RuntimeError("down")), nlu_loader=lambda: _NLU(),
                      recipe_chat=RecipeChat(statement_factory=str), domain_reader=reader)
    svc.handle(None, message="드론 추천해줘")
    assert reader.calls == []


@pytest.mark.parametrize("text", ["내 이름 지워줘", "죽고 싶어요", "어제 산 굴 먹고 배탈 났어요"])
def test_no_ai_domains_never_reach_the_reader(sqlite_db, text):
    reader = _Reader({"domain": "food", "confidence": "high"})
    _svc(sqlite_db, [], reader).handle(None, message=text)
    assert reader.calls == []


def test_health_regulation_phrases_are_rules():
    assert D.by_rules("콜레스테롤 낮추는 과일 추천").domain == "health"
    assert D.by_rules("혈당 관리에 좋은 간식").domain == "health"
    assert D.by_rules("사과 추천해줘") is None


def test_cs_domain_is_a_customer_task():
    from app.services.nlu.llm_client import CUSTOMER_FAST_TASKS, THINKING_BY_TASK

    assert "cs_domain" in CUSTOMER_FAST_TASKS and THINKING_BY_TASK["cs_domain"] is False
