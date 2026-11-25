"""예측 백테스트 (2026-11-24) — Q1 모집단·정답, 기준선 3종 + 선행 곡선 탐색기, 정보 누출 통제."""

from __future__ import annotations

import datetime as dt

import pytest

from app.services.trends import period
from app.services.trends.forecast import backtest as bt

ROWS = [
    {"date": "2024-11-11", "end_date": "", "event": "빼빼로데이", "type": "fixed", "category": "기념일"},
    {"date": "2025-11-11", "end_date": "", "event": "빼빼로데이", "type": "fixed", "category": "기념일"},
]


def _ranks(d: dt.date) -> dict[str, int]:
    r = {"쌀": 5}  # 늘 상위권 — 모집단에서 빠짐
    for i in range(150):
        r[f"채움{i}"] = 300 + i
    if dt.date(d.year, 11, 1) <= d <= dt.date(d.year, 11, 12):
        r["빼빼로"] = 3  # 해마다 행사 전 10일
    else:
        r["빼빼로"] = 420
    if d == dt.date(2025, 10, 22):
        r["잠깐"] = 80  # 예측일 직전 주에만 100위 안 → 최근 상태 유지 기준선이 고름
    elif dt.date(2025, 10, 23) <= d <= dt.date(2025, 10, 30):
        r["잠깐"] = 200
    if d == dt.date(2025, 11, 5):
        r["깜짝"] = 40  # 아무도 못 맞힘(놓친 주요 상승)
    if dt.date(2025, 10, 29) <= d <= dt.date(2025, 10, 31):
        r["미래만"] = 10  # 예측일 뒤에만 — 예측 쪽에서 보이면 정보 누출
    return r


@pytest.fixture
def rank_dir(tmp_path):
    period._CACHE.clear()
    d = dt.date(2024, 9, 1)
    while d <= dt.date(2025, 12, 15):
        if d != dt.date(2025, 11, 7):  # 하루 누락
            rows = sorted(_ranks(d).items(), key=lambda kv: kv[1])
            text = "date,rank,keyword\n" + "".join(f"{d.isoformat()},{r},{k}\n" for k, r in rows)
            (tmp_path / f"food_{d.isoformat()}.csv").write_text(text, encoding="utf-8")
        d += dt.timedelta(days=1)
    return tmp_path


def test_population_and_truth(rank_dir):
    days = bt._Days(rank_dir)
    top_now, vocab = bt.population(days, dt.date(2025, 10, 25))
    assert top_now == {"쌀"} and "빼빼로" in vocab and "미래만" not in vocab  # 미래만은 예측일까지 한 번도 안 나옴
    hits, seen = bt.truth(days, dt.date(2025, 10, 25), 28, top_now)
    assert "쌀" not in hits  # 지금 100위 안이면 Q1 대상 아님(유지는 따로)
    assert (
        hits["빼빼로"]["first"] == 7 and hits["깜짝"]["best"] == 40 and seen == 27
    )  # 처음 보는 키워드도 정답에 셈 · 11-07 누락
    assert bt.truth(days, dt.date(2025, 12, 10), 28, top_now) is None  # 자료가 모자라면 판정 안 함


def test_methods_and_no_leak(rank_dir):
    days = bt._Days(rank_dir)
    as_of = dt.date(2025, 10, 25)
    pop, _ = bt.population(days, as_of)  # 지금 100위 안(빼야 할 것)
    kw = dict(rows=ROWS, rank_dir=rank_dir, cache={})
    assert set(bt.m_recent(days, as_of, 28, pop, **kw)) == {"잠깐"}
    assert set(bt.m_last_year(days, as_of, 28, pop, **kw)) == {"빼빼로"}
    assert set(bt.m_event_rel(days, as_of, 28, pop, **kw)) == {"빼빼로"}
    assert set(bt.m_event_rel(days, as_of, 7, pop, **kw)) == set()  # 행사가 기간 밖
    ex = bt.m_explorer(days, as_of, 28, pop, **kw)
    assert set(ex) == {"빼빼로"}
    for m in bt.METHODS:  # 예측일 뒤에만 있는 키워드는 어떤 방법도 고르지 못함
        assert "미래만" not in bt.FUNCS[m](days, as_of, 28, pop, **kw)


