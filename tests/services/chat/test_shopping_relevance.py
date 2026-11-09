"""쇼핑 검색어·관련성 (2026-10-31): 문장 전체를 검색어로 보내 핫팩·노트북이 추천되던 문제.

* 조건이 붙은 문장은 상품어('휘태커스초콜릿')로 검색하고, 결과는 그 말과 겹쳐야만 보여 준다.
* 관련 상품이 없으면 그렇다고 말하고, 네이버 쇼핑커넥트 등록부(브랜드커넥트에서 발급한 링크)를 찾아본다.
* 짧은 요청(2026-11-02~)도 상품어만 검색하고, 그 말(또는 같은 부류의 말)과 겹치는 상품만 보여 준다.
"""
from __future__ import annotations

from app.services.chat.service import ChatService, relevant, shopping_terms
from app.services.recipe_chat.service import RecipeChat
from tests.services.chat.conftest import FakeShopping

SENTENCE = "휘태커스초콜릿 중에 너무 달지 않고 아이랑 같이 먹기 좋은 거 추천해 줘"
JUNK = [{"product_name": n, "price": 9000, "product_url": "https://www.coupang.com/x", "platform_name": "coupang"}
        for n in ("올덴 화롯불 특대형 대용량 핫팩 150g, 20개", "위칙 소독 섬유유연제 본품, 2.3L", "레노버 아이디어패드 슬림 3")]
GOOD = [{"product_name": "휘태커스 다크 초콜릿 72% 250g", "price": 8900, "product_url": "https://www.coupang.com/w",
         "platform_name": "coupang"}]


def md(res):
    return "\n".join(b["data"].get("md", "") for b in res["blocks"] if b["type"] in ("text", "notice"))


def test_a_sentence_is_searched_by_its_product_word():
    assert shopping_terms(SENTENCE) == ("휘태커스초콜릿", ["휘태커스초콜릿"])
    assert shopping_terms("사과 추천해줘") == ("사과", ["사과"])          # 2026-11-02: 짧은 요청도 상품어만 검색·관련성 확인
    assert shopping_terms("사과를 추천해 줘") == ("사과", ["사과"])
    assert shopping_terms("두바이 쫀득쿠키 추천해줘")[0] == "두바이 쫀득쿠키"
    assert shopping_terms("빼빼로데이에 회사 동료 20명한테 돌릴 과자 선물 추천해 줘")[0] == "빼빼로데이"
    word = shopping_terms("빼빼로데이에 회사 동료 20명한테 돌릴 과자 선물 추천해 줘", lambda t: {"keyword": "과자"})
    assert word == ("과자", ["과자"])
    assert shopping_terms(SENTENCE.replace("휘태커스초콜릿 중에", "회사에서"), lambda t: {"keyword": "노트북"})[0] != "노트북"


def test_unrelated_products_are_never_recommended(sqlite_db, monkeypatch):
    monkeypatch.delenv("NAVER_CONNECT_REGISTRY_CSV", raising=False)
    shop = FakeShopping(items=JUNK)
    svc = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message=SENTENCE)
    assert shop.calls[0][0] == "휘태커스초콜릿"
    assert not any(b["type"] == "product_list" for b in res["blocks"])
    assert "쿠팡에서 **휘태커스초콜릿** 관련 상품을 찾지 못했어요. 관련 없는 상품은 보여 드리지 않았어요." in md(res)
    assert "네이버 쇼핑커넥트(브랜드커넥트)에 등록한 **휘태커스초콜릿** 링크도 아직 없어요." in md(res)


def test_related_products_are_kept(sqlite_db):
    svc = ChatService(sqlite_db, shopping=FakeShopping(items=JUNK + GOOD), recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message=SENTENCE)
    items = next(b for b in res["blocks"] if b["type"] == "product_list")["data"]["items"]
    assert [i["title"] for i in items] == ["휘태커스 다크 초콜릿 72% 250g"]


