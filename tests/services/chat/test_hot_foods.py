"""'요즘 뜨는 식품' (2026-11-06): 문장을 쿠팡에서 검색하지 않고 급상승 리포트로 답한다.

실제 화면(2026-11-06): '요즘 뜨는 식품' → 상품명에 '요즘 뜨는'이 적힌 생수·하스카프베리 건강식품이 추천됐다.
"""
from __future__ import annotations

from app.services.chat.hot import is_hot_request, pick, sources_note
from app.services.chat.service import ChatService
from app.services.recipe_chat.service import RecipeChat
from tests.services.chat.conftest import FakeShopping

END = "2026-11-05"


def item(kw, times, n=2, status="surging", yt=None):
    return {"keyword": kw, "status": status, "ratio_recent": times, "ratio_peak": times + 1, "onset": "2026-10-25",
            "series": [{"date": END, "value": 50}], "rank": 10,
            "blog": {"status": "ok", "rising": True, "clues": {"선물·시즌": 3}},
            "rank_trend": {"status": "ok", "improved": True, "last": {"date": END, "rank": 3}},
            "google": {"status": "none"}, "youtube": yt,
            "cross": {"n": n, "of": 3, "parts": {"블로그 글 증가": True, "식품 순위 상승": True, "구글 트렌드": False}},
            "cause": {"cause": "빼빼로데이 선물 수요", "kind": "선물·시즌"}, "ask": f"{kw} 추천해줘"}


REPORT = {"data_until": END, "generated_at": "2026-11-06T10:00:00+09:00", "items": [
    item("빼빼로", 13.2, yt={"status": "ok", "recent": 30, "previous": 6, "saturated": False, "rising": True,
                            "window_days": 14}),
    item("과메기", 4.0), item("귤10kg", 4.4), item("도루묵", 5.7), item("홍익상회", 8.9, n=1)]}


def shop_items(q):
    return [{"product_name": f"{q} 1kg", "price": 12000, "product_url": f"https://www.coupang.com/vp/{abs(hash(q)) % 9999}",
             "platform_name": "쿠팡", "is_coupang": True, "is_rocket": True},
            {"product_name": "요즘 뜨는 알뜰 생수 2L 36개", "price": 29360, "product_url": "https://www.coupang.com/vp/water",
             "platform_name": "쿠팡", "is_coupang": True}]


class Shop(FakeShopping):
    def __call__(self, query, priority, session_id):
        self.calls.append((query, priority, session_id))
        return {"items": shop_items(query)}


def svc(db, report=REPORT, shop=None):
    return ChatService(db, shopping=shop or Shop(), recipe_chat=RecipeChat(statement_factory=str),
                       trend_report=lambda: report)


def blocks_of(res, kind):
    return [b for b in res["blocks"] if b["type"] == kind]


def md(res):
    return "\n".join(b["data"].get("md", "") for b in res["blocks"] if b["type"] in ("text", "notice"))


def test_which_sentences_are_trend_questions():
    assert is_hot_request("요즘 뜨는 식품") == {"category": None}
    assert is_hot_request("요즘 핫한 먹거리 추천해줘") == {"category": None}
    assert is_hot_request("요즘 유행하는 과일 뭐야") == {"category": "과일"}
    assert is_hot_request("요즘 잘 팔리는 해산물") == {"category": "해산물"}
    assert is_hot_request("요즘 인기 있는 사과 추천") is None          # 상품 이름이 있으면 그 상품 검색
    assert is_hot_request("요즘 유행하는 요리 알려줘") is None          # 요리 트렌드는 레시피가 맡는다
    assert is_hot_request("인기순으로 보여줘") is None
    assert is_hot_request("사과 추천해줘") is None


def test_the_sentence_is_never_searched_and_trending_foods_are_shown(sqlite_db):
    shop = Shop()
    res = svc(sqlite_db, shop=shop).handle(None, message="요즘 뜨는 식품")
    assert res["stage"] == "shopping_hot"
    assert all("요즘" not in q for q, _p, _s in shop.calls)                       # 문장 자체로 검색하지 않음
    assert [q for q, _p, _s in shop.calls] == ["빼빼로", "과메기", "귤10kg"]       # 위 3개 식품만 상품 검색
    [trend] = blocks_of(res, "trend_list")
    assert [i["keyword"] for i in trend["data"]["items"]][:2] == ["빼빼로", "과메기"]
    assert trend["data"]["data_until"] == END


