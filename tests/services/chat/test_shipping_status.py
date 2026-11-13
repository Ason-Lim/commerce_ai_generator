"""2026-11-13 (S5) 배송비 상태 — 무료 '표시'·적힌 배송비를 0원·총액으로 확정하지 않는다."""
from app.services.chat import explain
from app.services.chat.explain import shipping_fields, shipping_note


def test_free_label_is_not_zero_won():
    f = shipping_fields({"price": 10000}, True)
    assert f == {"shipping_status": "free_label", "shipping_fee": None, "total": None}


def test_source_zero_fee_is_treated_as_free_label():
    assert shipping_fields({"price": 10000, "shipping_fee": 0}, None)["shipping_status"] == "free_label"


def test_listed_fee_is_kept_but_not_added_to_total():
    f = shipping_fields({"price": 10000, "shipping_fee": "3000"}, None)
    assert f == {"shipping_status": "fee_label", "shipping_fee": 3000, "total": None}


def test_unknown_and_confirmed():
    assert shipping_fields({"price": 1}, None)["shipping_status"] == "unknown"
    card = {"price": 10000, "shipping_fee": 2500, "total": 12500, "shipping_status": "confirmed"}
    assert shipping_fields(card, None) == {"shipping_status": "confirmed", "shipping_fee": 2500, "total": 12500}


def test_notes():
    assert shipping_note({"shipping_status": "free_label"}) == "무료배송 표시 (조건은 판매처에서 확인)"
    assert shipping_note({"shipping_status": "fee_label", "shipping_fee": 3000}) == "배송비 3,000원 표시 (주문 때 확인)"
    assert shipping_note({}) == "배송비는 미확인"


def test_old_saved_free_card_is_normalized():
    old = {"key": "k", "title": "사과 2kg", "price": 20000, "shipping_fee": 0, "total": 20000, "free_shipping": True}
    new = explain.reweigh(old)
    assert new["shipping_status"] == "free_label" and new["total"] is None and new["shipping_fee"] is None
