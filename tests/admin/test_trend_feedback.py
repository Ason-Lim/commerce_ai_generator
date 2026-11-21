"""트렌드 글 끝 피드백 (2026-11-21) — 설계 §3 '시험(넘어가는 기준)'·§6-8 첫 버전 기준."""
from __future__ import annotations

import sqlite3

import pytest

from tests.services.trend_posts.helpers import Clock, item, report, search_result

H = {"X-Access-Token": "test-token"}


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("TREND_POSTS_DIR", str(tmp_path / "posts"))
    monkeypatch.setenv("TREND_FEEDBACK_DB", str(tmp_path / "fb.sqlite3"))
    monkeypatch.setenv("TREND_AI_COVER", "0")
    from app.services.trend_posts import feedback as fb, wiring
    from app.services.trends import surge

    monkeypatch.setattr(surge, "load", lambda date=None: report(item("대방어")))
    monkeypatch.setattr(wiring, "find_products", lambda k: search_result())
    monkeypatch.setattr(wiring, "find_recipe", lambda k: None)
    monkeypatch.setattr(fb, "LIMITER", fb._Limiter())
    return tmp_path


@pytest.fixture
def app_client(env):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.admin.routes import router as admin
    from app.api.trend_routes import router as public

    a = FastAPI()
    a.include_router(admin)
    a.include_router(public)
    return TestClient(a)


def _publish(c) -> str:
    pid = c.post("/admin/api/trend-posts/draft", json={"keyword": "대방어"}, headers=H).json()["id"]
    c.post(f"/admin/api/trend-posts/{pid}/submit", json={}, headers=H)
    assert c.post(f"/admin/api/trend-posts/{pid}/approve", json={}, headers=H).json()["status"] == "approved"
    return pid


def _rows(env):
    if not (env / "fb.sqlite3").exists():
        return []
    con = sqlite3.connect(env / "fb.sqlite3")
    con.row_factory = sqlite3.Row
    return [dict(r) for r in con.execute("SELECT * FROM feedback ORDER BY id")]


def _url(pid):
    from urllib.parse import quote
    return f"/api/trends/posts/{quote(pid)}/feedback"


def test_only_published_posts_take_feedback(app_client, env):
    pid = app_client.post("/admin/api/trend-posts/draft", json={"keyword": "대방어"}, headers=H).json()["id"]
    assert app_client.post(_url(pid), json={"rating": "good"}).status_code == 404       # 초안
    assert app_client.post(_url("2026-11-15-없는글"), json={"rating": "good"}).status_code == 404
    app_client.post(f"/admin/api/trend-posts/{pid}/submit", json={}, headers=H)
    app_client.post(f"/admin/api/trend-posts/{pid}/approve", json={}, headers=H)
    app_client.post(f"/admin/api/trend-posts/{pid}/withdraw", json={"note": "x"}, headers=H)
    assert app_client.post(_url(pid), json={"rating": "good"}).status_code == 404       # 내림


def test_values_outside_lists_and_free_text_are_refused(app_client, env):
    pid = _publish(app_client)
    assert app_client.post(_url(pid), json={"rating": "great"}).status_code == 400
    assert app_client.post(_url(pid), json={"rating": "bad", "reasons": ["why_clear"]}).status_code == 400   # 좋음 칩
    assert app_client.post(_url(pid), json={"rating": "good", "reasons": ["mismatch"]}).status_code == 400  # 나쁨 칩
    assert app_client.post(_url(pid), json={"rating": "bad", "comment": "별로"}).status_code == 422      # 자유 입력 없음
    assert app_client.post(_url(pid), json={"rating": "bad", "post_version": 9}).status_code == 422     # 판은 서버가
    assert _rows(env) == []


def test_change_in_same_version_updates_and_new_version_adds(app_client, env):
    pid = _publish(app_client)
    r = app_client.post(_url(pid), json={"rating": "bad", "reasons": ["generic"]})
    assert r.status_code == 200 and r.json() == {"ok": True, "rating": "bad", "reasons": ["generic"]}
    assert "tg_fb=" in r.headers["set-cookie"] and "httponly" in r.headers["set-cookie"].lower()
    app_client.post(_url(pid), json={"rating": "ok", "reasons": ["generic", "too_long", "generic"]})
    rows = _rows(env)
    assert len(rows) == 1 and rows[0]["rating"] == "ok" and rows[0]["reasons"] == "generic,too_long"
    assert rows[0]["post_version"] == 1 and rows[0]["source"] == "customer"
    # 서버가 게시본에서 정한 판·규칙 판
    assert rows[0]["format"] == "report" and rows[0]["rules_version"].startswith("report v")
    # 저장 칸에 IP·기기 정보·자유 입력 없음
    from app.services.trend_posts.feedback import FeedbackStore
    cols = FeedbackStore(env / "fb.sqlite3").columns()
    assert not {"ip", "user_agent", "comment", "text"} & set(cols)
    # 내림 → 다시 초안 → 다시 승인 = 2판 → 새 기록, 1판 기록은 그대로
    for a in ("withdraw", "reopen", "submit", "approve"):
        app_client.post(f"/admin/api/trend-posts/{pid}/{a}", json={"note": "고침"}, headers=H)
    app_client.post(_url(pid), json={"rating": "good"})
    rows = _rows(env)
    assert [(x["post_version"], x["rating"]) for x in rows] == [(1, "ok"), (2, "good")]