def test_run_aggregates_metrics(rank_dir):
    res = bt.run(rank_dir, dt.date(2025, 10, 18), dt.date(2025, 10, 25), step=7, rows=ROWS, horizons=(14, 28))
    assert res["dates"] == 2 and not res["skipped"]
    m28 = res["metrics"]
    ly = m28["last_year"][28]
    assert ly["hits"] == 2 and ly["precision"] == 1.0  # 두 예측일 모두 빼빼로 적중
    assert m28["recent"][28]["false_pos"] >= 1  # '잠깐'은 다시 안 들어옴
    assert m28["explorer"][28]["extra_hits"] == 0  # 기준선이 이미 맞힌 것은 '추가 적중' 아님
    assert ly["major_missed"] is not None and ly["major_missed"] > 0  # '깜짝'은 아무도 못 맞힘
    assert ly["lead_median"] is not None
    assert res["evaluated"] == ["2025-10-18", "2025-10-25"]
    assert m28["last_year"][28]["top20_lead7"] == 1.0  # 빼빼로 첫 진입이 7일 이상 뒤 (제출 1개 중 1개)
    assert m28["recent"][28]["top20_lead7"] == 0.0
    assert (
        m28["last_year"][28]["first_seen_true"] >= 1 and m28["last_year"][28]["recall_known"] is not None
    )  # '깜짝'은 처음 등장
    u = res["union"][28]
    assert u["major_first_seen"] >= 2 and u["major_missed_all"] is not None  # 합집합으로도 놓친 비율
    assert "explorer_repeat" in m28 and m28["explorer_repeat"][28]["n_pred"] == 0  # 판정 해가 하나뿐이라 '반복' 없음
    early = bt.run(rank_dir, dt.date(2024, 9, 1), dt.date(2024, 9, 1), rows=ROWS, horizons=(7,))
    assert early["dates"] == 1  # 자료 시작일 — 모집단은 그날 하루로
    none = bt.run(rank_dir, dt.date(2023, 1, 2), dt.date(2023, 1, 2), rows=ROWS, horizons=(7,))
    assert none["dates"] == 0 and none["skipped"][0]["why"].startswith("최근 7일")


def test_common_dates_and_q1p_and_min_share(rank_dir):
    # 2025-12-01 → 28일 기간 관측일 14일(자료 끝 12-15) < 17 → 판정 불가 → 그 예측일은 모든 기간에서 빠진다
    res = bt.run(rank_dir, dt.date(2025, 12, 1), dt.date(2025, 12, 1), rows=ROWS)
    assert res["dates"] == 0 and "28일" in res["skipped"][0]["why"]
    q = bt.run(rank_dir, dt.date(2025, 10, 25), dt.date(2025, 10, 25), rows=ROWS, horizons=(28,), question="q1p")
    assert (
        q["question"] == "q1p" and q["metrics"]["recent"][28]["n_pred"] == 0
    )  # 최근 100위 안이던 '잠깐'은 Q1′ 대상 아님
    strict = bt.run(rank_dir, dt.date(2025, 10, 25), dt.date(2025, 10, 25), rows=ROWS, horizons=(28,), min_share=1.0)
    assert strict["dates"] == 0  # 11-07 하루 누락 → 관측률 100% 기준이면 판정하지 않음
    for m in ("recent", "last_year"):  # 같은 예측일이면 기간이 달라도 기준선의 예측 수가 같다(최근 유지)
        r = bt.run(
            rank_dir, dt.date(2025, 10, 25), dt.date(2025, 10, 25), rows=ROWS, horizons=(7, 14, 28), methods=(m,)
        )
        if m == "recent":
            assert len({r["metrics"][m][h]["n_pred"] for h in (7, 14, 28)}) == 1


def test_ordering_experiments_keep_candidates():
    """실험 순서 바꾸기는 전년 기준 후보 집합을 그대로 두고(②) 순서만 바꾼다."""
    import datetime as dt

    from app.services.trends.forecast import backtest as bt

    class D:
        files = {}

        def get(self, d):
            if d == dt.date(2025, 3, 10):
                return {"A": 10, "B": 50}
            if d == dt.date(2024, 3, 11):
                return {"B": 30}
            return None

    days = D()
    as_of = dt.date(2026, 3, 1)
    base = bt.m_last_year_lunar(days, as_of, 28, set(), rows=[])
    two = bt.m_ly_two_years(days, as_of, 28, set(), rows=[])
    assert set(base) == set(two) == {"A", "B"}
    assert sorted(two, key=two.get) == ["B", "A"] and sorted(base, key=base.get) == ["A", "B"]
    assert set(bt.EXPERIMENTS) <= set(bt.FUNCS) and not set(bt.EXPERIMENTS) & set(bt.METHODS)
