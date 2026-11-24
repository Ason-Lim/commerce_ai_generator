"""발주사 3단계 (2026-11-24) — 발주서 메일 준비·확인·보내기(.eml / SMTP) · 확인 링크로 파일 받기."""

from __future__ import annotations

import email
from email import policy
import os
import io
from datetime import datetime

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from openpyxl import load_workbook
from sqlalchemy import select

os.environ.setdefault("CORPMALL_KEY", Fernet.generate_key().decode())

from app.services.corpmall import mailer, po, podoc, suppliers  # noqa: E402
from app.services.corpmall import store as corp  # noqa: E402

KST = corp.KST
IN = datetime(2026, 12, 3, 10, 0, tzinfo=KST)
SHIP = {"name": "홍길동", "phone": "010-1234-5678", "zipcode": "04524", "address": "서울 중구 세종대로 110", "memo": ""}
H = {"X-Access-Token": "test-token"}
BASE = "https://app.example.kr"


PROFILE = {"company_name": "커머스에이아이", "business_no": "000-00-00000", "address": "서울"}


@pytest.fixture(autouse=True)
def _profile(monkeypatch):
    """발주사 정보가 있어야 정식 발주(없으면 미확정) — 검토 반영 2026-11-24."""
    from app.admin.b2b import proposal

    monkeypatch.setattr(proposal, "load_profile", lambda path=None: dict(PROFILE))


@pytest.fixture
def eng(tmp_path, monkeypatch):
    monkeypatch.setenv("CS_DIR", str(tmp_path / "cs"))
    monkeypatch.setenv("OPERATOR_NOTIFY", "off")
    for k in ("MAIL_SMTP_HOST", "MAIL_FROM", "MAIL_SMTP_USER", "MAIL_SMTP_PASSWORD"):
        monkeypatch.delenv(k, raising=False)
    corp.reset_limits()
    return corp.engine()


def _po(eng, slug, *, master=True):
    m = corp.create_mall(
        eng,
        {
            "slug": slug,
            "client": "샘플공사",
            "opens_at": "2026-12-01T09:00",
            "closes_at": "2026-12-10T18:00",
            "delivery_mode": "individual",
            "items": [{"id": "A", "name": "한과"}],
        },
    )
    corp.set_status(eng, m["mall_id"], "open")
    ((_, code, _),) = corp.issue_codes(eng, m["mall_id"], 1)
    if master:
        s = suppliers.save(
            eng, {"name": f"메일식품-{slug}", "contact": {"name": "박담당", "email": "po@supplier.example"}}
        )
        po.set_suppliers(eng, m["mall_id"], {"A": {"supplier_id": s["supplier_id"], "unit_cost": 30000}})
    else:
        po.set_suppliers(eng, m["mall_id"], {"A": {"supplier": "이름만농원"}})
    corp.choose(eng, slug, code, "A", "ip", shipping=SHIP, consent=True, at=IN)
    b = po.create_batch(eng, m["mall_id"], by="t")
    return m, b["pos"][0]


def test_prepare_compose_and_edit(eng):
    m, no = _po(eng, f"ml-a-{os.urandom(2).hex()}")
    d = mailer.prepare(eng, m["mall_id"], no)
    assert d["to"] == "po@supplier.example" and no in d["subject"] and mailer.ACK in d["body"]
    assert "33,000원" in d["body"] and "홍길동" not in d["body"] and "세종대로" not in d["body"]
    assert mailer.prepare(eng, m["mall_id"], no)["mail_id"] == d["mail_id"]  # 보내지 않은 초안은 하나
    with eng.connect() as c:
        raw = repr(c.execute(select(corp.t_po_mail)).mappings().all())
    assert "po@supplier.example" not in raw  # 받는 사람은 암호화
    with pytest.raises(corp.MallError, match="ACK_LINK"):
        mailer.edit(eng, m["mall_id"], d["mail_id"], subject="x", body="링크 없음", attach=False)
    e = mailer.edit(eng, m["mall_id"], d["mail_id"], subject="[발주] 수정", body=d["body"] + "\n추가 메모", attach=True)
    assert e["subject"] == "[발주] 수정" and e["attach"]


def test_prepare_needs_supplier_master(eng):
    m, no = _po(eng, f"ml-b-{os.urandom(2).hex()}", master=False)
    with pytest.raises(corp.MallError, match="이름만"):
        mailer.prepare(eng, m["mall_id"], no)


def _link_key(data: bytes, no: str) -> str:
    body = email.message_from_bytes(data, policy=policy.default).get_body(preferencelist=("plain",)).get_content()
    return next(w for w in body.split() if f"/corp/po/{no}#k=" in w).split("#k=")[1]


