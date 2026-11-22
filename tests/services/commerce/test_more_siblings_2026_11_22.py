"""2026-11-22 23:0x 사용자 PDF: '캡슐레이션효소 추천해줘' → 상품 1개.
쿠팡 검색 API 가 효소류 검색어에 한 상품(옵션 10개)만 준다 → 끝말이 같은 다른 순위 키워드로 더 찾는다."""
from app.services.commerce import coupang_gaps

RANKS = {"캡슐레이션효소": 54, "카무트효소": 98, "효소": 300, "여주발효효소": 410, "명가효소": 5,
         "막걸리효소": 6, "사과": 7}


def test_siblings_share_the_head_word():
    assert coupang_gaps.sibling_queries("캡슐레이션효소", RANKS) == ["카무트효소", "여주발효효소"]
    assert coupang_gaps.sibling_queries("캡슐레이션효소", RANKS, limit=3) == ["카무트효소", "여주발효효소", "효소"]


def test_no_shop_or_alcohol_and_only_single_korean_words():
    sib = coupang_gaps.sibling_queries("캡슐레이션효소", RANKS, limit=5)
    assert "명가효소" not in sib and "막걸리효소" not in sib
    assert coupang_gaps.sibling_queries("효소 30포", RANKS) == []
    assert coupang_gaps.sibling_queries("사과", RANKS) == []          # 2자 — 끝말 나누지 않음
    assert coupang_gaps.sibling_queries("수박", {}) == []


def test_search_more_uses_siblings(monkeypatch):
    from app.services.commerce import search

    monkeypatch.setattr(coupang_gaps, "ranked_keywords", lambda: RANKS)
    assert search.coupang_gaps_siblings("캡슐레이션효소") == ["카무트효소", "여주발효효소"]
