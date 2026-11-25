"""못 맞힌 이유 · 트렌드 변화 리포트 (2026-11-25) — 합성 자료, 외부 호출 없음."""

from __future__ import annotations

import csv
import datetime as dt

import pytest

from app.services.trends.forecast import backtest as bt
from app.services.trends.forecast import ledger
from app.services.trends.forecast import trend_shift as ts

H = {"X-Access-Token": "test-token"}
AS_OF = dt.date(2026, 3, 1)
ROWS: list[dict] = []  # 명절 없음 → 전년 기준 = 364일 전


def _write(rank, day: dt.date, rows: dict[str, int]):
    with open(rank / f"food_{day.isoformat()}.csv", "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "rank", "keyword"])
        used = set(rows.values())
        for kw, r in rows.items():
            w.writerow([day.isoformat(), r, kw])
        for r in range(1, 501):
            if r not in used:
                w.writerow([day.isoformat(), r, f"채움{r}"])


def _ly(d: dt.date) -> dict[str, int]:
    """작년(364일 전 기준 같은 28일 = 2025-03-03~03-30) 50위 안: 돌아옴·늦게·시점·식음 4개."""
    out = {"쌀20kg": 1}
    if dt.date(2025, 3, 3) <= d <= dt.date(2025, 3, 30):
        out |= {"딸기": 5, "냉이": 6, "달래": 7, "두바이쫀득쿠키": 8}
    return out


def _ty(d: dt.date) -> dict[str, int]:
    out = {"쌀20kg": 1}
    k = (d - AS_OF).days
    if 10 <= k <= 20:
        out["딸기"] = 9  # 7일+ 앞서 적중
    if 2 <= k <= 4:
        out["냉이"] = 30  # 늦게 적중 (7일 안)
    if 31 <= k <= 33:
        out["달래"] = 40  # 기간 뒤 14일 안 → 시점 어긋남
    if 5 <= k <= 6:
        out["신상과자"] = 20  # 처음 등장 (400일 동안 상위 500 밖)
    return out  # 두바이쫀득쿠키 = 안 옴


@pytest.fixture
def rank(tmp_path, monkeypatch):
    rank = tmp_path / "rank"
    rank.mkdir()
    d = dt.date(2025, 2, 20)
    while d <= dt.date(2025, 4, 20):
        _write(rank, d, _ly(d))
        d += dt.timedelta(days=1)
    d = AS_OF - dt.timedelta(days=6)
    while d <= AS_OF + dt.timedelta(days=45):
        _write(rank, d, _ty(d))
        d += dt.timedelta(days=1)
    monkeypatch.setenv("NAVER_DAILY_RANK_DIR", str(rank))
    monkeypatch.delenv("ADMIN_GUEST_TRENDS", raising=False)
    return rank


def test_classify_top(rank):
    days = bt._Days(rank)
    hits, _ = bt.truth(days, AS_OF, 28, {"쌀20kg"})
    near = bt.near_window(days, AS_OF, 28)
    br = bt.classify_top(["딸기", "냉이", "달래", "두바이쫀득쿠키"], hits, near)
    assert br == {"lead": ["딸기"], "late": ["냉이"], "timing": ["달래"], "gone": ["두바이쫀득쿠키"]}


def test_trend_shift_report(rank):
    r = ts.report(rank, AS_OF, rows=ROWS)
    assert r["status"] == "ok" and r["last_year_major"] == 4
    assert (r["came_back"], r["timing_off"], r["cooled"]) == (2, 1, 1)
    assert [x["keyword"] for x in r["cooled_items"]] == ["두바이쫀득쿠키"]
    assert r["cooled_items"][0]["this_year_best"] is None
    assert [x["keyword"] for x in r["new_items"]] == ["신상과자"] and r["new_items"][0]["first_date"] == "2026-03-06"
    # 기준일 뒤 42일 자료가 없으면 판정 대기
    assert ts.report(rank, AS_OF + dt.timedelta(days=7), rows=ROWS)["status"] == "pending"
    assert ts.default_as_of(rank) == AS_OF + dt.timedelta(days=45 - 42)


def test_backtest_miss_breakdown_sums_to_one(rank):
    res = bt.run(rank, AS_OF, AS_OF, methods=("last_year", "last_year_lunar"), rows=ROWS)
    b = res["metrics"]["last_year_lunar"][28]["miss_breakdown"]
    assert b == {"lead": 0.25, "late": 0.25, "timing": 0.25, "gone": 0.25}
    assert res["union"][28]["first_seen_share"] is not None


def test_ledger_reasons_and_first_seen(rank, tmp_path):
    root = tmp_path / "lg"
    ledger.save(rank, AS_OF, now=dt.datetime(2026, 3, 2, 9), root=root, rows=ROWS)
    res = ledger.evaluate(rank, root=root)
    assert res["graded_weeks"] == 1
    e = res["entries"][0]
    assert e["methods"]["last_year_lunar"]["reasons"] == {"lead": 1, "late": 1, "timing": 1, "gone": 1}
    assert e["methods"]["last_year_lunar"]["gone_keywords"] == ["두바이쫀득쿠키"]
    assert e["first_seen"] == 1 and res["first_seen"]["share"] is not None
    assert res["summary"]["last_year_lunar"]["reasons"]["gone"] == 0.25


def test_trend_shift_api(admin_client, rank):
    url = f"/admin/api/trends/forecast/trend-shift?as_of={AS_OF.isoformat()}&weeks=2"
    assert admin_client.get(url).status_code == 401
    d = admin_client.get(url, headers=H).json()
    assert d["status"] == "ok" and len(d["weekly"]) == 2 and d["latest_as_of"] == "2026-03-04"
    html = admin_client.get("/admin/trends", headers=H).text
    assert 'id="tshift"' in html and "/admin/api/trends/forecast/trend-shift" in html and "못 맞힌 이유" in html
