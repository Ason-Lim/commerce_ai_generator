"""2026-11-22 창 3-B '내 보관함' — 최근 검색(여러 대화 세션) · 관심 상품 · 기록 지우기."""

from __future__ import annotations

import uuid

from app.services.chat.service import ChatService
from app.services.recipe_chat.service import RecipeChat
from tests.services.chat.test_evoo_retry_2026_11_22 import ByQuery, _cp


def svc(db):
    shop = ByQuery({"사과": [_cp("부사 사과 2kg", 19900, 1), _cp("홍로 사과 3kg", 25900, 2)],
                    "귤": [_cp("제주 감귤 5kg", 15900, 3), _cp("하우스 귤 2kg", 12900, 4)]})
    return ChatService(db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))


def test_recent_across_sessions_and_forget(sqlite_db):
    s = svc(sqlite_db)
    owner = str(uuid.uuid4())
    a = s.handle(None, message="사과")["session_id"]
    b = s.handle(None, message="귤")["session_id"]               # 새 대화
    view = s.shelf_view(owner, [b, a])
    assert {r["query"] for r in view["recent"]} == {"사과", "귤"}
    assert all(c["go"].startswith(f"/go/{r['session_id']}/k/") for r in view["recent"] for c in r["cards"])
    key = view["recent"][0]["cards"][0]["key"]
    assert s.set_saved(owner, view["recent"][0]["session_id"], key, True)["ok"]
    assert len(s.shelf_view(owner, [a, b])["saved"]) == 1

    out = s.forget(owner, [a, b])
    assert out["ok"] and out["saved"] and out["sessions"] >= 2
    after = s.shelf_view(owner, [a, b])
    assert after == {"saved": [], "recent": [], "tickets": []}   # 11-23 창 4 ③: 문의 칸


def test_bad_ids_are_ignored(sqlite_db):
    s = svc(sqlite_db)
    assert s.shelf_view("x", ["../etc", "nope"]) == {"saved": [], "recent": [], "tickets": []}
    assert s.forget("x", ["nope"])["ok"]


def test_forget_route_refuses_settings(sqlite_db):
    """기록 지우기 요청에 설정 값을 실을 자리가 없다 (extra=forbid)."""
    import pytest
    from pydantic import ValidationError

    from app.api.chat_routes import ShelfIn

    with pytest.raises(ValidationError):
        ShelfIn(owner=None, sessions=[], avoid=["땅콩"])


def test_other_owner_cannot_see_or_clear(sqlite_db):
    """로그인 없는 보관함 — 무작위 주인 값이 곧 접근 수단. 다른 값·빠진 값으로는 보이지도 지워지지도 않는다."""
    s = svc(sqlite_db)
    a_owner, b_owner = str(uuid.uuid4()), str(uuid.uuid4())
    sid = s.handle(None, message="사과")["session_id"]
    key = s.shelf_view(a_owner, [sid])["recent"][0]["cards"][0]["key"]
    assert s.set_saved(a_owner, sid, key, True)["ok"]
    assert s.shelf_view(b_owner, [])["saved"] == []
    assert s.shelf_view(None, [])["saved"] == [] and s.shelf_view("", [])["saved"] == []
    assert s.shelf_view("not-a-uuid", [])["saved"] == []
    s.forget(b_owner, [])                       # 다른 주인 값으로 지우기
    s.forget(None, [])                          # 주인 값 빠짐
    assert len(s.shelf_view(a_owner, [])["saved"]) == 1


def test_forget_clears_every_listed_session(sqlite_db):
    """이 브라우저가 쓴 대화 세션 여러 개를 한 번에 — 이전 세션의 최근 검색도 지워진다."""
    s = svc(sqlite_db)
    owner = str(uuid.uuid4())
    sids = [s.handle(None, message=q)["session_id"] for q in ("사과", "귤", "사과")]
    assert len(s.shelf_view(owner, sids)["recent"]) == 2
    assert s.forget(owner, sids)["sessions"] >= 3
    assert s.shelf_view(owner, sids)["recent"] == []
