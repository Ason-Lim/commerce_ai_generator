"""셀러 SCM ③ (창 5, 2026-11-25) — 재고·품절 · 공급사 · 주문 CSV · 발주서 · 송장 · 알림 · 격리 · 개인정보."""

from __future__ import annotations

import io
import os
from datetime import datetime, timedelta

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from openpyxl import load_workbook

os.environ.setdefault("CORPMALL_KEY", Fernet.generate_key().decode())

from app.services.corpmall import store as corp  # noqa: E402
from app.services.seller import products as prod  # noqa: E402
from app.services.seller import scm  # noqa: E402
from app.services.seller import store as sel  # noqa: E402

H = {"X-Access-Token": "test-token"}
IP = "1.1.1.1"
KST = sel.KST
P = {"name": "제주 감귤 5kg", "volume": "5kg", "price": "23900", "origin": "제주"}


@pytest.fixture
def eng():
    corp.reset_limits()
    e = scm.engine()
    with e.begin() as c:
        for t in (scm.t_order, scm.t_batch, scm.t_supply, scm.t_supplier, scm.t_stock, prod.t_product,
                  sel.t_event, sel.t_key, sel.t_seller):  # fmt: skip
            c.execute(t.delete())
    return e


@pytest.fixture
def client():
    from app.main import app

    return TestClient(app)


def _seller(eng, name="가농장"):
    s = sel.create_seller(eng, name=name, kind="consign", contact={"name": "김", "email": "k@a.kr"}, by="operator")
    sel.set_status(eng, s["seller_id"], "active", by="operator", reason="ok")
    k = sel.issue_key(eng, s["seller_id"], by="operator")["code"]
    p = prod.save(eng, k, IP, P)
    return s, k, p["product_id"]


def _csv(pid, *lines):
    head = "판매처 주문번호,상품 번호,수량,받는 분,휴대폰,우편번호,주소,배송 메모,주문일\n"
    return head + "".join(
        f"{no},{pid},{q},홍길동,010-1234-5678,04524,서울 중구 세종대로 110,{memo},{od}\n" for no, q, memo, od in lines
    )


# ── 재고·품절 ──
def test_stock_zero_is_sold_out_and_alert_only_for_approved(eng):
    s, k, pid = _seller(eng)
    got = scm.set_stock(eng, k, IP, pid, stock="0", sold_out=False, restock_on="2026-12-05")
    assert got["sold_out"] is True and got["restock_on"] == "2026-12-05"
    assert scm.my_alerts(eng, k, IP)["sold_out"] == []  # 아직 검수 대기 상품
    prod.review(eng, pid, "approved", by="operator")
    assert [x["product_id"] for x in scm.my_alerts(eng, k, IP)["sold_out"]] == [pid]
    with pytest.raises(sel.SellerError, match="입고 예정일"):
        scm.set_stock(eng, k, IP, pid, stock=3, sold_out=False, restock_on="12/5")


# ── 주문 CSV ──
def test_order_csv_needs_entrust_and_is_all_or_nothing(eng):
    _, k, pid = _seller(eng)
    with pytest.raises(sel.SellerError, match="맡긴다는 확인"):
        scm.import_orders(eng, k, IP, _csv(pid, ("N1", 1, "", "2026-11-25")), entrust_ok=False)
    bad = _csv(pid, ("N1", 1, "", "2026-11-25")) + "N2,P00000000,1,김,010-1111-2222,,서울,,\n"
    got = scm.import_orders(eng, k, IP, bad, entrust_ok=True)
    assert got["ok"] is False and got["errors"][0]["line"] == 3 and scm.list_orders(eng, k, IP) == []
    got = scm.import_orders(
        eng, k, IP, _csv(pid, ("N1", 1, "", "2026-11-25"), ("N2", 2, "경비실", "2026-11-25")), entrust_ok=True
    )
    assert got == {"ok": True, "added": 2, "skipped": 0, "errors": []}
    again = scm.import_orders(eng, k, IP, _csv(pid, ("N1", 1, "", "2026-11-25")), entrust_ok=True)
    assert again["added"] == 0 and again["skipped"] == 1


