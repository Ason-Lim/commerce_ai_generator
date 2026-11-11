"""2026-11-11: AI 사용량·비용 기록과 관리자 보고."""
from app.services.ai import pricing, usage


def test_report_sums_cost_and_estimates_savings(monkeypatch):
    monkeypatch.delenv("USD_KRW", raising=False)
    usage.record("food_knowledge", "deepseek:deepseek-v4-flash", 1_000_000, 1_000_000)        # $0.42
    usage.record("food_knowledge", "deepseek:deepseek-v4-flash", cached=True)
    usage.record("food_knowledge", "deepseek:deepseek-v4-flash", cached=True)
    usage.record("cross_check:food_knowledge", "anthropic:claude-sonnet-5-5", 100_000, 10_000)  # $0.30
    usage.record("admin_llm", "openai:gpt-4.1-mini", 500, 50)                                  # 요금 미등록
    r = usage.report(30)
    t = {x["task"]: x for x in r["tasks"]}
    assert abs(t["food_knowledge"]["usd"] - 0.42) < 1e-9 and t["food_knowledge"]["reused"] == 2
    assert abs(t["food_knowledge"]["saved_usd"] - 0.84) < 1e-9 and t["food_knowledge"]["saved_krw"] == 1176.0
    assert abs(t["cross_check:food_knowledge"]["usd"] - 0.30) < 1e-9
    assert t["cross_check:food_knowledge"]["label"] == "교차 확인 (Claude 검토)"
    assert t["admin_llm"]["unpriced"] == 1 and t["admin_llm"]["usd"] == 0
    assert r["total"]["calls"] == 3 and r["total"]["reused"] == 2 and r["usd_krw_assumed"] is True
    assert abs(r["total"]["krw"] - 0.72 * 1400) < 1e-6


def test_prices_can_be_overridden(monkeypatch):
    monkeypatch.setenv("AI_PRICES", '{"gpt-4.1-mini": [0.4, 1.6]}')
    monkeypatch.setenv("USD_KRW", "1350")
    assert pricing.price_of("openai:gpt-4.1-mini") == (0.4, 1.6) and pricing.usd_krw() == 1350
    assert pricing.cost_usd("unknown-model", 10, 10) is None
