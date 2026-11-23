"""창 4 ③ — 티켓·사람 필수 대기열·운영자 알림 (2026-11-23). 설계 claude/stage4_design_2026-11-23.md §3."""
from __future__ import annotations

import json
from datetime import datetime

import pytest

from app.services.chat import domain_answers as A
from app.services.chat.service import ChatService
from app.services.cs import bizdays, notify, tickets as T
from app.services.recipe_chat.service import RecipeChat
from tests.services.chat.conftest import FakeShopping

OWNER = "11111111-2222-3333-4444-555555555555"
KST = T.KST


class _NLU:
    def parse(self, text):
        return {"action_intent": "shopping"}


def _svc(db):
    return ChatService(db, shopping=FakeShopping(items=[]), nlu_loader=lambda: _NLU(), recipe_chat=RecipeChat(statement_factory=str))


def _md(res):
    return json.dumps(res["blocks"], ensure_ascii=False)


@pytest.mark.parametrize("text,domain", [("어제 산 굴 먹고 배탈 났어요", "food_safety"), ("죽고 싶어요", "emergency"),
                                         ("내 기록 지워 주세요", "privacy"), ("보상해 주세요", "dispute")])
def test_human_required_turns_create_a_ticket_and_say_so(sqlite_db, text, domain):
    res = _svc(sqlite_db).handle(None, message=text, owner=OWNER)
    q = T.queue()
    assert len(q) == 1 and q[0]["domain"] == domain and q[0]["status"] == "open" and q[0]["human"] is True
    assert q[0]["id"] in _md(res)                                 # 실제 접수됐을 때만 접수 번호·안내
    assert q[0]["owner"] == OWNER and q[0]["summary"] == text


@pytest.mark.parametrize("text", ["개인정보 어떻게 처리해?", "노트북 추천해줘", "배송 언제 와요?", "당뇨 환자가 먹어도 되는 과일 있어?"])
def test_questions_and_guidance_domains_do_not_create_tickets(sqlite_db, text):
    res = _svc(sqlite_db).handle(None, message=text, owner=OWNER)
    assert T.queue() == [] and "접수 번호" not in _md(res) and "운영팀" not in _md(res)


def test_same_conversation_does_not_duplicate_within_an_hour(sqlite_db):
    svc = _svc(sqlite_db)
    sid = svc.handle(None, message="딸기에 곰팡이가 피어 있어요", owner=OWNER)["session_id"]
    svc.handle(sid, message="딸기에 곰팡이가 피어 있어요", owner=OWNER)
    assert len(T.queue()) == 1


def test_operator_alert_has_no_customer_sentence(monkeypatch, tmp_path):
    sent = []
    monkeypatch.setenv("OPERATOR_NOTIFY", "mac")
    monkeypatch.setattr(notify, "_mac", lambda title, body: sent.append((title, body)) or True)
    t = T.create("food_safety", sid="abcd1234", owner=None, summary="굴 먹고 배탈 났어요")
    assert t["alerted"] == "mac" and sent and "굴" not in sent[0][1] and t["id"] in sent[0][1]
    log = (T.store_dir() / "alerts.jsonl").read_text(encoding="utf-8")
    assert t["id"] in log and "굴" not in log


def test_only_admin_functions_close_tickets_and_chat_cannot(sqlite_db):
    """AI 단독 종결 금지 — 대화 쪽 코드에는 상태를 바꾸는 길이 없다(관리자 answer/close 만)."""
    import inspect

    from app.services.chat import service as chat_service

    src = inspect.getsource(chat_service)
    assert "cs_tickets.close" not in src and "cs_tickets.answer" not in src
    svc = _svc(sqlite_db)
    svc.handle(None, message="어제 산 굴 먹고 배탈 났어요", owner=OWNER)
    svc.handle(None, message="이제 괜찮아요 고마워", owner=OWNER)
    assert T.queue()[0]["status"] == "open"
    tid = T.queue()[0]["id"]
    T.answer(tid, "판매처에 전달했고 해당 상품 노출을 멈췄어요.", by="operator")
    view = T.for_owner(OWNER)
    assert view[0]["status"] == "answered" and view[0]["messages"][-1]["kind"] == "reply"
    T.close(tid, by="operator")
    assert T.queue()[0]["status"] == "closed"


