"""발주사 3단계 (2026-11-24) — 발주서 메일 준비·확인·보내기(.eml / SMTP) · 확인 링크로 파일 받기."""

from __future__ import annotations

import email
from email import policy
import os
from datetime import datetime, timedelta

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import select

os.environ.setdefault("CORPMALL_KEY", Fernet.generate_key().decode())

from app.services.corpmall import mailer, po, podoc, suppliers  # noqa: E402
from app.services.corpmall import store as corp  # noqa: E402

KST = corp.KST
IN = datetime(2026, 12, 3, 10, 0, tzinfo=KST)
SHIP = {"name": "홍길동", "phone": "010-1234-5678", "zipcode": "04524", "address": "서울 중구 세종대로 110", "memo": ""}
H = {"X-Access-Token": "test-token"}
BASE = "https://app.example.kr"


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


def test_eml_without_smtp_has_fresh_link_and_no_personal_data(eng):
    m, no = _po(eng, f"ml-c-{os.urandom(2).hex()}")
    d = mailer.prepare(eng, m["mall_id"], no)
    with pytest.raises(corp.MallError, match="연결되지 않았어요"):
        mailer.send(eng, m["mall_id"], d["mail_id"], base_url=BASE)
    data, name = mailer.eml(eng, m["mall_id"], d["mail_id"], base_url=BASE)
    msg = email.message_from_bytes(data, policy=policy.default)
    body = msg.get_body(preferencelist=("plain",)).get_content()
    assert name == f"{no}.eml" and msg["To"] == "po@supplier.example" and msg["X-Unsent"] == "1"
    link = next(w for w in body.split() if w.startswith(f"{BASE}/corp/po/{no}#k="))
    assert "홍길동" not in data.decode("utf-8", "ignore") and not list(msg.iter_attachments())
    key = link.split("#k=")[1]
    assert podoc.public_view(eng, no, key, "ip")["po"]["po_no"] == no
    data2, _ = mailer.eml(eng, m["mall_id"], d["mail_id"], base_url=BASE)  # 다시 받으면 옛 링크 막힘
    with pytest.raises(corp.MallError):
        podoc.public_view(eng, no, key, "ip2")
    assert mailer.mark_sent(eng, m["mall_id"], d["mail_id"])["status"] == "manual"
    with pytest.raises(corp.MallError, match="이미 보낸"):
        mailer.eml(eng, m["mall_id"], d["mail_id"], base_url=BASE)
    assert any(e["kind"] == "po_mail_manual" for e in corp.events(eng, m["mall_id"]))
    assert "po@supplier.example" not in repr(corp.events(eng, m["mall_id"]))


class _FakeSMTP:
    sent: list = []
    fail = False

    def __init__(self, host, port, timeout=None):
        self.host = host

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def starttls(self, context=None):
        pass

    def login(self, u, p):
        pass

    def send_message(self, msg):
        if _FakeSMTP.fail:
            raise OSError("connection refused")
        _FakeSMTP.sent.append(msg)


def test_smtp_send_attach_and_failure(eng, monkeypatch):
    monkeypatch.setenv("MAIL_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("MAIL_FROM", "order@ourco.example")
    monkeypatch.setattr(mailer.smtplib, "SMTP", _FakeSMTP)
    _FakeSMTP.sent, _FakeSMTP.fail = [], True
    m, no = _po(eng, f"ml-d-{os.urandom(2).hex()}")
    d = mailer.prepare(eng, m["mall_id"], no)
    mailer.edit(eng, m["mall_id"], d["mail_id"], subject=d["subject"], body=d["body"], attach=True)
    with pytest.raises(corp.MallError, match="보내지 못했어요"):
        mailer.send(eng, m["mall_id"], d["mail_id"], base_url=BASE)
    assert mailer.get(eng, d["mail_id"])["status"] == "failed"
    _FakeSMTP.fail = False
    got = mailer.send(eng, m["mall_id"], d["mail_id"], base_url=BASE)  # 실패한 메일은 다시 보낼 수 있음
    assert got["status"] == "sent" and len(_FakeSMTP.sent) == 1
    msg = _FakeSMTP.sent[0]
    att = list(msg.iter_attachments())
    assert msg["From"] == "order@ourco.example" and len(att) == 1 and att[0].get_filename().endswith(".xlsx")
    with pytest.raises(corp.MallError, match="이미 보낸"):
        mailer.send(eng, m["mall_id"], d["mail_id"], base_url=BASE)


def test_supplier_file_via_link_expires(eng, monkeypatch):
    m, no = _po(eng, f"ml-e-{os.urandom(2).hex()}")
    key = podoc.ack_link(eng, m["mall_id"], no).split("#k=")[1]
    data, name = podoc.supplier_file(eng, no, key, "ip")
    assert name.endswith(".xlsx") and data[:2] == b"PK"
    assert any(
        e["kind"] == "po_download" and e["detail"]["by"] == "supplier_link" for e in corp.events(eng, m["mall_id"])
    )
    later = corp.now() + timedelta(days=podoc.FILE_DAYS + 1)
    monkeypatch.setattr(corp, "now", lambda: later)
    with pytest.raises(corp.MallError, match="30일"):
        podoc.supplier_file(eng, no, key, "ip")


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
    key = next(
        w
        for w in email.message_from_bytes(r.content, policy=policy.default).get_body().get_content().split()
        if "#k=" in w
    ).split("#k=")[1]
    f = cl.post(f"/corp/api/po/{no}/file", json={"key": key})
    assert f.status_code == 200 and "attachment" in f.headers["content-disposition"]
    assert cl.post(f"/corp/api/po/{no}/file", json={"key": "bad"}).status_code == 400
    assert cl.post(f"{base}/mails/{d['mail_id']}/mark-sent", headers=H).json()["mail"]["status"] == "manual"
