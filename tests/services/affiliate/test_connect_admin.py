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
    monkeypatch.setattr(surge, "blog_draft", lambda report, kws=None, **kw: {
        "title": "[트렌드 리포트] 테스트", "tags": ["a"], "body": "본문", "keywords": kws or ["두쫀쿠", "버터떡"]})
    from app.services.trend_posts import wiring                  # 2026-11-17: 쿠팡 링크는 시험용 검색 결과로
    monkeypatch.setattr(wiring, "find_products", lambda k: {"items": []} if k == "버터떡" else {"items": [
        {"section": "picks", "product": {"title": f"{k} 상품"},
         "offer": {"platform": "쿠팡", "product_url": f"https://link.coupang.com/a/{abs(hash(k)) % 999}",
                   "price_krw": 3900, "link_type": "affiliate"}}]})
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
    # 2026-11-17: 쿠팡 링크 — 찾은 개수, 못 찾은 키워드(주류 포함)는 운영 메모 안에만
    assert out["coupang"] == {"두쫀쿠": 1, "버터떡": 0, "하이볼": 0}
    assert "쿠팡 링크를 찾지 못한 키워드(주류는 넣지 않음): 버터떡, 하이볼" in memo


def test_blog_draft_can_skip_coupang(client):
    c, _ = client
    out = c.post("/admin/api/trends/blog-draft", headers=H, json={"keywords": ["두쫀쿠"], "with_coupang": False}).json()
    assert out["coupang"] is None



def test_blog_draft_makes_two_versions_and_saves_edits(client, monkeypatch):
    """2026-11-17: 네이버 블로그용 + 쿠팡용 두 판, 고친 내용 저장 (운영 메모는 그대로), 저장 위치는 초안 폴더만."""
    from app.services.trends import surge

    monkeypatch.setattr(surge, "blog_draft", lambda report, kws=None, **kw: {
        "title": f"[트렌드 리포트] {kw.get('variant')}", "tags": ["a"], "variant": kw.get("variant", "naver"),
        "body": f"본문 {kw.get('variant')} connect_ok={kw.get('connect_ok')}", "keywords": kws or ["두쫀쿠"]})
    monkeypatch.setenv("SC_BLOG_APPROVED", "1")
    c, root = client
    out = c.post("/admin/api/trends/blog-draft", headers=H, json={"keywords": ["두쫀쿠", "버터떡"]}).json()
    naver, coupang = out["drafts"]["naver"], out["drafts"]["coupang"]
    assert out["file"] == naver["file"] and coupang["file"] == naver["file"][:-4] + "_쿠팡용.txt"
    assert naver["body"] == "본문 naver connect_ok=True" and coupang["body"].startswith("본문 coupang")
    naver_text = (root / naver["file"]).read_text(encoding="utf-8")
    coupang_text = (root / coupang["file"]).read_text(encoding="utf-8")
    assert "쇼핑커넥트 링크 발급이 필요한 키워드" in naver_text                     # 발급 안내는 네이버용 메모에만
    assert "쇼핑커넥트" not in coupang_text and "쿠팡 링크를 찾지 못한 키워드(주류는 넣지 않음): 버터떡" in coupang_text
    monkeypatch.setenv("SC_BLOG_APPROVED", "0")
    out = c.post("/admin/api/trends/blog-draft", headers=H, json={"keywords": ["두쫀쿠"]}).json()
    assert out["drafts"]["naver"]["body"].endswith("connect_ok=False")

    # 고쳐 저장 — 운영 메모는 남고, 제목·태그·본문이 바뀐다
    edited = ("이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.\n"
              "고친 본문 https://link.coupang.com/a/x")
    r = c.post("/admin/api/trends/blog-draft/save", headers=H, json={
        "file": naver["file"], "title": "고친 제목", "tags": ["#두쫀쿠", " 디저트 "], "body": edited}).json()
    assert r["saved"] and r["warnings"] == []
    text = (root / naver["file"]).read_text(encoding="utf-8")
    memo, rest = text.split("─" * 30, 1)
    assert memo.startswith("[운영 메모 — 블로그에 붙여 넣지 마세요]") and "고친" not in memo
    assert "고친 제목\n\n태그: 두쫀쿠, 디저트\n\n" + edited in rest

    # 경고 (막지는 않음): 쿠팡 링크인데 고지 없음 · 남은 삽입 자리 · 승인 전 쇼핑커넥트 고지
    w = c.post("/admin/api/trends/blog-draft/save", headers=H, json={
        "file": coupang["file"], "title": "t", "body": "https://link.coupang.com/a/x\n▶ [여기에 상품]\n"
        "이 포스팅은 네이버 쇼핑 커넥트 활동의 일환으로"}).json()["warnings"]
    assert len(w) == 3

    # 초안 폴더 밖·없는 파일은 저장하지 않음
    for bad in ("var/blog_drafts/../../.env", ".env", "var/blog_drafts/trend_없음.txt", "var/blog_drafts/x.txt"):
        assert c.post("/admin/api/trends/blog-draft/save", headers=H,
                      json={"file": bad, "title": "t", "body": "b"}).status_code in (404, 422), bad
    assert c.post("/admin/api/trends/blog-draft/save", json={"file": naver["file"], "title": "t", "body": "b"}).status_code == 401
