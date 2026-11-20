"""선행 곡선 탐색기 — 합성 순위 파일로 반복 패턴 판정·곡선·예보 재료·as_of·행사군을 확인 (외부 호출 없음)."""
from __future__ import annotations

import csv
import datetime as dt

import pytest

from app.services.trends.forecast import calendar as cal
from app.services.trends.forecast import events as ev

EVENT = dt.date(2025, 11, 11)   # 빼빼로데이 2025


def write_day(rank_dir, day: dt.date, rows: dict[str, int]):
    with open(rank_dir / f"food_{day.isoformat()}.csv", "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "rank", "keyword"])
        used = set(rows.values())
        for kw, r in rows.items():
            w.writerow([day.isoformat(), r, kw])
        for r in range(1, 501):
            if r not in used:
                w.writerow([day.isoformat(), r, f"채움{r}"])


def pepero_rows(k: int) -> dict[str, int]:
    rows = {"쌀20kg": 1, "수능선물": 30}                       # 유지형 · 지속형
    if -10 <= k <= 3:
        rows["빼빼로"] = 2 if k <= 0 else 60                   # -10 진입, 당일까지 2위, +1~+3 60위, +4 부터 500위 밖
    elif -28 <= k < -10:
        rows["빼빼로"] = 150 + k                                # 100위 밖에서 올라오는 중
    if -14 <= k <= -3:
        rows["빼빼로만들기"] = 10 + abs(k + 8)                  # -8 에 10위, 양옆 11·12…
    return rows


@pytest.fixture
def rank_dir(tmp_path):
    d = tmp_path / "rank"
    d.mkdir()
    for event in (dt.date(2024, 11, 11), EVENT):
        for k in range(ev.REL_FROM, ev.REL_TO + 1):
            if k == -20:
                continue                                        # 누락일
            write_day(d, event + dt.timedelta(days=k), pepero_rows(k))
    return d


def test_calendar_dates_and_verification():
    assert cal.occurrences("빼빼로데이")[2026] == dt.date(2026, 11, 11)
    assert cal.occurrences("초복")[2025] == dt.date(2025, 7, 20)
    assert cal.occurrences("설날")[2026] == dt.date(2026, 2, 17)
    rows = cal.load()
    st = {(r["date"][:4], r["event"]): r["verification_status"] for r in rows}
    assert st[("2025", "초복")] == "official" and st[("2026", "초복")] == "computed"
    assert st[("2026", "김장 시즌")] == "approx" and st[("2026", "빼빼로데이")] == "fixed"


def test_states_out_vs_missing(rank_dir):
    r = ev.event_report("빼빼로데이", rank_dir, [2025], as_of=dt.date(2026, 1, 1))
    a = {k["keyword"]: k for k in r["keywords"]}["빼빼로"]["years"][2025]
    by = dict((k, v) for k, v in a["curve"])
    assert by[-20] is None and by[7] == "out" and by[0] == 2
    assert a["missing_days"] == 1 and a["out_days"] >= 11 and a["usable"]
    # 'out' 은 100위 밖으로 쓰여 이탈 판정에 들어간다 (집계에서 빠지는 건 None 만)
    assert a["bound"] and a["reasons"] == []


def test_repeat_needs_two_years(rank_dir):
    one = {k["keyword"]: k for k in ev.event_report("빼빼로데이", rank_dir, [2025], as_of=dt.date(2026, 1, 1))["keywords"]}
    assert one["빼빼로"]["grade"] == "후보" and one["빼빼로"]["judged_years"] == [2025]
    two = {k["keyword"]: k for k in ev.event_report("빼빼로데이", rank_dir, [2024, 2025], as_of=dt.date(2026, 1, 1))["keywords"]}
    assert two["빼빼로"]["grade"] == "반복" and two["빼빼로"]["bound_years"] == [2024, 2025]
    assert two["빼빼로"]["lead_days"] == 10
    assert "쌀20kg" not in two and "수능선물" not in two


def test_peak_runs(rank_dir):
    two = {k["keyword"]: k for k in ev.event_report("빼빼로데이", rank_dir, [2024, 2025], as_of=dt.date(2026, 1, 1))["keywords"]}
    a = two["빼빼로"]["years"][2025]
    assert a["peak_best"] == [-10, 0]                            # 2위가 연속된 날
    assert a["peak_top"] == [-10, 0]                             # 20위 안 연속 구간 (+1 은 60위라 끊김)
    m = two["빼빼로만들기"]["years"][2025]
    assert m["peak_best"] == [-8, -8] and m["peak_top"] == [-14, -3]
    assert two["빼빼로"]["peak_rel"] == [-10, 0]


def test_as_of_blocks_future(rank_dir):
    r = ev.event_report("빼빼로데이", rank_dir, [2024, 2025], as_of=dt.date(2025, 11, 20))
    assert [s["year"] for s in r["skipped"]] == [2025] and "기준일" in r["skipped"][0]["why"]
    assert list(r["years"]) == [2024]
    r2 = ev.event_report("빼빼로데이", rank_dir, [2025], as_of=dt.date(2025, 11, 5))
    assert r2["skipped"] and r2["keywords"] == []


def test_seed_keeps_non_bound_with_reasons(rank_dir):
    r = ev.event_report("빼빼로데이", rank_dir, [2025], seeds=["쌀20kg", "수능선물"], as_of=dt.date(2026, 1, 1))
    by = {k["keyword"]: k for k in r["keywords"]}
    assert by["쌀20kg"]["grade"] == "씨앗" and "기준 구간에 이미 100위 안(유지형)" in by["쌀20kg"]["years"][2025]["reasons"]
    assert "행사 뒤에도 100위 안(지속형)" in by["수능선물"]["years"][2025]["reasons"]


def test_insufficient_data_is_not_judged(tmp_path):
    d = tmp_path / "rank"
    d.mkdir()
    for k in range(-12, 1):                                     # 기준·이탈 구간 자료 없음
        write_day(d, EVENT + dt.timedelta(days=k), pepero_rows(k))
    r = ev.event_report("빼빼로데이", d, [2025], seeds=["빼빼로"], as_of=dt.date(2026, 1, 1))
    a = {k["keyword"]: k for k in r["keywords"]}["빼빼로"]
    assert a["grade"] == "씨앗" and not a["years"][2025]["usable"] and len(a["years"][2025]["lack"]) == 3


def test_group_bokna(tmp_path):
    d = tmp_path / "rank"
    d.mkdir()
    chobok, malbok = dt.date(2025, 7, 20), dt.date(2025, 8, 9)
    span = (malbok - chobok).days                                # 20
    for k in range(ev.REL_FROM, span + ev.REL_TO + 1):
        rows = {"쌀20kg": 1}
        if -14 <= k <= span + 1:
            rows["삼계탕"] = 30                                  # 초복 2주 전부터 말복 다음날까지 30위
        write_day(d, chobok + dt.timedelta(days=k), rows)
    single = {k["keyword"]: k for k in ev.event_report("초복", d, [2025], seeds=["삼계탕"], as_of=dt.date(2026, 1, 1))["keywords"]}
    assert not single["삼계탕"]["years"][2025]["bound"]           # 초복 하나만 보면 '지속형'으로 탈락
    group = {k["keyword"]: k for k in ev.event_report("복날(초복~말복)", d, [2025], as_of=dt.date(2026, 1, 1))["keywords"]}
    assert group["삼계탕"]["grade"] == "후보" and group["삼계탕"]["lead_days"] == 14


def test_forecast_from_report(rank_dir):
    r = ev.event_report("빼빼로데이", rank_dir, [2024, 2025], as_of=dt.date(2026, 1, 1))
    f = {x["keyword"]: x for x in ev.forecast_from_report(r, dt.date(2026, 11, 11))}
    assert f["빼빼로"]["expected_enter"] == "2026-11-01"
    assert f["빼빼로"]["expected_peak"] == ["2026-11-01", "2026-11-11"] and f["빼빼로"]["basis_years"] == [2024, 2025]


def test_upcoming():
    up = cal.upcoming(dt.date(2026, 10, 20), 35)
    assert next(u for u in up if u["event"] == "빼빼로데이")["d_day"] == 22