def test_recipient_encrypted_and_masked(eng):
    _, k, pid = _seller(eng)
    scm.import_orders(eng, k, IP, _csv(pid, ("N1", 1, "", "2026-11-25")), entrust_ok=True)
    with eng.connect() as c:
        raw = c.execute(scm.t_order.select()).mappings().first()["ship_enc"]
    assert "홍길동" not in raw and "010-1234" not in raw and "세종대로" not in raw
    o = scm.list_orders(eng, k, IP)[0]
    assert o["recipient"].startswith("홍**") and "5678" in o["recipient"] and "1234" not in o["recipient"]


def test_order_csv_rejects_other_sellers_product(eng):
    _, ka, pa = _seller(eng, "가농장")
    _, kb, _ = _seller(eng, "나수산")
    got = scm.import_orders(eng, kb, IP, _csv(pa, ("N1", 1, "", "")), entrust_ok=True)
    assert got["ok"] is False and "내 상품 번호가 아니에요" in got["errors"][0]["error"]


# ── 공급사 · 발주서 · 송장 ──
def test_po_sheet_per_supplier_then_tracking(eng):
    _, k, pid = _seller(eng)
    p2 = prod.save(eng, k, IP, {**P, "name": "고흥 유자청"})["product_id"]
    v = scm.save_supplier(eng, k, IP, name="한라농원", contact={"name": "박", "email": "p@hanla.kr"})
    scm.set_supply(eng, k, IP, pid, supplier_id=v["supplier_id"], sku="HL-05")
    scm.import_orders(eng, k, IP, _csv(pid, ("N1", 1, "", "2026-11-25")) + f"N2,{p2},3,김철수,010-2222-3333,,부산 해운대구,,2026-11-25\n",
                      entrust_ok=True)  # fmt: skip
    b = scm.create_batch(eng, k, IP)
    assert b["n_orders"] == 2 and b["n_suppliers"] == 2
    with pytest.raises(sel.SellerError, match="새 주문이 없어요"):
        scm.create_batch(eng, k, IP)  # 같은 주문이 두 번 묶이지 않음
    data, name = scm.render_batch(eng, k, IP, b["batch_id"])
    wb = load_workbook(io.BytesIO(data))
    assert set(wb.sheetnames) == {"요약", "한라농원", scm.DIRECT}
    ws = wb["한라농원"]
    head = [c.value for c in ws[1]]
    row = [c.value for c in ws[2]]
    assert row[head.index("공급사 품번")] == "HL-05" and row[head.index("받는 분")] == "홍길동"
    assert ws.cell(row=2, column=head.index("휴대폰") + 1).number_format == "@"
    assert all(
        r[head.index("주소")] != "부산 해운대구" for r in ws.iter_rows(min_row=2, values_only=True)
    )  # 공급사별로 나뉨
    assert scm.list_batches(eng, k, IP)[0]["downloads"] == 1
    # 송장 채워 돌려줌
    oid = row[0]
    ws.cell(row=2, column=head.index("송장") + 1, value="612345678901")
    buf = io.BytesIO()
    wb.save(buf)
    got = scm.upload_tracking(eng, k, IP, "back.xlsx", buf.getvalue())
    assert got["set"] == 1 and got["problems"] == []
    o = next(x for x in scm.list_orders(eng, k, IP) if x["order_id"] == oid)
    assert o["status"] == "shipped" and o["tracking"] == "612345678901"


def test_tracking_numeric_cell_and_other_seller_rejected(eng):
    _, ka, pa = _seller(eng, "가농장")
    _, kb, _ = _seller(eng, "나수산")
    scm.import_orders(eng, ka, IP, _csv(pa, ("N1", 1, "", "")), entrust_ok=True)
    scm.create_batch(eng, ka, IP)
    oid = scm.list_orders(eng, ka, IP)[0]["order_id"]
    got = scm.upload_tracking(eng, kb, IP, "t.csv", f"주문 번호,송장\n{oid},612345678901\n".encode())
    assert got["set"] == 0 and "내 주문이 아니에요" in got["problems"][0]["why"]
    got = scm.upload_tracking(eng, ka, IP, "t.csv", f"주문 번호,송장\n{oid},6.12E+11\n".encode())
    assert got["set"] == 0 and "숫자로 바뀌어" in got["problems"][0]["why"]