def test_registered_shopping_connect_links_are_shown_when_coupang_has_none(sqlite_db, tmp_path, monkeypatch):
    reg = tmp_path / "naver_connect_links.csv"
    reg.write_text("키워드,상품명,스토어명,판매가,쇼핑커넥트 링크,수수료율(%),발급일,링크 확인일,사용처(블로그/사이트),메모\n"
                   "휘태커스초콜릿,휘태커스 밀크 초콜릿 250g,초콜릿상점,9500,https://naver.me/abc,3,2026-10-31,2026-10-31,사이트,\n"
                   "과메기,구룡포 과메기,바다,20000,,3,,,,\n", encoding="utf-8-sig")
    monkeypatch.setenv("NAVER_CONNECT_REGISTRY_CSV", str(reg))
    svc = ChatService(sqlite_db, shopping=FakeShopping(items=JUNK), recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message=SENTENCE)
    items = next(b for b in res["blocks"] if b["type"] == "product_list")["data"]["items"]
    assert [(i["mall"], i["title"], i["url"], i["price"]) for i in items] == [
        ("네이버 (쇼핑커넥트)", "휘태커스 밀크 초콜릿 250g", "https://naver.me/abc", 9500)]
    assert "네이버 쇼핑커넥트(브랜드커넥트)에서 발급해 등록해 둔 링크예요." in md(res)
    assert all(i["affiliate"] is True and i["affiliate_program"] == "네이버 쇼핑커넥트" for i in items)
    assert items[0]["source"] == "초콜릿상점"
    assert "수수료" in md(res) and "무료 운영" in md(res)


def test_relevance_is_about_shared_words():
    assert relevant("Whittaker's 휘태커스 밀크 초콜릿", ["휘태커스초콜릿"])
    assert not relevant("올덴 화롯불 특대형 대용량 핫팩", ["휘태커스초콜릿"])


def test_connect_links_are_listed_separately_next_to_coupang_results(sqlite_db, tmp_path, monkeypatch):
    """2026-11-02: 쿠팡 결과가 있어도 쇼핑커넥트 등록 상품을 별도 목록으로 보여 주고, 쿠팡 후보의 순서는 바꾸지 않는다."""
    reg = tmp_path / "naver_connect_links.csv"
    reg.write_text("상품명,스토어명,판매가,쇼핑커넥트 링크,키워드,링크 확인일\n"
                   "휘태커스 밀크 초콜릿 250g,초콜릿상점,9500,https://naver.me/abc,휘태커스초콜릿,2026.11.2\n",
                   encoding="utf-8-sig")
    monkeypatch.setenv("NAVER_CONNECT_REGISTRY_CSV", str(reg))
    svc = ChatService(sqlite_db, shopping=FakeShopping(items=JUNK + GOOD), recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message=SENTENCE)
    lists = [b["data"] for b in res["blocks"] if b["type"] == "product_list"]
    assert [i["title"] for i in lists[0]["items"]] == ["휘태커스 다크 초콜릿 72% 250g"]
    connect = next(d for d in lists if d.get("title", "").startswith("네이버 쇼핑커넥트 등록 상품"))
    assert [(i["title"], i["url"], i["affiliate"]) for i in connect["items"]] == [
        ("휘태커스 밀크 초콜릿 250g", "https://naver.me/abc", True)]
    assert "수수료" in connect["note"] and connect["items"][0]["rank"] == 2


def test_short_requests_also_find_registered_connect_links(sqlite_db, tmp_path, monkeypatch):
    reg = tmp_path / "naver_connect_links.csv"
    reg.write_text("상품명,스토어명,판매가,쇼핑커넥트 링크,키워드\n영주사과 홍로 2kg,햇살품은사과,22900,https://naver.me/s,사과 홍로\n",
                   encoding="utf-8-sig")
    monkeypatch.setenv("NAVER_CONNECT_REGISTRY_CSV", str(reg))
    apple = [{"product_name": "경북 부사 사과 3kg", "price": 19900, "product_url": "https://www.coupang.com/a",
              "platform_name": "coupang"}]
    svc = ChatService(sqlite_db, shopping=FakeShopping(items=apple), recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message="사과 추천해줘")
    titles = [i["title"] for b in res["blocks"] if b["type"] == "product_list" for i in b["data"]["items"]]
    assert "영주사과 홍로 2kg" in titles and "경북 부사 사과 3kg" in titles


