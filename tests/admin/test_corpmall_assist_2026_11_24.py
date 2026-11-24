"""폐쇄몰 임직원 문의 실시간 답 (2026-11-24) — 규칙 → AI(종류만) → 주문 상태 + 매뉴얼 템플릿 → 매뉴얼 밖은 사람."""

from __future__ import annotations

import os
from datetime import datetime

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

os.environ.setdefault("CORPMALL_KEY", Fernet.generate_key().decode())

from app.services.corpmall import assist, manual  # noqa: E402
from app.services.corpmall import store as corp  # noqa: E402

KST = corp.KST
IN = datetime(2026, 12, 3, 10, 0, tzinfo=KST)
SHIP = {"name": "홍길동", "phone": "010-1234-5678", "zipcode": "04524", "address": "서울 중구 세종대로 110", "memo": ""}
MAN = {
    "ship_plan": "2026-12-15",
    "courier": "가나택배",
    "exchange": "받은 날부터 7일 안에 상품 이상이 있으면 교환해 드려요.",
    "contact": "총무팀 사내 메신저",
}


@pytest.fixture
def eng(tmp_path, monkeypatch):
    monkeypatch.setenv("CS_DIR", str(tmp_path / "cs"))
    monkeypatch.setenv("OPERATOR_NOTIFY", "off")
    corp.reset_limits()
    return corp.engine()


def _mall(eng, slug, mode="individual", man=MAN, n=2):
    m = corp.create_mall(
        eng,
        {
            "slug": slug,
            "client": "샘플공사",
            "opens_at": "2026-12-01T09:00",
            "closes_at": "2026-12-10T18:00",
            "delivery_mode": mode,
            "default_item_id": "A",
            "manual": man,
            "items": [{"id": "A", "name": "한과"}, {"id": "B", "name": "감귤"}],
        },
    )
    corp.set_status(eng, m["mall_id"], "open")
    return m, corp.issue_codes(eng, m["mall_id"], n)


@pytest.mark.parametrize(
    "text, intent",
    [
        ("언제 도착해요?", "eta"),
        ("아직 안 왔어요", "eta"),
        ("송장 번호 알려 주세요", "eta"),
        ("받는 주소를 바꾸고 싶어요", "address_change"),
        ("배송지 잘못 넣었어요", "address_change"),
        ("이사해서 주소 변경할게요", "address_change"),
        ("선물을 다른 걸로 바꾸고 싶어요", "item_change"),
        ("잘못 골랐어요", "item_change"),
        ("교환 되나요", "exchange"),
        ("반품하고 싶어요", "exchange"),
        ("상자가 찌그러지고 파손됐어요", "defect"),
        ("하나가 덜 왔어요", "defect"),
        ("먹고 배가 아파요", "food_safety"),
        ("현금으로 주시면 안 되나요", "refund"),
        ("언제까지 골라야 해요?", "deadline"),
        ("어떻게 고르는 거예요", "how_to"),
        ("개인정보 지워 주세요", "privacy"),
        ("담당자 누구예요", "contact"),
    ],
)
def test_rules_read_common_questions(text, intent):
    assert assist.by_rules(text) == intent


def test_ai_only_picks_a_kind_and_low_confidence_goes_to_human():
    assert assist.read_ai(lambda _: {"intent": "eta", "confidence": "high"}, "그거 언제쯤") == "eta"
    assert assist.read_ai(lambda _: {"intent": "eta", "confidence": "low"}, "그거") is None
    assert assist.read_ai(lambda _: {"intent": "food_safety", "confidence": "high"}, "x") is None  # 규칙만
    assert assist.read_ai(lambda _: {"intent": "free_text", "confidence": "high"}, "x") is None
    assert assist.read_ai(lambda _: (_ for _ in ()).throw(RuntimeError()), "x") is None


