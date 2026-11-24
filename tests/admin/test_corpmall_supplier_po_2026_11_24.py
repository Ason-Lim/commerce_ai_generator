"""공급 거래처 · 정식 발주서 · 공급사 수신 확인 (2026-11-24) — commerce_ai 가 발주사가 될 때."""

from __future__ import annotations

import io
import os
from datetime import datetime

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from openpyxl import load_workbook
from sqlalchemy import select

os.environ.setdefault("CORPMALL_KEY", Fernet.generate_key().decode())

from app.services.corpmall import po, podoc, suppliers  # noqa: E402
from app.services.corpmall import store as corp  # noqa: E402

KST = corp.KST
IN = datetime(2026, 12, 3, 10, 0, tzinfo=KST)
SHIP = {"name": "홍길동", "phone": "010-1234-5678", "zipcode": "04524", "address": "서울 중구 세종대로 110", "memo": ""}
H = {"X-Access-Token": "test-token"}


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
    corp.reset_limits()
    return corp.engine()


def _sup(eng, name, **kw):
    d = {
        "name": name,
        "biz_no": "123-45-67890",
        "order_method": "email",
        "vat_mode": "excluded",
        "lead_days": 3,
        "payment_terms": "월말 마감 익월 10일",
        "contact": {"name": "박담당", "email": "po@example.com", "phone": "02-111-2222"},
    }
    d.update(kw)
    return suppliers.save(eng, d)


def _mall(eng, slug, mode="individual", n=3, manual=None):
    m = corp.create_mall(
        eng,
        {
            "slug": slug,
            "client": "샘플공사",
            "opens_at": "2026-12-01T09:00",
            "closes_at": "2026-12-10T18:00",
            "delivery_mode": mode,
            "default_item_id": "A",
            "manual": manual or {},
            "items": [{"id": "A", "name": "한과"}, {"id": "B", "name": "감귤"}],
        },
    )
    corp.set_status(eng, m["mall_id"], "open")
    return m, corp.issue_codes(eng, m["mall_id"], n)


def test_supplier_master_encrypts_contact_and_validates(eng):
    s = _sup(eng, f"가나식품-{os.getpid()}")
    assert s["contact"]["email"] == "po@example.com" and s["biz_no"] == "1234567890"
    with eng.connect() as c:
        raw = repr(
            c.execute(select(suppliers.t_supplier).where(suppliers.t_supplier.c.supplier_id == s["supplier_id"]))
            .mappings()
            .first()
        )
    assert "po@example.com" not in raw and "박담당" not in raw
    row = next(x for x in suppliers.list_all(eng) if x["supplier_id"] == s["supplier_id"])
    assert "contact" not in row and row["biz_no_masked"] == "123-**-***90" and row["has_contact"]
    for bad, why in (
        ({"biz_no": "12"}, "10자리"),
        ({"contact": {}}, "메일 주소가 있어야"),
        ({"vat_mode": "x"}, "다시 골라"),
        ({"lead_days": 99}, "0~60"),
        ({"contact": {"email": "nope"}}, "메일 주소를 확인"),
    ):
        with pytest.raises(corp.MallError, match=why):
            _sup(eng, f"오류-{why}", **bad)
    with pytest.raises(corp.MallError, match="이미 있어요"):
        _sup(eng, s["name"])
    upd = suppliers.save(eng, {**s, "contact": {"email": "new@example.com"}, "payment_terms": "선금"}, s["supplier_id"])
    assert upd["contact"]["email"] == "new@example.com" and upd["payment_terms"] == "선금"


