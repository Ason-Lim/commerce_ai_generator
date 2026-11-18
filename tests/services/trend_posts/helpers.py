"""트렌드 글 테스트 공통 재료 — 리포트 항목 · 검색 결과 · 레시피 결과 · 시계."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.services.trend_posts.service import TrendPosts
from app.services.trend_posts.store import FilePostStore

T0 = datetime(2026, 11, 16, 3, 0, tzinfo=timezone.utc)


class Clock:
    def __init__(self, t=T0):
        self.t = t

    def __call__(self):
        return self.t

    def advance(self, **kw):
        self.t = self.t + timedelta(**kw)


def item(keyword="대방어", **extra):
    base = {"keyword": keyword, "status": "surging", "ratio_recent": 2.69, "ratio_peak": 3.21, "onset": "2026-11-03",
            "rank_trend": {"status": "ok", "first": {"date": "2026-10-30", "rank": 464},
                           "last": {"date": "2026-11-15", "rank": 82}},
            "blog": {"status": "ok", "posts": 46, "last7": 46, "clues": {"할인·행사": 1}},
            "google": {"status": "unavailable"}, "cross": {"n": 2, "of": 2},
            "cause": {"cause": "제철 정보 글이 늘어난 것으로 보여요", "kind": "불명", "public": True}}
    base.update(extra)
    return base


def report(*items, data_until="2026-11-15"):
    return {"data_until": data_until, "generated_at": "2026-11-16T01:00:00+09:00",
            "items": list(items) or [item()], "sources": {}}


def pick(title, url, price=29900, link_type="affiliate", section="picks", seen_at=None, rocket=True,
         image="https://ads-partners.coupang.com/image1/thumb.jpg"):
    return {"section": section, "product": {"key": title, "title": title, "image_url": image},
            "offer": {"platform": "쿠팡", "product_url": url, "price_krw": price, "link_type": link_type,
                      "affiliate_program": "쿠팡 파트너스" if link_type == "affiliate" else None,
                      "seen_at": seen_at, "rocket": rocket},
            "score": {"rank": 1}}


def search_result():
    return {"items": [
        pick("대방어회 500g", "https://link.coupang.com/a/aaa"),
        pick("다른 몰 대방어", "https://shop.example/b", link_type="direct"),       # 쿠팡 아님 → 빠짐
        pick("대방어 필렛 1kg", "https://link.coupang.com/a/ccc", price=45900),
        pick("후보 밖 상품", "https://link.coupang.com/a/ddd", section="others"),   # picks 가 아님 → 빠짐
    ]}


def recipe_result(title="대방어 회덮밥", level="source"):
    return {"items": [{"recipe_id": "EPIS:1", "title": title, "source_name": "농식품정보누리(EPIS)",
                       "source_level": level, "provider": "epis", "ingredients": [{"name": "대방어"}, {"name": "밥"}],
                       "steps": [{"text": "1"}, {"text": "2"}, {"text": "3"}], "content_hash": "x", "citation": "c"}]}


def service(tmp_path, clock=None):
    return TrendPosts(FilePostStore(tmp_path / "posts"), clock or Clock())


def approved(svc, keyword="대방어", products=True):
    post, _ = svc.create_from_surge(report(item(keyword)), keyword,
                                    find_products=(lambda k: search_result()) if products else None)
    svc.submit(post.id)
    return svc.approve(post.id)
