"""블로그 초안 상품 링크 고르기·넣기 · '저장' = 네이버 임시저장 (2026-11-21 사용자 요청)."""
from __future__ import annotations

import pytest

from app.services.trend_posts import templates
from app.services.trends import blog_links as bl
from app.services.trends.surge import AD_PREFIX, COUPANG_DISCLOSURE, DISCLOSURE, SITE_OPS

NAVER_BODY = (f"{DISCLOSURE}\n\n도입\n\n■ 1. 비상식량\n- 데이터 줄\n▶ [여기에 스마트에디터 '쇼핑커넥트'로 상품 삽입: 비상식량]\n\n"
              "■ 2. 절임배추\n- 데이터 줄\n▶ [여기에 스마트에디터 '쇼핑커넥트'로 상품 삽입: 절임배추]\n\n※ 출처 줄")
L1 = {"title": "해남 절임배추 10kg", "url": "https://naver.me/aaa"}
L2 = {"title": "괴산 절임배추 20kg", "url": "https://naver.me/bbb"}


def test_naver_links_replace_placeholder_only_in_that_section():
    out = bl.set_naver_links(NAVER_BODY, "절임배추", [L1, L2], DISCLOSURE)
    assert f"{bl.NAVER_HEAD}\n- 해남 절임배추 10kg: https://naver.me/aaa\n- 괴산 절임배추 20kg: https://naver.me/bbb" in out
    assert "상품 삽입: 절임배추]" not in out and "상품 삽입: 비상식량]" in out       # 다른 절은 그대로
    assert out.index("■ 2. 절임배추") < out.index(bl.NAVER_HEAD) < out.index("※ 출처 줄")
    again = bl.set_naver_links(out, "절임배추", [L2], DISCLOSURE)                    # 바꾸면 묶음 통째로 교체
    assert "naver.me/aaa" not in again and again.count(bl.NAVER_HEAD) == 1
    back = bl.set_naver_links(again, "절임배추", [], DISCLOSURE)                     # 빼면 자리 안내로 되돌림
    assert back == NAVER_BODY


def test_naver_links_add_disclosure_and_refuse_other_hosts():
    bare = NAVER_BODY.replace(DISCLOSURE + "\n\n", "")
    assert bl.set_naver_links(bare, "비상식량", [L1], DISCLOSURE).startswith(DISCLOSURE)
    for bad in ("https://smartstore.naver.com/x/products/1", "http://naver.me/a", "https://evil.example/a"):
        with pytest.raises(bl.LinkError):
            bl.set_naver_links(NAVER_BODY, "비상식량", [{"title": "x", "url": bad}], DISCLOSURE)
    with pytest.raises(bl.LinkError, match="절을 찾지"):
        bl.set_naver_links(NAVER_BODY, "없는키워드", [L1], DISCLOSURE)


def test_connect_options_exact_keyword_first_and_skips_bad_rows():
    rows = [{"상품명": "괴산 절임배추 20kg", "쇼핑커넥트 링크": "https://naver.me/bbb", "키워드": "김장"},
            {"상품명": "해남 절임배추 10kg", "쇼핑커넥트 링크": "https://naver.me/aaa", "키워드": "절임배추"},
            {"상품명": "절임배추 막걸리 세트", "쇼핑커넥트 링크": "https://naver.me/ccc", "키워드": "절임배추"},
            {"상품명": "절임배추 정기배송", "쇼핑커넥트 링크": "https://naver.me/ddd", "키워드": "절임배추"},
            {"상품명": "절임배추 5kg", "쇼핑커넥트 링크": "https://smartstore.naver.com/x", "키워드": "절임배추"}]
    o = bl.connect_options(["절임배추", "비상식량"], rows)
    assert [(x["url"], x["match"]) for x in o["by_keyword"]["절임배추"]] == [
        ("https://naver.me/aaa", "키워드 같음"), ("https://naver.me/bbb", "이름에 포함")]
    assert o["by_keyword"]["비상식량"] == [] and len(o["all"]) == 2
    body, used = bl.auto_naver(NAVER_BODY, o, DISCLOSURE)                          # 자동은 키워드 같은 것만
    assert used == {"절임배추": 1} and "naver.me/aaa" in body and "naver.me/bbb" not in body


