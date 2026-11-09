"""골든 비교 (2026-11-03 p29): 예산 답변 턴·관심 상품 비교 턴의 화면 블록이 공통 서비스 이전 후에도 글자 그대로 같다.

골든 파일은 이전 전 코드로 만든 것이다 (fixtures/golden_reselect.json).  다시 만들 때만 UPDATE_GOLDEN=1.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from app.services.chat.service import ChatService
from app.services.recipe_chat.service import RecipeChat
from tests.services.chat.conftest import FakeShopping

GOLDEN = Path(__file__).parent / "fixtures" / "golden_reselect.json"
OWNER = "11111111-2222-4333-8444-555555555555"


def cp(n, name, price, *, rocket=None, free=None, ship=None):
    return {"product_name": name, "price": price, "shipping_fee": ship,
            "product_url": f"https://www.coupang.com/vp/products/{n}",
            "platform_name": "쿠팡", "is_coupang": True, "is_rocket": rocket, "is_free_shipping": free}


BEEF = [
    cp(1, "한우 1++ 등심 구이용 300g", 39000, rocket=True, free=True),
    cp(2, "한우 등심 500g 냉장", 52000, ship=3000),
    cp(3, "호주산 소고기 등심 1kg", 45000, free=True),
    cp(4, "한우 등심 선물세트 1.2kg 보자기 포장", 129000),
    cp(5, "미국산 척아이롤 2kg 대용량", 59000),
]
APPLE = [cp(11, "부사 사과 5kg", 30000), cp(12, "꿀사과 3kg", 21000, rocket=True)]


def _norm(obj, sid):
    text = json.dumps(obj, ensure_ascii=False, sort_keys=True)
    text = re.sub(r"\d{2}/\d{2} \d{2}:\d{2}", "<MM/DD hh:mm>", text)     # 담은·확인 시각 (시계에 따라 다름)
    return json.loads(text.replace(sid, "<SID>").replace(OWNER, "<OWNER>"))


def _svc(db, items):
    return ChatService(db, shopping=FakeShopping(items=items), recipe_chat=RecipeChat(statement_factory=str))


def scenarios(db) -> dict:
    out = {}
    for name, answer in (("budget_5man", "5만원 이하요"), ("budget_miss", "1만원 이하요"), ("budget_none", "예산 없어요"),
                         ("budget_range", "10만원대요")):
        s = _svc(db, BEEF)
        first = s.handle(None, message="소고기 등심 추천")
        sid = first["session_id"]
        out[name] = _norm(s.handle(sid, message=answer), sid)
    s = _svc(db, BEEF)
    res = s.handle(None, message="소고기 등심 추천", owner=OWNER)
    for c in [b for b in res["blocks"] if b["type"] == "product_list"][0]["data"]["items"][:3]:
        s.set_saved(OWNER, res["session_id"], c["key"], True)
    s.shopping = FakeShopping(items=APPLE)
    res2 = s.handle(res["session_id"], message="사과 추천", owner=OWNER)
    first_apple = [b for b in res2["blocks"] if b["type"] == "product_list"][0]["data"]["items"][0]
    s.set_saved(OWNER, res2["session_id"], first_apple["key"], True)
    cmp = s.handle(None, message="관심 상품 비교해줘", owner=OWNER)
    out["saved_compare"] = _norm(cmp, cmp["session_id"])
    empty = _svc(db, BEEF).handle(None, message="관심 상품 보여줘", owner="99999999-2222-4333-8444-555555555555")
    out["saved_empty"] = _norm(empty, empty["session_id"])
    return out


def test_reselect_turns_match_golden(sqlite_db):
    got = scenarios(sqlite_db)
    if os.environ.get("UPDATE_GOLDEN") == "1":
        GOLDEN.write_text(json.dumps(got, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    want = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert set(got) == set(want)
    for name in want:
        assert got[name] == want[name], name