def test_alcohol_requests_never_get_connect_links(sqlite_db, tmp_path, monkeypatch):
    """어필리에이트 운영정책 1장: 주류 관련 콘텐츠는 활동 제한 채널 — 술 질문에는 쇼핑커넥트 목록을 붙이지 않는다."""
    from app.services.chat.service import is_alcohol_request
    assert is_alcohol_request("와인 추천해줘") and is_alcohol_request("막걸리랑 어울리는 전") and is_alcohol_request("술안주 추천")
    assert not is_alcohol_request("맛술 대신 쓸 것") and not is_alcohol_request("사과 추천해줘") and not is_alcohol_request("술빵 만들기")
    reg = tmp_path / "naver_connect_links.csv"
    reg.write_text("상품명,스토어명,판매가,쇼핑커넥트 링크,키워드\n하루견과 믹스,넛츠피아,29900,https://naver.me/n,견과 안주\n",
                   encoding="utf-8-sig")
    monkeypatch.setenv("NAVER_CONNECT_REGISTRY_CSV", str(reg))
    nuts = [{"product_name": "하루견과 믹스 20봉", "price": 19900, "product_url": "https://www.coupang.com/n", "platform_name": "coupang"}]
    svc = ChatService(sqlite_db, shopping=FakeShopping(items=nuts), recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message="맥주 안주 견과 추천해줘")
    assert not any((b["data"].get("title") or "").startswith("네이버 쇼핑커넥트") for b in res["blocks"] if b["type"] == "product_list")
    assert "쇼핑커넥트" not in md(res)


def test_connect_cards_open_the_issued_link_directly(sqlite_db, tmp_path, monkeypatch):
    reg = tmp_path / "naver_connect_links.csv"
    reg.write_text("상품명,스토어명,판매가,쇼핑커넥트 링크,키워드\n영주사과 홍로 2kg,햇살품은사과,22900,https://naver.me/s,사과\n",
                   encoding="utf-8-sig")
    monkeypatch.setenv("NAVER_CONNECT_REGISTRY_CSV", str(reg))
    svc = ChatService(sqlite_db, shopping=FakeShopping(items=[]), recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message="사과 추천해줘")
    card = next(i for b in res["blocks"] if b["type"] == "product_list" for i in b["data"]["items"])
    assert card["direct"] is True and card["url"] == "https://naver.me/s"


def test_short_requests_drop_unrelated_products_but_keep_the_same_kind():
    """2026-11-02 실제 화면: '사과를 추천해 줘'에 '제이커스 종이소녀상만들기'가 섞였다."""
    assert not relevant("제이커스 종이소녀상만들기", ["사과"])
    assert relevant("아삭달콤 과즙 가득 제철 햇사과 10kg", ["사과"])
    assert relevant("곰곰 호주산 앞다리 샤브샤브용 (냉장)", ["소고기"])      # 부류 이름 → 같은 부류
    assert relevant("나주배 7.5kg", ["배"]) and not relevant("무료배송 사과 3kg", ["배"])
    assert relevant("제주 노지 감귤 3kg", ["귤"])


def test_short_request_shows_only_related_products(sqlite_db):
    items = [{"product_name": n, "price": p, "product_url": f"https://www.coupang.com/{i}", "platform_name": "coupang"}
             for i, (n, p) in enumerate([("아삭달콤 햇사과 10kg", 33900), ("제이커스 종이소녀상만들기", 2200)])]
    shop = FakeShopping(items=items)
    res = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str)).handle(None, message="사과를 추천해 줘")
    titles = [i["title"] for b in res["blocks"] if b["type"] == "product_list" for i in b["data"]["items"]]
    assert shop.calls[0][0] == "사과" and titles == ["아삭달콤 햇사과 10kg"]


