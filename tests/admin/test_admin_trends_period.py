"""급상승 키워드 기간 조회 API (2026-11-19) — 파일 폴더만 임시로 만든다 (외부 호출 없음)."""
from __future__ import annotations

import csv
import datetime as dt
import json

import pytest

H = {"X-Access-Token": "test-token"}
D0 = dt.date(2026, 10, 1)


def day(i):
    return (D0 + dt.timedelta(days=i)).isoformat()


@pytest.fixture
def dirs(tmp_path, monkeypatch):
    rank = tmp_path / "rank"
    rank.mkdir()
    for i in range(14):
        if i == 5:
            continue                                    # 누락일
        with open(rank / f"food_{day(i)}.csv", "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["date", "rank", "keyword"])
            rows = {"쌀20kg": 1, "대방어": 300 - i * 20}
            if i >= 8:
                rows["귤"] = 100 - i                   # 10-09 부터 상위 500 진입
            used = set(rows.values())
            for kw, r in rows.items():
                w.writerow([day(i), r, kw])
            for r in range(1, 501):
                if r not in used:
                    w.writerow([day(i), r, f"채움{r}"])
    surge = tmp_path / "surge"
    surge.mkdir()
    (surge / f"surge_{day(10)}.json").write_text(json.dumps({
        "generated_at": day(10) + "T08:00:00", "data_until": day(10),
        "items": [{"keyword": "대방어", "ratio_peak": 3.3, "ratio_recent": 3.0, "status": "surging", "onset": day(7),
                   "series": [{"date": day(k), "value": 1.0} for k in range(11)], "blog": {"status": "none"},
                   "cause": {"summary": "제철", "public": True}, "cross": {"n": 1}}]}, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setenv("NAVER_DAILY_RANK_DIR", str(rank))
    monkeypatch.setenv("TREND_SURGE_DIR", str(surge))
    monkeypatch.delenv("ADMIN_GUEST_TRENDS", raising=False)
    monkeypatch.delenv("NAVER_CONNECT_REGISTRY_CSV", raising=False)
    return rank, surge


def test_needs_admin(admin_client, dirs):
    assert admin_client.get("/admin/api/trends/period").status_code == 401
    assert admin_client.get("/admin/api/trends/keyword?keyword=귤").status_code == 401


def test_period_default_is_one_month_ending_at_last_file(admin_client, dirs):
    d = admin_client.get("/admin/api/trends/period", headers=H).json()
    assert d["ok"] and d["end"] == day(13) and d["source"]["kind"] == "daily" and d["source"]["note"] is None
    assert d["coverage"]["rank"]["files"] == 13 and d["coverage"]["rank"]["missing"] == 1
    assert d["days"]["observed"] == 13 and day(5) in d["days"]["missing"]
    ranked = {r["keyword"]: r for r in d["groups"]["ranked"]}
    assert ranked["대방어"]["change"] == 260 and ranked["대방어"]["surge"]["days"] == 1
    assert ranked["대방어"]["surge"]["status_at_end"] == "surging"
    assert d["groups"]["ranked"][0]["keyword"] == "대방어"          # 기본 정렬 = 시작→종료 개선폭
    entered = {r["keyword"] for r in d["groups"]["entered"]}
    assert "귤" in entered
    assert d["groups"]["ranked"][0]["has_link"] in (False, None)
    assert len(d["groups"]["ranked"][0]["series"]) == 13


def test_period_presets_and_custom_range(admin_client, dirs):
    w = admin_client.get("/admin/api/trends/period?preset=1w", headers=H).json()
    assert w["start"] == day(7) and w["end"] == day(13) and w["days"]["calendar"] == 7
    c = admin_client.get(f"/admin/api/trends/period?start={day(0)}&end={day(9)}&sort=max_gain&limit=5", headers=H).json()
    assert c["start"] == day(0) and c["end"] == day(9) and c["sort"] == "max_gain"
    assert all(len(v) <= 5 for v in c["groups"].values())
    assert c["surge_files"] == []                                # 10-11 파일은 종료일 뒤 → 안 읽음
    assert admin_client.get("/admin/api/trends/period?start=2020-01-01&end=2026-10-10", headers=H).status_code == 400
    assert admin_client.get("/admin/api/trends/period?preset=2y", headers=H).status_code == 422


def test_keyword_history(admin_client, dirs):
    h = admin_client.get(f"/admin/api/trends/keyword?keyword=귤&start={day(0)}&end={day(13)}", headers=H).json()
    assert h["keyword"] == "귤" and h["days_listed"] == 6
    status = {d: s for d, _, s in h["series"]}
    assert status[day(0)] == "out" and status[day(5)] == "missing" and status[day(13)] == "ok"
    assert h["latest_surge"] is None and h["period"] == {"start": day(0), "end": day(13)}
    assert any(c["keyword"] == "대방어" for c in h["companions"])
    d = admin_client.get("/admin/api/trends/keyword?keyword=대방어", headers=H).json()
    assert d["latest_surge"]["date"] == day(10) and d["surge_days"][0]["ratio_peak"] == 3.3


def test_falls_back_to_mixed_folder_with_note(admin_client, dirs, monkeypatch):
    rank, _ = dirs
    monkeypatch.delenv("NAVER_DAILY_RANK_DIR")
    monkeypatch.setenv("NAVER_DAILY_DIR", str(rank))
    d = admin_client.get("/admin/api/trends/period?preset=1w", headers=H).json()
    assert d["ok"] and d["source"]["kind"] == "mixed" and "30일 묶음" in d["source"]["note"]


def test_no_folder(admin_client, dirs, monkeypatch):
    monkeypatch.delenv("NAVER_DAILY_RANK_DIR")
    monkeypatch.delenv("NAVER_DAILY_DIR", raising=False)
    d = admin_client.get("/admin/api/trends/period", headers=H).json()
    assert d["ok"] is False and d["source"]["kind"] == "none"
    assert admin_client.get("/admin/api/trends/keyword?keyword=귤", headers=H).status_code == 404


def test_guest_can_read(admin_client, dirs, monkeypatch):
    import app.admin.routes as routes

    monkeypatch.setattr(routes, "guest_trends_on", lambda: True)      # .env 의 ADMIN_GUEST_TRENDS=1 과 같음
    d = admin_client.get("/admin/api/trends/period?preset=1w").json()
    assert d["ok"] and d["guest"] is True