def test_isolation_batches_and_suppliers(eng):
    _, ka, pa = _seller(eng, "가농장")
    _, kb, pb = _seller(eng, "나수산")
    v = scm.save_supplier(eng, ka, IP, name="한라농원", contact=None)
    with pytest.raises(sel.SellerError, match="없는 공급사"):
        scm.set_supply(eng, kb, IP, pb, supplier_id=v["supplier_id"])
    with pytest.raises(sel.SellerError, match="없는 상품"):
        scm.set_stock(eng, kb, IP, pa, stock=1, sold_out=False, restock_on=None)
    scm.import_orders(eng, ka, IP, _csv(pa, ("N1", 1, "", "")), entrust_ok=True)
    b = scm.create_batch(eng, ka, IP)
    with pytest.raises(sel.SellerError, match="없는 발주 묶음"):
        scm.render_batch(eng, kb, IP, b["batch_id"])
    assert scm.list_orders(eng, kb, IP) == [] and scm.list_suppliers(eng, kb, IP) == []


# ── 지연 알림 ──
def test_delay_after_two_business_days(eng):
    _, k, pid = _seller(eng)
    scm.import_orders(eng, k, IP, _csv(pid, ("N1", 1, "", "2026-11-20")), entrust_ok=True)  # 금요일
    mon = datetime(2026, 11, 23, 10, tzinfo=KST)
    tue = datetime(2026, 11, 24, 10, tzinfo=KST)
    wed = datetime(2026, 11, 25, 10, tzinfo=KST)
    assert scm.my_alerts(eng, k, IP, at=tue)["delayed_orders"] == 0  # 월·화 = 2영업일
    assert scm.my_alerts(eng, k, IP, at=wed)["delayed_orders"] == 1
    assert scm.list_orders(eng, k, IP, at=mon)[0]["delayed"] is False
    al = scm.all_alerts(eng, at=wed)
    assert al[0]["delayed_orders"] == 1 and al[0]["new_orders"] == 1
    assert "홍길동" not in str(al) and "010" not in str(al)


# ── 보존 ──
def test_purge_after_ship_30_days_unshipped_90_days(eng):
    _, k, pid = _seller(eng)
    scm.import_orders(eng, k, IP, _csv(pid, ("N1", 1, "", ""), ("N2", 1, "", "")), entrust_ok=True)
    scm.create_batch(eng, k, IP)
    o1 = scm.list_orders(eng, k, IP)[-1]["order_id"]
    scm.upload_tracking(eng, k, IP, "t.csv", f"주문 번호,송장\n{o1},612345678901\n".encode())
    now = sel.now()
    assert scm.purge(eng, now + timedelta(days=29)) == 0
    assert scm.purge(eng, now + timedelta(days=31)) == 1  # 출고된 주문만
    assert scm.purge(eng, now + timedelta(days=91)) == 1  # 출고 안 된 주문
    assert all(o["recipient"] == "(지움)" for o in scm.list_orders(eng, k, IP))


# ── API · 관리자 ──
def test_api_flow_and_admin_alerts(client, eng):
    _, k, pid = _seller(eng)
    r = client.post(
        "/seller/api/stock",
        json={"key": k, "product_id": pid, "stock": 0, "sold_out": True, "restock_on": "2026-12-01"},
    )
    assert r.json()["stock"]["sold_out"] is True
    r = client.post("/seller/api/orders/csv", json={"key": k, "csv": _csv(pid, ("N1", 1, "", "")), "entrust_ok": True})
    assert r.json()["added"] == 1
    bid = client.post("/seller/api/po", json={"key": k}).json()["batch"]["batch_id"]
    r = client.post("/seller/api/po/file", json={"key": k, "batch_id": bid})
    assert r.status_code == 200 and r.headers["content-type"].startswith("application/vnd.openxmlformats")
    assert "noindex" in r.headers.get("x-robots-tag", "")
    oid = client.post("/seller/api/orders", json={"key": k}).json()["orders"][0]["order_id"]
    r = client.post(
        "/seller/api/tracking",
        data={"key": k},
        files={"file": ("t.csv", f"주문 번호,송장\n{oid},612345678901\n".encode())},
    )
    assert r.json()["set"] == 1
    assert client.post("/seller/api/orders", json={"key": k, "seller_id": "x"}).status_code == 422
    a = client.get("/admin/api/seller-alerts", headers=H).json()["alerts"]
    assert a == [] or "홍길동" not in str(a)
    assert client.get("/admin/api/seller-alerts").status_code in (401, 403)