def test_beef_request_does_not_take_pork_with_the_same_cut_name():
    """'목심'·'앞다리'는 소·돼지 모두에 있다 — '소고기'에 '한돈 목살'이, '돼지고기'에 '한우 앞다리'가 섞이지 않게."""
    assert not relevant("한돈 목살 구이용 500g", ["소고기"]) and not relevant("돼지 목심", ["소고기"])
    assert relevant("한우 앞다리 불고기용", ["소고기"]) and not relevant("한우 앞다리 불고기용", ["돼지고기"])
    assert relevant("한돈 앞다리 수육용", ["돼지고기"])


def test_connect_registry_skips_unissued_alcohol_and_excluded_rows(sqlite_db, tmp_path, monkeypatch):
    """2026-11-02: 상품 주소(발급 링크 아님)·주류 상품·실적 제외 유형(정기배송 등) 줄은 보여 주지 않는다."""
    reg = tmp_path / "naver_connect_links.csv"
    reg.write_text("상품명,스토어명,판매가,쇼핑커넥트 링크,키워드\n"
                   "영주사과 홍로 2kg,햇살품은사과,22900,https://naver.me/s,사과\n"
                   "청송 사과 3kg,청송,19900,https://smartstore.naver.com/x/products/1,사과\n"
                   "사과 정기배송 4주,과일가게,49000,https://naver.me/sub,사과\n"
                   "사과 와인 750ml,양조장,25000,https://naver.me/wine,사과\n"
                   "사과 술빵 10개,빵집,12000,https://naver.me/bread,사과\n", encoding="utf-8-sig")
    monkeypatch.setenv("NAVER_CONNECT_REGISTRY_CSV", str(reg))
    svc = ChatService(sqlite_db, shopping=FakeShopping(items=[]), recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message="사과 추천해줘")
    urls = [i["url"] for b in res["blocks"] if b["type"] == "product_list" for i in b["data"]["items"]]
    assert urls == ["https://naver.me/s", "https://naver.me/bread"]


def test_missing_connect_links_are_queued_only_when_enabled(sqlite_db, tmp_path, monkeypatch):
    import sqlite3

    reg = tmp_path / "naver_connect_links.csv"
    reg.write_text("상품명,스토어명,판매가,쇼핑커넥트 링크,키워드\n영주사과 홍로 2kg,햇살품은사과,22900,https://naver.me/s,사과\n",
                   encoding="utf-8-sig")
    db = tmp_path / "sc.sqlite3"
    monkeypatch.setenv("NAVER_CONNECT_REGISTRY_CSV", str(reg))
    monkeypatch.setattr("app.services.affiliate.naver_shopping_connect.DB_PATH", db)
    svc = ChatService(sqlite_db, shopping=FakeShopping(items=[]), recipe_chat=RecipeChat(statement_factory=str))
    monkeypatch.delenv("SC_REQUEST_QUEUE", raising=False)
    svc.handle(None, message="과메기 추천해줘")
    assert not db.exists()
    monkeypatch.setenv("SC_REQUEST_QUEUE", "1")
    svc.handle(None, message="과메기 추천해줘")
    svc.handle(None, message="과메기 추천해줘")
    svc.handle(None, message="사과 추천해줘")          # 링크가 있으면 쌓지 않는다
    svc.handle(None, message="막걸리 추천해줘")        # 주류는 쌓지 않는다
    rows = sqlite3.connect(db).execute("select keyword, hit_count, status from sc_link_requests").fetchall()
    assert rows == [("과메기", 2, "open")]


