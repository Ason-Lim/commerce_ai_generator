"""셀러 센터 문의 ⑤ (창 5, 2026-11-25) — 규칙 분야 판단 · 안내문 · 사람 필수 티켓 · 격리 · 개인정보 가림."""

from __future__ import annotations

import os

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

os.environ.setdefault("CORPMALL_KEY", Fernet.generate_key().decode())

from app.services.corpmall import store as corp  # noqa: E402
from app.services.cs import tickets  # noqa: E402
from app.services.seller import chat  # noqa: E402
from app.services.seller import store as sel  # noqa: E402

IP = "1.1.1.1"
H = {"X-Access-Token": "test-token"}


@pytest.fixture
def eng(tmp_path, monkeypatch):
    monkeypatch.setenv("CS_DIR", str(tmp_path / "cs"))
    monkeypatch.setenv("OPERATOR_NOTIFY", "off")
    corp.reset_limits()
    e = sel.engine()
    with e.begin() as c:
        for t in (sel.t_event, sel.t_key, sel.t_seller):
            c.execute(t.delete())
    return e


def _seller(eng, name="가농장"):
    s = sel.create_seller(eng, name=name, kind="direct", contact={"name": "김", "email": "k@a.kr"}, by="operator")
    sel.set_status(eng, s["seller_id"], "active", by="operator", reason="ok")
    return s, sel.issue_key(eng, s["seller_id"], by="operator")["code"]


@pytest.mark.parametrize(
    "text,topic",
    [
        ("이번 달 이용료 감면 가능할까요", "fee"),
        ("세금계산서는 언제 나오나요", "fee"),
        ("입점 승인 언제 되나요", "status"),
        ("계약 해지하고 싶어요", "status"),
        ("초대 코드를 잃어버렸어요", "account"),
        ("발주서 엑셀에 송장 칸이 없어요", "orders"),
        ("반려 이유가 뭔가요", "review"),
        ("품절 표시는 어떻게 하나요", "listing"),
        ("스마트스토어 상품 가져오기 되나요", "import"),
        ("손님이 먹고 배탈이 났대요", "food_safety"),
        ("안녕하세요 그냥 궁금한게 있어요", "other"),
    ],
)
def test_classify(text, topic):
    assert chat.classify(text) == topic


@pytest.mark.parametrize("topic", ["status", "fee", "account"])
def test_human_required_topics_open_ticket_and_never_decide(eng, topic):
    _, k = _seller(eng)
    text = {"status": "입점 승인 언제 되나요", "fee": "이용료 환불해 주세요", "account": "초대 코드를 잃어버렸어요"}[
        topic
    ]
    got = chat.ask(eng, k, IP, text)
    assert got["topic"] == topic and got["ticket_id"]
    t = next(x for x in tickets.queue() if x["id"] == got["ticket_id"])
    assert t["domain"] == chat.TICKET[topic] and t["human"] is True and t["status"] == "open"
    # 답 문장이 승인·환불·면제를 약속하지 않는다
    for bad in ("승인했", "환불했", "면제했", "환불해 드릴게", "승인해 드릴게"):
        assert bad not in got["answer"]


def test_howto_topics_answer_without_ticket_then_handoff(eng):
    _, k = _seller(eng)
    got = chat.ask(eng, k, IP, "발주서는 어떻게 만들어요")
    assert got["topic"] == "orders" and got["ticket_id"] is None and got["offer_handoff"] is True
    got = chat.ask(eng, k, IP, "발주서는 어떻게 만들어요", handoff=True)
    assert got["ticket_id"] and got["offer_handoff"] is False


def test_pii_masked_before_ticket(eng):
    _, k = _seller(eng)
    got = chat.ask(eng, k, IP, "손님 010-1234-5678 주소 바꿔 달래요 입점 승인도 궁금", handoff=True)
    t = next(x for x in tickets.queue() if x["id"] == got["ticket_id"])
    assert "010-1234-5678" not in t["summary"] and got["masked"]


def test_isolation_between_sellers(eng):
    _, ka = _seller(eng, "가농장")
    _, kb = _seller(eng, "나수산")
    chat.ask(eng, ka, IP, "이용료 환불해 주세요")
    assert chat.my_asks(eng, kb, IP) == []
    assert len(chat.my_asks(eng, ka, IP)) == 1


def test_reply_visible_to_seller_and_close_only_by_admin(eng):
    from app.main import app

    _, k = _seller(eng)
    tid = chat.ask(eng, k, IP, "입점 승인 언제 되나요")["ticket_id"]
    cl = TestClient(app)
    r = cl.post(
        f"/admin/api/cs/tickets/{tid}/answer", headers=H, json={"text": "서류 확인 뒤 3영업일 안에 알려 드려요"}
    )
    assert r.status_code == 200
    asks = cl.post("/seller/api/asks", json={"key": k}).json()["asks"]
    assert any(m["kind"] == "reply" for m in asks[0]["messages"])
    paths = {r.path for r in app.routes if getattr(r, "path", "").startswith("/seller")}
    assert not any(w in p for p in paths for w in ("answer", "close", "status", "approve"))


def test_open_limit(eng):
    _, k = _seller(eng)
    for i in range(chat.MAX_OPEN):
        chat.ask(eng, k, IP, f"이용료 문의 {i}번째", handoff=False)
    got = chat.ask(eng, k, IP, "이용료 문의 하나 더")
    assert got["ticket_id"] is None and "많아" in got["answer"]
    assert chat.ask(eng, k, IP, "손님이 먹고 배탈이 났대요")["ticket_id"]  # 식품 안전은 한도와 상관없이


def test_emergency_answer_has_no_phone_numbers(eng):
    assert not any(n in chat.ANSWERS["emergency"] for n in ("119", "112", "1393", "109"))
