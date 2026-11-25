"""행사별 리포트카드 (2026-11-25) — 합성 자료, 외부 호출 없음."""

from __future__ import annotations

import csv
import datetime as dt

import pytest

from app.services.trends.forecast import report_card as rc

H = {"X-Access-Token": "test-token"}
ROWS = [
    {"date": "2025-11-11", "event": "빼빼로데이", "type": "fixed", "category": "기념일"},
    {"date": "2026-11-11", "event": "빼빼로데이", "type": "fixed", "category": "기념일"},
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


@pytest.fixture
def rank(tmp_path, monkeypatch):
    """2025: 빼빼로 행사 10일 전부터 3위. 2026: 예보일(10-14) 뒤 12일째(10-26) 빼빼로 5위 진입(선행 적중), 신상초코 처음 등장."""
    rank = tmp_path / "rank"
    rank.mkdir()
    d = dt.date(2025, 10, 1)
    while d <= dt.date(2026, 11, 30):
        rows = {"쌀20kg": 1}
        if dt.date(2025, 11, 1) <= d <= dt.date(2025, 11, 11):
            rows["빼빼로"] = 3
        if dt.date(2026, 10, 26) <= d <= dt.date(2026, 11, 11):
            rows["빼빼로"] = 5
        if dt.date(2026, 11, 5) <= d <= dt.date(2026, 11, 8):
            rows["신상초코"] = 30
        _write(rank, d, rows)
        d += dt.timedelta(days=1)
    monkeypatch.setenv("NAVER_DAILY_RANK_DIR", str(rank))
    monkeypatch.delenv("ADMIN_GUEST_TRENDS", raising=False)
    return rank


def test_report_card_2026(rank):
    c = rc.report_card(rank, "빼빼로데이", 2026, rows=ROWS)
    assert c["status"] == "ok" and c["as_of"] == "2026-10-14" and c["window"] == ["2026-10-15", "2026-11-11"]
    assert c["methods"]["last_year_lunar"]["lead"] == 1 and c["methods"]["last_year_lunar"]["lead_keywords"] == [
        "빼빼로"
    ]
    by = {r["keyword"]: r for r in c["rises"]}
    assert "전년 기준(비교 기준)" in by["빼빼로"]["predicted_by"] and by["빼빼로"]["d_day"] == 16
    assert by["신상초코"]["predicted_by"] == [] and by["신상초코"]["candidate_rank"] == {}
    assert by["신상초코"]["history"] == "없음"  # 과거 400일 중 371일(92%) 자료 → 판정, 처음 보는 키워드
    assert c["missed"] == 1 and c["major_rise"] == 2


def test_summary_and_missing(rank):
    s = rc.summary(rank, "빼빼로데이", rows=ROWS)
    assert [x["year"] for x in s] == [2025, 2026]
    assert (
        s[0]["status"] == "ok" and s[0]["lead_rate"]["last_year_lunar"] is None
    )  # 2024 자료 없음 → 전년 기준 후보 없음
    assert s[1]["status"] == "ok" and s[1]["lead_rate"]["last_year_lunar"] == 1.0
    assert rc.report_card(rank, "빼빼로데이", 2030, rows=ROWS)["status"] == "no_event"


def test_route(admin_client, rank):
    assert admin_client.get("/admin/api/trends/forecast/report-card?event=빼빼로데이").status_code == 401
    d = admin_client.get("/admin/api/trends/forecast/report-card?event=빼빼로데이&year=2026", headers=H).json()
    assert d["summary"] and d["card"]["event"] == "빼빼로데이"
    html = admin_client.get("/admin/trends", headers=H).text
    assert 'id="rcard"' in html and "/admin/api/trends/forecast/report-card" in html