def test_eta_answers_from_manual_and_order_state(eng):
    m, codes = _mall(eng, "a-eta")
    code = codes[0][1]
    r = corp.ask(eng, "a-eta", code, "언제 와요?", "ip", at=IN)
    assert (
        r["intent"] == "eta"
        and "아직 고르신 선물이 없어요" in r["answer"]
        and "12월 15일" in r["answer"]
        and not r["ticket_id"]
    )
    corp.choose(eng, "a-eta", code, "A", "ip", shipping=SHIP, consent=True, at=IN)
    r = corp.ask(eng, "a-eta", code, "언제 도착해요", "ip", at=IN)
    assert "12월 15일(화) 출고 예정" in r["answer"] and "1~3일" in r["answer"] and r["offer_handoff"]
    oid = corp.orders(eng, m["mall_id"])[0]["order_id"]
    assert corp.set_tracking(eng, m["mall_id"], [{"order_id": oid, "tracking": "1234-5678-9012"}]) == 1
    r = corp.ask(eng, "a-eta", code, "배송 조회", "ip", at=IN)
    assert "가나택배 송장 번호 1234-5678-9012" in r["answer"]
    late = datetime(2026, 12, 25, 10, tzinfo=KST)
    r = corp.ask(eng, "a-eta", code, "아직 안 왔어요", "ip", at=late)
    assert r["ticket_id"] and "늦어지고" in r["answer"]
    corp.mark(eng, m["mall_id"], [oid], "delivered")
    assert "배송 완료" in corp.ask(eng, "a-eta", code, "언제 와요", "ip", at=late)["answer"]


def test_eta_without_ship_plan_does_not_invent_dates(eng):
    _, codes = _mall(eng, "a-noplan", man={})
    code = codes[0][1]
    corp.choose(eng, "a-noplan", code, "A", "ip", shipping=SHIP, consent=True, at=IN)
    r = corp.ask(eng, "a-noplan", code, "언제 도착해요", "ip", at=IN)
    assert "정해지면" in r["answer"] and not any(ch.isdigit() for ch in r["answer"].split("출고일")[0])
    assert "계약에 따라" in corp.ask(eng, "a-noplan", code, "교환 되나요", "ip", at=IN)["answer"]


def test_address_and_item_change_go_to_screen_not_chat(eng):
    m, codes = _mall(eng, "a-change")
    code = codes[0][1]
    corp.choose(eng, "a-change", code, "A", "ip", shipping=SHIP, consent=True, at=IN)
    r = corp.ask(eng, "a-change", code, "주소 바꾸고 싶어요", "ip", at=IN)
    assert r["action"] == "change_address" and "끝 4자리" in r["answer"] and not r["ticket_id"]
    r = corp.ask(eng, "a-change", code, "선물을 다른 걸로 바꿀래요", "ip", at=IN)
    assert r["action"] == "change_item" and not r["ticket_id"]
    corp.export_orders(eng, m["mall_id"], by="t")  # 발송 준비 시작 → 화면에서 못 바꿈
    r = corp.ask(eng, "a-change", code, "배송지 변경해 주세요", "ip", at=IN)
    assert r["action"] is None and r["ticket_id"] and "발송 준비" in r["answer"]
    r = corp.ask(eng, "a-change", code, "선물 바꿀 수 있나요", "ip", at=IN)
    assert r["action"] is None and r["offer_handoff"]


def test_bulk_mall_address_answer(eng):
    _, codes = _mall(eng, "a-bulk", mode="bulk")
    r = corp.ask(eng, "a-bulk", codes[0][1], "받는 주소 바꾸고 싶어요", "ip", at=IN)
    assert "회사로 한꺼번에" in r["answer"]


def test_human_required_kinds_open_tickets(eng):
    from app.services.cs import tickets

    _, codes = _mall(eng, "a-human")
    code = codes[0][1]
    for text, dom in (
        ("상자가 파손돼서 왔어요", "corpmall"),
        ("먹고 배탈이 났어요", "food_safety"),
        ("개인정보 삭제해 주세요", "privacy"),
        ("ㅁㄴㅇㄹ 그거 그거", "corpmall"),
    ):
        r = corp.ask(eng, "a-human", code, text, "ip", at=IN)
        assert r["ticket_id"] and not r["offer_handoff"], text
        t = next(t for t in tickets.queue() if t["id"] == r["ticket_id"])
        assert t["domain"] == dom and t["owner"].startswith("corp:")
    assert "1399" in corp.ask(eng, "a-human", code, "먹고 배가 아파요", "ip", at=IN)["answer"]
    r = corp.ask(eng, "a-human", code, "현금으로 받을 수 있나요", "ip", at=IN)
    assert not r["ticket_id"] and r["offer_handoff"] and "현금" in r["answer"]