COUPANG_BODY = (f"{COUPANG_DISCLOSURE}\n{SITE_OPS}\n\n먼저 답부터\n\n■ 1. 절임배추\n- 데이터\n결제 전 확인 줄\n▶ 쿠팡에서 보기\n"
                "- 예전 상품: https://link.coupang.com/a/old\n  · 중량·수량: 10kg (상품명 표기)\n\n■ 2. 황석어젓갈\n- 데이터\n\n"
                f"※ 출처\n{COUPANG_DISCLOSURE}")
C1 = {"title": "[로켓프레시] 해남 절임배추 20kg", "url": "https://link.coupang.com/a/new", "rocket": True}
KW = dict(disclosure=COUPANG_DISCLOSURE, site_ops=SITE_OPS, ad_prefix=AD_PREFIX, hold_line=templates.HOLD_LINE["blog"])


def test_coupang_links_swap_block_and_add_new_section_block():
    t, out = bl.set_coupang_links("[광고] 제목", COUPANG_BODY, "절임배추", [C1], **KW)
    assert "link.coupang.com/a/old" not in out and "예전 상품" not in out and "10kg (상품명 표기)" not in out
    assert "- [로켓프레시] 해남 절임배추 20kg: https://link.coupang.com/a/new\n  · 중량·수량: 20kg" in out
    assert out.count("결제 전 확인 줄") == 1                                            # 있던 줄은 그대로
    t2, out2 = bl.set_coupang_links(t, out, "황석어젓갈", [{"title": "황석어젓 1kg", "url": "https://link.coupang.com/a/j"}],
                                    **KW)
    sec = out2[out2.index("■ 2. 황석어젓갈"):out2.index("※ 출처")]
    assert bl.COUPANG_HEAD in sec and "https://link.coupang.com/a/j" in sec and "배송비" in sec   # 처음 넣는 절엔 결제 전 확인도
    assert t2 == "[광고] 제목"


def test_coupang_links_add_disclosure_and_ad_label_when_missing():
    bare = "도입\n\n■ 1. 절임배추\n- 데이터\n\n※ 출처"
    t, out = bl.set_coupang_links("절임배추 고르는 법", bare, "절임배추", [C1], **KW)
    assert t == "[광고] 절임배추 고르는 법" and out.startswith(COUPANG_DISCLOSURE + "\n" + SITE_OPS)
    assert out.rstrip().endswith(COUPANG_DISCLOSURE)


def test_coupang_links_refused_for_hold_and_bad_hosts():
    with pytest.raises(bl.LinkError, match="보류"):
        bl.set_coupang_links("t", COUPANG_BODY + "\n" + templates.HOLD_LINE["blog"], "절임배추", [C1], **KW)
    with pytest.raises(bl.LinkError):
        bl.set_coupang_links("t", COUPANG_BODY, "절임배추", [{"title": "x", "url": "https://evil.example/a"}], **KW)