def test_po_amounts_due_and_snapshot(eng):
    ex = _sup(eng, f"별도식품-{os.getpid()}", vat_mode="excluded", lead_days=3)
    inc = _sup(eng, f"포함농원-{os.getpid()}", vat_mode="included", lead_days=None)
    m, codes = _mall(eng, "s-amt")
    po.set_suppliers(
        eng,
        m["mall_id"],
        {
            "A": {"supplier_id": ex["supplier_id"], "sku": "0012", "unit_cost": "12,345"},
            "B": {"supplier_id": inc["supplier_id"], "unit_cost": 11000},
        },
    )
    for (_, code, _), item in zip(codes, "AAB", strict=True):
        corp.choose(eng, "s-amt", code, item, "ip", shipping=SHIP, consent=True, at=IN)
    b = po.create_batch(eng, m["mall_id"], by="t")
    pos = {p["supplier"]: p for p in podoc.list_pos(eng, m["mall_id"])}
    a, bb = pos[ex["name"]], pos[inc["name"]]
    assert b["pos"] == sorted(p["po_no"] for p in pos.values())
    assert a["lines"][0]["qty"] == 2 and a["supply_amount"] == 24690 and a["vat"] == 2469 and a["total"] == 27159
    assert bb["total"] == 11000 and bb["supply_amount"] == 10000 and bb["vat"] == 1000
    assert (
        a["payment_terms"] == "월말 마감 익월 10일" and a["due_date"] and bb["due_date"] is None
    )  # 납기: 기본 납기 / 협의
    # 단가를 바꿔도 이미 낸 발주서는 그대로
    po.set_suppliers(eng, m["mall_id"], {"A": {"supplier_id": ex["supplier_id"], "unit_cost": 1}})
    assert podoc.get(eng, a["po_no"])["total"] == 27159


def test_missing_cost_is_not_zero_and_ship_plan_is_due(eng):
    s = _sup(eng, f"미정식품-{os.getpid()}")
    m, codes = _mall(eng, "s-miss", manual={"ship_plan": "2026-12-15"})
    po.set_suppliers(eng, m["mall_id"], {"A": {"supplier_id": s["supplier_id"]}})
    corp.choose(eng, "s-miss", codes[0][1], "A", "ip", shipping=SHIP, consent=True, at=IN)
    po.create_batch(eng, m["mall_id"], by="t")
    p = podoc.list_pos(eng, m["mall_id"])[0]
    assert p["total"] is None and p["needs_cost"] and p["due_date"] == "2026-12-15"
    assert podoc.won(p["total"]) == "단가 확인 필요"


def test_supplier_file_has_formal_po_sheet(eng):
    s = _sup(eng, f"시트식품-{os.getpid()}")
    m, codes = _mall(eng, "s-sheet")
    po.set_suppliers(eng, m["mall_id"], {"A": {"supplier_id": s["supplier_id"], "sku": "0007", "unit_cost": 10000}})
    corp.choose(eng, "s-sheet", codes[0][1], "A", "ip", shipping=SHIP, consent=True, at=IN)
    b = po.create_batch(eng, m["mall_id"], by="t")
    wb = load_workbook(io.BytesIO(po.render(eng, m["mall_id"], b["batch_id"], supplier=s["name"])[0]))
    assert wb.sheetnames[0] == "발주서"
    text = repr([[c.value for c in r] for r in wb["발주서"].iter_rows()])
    assert b["pos"][0] in text and "11000" in text and "월말 마감 익월 10일" in text and "0007" in text
    assert "홍길동" not in text  # 발주서 시트엔 배송 정보 없음 (다음 시트)
    full = load_workbook(io.BytesIO(po.render(eng, m["mall_id"], b["batch_id"])[0]))
    assert "발주 번호" in [c.value for c in full["요약"][1]]