def test_product_cards_say_why_with_the_trend_first_and_drop_unrelated_titles(sqlite_db):
    res = svc(sqlite_db).handle(None, message="요즘 뜨는 식품")
    lists = blocks_of(res, "product_list")
    assert lists[0]["data"]["title"] == "빼빼로 — 검색량 평소의 약 13.2배"
    titles = [c["title"] for b in lists for c in b["data"]["items"]]
    assert not any("생수" in t for t in titles)                                    # 상품명의 '요즘 뜨는'에 끌려오지 않음
    first = lists[0]["data"]["items"][0]
    assert first["why"][0] == {"text": "'빼빼로' 네이버 검색량이 평소의 약 13.2배예요 (10/25부터, 11/5까지)",
                               "basis": "trend"}
    assert first["go"].startswith(f"/go/{res['session_id']}/k/")


def test_sources_are_named_and_the_signal_is_not_called_quality(sqlite_db):
    text = md(svc(sqlite_db).handle(None, message="요즘 뜨는 식품"))
    assert "네이버 데이터랩 검색어 트렌드" in text and "유튜브 영상 제목·게시일" in text
    assert "구글 트렌드 (연결 전)" in text                                       # 예시 CSV 는 근거로 치지 않음
    assert "맛·품질·안전을 뜻하지 않아요" in text
    assert "구글 트렌드" in sources_note({"naver_datalab": True}) and "확인한 곳** 네이버 데이터랩" in sources_note({})


def test_chips_ask_for_one_food(sqlite_db):
    [chips] = blocks_of(svc(sqlite_db).handle(None, message="요즘 뜨는 식품"), "chips")
    assert chips["data"]["items"][:3] == ["빼빼로 추천해줘", "과메기 추천해줘", "귤10kg 추천해줘"]


def test_category_filter_and_saying_so_when_nothing_fits(sqlite_db):
    res = svc(sqlite_db).handle(None, message="요즘 유행하는 과일 뭐야")
    assert [i["keyword"] for i in blocks_of(res, "trend_list")[0]["data"]["items"]] == ["귤10kg"]
    res = svc(sqlite_db).handle(None, message="요즘 뜨는 라면")
    assert "급상승 목록에는 **라면**으로 볼 식품이 없어요" in md(res)
    assert pick({"items": REPORT["items"]}, "해산물")[1] is True


def test_no_report_means_no_made_up_trends(sqlite_db):
    res = svc(sqlite_db, report=None).handle(None, message="요즘 뜨는 식품")
    assert not blocks_of(res, "product_list") and "오늘의 급상승 리포트가 아직 없어요" in md(res)


def test_earlier_trend_cards_keep_their_links(sqlite_db):
    s = svc(sqlite_db)
    res = s.handle(None, message="요즘 뜨는 식품")
    card = blocks_of(res, "product_list")[0]["data"]["items"][0]
    s.handle(res["session_id"], message="사과 추천해줘")
    assert s.resolve_go_key(res["session_id"], card["key"]) == card["url"]


def test_products_must_carry_the_trending_name():
    """실제 결과(11/06): '볶음너구리' 후보에 불닭볶음면 큰컵세트가 섞였다."""
    from app.services.chat.hot import names_food
    assert names_food("네이처블룸, 농심 볶음너구리 130gx4", "볶음너구리")
    assert not names_food("볶음면 큰컵세트 불닭볶음면 까르보불닭 콕콕라면", "볶음너구리")
    assert names_food("제주 감귤 10kg 가정용", "귤10kg") and names_food("해남 절임배추 20kg", "절임배추20kg")
    assert names_food("국산 생새우 김장용 1kg", "김장용생새우") and not names_food("냉동 칵테일새우 1kg", "김장용생새우")
