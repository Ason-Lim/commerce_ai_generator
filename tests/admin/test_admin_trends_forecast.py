"""행사 선행 곡선 API (2026-11-19 밤) — 빼빼로데이 2025 합성 자료 (외부 호출 없음)."""

from __future__ import annotations

import csv
import datetime as dt

import pytest

H = {"X-Access-Token": "test-token"}
EVENT = dt.date(2025, 11, 11)


@pytest.fixture
def rank_dir(tmp_path, monkeypatch):
    rank = tmp_path / "rank"
    rank.mkdir()
    for k in range(-35, 15):
        day = (EVENT + dt.timedelta(days=k)).isoformat()
        rows = {"쌀20kg": 1}
        if -10 <= k <= 3:
            rows["빼빼로"] = 2 if k <= 0 else 60
        with open(rank / f"food_{day}.csv", "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["date", "rank", "keyword"])
            used = set(rows.values())
            for kw, r in rows.items():
                w.writerow([day, r, kw])
            for r in range(1, 501):
                if r not in used:
                    w.writerow([day, r, f"채움{r}"])
    monkeypatch.setenv("NAVER_DAILY_RANK_DIR", str(rank))
    monkeypatch.delenv("ADMIN_GUEST_TRENDS", raising=False)
    monkeypatch.delenv("NAVER_CONNECT_REGISTRY_CSV", raising=False)
    return rank


def test_needs_admin(admin_client, rank_dir):
    assert admin_client.get("/admin/api/trends/forecast/events").status_code == 401
    assert admin_client.get("/admin/api/trends/forecast/event?event=빼빼로데이").status_code == 401


def test_events_list(admin_client, rank_dir):
    d = admin_client.get("/admin/api/trends/forecast/events", headers=H).json()
    assert d["ok"] and d["data_years"] == [2025]
    names = {e["event"] for e in d["events"]}
    assert {"설날", "추석", "초복", "수능", "빼빼로데이", "동지", "복날(초복~말복)"} <= names
    pepero = next(e for e in d["events"] if e["event"] == "빼빼로데이")
    assert pepero["dates"]["2026"] == "2026-11-11" and pepero["dates"]["2025"] == "2025-11-11"


def test_event_curve_and_forecast(admin_client, rank_dir):
    d = admin_client.get(
        "/admin/api/trends/forecast/event?event=빼빼로데이&years=2025&seeds=쌀20kg&as_of=2026-01-01", headers=H
    ).json()
    assert d["years"]["2025"]["start"] == "2025-11-11" and d["years"]["2025"]["coverage"]["observed"] == 50
    by = {k["keyword"]: k for k in d["keywords"]}
    assert by["빼빼로"]["grade"] == "후보" and by["빼빼로"]["lead_days"] == 10  # 한 해만 → 후보 (반복은 2개 해부터)
    assert by["쌀20kg"]["grade"] == "씨앗" and "유지형" in " ".join(by["쌀20kg"]["years"]["2025"]["reasons"])
    assert by["빼빼로"]["coupang"] is None and by["빼빼로"]["has_link"] in (False, None)
    assert d["next"]["date"] == "2026-11-11" and d["as_of"] == "2026-01-01"
    f = {x["keyword"]: x for x in d["next"]["forecast"]}
    assert "빼빼로" in f and "쌀20kg" not in f
    assert admin_client.get("/admin/api/trends/forecast/event?event=없는행사", headers=H).status_code == 404


def test_as_of_hides_unfinished_year(admin_client, rank_dir):
    d = admin_client.get("/admin/api/trends/forecast/event?event=빼빼로데이&as_of=2025-11-15", headers=H).json()
    assert d["years"] == {} and d["skipped"] and "기준일" in d["skipped"][-1]["why"]


def test_backtest_api(admin_client, rank_dir):
    """2026-11-24 예측 백테스트 — 기준선 3종(+탐색기) 합산 지표, 관리자만, 기간 제한."""
    url = "/admin/api/trends/forecast/backtest?start=2025-10-20&end=2025-10-27&step=7"
    assert admin_client.get(url).status_code == 401
    d = admin_client.get(url, headers=H).json()
    assert d["dates"] == 2 and set(d["metrics"]) == {"recent", "last_year", "event_rel", "explorer"}
    x = d["metrics"]["recent"]["28"] if "28" in d["metrics"]["recent"] else d["metrics"]["recent"][28]
    assert {"precision", "recall", "top20_precision", "lead_median", "major_missed", "false_pos"} <= set(x)
    base = admin_client.get(url + "&explorer=0", headers=H).json()
    assert set(base["metrics"]) == {"recent", "last_year", "event_rel"}
    bad = admin_client.get("/admin/api/trends/forecast/backtest?start=2024-01-01&end=2025-12-31", headers=H)
    assert bad.status_code == 400
