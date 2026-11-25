"""셀러 영업 후보 관리자 API (2026-11-25)."""

from __future__ import annotations

from app.services.commerce import coupang_gaps as cg


def test_seller_leads_route(admin_client, tmp_path, monkeypatch):
    monkeypatch.setenv("COUPANG_GAPS_DB", str(tmp_path / "r.sqlite3"))
    cg.GapStore().record("말린 무화과", "zero")
    h = {"X-Access-Token": "test-token"}
    assert admin_client.get("/admin/api/coupang-gaps/leads").status_code in (401, 403)
    j = admin_client.get("/admin/api/coupang-gaps/leads", headers=h).json()
    assert j["items"][0]["query"] == "말린 무화과" and "영업 전" in j["note"]
    r = admin_client.get("/admin/api/coupang-gaps/leads?format=csv", headers=h)
    assert r.status_code == 200 and "text/csv" in r.headers["content-type"] and "말린 무화과" in r.text
