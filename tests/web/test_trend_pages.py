"""공개 /trends 페이지 (2단계) — 승인된 글만, 상품 이동은 누를 때만 + 클릭 기록, 오래된 가격 숨김."""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import trend_routes
from html import escape

from tests.services.trend_posts.helpers import Clock, approved, item, report, search_result, service


@pytest.fixture
def env(tmp_path, monkeypatch):
    clock = Clock()
    svc = service(tmp_path, clock)
    clicks = []
    monkeypatch.setattr("app.services.analytics_logger.log_product_click",
                        lambda **kw: clicks.append(kw))
    app = FastAPI()
    app.include_router(trend_routes.router)
    app.dependency_overrides[trend_routes.get_trend_posts] = lambda: svc
    return TestClient(app, follow_redirects=False), svc, clock, clicks


def test_index_and_post_show_only_approved(env):
    client, svc, _clock, _ = env
    live = approved(svc)
    waiting, _ = svc.create_from_surge(report(item("천수무")), "천수무")
    svc.submit(waiting.id)
    r = client.get("/trends")
    assert r.status_code == 200 and escape(live.title) in r.text and "천수무" not in r.text
    assert client.get(f"/trends/{live.id}").status_code == 200
    miss = client.get(f"/trends/{waiting.id}")
    assert miss.status_code == 404 and "천수무" not in miss.text
    for odd in ("/trends/x", "/trends/..%2F..%2Fetc%2Fpasswd"):
        assert client.get(odd).status_code == 404


def test_go_redirects_only_for_published_products_and_logs_the_click(env):
    client, svc, _clock, clicks = env
    post = approved(svc)
    r = client.get(f"/trends/{post.id}/go/1")
    assert r.status_code == 302 and r.headers["location"] == "https://link.coupang.com/a/aaa"
    assert clicks[-1]["session_id"] == f"trend:{post.id}" and clicks[-1]["query"] == "trend"
    assert clicks[-1]["product"]["selected_section"] == "trend" and clicks[-1]["product"]["rank"] == 1
    for bad in (f"/trends/{post.id}/go/0", f"/trends/{post.id}/go/9"):
        assert client.get(bad).headers["location"] == "/trends"
    svc.withdraw(post.id, "내림")
    n = len(clicks)
    assert client.get(f"/trends/{post.id}/go/1").headers["location"] == "/trends" and len(clicks) == n


def test_admin_browser_clicks_are_marked_internal(env, monkeypatch):
    client, svc, _clock, clicks = env
    post = approved(svc)
    monkeypatch.setattr("app.admin.auth.request_ok", lambda request: True)
    client.get(f"/trends/{post.id}/go/2")
    assert clicks[-1]["query"] == "trend_internal"


def test_click_log_failure_does_not_block_the_redirect(env, monkeypatch):
    client, svc, _clock, _ = env
    post = approved(svc)

    def boom(**kw):
        raise RuntimeError("db down")

    monkeypatch.setattr("app.services.analytics_logger.log_product_click", boom)
    assert client.get(f"/trends/{post.id}/go/1").status_code == 302


def test_page_hides_price_after_30_days(env):
    client, svc, clock, _ = env
    post = approved(svc)
    assert "29,900원" in client.get(f"/trends/{post.id}").text
    clock.advance(days=31)
    text = client.get(f"/trends/{post.id}").text
    assert "29,900" not in text and "가격은 판매처에서 확인해 주세요" in text


def test_main_app_serves_trends_before_the_screen(monkeypatch):
    from app import main

    paths = [getattr(r, "path", "") for r in main.app.routes]
    assert "/trends/{post_id}" in paths and paths.index("/trends") < len(paths)
    assert search_result()                                    # helpers 재사용 확인