def test_ack_link_flow(eng):
    s = _sup(eng, f"확인식품-{os.getpid()}")
    m, codes = _mall(eng, "s-ack", manual={"ship_plan": "2026-12-15", "arrive_by": "2026-12-18"})
    po.set_suppliers(eng, m["mall_id"], {"A": {"supplier_id": s["supplier_id"], "unit_cost": 5000}})
    corp.choose(eng, "s-ack", codes[0][1], "A", "ip", shipping=SHIP, consent=True, at=IN)
    po.create_batch(eng, m["mall_id"], by="t")
    no = podoc.list_pos(eng, m["mall_id"])[0]["po_no"]
    assert podoc.get(eng, no)["delivered_at"] is None
    link = podoc.ack_link(eng, m["mall_id"], no)
    key = link.split("#k=")[1]
    assert podoc.get(eng, no)["delivered_at"]  # 링크를 만들면 '전달됨'
    with eng.connect() as c:
        assert key not in repr(c.execute(select(corp.t_po)).mappings().all())
    v = podoc.public_view(eng, no, key, "ip")
    assert v["po"]["po_no"] == no and "홍길동" not in repr(v) and "010-1234" not in repr(v)
    assert v["po"]["ship_by"] == "2026-12-15" and v["po"]["arrive_by"] == "2026-12-18"  # 출고·도착 따로
    assert podoc.get(eng, no)["viewed_at"]
    with pytest.raises(corp.MallError, match="이름"):
        podoc.respond(eng, no, key, "ip", action="accept", name=" ", agree=True)
    with pytest.raises(corp.MallError, match="수락한다는 표시"):  # 수락은 명시 동의가 있어야
        podoc.respond(eng, no, key, "ip", action="accept", name="물류팀 김")
    with pytest.raises(corp.MallError, match="변경 요청"):  # 출고 기한보다 늦은 예정일로는 수락 불가
        podoc.respond(eng, no, key, "ip", action="accept", name="물류팀 김", agree=True, ship_date="2026-12-16")
    got = podoc.respond(
        eng,
        no,
        key,
        "ip",
        action="accept",
        name="물류팀 김",
        agree=True,
        ship_date="2026-12-14",
        memo="연락 010-9999-8888",
    )
    first_at = got["ack_at"]
    assert got["status"] == "accepted" and got["ack_ship_date"] == "2026-12-14" and "8888" not in got["ack_memo"]
    assert got["ship_by"] == "2026-12-15"  # 공급사 예정일이 발주 조건을 덮어쓰지 않음
    again = podoc.acknowledge(eng, no, key, "ip", name="물류팀 박", ship_date="2026-12-13")
    assert again["ack_at"] == first_at and again["ack_ship_date"] == "2026-12-13"  # 처음 응답 시각은 그대로
    last = again["history"][-1]  # 고친 사람·전후 값은 기록에
    assert last["by"] == "공급사(물류팀 박)" and last["before"]["ack_ship_date"] == "2026-12-14"
    assert last["after"]["ack_ship_date"] == "2026-12-13" and last["at"]
    new_key = podoc.ack_link(eng, m["mall_id"], no).split("#k=")[1]  # 새로 만들면 옛 링크 막힘
    with pytest.raises(corp.MallError, match="맞지 않거나"):
        podoc.public_view(eng, no, key, "ip2")
    assert podoc.public_view(eng, no, new_key, "ip3")["po"]["status"] == "accepted"


def test_change_request_goes_to_operator_review(eng):
    s = _sup(eng, f"변경식품-{os.getpid()}")
    m, codes = _mall(eng, "s-chg", manual={"ship_plan": "2026-12-15"})
    po.set_suppliers(eng, m["mall_id"], {"A": {"supplier_id": s["supplier_id"], "unit_cost": 5000}})
    corp.choose(eng, "s-chg", codes[0][1], "A", "ip", shipping=SHIP, consent=True, at=IN)
    no = po.create_batch(eng, m["mall_id"], by="t")["pos"][0]
    key = podoc.ack_link(eng, m["mall_id"], no).split("#k=")[1]
    with pytest.raises(corp.MallError, match="메모"):
        podoc.respond(eng, no, key, "ip", action="change", name="영업팀")
    got = podoc.respond(
        eng, no, key, "ip", action="change", name="영업팀", ship_date="2026-12-18", memo="12/18 출고 가능"
    )
    assert got["status"] == "change_requested" and got["ship_by"] == "2026-12-15" and got["total"] == 5500
    with pytest.raises(corp.MallError, match="어떻게 수락"):
        podoc.mark_ack(eng, m["mall_id"], no, by="op")
    ok = podoc.mark_ack(eng, m["mall_id"], no, by="op", note="12/18 출고로 발주처와 합의")
    assert ok["status"] == "accepted" and ok["history"][-1]["before"]["status"] == "change_requested"
    with pytest.raises(corp.MallError, match="수락 전이거나"):
        podoc.mark_ack(eng, m["mall_id"], no, by="op", note="again")


