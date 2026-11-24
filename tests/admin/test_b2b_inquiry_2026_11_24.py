"""B2B 문의 창구 1차 (2026-11-24) — 공개 문의 접수 · 관리자 처리 · 콘솔 공고 등록 · 연락처 파기 · 폐쇄몰 임직원 문의."""

from __future__ import annotations

import os
from datetime import datetime, timedelta

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import select

os.environ.setdefault("CORPMALL_KEY", Fernet.generate_key().decode())

from app.services.b2b_inquiry import store  # noqa: E402

FORM = {
    "company": "샘플공사",
    "kind": "public_bid",
    "occasion": "설",
    "due_date": "2027-01-20",
    "headcount": "300",
    "budget_per_person": "50,000",
    "delivery": "individual",
    "notice_url": "https://example.org/notice/1",
    "message": "지역 특산물 3종 중 선택. 담당 010-9999-8888 로 연락 주세요",
    "website": "",
    "contact_name": "김담당",
    "email": "buyer@example.org",
    "phone": "02-123-4567",
    "consent": True,
}
H = {"X-Access-Token": "test-token"}


@pytest.fixture
def eng(tmp_path, monkeypatch):
    monkeypatch.setenv("CS_DIR", str(tmp_path / "cs"))
    monkeypatch.setenv("OPERATOR_NOTIFY", "off")
    store.reset_limits()
    return store.engine()


def test_submit_encrypts_contact_and_masks_message(eng):
    got = store.submit(eng, FORM, "ip1")
    assert got["masked"] == ["전화번호"]
    with eng.connect() as c:
        r = c.execute(select(store.t_inq).where(store.t_inq.c.inquiry_id == got["inquiry_id"])).mappings().first()
    raw = repr(dict(r))
    for s in ("김담당", "buyer@example.org", "1234567", "9999-8888"):
        assert s not in raw
    lst = [q for q in store.list_inquiries(eng) if q["inquiry_id"] == got["inquiry_id"]]
    assert lst[0]["company"] == "샘플공사" and "contact" not in lst[0] and lst[0]["budget_per_person"] == 50000
    full = store.get(eng, got["inquiry_id"], with_contact=True)
    assert full["contact"] == {"name": "김담당", "email": "buyer@example.org", "phone": "021234567"}


@pytest.mark.parametrize(
    "bad, why",
    [
        ({"company": ""}, "이름"),
        ({"email": "", "phone": ""}, "하나는"),
        ({"email": "nope"}, "메일"),
        ({"phone": "12"}, "전화"),
        ({"consent": False}, "동의"),
        ({"occasion": "생일"}, "선택"),
        ({"headcount": "삼백"}, "숫자"),
        ({"budget_per_person": "10"}, "너무"),
        ({"notice_url": "javascript:x"}, "http"),
        ({"due_date": "다음주"}, "날짜"),
    ],
)
def test_submit_validation(eng, bad, why):
    with pytest.raises(store.InquiryError, match=why):
        store.submit(eng, dict(FORM, **bad), "ipv")


def test_honeypot_and_rate_limit(eng):
    before = len(store.list_inquiries(eng))
    got = store.submit(eng, dict(FORM, website="http://spam"), "bot")
    assert got.get("ignored") and len(store.list_inquiries(eng)) == before
    for _ in range(store.PER_CLIENT_HOUR - 1):
        store.submit(eng, FORM, "bot")
    with pytest.raises(store.InquiryError, match="한 시간"):
        store.submit(eng, FORM, "bot")
    store.submit(eng, FORM, "other")


def test_quoted_needs_human_check_and_status_flow(eng):
    iid = store.submit(eng, FORM, "ip")["inquiry_id"]
    with pytest.raises(store.InquiryError, match="사람이 확인"):
        store.set_status(eng, iid, "quoted", by="op")
    d = store.set_status(eng, iid, "quoted", by="op", human_checked=True, note="견적서 v2 메일 회신")
    assert d["status"] == "quoted" and d["events"][-1]["human_checked"]
    with pytest.raises(store.InquiryError):
        store.set_status(eng, iid, "sent_by_ai", by="op")
    d = store.note(eng, iid, "통화함 010-1111-2222", by="op")
    assert "1111" not in repr(d["events"])
    assert store.counts(eng)["quoted"] >= 1


def test_to_bid_registers_conditions_without_contact(eng):
    from app.admin.b2b import bids as bidstore

    iid = store.submit(eng, FORM, "ip")["inquiry_id"]
    bid_id = store.to_bid(eng, iid, by="op")
    assert bid_id.startswith("bid-inq")
    n = bidstore.get(bid_id)
    blob = repr(n.model_dump())
    assert "김담당" not in blob and "buyer@" not in blob and "1234567" not in blob
    assert n.verification == "document_provided" and n.source == "inquiry" and n.budget == 15_000_000
    assert n.requirement.headcount == 300
    d = store.get(eng, iid)
    assert d["bid_id"] == bid_id and d["status"] == "reviewing"
    assert store.to_bid(eng, iid, by="op") == bid_id  # 다시 눌러도 같은 공고


