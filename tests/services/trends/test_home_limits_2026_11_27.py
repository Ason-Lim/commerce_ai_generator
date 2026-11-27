"""2026-11-27 사용자: 쿠팡 랭킹 102개(→ API 최대 100), 함께 보면 좋은 상품 개수 늘리기(30 → 60)."""
import datetime as dt

from app.services.trends import coupang_best as cb, home_rankings as hr, together


def test_limits():
    assert hr.LIMITS["home"]["coupang"] == 100 and together.LIMITS["home"] == 60


def test_ranked_returns_up_to_100_from_one_snapshot():
    snap = {"items": [{"rank": i, "product_id": str(i), "title": f"상품{i}", "price": 1000, "image": None, "url": None,
                       "rocket": False, "free_shipping": False} for i in range(1, 101)], "fetched_at": "2026-11-27T15:00:00+09:00"}
    now = dt.datetime(2026, 11, 27, 15, 0, tzinfo=dt.timezone(dt.timedelta(hours=9)))
    assert len(cb.ranked(now.date(), now, hr.LIMITS["home"]["coupang"], snap=snap)["items"]) == 100
