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
    m, codes = _mall(eng, "s-ack")
    po.set_suppliers(eng, m["mall_id"], {"A": {"supplier_id": s["supplier_id"], "unit_cost": 5000}})
    corp.choose(eng, "s-ack", codes[0][1], "A", "ip", shipping=SHIP, consent=True, at=IN)
    po.create_batch(eng, m["mall_id"], by="t")
    no = podoc.list_pos(eng, m["mall_id"])[0]["po_no"]
    link = podoc.ack_link(eng, m["mall_id"], no)
    key = link.split("#k=")[1]
    with eng.connect() as c:
        assert key not in repr(c.execute(select(corp.t_po)).mappings().all())
    v = podoc.public_view(eng, no, key, "ip")
    assert v["po"]["po_no"] == no and "홍길동" not in repr(v) and "010-1234" not in repr(v)
    with pytest.raises(corp.MallError, match="이름"):
        podoc.acknowledge(eng, no, key, "ip", name=" ")
    got = podoc.acknowledge(eng, no, key, "ip", name="물류팀 김", ship_date="2026-12-14", memo="연락 010-9999-8888")
    first_at = got["ack_at"]
    assert got["status"] == "acknowledged" and got["ack_ship_date"] == "2026-12-14" and "8888" not in got["ack_memo"]
    again = podoc.acknowledge(eng, no, key, "ip", name="물류팀 김", ship_date="2026-12-15")
    assert again["ack_at"] == first_at and again["ack_ship_date"] == "2026-12-15"  # 확인 시각은 처음 값
    new_key = podoc.ack_link(eng, m["mall_id"], no).split("#k=")[1]  # 새로 만들면 옛 링크 막힘
    with pytest.raises(corp.MallError, match="맞지 않거나"):
        podoc.public_view(eng, no, key, "ip2")
    assert podoc.public_view(eng, no, new_key, "ip3")["po"]["status"] == "acknowledged"


def test_operator_mark_and_cancel_returns_orders(eng):
    s = _sup(eng, f"취소식품-{os.getpid()}")
    m, codes = _mall(eng, "s-cx")
    po.set_suppliers(eng, m["mall_id"], {"A": {"supplier_id": s["supplier_id"], "unit_cost": 5000}})
    corp.choose(eng, "s-cx", codes[0][1], "A", "ip", shipping=SHIP, consent=True, at=IN)
    corp.choose(eng, "s-cx", codes[1][1], "A", "ip", shipping=SHIP, consent=True, at=IN)
    po.create_batch(eng, m["mall_id"], by="t")
    no = podoc.list_pos(eng, m["mall_id"])[0]["po_no"]
    with pytest.raises(corp.MallError, match="이유"):
        podoc.cancel(eng, m["mall_id"], no, by="op", reason="")
    oid = corp.orders(eng, m["mall_id"])[0]["order_id"]
    corp.set_tracking(eng, m["mall_id"], [{"order_id": oid, "tracking": "777"}])
    with pytest.raises(corp.MallError, match="송장이 들어갔거나"):
        podoc.cancel(eng, m["mall_id"], no, by="op", reason="품절")
    with corp.engine().begin() as c:  # 시험: 송장 지우고 다시
        c.execute(corp.t_order.update().where(corp.t_order.c.order_id == oid).values(tracking=None))
    got = podoc.cancel(eng, m["mall_id"], no, by="op", reason="품절로 다른 거래처")
    assert got["status"] == "cancelled"
    assert {o["ship_status"] for o in corp.orders(eng, m["mall_id"])} == {"requested"}
    b2 = po.create_batch(eng, m["mall_id"], by="t")  # 다시 묶을 수 있음
    assert b2["orders"] == 2
    no2 = b2["pos"][0]
    assert podoc.mark_ack(eng, m["mall_id"], no2, by="op", note="11/25 메일 회신")["ack_via"] == "operator"
    with pytest.raises(corp.MallError, match="확인 전"):
        podoc.mark_ack(eng, m["mall_id"], no2, by="op")


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
    ack = cl.post(f"/corp/api/po/{no}/ack", json={"key": key, "name": "물류팀"}).json()
    assert ack["ok"] and ack["po"]["status"] == "acknowledged"
    assert cl.post(f"/corp/api/po/{no}/view", json={"key": "bad"}).status_code == 400
    assert cl.post(f"{base}/pos/{no}/cancel", headers=H, json={"reason": "시험"}).json()["po"]["status"] == "cancelled"