def test_affiliate_results_start_with_a_clear_disclosure(sqlite_db):
    """쿠팡 파트너스 경제적 이해관계 표시 가이드(#160): '광고'·명확한 문구를 응답 맨 위에 (링크 아래만은 위반)."""
    items = [{"product_name": "아삭달콤 햇사과 10kg", "price": 33900, "product_url": "https://www.coupang.com/a",
              "platform_name": "coupang", "is_coupang": True}]
    res = ChatService(sqlite_db, shopping=FakeShopping(items=items), recipe_chat=RecipeChat(statement_factory=str)).handle(
        None, message="사과 추천해줘")
    first = res["blocks"][0]
    assert first["type"] == "notice" and first["data"]["affiliate"] is True
    assert first["data"]["md"].startswith("**광고** · 이 게시물은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.")
    assert "받을 수 있" not in first["data"]["md"]           # 조건부 표현 금지
    assert sum(1 for b in res["blocks"] if b["type"] == "notice" and b["data"].get("affiliate")) == 1


def test_no_disclosure_when_nothing_affiliate_is_shown(sqlite_db):
    items = [{"product_name": "아삭달콤 햇사과 10kg", "price": 33900, "product_url": "https://shop.example/a",
              "platform_name": "naver"}]
    res = ChatService(sqlite_db, shopping=FakeShopping(items=items), recipe_chat=RecipeChat(statement_factory=str)).handle(
        None, message="사과 추천해줘")
    assert not any(b["type"] == "notice" and b["data"].get("affiliate") for b in res["blocks"])


def test_search_words_are_shopping_even_inside_a_recipe_conversation():
    """2026-11-04 실제 화면: 레시피 대화 중 '사과를 검색해줘'가 '무엇을 원하시는지 모르겠어요'로 빠졌다."""
    from app.services.chat.service import _looks_like_shopping
    assert _looks_like_shopping("사과를 검색해줘") and _looks_like_shopping("사과 찾아줘") and _looks_like_shopping("한우 주문")
    assert not _looks_like_shopping("김치찌개 레시피 찾아줘")      # 레시피 요청은 레시피로
    assert not _looks_like_shopping("3인분으로 바꿔 줘") and not _looks_like_shopping("버터 50g 있어요")
    assert shopping_terms("사과를 검색해줘") == ("사과", ["사과"])


def test_other_choice_reason_never_compares_totals_of_different_amounts():
    """2026-11-04 실제 화면: '10kg 68,900원' 가성비 상품보다 '중량 미표기 12,800원'이 '56,100원 저렴'으로 나왔다."""
    from app.services.chat.explain import _alt_text
    ref = {"role": "value", "per100g": 689, "weight_g": 10000, "price": 68900, "total": 68900}
    assert "저렴" not in _alt_text({"title": "못난이사과", "price": 12800, "total": 12800}, ref)
    assert "100g당" not in _alt_text({"title": "못난이사과", "price": 12800, "total": 12800}, ref)
    assert _alt_text({"per100g": 1790, "weight_g": 1000, "price": 17900}, ref) == "100g당 1,790원으로 가성비 상품보다 100g당 1,101원 비싸요"


def test_blemished_and_gift_wording_are_shown_as_seller_claims():
    """2026-11-04 실제 상품: '선물용 꿀사과 흠과, 가정용 혼합 10kg' — '선물 포장'이 아니라 선물용 표기, 흠과 표기도 알린다."""
    from app.services.chat.explain import seller_claims
    assert seller_claims("건강을 담은 장군이네 경북 청송 가정용 선물용 꿀사과 흠과, 1개, 가정용 혼합 10kg") == [
        "선물용·세트 표기", "흠과·못난이 표기"]