def test_purge_contact_after_done(eng):
    iid = store.submit(eng, FORM, "ip")["inquiry_id"]
    won = store.submit(eng, FORM, "ip")["inquiry_id"]
    store.set_status(eng, iid, "lost", by="op")
    store.set_status(eng, won, "won", by="op")
    later = datetime.now(store.KST) + timedelta(days=store.CONTACT_KEEP_DAYS)
    store.purge(eng, later - timedelta(days=2))
    assert store.get(eng, iid, with_contact=True)["contact"]
    assert store.purge(eng, later + timedelta(days=1)) >= 1
    d = store.get(eng, iid, with_contact=True)
    assert d["contact"] is None and d["purged"] and d["company"] == "샘플공사"
    assert store.get(eng, won, with_contact=True)["contact"]  # 수주는 계약 관리로 — 여기서 안 지움


def test_routes(eng):
    from app.main import app

    cl = TestClient(app)
    assert "noindex" in cl.get("/biz/inquiry").headers["x-robots-tag"]
    r = cl.post("/biz/api/inquiry", json=FORM)
    assert r.json()["ok"], r.text
    iid = r.json()["inquiry_id"]
    assert cl.post("/biz/api/inquiry", json=dict(FORM, extra=1)).status_code == 422
    assert not cl.post("/biz/api/inquiry", json=dict(FORM, consent=False)).json()["ok"]
    assert cl.get("/admin/api/b2b-inquiry").status_code == 401
    lst = cl.get("/admin/api/b2b-inquiry", headers=H).json()
    assert any(q["inquiry_id"] == iid for q in lst["inquiries"]) and "김담당" not in repr(lst)
    assert cl.get(f"/admin/api/b2b-inquiry/{iid}", headers=H).json()["inquiry"]["contact"]["name"] == "김담당"
    tb = cl.post(f"/admin/api/b2b-inquiry/{iid}/to-bid", headers=H).json()
    assert tb["console"].startswith("/admin/b2b?q=bid-inq")
    assert cl.post(f"/admin/api/b2b-inquiry/{iid}/status", json={"status": "quoted"}, headers=H).status_code == 400
    assert (
        cl.post(
            f"/admin/api/b2b-inquiry/{iid}/status", json={"status": "quoted", "human_checked": True}, headers=H
        ).json()["inquiry"]["status"]
        == "quoted"
    )


def test_corpmall_employee_ask_flows_to_cs(eng):
    from app.services.corpmall import store as corp
    from app.services.cs import tickets

    corp.reset_limits()
    m = corp.create_mall(
        eng,
        {
            "slug": "t-ask",
            "client": "샘플공사",
            "opens_at": "2026-12-01T09:00",
            "closes_at": "2026-12-10T18:00",
            "delivery_mode": "bulk",
            "items": [{"id": "A", "name": "한과"}],
        },
    )
    corp.set_status(eng, m["mall_id"], "open")
    ((label, code, token),) = corp.issue_codes(eng, m["mall_id"], 1)
    with pytest.raises(corp.MallError, match="종류"):
        corp.ask(eng, "t-ask", code, "refund_now", "환불", "ip")
    got = corp.ask(eng, "t-ask", code, "delivery", "언제 와요? 제 번호 010-2222-3333", "ip")
    assert got["masked"] == ["전화번호"] and got["asks"][0]["status"] == "open"
    q = [t for t in tickets.queue() if t["domain"] == "corpmall"]
    assert len(q) == 1 and "3333" not in q[0]["summary"] and "#1 배송" in q[0]["summary"] and q[0]["human"]
    tickets.answer(q[0]["id"], "12월 15일 출고 예정이에요.", by="operator")
    assert corp.enter(eng, "t-ask", token, "ip")["asks"][0]["messages"][-1]["text"].startswith("12월 15일")
    new_label, new_code, _ = corp.void_and_reissue(eng, m["mall_id"], label)  # 재발급해도 문의가 따라감
    assert corp.enter(eng, "t-ask", new_code, "ip")["asks"][0]["id"] == q[0]["id"]
    for i in range(corp.MAX_OPEN_ASKS):
        corp.ask(eng, "t-ask", new_code, "other", f"질문 {i}", "ip")
    with pytest.raises(corp.MallError, match="기다리는"):
        corp.ask(eng, "t-ask", new_code, "other", "또 질문", "ip")
