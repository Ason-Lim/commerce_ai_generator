"""2026-11-21 사용자 대화 확인(올리브 → 생 올리브 → 올리브유 → 엑스트라 버전)에서 나온 오류.

1. '올리브유' — 쿠팡이 '해표 압착 올리브유'를 용량·수량 옵션별로 같은 이름으로 돌려줘 하나로 합쳐졌는데,
   카드에는 옵션이 있다는 말이 없었다 → 대표 카드에 '용량·수량 옵션이 있어요 · 같은 이름 상품 n개 · 가격 범위'.
2. '엑스트라 버전'(엑스트라버진 오타) — 앞 대화를 잇지 않고 문장 그대로 찾아 스케쳐스 신발·크리컷 커팅기를 추천
   → 오타 고침 · 꾸밈말만 말하면 앞서 찾은 상품에 이어 찾기 · 쿠팡 분류가 식품 밖이면 후보에서 뺌.
3. '생 올리브' — '생'이 검색어에서 빠져 '올리브'와 같은 답 → '생 올리브'로 찾고, '생' 표기 상품이 없으면 알린다.
4. 네이버쇼핑 '올리브 가정용' 확인할 점이 '흠과·못난이 여부' — 과일·채소에만 맞는 말.
"""
from __future__ import annotations

from app.services.chat.service import ChatService, naver_search_links, refine_followup
from app.services.commerce.nonfood import is_non_food_category
from app.services.commerce.search import fix_typos, fresh_request
from app.services.recipe_chat.service import RecipeChat
from app.services.recommendation.deduplication import deduplicate_market_items
from tests.services.chat.conftest import FakeShopping


def _cp(name, price, item_id, category="식품"):
    return {"product_name": name, "price": price, "platform": "coupang", "mall_name": "쿠팡", "is_coupang": True,
            "product_url": f"https://link.coupang.com/re/AFFSDP?pageKey=100&itemId={item_id}&vendorItemId=9{item_id}",
            "category_name": category}


def md(res):
    return "\n".join(b["data"].get("md", "") for b in res["blocks"] if b["type"] in ("text", "notice"))


def items_of(res):
    return [i for b in res["blocks"] if b["type"] == "product_list" for i in b["data"]["items"]]


# 1. 같은 이름 옵션 ────────────────────────────────────────────────

def test_same_name_options_are_merged_but_recorded():
    got = deduplicate_market_items([_cp("해표 압착 올리브유", 9860, 1), _cp("해표 압착 올리브유", 7950, 2),
                                    _cp("해표 압착 올리브유", 6900, 3), _cp("페페브루노 포마스 올리브오일", 10900, 4)])
    assert [g["product_name"] for g in got] == ["해표 압착 올리브유", "페페브루노 포마스 올리브오일"]
    assert got[0]["price"] == 6900
    assert got[0]["same_name_options"] == {"count": 3, "price_min": 6900, "price_max": 9860}
    assert "same_name_options" not in got[1]


def test_exact_duplicates_are_not_called_options():
    got = deduplicate_market_items([_cp("해표 압착 올리브유", 6900, 3), _cp("해표 압착 올리브유", 6900, 3)])
    assert len(got) == 1 and "same_name_options" not in got[0]


def test_option_note_reaches_the_chat_card(sqlite_db):
    merged = deduplicate_market_items([_cp("해표 압착 올리브유", 9860, 1), _cp("해표 압착 올리브유", 6900, 3)])
    svc = ChatService(sqlite_db, shopping=FakeShopping(items=merged), recipe_chat=RecipeChat(statement_factory=str))
    card = items_of(svc.handle(None, message="올리브유"))[0]
    assert card["weight_note"] == {"kind": "options", "label": "용량·수량 옵션이 있어요",
                                   "detail": "같은 이름 상품 2개 · 6,900~9,860원"}
    assert "same_name_options" not in card and "category" not in card     # 화면에는 weight_note 로만


# 2. 엑스트라 버전 ────────────────────────────────────────────────

SHOES = _cp("스케쳐스 남성 (엑스트라 와이드핏VER 보통핏VER) 슬립인스 고워크", 139000, 7, "패션의류잡화")
CRICUT = _cp("크리컷 조이 엑스트라 디지털 버전 3295663", 309900, 8, "가전디지털")
EVOO = _cp("데체코 엑스트라버진 올리브유 500ml, 1개", 12900, 9)


def test_typo_and_non_food_category():
    assert fix_typos("엑스트라 버전") == "엑스트라버진"
    assert fix_typos("엑스트라버전 올리브유") == "엑스트라버진 올리브유"
    assert fix_typos("버전 업") == "버전 업"
    assert is_non_food_category("패션의류잡화") and is_non_food_category("가전디지털")
    assert not is_non_food_category("식품") and not is_non_food_category("헬스/건강식품")
    assert not is_non_food_category(None) and not is_non_food_category("")


