"""쿠팡 API 데이터 저장 줄이기 (2026-11-23 — 쿠팡 답: 오픈 API 약관 제5조 ③ 복제·저장·전송 금지).

사용자 결정: 검색 캐시 10분 · 대화 카드 24시간 · 관심 상품·트렌드 글은 그대로.
설계 claude/coupang_storage_scope_2026-11-23.md §4.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from app.services.chat import card_expiry as CE
from app.services.chat.service import ChatService
from app.services.recipe_chat.service import RecipeChat
from tests.services.chat.conftest import FakeShopping

STATE = {"version": 1, "mode": "shopping", "turns": [],
         "seen": [{"query": "사과", "at": "11/23 10:00", "budget": None,
                   "cards": [{"key": "a" * 12, "rank": 1, "title": "부사 사과 2kg", "price": 19900, "image": "https://x/i.jpg",
                              "url": "https://link.coupang.com/a/1", "mall": "쿠팡"}]}],
         "last_items": [{"rank": 1, "url": "https://link.coupang.com/a/1", "title": "부사 사과 2kg", "mall": "쿠팡"}]}


def test_strip_keeps_only_key_rank_link_and_our_query():
    out = CE.strip(STATE)
    dumped = json.dumps(out, ensure_ascii=False)
    for word in ("부사 사과", "19900", "i.jpg", "쿠팡\""):
        assert word not in dumped
    assert out["seen"][0]["query"] == "사과" and out["seen"][0]["expired"] is True
    assert out["seen"][0]["cards"] == [{"key": "a" * 12, "rank": 1, "url": "https://link.coupang.com/a/1"}]
    assert out["last_items"] == [{"rank": 1, "url": "https://link.coupang.com/a/1"}]
    assert not CE.has_cards(out) and CE.strip(out) == out


def test_is_old_uses_24_hours(monkeypatch):
    now = datetime(2026, 11, 23, 12, tzinfo=timezone.utc)
    assert CE.is_old(now - timedelta(hours=25), now) and not CE.is_old(now - timedelta(hours=23), now)
    assert CE.is_old("2026-11-22 10:00:00", now) and not CE.is_old(None, now)
    monkeypatch.setenv("COUPANG_CARD_HOURS", "48")
    assert not CE.is_old(now - timedelta(hours=25), now)


class _NLU:
    def parse(self, text):
        return {"action_intent": "shopping"}


APPLE = [{"product_name": "부사 사과 2kg", "price": 19900, "product_url": "https://www.coupang.com/vp/products/1",
          "platform_name": "coupang", "is_coupang": True}]


def _svc(db):
    return ChatService(db, shopping=FakeShopping(items=APPLE), nlu_loader=lambda: _NLU(),
                       recipe_chat=RecipeChat(statement_factory=str))


def _age(db, sid, hours):
    with db.write() as conn:
        conn.execute(f"UPDATE recipe_chat_session SET updated_at = datetime('now', '-{hours} hours') WHERE session_id = '{sid}'")


def test_old_conversation_cards_are_stripped_on_load_and_cannot_be_saved(sqlite_db):
    svc = _svc(sqlite_db)
    sid = svc.handle(None, message="사과 추천해줘")["session_id"]
    state, _rev, _ = svc._load(sid)
    key = state["seen"][-1]["cards"][0]["key"]
    assert state["seen"][-1]["cards"][0].get("title")                       # 방금은 그대로
    _age(sqlite_db, sid, 30)
    state, _rev, _ = svc._load(sid)
    assert not CE.has_cards(state) and state["seen"][-1]["cards"][0]["key"] == key
    assert svc.resolve_go_key(sid, key)                                       # 링크 이동은 그대로
    res = svc.set_saved("0" * 8 + "-0000-0000-0000-" + "0" * 12, sid, key, True)
    assert res["ok"] is False and res["error"] == "expired_item"


def test_recent_conversation_keeps_cards(sqlite_db):
    svc = _svc(sqlite_db)
    sid = svc.handle(None, message="사과 추천해줘")["session_id"]
    _age(sqlite_db, sid, 2)
    state, _rev, _ = svc._load(sid)
    assert CE.has_cards(state)


def test_search_cache_default_is_ten_minutes(monkeypatch):
    from app.services import coupang_api
    from app.services.trends import coupang_best

    monkeypatch.delenv("COUPANG_SEARCH_CACHE_MINUTES", raising=False)
    assert coupang_api._cache_minutes() == 10.0
    assert coupang_best.TTL_SECONDS == 600


def test_weak_match_signal_keeps_counts_not_product_names(tmp_path, monkeypatch):
    from app.services.chat import miss_signals

    monkeypatch.setattr(miss_signals, "enabled", lambda: True)
    monkeypatch.setattr(miss_signals, "_dir", lambda: tmp_path)
    resp = {"stage": "shopping", "blocks": [{"type": "product_list", "data": {"items": [
        {"product_name": "한일식품 본고장 홍게라면 나베 127g"}, {"product_name": "청정원 쉐프의 치킨스톡"}]}}]}
    miss_signals.observe("s1", "최강록 셰프 라면 추천", resp)
    dumped = "".join(f.read_text(encoding="utf-8") for f in tmp_path.glob("*.jsonl"))
    assert "weak_match" in dumped and "홍게라면" not in dumped and "치킨스톡" not in dumped
