"""창 3-D ② 기록 보강 (2026-11-23) — 지표 분모 '보여 준 것' 한 줄 (kind=served).

설계 claude/improve_without_training_proposal_2026-11-22.md §7: 최종 0건·후보 1~2개·자동 다시 찾기 비율의 분모 =
고객 상품 검색 요청(운영자 시험 제외), 쿠팡 호출 수·응답 시간·AI 호출 수. 웹 대화는 search_log·impression_log 를
쓰지 않아 분모가 없었다. 손님 문장은 남기지 않는다.
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.services.chat import miss_signals as M, turn_metrics as TM


def rows(tmp, kind="served"):
    return [r for p in tmp.glob("*.jsonl") for r in map(json.loads, p.read_text(encoding="utf-8").splitlines())
            if r["kind"] == kind]


@pytest.fixture
def signals(tmp_path, monkeypatch):
    monkeypatch.setenv("MISS_SIGNALS", "on")
    monkeypatch.setenv("MISS_SIGNALS_DIR", str(tmp_path))
    M._LAST.clear()
    return tmp_path


def plist(n, **data):
    return {"type": "product_list", "data": {"items": [{"title": f"상품{i}"} for i in range(n)], **data}}


def test_shown_counts_by_slot():
    blocks = [plist(3), plist(4, title="다른 후보 4개", collapsed=True),
              plist(2, title="다른 검색어로 찾은 추가 후보 2개"), {"type": "search_links", "data": {}}]
    assert M.shown_counts(blocks) == {"n_main": 3, "n_collapsed": 4, "n_extra": 2, "search_links": True}


def test_served_row_has_counts_but_no_sentence(signals):
    m, tok = TM.start()
    TM.bump("coupang_calls")
    TM.bump("coupang_calls")
    TM.flag("refetch_tried")
    TM.stop(tok)
    m["ms"] = 830
    M.served("abcdef1234567890", {"stage": "shopping", "blocks": [plist(2)]}, m, internal=True)
    (r,) = rows(signals)
    assert r["sid"] == "abcdef12" and r["product"] and r["few"] and not r["zero"]
    assert (r["coupang_calls"], r["refetch_tried"], r["refetch_found"], r["ms"], r["internal"]) == (2, True, False, 830, True)
    assert "text" not in r and "words" not in r                 # 손님 문장 없음


def test_zero_and_non_product_turns(signals):
    M.served("s", {"stage": "shopping", "blocks": [{"type": "text", "data": {"text": "찾지 못했어요"}}]}, {})
    M.served("s", {"stage": "recipe_card", "blocks": [{"type": "recipe_card", "data": {}}]}, {})
    M.served("s", {"stage": "shopping", "blocks": [{"type": "notice", "data": {"text": "'사과' 상품을 불러오지 못했어요."}}]}, {})
    zero, recipe, failed = rows(signals)
    assert zero["product"] and zero["zero"] and not zero["few"] and not zero["failed"]
    assert failed["failed"] and not failed["zero"]
    assert not recipe["product"] and not recipe["zero"]


def test_counting_only_inside_a_turn():
    TM.bump("coupang_calls")                                     # 차례 밖 — 아무 일 없음
    m, tok = TM.start()
    TM.bump("ai_calls")
    TM.stop(tok)
    TM.bump("ai_calls")
    assert m["ai_calls"] == 1


def test_off_switch(signals, monkeypatch):
    monkeypatch.setenv("MISS_SIGNALS", "off")
    M.served("s", {"stage": "shopping", "blocks": [plist(1)]}, {})
    assert rows(signals) == []


def test_coupang_cache_and_call_are_counted(monkeypatch):
    from app.services import coupang_api as ca

    monkeypatch.setattr(ca, "is_coupang_available", lambda: True)
    monkeypatch.setattr(ca, "_SEARCH_CACHE", {})
    monkeypatch.setattr("app.services.coupang_rate.acquire", lambda: True)

    class R:
        def raise_for_status(self):
            pass

        def json(self):
            return {"data": {"productData": [{"productName": "사과", "productPrice": 1000, "productUrl": "https://link.coupang.com/a"}]}}

    monkeypatch.setattr(ca.requests, "get", lambda *a, **k: R())
    monkeypatch.setattr(ca, "_build_authorization", lambda *a: "x")
    m, tok = TM.start()
    ca.search_coupang_products("사과")
    ca.search_coupang_products("사과")                           # 같은 말 → 캐시
    TM.stop(tok)
    assert (m["coupang_calls"], m["coupang_cache_hits"]) == (1, 1)


def test_ai_usage_is_counted(tmp_path, monkeypatch):
    from app.services.ai import usage

    monkeypatch.setattr(usage, "_conn", lambda: (_ for _ in ()).throw(RuntimeError("시험 — DB 안 씀")))
    m, tok = TM.start()
    usage.record("shop_keyword", "openai:m", 10, 5)
    usage.record("shop_keyword", "openai:m", 0, 0, cached=True)
    TM.stop(tok)
    assert (m["ai_calls"], m["ai_cache_hits"]) == (1, 1)


def test_chat_api_writes_one_served_row_per_turn(signals, sqlite_db, shopping):
    from app.api import chat_routes
    from app.main import app

    app.dependency_overrides[chat_routes.get_chat_service] = lambda: _service(sqlite_db, shopping)
    try:
        c = TestClient(app)
        c.post("/api/chat", json={"message": "사과 추천해줘"})
        c.post("/api/chat", json={"message": "사과 추천해줘"})
    finally:
        app.dependency_overrides.clear()
    got = rows(signals)
    assert len(got) == 2 and all(r["product"] and r["n_main"] >= 1 and isinstance(r["ms"], int) for r in got)
    assert all(r["internal"] is False for r in got)
    text = "".join(p.read_text(encoding="utf-8") for p in signals.glob("*.jsonl"))
    assert "사과 추천해줘" not in [r.get("text") for r in got]
    assert all("text" not in r for r in got) and "served" in text


def _service(db, shopping):
    from app.services.chat.service import ChatService
    from app.services.recipe_chat.service import RecipeChat

    return ChatService(db, shopping=shopping, recipe_chat=RecipeChat(statement_factory=str))


def test_click_slot_extra_vs_main(monkeypatch):
    """판매처 이동 세 갈래 — 추가 후보 칸(more_as 있음) 클릭은 chat_extra 로 남는다."""
    from fastapi import FastAPI

    from app.api import chat_routes

    clicks = []
    monkeypatch.setattr("app.services.analytics_logger.log_product_click", lambda **k: clicks.append(k))

    class Svc:
        def seen_card(self, sid, key):
            return {"url": "https://link.coupang.com/a", "title": "t", "mall": "쿠팡",
                    **({"more_as": "카무트효소"} if key == "b" * 12 else {})}

        def resolve_go_key(self, sid, key):
            return "https://link.coupang.com/a"

    app = FastAPI()
    app.include_router(chat_routes.router)
    app.dependency_overrides[chat_routes.get_chat_service] = lambda: Svc()
    c = TestClient(app)
    sid = "0" * 8 + "-0000-0000-0000-" + "0" * 12
    c.get(f"/go/{sid}/k/{'a' * 12}", follow_redirects=False)
    c.get(f"/go/{sid}/k/{'b' * 12}", follow_redirects=False)
    assert [k["product"]["selected_section"] for k in clicks] == ["chat", "chat_extra"]
