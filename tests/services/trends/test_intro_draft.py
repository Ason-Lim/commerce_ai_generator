"""2026-11-21 '상품 소개형' 블로그 초안 — 급상승 리포트에 없는 키워드(예: 사과)도 검색량 데이터 없이 초안을 만든다.

* 모두 소개형: 트렌드 리포트 제목·데이터랩 도입·검색량 출처 줄이 없고, 소개형 도입·출처 줄이 있다. 숫자를 지어내지 않는다.
* 섞인 글: 리포트 키워드는 데이터 줄 그대로, 소개형 키워드는 '이번 급상승 리포트에 없는 키워드' 한 줄.
* 관리자 경로: 리포트가 없어도 키워드를 주면 소개형으로, 운영 메모에 소개형 표시, 파일 이름 trend_<오늘>_소개_….
"""
from __future__ import annotations

import pytest

from app.services.trends import surge as S

REPORT = {"generated_at": "2026-11-20T10:00:00+09:00", "data_until": "2026-11-20", "items": [
    {"keyword": "방어필렛", "status": "surging", "ratio_recent": 3.2, "ratio_peak": 4.0, "peak_day": "11/19",
     "onset": "11/12", "rank_trend": {"status": "ok", "first": {"date": "11/06", "rank": 300},
                                     "last": {"date": "11/20", "rank": 120}},
     "blog": {"status": "ok", "posts": 10, "last7": 6, "clues": {}}, "google": {"status": "none"}}]}
LINKS = {"사과": [{"title": "경북 부사 사과 3kg", "url": "https://link.coupang.com/a/s1", "rocket": True}]}


def test_all_intro_draft_has_no_search_data():
    for variant in ("naver", "coupang"):
        d = S.blog_draft({"items": [], "data_until": "2026-11-21"}, ["사과"], intro=["사과"], variant=variant,
                         coupang=LINKS, connect_ok=False)
        body = d["body"]
        assert d["intro"] == ["사과"] and d["keywords"] == ["사과"]
        assert "데이터랩" not in body and "검색량이" not in body and "배예요" not in body and "순위:" not in body
        assert S.INTRO_LEAD.format(k="사과를") in body and S.INTRO_SOURCE_LINE in body
        assert "트렌드 리포트" not in d["title"] and "트렌드리포트" not in d["tags"]
        assert "■ 1. 사과" in body and S.INTRO_ITEM_LINE not in body
    coupang = S.blog_draft({"items": [], "data_until": "2026-11-21"}, ["사과"], intro=["사과"], variant="coupang",
                           coupang=LINKS)
    assert coupang["title"].startswith("[광고] ") and "- 경북 부사 사과 3kg: https://link.coupang.com/a/s1" in coupang["body"]
    assert coupang["body"].rstrip().endswith(S.COUPANG_DISCLOSURE)


def test_mixed_draft_keeps_report_data_and_marks_intro_keyword():
    d = S.blog_draft(REPORT, ["방어필렛", "사과"], intro=["사과"], variant="coupang", coupang=LINKS)
    body = d["body"]
    assert d["keywords"] == ["방어필렛", "사과"] and d["intro"] == ["사과"]
    first, second = body.split("■ 2. 사과")
    assert "약 3.2배" in first and "300위 → 11/20 120위" in first
    assert S.INTRO_ITEM_LINE in second and "배예요" not in second
    assert "데이터랩" in body                                         # 리포트 키워드가 있으면 데이터 출처 줄 유지


def test_report_draft_unchanged_without_intro():
    d = S.blog_draft(REPORT, ["방어필렛"], variant="naver", connect_ok=False)
    assert d["intro"] == [] and S.INTRO_ITEM_LINE not in d["body"] and S.INTRO_SOURCE_LINE not in d["body"]
    assert d["body"].startswith("네이버 데이터랩")


fastapi = pytest.importorskip("fastapi")


@pytest.fixture
def client(tmp_path, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.admin import auth, routes

    monkeypatch.setattr(auth, "expected_token", lambda: "test-token")
    monkeypatch.setattr(S, "ROOT", tmp_path)
    monkeypatch.delenv("NAVER_CONNECT_REGISTRY_CSV", raising=False)
    monkeypatch.setattr(routes, "_coupang_links", lambda kws, channel=None, limit=None: {k: LINKS.get(k, []) for k in kws})
    monkeypatch.setattr(routes, "_blog_serp", lambda kws: {})
    monkeypatch.setattr(routes, "_blog_recipes", lambda *a, **k: {})
    app = FastAPI()
    app.include_router(routes.router)
    return TestClient(app), tmp_path


H = {"X-Access-Token": "test-token"}


def test_route_makes_intro_draft_without_any_report(client, monkeypatch):
    c, root = client
    monkeypatch.setattr(S, "load", lambda date=None, env=None: None)
    out = c.post("/admin/api/trends/blog-draft", headers=H, json={"keywords": ["사과"]})
    assert out.status_code == 200, out.text
    d = out.json()
    assert d["intro"] == ["사과"]
    coupang = d["drafts"]["coupang"]
    assert "_소개_사과" in coupang["file"]
    text = (root / coupang["file"]).read_text(encoding="utf-8")
    assert "상품 소개형(리포트에 없는 키워드 — 검색량 데이터 없이): 사과" in text
    assert "데이터랩" not in text.split("─" * 30, 1)[1]
    assert c.post("/admin/api/trends/blog-draft", headers=H, json={}).status_code == 404   # 리포트·키워드 둘 다 없음


def test_route_mixes_report_and_intro_keywords(client, monkeypatch):
    c, _ = client
    monkeypatch.setattr(S, "load", lambda date=None, env=None: REPORT)
    d = c.post("/admin/api/trends/blog-draft", headers=H, json={"keywords": ["방어필렛", "사과"]}).json()
    assert d["intro"] == ["사과"] and d["drafts"]["coupang"]["keywords"] == ["방어필렛", "사과"]
    assert "trend_2026-11-20_" in d["drafts"]["coupang"]["file"]