def test_auto_answers_are_sampled_for_weekly_review(eng, tmp_path):
    from app.services.cs import review

    _, codes = _mall(eng, "a-review")
    corp.ask(eng, "a-review", codes[0][1], "언제 와요? 010-1111-2222", "ip", at=IN)
    blob = repr(review.samples(days=1))
    assert "corp_eta" in blob and "2222" not in blob


def test_manual_validation_and_common_text_has_no_promises(eng):
    with pytest.raises(corp.MallError, match="형식"):
        _mall(eng, "a-bad1", man={"ship_plan": "다음주"})
    with pytest.raises(corp.MallError, match="확정"):
        _mall(eng, "a-bad2", man={"arrive_note": "반드시 도착해요"})
    for k, v in manual.COMMON.items():
        assert not manual.FORBIDDEN.search(v), k
    for q, a in manual.BUYER_FAQ:
        assert not manual.FORBIDDEN.search(a), q
    m, _ = _mall(eng, "a-upd", man={})
    assert corp.update_manual(eng, m["mall_id"], {"courier": "다라택배", "zzz": "x"}) == {"courier": "다라택배"}
    assert corp.get_mall(eng, mall_id=m["mall_id"])["manual"] == {"courier": "다라택배"}


def test_routes(eng):
    from app.main import app

    H = {"X-Access-Token": "test-token"}
    cl = TestClient(app)
    m, codes = _mall(eng, "a-route")
    r = cl.post("/corp/api/a-route/ask", json={"code": codes[0][2], "text": "언제까지 골라요?"})
    assert r.json()["ok"] and r.json()["intent"] in ("deadline",)
    assert cl.post("/corp/api/a-route/ask", json={"code": codes[0][2], "text": "x", "topic": "eta"}).status_code == 422
    h = cl.post(
        "/corp/api/a-route/ask", json={"code": codes[0][2], "text": "담당자와 얘기하고 싶어요", "handoff": True}
    ).json()
    assert h["ticket_id"]
    assert cl.post(
        f"/admin/api/corpmall/{m['mall_id']}/manual", json={"manual": {"ship_plan": "2026-12-20"}}, headers=H
    ).json()["manual"] == {"ship_plan": "2026-12-20"}
    assert (
        cl.post(
            f"/admin/api/corpmall/{m['mall_id']}/manual", json={"manual": {"courier": "무조건 내일"}}, headers=H
        ).status_code
        == 400
    )
    assert (
        cl.post(
            f"/admin/api/corpmall/{m['mall_id']}/tracking",
            json={"rows": [{"order_id": "Onope", "tracking": "1"}]},
            headers=H,
        ).json()["n"]
        == 0
    )
    assert len(cl.get("/admin/api/corpmall-manual", headers=H).json()["fields"]) == len(manual.MALL_FIELDS)
    faq = cl.get("/biz/api/faq").json()["faq"]
    assert faq and all(f["q"] and f["a"] for f in faq)


def test_migrate_adds_tracking_column(tmp_path):
    import sqlalchemy

    url = f"sqlite:///{tmp_path / 'old.sqlite3'}"
    e = sqlalchemy.create_engine(url)
    with e.begin() as c:
        c.execute(
            sqlalchemy.text(
                "CREATE TABLE corpmall_order (order_id VARCHAR(20) PRIMARY KEY, mall_id VARCHAR(20), "
                "code_hash VARCHAR(64), item_id VARCHAR(40))"
            )
        )
    corp.engine(url)
    assert "tracking" in {c["name"] for c in sqlalchemy.inspect(e).get_columns("corpmall_order")}
