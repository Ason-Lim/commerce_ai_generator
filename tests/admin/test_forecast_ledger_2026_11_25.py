"""전년 기준(설·추석 맞춤) · 탐색기 근거 열 · 예보 장부 (2026-11-25) — 합성 자료, 외부 호출 없음."""

from __future__ import annotations

import csv
import datetime as dt
import json

import pytest

from app.services.trends.forecast import backtest as bt
from app.services.trends.forecast import ledger
from app.services.trends.forecast import next_weeks as nw

H = {"X-Access-Token": "test-token"}
ROWS = [
    {"date": "2025-01-29", "event": "설날", "type": "lunar"},
    {"date": "2026-02-17", "event": "설날", "type": "lunar"},
    {"date": "2025-10-06", "event": "추석", "type": "lunar"},
    {"date": "2026-09-25", "event": "추석", "type": "lunar"},
]


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


def _span(rank, a: dt.date, b: dt.date, fn):
    d = a
    while d <= b:
        _write(rank, d, fn(d))
        d += dt.timedelta(days=1)


def test_year_back_lunar_and_normal():
    sh = bt.lunar_shifts(ROWS)
    # 설날 D-10 → 작년 설날 D-10
    src, name = bt.year_back(dt.date(2026, 2, 7), sh)
    assert name == "설날" and src == dt.date(2025, 1, 19)
    # 추석 당일 → 작년 추석 당일
    assert bt.year_back(dt.date(2026, 9, 25), sh) == (dt.date(2025, 10, 6), "추석")
    # 명절 구간 밖은 364일 전
    assert bt.year_back(dt.date(2026, 6, 1), sh) == (dt.date(2026, 6, 1) - dt.timedelta(days=364), None)


@pytest.fixture
def lunar_dir(tmp_path, monkeypatch):
    """작년 설날(2025-01-29) D-14~D-1 에 '한과세트' 3위. 364일 전 같은 주(2025-01-28~02-11 무렵)엔 없음."""
    rank = tmp_path / "rank"
    rank.mkdir()
    _span(
        rank,
        dt.date(2025, 1, 1),
        dt.date(2025, 3, 10),
        lambda d: {"쌀20kg": 1} | ({"한과세트": 3} if dt.date(2025, 1, 15) <= d <= dt.date(2025, 1, 28) else {}),
    )
    _span(rank, dt.date(2026, 1, 25), dt.date(2026, 2, 1), lambda d: {"쌀20kg": 1})
    monkeypatch.setenv("NAVER_DAILY_RANK_DIR", str(rank))
    monkeypatch.delenv("ADMIN_GUEST_TRENDS", raising=False)
    monkeypatch.delenv("NAVER_CONNECT_REGISTRY_CSV", raising=False)
    return rank


def test_backtest_lunar_baseline_beats_plain_shift(lunar_dir):
    days = bt._Days(lunar_dir)
    as_of = dt.date(2026, 2, 1)  # 설날 D-16
    top_now = {"쌀20kg"}
    plain = bt.m_last_year(days, as_of, 14, top_now)
    lunar = bt.m_last_year_lunar(days, as_of, 14, top_now, rows=ROWS)
    assert "한과세트" not in plain and lunar.get("한과세트") == 3
    assert "last_year_lunar" in bt.BASELINES and "last_year_lunar" in bt.METHODS


def test_next_weeks_tags_lunar_and_explorer_fields(lunar_dir):
    out = nw.next_weeks(lunar_dir, dt.date(2026, 2, 1), weeks=2, rows=ROWS)
    w1 = out["weeks"][0]
    assert w1["baseline_tag"] == "전년 설날 맞춤"
    it = {i["keyword"]: i for i in w1["items"]}["한과세트"]
    assert it["sources"][0] == "전년 설날 맞춤"
    assert "explorer_repeat" in it and it["explorer_repeat"] is None  # 반복 판정할 해가 2개 안 됨 → 표시 없음
    assert w1["explorer_only"] == []


def test_ledger_save_once_live_and_grade(tmp_path, lunar_dir):
    root = tmp_path / "ledger"
    as_of = dt.date(2025, 1, 10)
    r = ledger.save(lunar_dir, as_of, now=dt.datetime(2025, 1, 11, 9), root=root, rows=ROWS)
    assert r["status"] == "saved" and r["live"] is True
    rec = json.loads((root / "2025-01-10.json").read_text(encoding="utf-8"))
    assert "한과세트" not in rec["top_now"] and set(rec["methods"]) == set(ledger.METHODS)
    # 한 번 적은 예보는 고치지 않는다
    assert ledger.save(lunar_dir, as_of, root=root, rows=ROWS)["status"] == "exists"
    # 뒤늦게 만든 예보는 live=False → 기본 성적에서 빠짐
    late = ledger.save(lunar_dir, dt.date(2025, 1, 3), now=dt.datetime(2025, 2, 1), root=root, rows=ROWS)
    assert late["live"] is False
    res = ledger.evaluate(lunar_dir, root=root)
    by = {e["as_of"]: e for e in res["entries"]}
    assert by["2025-01-10"]["status"] == "graded" and by["2025-01-10"]["n_true"] >= 1
    assert res["graded_weeks"] == 1 and res["retro_excluded"] == 1
    assert (
        res["baseline"] == "last_year_lunar" and "vs_baseline_pp" in res["summary"]["recent"]
    )  # 2024 자료 없음 → 비교값 None
    assert res["target"]["review_after_weeks"] == 12 and res["target"]["weeks_left"] == 11
    assert ledger.evaluate(lunar_dir, root=root, include_retro=True)["graded_weeks"] == 2


def test_ledger_pending_before_28_days(tmp_path, lunar_dir):
    root = tmp_path / "ledger"
    ledger.save(lunar_dir, dt.date(2026, 2, 1), now=dt.datetime(2026, 2, 1, 9), root=root, rows=ROWS)
    res = ledger.evaluate(lunar_dir, root=root)
    assert res["entries"][0]["status"] == "pending" and res["pending"] == 1


def test_ledger_routes(admin_client, lunar_dir, tmp_path, monkeypatch):
    monkeypatch.setenv("FORECAST_LEDGER_DIR", str(tmp_path / "lg"))
    assert admin_client.get("/admin/api/trends/forecast/ledger").status_code == 401
    d = admin_client.get("/admin/api/trends/forecast/ledger", headers=H).json()
    assert d["graded_weeks"] == 0 and d["metric"].startswith("28일")
    assert admin_client.post("/admin/api/trends/forecast/ledger/save").status_code in (401, 403)
    r = admin_client.post("/admin/api/trends/forecast/ledger/save", headers=H).json()
    assert r["status"] in ("saved", "no_data") and r["as_of"] == (dt.date.today() - dt.timedelta(days=1)).isoformat()


def test_trends_page_has_ledger(admin_client):
    html = admin_client.get("/admin/trends", headers=H).text
    assert 'id="lg-box"' in html and "/admin/api/trends/forecast/ledger" in html and "탐색기(반복만)" in html
