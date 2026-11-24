"""폐쇄몰 공급사별 발주서·송장 회수 (2026-11-24) + 직원 화면 우편번호 찾기."""

from __future__ import annotations

import io
import os
from datetime import datetime

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from openpyxl import Workbook, load_workbook

os.environ.setdefault("CORPMALL_KEY", Fernet.generate_key().decode())

from app.services.corpmall import po  # noqa: E402
from app.services.corpmall import store as corp  # noqa: E402

KST = corp.KST
IN = datetime(2026, 12, 3, 10, 0, tzinfo=KST)
SHIP = {
    "name": "홍길동",
    "phone": "010-1234-5678",
    "zipcode": "04524",
    "address": "서울 중구 세종대로 110 3층",
    "memo": "=HYPERLINK(\"x\")",
}
H = {"X-Access-Token": "test-token"}


@pytest.fixture
def eng(tmp_path, monkeypatch):
    monkeypatch.setenv("CS_DIR", str(tmp_path / "cs"))
    monkeypatch.setenv("OPERATOR_NOTIFY", "off")
    corp.reset_limits()
    return corp.engine()


def _mall(eng, slug, mode="individual", n=3):
    m = corp.create_mall(
        eng,
        {
            "slug": slug,
            "client": "샘플공사",
            "opens_at": "2026-12-01T09:00",
            "closes_at": "2026-12-10T18:00",
            "delivery_mode": mode,
            "default_item_id": "A",
            "items": [{"id": "A", "name": "한과"}, {"id": "B", "name": "감귤"}, {"id": "C", "name": "김"}],
        },
    )
    corp.set_status(eng, m["mall_id"], "open")
    return m, corp.issue_codes(eng, m["mall_id"], n)


def _sheets(data: bytes) -> dict[str, list[list]]:
    wb = load_workbook(io.BytesIO(data))
    return {ws.title: [list(r) for r in ws.iter_rows(values_only=True)] for ws in wb.worksheets}


def test_suppliers_are_internal_only(eng):
    m, codes = _mall(eng, "p-sup")
    with pytest.raises(corp.MallError, match="없는 상품"):
        po.set_suppliers(eng, m["mall_id"], {"Z": {"supplier": "x"}})
    got = po.set_suppliers(
        eng, m["mall_id"], {"A": {"supplier": "가나식품", "sku": "HG-18"}, "B": {"supplier": "제주농원"}}
    )
    assert got[0] == {"id": "A", "name": "한과", "supplier": "가나식품", "sku": "HG-18"}
    pub = corp.enter(eng, "p-sup", codes[0][1], "ip", at=IN)["mall"]
    assert "가나식품" not in repr(pub) and "HG-18" not in repr(pub)


def test_individual_po_splits_by_supplier_and_marks_exported(eng):
    m, codes = _mall(eng, "p-ind")
    po.set_suppliers(eng, m["mall_id"], {"A": {"supplier": "가나식품", "sku": "HG-18"}, "B": {"supplier": "제주농원"}})
    for (_, code, _), item in zip(codes, "ABC", strict=True):
        corp.choose(eng, "p-ind", code, item, "ip", shipping=SHIP, consent=True, at=IN)
    data, summary = po.build(eng, m["mall_id"], by="t")
    assert summary == {"orders": 3, "suppliers": 3, "unassigned": 1}
    sh = _sheets(data)
    assert list(sh) == ["요약", "가나식품", "제주농원", po.UNASSIGNED]
    row = sh["가나식품"][1]
    assert row[1] == "한과" and row[2] == "HG-18" and row[4] == "홍길동" and row[7] == "서울 중구 세종대로 110 3층"
    assert row[8] == "'=HYPERLINK(\"x\")"  # 수식으로 들어가지 않음
    assert sh["가나식품"][0][-1] == "송장" and row[-1] in (None, "")
    assert {o["ship_status"] for o in corp.orders(eng, m["mall_id"])} == {"exported"}
    with pytest.raises(corp.MallError, match="넣을 주문이 없어요"):
        po.build(eng, m["mall_id"], by="t")
    ev = corp.events(eng, m["mall_id"])
    assert any(e["kind"] == "po_exported" for e in ev) and "홍길동" not in repr(ev)


