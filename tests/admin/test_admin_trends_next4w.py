"""다음 4주 예보 (2026-11-24) — 합성 순위 자료, 외부 호출 없음."""

from __future__ import annotations

import csv
import datetime as dt

import pytest

from app.services.trends.forecast import next_weeks as nw

H = {"X-Access-Token": "test-token"}
AS_OF = dt.date(2026, 11, 1)


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


@pytest.fixture
def rank_dir(tmp_path, monkeypatch):
    rank = tmp_path / "rank"
    rank.mkdir()
    # 작년: 2025-10-20 ~ 2025-12-10 (빼빼로데이 2025-11-11 앞뒤)
    d = dt.date(2025, 10, 20)
    while d <= dt.date(2025, 12, 10):
        rows = {"쌀20kg": 1}
        if dt.date(2025, 11, 3) <= d <= dt.date(2025, 11, 11):
            rows["빼빼로"] = 3
        if dt.date(2025, 11, 24) <= d <= dt.date(2025, 11, 28):
            rows["절임배추"] = 40
        _write(rank, d, rows)
        d += dt.timedelta(days=1)
    # 올해: 기준일 앞 7일 — 쌀20kg 은 지금도 상위권
    d = AS_OF - dt.timedelta(days=6)
    while d <= AS_OF:
        _write(rank, d, {"쌀20kg": 1})
        d += dt.timedelta(days=1)
    monkeypatch.setenv("NAVER_DAILY_RANK_DIR", str(rank))
    monkeypatch.delenv("ADMIN_GUEST_TRENDS", raising=False)
    monkeypatch.delenv("NAVER_CONNECT_REGISTRY_CSV", raising=False)
    return rank


def _kw(week):
    return {it["keyword"]: it for it in week["items"]}


def test_candidates_by_week(rank_dir):
    out = nw.next_weeks(rank_dir, AS_OF, top_n=50)
    assert out["status"] == "ok" and len(out["weeks"]) == 4
    w1, w2, w3, w4 = out["weeks"]
    assert (w1["start"], w1["end"]) == ("2026-11-02", "2026-11-08")
    # 1주: 작년 같은 주(2025-11-03~09)에 3위 → 전년 같은 주 후보
    assert _kw(w1)["빼빼로"]["sources"][0] == "전년 같은 주" and _kw(w1)["빼빼로"]["last_year_best"] == 3
    # 지금 100위 안인 쌀20kg 은 빠진다
    assert "쌀20kg" not in _kw(w1) and out["excluded_top_now"] >= 1
    # 2주(11-09~15): 빼빼로데이 D-10 행사 근거가 붙는다
    assert any(e["event"] == "빼빼로데이" and e["d_day"] == 10 for e in w2["events"])
    assert "빼빼로데이 D-10" in _kw(w2)["빼빼로"]["sources"]
    # 4주(11-23~29): 작년 11-24~28 의 절임배추
    assert _kw(w4)["절임배추"]["last_year_best"] == 40
    assert all(w["last_year_coverage"] == 1.0 and w["warning"] is None for w in out["weeks"])


def test_no_future_reading_and_low_coverage(rank_dir):
    # 작년 자료가 없는 주는 경고
    out = nw.next_weeks(rank_dir, AS_OF, weeks=6)
    w6 = out["weeks"][5]  # 2026-12-07~13 ↔ 2025-12-08~14 (12-10 까지만 있음)
    assert w6["last_year_coverage"] < nw.LOW_COVERAGE and w6["warning"]
    # 기준일 최근 7일 파일이 없으면 no_data
    assert nw.next_weeks(rank_dir, dt.date(2026, 6, 1))["status"] == "no_data"


def test_api_needs_admin_and_returns(admin_client, rank_dir):
    assert admin_client.get("/admin/api/trends/forecast/next4w?as_of=2026-11-01").status_code == 401
    d = admin_client.get("/admin/api/trends/forecast/next4w?as_of=2026-11-01", headers=H).json()
    assert d["status"] == "ok" and d["as_of"] == "2026-11-01"
    item = _kw(d["weeks"][0])["빼빼로"]
    assert item["has_link"] in (False, None)
    assert "탐색기" not in " ".join(s for w in d["weeks"] for it in w["items"] for s in it["sources"])


def test_trends_page_has_section(admin_client):
    html = admin_client.get("/admin/trends", headers=H).text
    assert 'id="next4w"' in html and "/admin/api/trends/forecast/next4w" in html


def test_api_coupang_counts_only_when_asked(admin_client, rank_dir, monkeypatch):
    calls = []

    def fake(kws, **kw):
        calls.append(list(kws))
        return {k: ([{"url": "u1"}, {"url": "u2"}] if k == "빼빼로" else []) for k in kws}

    monkeypatch.setattr("app.admin.routes._coupang_links", fake)
    # 기본: 쿠팡을 부르지 않고 미확인(None)
    d = admin_client.get("/admin/api/trends/forecast/next4w?as_of=2026-11-01", headers=H).json()
    assert calls == [] and d["coupang_checked"] is False
    assert all(it["coupang"] is None for w in d["weeks"] for it in w["items"])
    # coupang=1: 한 번만, 주끼리 겹친 키워드는 한 번씩
    d = admin_client.get("/admin/api/trends/forecast/next4w?as_of=2026-11-01&coupang=1", headers=H).json()
    assert len(calls) == 1 and len(calls[0]) == len(set(calls[0])) and "빼빼로" in calls[0]
    assert d["coupang_checked"] is True
    assert _kw(d["weeks"][0])["빼빼로"]["coupang"] == 2 and _kw(d["weeks"][3])["절임배추"]["coupang"] == 0


def test_trends_page_has_coupang_button(admin_client):
    html = admin_client.get("/admin/trends", headers=H).text
    assert 'id="nw-cp"' in html and "<th>쿠팡 상품</th></tr></thead><tbody>${rows}" in html
