"""2026-11-11: AI 사용량·비용 기록과 관리자 보고 — DeepSeek 피크/비피크·캐시 적중·옛 모델 이름."""
from datetime import datetime, timezone

from app.services.ai import pricing, usage

PEAK = datetime(2026, 11, 11, 2, 0, tzinfo=timezone.utc)       # 수요일 UTC 02시 = 한국 11시 (피크)
OFF = datetime(2026, 11, 11, 12, 0, tzinfo=timezone.utc)       # 수요일 UTC 12시 = 한국 21시 (비피크)
SAT = datetime(2026, 11, 14, 2, 0, tzinfo=timezone.utc)        # 토요일은 하루 종일 비피크


def test_deepseek_peak_offpeak_and_cache_hit_prices():
    assert pricing.is_peak(PEAK) and not pricing.is_peak(OFF) and not pricing.is_peak(SAT)
    m = "deepseek:deepseek-v4-flash"                              # 옛 이름 → deepseek-flash 요금
    assert pricing.canonical(m) == "deepseek-flash"
    assert abs(pricing.cost_usd(m, 1_000_000, 1_000_000, at=PEAK) - 1.50) < 1e-9     # 0.30 + 1.20
    assert abs(pricing.cost_usd(m, 1_000_000, 1_000_000, at=OFF) - 0.75) < 1e-9      # 비피크 절반 (0.15 + 0.60)
    assert abs(pricing.cost_usd(m, 1_000_000, 0, hit=1_000_000, at=PEAK) - 0.006) < 1e-12   # 전부 캐시 적중
    assert abs(pricing.cost_usd("anthropic:claude-sonnet-5-5", 100_000, 10_000, at=OFF) - 0.30) < 1e-9   # 피크 없음
    assert pricing.cost_usd("unknown-model", 10, 10) is None


def test_report_sums_cost_and_estimates_savings(monkeypatch):
    monkeypatch.delenv("USD_KRW", raising=False)
    usage.record("food_knowledge", "deepseek:deepseek-v4-flash", 1_000_000, 1_000_000,
                 served="deepseek-flash", at=PEAK)                                         # $1.50
    usage.record("food_knowledge", "deepseek:deepseek-v4-flash", 1_000_000, 1_000_000, at=OFF)   # $0.75
    usage.record("food_knowledge", "deepseek:deepseek-v4-flash", cached=True)
    usage.record("cross_check:food_knowledge", "anthropic:claude-sonnet-5-5", 100_000, 10_000)  # $0.30
    usage.record("admin_llm", "openai:gpt-4.1-mini", 500, 50)                                  # 요금 미등록
    r = usage.report(30)
    t = {x["task"]: x for x in r["tasks"]}
    assert abs(t["food_knowledge"]["usd"] - 2.25) < 1e-9 and t["food_knowledge"]["reused"] == 1
    assert abs(t["food_knowledge"]["saved_usd"] - 1.125) < 1e-9          # 평균 1.125 × 재사용 1
    assert r["peak"]["calls"] == 1 and abs(r["peak"]["usd"] - 1.50) < 1e-9
    assert t["admin_llm"]["unpriced"] == 1 and t["admin_llm"]["usd"] == 0
    assert r["total"]["calls"] == 4 and r["usd_krw_assumed"] is True and r["prices_checked"] == "2026-11-11"


def test_requested_and_served_model_are_both_shown():
    usage.record("shop_keyword", "deepseek:deepseek-v4-flash", 10, 10, served="DeepSeek-V4.1-Flash-1017", at=OFF)
    models = [m["model"] for m in usage.report(30)["models"]]
    assert models == ["deepseek:deepseek-v4-flash"]          # 같은 요금 모델(별칭)이면 이름 하나로
    usage.record("shop_keyword", "deepseek:deepseek-v4-flash", 10, 10, served="deepseek-v4-pro", at=OFF)
    assert "deepseek:deepseek-v4-flash → deepseek-v4-pro" in [m["model"] for m in usage.report(30)["models"]]


def test_prices_can_be_overridden(monkeypatch):
    monkeypatch.setenv("AI_PRICES", '{"gpt-4.1-mini": [0.4, 1.6]}')
    monkeypatch.setenv("USD_KRW", "1350")
    assert pricing.price_of("openai:gpt-4.1-mini") == {"in": 0.4, "out": 1.6} and pricing.usd_krw() == 1350