def test_operator_feedback_is_kept_apart(app_client, env):
    pid = _publish(app_client)
    app_client.post(_url(pid), json={"rating": "bad", "reasons": ["wrong"]}, headers=H)
    assert _rows(env)[0]["source"] == "operator"
    o = app_client.get("/admin/api/trend-feedback", headers=H).json()
    assert o["by_version"] == [] and o["needs_check"] == [] and o["operator"][0]["n"] == 1


def test_immediate_signal_and_version_summary_and_check(app_client, env):
    pid = _publish(app_client)
    app_client.post(_url(pid), json={"rating": "bad", "reasons": ["mismatch", "too_long"]})
    app_client.cookies.clear()
    app_client.post(_url(pid), json={"rating": "good", "reasons": ["short"]})
    app_client.cookies.clear()
    app_client.post(_url(pid), json={"rating": "ok", "reasons": ["too_long"]})
    o = app_client.get("/admin/api/trend-feedback", headers=H).json()
    assert len(o["needs_check"]) == 1 and o["needs_check"][0]["signal"] == ["상품이 주제와 안 맞아요"]
    g = o["by_version"][0]
    assert (g["n"], g["good"], g["ok"], g["bad"]) == (3, 1, 1, 1) and g["helpful_rate"] == pytest.approx(0.333)
    assert g["chip_rates"]["너무 길어요"] == pytest.approx(0.667) and g["review"] is False
    fid = o["needs_check"][0]["id"]
    assert app_client.post(f"/admin/api/trend-feedback/{fid}/checked", json={"note": "상품 뺌"}, headers=H).json()["ok"]
    assert app_client.get("/admin/api/trend-feedback", headers=H).json()["needs_check"] == []
    assert app_client.post(f"/admin/api/trend-feedback/{fid}/checked", json={}, headers=H).status_code == 404
    assert app_client.get("/admin/api/trend-feedback").status_code == 401


def test_public_page_and_api_show_no_aggregates(app_client, env):
    pid = _publish(app_client)
    app_client.post(_url(pid), json={"rating": "good"})
    from urllib.parse import quote
    page = app_client.get("/trends/" + quote(pid)).text
    assert "이 글이 도움이 됐나요?" in page and "이름이나 연락처는 입력받지 않습니다" in page
    assert "명이" not in page and "helpful" not in page
    # 이름 있는 버튼만 (빈 버튼 0)
    import re
    buttons = re.findall(r"<button[^>]*>(.*?)</button>", page[page.index('id=fb'):], re.S)
    assert len(buttons) == 3 + 6 + 3 and all(b.strip() for b in buttons)
    listed = app_client.get("/api/trends/posts").text
    assert "rating" not in listed and "feedback" not in listed
    # 미리 보기(초안)에는 피드백 없음
    d = app_client.post("/admin/api/trend-posts/draft", json={"keyword": "대방어"}, headers=H).json()
    assert d["id"] == pid                                  # 같은 주제 글이 있어 그 글을 연다 — 새 글로 확인
    from app.services.trend_posts import render
    from app.services.trend_posts.store import FilePostStore
    draft = FilePostStore(env / "posts").get(pid).model_copy(update={"status": "draft"})
    assert "id=fb" not in render.post_page(draft)


def test_rate_limit_per_browser(app_client, env):
    pid = _publish(app_client)
    codes = [app_client.post(_url(pid), json={"rating": "good"}).status_code for _ in range(12)]
    assert codes[:10] == [200] * 10 and codes[-1] == 429


def test_one_year_retention_and_no_auto_actions(env):
    from app.services.trend_posts import feedback as fb
    from app.services.trend_posts.service import TrendPosts
    from app.services.trend_posts.store import FilePostStore

    clock = Clock()
    svc = TrendPosts(store=FilePostStore(env / "posts"), clock=clock)
    post, _ = svc.create_from_surge(report(), "대방어", find_products=lambda k: search_result())
    svc.submit(post.id)
    post = svc.approve(post.id)
    st = fb.FeedbackStore(env / "fb.sqlite3", clock=clock)
    for i in range(12):
        st.record(post, "bad", ["wrong"], f"{i:032x}", operator=False)
    assert svc.get(post.id).status == "approved"           # 나쁨이 많아도 글은 그대로 (자동 내림 없음)
    assert st.by_version()[0]["review"] is True
    clock.advance(days=366)
    st.record(post, "good", [], "f" * 32, operator=False)
    assert [g["n"] for g in st.by_version()] == [1]


def test_improvement_log(app_client, env):
    body = {"day": "2026-11-21", "scope": "rule", "basis": "'너무 길어요' 4주 34표 중 9표(26%)", "change": "기준 3줄→2줄",
            "rules_from": "report v1.1", "rules_to": "report v1.2", "approver": "Ason", "check_due": "2026-12-19"}
    r = app_client.post("/admin/api/trend-feedback/improvements", json=body, headers=H).json()
    assert r["id"] and r["rules_to"] == "report v1.2" and r["result"] is None
    assert app_client.post("/admin/api/trend-feedback/improvements", json={**body, "scope": "x"}, headers=H).status_code == 422
    assert app_client.post(f"/admin/api/trend-feedback/improvements/{r['id']}/result", json={"result": "좋아짐"},
                           headers=H).status_code == 400
    assert app_client.post(f"/admin/api/trend-feedback/improvements/{r['id']}/result", json={"result": "유지"},
                           headers=H).json()["ok"]
    assert app_client.get("/admin/api/trend-feedback", headers=H).json()["improvements"][0]["result"] == "유지"