def test_site_hides_connect_links_by_default(sqlite_db, tmp_path, monkeypatch):
    """2026-11-04 네이버 회신: 자체 웹/앱 사용자에게 쇼핑커넥트 링크를 보여 주는 것은 정책상 허용되지 않는다 —
    NAVER_CONNECT_ON_SITE=1 이 아니면 목록·안내·발급 요청 모두 없다 (블로그용 등록부 점검은 그대로)."""
    from app.services.chat.service import connect_links, registry_links

    reg = tmp_path / "naver_connect_links.csv"
    reg.write_text("상품명,스토어명,판매가,쇼핑커넥트 링크,키워드\n영주사과 홍로 2kg,햇살품은사과,22900,https://naver.me/s,사과\n",
                   encoding="utf-8-sig")
    monkeypatch.setenv("NAVER_CONNECT_REGISTRY_CSV", str(reg))
    monkeypatch.delenv("NAVER_CONNECT_ON_SITE", raising=False)
    monkeypatch.setenv("SC_REQUEST_QUEUE", "1")
    db = tmp_path / "sc.sqlite3"
    monkeypatch.setattr("app.services.affiliate.naver_shopping_connect.DB_PATH", db)
    assert connect_links(["사과"]) == [] and [r["url"] for r in registry_links(["사과"])] == ["https://naver.me/s"]
    apple = [{"product_name": "경북 부사 사과 3kg", "price": 19900, "product_url": "https://www.coupang.com/a",
              "platform_name": "coupang"}]
    svc = ChatService(sqlite_db, shopping=FakeShopping(items=apple), recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message="사과 추천해줘")
    titles = [i["title"] for b in res["blocks"] if b["type"] == "product_list" for i in b["data"]["items"]]
    assert titles == ["경북 부사 사과 3kg"]
    empty = ChatService(sqlite_db, shopping=FakeShopping(items=[]), recipe_chat=RecipeChat(statement_factory=str))
    res = empty.handle(None, message="과메기 추천해줘")
    assert "쇼핑커넥트" not in md(res)
    assert not db.exists()                                  # 사이트에 안 쓰는 링크를 대화 검색으로 요청하지 않는다


def _search_block(res):
    return next((b["data"] for b in res["blocks"] if b["type"] == "search_links"), None)


def test_naver_search_links_follow_the_request_and_the_picks(sqlite_db):
    """2026-11-04: 고객 편의용 네이버쇼핑 '검색' 링크 (제휴 아님) — 상품어 · 고른 후보의 중량 · 가정용/선물 용도로 최대 3개.
    추천 카드보다 조용한 별도 블록(search_links)으로 내려 보낸다."""
    from urllib.parse import quote

    from app.services.chat.service import NAVER_SEARCH_URL, naver_search_links

    apple = [{"product_name": "경북 부사 사과 3kg 가정용", "price": 19900, "product_url": "https://www.coupang.com/a",
              "platform_name": "coupang", "is_coupang": True}]
    svc = ChatService(sqlite_db, shopping=FakeShopping(items=apple), recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message="사과 추천해줘")
    block = _search_block(res)
    assert block["title"] == "네이버쇼핑에서 직접 찾아보기" and block["badge"] == "제휴 아님 · 수수료 없음"
    assert [(l["query"], l["url"]) for l in block["links"]] == [
        (q, NAVER_SEARCH_URL + quote(q)) for q in ("사과", "사과 3kg", "사과 가정용")]
    assert all(l["check"] for l in block["links"])
    types = [b["type"] for b in res["blocks"]]
    assert types.index("product_list") < types.index("search_links")
    assert "수수료 없음" not in md(res)                       # 본문 글씨로는 나오지 않는다
    assert [q for q, _ in naver_search_links("사과", "부모님 선물용 사과")] == ["사과", "사과 선물세트"]
    assert naver_search_links("와인", "와인 추천해줘") == [] and naver_search_links("", "") == []


def test_naver_search_links_also_when_coupang_has_nothing_and_can_be_switched_off(sqlite_db, monkeypatch):
    svc = ChatService(sqlite_db, shopping=FakeShopping(items=[]), recipe_chat=RecipeChat(statement_factory=str))
    block = _search_block(svc.handle(None, message="과메기 추천해줘"))
    assert block and block["links"][0]["url"].startswith("https://search.shopping.naver.com/search/all?query=")
    monkeypatch.setenv("NAVER_SEARCH_LINKS", "0")
    assert _search_block(svc.handle(None, message="과메기 추천해줘")) is None
