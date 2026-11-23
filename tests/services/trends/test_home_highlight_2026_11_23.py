"""홈 카테고리 '이번 주 주목' 대표 상품 (2026-11-23 저녁 B) — 저장 없음, 주목 키워드만, 이름에 키워드가 든 식품만."""
from __future__ import annotations

from app.services.trends import highlight as hl

ITEMS = [{"product_name": "곶감 말리는 건조망 3단", "product_url": "https://link.coupang.com/a/x1", "image_url": "https://image.coupangcdn.com/1.jpg",
          "price": 9900, "category_name": "생활용품"},
         {"product_name": "상주 반건시 곶감 1kg", "product_url": "https://link.coupang.com/a/x2", "image_url": "https://evil.example/2.jpg",
          "price": 19900, "is_rocket": True},
         {"product_name": "곶감 선물세트", "product_url": "javascript:alert(1)", "image_url": None, "price": 1}]


def test_pick_first_food_with_keyword_and_safe_links():
    calls = []
    got = hl.pick("곶감", search=lambda kw, n: calls.append(kw) or ITEMS)
    assert calls == ["곶감"]
    assert got["title"] == "상주 반건시 곶감 1kg"                     # 식품 분류가 아닌 '생활용품'은 건너뜀
    assert got["image"] is None                                         # 쿠팡 그림 주소가 아니면 쓰지 않음
    assert got["go_url"].startswith("/home/hgo/") and "link.coupang" not in got["go_url"]


def test_target_within_ttl_then_search_fallback(monkeypatch):
    got = hl.pick("곶감", search=lambda kw, n: ITEMS[1:2])
    key = got["go_url"].rsplit("/", 1)[1]
    assert hl.target(key) == ("https://link.coupang.com/a/x2", True)
    monkeypatch.setattr(hl, "TTL", -1)
    url, aff = hl.target(key)
    assert aff is False and url.startswith("https://www.coupang.com/np/search?q=")
    assert hl.target("ffffffffffff") == ("/", False)


def test_no_match_returns_none():
    assert hl.pick("과메기", search=lambda kw, n: ITEMS) is None


def test_route_only_accepts_current_highlight_keywords(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.api import trend_routes
    from app.services.trends import home_rankings as hr

    monkeypatch.setattr(hr, "build", lambda view="home", **k: {"categories": {"tabs": [{"tag": "gift", "highlight": {"keyword": "곶감"}}]}})
    monkeypatch.setattr(hl, "pick", lambda kw, search=None: {"keyword": kw, "title": "곶감", "go_url": "/home/hgo/0123456789ab"})
    app = FastAPI()
    app.include_router(trend_routes.router)
    c = TestClient(app)
    assert c.get("/api/home/highlight", params={"kw": "노트북"}).status_code == 404       # 아무 검색어나 쿠팡에 보내지 않음
    r = c.get("/api/home/highlight", params={"kw": "곶감"})
    assert r.status_code == 200 and r.json()["item"]["title"] == "곶감" and r.headers["cache-control"] == "no-store"
    assert c.get("/home/hgo/zz", follow_redirects=False).headers["location"] == "/"
