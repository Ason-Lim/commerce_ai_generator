"""관리자 트렌드 글 검토 대기열 (2단계) — 초안 → 검토 요청 → 승인(정책 검사) · 반려 · 내림."""
from __future__ import annotations

import pytest

from tests.services.trend_posts.helpers import item, recipe_result, report, search_result

H = {"X-Access-Token": "test-token"}


@pytest.fixture
def posts_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("TREND_POSTS_DIR", str(tmp_path / "posts"))
    from app.services.trend_posts import wiring
    from app.services.trends import surge

    monkeypatch.setattr(surge, "load", lambda date=None: report(item("대방어"), item("하이볼")))
    monkeypatch.setattr(wiring, "find_products", lambda k: search_result())
    monkeypatch.setattr(wiring, "find_recipe", lambda k: recipe_result())
    return tmp_path / "posts"


def test_needs_admin(admin_client, posts_dir):
    assert admin_client.get("/admin/api/trend-posts").status_code == 401
    assert admin_client.post("/admin/api/trend-posts/draft", json={"keyword": "대방어"}).status_code == 401
    r = admin_client.get("/admin/trend-posts/2026-11-15-대방어/preview", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].startswith("/admin/login")


def test_full_flow(admin_client, posts_dir):
    r = admin_client.post("/admin/api/trend-posts/draft", json={"keyword": "대방어"}, headers=H)
    assert r.status_code == 200 and r.json()["created"] and r.json()["issues"] == []
    pid = r.json()["id"]
    again = admin_client.post("/admin/api/trend-posts/draft", json={"keyword": "대방어"}, headers=H).json()
    assert again["created"] is False and again["id"] == pid
    assert admin_client.post(f"/admin/api/trend-posts/{pid}/approve", json={}, headers=H).status_code == 409
    assert admin_client.post(f"/admin/api/trend-posts/{pid}/submit", json={}, headers=H).json()["status"] == "pending"
    pre = admin_client.get(f"/admin/trend-posts/{pid}/preview", headers=H)
    assert pre.status_code == 200 and "미리 보기" in pre.text and pre.headers["x-robots-tag"] == "noindex, nofollow"
    ok = admin_client.post(f"/admin/api/trend-posts/{pid}/approve", json={"note": "확인"}, headers=H).json()
    assert ok["status"] == "approved" and ok["public_url"] == "/trends/" + "2026-11-15-%EB%8C%80%EB%B0%A9%EC%96%B4"
    listed = admin_client.get("/admin/api/trend-posts?status=approved", headers=H).json()
    assert [p["id"] for p in listed["items"]] == [pid] and listed["counts"] == {"approved": 1}
    assert admin_client.post(f"/admin/api/trend-posts/{pid}/withdraw", json={"note": "수정"},
                             headers=H).json()["status"] == "withdrawn"


def test_policy_failure_is_returned_with_issues(admin_client, posts_dir):
    pid = admin_client.post("/admin/api/trend-posts/draft", json={"keyword": "대방어"}, headers=H).json()["id"]
    r = admin_client.post(f"/admin/api/trend-posts/{pid}/update",
                          json={"fields": {"summary": "가성비 최고 29,900원"}}, headers=H)
    assert r.status_code == 200 and {i["code"] for i in r.json()["issues"]} == {"numbers", "price_claim"}
    admin_client.post(f"/admin/api/trend-posts/{pid}/submit", json={}, headers=H)
    r = admin_client.post(f"/admin/api/trend-posts/{pid}/approve", json={}, headers=H)
    assert r.status_code == 409 and r.json()["detail"]["code"] == "policy" and r.json()["detail"]["issues"]
    assert admin_client.post(f"/admin/api/trend-posts/{pid}/reject", json={}, headers=H).status_code == 400
    assert admin_client.post(f"/admin/api/trend-posts/{pid}/reject", json={"note": "가격 문구"},
                             headers=H).json()["status"] == "rejected"


def test_bad_edits_are_refused(admin_client, posts_dir):
    pid = admin_client.post("/admin/api/trend-posts/draft", json={"keyword": "대방어"}, headers=H).json()["id"]
    assert admin_client.post(f"/admin/api/trend-posts/{pid}/update", json={"fields": {"status": "approved"}},
                             headers=H).status_code == 400
    assert admin_client.post(f"/admin/api/trend-posts/{pid}/update", json={"fields": {"products": [{"x": 1}]}},
                             headers=H).status_code == 400
    assert admin_client.post(f"/admin/api/trend-posts/{pid}/explode", json={}, headers=H).status_code == 404
    assert admin_client.get("/admin/api/trend-posts/2026-01-01-없음", headers=H).status_code == 404


def test_alcohol_draft_has_no_products(admin_client, posts_dir):
    r = admin_client.post("/admin/api/trend-posts/draft", json={"keyword": "하이볼"}, headers=H).json()
    assert r["products"] == [] and not r["title"].startswith("[광고]")
