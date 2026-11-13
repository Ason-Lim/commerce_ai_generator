"""2026-11-12 사용자 결정 — 가정 기준 양과 레시피 재료의 빠른 배송.

* 대용량(5kg 초과, 액체 5L 초과, '업소용'·'대용량' 표기)은 고객이 요청할 때만 추천에 넣는다.
  요청이 없으면 '다른 후보' 맨 뒤에 이유와 함께 둔다. 전부 대용량이면 빼지 않는다.
* 예외: 쌀(20kg까지)·물(24L까지)은 한 번에 많이 사는 품목.
* 레시피 재료 상품은 같은 양 적합 단계 안에서 로켓배송 표시 상품을 먼저.
"""
from app.services.chat import explain
from app.services.recipe_chat import pack_fit


def _card(title, price, **kw):
    return explain.enrich(dict({"title": title, "price": price, "mall": "쿠팡", "shipping_fee": None, "total": None}, **kw), {})


APPLES = [_card("부사 사과 10kg 산지직송", 41400), _card("부사 사과 2kg", 13000), _card("부사 사과 3kg", 17500)]


def test_bulk_is_held_back_unless_asked():
    got = explain.choose([dict(c) for c in APPLES], ask="사과")
    assert all("10kg" not in p["title"] for p in got["picks"])
    last = got["others"][-1]
    assert "10kg" in last["title"] and "대용량(10kg)이라" in last["why"][-1]["text"]
    assert got["bulk_held"] == 1


def test_bulk_comes_back_when_asked():
    for ask in ("사과 대용량", "식당용 사과", "사과 10kg"):
        got = explain.choose([dict(c) for c in APPLES], ask=ask)
        assert any("10kg" in p["title"] for p in got["picks"]), ask
        assert got["bulk_held"] == 0


def test_all_bulk_is_not_emptied():
    cards = [_card("사과 10kg", 41000), _card("사과 15kg", 55000)]
    got = explain.choose(cards, ask="사과")
    assert len(got["picks"]) == 2 and got["bulk_held"] == 0


def test_rice_and_water_have_their_own_limits():
    rice = [_card("햅쌀 10kg", 32000), _card("백미 20kg", 55000), _card("쌀 4kg", 15000)]
    assert explain.choose(rice, ask="쌀")["bulk_held"] == 0
    water = [_card("삼다수 2L, 12개", 12000), _card("생수 500ml 20병", 8000)]
    assert explain.choose(water, ask="생수")["bulk_held"] == 0
    assert explain.bulk_size(_card("우유 2.3L, 4개", 20000)) == "9.2L"


def test_bulk_title_word_counts_only_without_size():
    assert explain.bulk_size(_card("업소용 식용유", 30000)) == "업소용 표기"
    assert explain.bulk_size(_card("미국산 척아이롤 2kg 대용량", 59000)) is None     # 표기 중량이 가정용이면 문구보다 중량


def test_recipe_ingredient_prefers_fast_delivery_within_same_fit():
    need = {"name": "굴", "amount": "400", "unit": "g", "display": "400g"}
    cards = [{"title": "통영 생굴 500g", "rocket": None}, {"title": "통영 깐굴 500g", "rocket": True},
             {"title": "통영 생굴 300g", "rocket": True}, {"title": "통영 생굴 5kg 업소용", "rocket": True}]
    kept, _ = pack_fit.arrange(cards, need)
    assert [c["title"] for c in kept][:2] == ["통영 깐굴 500g", "통영 생굴 500g"]   # 같은 '필요량 맞음' 안에서 로켓 먼저
    assert kept[-1]["fit"] == "bulk"                                                # 대용량은 로켓이어도 맨 뒤


def test_chat_and_rest_tell_that_bulk_was_held(sqlite_db):
    from app.domain.commerce.requests import SearchRequest
    from app.services.chat.service import ChatService
    from app.services.commerce.search import search_products
    from app.services.recipe_chat.service import RecipeChat
    from tests.services.chat.conftest import FakeShopping

    items = [{"product_name": t, "price": p, "product_url": f"https://www.coupang.com/vp/products/{n}",
              "platform_name": "쿠팡", "is_coupang": True}
             for n, (t, p) in enumerate([("부사 사과 10kg", 41400), ("부사 사과 2kg", 13000), ("부사 사과 3kg", 17500)], 1)]
    svc = ChatService(sqlite_db, shopping=FakeShopping(items=items), recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message="사과 추천")
    notes = [b["data"]["md"] for b in res["blocks"] if b["type"] == "notice"]
    assert any("대용량 상품 1개" in n and "대용량 사과" in n for n in notes), notes
    rest = search_products(SearchRequest(text="사과 추천"), shopping=FakeShopping(items=items))
    assert any("대용량 상품 1개" in w for w in rest.warnings)


def test_gift_request_does_not_pick_blemished_fruit():
    """2026-11-13 e2 사람 평가: '부모님 선물 사과' 1위가 못난이 사과였다 — 선물 질의에서는 흠과·못난이 표기를 고르지 않는다."""
    cards = [_card("[로켓프레시] 다조은 못난이 사과, 1개, 2.5kg(소과, 13~15입)", 10900),
             _card("[로켓프레시] 다조은 사과, 2개, 1.3kg(중과, 5~6입)", 15380),
             _card("최대15brix 세척사과 껍질째먹는 햇사과, 1박스, 5kg", 31250)]
    got = explain.choose([dict(c) for c in cards], ask="부모님 선물 사과")
    assert all("못난이" not in p["title"] for p in got["picks"])
    assert "못난이" in got["others"][-1]["title"] and "흠과·못난이" in got["others"][-1]["why"][-1]["text"]
    plain = explain.choose([dict(c) for c in cards], ask="사과")          # 선물이 아니면 그대로 견준다
    assert any("못난이" in p["title"] for p in plain["picks"])


