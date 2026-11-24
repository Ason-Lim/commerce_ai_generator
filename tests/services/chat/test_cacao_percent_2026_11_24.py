"""2026-11-24 (사용자 PDF): '카카오 70% 이상 다크초콜릿 중에 쓴맛 덜한 거' — 후보 1개(85%)만 나왔다.

함량 조건은 검색어에서 떼고 상품명 표기 함량으로 거른다 (사용자 결정: 거르기에 씀).
보여 주는 순서는 함량 높은 순이 기본, '함량 낮은 순으로' 칩으로 다시 본다.
"""

from __future__ import annotations

import pytest

from app.services.chat import followup as fu
from app.services.chat.service import ChatService
from app.services.commerce import cacao
from app.services.recipe_chat.service import RecipeChat
from tests.services.chat.test_evoo_retry_2026_11_22 import ByQuery, _cp, md

ASK = "카카오 70% 이상 다크초콜릿 중에 쓴맛 덜한 거 추천해 줘"


@pytest.mark.parametrize(
    ("text", "lo", "hi", "rest"),
    [
        (ASK, 70, None, "다크초콜릿 중에 쓴맛 덜한 거 추천해 줘"),
        ("카카오 함량 80% 이하 초콜릿", None, 80, "초콜릿"),
        ("70~80% 다크초콜릿", 70, 80, "다크초콜릿"),
        ("카카오70%이상 초콜릿 추천", 70, None, "초콜릿 추천"),
        ("카카오 80% 이상 추천해 줘", 80, None, "다크초콜릿 추천해 줘"),
    ],
)
def test_parse_and_strip(text, lo, hi, rest):
    c = cacao.parse_condition(text)
    assert (c["min"], c["max"]) == (lo, hi)
    assert cacao.strip_condition(text, c) == rest


@pytest.mark.parametrize("text", ["다크초콜릿 추천", "두유 70% 이상", "올리브유 100% 엑스트라버진"])
def test_no_condition(text):
    assert cacao.parse_condition(text) is None


@pytest.mark.parametrize(
    ("title", "pct"),
    [
        ("티르마 미니 다크 초콜릿 85% 카카오", 85),
        ("부샤드 나폴리탄 다크초콜릿 72%", 72),
        ("롯데웰푸드 드림카카오 82%, 86g, 2개", 82),
        ("다크초콜릿 100% 무가당 비알칼리 카카오매스", 100),
        ("노브랜드 다크 초콜렛 100g", None),
    ],
)
def test_title_percent(title, pct):
    assert cacao.title_percent(title) == pct


def _shop():
    return ByQuery(
        {
            "다크초콜릿": [
                _cp("파베글라스 루미에르 컴파운드 코인 코팅 다크초콜릿, 1kg, 1개", 11920, 1),
                _cp("부샤드 나폴리탄 다크초콜릿 72%", 9340, 2),
                _cp("티르마 미니 다크 초콜릿 85% 카카오", 12900, 3),
                _cp("롯데웰푸드 드림카카오 82%, 86g, 2개", 7080, 4),
                _cp("파베글라스 벨벳 다크 65% 커버춰 리얼 초콜릿, 400g, 1개", 13800, 5),
                _cp("린트엑셀런스 다크 90% 초콜릿, 100g, 2개", 14280, 6),
            ]
        }
    )


def _titles(res):
    return [i["title"] for b in res["blocks"] if b["type"] == "product_list" for i in b["data"]["items"]]


def test_chat_filters_by_percent_high_first(sqlite_db):
    shop = _shop()
    svc = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message=ASK)
    assert shop.calls[0] == "다크초콜릿"  # 함량 조건은 검색어에서 뗌
    shown = _titles(res)
    assert shown[:4] == [
        "린트엑셀런스 다크 90% 초콜릿, 100g, 2개",
        "티르마 미니 다크 초콜릿 85% 카카오",
        "롯데웰푸드 드림카카오 82%, 86g, 2개",
        "부샤드 나폴리탄 다크초콜릿 72%",
    ]
    assert not any("65%" in t or "컴파운드" in t for t in shown)  # 조건 밖·표기 없음은 뺌
    text = md(res)
    assert "함량이 높은 순" in text and "낮은 순으로 다시 보여 드릴까요?" in text
    first = next(i for b in res["blocks"] if b["type"] == "product_list" for i in b["data"]["items"])
    assert "카카오 90% (상품명 표기)" in str(first.get("why"))
    assert "함량 표기가 없는 상품 1개" in text and "조건 밖인 상품 1개" in text
    chips = [c for b in res["blocks"] if b["type"] == "chips" for c in b["data"]["items"]]
    assert "함량 낮은 순으로" in chips

    low = svc.handle(res["session_id"], message="함량 낮은 순으로")
    lows = _titles(low)
    assert lows.index("부샤드 나폴리탄 다크초콜릿 72%") < lows.index("린트엑셀런스 다크 90% 초콜릿, 100g, 2개")
    notes = " ".join(b["data"].get("note") or "" for b in low["blocks"] if b["type"] == "product_list")
    assert "카카오 함량 낮은 순" in md(low) and "추천 순서가 아니에요" in notes
    assert "함량 높은 순으로" in [c for b in low["blocks"] if b["type"] == "chips" for c in b["data"]["items"]]


def test_followup_parse_cacao_sort():
    assert fu.parse("함량 낮은 순으로") == {"kind": "sort", "by": "cacao_low"}
    assert fu.parse("함량 높은 순") == {"kind": "sort", "by": "cacao_high"}
    assert fu.parse("가격 낮은 순으로") == {"kind": "sort", "by": "price"}


def test_single_candidate_head_line(sqlite_db):
    shop = ByQuery(
        {"다크초콜릿": [_cp("티르마 미니 다크 초콜릿 85% 카카오", 12900, 1), _cp("노브랜드 다크 초콜렛 100g", 2880, 2)]}
    )
    svc = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message=ASK)
    text = md(res)
    assert "조건에 맞는 후보가 1개뿐이에요" in text and "견줘서 1개를 골랐어요" not in text
    assert "최저가" not in text


def test_coupang_fetch_time_becomes_card_seen_at(monkeypatch):
    """2026-11-24: 쿠팡 검색 시각을 상품에 붙이고(캐시로 다시 줘도 처음 시각), 카드의 확인 시각으로 쓴다."""
    from app.services import coupang_api
    from app.services.chat.service import item_to_card

    monkeypatch.setattr(coupang_api, "is_coupang_available", lambda: True)
    monkeypatch.setattr(coupang_api, "_SEARCH_CACHE", {})
    monkeypatch.setattr(
        coupang_api,
        "_search_coupang_products",
        lambda k, n: [{"title": "부샤드 나폴리탄 다크초콜릿 72%", "price": 9340}],
    )
    first = coupang_api._search_coupang_products_cached("다크초콜릿", 10)
    again = coupang_api._search_coupang_products_cached("다크초콜릿", 10)
    assert first[0]["fetched_at"] and again[0]["fetched_at"] == first[0]["fetched_at"]
    card = item_to_card(dict(first[0], product_name="부샤드 나폴리탄 다크초콜릿 72%"), 1)
    assert card["seen_at"] == first[0]["fetched_at"]
    saved = item_to_card(
        {"title": "x", "price": 1, "seen_at": "11/20 10:00", "fetched_at": "2026-11-24T05:00:00+00:00"}, 1
    )
    assert saved["seen_at"] == "11/20 10:00"  # 저장해 둔 결과의 시각이 먼저
