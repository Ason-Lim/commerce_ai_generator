"""가격 레이어 — 시세 시계열·현재 위치·전년 전망·매수 시점·상대일 곡선 (2026-11-19 밤). 합성 자료, 외부 호출 없음."""
from __future__ import annotations

import csv
import datetime as dt
import json

import pytest

from app.services.trends.forecast import prices as pr

AS_OF = dt.date(2026, 11, 19)


def _daily(start: dt.date, end: dt.date, fn) -> list[dict]:
    rows, d = [], start
    while d <= end:
        if d.weekday() < 5:                               # KAMIS 는 평일만
            rows.append({"date": d, "item": "배추", "kind": "가을", "rank": "상품", "unit": "1포기", "price": fn(d), "src": "history"})
        d += dt.timedelta(days=1)
    return rows


def kimjang_price(d: dt.date) -> int:
    """11월 초 정점(6,000) → 11월 말 3,000 으로 내리는 김장 패턴, 평소 3,500."""
    if d.month == 10 and d.day >= 20 or d.month == 11 and d.day <= 10:
        return 6000
    if d.month == 11:
        return 6000 - (d.day - 10) * 150
    return 3500


@pytest.fixture
def rows():
    return _daily(dt.date(2024, 1, 2), AS_OF, kimjang_price)


def test_series_median_and_as_of(rows):
    rows2 = rows + [{"date": AS_OF, "item": "배추", "kind": "가을", "rank": "중품", "unit": "1포기", "price": 1000, "src": "history"},
                    {"date": AS_OF + dt.timedelta(days=5), "item": "배추", "kind": "가을", "rank": "상품", "unit": "1포기", "price": 1, "src": "history"}]
    s = pr.series(rows2, "배추", "가을", as_of=AS_OF)
    assert max(s) == AS_OF                                  # as_of 뒤는 안 읽음
    assert s[AS_OF] == int((kimjang_price(AS_OF) + 1000) / 2)   # 같은 날 두 등급 → 중앙값
    assert pr.series(rows2, "배추", "봄") == {}              # 품종 필터
    assert pr.series(rows2, "무") == {}


def test_position_pct_and_vs(rows):
    s = pr.series(rows, "배추", "가을")
    p = pr.position(s, AS_OF)
    assert p["date"] == "2026-11-19" and p["price"] == kimjang_price(AS_OF)
    assert p["n_52w"] >= 240 and 0 < p["pct_52w"] < 1
    assert p["min_52w"] == min(s[d] for d in s if (AS_OF - d).days < 364) and p["max_52w"] == 6000
    assert p["vs_1m"] == round((kimjang_price(AS_OF) / kimjang_price(dt.date(2026, 10, 19)) - 1) * 100)
    assert p["vs_1y"] == 0                                  # 작년 같은 날과 같은 값
    assert pr.position(s, dt.date(2023, 1, 1)) is None


def test_outlook_per_year_and_waiting_verdict(rows):
    s = pr.series(rows, "배추", "가을")
    ol = pr.outlook(s, AS_OF)
    assert set(ol[28]["years"]) == {2024, 2025} and ol[28]["n"] == 2
    assert ol[28]["median"] < 0.9                           # 11-19 → 12-17: 4,650 → 3,500
    assert ol[28]["agree"] is True
    t = pr.buy_timing(pr.position(s, AS_OF), ol)
    assert t["verdict"] == "기다리기" and t["best_h"] in (14, 28) and t["expected_28d"] < -5
    assert any("가장 낮을" in r for r in t["reasons"]) and any("전년 같은 시기" in r for r in t["reasons"])


def test_now_verdict_when_cheap_and_rising(rows):
    s = pr.series(rows, "배추", "가을")
    as_of = dt.date(2026, 10, 10)                           # 평소 3,500 → 10-20 부터 6,000
    t = pr.buy_timing(pr.position(s, as_of), pr.outlook(s, as_of))
    assert t["verdict"] == "지금" and t["expected_28d"] > 5


def test_hold_when_sparse_or_one_year():
    rows = _daily(dt.date(2026, 10, 1), AS_OF, kimjang_price)          # 올해만 → 전년 비교 불가
    s = pr.series(rows, "배추", "가을")
    t = pr.buy_timing(pr.position(s, AS_OF), pr.outlook(s, AS_OF))
    assert t["verdict"] == "보류" and any("전년 비교 가능 해 0" in r for r in t["reasons"])
    assert pr.buy_timing(None, {})["verdict"] == "보류"
    rows1 = _daily(dt.date(2025, 1, 2), AS_OF, kimjang_price)          # 전년 1개 → MIN_YEARS 미달 + 참고 문구
    t1 = pr.buy_timing(pr.position(pr.series(rows1, "배추"), AS_OF), pr.outlook(pr.series(rows1, "배추"), AS_OF))
    assert t1["verdict"] == "보류" and any(r.startswith("참고:") for r in t1["reasons"])


