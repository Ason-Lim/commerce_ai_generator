"""관리자 트렌드 탭의 쇼핑커넥트 발급 요청 목록·정리 버튼 · 블로그 초안의 '발급이 필요한 상품' (2026-11-02)."""
from __future__ import annotations

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.services.affiliate import naver_shopping_connect as sc  # noqa: E402

H = {"X-Access-Token": "test-token"}
HEAD = "상품명,스토어명,판매가,쇼핑커넥트 링크,키워드\n"
REPORT = {"generated_at": "2026-10-30T10:00:00+09:00", "data_until": "2026-10-30",
          "items": [{"keyword": "두쫀쿠", "status": "surging"}, {"keyword": "버터떡", "status": "new"},
                    {"keyword": "하이볼", "status": "surging"}]}


@pytest.fixture
def client(tmp_path, monkeypatch):
    from app.admin import auth, routes
    from app.services.trends import surge

    monkeypatch.setattr(auth, "expected_token", lambda: "test-token")
    monkeypatch.setattr(sc, "DB_PATH", tmp_path / "sc.sqlite3")
    reg = tmp_path / "reg.csv"
    reg.write_text(HEAD + "카페블룸 두쫀쿠 50g,카페 블룸,3900,https://naver.me/d,두쫀쿠\n", encoding="utf-8-sig")
    monkeypatch.setenv("NAVER_CONNECT_REGISTRY_CSV", str(reg))
    monkeypatch.setenv("SC_REQUEST_QUEUE", "1")
    monkeypatch.setattr(surge, "ROOT", tmp_path)
    monkeypatch.setattr(surge, "load", lambda date=None, env=None: REPORT)
    monkeypatch.setattr(surge, "blog_draft", lambda report, kws=None: {
        "title": "[트렌드 리포트] 테스트", "tags": ["a"], "body": "본문", "keywords": kws or ["두쫀쿠", "버터떡"]})
    app = FastAPI()
    app.include_router(routes.router)
    return TestClient(app), tmp_path


def test_requests_need_the_token(client):
    c, _ = client
    assert c.get("/admin/api/connect/requests").status_code == 401
    assert c.post("/admin/api/connect/requests/1", json={"status": "issued"}).status_code == 401


def test_queue_from_report_list_and_tidy_up(client):
    c, _ = client
    assert c.post("/admin/api/connect/queue-trends", headers=H, json={}).json()["queued"] == ["버터떡"]
    with sc.connect() as conn:
        sc.queue_request(conn, "과메기")
        sc.queue_request(conn, "과메기")
    d = c.get("/admin/api/connect/requests", headers=H).json()
    assert d["queue_on"] is True
    assert [(i["keyword"], i["reason_label"], i["hit_count"], i["registered"]) for i in d["items"]] == [
        ("과메기", "검색 미매칭", 2, False), ("버터떡", "급상승", 1, False)]
    gwamegi = d["items"][0]["id"]
    assert c.post(f"/admin/api/connect/requests/{gwamegi}", headers=H, json={"status": "issued"}).json() == {"ok": True}
    assert [i["keyword"] for i in c.get("/admin/api/connect/requests", headers=H).json()["items"]] == ["버터떡"]
    done = c.get("/admin/api/connect/requests?status=issued", headers=H).json()["items"]
    assert [i["keyword"] for i in done] == ["과메기"]
    assert c.post(f"/admin/api/connect/requests/{gwamegi}", headers=H, json={"status": "bogus"}).status_code == 422
    with sc.connect() as conn:                                   # 같은 키워드가 다시 열려 있으면 되돌리지 않는다
        sc.queue_request(conn, "과메기")
    assert c.post(f"/admin/api/connect/requests/{gwamegi}", headers=H, json={"status": "open"}).status_code == 409


def test_blog_draft_lists_products_that_need_links(client):
    c, root = client
    out = c.post("/admin/api/trends/blog-draft", headers=H, json={"keywords": ["두쫀쿠", "버터떡", "하이볼"]}).json()
    assert out["link_needs"] == {"need": ["버터떡"], "have": ["두쫀쿠"], "alcohol": ["하이볼"]}
    text = (root / out["file"]).read_text(encoding="utf-8")
    assert text.startswith("[운영 메모 — 블로그에 붙여 넣지 마세요]")
    assert "쇼핑커넥트 링크 발급이 필요한 키워드: 버터떡" in text
    memo, rest = text.split("─" * 30, 1)
    assert "[트렌드 리포트] 테스트" in rest and "본문" in rest and "본문" not in memo
    assert out["body"] == "본문"                                     # 블로그에 붙일 본문에는 메모가 없다
