"""2026-11-27 사용자: 해외 직구 검색되는 상품은 '로켓배송만' 옆에 '해외직구' 칩."""
from __future__ import annotations

import pytest

from app.services.chat import followup as fu
from tests.services.chat.test_followup_2026_11_22 import OLIVE, chat, chips


@pytest.fixture(autouse=True)
def env(monkeypatch):
    for k in ("DIRECT_IN_CHAT", "SHOPIFY_CATALOG"):
        monkeypatch.delenv(k, raising=False)


@pytest.mark.parametrize("t", ["해외직구", "직구", "해외 직구로 보여줘", "직구 상품", "직구로"])
def test_parse_direct(t):
    assert fu.parse(t) == {"kind": "direct"}


@pytest.mark.parametrize("t", ["올리브유 직구", "직구 올리브유 추천", "해외직구 관세 얼마야?"])
def test_direct_with_item_or_question_is_normal_path(t):
    assert fu.parse(t) is None


def test_chip_sits_right_after_rocket():
    cards = [{"rank": i, "price": 1000 * i, "rocket": i == 1} for i in range(1, 4)]
    out = fu.chips_after(cards, more_left=True, changed=False, direct=True)
    assert out.index("해외직구") == out.index("로켓배송만") + 1


def test_olive_answer_has_direct_chip_and_turn_returns_direct_block(sqlite_db):
    svc, shop = chat(sqlite_db, {"올리브유": OLIVE})
    first = svc.handle(None, message="올리브유")
    assert "해외직구" in chips(first)
    n = len(shop.calls)
    res = svc.handle(first["session_id"], message="해외직구")
    assert len(shop.calls) == n                                        # 쿠팡 새 검색 없음
    blk = [b for b in res["blocks"] if b["type"] == "direct_buy"]
    assert blk and blk[0]["data"]["key"] == "olive_oil" and "해외직구" not in chips(res)


def test_no_chip_for_items_not_in_direct_list(sqlite_db):
    svc, _ = chat(sqlite_db, {"사과": OLIVE})
    assert "해외직구" not in chips(svc.handle(None, message="사과"))


def test_chip_off_with_switch(sqlite_db, monkeypatch):
    monkeypatch.setenv("DIRECT_IN_CHAT", "0")
    svc, _ = chat(sqlite_db, {"올리브유": OLIVE})
    assert "해외직구" not in chips(svc.handle(None, message="올리브유"))