def test_bulk_po_only_after_close_with_quantities(eng):
    m, codes = _mall(eng, "p-bulk", mode="bulk")
    po.set_suppliers(eng, m["mall_id"], {i: {"supplier": "가나식품"} for i in "ABC"})
    corp.choose(eng, "p-bulk", codes[0][1], "B", "ip", at=IN)
    with pytest.raises(corp.MallError, match="마감한 뒤"):
        po.build(eng, m["mall_id"], by="t")
    corp.close_mall(eng, m["mall_id"])  # 나머지 2개는 기본 선물(A)
    data, summary = po.build(eng, m["mall_id"], by="t")
    sh = _sheets(data)
    rows = {r[0]: r[2] for r in sh["가나식품"][1:]}
    assert rows == {"감귤": 1, "한과": 2} and summary["orders"] == 3
    assert "수령지" in sh["가나식품"][0][3]


def test_tracking_file_round_trip(eng):
    m, codes = _mall(eng, "p-trk")
    po.set_suppliers(eng, m["mall_id"], {"A": {"supplier": "가나식품"}})
    corp.choose(eng, "p-trk", codes[0][1], "A", "ip", shipping=SHIP, consent=True, at=IN)
    data, _ = po.build(eng, m["mall_id"], by="t")
    wb = load_workbook(io.BytesIO(data))
    ws = wb["가나식품"]
    ws.cell(row=2, column=10, value=123456789012)  # 공급사가 숫자로 채움
    buf = io.BytesIO()
    wb.save(buf)
    rows = po.read_tracking("발주서_회신.xlsx", buf.getvalue())
    assert rows == [{"order_id": corp.orders(eng, m["mall_id"])[0]["order_id"], "tracking": "123456789012"}]
    csv_rows = po.read_tracking("x.csv", f"주문번호,송장번호\n{rows[0]['order_id']},9999-1\nOBAD,1\n".encode())
    assert csv_rows == [{"order_id": rows[0]["order_id"], "tracking": "9999-1"}]
    wb2 = Workbook()
    wb2.active.append(["아무", "칸"])
    b2 = io.BytesIO()
    wb2.save(b2)
    assert po.read_tracking("x.xlsx", b2.getvalue()) == []


def test_routes(eng):
    from app.main import app

    cl = TestClient(app)
    m, codes = _mall(eng, "p-route")
    assert cl.post(f"/admin/api/corpmall/{m['mall_id']}/po").status_code == 401
    assert cl.post(
        f"/admin/api/corpmall/{m['mall_id']}/suppliers", json={"suppliers": {"A": {"supplier": "가나식품"}}}, headers=H
    ).json()["ok"]
    assert cl.post(f"/admin/api/corpmall/{m['mall_id']}/po", headers=H).status_code == 400  # 주문 없음
    corp.choose(eng, "p-route", codes[0][1], "A", "ip", shipping=SHIP, consent=True, at=IN)
    r = cl.post(f"/admin/api/corpmall/{m['mall_id']}/po", headers=H)
    assert r.status_code == 200 and r.headers["x-po-summary"] == "1,1,0" and r.headers["cache-control"] == "no-store"
    assert "attachment" in r.headers["content-disposition"]
    oid = corp.orders(eng, m["mall_id"])[0]["order_id"]
    up = cl.post(
        f"/admin/api/corpmall/{m['mall_id']}/tracking-file",
        headers=H,
        files={"file": ("회신.csv", f"주문 번호,송장\n{oid},5555\n".encode(), "text/csv")},
        data={"shipped": "true"},
    )
    assert up.json() == {"ok": True, "read": 1, "n": 1, "skipped": 0}
    assert corp.orders(eng, m["mall_id"])[0]["ship_status"] == "shipped"
    bad = cl.post(
        f"/admin/api/corpmall/{m['mall_id']}/tracking-file",
        headers=H,
        files={"file": ("x.csv", b"a,b\n1,2\n", "text/csv")},
    )
    assert bad.status_code == 400


def test_employee_page_postcode_search_loads_only_on_click():
    from app.main import app

    cl = TestClient(app)
    r = cl.get("/corp/p-page")
    assert r.status_code == 200 and r.headers["referrer-policy"] == "strict-origin"
    html = r.text
    assert "t1.kakaocdn.net/mapjsapi/bundle/postcode/prod/postcode.v2.js" in html and 'id="zipBtn"' in html
    assert '<script src="https://t1.kakaocdn.net' not in html  # 처음부터 불러오지 않음(버튼 누를 때만)
    assert 'id="s_addr2"' in html and 'content="strict-origin"' in html
