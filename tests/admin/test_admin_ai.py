"""2026-11-11: 관리자 AI 탭 — 비용·재사용·저장된 결과·확인된 사실."""
from app.services.ai import cache as ai_cache
from app.services.ai import usage

H = {"X-Access-Token": "test-token"}


def test_ai_page_needs_login_and_api_needs_token(admin_client):
    assert admin_client.get("/admin/ai", follow_redirects=False).status_code == 303
    assert admin_client.get("/admin/api/ai/cost").status_code == 401
    assert admin_client.get("/admin/api/ai/knowledge").status_code == 401


def test_ai_cost_and_knowledge(admin_client):
    usage.record("food_knowledge", "deepseek:deepseek-v4-flash", 2000, 1000)
    usage.record("food_knowledge", "deepseek:deepseek-v4-flash", cached=True)
    ai_cache.put("food_knowledge", "k", {"tips": ["x"]}, days=1, label="딸기 | 제철")
    r = admin_client.get("/admin/api/ai/cost?days=7", headers=H).json()
    assert r["total"]["calls"] == 1 and r["total"]["reused"] == 1 and r["total"]["usd"] > 0
    assert r["tasks"][0]["label"].startswith("식품 지식")
    k = admin_client.get("/admin/api/ai/knowledge", headers=H).json()
    assert k["cache"][0]["entries"] == 1 and k["facts"] and all(f["source_url"] for f in k["facts"])
    page = admin_client.get("/admin/ai", headers=H)
    assert page.status_code in (200, 303)
