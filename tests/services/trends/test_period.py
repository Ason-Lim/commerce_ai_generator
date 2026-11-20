"""급상승 키워드 기간 조회 (2026-11-19) — 파일만 쓰는 모의 시험.

GPT 검토의 '핵심 검증' 네 가지: 500위 진입·이탈, 누락일, 급등 후 하락, 과거 조회에 미래 자료가 섞이는 경우.
"""
from __future__ import annotations

import csv
import datetime as dt
import json

import pytest

from app.services.trends import period as P

D0 = dt.date(2026, 10, 1)


def day(i: int) -> str:
    return (D0 + dt.timedelta(days=i)).isoformat()


def write_day(folder, i: int, ranks: dict[str, int], fill_to: int = 500):
    """키워드→순위를 쓰고 나머지 순위는 가짜 키워드로 채운다 (하루 상위 500 모양)."""
    used = set(ranks.values())
    rows = sorted(ranks.items(), key=lambda x: x[1])
    for r in range(1, fill_to + 1):
        if r not in used:
            rows.append((f"채움{r}", r))
    rows.sort(key=lambda x: x[1])
    with open(folder / f"food_{day(i)}.csv", "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "rank", "keyword"])
        for kw, r in rows:
            w.writerow([day(i), r, kw])


@pytest.fixture
def ranks(tmp_path):
    """20일 (10-01~10-20), 10-07 파일 없음.
    대방어: 400 → 20 (10-10 정점) → 450   (급등 후 하락: 최대 개선폭 380, 시작→종료는 -50)
    귤:     10-05 부터만 등장(상위 500 진입), 300 → 30
    복숭아: 10-01~10-12 만 (500위 밖으로 이탈)
    쌀20kg: 내내 3위 (변화 없음)
    """
    folder = tmp_path / "rank"
    folder.mkdir()
    for i in range(20):
        if i == 6:                         # 10-07 누락
            continue
        d = D0 + dt.timedelta(days=i)
        r: dict[str, int] = {"쌀20kg": 3}
        if i <= 9:
            r["대방어"] = 400 - (380 * i // 9)          # 400 → 20
        else:
            r["대방어"] = 20 + (430 * (i - 9) // 10)     # 20 → 450
        if i >= 4:
            r["귤"] = 300 - (270 * (i - 4) // 15)        # 300 → 30
        if i <= 11:
            r["복숭아"] = 50 + i * 10
        write_day(folder, i, r)
    return folder


@pytest.fixture
def surge(tmp_path):
    """급상승 파일: 10-09·10-10 에 대방어, 10-25(미래) 에 귤."""
    folder = tmp_path / "surge"
    folder.mkdir()
    for d, items in {day(8): [("대방어", 3.1, "rising")], day(9): [("대방어", 4.2, "surging")],
                     day(24): [("귤", 5.0, "surging")]}.items():
        (folder / f"surge_{d}.json").write_text(json.dumps({
            "generated_at": d + "T08:00:00", "data_until": d,
            "items": [{"keyword": k, "ratio_peak": rp, "ratio_recent": rp, "status": st, "onset": day(5),
                       "series": [{"date": day(i), "value": 10.0} for i in range(10)], "blog": {"status": "none"},
                       "cause": {"cause": "시즌", "kind": "선물·시즌", "confidence": "mid", "public": True}, "cross": {"n": 1}} for k, rp, st in items]},
            ensure_ascii=False), encoding="utf-8")
    return folder


def row(table, kw):
    for g in table["groups"].values():
        for r in g:
            if r["keyword"] == kw:
                return r
    raise AssertionError(f"{kw} 없음")


def test_missing_day_is_excluded_not_filled(ranks):
    t = P.period_table(ranks, day(0), day(19))
    assert t["days"] == {"calendar": 20, "observed": 19, "missing": [day(6)]}
    r = row(t, "쌀20kg")
    assert r["days_listed"] == 19 and r["change"] == 0 and r["max_gain"] == 0
    assert all(d != day(6) for d, _ in r["series"])


def test_surge_then_fall_keeps_change_and_max_gain_apart(ranks, surge):
    t = P.period_table(ranks, day(0), day(19), surge_dir=surge)
    r = row(t, "대방어")
    assert r["group"] == "ranked"
    assert r["start"]["rank"] == 400 and r["end"]["rank"] == 450
    assert r["change"] == -50                      # 시작 대비 종료는 하락
    assert r["max_gain"] == 380 and r["best"] == {"date": day(9), "rank": 20}
    assert r["from_outside"] is False
    assert r["recent_direction"] == "down"
    assert r["surge"]["days"] == 2 and r["surge"]["first"] == day(8)
    assert r["surge"]["peak_ratio"] == 4.2 and r["surge"]["status_at_end"] == "surging"


def test_entering_top500_is_its_own_group_not_a_change(ranks):
    t = P.period_table(ranks, day(0), day(19))
    r = row(t, "귤")
    assert r["group"] == "entered" and r["change"] is None
    assert r["start"] == {"date": day(0), "rank": None} and r["end"]["rank"] == 30
    assert r["max_gain"] == 501 - 30 and r["from_outside"] is True
    assert r["days_listed"] == 15 and r["days_top100"] >= 1
    assert t["groups"]["entered"][0]["keyword"] == "귤"        # 진입 그룹은 종료 순위 좋은 순


def test_exiting_top500(ranks):
    r = row(P.period_table(ranks, day(0), day(19)), "복숭아")
    assert r["group"] == "exited" and r["end"]["rank"] is None and r["change"] is None
    assert r["days_listed"] == 11                               # 10-07 누락 빼고 10-01~10-12


def test_past_query_does_not_see_future_surge_files(ranks, surge):
    t = P.period_table(ranks, day(0), day(12), surge_dir=surge)
    assert row(t, "귤")["surge"]["days"] == 0                  # 10-25 파일은 종료일(10-13) 뒤
    assert t["surge_files"] == [day(8), day(9)]
    h = P.keyword_history("귤", ranks, end=day(12), surge_dir=surge)
    assert h["surge_days"] == [] and h["latest_surge"] is None
    h2 = P.keyword_history("귤", ranks, surge_dir=surge)        # end 없음 → 전부
    assert len(h2["surge_days"]) == 1 and h2["latest_surge"]["date"] == day(24)
    assert h2["latest_surge"]["cause"] == {"text": "시즌", "kind": "선물·시즌", "confidence": "mid", "label": None}


def test_default_sort_is_start_to_end_change(ranks):
    t = P.period_table(ranks, day(0), day(19))
    ranked = [r["keyword"] for r in t["groups"]["ranked"]]
    assert ranked.index("쌀20kg") < ranked.index("대방어")       # 0 > -50; 채움 키워드는 변화 0
    t2 = P.period_table(ranks, day(0), day(19), sort="max_gain")
    assert t2["groups"]["ranked"][0]["keyword"] == "대방어"


def test_history_series_marks_missing_out_and_ok(ranks):
    h = P.keyword_history("귤", ranks)
    status = {d: s for d, _, s in h["series"]}
    assert status[day(0)] == "out" and status[day(6)] == "missing" and status[day(19)] == "ok"
    assert h["best"]["rank"] == 30 and h["days_listed"] == 15
    kinds = [s["stage"] for s in h["stages"]]
    assert kinds[0] == "등장" and "정점" in kinds
    dates = [s["date"] for s in h["stages"]]
    assert dates == sorted(dates)                               # 등장 → 상승 → 정점 순서가 날짜와 맞음


def test_has_link_and_coverage(ranks, surge):
    t = P.period_table(ranks, day(0), day(19), surge_dir=surge, has_link=lambda k: k == "귤", with_series=False)
    assert row(t, "귤")["has_link"] is True and row(t, "대방어")["has_link"] is False
    assert "series" not in row(t, "귤")
    c = P.coverage(ranks, surge)
    assert c["rank"] == {"first": day(0), "last": day(19), "files": 19, "calendar_days": 20, "missing": 1}
    assert c["surge"]["first"] == day(8) and c["surge"]["files"] == 3


def test_resolve_period_and_source_note():
    assert P.resolve_period("1w", None, None, "2026-11-18") == ("2026-11-12", "2026-11-18")
    assert P.resolve_period(None, "2026-08-20", "2026-11-19", None) == ("2026-08-20", "2026-11-19")
    assert P.source_note("daily", None) is None
    assert "30일 묶음" in P.source_note("mixed", None)


def test_companions(ranks):
    t = P.period_table(ranks, day(0), day(19))
    c = P.companions("귤10kg", t)
    assert c and c[0]["keyword"] == "귤" and c[0]["related"] is True


def test_direction_short_and_flat():
    assert P.direction([10] * 5) == "short"
    assert P.direction([10] * 14) == "flat"
    assert P.direction([300] * 7 + [100] * 7) == "up"
    assert P.direction([100] * 7 + [None] * 7) == "down"
