"""2026-11-21 대화 답 피드백 (설계 claude/trend_post_format_feedback_2026-11-20.md §5) — 결정 신호 때 대화당 한 번.

넘어가는 기준: 신호(판매처 이동·♡·마무리 말) + 직전 답이 쇼핑 추천일 때만 묻기, 대화당 한 번, 닫으면 다시 묻지 않음,
값 목록 밖·자유 입력 거부, 원문·IP 미저장(칼럼), 운영자 평가 분리, 공개 응답에 집계 없음, 순위 불변(쇼핑 경로 안 건드림).
"""
from __future__ import annotations

import pytest

from app.services.chat import answer_feedback as afb
from app.services.chat.service import ChatService
from app.services.recipe_chat.service import RecipeChat
from tests.services.chat.conftest import FakeShopping

SHOWN = {"mode": "shopping", "last_items": [{"rank": 1}], "pending": {"kind": "budget", "query": "사과"}}


def test_closing_words():
    for t in ("이걸로 할게요", "이거 살게", "고마워요!", "감사합니다", "주문할게요", "이걸로 할게 ㅎㅎ"):
        assert afb.is_closing(t), t
    for t in ("고마워 근데 배도 찾아줘", "사과 추천", "이걸로 할게 하나 더 보여줘", ""):
        assert not afb.is_closing(t), t


def test_ask_once_per_session_and_only_after_shopping(tmp_path):
    st = afb.AnswerFeedbackStore(tmp_path / "f.sqlite3")
    sid = "00000000-0000-4000-8000-000000000001"
    assert not st.ask(sid, "go", {"mode": "recipe"})
    assert not st.ask(sid, "go", {"mode": "shopping", "last_items": []})
    assert not st.ask(sid, "bogus", SHOWN)
    assert st.ask(sid, "go", SHOWN)
    assert not st.ask(sid, "save", SHOWN)                     # 대화당 한 번
    assert st.record(sid, "bad", ["no_product", "thin"], operator=False)["reasons"] == ["no_product", "thin"]
    st.record(sid, "ok", ["misread"], operator=False)          # 바꾸면 갱신
    view = st.overview()
    assert view["by_signal"][0]["n"] == 1 and view["by_signal"][0]["ok"] == 1
    with pytest.raises(afb.AnswerFeedbackError):
        st.record(sid, "great", [], operator=False)
    with pytest.raises(afb.AnswerFeedbackError):
        st.record(sid, "good", ["no_product"], operator=False)  # 좋음에는 이유 칩 없음
    with pytest.raises(afb.AnswerFeedbackError):
        st.record(sid, "bad", ["직접 쓴 말"], operator=False)
    other = "00000000-0000-4000-8000-000000000002"
    with pytest.raises(afb.AnswerFeedbackError):
        st.record(other, "good", [], operator=False)           # 묻지 않은 대화는 받지 않음
    assert st.ask(other, "save", SHOWN) and st.close(other)
    with pytest.raises(afb.AnswerFeedbackError):
        st.record(other, "good", [], operator=False)           # 닫은 대화는 받지 않음
    cols = set(st.columns("answers")) | set(st.columns("asks"))
    assert not cols & {"ip", "message", "text", "user_agent", "comment"}
    assert set(afb.summary(SHOWN)) == {"query", "budget", "shown"}


def test_operator_answers_are_kept_apart(tmp_path):
    st = afb.AnswerFeedbackStore(tmp_path / "f.sqlite3")
    sid = "00000000-0000-4000-8000-000000000003"
    st.ask(sid, "closing", SHOWN)
    st.record(sid, "good", [], operator=True)
    assert st.overview("customer")["by_signal"][0]["n"] == 0
    assert st.overview("operator")["by_signal"][0]["n"] == 1


def _svc(sqlite_db, tmp_path):
    return ChatService(sqlite_db, shopping=FakeShopping(), recipe_chat=RecipeChat(statement_factory=str),
                       answer_feedback=afb.AnswerFeedbackStore(tmp_path / "f.sqlite3"))