def test_relative_curve_ratio_base(rows):
    s = pr.series(rows, "배추", "가을")
    anchors = {2024: dt.date(2024, 11, 15), 2025: dt.date(2025, 11, 15), 2026: dt.date(2026, 11, 15)}
    c = pr.relative_curve(s, anchors, as_of=AS_OF)
    assert c[2024]["base"] == 3500 and c[2024]["points"][0][0] == -42
    peak = max(p[2] for p in c[2024]["points"] if p[2])
    assert abs(peak - 6000 / 3500) < 0.01
    assert max(p[0] for p in c[2026]["points"]) <= 4         # as_of(11-19) 뒤는 없음


def test_daily_points_loader(tmp_path):
    doc = {"price": [{"product_cls_code": "01", "productName": "계란/XL30구(일반란)", "unit": "30구", "lastest_day": "2026-11-17",
                      "dpr1": "7,243", "dpr2": "7,243", "dpr3": "6,664", "dpr4": "6,000"},
                     {"product_cls_code": "02", "productName": "계란/XL30구(일반란)", "unit": "30구", "lastest_day": "2026-11-17", "dpr1": "5,000"}]}
    (tmp_path / "daily_2026-11-18.json").write_text(json.dumps(doc), encoding="utf-8")
    pts = pr.load_daily_points(tmp_path)
    assert {p["date"] for p in pts} == {dt.date(2026, 11, 17), dt.date(2026, 11, 16), dt.date(2026, 10, 17), dt.date(2025, 11, 17)}
    assert all(p["item"] == "계란" and p["kind"] == "XL30구(일반란)" for p in pts)     # 도매(02)는 뺌
    s = pr.series(pts, "계란", "XL30구(일반란)")
    assert pr.position(s, AS_OF)["vs_1y"] == round((7243 / 6000 - 1) * 100)
    assert pr.buy_timing(pr.position(s, AS_OF), pr.outlook(s, AS_OF))["verdict"] == "보류"   # 성긴 자료


def test_watchlist_drivers_consistent():
    wl, drv = pr.watchlist(), pr.drivers()
    assert wl and drv
    for r in wl:
        for d in r["drivers"].split(";"):
            assert not d or d in drv, (r["item"], d)
        assert r["overseas"] in ("no", "quote")
    assert all(d["status"] == "가설" for d in drv.values())
    assert any(r["item"] in ("올리브유", "커피 원두") and r["overseas"] == "quote" for r in wl)


def test_active_drivers_latest_signal_before_as_of():
    row = {"drivers": "kimjang;fx"}
    drv = {"kimjang": {"driver": "김장", "direction": "up", "status": "가설", "lag_days_min": "-21", "lag_days_max": "21", "signal_source": "달력"},
           "fx": {"driver": "환율", "direction": "up", "status": "가설", "lag_days_min": "30", "lag_days_max": "90", "signal_source": "한은"}}
    sig = [{"date": "2026-11-01", "driver": "kimjang", "state": "off", "note": ""},
           {"date": "2026-11-15", "driver": "kimjang", "state": "on", "note": "시즌"},
           {"date": "2026-12-01", "driver": "kimjang", "state": "off", "note": "미래"}]
    act = pr.active_drivers(row, drv, sig, AS_OF)
    assert [a["id"] for a in act] == ["kimjang", "fx"]
    assert act[0]["state"] == "on" and act[0]["signal_date"] == "2026-11-15"
    assert act[1]["state"] == "unknown"


def test_summary_orders_by_verdict_and_handles_no_kamis(rows, tmp_path, monkeypatch):
    wl = [{"item": "배추", "group": "김장", "kamis_item": "배추", "kamis_kind": "가을", "drivers": "kimjang", "overseas": "no"},
          {"item": "올리브유", "group": "수입식품", "kamis_item": "", "kamis_kind": "", "drivers": "", "overseas": "quote"}]
    out = pr.summary(AS_OF, rows=rows, wl=wl)
    assert [o["item"] for o in out] == ["배추", "올리브유"]
    assert out[0]["verdict"] == "기다리기" and out[1]["verdict"] == "보류" and out[1]["kamis_item"] is None


def test_item_report_with_calendar_anchor(rows):
    row = {"item": "배추", "group": "김장", "kamis_item": "배추", "kamis_kind": "가을", "anchor_event": "김장 시즌",
           "drivers": "", "overseas": "no", "keywords": "배추;절임배추"}
    cal = [{"date": "2024-11-15", "event": "김장 시즌"}, {"date": "2025-11-15", "event": "김장 시즌"}]
    rep = pr.item_report(row, rows, AS_OF, drv={}, sig=[], cal_rows=cal)
    assert rep["curves"]["event"] == "김장 시즌" and set(rep["curves"]["years"]) == {2024, 2025}
    assert rep["timing"]["verdict"] == "기다리기" and rep["keywords"] == ["배추", "절임배추"]
    assert rep["series_1y"][-1][0] == "2026-11-19"
