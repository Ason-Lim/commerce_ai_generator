"""2026-11-21 사용자 결정: 고객 문장이 들어가는 작업은 DeepSeek(중국)에 보내지 않는다 — OpenAI 가 쓰고(저장본은 Claude 검토),
실패하면 Claude 로. 내부 작업(고객 문장 없음)은 DeepSeek 그대로. CUSTOMER_LLM_PROVIDER=deepseek 로 되돌릴 수 있다."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services.nlu.llm_client import CUSTOMER_TASKS, LLMClient

ENV = {"LLM_PROVIDER": "deepseek", "DEEPSEEK_API_KEY": "d", "DEEPSEEK_MODEL": "deepseek-flash",
       "OPENAI_API_KEY": "o", "ANTHROPIC_API_KEY": "a", "CUSTOMER_LLM_PROVIDER": "openai"}


def _openai_ok(calls):
    def factory(**kw):
        def create(**req):
            calls.append(("openai", req["model"], kw.get("base_url")))
            msg = SimpleNamespace(content='{"keyword": "사과"}')
            return SimpleNamespace(choices=[SimpleNamespace(message=msg)], usage=None, model=req["model"])
        return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    return factory


def _claude_ok(calls):
    def post(url, json, timeout, headers):
        calls.append(("anthropic", json["model"], url))
        return SimpleNamespace(raise_for_status=lambda: None,
                               json=lambda: {"content": [{"type": "text", "text": '{"keyword": "배"}'}], "usage": {}})
    return post


@pytest.mark.parametrize("task,model", [("shop_keyword", "gpt-5.4-mini"), ("chat_intent", "gpt-5.4-mini"),
                                        ("stock_chat", "gpt-5.4-mini"), ("food_knowledge", "gpt-5.4"),
                                        ("recipe_consult", "gpt-5.4")])
def test_customer_tasks_go_to_openai_not_deepseek(task, model):
    calls = []
    c = LLMClient("x", provider="deepseek", env=ENV, task=task, openai_factory=_openai_ok(calls))
    assert c.chat_json("사과 추천") == {"keyword": "사과"}
    assert calls == [("openai", model, None)]                 # base_url 없음 = DeepSeek 주소로 보내지 않음


@pytest.mark.parametrize("task", ["trend_cause", "recipe_supplement", "recipe_easy_view", "recipe_discover", "warm_classify"])
def test_internal_tasks_stay_on_deepseek(task):
    assert task not in CUSTOMER_TASKS
    c = LLMClient("x", provider="deepseek", env=ENV, task=task)
    assert c.provider == "deepseek" and c.fallback is None


def test_openai_failure_falls_back_to_claude_not_deepseek():
    calls = []

    def broken(**kw):
        def create(**req):
            calls.append(("openai", req["model"], kw.get("base_url")))
            raise TimeoutError("openai down")
        return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))

    c = LLMClient("x", provider="deepseek", env=ENV, task="shop_keyword", openai_factory=broken,
                  http_post=_claude_ok(calls))
    assert c.chat_json("배 추천") == {"keyword": "배"}
    assert [x[0] for x in calls] == ["openai", "anthropic"] and calls[1][1] == "claude-haiku-5-5"
    assert not any("deepseek" in str(x) for x in calls)


def test_model_overrides_revert_and_missing_openai_key():
    c = LLMClient("x", provider="deepseek", env=dict(ENV, OPENAI_FAST_MODEL="gpt-5.4-nano"), task="shop_keyword")
    assert (c.provider, c._model_name()) == ("openai", "gpt-5.4-nano")
    assert LLMClient("x", provider="deepseek", env=dict(ENV, CUSTOMER_LLM_PROVIDER="deepseek"),
                     task="shop_keyword").provider == "deepseek"
    no_openai = {k: v for k, v in ENV.items() if k != "OPENAI_API_KEY"}
    c = LLMClient("x", provider="deepseek", env=no_openai, task="food_knowledge")
    assert (c.provider, c._model_name()) == ("anthropic", "claude-sonnet-5-5")   # 중국으로 되돌아가지 않음
    c = LLMClient("x", env=ENV, cache="food_nlu")                                 # LLM_PROVIDER=deepseek 로 만든 것도
    assert c.provider == "openai"


def test_cache_key_and_cost_use_the_routed_model():
    from app.services.ai import pricing

    c = LLMClient("x", provider="deepseek", env=ENV, cache="shop_keyword")
    assert f"{c.provider}:{c._model_name()}" == "openai:gpt-5.4-mini"
    assert pricing.price_of("openai:gpt-5.4-mini")["out"] == 4.50 and pricing.price_of("gpt-5.4")["in"] == 2.50
