"""KAMIS 공공 시세 참고 (2026-11-02): 단위를 맞출 수 있을 때만 견주고, 순위에는 쓰지 않는다."""
from __future__ import annotations

from app.services.chat import explain
from app.services.public_price import kamis

RAW = {"error_code": "000", "price": [
    {"product_cls_code": "01", "category_name": "축산물", "productName": "소/등심(1++등급)", "unit": "100g",
     "dpr1": "16,886", "lastest_day": "2026-10-29"},
    {"product_cls_code": "01", "category_name": "축산물", "productName": "돼지/삼겹살", "unit": "100g",
     "dpr1": "2,847", "lastest_day": "2026-10-29"},
    {"product_cls_code": "01", "category_name": "과일류", "productName": "사과/홍로", "unit": "10개",
     "dpr1": "22,056", "lastest_day": "2026-10-30"},
    {"product_cls_code": "02", "category_name": "과일류", "productName": "사과/후지", "unit": "10kg",
     "dpr1": "52,300", "lastest_day": "2026-10-30"},
    {"product_cls_code": "02", "category_name": "과일류", "productName": "사과/시나노골드", "unit": "10kg",
     "dpr1": "39,320", "lastest_day": "2026-10-30"},
    {"product_cls_code": "01", "category_name": "축산물", "productName": "계란/XL10구(일반란)", "unit": "10구",
     "dpr1": "4,209", "lastest_day": "2026-10-29"},
    {"product_cls_code": "01", "category_name": "축산물", "productName": "계란/XL30구(일반란)", "unit": "30구",
     "dpr1": "6,664", "lastest_day": "2026-10-29"},
]}
ROWS = kamis.parse(RAW)


def ref(title, price, weight=None):
    return kamis.reference({"title": title, "price": price, "weight_g": weight}, ROWS)


def test_count_units_are_not_used_and_weight_units_are_normalised():
    assert all(r["measure"] in ("g", "구") for r in ROWS)          # 사과/홍로 10개 는 빠진다
    assert kamis.unit_amount("10kg") == (10000, "g") and kamis.unit_amount("1L") == (1000, "ml")
    assert kamis.unit_amount("1포기") is None


def test_same_cut_and_grade_is_compared_per_100g():
    r = ref("한우 1++등급 등심 300g 구이용", 45000, 300)
    assert (r["cls"], r["ref"], r["own"], r["pct"]) == ("소매", 16886, 15000, -11)
    assert "100g당 16,886원" in kamis.line(r) and "11% 낮아요" in kamis.line(r)


def test_beef_without_a_cut_or_processed_goods_get_no_reference():
    assert ref("한우 선물 세트 1++ 투뿔", 598000, None) is None
    assert ref("사과즙 30포", 25000, None) is None
    assert ref("두바이 쫀득 쿠키 50g", 3900, 50) is None


def test_unknown_variety_never_mixes_different_varieties():
    assert ref("영주사과 홍로 2kg", 22900, 2000) is None           # 도매에 홍로 없음, 후지·시나노골드를 섞지 않음
    r = ref("세척사과 햇 부사 2kg", 11900, 2000)                    # 부사 = 후지
    assert r["cls"] == "도매" and r["kinds"] == ["후지"] and "도매가라" in kamis.line(r)


def test_egg_pack_size_is_matched():
    r = ref("무항생제 특란 30구", 9900)
    assert r["kinds"] == ["XL30구(일반란)"] and r["measure"] == "구" and r["ref"] == 222


def test_annotate_adds_a_line_after_choose_without_changing_order():
    cards = [explain.enrich({"title": t, "price": p, "shipping_fee": 0, "total": p, "url": f"https://x/{n}"}, {})
             for n, (t, p) in enumerate([("국내산 한돈 삼겹살 500g", 13900), ("한돈 삼겹살 1kg", 30000)])]
    for n, c in enumerate(cards, 1):
        c["rank"] = n
    picked = explain.choose(cards)
    before = [(c["title"], c["role"]) for c in picked["picks"]]
    kamis.annotate(picked["picks"], ROWS)
    assert [(c["title"], c["role"]) for c in picked["picks"]] == before
    lines = [w for c in picked["picks"] for w in c["why"] if w["basis"] == "public"]
    assert len(lines) == 2 and all("KAMIS 소매 시세" in w["text"] for w in lines)


def test_switch_off(monkeypatch):
    monkeypatch.setenv("KAMIS_REFERENCE", "0")
    c = {"title": "한돈 삼겹살 500g", "price": 13900, "weight_g": 500, "why": []}
    kamis.annotate([c], ROWS)
    assert c["why"] == []


def test_a_cut_kamis_does_not_list_is_not_compared():
    rows = kamis.parse({"price": [
        {"product_cls_code": "01", "productName": "수입 소고기/갈비(호주산)", "unit": "100g", "dpr1": "4,425", "lastest_day": "2026-10-29"},
        {"product_cls_code": "01", "productName": "수입 소고기/갈비살(호주산)", "unit": "100g", "dpr1": "5,947", "lastest_day": "2026-10-29"}]})
    assert kamis.reference({"title": "호주산 소고기 척아이롤 1kg", "price": 29900, "weight_g": 1000}, rows) is None
    r = kamis.reference({"title": "호주산 소고기 갈비살 1kg", "price": 45900, "weight_g": 1000}, rows)
    assert r["kinds"] == ["갈비살(호주산)"]
