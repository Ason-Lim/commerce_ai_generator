"""2026-11-11: 냉동 상품은 생과와 같은 기준으로 견주지 않고 '냉동 상품 N개 따로 보기'로 나눈다."""
from app.services.chat import explain


def _items():
    mk = lambda n, p: {"product_name": n, "price": p, "shipping_fee": 0, "is_coupang": True,  # noqa: E731
                       "product_url": f"https://shop.example.com/{abs(hash(n)) % 10000}"}
    return [mk("감미인 국내산 딸기 (냉동), 1kg", 7990), mk("논산 설향 딸기 500g", 15900),
            mk("고당도 설향딸기 1kg", 28500), mk("산지직송 딸기 700g", 21900)]


def test_frozen_words():
    for t in ("국내산 딸기 (냉동), 1kg", "급속냉동 블루베리 1kg", "IQF 냉동딸기"):
        assert explain.is_frozen(t), t
    for t in ("무냉동 생딸기 1kg", "비냉동 직송", "냉동실 보관 가능 떡", "냉동 아님 생물 고등어", "설향 딸기 500g"):
        assert not explain.is_frozen(t), t


def _blocks(res, kind):
    return [b for b in res["blocks"] if b.get("type") == kind]


def test_frozen_goes_to_its_own_list(sqlite_db, shopping):
    from app.services.chat.service import ChatService

    shopping.items = _items()
    res = ChatService(sqlite_db, shopping=shopping).handle(None, message="딸기 추천해줘")
    lists = _blocks(res, "product_list")
    frozen = [b for b in lists if (b["data"].get("title") or "").startswith("냉동 상품")]
    assert len(frozen) == 1 and frozen[0]["data"]["collapsed"] is True
    assert frozen[0]["data"]["title"] == "냉동 상품 1개 따로 보기"
    assert [i["title"] for i in frozen[0]["data"]["items"]] == ["감미인 국내산 딸기 (냉동), 1kg"]
    others = [i["title"] for b in lists if b is not frozen[0] for i in b["data"]["items"]]
    assert not any("냉동" in t for t in others)                       # 가성비 등 비교 후보에 없다
    assert "후보 3개" in res["blocks"][1]["data"]["md"] or any("후보 3개" in (b["data"].get("md") or "")
                                                              for b in _blocks(res, "text"))


def test_asking_for_frozen_keeps_them_in_the_comparison(sqlite_db, shopping):
    from app.services.chat.service import ChatService

    shopping.items = _items()
    res = ChatService(sqlite_db, shopping=shopping).handle(None, message="냉동 딸기 추천해줘")
    titles = [(b["data"].get("title") or "") for b in _blocks(res, "product_list")]
    assert not any(t.startswith("냉동 상품") for t in titles)


def test_all_frozen_results_are_not_split(sqlite_db, shopping):
    from app.services.chat.service import ChatService

    shopping.items = [i for i in _items() if "냉동" in i["product_name"]] + [
        {"product_name": "급속냉동 딸기 2kg", "price": 12900, "shipping_fee": 0, "is_coupang": True,
         "product_url": "https://shop.example.com/x"}]
    res = ChatService(sqlite_db, shopping=shopping).handle(None, message="딸기 추천해줘")
    titles = [(b["data"].get("title") or "") for b in _blocks(res, "product_list")]
    assert not any(t.startswith("냉동 상품") for t in titles)


def test_compare_table_leaves_frozen_out():
    from app.services.chat import product_compare

    seen = {"query": "딸기", "at": "11-11", "cards": [
        {"key": "a", "title": "딸기 (냉동) 1kg", "price": 7990, "total": 7990, "frozen": True},
        {"key": "b", "title": "설향 딸기 500g", "price": 15900, "total": 15900},
        {"key": "c", "title": "설향 딸기 1kg", "price": 28500, "total": 28500}]}
    data = product_compare.build("딸기", seen, None, lambda c: f"/go/{c['key']}")
    assert [r["key"] for r in data["rows"]] == ["b", "c"]
    assert any("냉동 상품 1개" in n for n in data["notes"])
