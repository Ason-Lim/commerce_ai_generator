"""2026-11-22 사용자 대화 확인: '올리브유' → '엑스트라 버전' → '쿠팡에서 엑스트라버진 올리브유 관련 상품을 찾지 못했어요'.

쿠팡 파트너스 검색은 '엑스트라버진 올리브유'(붙여 씀)에 0건, '올리브유 엑스트라'·'버진 올리브유'에는 상품을 돌려줬다(MCP 재현).
→ 0건이면 '엑스트라 버진 올리브유' → '올리브유' 순으로 다시 찾고, 엑스트라버진을 찾았으니 포마스·퓨어는 빼고
  등급 표기 상품을 먼저 견준다.
"""

from __future__ import annotations

from app.services.chat.service import ChatService
from app.services.commerce.search import grade_filter, retry_queries
from app.services.recipe_chat.service import RecipeChat


def _cp(name, price, item_id):
    return {
        "product_name": name,
        "price": price,
        "platform": "coupang",
        "mall_name": "쿠팡",
        "is_coupang": True,
        "product_url": f"https://link.coupang.com/re/AFFSDP?pageKey=100&itemId={item_id}&vendorItemId=9{item_id}",
        "category_name": "식품",
    }


BASE = [
    _cp("해표 압착 올리브유", 6900, 1),
    _cp("살부루아 올리브 포마스유 1L (PET)", 19900, 2),
    _cp("커클랜드 엑스트라버진 올리브유 3L 스페인산 저온압착 올리브오일", 71980, 3),
    _cp("올리타리아 엑스트라 버진 올리브유, 1L, 1개", 15900, 4),
    _cp("피에트로코리첼리 올리브유", 11500, 5),
]


class ByQuery:
    """쿠팡처럼 검색어마다 다른 결과 — 없는 말은 0건."""

    def __init__(self, table):
        self.table, self.calls = table, []

    def __call__(self, query, priority, session_id):
        self.calls.append(query)
        return {"items": list(self.table.get(query, [])), "recommendation_path": "canonical_provider"}


def md(res):
    return "\n".join(b["data"].get("md", "") for b in res["blocks"] if b["type"] in ("text", "notice"))


def titles(res):
    return [i["title"] for b in res["blocks"] if b["type"] == "product_list" for i in b["data"]["items"]]


def test_retry_queries():
    assert retry_queries("엑스트라버진 올리브유") == ["엑스트라버진 올리브유 500ml", "엑스트라버진 올리브유 1L", "올리브유"]
    assert retry_queries("올리브유") == ["올리브오일"]          # 2026-11-22: 바꿔 쓸 말 표 (data/query_synonyms.csv)
    assert retry_queries("참기름") == []


def test_grade_filter_drops_other_grades_and_unlabelled_when_enough():
    cards = [{"title": t["product_name"]} for t in BASE]
    kept, info = grade_filter("엑스트라버진 올리브유", cards)
    assert [c["title"] for c in kept] == [BASE[2]["product_name"], BASE[3]["product_name"]]
    assert info == {"stated": 2, "unknown": 0, "unknown_cards": [], "dropped": 3}


def test_grade_filter_keeps_unlabelled_with_note_when_few():
    cards = [
        {"title": "커클랜드 엑스트라버진 올리브유 3L"},
        {"title": "피에트로코리첼리 올리브유"},
        {"title": "프리모셰프 포마스 올리브오일"},
    ]
    kept, info = grade_filter("엑스트라버진 올리브유", cards)
    # 2026-11-22 외부 검토 2: 표기 없는 상품은 견주는 후보에 섞지 않고 따로('등급 확인 필요')
    assert [c["title"] for c in kept] == ["커클랜드 엑스트라버진 올리브유 3L"]
    assert [c["title"] for c in info["unknown_cards"]] == ["피에트로코리첼리 올리브유"]
    assert "grade_note" in info["unknown_cards"][0]
    assert {k: info[k] for k in ("stated", "unknown", "dropped")} == {"stated": 1, "unknown": 1, "dropped": 1}
    assert grade_filter("올리브유", cards) == (cards, None)


def test_chat_retries_when_coupang_returns_nothing(sqlite_db):
    shop = ByQuery({"올리브유": BASE})
    svc = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message="엑스트라 버진 올리브유")
    assert shop.calls == ["엑스트라버진 올리브유", "엑스트라버진 올리브유 500ml", "엑스트라버진 올리브유 1L", "올리브유"]
    got = titles(res)
    assert BASE[2]["product_name"] in got and BASE[3]["product_name"] in got
    assert not any("포마스" in t for t in got) and "해표 압착 올리브유" not in got
    text = md(res)
    assert "'올리브유'로 다시 찾았어요" in text and "엑스트라버진 표기가 있는 상품 2개" in text
    assert "찾지 못했어요" not in text