# ── 관리자 경로 ───────────────────────────────────────────────────────
@pytest.fixture
def client(tmp_path, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.admin import auth, routes
    from app.services.trends import blog_autosave as bas, surge

    monkeypatch.setattr(auth, "expected_token", lambda: "test-token")
    monkeypatch.setattr(surge, "ROOT", tmp_path)
    folder = tmp_path / "var" / "blog_drafts"
    folder.mkdir(parents=True)
    (folder / "trend_2026-11-20_절임배추.txt").write_text(f"[광고] 제목\n\n태그: 절임배추\n\n{NAVER_BODY}\n", encoding="utf-8")
    (folder / "trend_2026-11-20_절임배추_쿠팡용.txt").write_text(f"[광고] 제목\n\n태그: 절임배추\n\n{COUPANG_BODY}\n",
                                                               encoding="utf-8")
    reg = tmp_path / "links.csv"
    reg.write_text("상품명,쇼핑커넥트 링크,키워드\n해남 절임배추 10kg,https://naver.me/aaa,절임배추\n", encoding="utf-8")
    monkeypatch.setenv("NAVER_CONNECT_REGISTRY_CSV", str(reg))
    monkeypatch.setenv("SC_BLOG_APPROVED", "1")
    monkeypatch.setenv("BLOG_AUTODRAFT", "1")
    monkeypatch.setattr(bas, "mcp_python", lambda env=None: reg)
    started = []

    def fake_start(path, **kw):
        started.append(kw)
        rec = {"status": "done", **(kw.get("extra") or {})}
        bas._write(path, rec)
        return rec

    monkeypatch.setattr(bas, "start", fake_start)
    monkeypatch.setattr(routes, "_title_similarity_cached", lambda *a, **k: {"status": "off"})
    monkeypatch.setattr(routes, "_coupang_links_now", lambda kws, limit=None: {k: [C1] for k in kws})
    app = FastAPI()
    app.include_router(routes.router)
    return TestClient(app), started


H = {"X-Access-Token": "test-token"}
NF = "var/blog_drafts/trend_2026-11-20_절임배추.txt"
CF = "var/blog_drafts/trend_2026-11-20_절임배추_쿠팡용.txt"


def test_link_options_and_apply_routes(client):
    c, _ = client
    o = c.get("/admin/api/trends/blog-draft/link-options", headers=H, params={"file": NF}).json()
    assert o["keywords"] == ["비상식량", "절임배추"] and o["connect_ok"] is True
    assert o["by_keyword"]["절임배추"][0]["url"] == "https://naver.me/aaa"
    r = c.post("/admin/api/trends/blog-draft/apply-links", headers=H, json={
        "variant": "naver", "title": "[광고] 제목", "body": NAVER_BODY, "keyword": "절임배추", "links": [L1]}).json()
    assert "https://naver.me/aaa" in r["body"]
    co = c.get("/admin/api/trends/blog-draft/link-options", headers=H, params={"file": CF}).json()
    assert co["keywords"] == ["절임배추", "황석어젓갈"] and co["by_keyword"]["절임배추"][0]["url"] == C1["url"]
    bad = c.post("/admin/api/trends/blog-draft/apply-links", headers=H, json={
        "variant": "coupang", "title": "t", "body": COUPANG_BODY, "keyword": "절임배추",
        "links": [{"title": "x", "url": "https://naver.me/aaa"}]})
    assert bad.status_code == 400
    assert c.post("/admin/api/trends/blog-draft/apply-links", json={
        "variant": "naver", "title": "t", "body": "b", "keyword": "k", "links": []}).status_code == 401


def test_naver_links_need_blog_approval(client, monkeypatch):
    c, _ = client
    monkeypatch.setenv("SC_BLOG_APPROVED", "0")
    r = c.post("/admin/api/trends/blog-draft/apply-links", headers=H, json={
        "variant": "naver", "title": "t", "body": NAVER_BODY, "keyword": "절임배추", "links": [L1]})
    assert r.status_code == 400 and "SC_BLOG_APPROVED" in r.json()["detail"]


def test_save_then_temp_save_does_not_duplicate(client):
    """'저장' = 네이버 임시저장: 같은 내용은 다시 넣지 않고, 고친 뒤 다시 넣을 때는 한 번 확인."""
    c, started = client
    r = c.post("/admin/api/trends/blog-draft/approve", headers=H, json={"file": CF})
    assert r.status_code == 200 and len(started) == 1 and started[0]["extra"]["content_hash"]
    same = c.post("/admin/api/trends/blog-draft/approve", headers=H, json={"file": CF}).json()
    assert same["skipped"] == "same_content" and len(started) == 1
    c.post("/admin/api/trends/blog-draft/save", headers=H, json={"file": CF, "title": "[광고] 제목", "tags": ["절임배추"],
                                                               "body": COUPANG_BODY + "\n고친 줄"})
    again = c.post("/admin/api/trends/blog-draft/approve", headers=H, json={"file": CF})
    assert again.status_code == 409 and again.json()["detail"]["need_confirm"] == "again" and len(started) == 1
    ok = c.post("/admin/api/trends/blog-draft/approve", headers=H, json={"file": CF, "confirm_again": True})
    assert ok.status_code == 200 and len(started) == 2