def test_non_food_products_are_never_recommended(sqlite_db, monkeypatch):
    monkeypatch.delenv("NAVER_CONNECT_REGISTRY_CSV", raising=False)
    shop = FakeShopping(items=[SHOES, CRICUT])
    svc = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message="엑스트라 버전")
    assert shop.calls[0][0] == "엑스트라버진"
    assert not items_of(res)
    assert "관련 없는 상품은 보여 드리지 않았어요" in md(res)


def test_a_qualifier_follow_up_continues_the_previous_search(sqlite_db):
    shop = FakeShopping(items=[_cp("해표 압착 올리브유 900ml", 9860, 1), EVOO, SHOES])
    svc = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    first = svc.handle(None, message="올리브유")
    res = svc.handle(first["session_id"], message="엑스트라 버전")
    assert shop.calls[-1][0] == "엑스트라버진 올리브유"
    assert "앞서 찾은 '올리브유'에 이어서 **엑스트라버진 올리브유** 로 찾아봤어요." in md(res)
    titles = [i["title"] for i in items_of(res)]
    assert titles and not any("스케쳐스" in t for t in titles)


def test_refine_followup_rules():
    st = {"mode": "shopping", "pending": {"kind": "budget", "query": "올리브유"}}
    assert refine_followup("국산은요?", st)["text"] == "국산 올리브유"
    assert refine_followup("냉동으로", st)["text"] == "냉동 올리브유"
    assert refine_followup("엑스트라버진 올리브유", st) is None          # 상품어가 있으면 새 검색
    assert refine_followup("고마워", st) is None
    assert refine_followup("엑스트라버진", {"mode": "recipe"}) is None       # 직전이 쇼핑 답일 때만
    seen = {"mode": "shopping", "seen": [{"query": "사과"}]}
    assert refine_followup("유기농", seen)["text"] == "유기농 사과"


# 3. 생 올리브 ────────────────────────────────────────────────

def test_fresh_word_is_kept_in_the_search(sqlite_db):
    assert fresh_request("생 올리브", "올리브") == "올리브"
    assert fresh_request("생수 추천", "생수") is None and fresh_request("생일 케이크", "케이크") is None
    jars = [_cp("마리오 블랙 올리브 홀 절임 310g", 3300, 1), _cp("리치스 그린 올리브 365g", 5300, 2)]
    shop = FakeShopping(items=jars)
    svc = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message="생 올리브")
    assert shop.calls[0][0] == "생 올리브"
    assert "상품명에 '생 올리브' 표기가 있는 상품이 없어요" in md(res)


def test_no_fresh_notice_when_a_fresh_product_is_there(sqlite_db):
    shop = FakeShopping(items=[_cp("스페인산 생올리브 1kg", 19000, 1), _cp("리치스 그린 올리브 365g", 5300, 2)])
    svc = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    assert "표기가 있는 상품이 없어요" not in md(svc.handle(None, message="생 올리브"))


# 4. 네이버쇼핑 확인할 점 ────────────────────────────────────────

def test_blemish_tip_only_for_fruit_and_vegetables():
    assert ("올리브 가정용", "용량·구성 표기와 교환·반품 조건을 확인하세요") in naver_search_links("올리브", "올리브")
    assert ("사과 가정용", "흠과·못난이 여부와 교환·반품 조건을 확인하세요") in naver_search_links("사과", "사과")
    assert ("양파 가정용", "흠과·못난이 여부와 교환·반품 조건을 확인하세요") in naver_search_links("양파", "양파")


# 2026-11-21 2차 확인(PDF): '생올리브' → '엑스트라 버전' ─────────────────────

def test_oil_only_qualifier_does_not_stick_to_a_non_oil_search():
    st = {"mode": "shopping", "pending": {"kind": "budget", "query": "생올리브"}}
    assert refine_followup("엑스트라 버전", st) is None                 # '엑스트라버진 생올리브'로 잇지 않음
    assert refine_followup("국산은요?", st)["text"] == "국산 생올리브"
    oil = {"mode": "shopping", "pending": {"kind": "budget", "query": "올리브유"}}
    assert refine_followup("엑스트라 버전", oil)["text"] == "엑스트라버진 올리브유"
    assert refine_followup("압착", {"mode": "shopping", "pending": {"kind": "budget", "query": "참기름"}})["text"] == "압착 참기름"


def test_oil_only_follow_up_after_olives_searches_the_word_alone(sqlite_db, monkeypatch):
    monkeypatch.delenv("NAVER_CONNECT_REGISTRY_CSV", raising=False)
    shop = FakeShopping(items=[_cp("리치스 그린 올리브 365g", 5300, 2), EVOO, SHOES])
    svc = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    first = svc.handle(None, message="생올리브")
    res = svc.handle(first["session_id"], message="엑스트라 버전")
    assert shop.calls[-1][0] == "엑스트라버진"
    assert not any("스케쳐스" in i["title"] for i in items_of(res))


def test_attached_fresh_word():
    assert fresh_request("생올리브", "생올리브") == "올리브"
    assert fresh_request("생연어 추천", "생연어") == "연어"
    for t in ("생강", "생수", "생크림", "생일 케이크", "생닭"):
        assert fresh_request(t, t) is None, t