def test_followup_after_olive_oil_uses_retry(sqlite_db):
    shop = ByQuery({"올리브유": BASE})
    svc = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    first = svc.handle(None, message="올리브유")
    res = svc.handle(first["session_id"], message="엑스트라 버전")
    assert "엑스트라버진 올리브유" in shop.calls[1]
    assert BASE[2]["product_name"] in titles(res)
    assert "grade_note" not in str([b for b in res["blocks"] if b["type"] == "product_list"])


def test_no_retry_when_first_search_has_results(sqlite_db):
    shop = ByQuery({"엑스트라버진 올리브유": [BASE[2]]})
    svc = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    svc.handle(None, message="엑스트라버진 올리브유")
    assert shop.calls == ["엑스트라버진 올리브유"]


def test_still_empty_after_retries(sqlite_db):
    shop = ByQuery({})
    svc = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message="엑스트라버진 올리브유")
    assert len(shop.calls) == 4
    assert "찾지 못했어요" in md(res)


# ── 2026-11-22 오후: 쿠팡이 무관한 10개(건전지·클렌징 폼·놀이공원 표…)를 준 경우 · 쿠팡 검색 결과 링크 ──────────────

JUNK = [dict(_cp(t, 9000 + i, 50 + i), category_name=c) for i, (c, t) in enumerate([
    ("생활용품", "듀라셀 알카라인 AA 건전지"), ("뷰티", "센카 퍼펙트 휩 프레시 클렌징 폼"),
    ("도서/음반", "타이거 은행놀이 (리뉴얼)"), ("국내투어", "★롯데월드 아쿠아리움 1인권"),
    ("로켓프레시", "손질 코다리토막 (냉동)")])]


def test_unrelated_results_also_trigger_retry(sqlite_db):
    shop = ByQuery({"엑스트라버진 올리브유": JUNK, "엑스트라버진 올리브유 500ml": JUNK, "엑스트라버진 올리브유 1L": JUNK,
                    "올리브유": BASE})
    svc = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message="엑스트라 버진 올리브유")
    assert shop.calls == ["엑스트라버진 올리브유", "엑스트라버진 올리브유 500ml", "엑스트라버진 올리브유 1L", "올리브유"]
    got = titles(res)
    assert BASE[2]["product_name"] in got and not any("건전지" in t or "아쿠아리움" in t for t in got)
    assert "'올리브유'로 다시 찾았어요" in md(res)


def test_coupang_search_link_block_when_nothing_usable(sqlite_db, tmp_path, monkeypatch):
    monkeypatch.setenv("COUPANG_SEARCH_LINK", "on")
    monkeypatch.setenv("COUPANG_GAPS_DB", str(tmp_path / "g.sqlite3"))
    made = []
    monkeypatch.setattr("app.services.coupang_api.search_deeplink",
                        lambda q: made.append(q) or "https://link.coupang.com/a/test123")
    shop = ByQuery({})
    svc = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message="엑스트라 버진 올리브유")
    links = [b for b in res["blocks"] if b["type"] == "search_links"]
    cp = next(b for b in links if b["data"]["title"] == "쿠팡에서 직접 찾아보기")
    assert cp["data"]["links"][0]["url"].startswith(f"/go/q/{res['session_id']}/")
    assert "우리가 고르거나 견준 상품이 아니에요" in cp["data"]["links"][0]["check"]
    kinds = [b["type"] for b in res["blocks"]]
    notice_at = next(i for i, b in enumerate(res["blocks"]) if b["type"] == "notice" and "쿠팡 파트너스" in b["data"]["md"])
    assert notice_at < kinds.index("search_links")                      # 고지가 링크보다 먼저
    svc.handle(None, message="엑스트라 버진 올리브유")
    assert made == ["엑스트라버진 올리브유"]                               # 두 번째는 저장된 링크 재사용