def test_per_unit_is_not_compared_across_different_sizes():
    """2026-11-13 e2 사람 평가 '우유': 산양유 18개가 '개당' 싸다고 1위가 됐다 — 한 개 크기가 다르거나 모르는 상품과 섞이면 개당 비교 안 함."""
    assert explain.parse_volume("파스퇴르 산양유 프로틴 우유 180ml, 180ml, 18개")["volume"] == 3240   # 반복 표기는 같은 크기
    cards = [_card("과일담은 진짜 바나나우유, 8개, 220ml", 13940), _card("산양유 프로틴 우유 18개입 박스", 26640)]
    first = explain.choose(cards, ask="우유")["picks"][0]
    assert first["role"] == "lowest" and "개당" not in first["why"][0]["text"]
    same = [_card("두유 190ml, 24개", 14000), _card("두유 190ml, 16개", 10000)]   # 같은 크기끼리는 그대로
    assert explain.choose(same, ask="두유")["picks"][0]["role"] == "value"


# ── 2026-11-13 사용자 결정: 가정용 양(3kg 이하)에서 1위 · '당도 표기' 자리 (판매자 주장) ──────────────

def test_first_pick_comes_from_household_amount():
    cards = [_card("사과 5kg", 25000), _card("사과 2kg", 13000), _card("사과 3kg", 18000)]
    first = explain.choose(cards, ask="사과")["picks"][0]
    assert first["title"] == "사과 3kg" and first["why"][0]["text"].startswith("가정용 양(3kg 이하) 후보 2개 중")


def test_single_household_item_is_shown_before_cheaper_big_box():
    cards = [_card("나주배 5kg", 19900), _card("나주배 3kg", 12900), _card("나주배 10kg", 21900)]   # 귤은 예외(10kg 까지)라 배로
    got = explain.choose(cards, ask="배")
    assert [p["role"] for p in got["picks"][:2]] == ["house", "value"]
    assert got["picks"][0]["title"] == "나주배 3kg" and got["picks"][1]["title"] == "나주배 5kg"   # 가성비는 정직하게 100g당 최저
    assert explain.criteria_line(got["picks"], None).startswith("가정용 양")


def test_household_band_is_off_when_amount_or_bulk_is_asked():
    cards = [_card("귤 5kg", 17900), _card("귤 2kg", 9900), _card("귤 3kg", 13900)]
    assert explain.choose([dict(c) for c in cards], ask="가성비 귤 5kg")["picks"][0]["title"] == "귤 5kg"
    assert explain.choose([dict(c) for c in cards], ask="귤 넉넉하게")["picks"][0]["title"] == "귤 5kg"


def test_sweetness_role_names_the_seller_number_as_a_claim():
    cards = [_card("감귤 3kg", 12900), _card("감귤 2kg", 9900), _card("[로켓프레시] 귤탐 당도선별 11Brix 감귤", 12990),
             _card("[GAP인증]최고15brix 고당도 제주 감귤 3kg", 15000)]
    got = explain.choose(cards, ask="감귤")
    sweet = next(p for p in got["picks"] if p["role"] == "sweet")
    assert "11Brix" in sweet["title"]                                          # '최고 15brix'는 상한 주장이라 제외
    assert sweet["why"][0]["text"] == "판매자가 당도 11brix라고 적은 상품이에요 (판매자 주장)"
    assert sweet["role_label"] == "당도 표기"
    assert explain.brix_stated("최대21브릭스 샤인머스캣") is None and explain.brix_stated("평균12Brix 감귤") == "12"


def test_gift_request_does_not_use_household_band():
    """d6 기준점: '부모님 선물 망고'에서 가정용 양 자리가 선물용 상품을 먼저 가져가 '선물용' 배지가 사라졌다."""
    cards = [_card("제주 애플 망고 3kg 선물세트", 89000), _card("태국 망고 5kg", 45000), _card("망고 4kg 산지직송", 52000)]
    got = explain.choose(cards, ask="부모님 선물 망고")
    roles = [p["role"] for p in got["picks"]]
    assert "house" not in roles and "gift" in roles


def test_tangerine_box_is_household_up_to_10kg():
    """2026-11-13 사용자 결정 — e2 사람 평가에서 5명 중 3명이 귤 10kg 을 골랐다. 귤은 10kg 까지 가정용(가정용 양 5kg)."""
    cards = [_card("고당도 제주 감귤 5kg", 19900), _card("귤담원 제주 감귤 3kg", 12900),
             _card("서귀포 조생 감귤 10kg", 21900), _card("제주 감귤 15kg", 30000)]
    got = explain.choose(cards, ask="감귤")
    titles = {p["role"]: p["title"] for p in got["picks"]}
    assert titles["value"] == "고당도 제주 감귤 5kg"            # 가정용 양(5kg 이하) 안 100g당 최저
    assert titles["ample"] == "서귀포 조생 감귤 10kg"           # 10kg 은 넉넉한 양으로 보인다
    assert got["bulk_held"] == 1 and "15kg" in got["others"][-1]["title"]
