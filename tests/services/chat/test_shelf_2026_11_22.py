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
    assert after == {"saved": [], "recent": []}


def test_bad_ids_are_ignored(sqlite_db):
    s = svc(sqlite_db)
    assert s.shelf_view("x", ["../etc", "nope"]) == {"saved": [], "recent": []}
    assert s.forget("x", ["nope"])["ok"]


def test_forget_route_refuses_settings(sqlite_db):
    """기록 지우기 요청에 설정 값을 실을 자리가 없다 (extra=forbid)."""
    import pytest
    from pydantic import ValidationError

    from app.api.chat_routes import ShelfIn

    with pytest.raises(ValidationError):
        ShelfIn(owner=None, sessions=[], avoid=["땅콩"])
