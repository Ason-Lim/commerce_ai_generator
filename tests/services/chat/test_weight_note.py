"""2026-11-11: 상세페이지를 열기 전에 알 수 있게 — 중량 옵션·증정분 안내."""
from app.services.chat import explain, product_compare


def test_option_list_says_there_are_weight_options():
    note = explain.weight_note("제주 감귤 2kg 5kg 10kg 선택")
    assert note == {"kind": "options", "label": "중량 옵션이 있어요", "detail": "2kg · 5kg · 10kg"}


def test_bonus_amounts_are_told_apart_from_options():
    cases = {
        "양파 3kg+1kg": "3kg + 1kg 증정",
        "사과 5kg (+500g 증정)": "5kg + 500g 증정",
        "고구마 10kg 1kg 증정": "10kg + 1kg 증정",
        "증정 1kg 포함 감자 5kg": "5kg + 1kg 증정",
        "한우 불고기 500g 1+1": "1+1 구성",
    }
    for title, detail in cases.items():
        assert explain.weight_note(title) == {"kind": "bonus", "label": "증정분이 있어요", "detail": detail}, title
        assert explain.parse_weight(title)["weight"] is None, title          # 증정 조건을 모르니 100g당 계산 안 함


def test_plain_weights_get_no_note():
    for title in ("삼겹살 1kg 냉동", "한돈 삼겹살 500g x 2팩", "2026년 햇사과 5kg", "우유 900mL"):
        assert explain.weight_note(title) is None, title


def test_card_carries_the_note_and_no_per100g():
    card = explain.enrich({"title": "감귤 2kg 5kg 10kg", "price": 19900, "total": 19900}, {})
    assert card["weight_note"]["label"] == "중량 옵션이 있어요" and card["per100g"] is None
    card = explain.enrich({"title": "한우 불고기 500g 1+1", "price": 29900, "total": 29900}, {})
    assert card["weight_note"]["label"] == "증정분이 있어요" and card["per100g"] is None


def test_compare_table_says_options_and_bonus_instead_of_unknown_size():
    seen = {"query": "감귤", "at": "11-11 11:00", "cards": [
        {"key": "a", "title": "감귤 2kg 5kg 10kg", "price": 19900, "total": 19900},
        {"key": "b", "title": "감귤 3kg+1kg", "price": 15900, "total": 15900},
        {"key": "c", "title": "감귤 5kg", "price": 17900, "total": 17900},
        {"key": "d", "title": "감귤 한 상자", "price": 12900, "total": 12900},
    ]}
    data = product_compare.build("감귤", seen, None, lambda c: f"/go/{c['key']}")
    rows = {r["key"]: r for r in data["rows"]}
    assert rows["a"]["weight_note"]["kind"] == "options" and rows["a"]["per100g"] is None
    assert rows["b"]["weight_note"]["kind"] == "bonus" and rows["b"]["pack"] is None and rows["b"]["per100g"] is None
    assert rows["c"]["weight_note"] is None and rows["c"]["per100g"] == 358
    notes = " ".join(data["notes"])
    assert "용량이 없는 1개" in notes and "중량 옵션이 있는 1개" in notes and "증정분이 있는 1개" in notes


def test_korean_right_after_the_unit_is_still_read():
    assert explain.parse_weight("감귤 만다린 4kg내외 수입")["weight"] == 4000
    assert explain.parse_weight("사과 10kg박스")["weight"] == 10000


def test_db_fallback_uses_the_chat_rule():
    """예비 경로(app/main.py)도 채팅과 같은 규칙 — 예전엔 '여러 중량 중 마지막 값'(2kg 1kg 350g → 350g)을 썼다."""
    from app import main

    assert main.estimate_weight_grams("못난이 딸기 2kg 1kg 350g") == 0
    assert main.calculate_price_per_100g({"product_name": "못난이 딸기 2kg 1kg 350g", "price": 8400}) == 0
    assert main.weight_note("못난이 딸기 2kg 1kg 350g")["label"] == "중량 옵션이 있어요"
    assert main.calculate_price_per_100g({"product_name": "감귤 4kg내외", "price": 19580}) == 489.5
    assert main.calculate_price_per_100g({"product_name": "딸기 500g / 1kg", "price": 1, "unit_price_per_kg": 9000}) == 900