def test_eml_keeps_same_link_and_no_personal_data(eng):
    m, no = _po(eng, f"ml-c-{os.urandom(2).hex()}")
    d = mailer.prepare(eng, m["mall_id"], no)
    with pytest.raises(corp.MallError, match="연결되지 않았어요"):
        mailer.send(eng, m["mall_id"], d["mail_id"], base_url=BASE)
    data, name = mailer.eml(eng, m["mall_id"], d["mail_id"], base_url=BASE)
    msg = email.message_from_bytes(data, policy=policy.default)
    assert name == f"{no}.eml" and msg["To"] == "po@supplier.example" and msg["X-Unsent"] == "1"
    assert "홍길동" not in data.decode("utf-8", "ignore") and not list(msg.iter_attachments())
    key = _link_key(data, no)
    assert podoc.public_view(eng, no, key, "ip")["po"]["po_no"] == no
    data2, _ = mailer.eml(eng, m["mall_id"], d["mail_id"], base_url=BASE)  # 다시 받아도 같은 링크 — 안 끊김
    assert _link_key(data2, no) == key and podoc.public_view(eng, no, key, "ip2")
    sends = [h["what"] for h in podoc.get(eng, no)["sends"]]
    assert sends.count("link_issued") == 1 and sends.count("eml_downloaded") == 2  # .eml 받음 ≠ 보냄
    assert mailer.mark_sent(eng, m["mall_id"], d["mail_id"])["status"] == "manual"
    assert podoc.get(eng, no)["sends"][-1]["what"] == "manual_sent"
    with pytest.raises(corp.MallError, match="이미 보낸"):
        mailer.eml(eng, m["mall_id"], d["mail_id"], base_url=BASE)
    # 명시적 재발급만 옛 링크를 막는다
    new_key = podoc.ack_link(eng, m["mall_id"], no, reissue=True).split("#k=")[1]
    assert new_key != key and podoc.get(eng, no)["sends"][-1]["what"] == "link_reissued"
    with pytest.raises(corp.MallError, match="맞지 않거나"):
        podoc.public_view(eng, no, key, "ip3")
    assert "po@supplier.example" not in repr(corp.events(eng, m["mall_id"]))
    with eng.connect() as c:  # 링크 원문은 암호화로만
        assert new_key not in repr(c.execute(select(corp.t_po)).mappings().all())


class _FakeSMTP:
    sent: list = []
    fail = None  # None · "connect" · "refused" · "disconnect"

    def __init__(self, host, port, timeout=None):
        if _FakeSMTP.fail == "connect":
            raise OSError("connection refused")

    def starttls(self, context=None):
        pass

    def login(self, u, p):
        pass

    def send_message(self, msg):
        if _FakeSMTP.fail == "refused":
            raise mailer.smtplib.SMTPRecipientsRefused({"po@supplier.example": (550, b"no such user")})
        if _FakeSMTP.fail == "disconnect":
            _FakeSMTP.sent.append(msg)  # 서버는 받았을 수도 있음
            raise mailer.smtplib.SMTPServerDisconnected("lost")
        _FakeSMTP.sent.append(msg)

    def quit(self):
        raise mailer.smtplib.SMTPServerDisconnected("bye")  # 접수 뒤 종료 오류는 무시돼야