def test_closing_after_recommendation_asks_once_and_does_not_search(sqlite_db, tmp_path):
    svc = _svc(sqlite_db, tmp_path)
    first = svc.handle(None, message="사과")
    calls = len(svc.shopping.calls)
    res = svc.handle(first["session_id"], message="이걸로 할게요")
    assert len(svc.shopping.calls) == calls                     # 쿠팡에서 '이걸로 할게요'를 찾지 않음
    assert res["stage"] == "closing"
    assert [b["type"] for b in res["blocks"]] == ["text", "answer_feedback"]
    again = svc.handle(first["session_id"], message="고마워요")
    assert [b["type"] for b in again["blocks"]] == ["text"]       # 대화당 한 번
    # 같은 대화의 판매처 이동 신호도 다시 묻지 않음
    assert svc.answer_feedback_signal(first["session_id"], "go") == {"ask": False}


def test_thanks_before_any_recommendation_is_not_searched(sqlite_db, tmp_path):
    svc = _svc(sqlite_db, tmp_path)
    res = svc.handle(None, message="고마워")
    assert svc.shopping.calls == [] and res["stage"] == "closing"
    assert all(b["type"] != "answer_feedback" for b in res["blocks"])


def test_go_signal_then_answer(sqlite_db, tmp_path):
    svc = _svc(sqlite_db, tmp_path)
    sid = svc.handle(None, message="사과")["session_id"]
    got = svc.answer_feedback_signal(sid, "go")
    assert got["ask"] is True and got["block"]["type"] == "answer_feedback"
    assert "이름이나 연락처는 입력받지 않습니다" in got["block"]["data"]["note"]
    assert svc.answer_feedback(sid, "bad", ["price_diff"]) == {"ok": True, "rating": "bad", "reasons": ["price_diff"]}
    assert svc.answer_feedback_signal("not-a-session", "go") == {"ask": False}
    assert svc.answer_feedback_signal(sid, "closing") == {"ask": False}          # 화면 신호는 go·save 만


fastapi = pytest.importorskip("fastapi")


def test_api_rejects_extra_keys(sqlite_db, tmp_path):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.api import chat_routes

    svc = _svc(sqlite_db, tmp_path)
    app = FastAPI()
    app.include_router(chat_routes.router)
    app.dependency_overrides[chat_routes.get_chat_service] = lambda: svc
    c = TestClient(app)
    sid = svc.handle(None, message="사과")["session_id"]
    assert c.post("/api/chat/answer-feedback/signal", json={"session_id": sid, "signal": "save"}).json()["ask"] is True
    assert c.post("/api/chat/answer-feedback", json={"session_id": sid, "rating": "bad", "comment": "x"}).status_code == 422
    ok = c.post("/api/chat/answer-feedback", json={"session_id": sid, "rating": "ok", "reasons": ["thin"]})
    assert ok.status_code == 200 and "helpful_rate" not in ok.text and "n" not in ok.json()
    assert c.post("/api/chat/answer-feedback", json={"session_id": sid, "rating": "meh"}).status_code == 400


def test_answers_are_rolled_up_before_purge(tmp_path):
    from datetime import datetime, timezone
    import sqlite3

    clock = {"t": datetime(2025, 1, 10, tzinfo=timezone.utc)}
    st = afb.AnswerFeedbackStore(tmp_path / "f.sqlite3", clock=lambda: clock["t"])
    old = "00000000-0000-4000-8000-000000000009"
    st.ask(old, "go", SHOWN)
    st.record(old, "bad", ["thin"], operator=False)
    clock["t"] = datetime(2026, 2, 1, tzinfo=timezone.utc)
    st.ask("00000000-0000-4000-8000-00000000000a", "save", SHOWN)     # 묻기 기록할 때 1년 지난 것을 접고 지움
    con = sqlite3.connect(tmp_path / "f.sqlite3")
    assert con.execute("SELECT COUNT(*) FROM answers").fetchone()[0] == 0
    assert con.execute("SELECT month, signal, rating, reasons, n FROM answers_rollup").fetchall() == [
        ("2025-01", "go", "bad", "thin", 1)]