def test_draft_when_name_only_or_no_cost_or_no_profile(eng, monkeypatch):
    from app.admin.b2b import proposal
    from app.services.corpmall import mailer

    s = _sup(eng, f"초안식품-{os.getpid()}")
    m, codes = _mall(eng, "s-draft")
    po.set_suppliers(eng, m["mall_id"], {"A": {"supplier": "이름만상회"}, "B": {"supplier_id": s["supplier_id"]}})
    corp.choose(eng, "s-draft", codes[0][1], "A", "ip", shipping=SHIP, consent=True, at=IN)
    corp.choose(eng, "s-draft", codes[1][1], "B", "ip", shipping=SHIP, consent=True, at=IN)
    b = po.create_batch(eng, m["mall_id"], by="t")
    pos = {p["supplier"]: p for p in podoc.list_pos(eng, m["mall_id"])}
    name_only, no_cost = pos["이름만상회"], pos[s["name"]]
    assert name_only["status"] == "draft" and "공급 거래처 미연결(이름만)" in name_only["gaps"]
    assert no_cost["status"] == "draft" and no_cost["gaps"] == ["매입 단가 없음"]
    for fn in (
        lambda: podoc.ack_link(eng, m["mall_id"], no_cost["po_no"]),
        lambda: mailer.prepare(eng, m["mall_id"], no_cost["po_no"]),
        lambda: podoc.operator_supplier_file(eng, m["mall_id"], no_cost["po_no"]),
    ):
        with pytest.raises(corp.MallError, match="미확정"):
            fn()
    sheet = load_workbook(io.BytesIO(po.render(eng, m["mall_id"], b["batch_id"], supplier=s["name"])[0]))["발주서"]
    assert "정식 발주 아님" in sheet["A1"].value
    with pytest.raises(corp.MallError, match="매입 단가 없음"):
        podoc.finalize(eng, m["mall_id"], no_cost["po_no"])
    po.set_suppliers(eng, m["mall_id"], {"B": {"supplier_id": s["supplier_id"], "unit_cost": 7000}})
    monkeypatch.setattr(proposal, "load_profile", lambda path=None: {})
    with pytest.raises(corp.MallError, match="발주사 회사명"):  # 발주사 정보 없음 → 아직 미확정
        podoc.finalize(eng, m["mall_id"], no_cost["po_no"])
    monkeypatch.setattr(proposal, "load_profile", lambda path=None: dict(PROFILE))
    fin = podoc.finalize(eng, m["mall_id"], no_cost["po_no"])
    assert fin["status"] == "issued" and fin["total"] == 7700 and fin["version"] == 2
    assert fin["history"][-1]["what"] == "finalize" and fin["history"][-1]["before"]["total"] is None
    assert podoc.ack_link(eng, m["mall_id"], fin["po_no"]).startswith("/corp/po/")
    with pytest.raises(corp.MallError, match="미확정 발주서만"):
        podoc.finalize(eng, m["mall_id"], fin["po_no"])
    # 이름만인 공급사는 거래처를 연결해도 이름이 다르면 다시 묶어야
    po.set_suppliers(eng, m["mall_id"], {"A": {"supplier_id": s["supplier_id"], "unit_cost": 1000}})
    with pytest.raises(corp.MallError, match="다시 묶어"):
        podoc.finalize(eng, m["mall_id"], name_only["po_no"])
    with eng.connect() as c:  # 미확정도 다운로드 기록은 남음(판·지문)
        ev = [r for r in c.execute(select(corp.t_event).where(corp.t_event.c.kind == "po_download")).mappings()]
    assert any((e["detail"] or {}).get("sha256") for e in ev)


def test_tax_exempt_items_split(eng):
    s = _sup(eng, f"면세농원-{os.getpid()}", vat_mode="excluded")
    m, codes = _mall(eng, "s-tax")
    po.set_suppliers(
        eng,
        m["mall_id"],
        {
            "A": {"supplier_id": s["supplier_id"], "unit_cost": 10000},
            "B": {"supplier_id": s["supplier_id"], "unit_cost": 20000, "tax_type": "exempt"},
        },
    )
    corp.choose(eng, "s-tax", codes[0][1], "A", "ip", shipping=SHIP, consent=True, at=IN)
    corp.choose(eng, "s-tax", codes[1][1], "B", "ip", shipping=SHIP, consent=True, at=IN)
    p = podoc.get(eng, po.create_batch(eng, m["mall_id"], by="t")["pos"][0])
    assert p["exempt_amount"] == 20000 and p["vat"] == 1000 and p["supply_amount"] == 30000 and p["total"] == 31000
    assert {ln["item_id"]: ln["tax_type"] for ln in p["lines"]} == {"A": "taxable", "B": "exempt"}
    with pytest.raises(corp.MallError, match="과세 구분"):
        po.set_suppliers(eng, m["mall_id"], {"A": {"supplier_id": s["supplier_id"], "tax_type": "zero"}})