def _smtp(monkeypatch):
    monkeypatch.setenv("MAIL_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("MAIL_FROM", "order@ourco.example")
    monkeypatch.setattr(mailer.smtplib, "SMTP", _FakeSMTP)
    _FakeSMTP.sent, _FakeSMTP.fail = [], None


def test_smtp_send_attach_and_definite_failure(eng, monkeypatch):
    _smtp(monkeypatch)
    m, no = _po(eng, f"ml-d-{os.urandom(2).hex()}")
    d = mailer.prepare(eng, m["mall_id"], no)
    mailer.edit(eng, m["mall_id"], d["mail_id"], subject=d["subject"], body=d["body"], attach=True)
    _FakeSMTP.fail = "connect"
    with pytest.raises(corp.MallError, match="연결하지 못했어요"):
        mailer.send(eng, m["mall_id"], d["mail_id"], base_url=BASE)
    assert mailer.get(eng, d["mail_id"])["status"] == "failed"
    _FakeSMTP.fail = "refused"
    with pytest.raises(corp.MallError, match="받지 않았어요"):
        mailer.send(eng, m["mall_id"], d["mail_id"], base_url=BASE)
    assert mailer.get(eng, d["mail_id"])["status"] == "failed"
    _FakeSMTP.fail = None
    got = mailer.send(eng, m["mall_id"], d["mail_id"], base_url=BASE)  # 실패가 확실한 메일은 다시 보낼 수 있음
    assert got["status"] == "sent" and len(_FakeSMTP.sent) == 1
    assert podoc.get(eng, no)["sends"][-1]["what"] == "smtp_accepted"
    msg = _FakeSMTP.sent[0]
    att = list(msg.iter_attachments())
    assert msg["From"] == "order@ourco.example" and len(att) == 1 and att[0].get_filename().endswith(".xlsx")
    with pytest.raises(corp.MallError, match="이미 보낸"):
        mailer.send(eng, m["mall_id"], d["mail_id"], base_url=BASE)


def test_smtp_unknown_result_blocks_resend(eng, monkeypatch):
    _smtp(monkeypatch)
    m, no = _po(eng, f"ml-u-{os.urandom(2).hex()}")
    d = mailer.prepare(eng, m["mall_id"], no)
    _FakeSMTP.fail = "disconnect"
    with pytest.raises(corp.MallError, match="갔는지 몰라요"):
        mailer.send(eng, m["mall_id"], d["mail_id"], base_url=BASE)
    assert mailer.get(eng, d["mail_id"])["status"] == "unknown"
    assert podoc.get(eng, no)["sends"][-1]["what"] == "smtp_unknown"
    _FakeSMTP.fail = None
    for fn in (
        lambda: mailer.send(eng, m["mall_id"], d["mail_id"], base_url=BASE),
        lambda: mailer.eml(eng, m["mall_id"], d["mail_id"], base_url=BASE),
    ):
        with pytest.raises(corp.MallError, match="결과를 모르는"):
            fn()
    assert len(_FakeSMTP.sent) == 1  # 자동·버튼 재발송 없음
    assert mailer.prepare(eng, m["mall_id"], no)["mail_id"] == d["mail_id"]  # 새 메일로 우회도 안 됨
    with pytest.raises(corp.MallError, match="어떻게 확인"):
        mailer.mark_not_sent(eng, m["mall_id"], d["mail_id"], by="op", note="")
    assert (
        mailer.mark_not_sent(eng, m["mall_id"], d["mail_id"], by="op", note="11/25 전화 — 못 받음")["status"]
        == "failed"
    )
    assert mailer.send(eng, m["mall_id"], d["mail_id"], base_url=BASE)["status"] == "sent"
    # 다른 메일: 결과 불명 → 공급사가 받았다고 확인
    m2, no2 = _po(eng, f"ml-u2-{os.urandom(2).hex()}")
    d2 = mailer.prepare(eng, m2["mall_id"], no2)
    _FakeSMTP.fail = "disconnect"
    with pytest.raises(corp.MallError):
        mailer.send(eng, m2["mall_id"], d2["mail_id"], base_url=BASE)
    assert mailer.mark_sent(eng, m2["mall_id"], d2["mail_id"])["status"] == "manual"


def test_no_mail_while_change_requested(eng):
    m, no = _po(eng, f"ml-cr-{os.urandom(2).hex()}")
    key = podoc.ack_link(eng, m["mall_id"], no).split("#k=")[1]
    d = mailer.prepare(eng, m["mall_id"], no)
    podoc.respond(eng, no, key, "ip", action="change", name="영업", memo="수량 2개 부족")
    for fn in (
        lambda: mailer.prepare(eng, m["mall_id"], no),
        lambda: mailer.eml(eng, m["mall_id"], d["mail_id"], base_url=BASE),
    ):
        with pytest.raises(corp.MallError, match="변경 요청을 먼저"):
            fn()
    podoc.mark_ack(eng, m["mall_id"], no, by="op", note="부족분 다음 주 출고로 합의")
    assert mailer.eml(eng, m["mall_id"], d["mail_id"], base_url=BASE)[0]  # 정리 뒤엔 됨


def test_supplier_file_scope_and_lifetime(eng):
    """확인 링크의 파일 범위 — 그 공급사·그 발주서만, 취소·배송 완료·파기 뒤 막힘(기간 고정 아님)."""
    m = corp.create_mall(
        eng,
        {
            "slug": f"ml-e-{os.urandom(2).hex()}",
            "client": "샘플공사",
            "opens_at": "2026-12-01T09:00",
            "closes_at": "2026-12-10T18:00",
            "delivery_mode": "individual",
            "items": [{"id": "A", "name": "한과"}, {"id": "B", "name": "감귤"}],
        },
    )
    corp.set_status(eng, m["mall_id"], "open")
    codes = corp.issue_codes(eng, m["mall_id"], 2)
    sa = suppliers.save(eng, {"name": f"가공급-{os.urandom(2).hex()}", "contact": {"email": "a@x.example"}})
    sb = suppliers.save(eng, {"name": f"나공급-{os.urandom(2).hex()}", "contact": {"email": "b@x.example"}})
    po.set_suppliers(
        eng,
        m["mall_id"],
        {
            "A": {"supplier_id": sa["supplier_id"], "unit_cost": 1000},
            "B": {"supplier_id": sb["supplier_id"], "unit_cost": 2000},
        },
    )
    other = {**SHIP, "name": "김다른", "phone": "010-2222-3333"}
    corp.choose(eng, m["slug"], codes[0][1], "A", "ip", shipping=SHIP, consent=True, at=IN)
    corp.choose(eng, m["slug"], codes[1][1], "B", "ip", shipping=other, consent=True, at=IN)
    nos = po.create_batch(eng, m["mall_id"], by="t")["pos"]
    pa = next(p for p in podoc.list_pos(eng, m["mall_id"]) if p["supplier"] == sa["name"])
    pb = next(p for p in podoc.list_pos(eng, m["mall_id"]) if p["po_no"] != pa["po_no"])
    ka = podoc.ack_link(eng, m["mall_id"], pa["po_no"]).split("#k=")[1]
    kb = podoc.ack_link(eng, m["mall_id"], pb["po_no"]).split("#k=")[1]
    wb = load_workbook(io.BytesIO(podoc.supplier_file(eng, pa["po_no"], ka, "ip")[0]))
    text = repr([[c.value for c in r] for ws in wb for r in ws.iter_rows()])
    assert "홍길동" in text and "김다른" not in text and sb["name"] not in text and len(nos) == 2  # 그 공급사 것만
    with pytest.raises(corp.MallError, match="맞지 않거나"):  # A 링크로 B 발주서 안 열림
        podoc.supplier_file(eng, pb["po_no"], ka, "ip")
    assert podoc.get(eng, pa["po_no"])["sends"][-1]["what"] == "file_downloaded_by_supplier"
    # 배송 완료 → 막힘
    oa = next(o for o in corp.orders(eng, m["mall_id"]) if o["item_id"] == "A")["order_id"]
    corp.mark(eng, m["mall_id"], [oa], "delivered")
    with pytest.raises(corp.MallError, match="배송 완료"):
        podoc.supplier_file(eng, pa["po_no"], ka, "ip")
    # 파기 → 막힘
    ob = next(o for o in corp.orders(eng, m["mall_id"]) if o["item_id"] == "B")["order_id"]
    with eng.begin() as c:
        c.execute(
            corp.t_order.update().where(corp.t_order.c.order_id == ob).values(ship_enc=None, purged_at=corp.now())
        )
    with pytest.raises(corp.MallError, match="파기"):
        podoc.supplier_file(eng, pb["po_no"], kb, "ip")


def test_supplier_file_blocked_after_cancel(eng):
    m, no = _po(eng, f"ml-x-{os.urandom(2).hex()}")
    key = podoc.ack_link(eng, m["mall_id"], no).split("#k=")[1]
    podoc.cancel(eng, m["mall_id"], no, by="op", reason="시험")
    with pytest.raises(corp.MallError, match="취소 요청 중"):
        podoc.supplier_file(eng, no, key, "ip")
    podoc.respond(eng, no, key, "ip", action="cancel_ok", name="물류")
    with pytest.raises(corp.MallError, match="맞지 않거나"):
        podoc.supplier_file(eng, no, key, "ip2")


def test_routes(eng):
    from app.main import app

    cl = TestClient(app)
    m, no = _po(eng, f"ml-r-{os.urandom(2).hex()}")
    base = f"/admin/api/corpmall/{m['mall_id']}"
    assert cl.post(f"{base}/pos/{no}/mail").status_code == 401
    d = cl.post(f"{base}/pos/{no}/mail", headers=H).json()["mail"]
    lst = cl.get(f"{base}/mails", headers=H).json()
    assert lst["smtp"] is False and lst["mails"][0]["mail_id"] == d["mail_id"]
    assert cl.post(f"{base}/mails/{d['mail_id']}/send", headers=H).status_code == 400
    r = cl.get(f"{base}/mails/{d['mail_id']}/eml", headers=H)
    assert r.status_code == 200 and r.headers["content-type"].startswith("message/rfc822")
    key = _link_key(r.content, no)
    f = cl.post(f"/corp/api/po/{no}/file", json={"key": key})
    assert f.status_code == 200 and "attachment" in f.headers["content-disposition"]
    assert cl.post(f"/corp/api/po/{no}/file", json={"key": "bad"}).status_code == 400
    assert cl.post(f"{base}/mails/{d['mail_id']}/mark-sent", headers=H).json()["mail"]["status"] == "manual"
    assert cl.post(f"{base}/mails/{d['mail_id']}/mark-not-sent", headers=H, json={"note": "x"}).status_code == 400
    same = cl.post(f"{base}/pos/{no}/ack-link", headers=H).json()["link"]
    assert same.endswith(key)  # 같은 판은 같은 링크
    assert not cl.post(f"{base}/pos/{no}/ack-link?reissue=true", headers=H).json()["link"].endswith(key)