def test_auto_followup_after_three_business_days():
    created = datetime(2026, 11, 20, 10, tzinfo=KST)                  # 금
    t = T.create("dispute", sid="s", owner=OWNER, summary="보상해 주세요", now=created)
    assert T.followups(t, datetime(2026, 11, 24, 10, tzinfo=KST)) == []   # 월·화 = 2영업일
    got = T.followups(t, datetime(2026, 11, 25, 11, tzinfo=KST))           # 수 = 3영업일
    assert len(got) == 1 and "결과를 여기에 남길게요" in got[0]["text"]
    assert T.queue()[0]["due_at"].startswith("2026-12-04")                  # 10영업일


def test_bizdays_skip_weekends_and_holidays():
    assert not bizdays.is_bizday(datetime(2026, 12, 25).date())             # 크리스마스
    assert not bizdays.is_bizday(datetime(2027, 2, 8).date())               # 설날 연휴
    assert bizdays.add_bizdays(datetime(2026, 12, 24, 9), 1).date().isoformat() == "2026-12-28"


def test_shelf_shows_tickets_and_forget_unlinks_them(sqlite_db):
    svc = _svc(sqlite_db)
    sid = svc.handle(None, message="어제 산 굴 먹고 배탈 났어요", owner=OWNER)["session_id"]
    shelf = svc.shelf_view(OWNER, [sid])
    assert shelf["tickets"] and shelf["tickets"][0]["label"] == "식품 안전 신고"
    assert svc.shelf_view("99999999-2222-3333-4444-555555555555", [])["tickets"] == []   # 다른 브라우저에는 안 보임
    done = svc.forget(OWNER, [sid])
    assert done["tickets"] == 1 and svc.shelf_view(OWNER, [])["tickets"] == []
    q = T.queue()[0]
    assert q["owner"] is None and q["summary"] == "" and q["status"] == "open"   # 운영자 처리 기록은 남음


def test_prune_clears_summary_after_90_days_and_removes_after_a_year():
    T.create("dispute", sid="a", owner=None, summary="보상", now=datetime(2025, 11, 1, tzinfo=KST))
    T.create("dispute", sid="b", owner=None, summary="보상", now=datetime(2026, 7, 1, tzinfo=KST))
    T.create("dispute", sid="c", owner=None, summary="보상", now=datetime(2026, 11, 20, tzinfo=KST))
    got = T.prune(datetime(2026, 11, 23, tzinfo=KST))
    assert got == {"cleared": 1, "removed": 1}
    assert sorted(t["summary"] for t in T.queue()) == ["", "보상"]


def test_ticket_notice_only_with_a_real_ticket():
    assert "운영팀" not in json.dumps(A.blocks_for("food_safety"), ensure_ascii=False)
    got = json.dumps(A.blocks_for("food_safety", ticket={"id": "T1", "due_at": "2026-11-23T23:59:00"}), ensure_ascii=False)
    assert "T1" in got and "운영팀" in got


def test_admin_routes_require_token_and_close(monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import app

    monkeypatch.setattr("app.admin.auth.expected_token", lambda: "tok")
    t = T.create("dispute", sid="z", owner=None, summary="보상")
    c = TestClient(app)
    assert c.get("/admin/api/cs/tickets").status_code == 401
    h = {"X-Access-Token": "tok"}
    assert c.get("/admin/api/cs/tickets", headers=h).json()["tickets"][0]["id"] == t["id"]
    assert c.post(f"/admin/api/cs/tickets/{t['id']}/answer", json={"text": "확인했어요"}, headers=h).status_code == 200
    assert c.post(f"/admin/api/cs/tickets/{t['id']}/close", headers=h).json()["ticket"]["status"] == "closed"
