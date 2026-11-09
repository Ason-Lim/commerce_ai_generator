"""급상승 리포트의 유튜브 근거 · 구글 예시 데이터 차단 (2026-11-06).

유튜브: 최근 7일 영상 수와 한 달 전 같은 7일(36~29일 전, 데이터랩 '평소' 구간 안)을 견준다.
처음 만든 '최근 2주 vs 그 전 2주'는 실제 실행에서 인기 식품 대부분이 두 기간 모두 검색 상한(50개)을 채워 비교할 수 없었다.
"""
from __future__ import annotations

from app.services.trends import surge as S

END = "2026-11-05"


def vids(n, word="빼빼로", day="2026-11-03"):
    return [{"title": f"{word} 만들기 {i}", "link": f"https://www.youtube.com/watch?v=v{i:05d}", "date": day}
            for i in range(n)]


def windows(recent, base, word="빼빼로"):
    calls = []

    def search(kw, days, before_days=None):
        calls.append((days, before_days))
        return vids(recent, word) if before_days is None else vids(base, word, "2026-10-03")
    return search, calls


def test_youtube_compares_the_last_week_with_the_same_week_a_month_ago():
    search, calls = windows(12, 3)
    yt = S.youtube_evidence("빼빼로", search, END)
    assert calls == [(7, None), (36, 29)]
    assert yt["status"] == "ok" and (yt["recent"], yt["previous"]) == (12, 3) and yt["rising"] is True
    assert len(yt["titles"]) == 3 and set(yt["titles"][0]) == {"title", "link", "date", "source"}   # 제목·링크·날짜만
    assert S.youtube_evidence("빼빼로", windows(6, 5)[0], END)["rising"] is False


def test_a_full_recent_week_still_counts_as_rising_against_a_small_month_ago():
    yt = S.youtube_evidence("빼빼로", windows(50, 8)[0], END)
    assert (yt["recent"], yt["recent_more"], yt["previous"], yt["previous_more"]) == (50, True, 8, False)
    assert yt["rising"] is True


def test_both_weeks_full_cannot_be_compared_and_is_left_out_of_the_cross_check():
    yt = S.youtube_evidence("빼빼로", windows(50, 50)[0], END)
    assert yt["saturated"] and yt["rising"] is None
    cross = S.cross_check({"rising": True}, {"improved": True}, {"status": "unavailable"}, yt)
    assert cross["of"] == 2 and "유튜브 영상 증가" not in cross["parts"]       # 모름 ≠ 늘지 않음


def test_videos_that_do_not_name_the_food_are_not_counted():
    def search(kw, days, before_days=None):
        return [{"title": "오늘의 브이로그", "link": "x", "date": "2026-11-03"}] * 9
    yt = S.youtube_evidence("빼빼로", search, END)
    assert yt["status"] == "none" and yt["recent"] == 0 and yt["rising"] is False


def test_youtube_failure_is_reported_not_counted():
    def boom(kw, days, before_days=None):
        raise RuntimeError("quota")
    yt = S.youtube_evidence("빼빼로", boom, END)
    assert yt["status"] == "error"
    cross = S.cross_check({"rising": True}, {"improved": False}, {"status": "unavailable"}, yt)
    assert cross["of"] == 2 and "유튜브 영상 증가" not in cross["parts"]       # 보지 못한 곳은 분모에 넣지 않는다


def test_cross_check_counts_youtube_only_when_connected():
    yt = S.youtube_evidence("빼빼로", windows(12, 3)[0], END)
    c = S.cross_check({"rising": True}, {"improved": True}, {"status": "unavailable"}, yt)
    assert c == {"n": 3, "of": 3, "parts": {"블로그 글 증가": True, "식품 순위 상승": True, "유튜브 영상 증가": True}}


def test_add_youtube_to_an_existing_report_only_touches_the_top_items():
    report = {"data_until": END, "items": [
        {"keyword": k, "blog": {"rising": False}, "rank_trend": {"improved": True}, "google": {"status": "none"},
         "cross": {"n": 1, "of": 3, "parts": {}}} for k in ("빼빼로", "과메기", "귤")]}
    asked = []

    def search(kw, days, before_days=None):
        asked.append(kw)
        return vids(12, kw) if before_days is None else vids(3, kw, "2026-10-03")
    S.add_youtube(report, search, top=2)
    assert asked == ["빼빼로", "빼빼로", "과메기", "과메기"] and "youtube" not in report["items"][2]
    assert report["items"][0]["cross"]["n"] == 2 and report["items"][0]["cross"]["of"] == 4


def test_google_csv_is_used_only_when_verified():
    """trends_v4 CSV 는 수집기의 예시(stub) 데이터 — GOOGLE_TRENDS_VERIFIED=1 없이는 근거로 쓰지 않는다."""
    assert S.google_verified({}) is False and S.google_verified({"GOOGLE_TRENDS_VERIFIED": "1"}) is True
    report = {"data_until": END, "generated_at": "2026-11-06T10:00:00+09:00", "items": [{
        "keyword": "빼빼로", "status": "surging", "ratio_recent": 13.2, "onset": "2026-10-25", "series": [],
        "blog": {"status": "ok", "clues": {}}, "rank_trend": {"status": "ok"}, "google": {"status": "none"},
        "cross": {"n": 2, "of": 3, "parts": {"블로그 글 증가": True, "식품 순위 상승": True, "구글 트렌드": False}},
        "cause": None, "ask": "빼빼로 추천해줘"}]}
    view = S.public_view(report)
    assert view["sources"]["google"] is False and "구글 트렌드" not in view["items"][0]["cross"]["parts"]
    assert view["items"][0]["cross"]["of"] == 2
    view = S.public_view(dict(report, google_verified=True))
    assert view["sources"]["google"] is True and view["items"][0]["cross"]["of"] == 3


def test_a_capped_count_only_decides_when_it_is_certain():
    """실제 실행(11/06): 과메기 최근 7일 50개 이상 · 한 달 전 32개 → 2배 미만으로 '증가 아님'이라 하면 틀릴 수 있다."""
    assert S.youtube_rising(50, True, 32, False) is None        # 최근은 50보다 많을 수 있음 → 모름
    assert S.youtube_rising(48, True, 4, False) is True         # 하한만으로도 2배 이상
    assert S.youtube_rising(7, False, 50, True) is False        # 한 달 전이 50 이상, 최근 7 → 늘지 않음
    assert S.youtube_rising(49, True, 43, True) is None
    assert S.youtube_rising(14, False, 3, False) is True and S.youtube_rising(7, False, 4, False) is False