def test_cancel_before_and_after_delivery(eng):
    s = _sup(eng, f"취소식품-{os.getpid()}")
    m, codes = _mall(eng, "s-cx")
    po.set_suppliers(eng, m["mall_id"], {"A": {"supplier_id": s["supplier_id"], "unit_cost": 5000}})
    corp.choose(eng, "s-cx", codes[0][1], "A", "ip", shipping=SHIP, consent=True, at=IN)
    corp.choose(eng, "s-cx", codes[1][1], "A", "ip", shipping=SHIP, consent=True, at=IN)
    no = po.create_batch(eng, m["mall_id"], by="t")["pos"][0]
    with pytest.raises(corp.MallError, match="이유"):
        podoc.cancel(eng, m["mall_id"], no, by="op", reason="")
    oid = corp.orders(eng, m["mall_id"])[0]["order_id"]
    corp.set_tracking(eng, m["mall_id"], [{"order_id": oid, "tracking": "777"}])
    with pytest.raises(corp.MallError, match="송장이 들어갔거나"):
        podoc.cancel(eng, m["mall_id"], no, by="op", reason="품절")
    with corp.engine().begin() as c:  # 시험: 송장 지우고 다시
        c.execute(corp.t_order.update().where(corp.t_order.c.order_id == oid).values(tracking=None))
    # 1) 공급사에 전달 전 → 바로 취소, 주문 복원
    got = podoc.cancel(eng, m["mall_id"], no, by="op", reason="품절로 다른 거래처")
    assert got["status"] == "cancelled" and got["cancel_reason"] == "품절로 다른 거래처"
    assert {o["ship_status"] for o in corp.orders(eng, m["mall_id"])} == {"requested"}
    # 2) 전달 뒤 → 취소 요청만, 주문은 그대로(묶인 상태)
    no2 = po.create_batch(eng, m["mall_id"], by="t")["pos"][0]
    key = podoc.ack_link(eng, m["mall_id"], no2).split("#k=")[1]
    req = podoc.cancel(eng, m["mall_id"], no2, by="op", reason="발주처 행사 취소")
    assert req["status"] == "cancel_requested"
    assert {o["ship_status"] for o in corp.orders(eng, m["mall_id"])} == {"exported"}
    with pytest.raises(corp.MallError, match="발주서에 넣을 주문이 없어요"):  # 재발주 아직 안 됨
        po.create_batch(eng, m["mall_id"], by="t")
    v = podoc.public_view(eng, no2, key, "ip")
    assert v["po"]["status"] == "cancel_requested" and v["po"]["cancel_reason"] == "발주처 행사 취소"
    with pytest.raises(corp.MallError, match="취소 확인"):
        podoc.respond(eng, no2, key, "ip", action="accept", name="물류", agree=True)
    with pytest.raises(corp.MallError, match="취소 요청 중"):
        podoc.supplier_file(eng, no2, key, "ip")
    # 철회 → 원래 상태, 다시 요청 → 운영자 확인 표시로 취소
    assert podoc.withdraw_cancel(eng, m["mall_id"], no2, by="op")["status"] == "issued"
    podoc.cancel(eng, m["mall_id"], no2, by="op", reason="다시 취소")
    with pytest.raises(corp.MallError, match="어떻게 취소를"):
        podoc.confirm_cancel(eng, m["mall_id"], no2, by="op", note="")
    # 3) 공급사가 확인 화면에서 '취소 확인'
    done = podoc.respond(eng, no2, key, "ip", action="cancel_ok", name="물류팀 김")
    assert done["status"] == "cancelled" and done["history"][-1]["what"] == "cancel_confirmed_by_supplier"
    assert {o["ship_status"] for o in corp.orders(eng, m["mall_id"])} == {"requested"}
    with pytest.raises(corp.MallError, match="맞지 않거나"):  # 취소 뒤 링크 닫힘
        podoc.public_view(eng, no2, key, "ip4")
    # 4) 운영자 확인 표시
    no3 = po.create_batch(eng, m["mall_id"], by="t")["pos"][0]
    podoc.ack_link(eng, m["mall_id"], no3)
    podoc.cancel(eng, m["mall_id"], no3, by="op", reason="수량 변경")
    ok = podoc.confirm_cancel(eng, m["mall_id"], no3, by="op", note="11/26 전화 — 출고 전 확인")
    assert ok["status"] == "cancelled" and "11/26 전화" in ok["history"][-1]["by"]
    assert po.create_batch(eng, m["mall_id"], by="t")["orders"] == 2  # 재발주