def test_link_store_and_go_route(tmp_path, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.api import chat_routes
    from app.services.commerce import coupang_gaps as cg

    monkeypatch.setenv("COUPANG_GAPS_DB", str(tmp_path / "g.sqlite3"))
    link = cg.GapStore().link("엑스트라 버진 올리브유", lambda q: "https://link.coupang.com/a/abc")
    assert cg.GapStore().link_by_id(link["id"])["url"] == "https://link.coupang.com/a/abc"
    clicks = []
    monkeypatch.setattr("app.services.analytics_logger.log_product_click", lambda **kw: clicks.append(kw))
    app = FastAPI()
    app.include_router(chat_routes.router)
    r = TestClient(app).get(f"/go/q/sid1/{link['id']}", follow_redirects=False)
    assert r.status_code in (302, 307) and r.headers["location"] == "https://link.coupang.com/a/abc"
    assert clicks and clicks[0]["product"]["selected_section"] == "search_link"
    assert TestClient(app).get("/go/q/sid1/9999", follow_redirects=False).headers["location"] == "/"


def test_bare_grade_word_in_new_chat_searches_olive_oil(sqlite_db):
    """2026-11-22 15:31 PDF: 새 대화 '엑스트라 버진'만 → 품목 이름이 없어 '찾지 못했어요'였다."""
    assert retry_queries("엑스트라버진") == ["엑스트라버진 올리브유 500ml", "엑스트라버진 올리브유 1L", "올리브유"]
    shop = ByQuery({"엑스트라버진": JUNK, "올리브유": BASE})
    svc = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message="엑스트라 버진")
    assert shop.calls == ["엑스트라버진", "엑스트라버진 올리브유 500ml", "엑스트라버진 올리브유 1L", "올리브유"]
    assert BASE[2]["product_name"] in titles(res)
    # 2026-11-22 외부 검토 2: 어떻게 해석했는지 밝힌다
    assert "'엑스트라버진'만 말씀하셔서 **엑스트라버진 올리브유**를 찾는 것으로 보고 '올리브유'로 찾았어요" in md(res)


def test_size_variant_finds_labelled_evoo(sqlite_db):
    """2026-11-22 17:2x 운영 확인: '엑스트라버진 올리브유'·'올리브오일' 은 해표 압착만, '…500ml' 은 오뚜기 엑스트라버진."""
    evoo = _cp("오뚜기 엑스트라버진 올리브유", 10950, 70)
    shop = ByQuery({"엑스트라버진 올리브유": JUNK, "엑스트라버진 올리브유 500ml": [evoo, BASE[0]], "올리브유": [BASE[0]]})
    svc = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message="엑스트라버진 올리브유")
    assert shop.calls[:2] == ["엑스트라버진 올리브유", "엑스트라버진 올리브유 500ml"]
    lists_ = [b["data"] for b in res["blocks"] if b["type"] == "product_list"]
    assert [c["title"] for c in lists_[0]["items"]] == ["오뚜기 엑스트라버진 올리브유"]
    assert any((d.get("title") or "").startswith("등급 확인 필요") for d in lists_)
    assert "용량을 붙인 '엑스트라버진 올리브유 500ml'로 다시 찾았어요" in md(res)


def test_typo_name_searches_similar_word(sqlite_db):
    """2026-11-22 17:31: '브레타 치즈' — 쿠팡 사이트는 '부라타'로 고쳐 60개, 파트너스 검색 API 는 고치지 않음."""
    burrata = [_cp("벨지오이오조 부라타 치즈 113g", 7900, 80), _cp("코스트코 벨지오이오소 부라타치즈 453G", 17590, 81)]
    shop = ByQuery({"부라타 치즈": burrata})
    svc = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message="브레타 치즈")
    assert shop.calls[:2] == ["브레타 치즈", "부라타 치즈"]
    assert "벨지오이오조 부라타 치즈 113g" in titles(res)
    assert "비슷한 말 **'부라타'**(으)로 보고 찾았어요" in md(res)


def test_generic_word_from_ai_is_ignored(monkeypatch):
    """2026-11-22: 홈 예시 '돌잔치 하객 답례품으로 … 먹거리 추천해 줘' — AI 가 '먹거리'를 뽑았다."""
    from app.services.chat import service as S
    from app.services.commerce import coupang_gaps

    monkeypatch.setattr(coupang_gaps, "vocab", lambda: {"답례품", "해남절임배추"})
    text = "돌잔치 하객 답례품으로 1만 원대에 받는 사람이 좋아할 만한 먹거리 추천해 줘"
    assert S.shopping_terms(text, lambda t: {"keyword": "먹거리"})[0] == "답례품"
    assert S.shopping_terms("제철 해남절임배추로 4인분 저녁 메뉴 만들려면 뭐 사야 해?")[0] == "해남절임배추"
