"""2026-11-11: AI 결과 저장·재사용 + 교차 확인."""
from __future__ import annotations

import json

from app.services.ai import cache as ai_cache
from app.services.ai import cross_check
from app.services.nlu.llm_client import LLMClient


def test_store_put_get_expiry_and_off(monkeypatch):
    ai_cache.put("t", "k", {"a": 1}, days=1, label="라벨")
    hit = ai_cache.get("t", "k")
    assert hit["value"] == {"a": 1} and hit["label"] == "라벨"
    ai_cache.put("t", "old", {"a": 2}, days=-1)                 # 이미 만료
    assert ai_cache.get("t", "old") is None
    ai_cache.put("t", "empty", {}, days=1)                       # 빈 결과는 저장하지 않음
    assert ai_cache.get("t", "empty") is None
    assert ai_cache.stats()[0]["entries"] == 2 and ai_cache.stats()[0]["reused"] == 1
    monkeypatch.setenv("AI_CACHE", "0")
    assert ai_cache.get("t", "k") is None


class FakeCompletions:
    def __init__(self):
        self.calls = 0

    def create(self, **kw):
        self.calls += 1
        msg = type("M", (), {"content": json.dumps({"n": self.calls})})
        return type("R", (), {"choices": [type("C", (), {"message": msg})]})


def _client(fake, cache):
    env = {"DEEPSEEK_API_KEY": "k", "DEEPSEEK_MODEL": "m"}
    chat = type("Chat", (), {"completions": fake})
    return LLMClient("시스템", provider="deepseek", env=env, cache=cache,
                     openai_factory=lambda **kw: type("O", (), {"chat": chat})())


def test_llm_client_reuses_saved_answers_only_when_asked():
    fake = FakeCompletions()
    c = _client(fake, "shop_keyword")
    assert c.chat_json("딸기 1kg 추천") == {"n": 1}
    assert c.chat_json("딸기 1kg 추천") == {"n": 1} and fake.calls == 1      # 다시 쓰기
    assert c.chat_json("사과 추천") == {"n": 2}                              # 다른 입력은 새로
    plain = _client(fake, None)
    plain.chat_json("딸기 1kg 추천")
    assert fake.calls == 3                                                   # 저장 안 하는 호출


def test_cross_check_maps_verdicts_and_survives_bad_answers():
    items = ["제철: 12~5월", "품종 금실: 과육이 부드러움", "꼭지를 아래로 두세요"]
    got = cross_check.review("t", "식품: 딸기", items,
                             call=lambda s, u: {"items": [{"i": 1, "ok": False, "note": "금실은 단단한 편"},
                                                          {"i": 0, "ok": True}, {"i": 9, "ok": False}]})
    assert got == [{"ok": True, "note": ""}, {"ok": False, "note": "금실은 단단한 편"}, {"ok": True, "note": ""}]
    assert cross_check.review("t2", "x", items, call=lambda s, u: {"nope": 1}) is None
    assert cross_check.review("t3", "x", items, call=lambda s, u: (_ for _ in ()).throw(RuntimeError())) is None


def test_cross_check_is_off_without_a_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert cross_check.reviewer("food_knowledge") is None
    assert cross_check.review("t", "x", ["a"]) is None


def test_b2b_polish_reverts_lines_the_reviewer_rejects(monkeypatch):
    from app.admin.b2b import proposal

    monkeypatch.setattr(cross_check, "review", lambda task, ctx, items, instruction="", cache=True: [
        {"ok": False, "note": "원문에 없는 수상 실적"}, {"ok": True, "note": ""}])
    lines = ["납품 3일 안에 합니다", "교환은 7일 안에 됩니다", "같음"]
    polished = ["업계 1위 업체로서 3일 안에 납품합니다", "교환은 7영업일 이내 가능합니다", "같음"]
    assert proposal._cross_checked(lines, polished) == [lines[0], polished[1], "같음"]


def test_admin_llm_is_not_cached_and_b2b_review_is_not_saved(monkeypatch):
    from app.admin.shared import llm as admin_llm
    from app.services.ai import cache as C

    calls = []
    monkeypatch.setattr(admin_llm.LLMClient, "_chat_json", lambda self, s, u, **kw: calls.append(u) or {"lines": ["a"]})
    c = admin_llm.LLMClient()
    c.chat_json("지시", "공고 원문")
    c.chat_json("지시", "공고 원문")
    assert len(calls) == 2 and C.stats() == []               # 관리자 호출은 저장·재사용 안 함
    cross_check.review("b2b_polish", "x", ["원문: a\n다듬은 문장: b"],
                       call=lambda s, u: {"items": [{"i": 0, "ok": True}]}, cache=False)
    assert C.stats() == []


def test_deepseek_thinking_is_sent_only_when_asked(monkeypatch):
    from app.services.nlu.llm_client import LLMClient

    seen = []

    class Fake:
        def __init__(self, **kw):
            self.chat = self
            self.completions = self

        def create(self, **kw):
            seen.append(kw.get("extra_body"))
            msg = type("M", (), {"content": '{"ok": 1}'})
            return type("R", (), {"choices": [type("C", (), {"message": msg})], "usage": None, "model": "deepseek-flash"})

    env = {"DEEPSEEK_API_KEY": "k", "DEEPSEEK_MODEL": "deepseek-flash"}
    LLMClient("s", provider="deepseek", env=env, openai_factory=Fake).chat_json("a")
    LLMClient("s", provider="deepseek", env=env, openai_factory=Fake, thinking=False).chat_json("a")
    LLMClient("s", provider="deepseek", env={**env, "DEEPSEEK_THINKING": "off"}, openai_factory=Fake).chat_json("a")
    assert seen == [None, {"thinking": {"type": "disabled"}}, {"thinking": {"type": "disabled"}}]