def test_routes(eng):
    from app.main import app

    cl = TestClient(app)
    assert cl.get("/admin/api/b2b-suppliers").status_code == 401
    r = cl.post(
        "/admin/api/b2b-suppliers",
        headers=H,
        json={
            "name": f"라우트식품-{os.getpid()}",
            "biz_no": "1234567890",
            "contact": {"email": "po@example.com"},
            "lead_days": 2,
        },
    )
    sid = r.json()["supplier"]["supplier_id"]
    assert "po@example.com" not in repr(cl.get("/admin/api/b2b-suppliers", headers=H).json()["suppliers"])
    assert (
        cl.get(f"/admin/api/b2b-suppliers/{sid}", headers=H).json()["supplier"]["contact"]["email"] == "po@example.com"
    )
    assert cl.post("/admin/api/b2b-suppliers", headers=H, json={"name": "x", "zzz": 1}).status_code == 422
    m, codes = _mall(eng, "s-route")
    base = f"/admin/api/corpmall/{m['mall_id']}"
    assert cl.post(
        f"{base}/suppliers", headers=H, json={"suppliers": {"A": {"supplier_id": sid, "unit_cost": 9000}}}
    ).json()["ok"]
    corp.choose(eng, "s-route", codes[0][1], "A", "ip", shipping=SHIP, consent=True, at=IN)
    cl.post(f"{base}/po", headers=H)
    no = cl.get(f"{base}/pos", headers=H).json()["pos"][0]["po_no"]
    link = cl.post(f"{base}/pos/{no}/ack-link", headers=H).json()["link"]
    page = cl.get(f"/corp/po/{no}")
    assert page.status_code == 200 and "noindex" in page.headers["x-robots-tag"]
    key = link.split("#k=")[1]
    assert cl.post(f"/corp/api/po/{no}/view", json={"key": key}).json()["po"]["total"] == 9900
    assert not cl.post(f"/corp/api/po/{no}/ack", json={"key": key, "name": "물류팀"}).json()[
        "ok"
    ]  # 동의 없이 수락 안 됨
    ack = cl.post(f"/corp/api/po/{no}/ack", json={"key": key, "name": "물류팀", "agree": True}).json()
    assert ack["ok"] and ack["po"]["status"] == "accepted"
    assert cl.post(f"/corp/api/po/{no}/ack", json={"key": key, "name": "x", "action": "zzz"}).status_code == 422
    assert cl.post(f"/corp/api/po/{no}/view", json={"key": "bad"}).status_code == 400
    req = cl.post(f"{base}/pos/{no}/cancel", headers=H, json={"reason": "시험"}).json()["po"]
    assert req["status"] == "cancel_requested"  # 이미 링크로 전달됨
    assert cl.post(f"{base}/pos/{no}/cancel-confirm", headers=H, json={"note": ""}).status_code == 422
    done = cl.post(f"/corp/api/po/{no}/ack", json={"key": key, "name": "물류팀", "action": "cancel_ok"}).json()
    assert done["ok"] and done["po"]["status"] == "cancelled"
    assert cl.post(f"{base}/pos/{no}/finalize", headers=H).status_code == 400
