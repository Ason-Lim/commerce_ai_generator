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
    assert got[0] == {
        "id": "A",
        "name": "한과",
        "supplier_id": None,
        "supplier": "가나식품",
        "sku": "HG-18",
        "unit_cost": None,
    }
    pub = corp.enter(eng, "p-sup", codes[0][1], "ip", at=IN)["mall"]
    assert "가나식품" not in repr(pub) and "HG-18" not in repr(pub)


def _batch(eng, mall_id):
    b = po.create_batch(eng, mall_id, by="t")
    return b, _sheets(po.render(eng, mall_id, b["batch_id"])[0])


def test_individual_batch_excludes_unassigned_and_splits_files(eng):
    m, codes = _mall(eng, "p-ind")
    po.set_suppliers(eng, m["mall_id"], {"A": {"supplier": "가나식품", "sku": "0012"}, "B": {"supplier": "제주농원"}})
    for (_, code, _), item in zip(codes, "ABC", strict=True):
        corp.choose(eng, "p-ind", code, item, "ip", shipping=SHIP, consent=True, at=IN)
    b, sh = _batch(eng, m["mall_id"])
    assert (
        b["orders"] == 2 and set(b["suppliers"]) == {"가나식품", "제주농원"} and b["excluded"] == {"공급사 미지정": 1}
    )
    assert list(sh) == ["요약", "가나식품", "제주농원"]
    row = sh["가나식품"][1]
    assert row[1] == "한과" and row[2] == "0012" and row[4] == "홍길동" and row[5] == "010-1234-5678"
    assert row[6] == "04524" and row[8] == "'=HYPERLINK(\"x\")"  # 텍스트 셀(앞자리 0 유지), 수식 막기
    wb = load_workbook(io.BytesIO(po.render(eng, m["mall_id"], b["batch_id"])[0]))
    assert wb["가나식품"].cell(row=2, column=7).number_format == "@"
    st = {o["item_id"]: o["ship_status"] for o in corp.orders(eng, m["mall_id"])}
    assert st == {"A": "exported", "B": "exported", "C": "requested"}  # 미지정은 그대로 남음
    # 공급사 전달용 파일에는 그 공급사 것만
    one = _sheets(po.render(eng, m["mall_id"], b["batch_id"], supplier="제주농원")[0])
    assert list(one) == ["발주서", "제주농원"] and "한과" not in repr(one) and len(one["제주농원"]) == 2
    with pytest.raises(corp.MallError, match="이 묶음에 없어요"):
        po.render(eng, m["mall_id"], b["batch_id"], supplier="다른공급사")
    # 다시 받기 — 같은 내용
    assert _sheets(po.render(eng, m["mall_id"], b["batch_id"])[0]) == sh
    with pytest.raises(corp.MallError, match="공급사 미지정 1건"):
        po.create_batch(eng, m["mall_id"], by="t")
    po.set_suppliers(eng, m["mall_id"], {"C": {"supplier": "바다김"}})
    b2 = po.create_batch(eng, m["mall_id"], by="t")
    assert b2["orders"] == 1 and [x["batch_id"] for x in po.list_batches(eng, m["mall_id"])][0] == b2["batch_id"]
    ev = corp.events(eng, m["mall_id"])
    assert {"po_batch", "po_download"} <= {e["kind"] for e in ev} and "홍길동" not in repr(ev)


def test_bulk_batch_only_after_close_with_quantities(eng):
    m, codes = _mall(eng, "p-bulk", mode="bulk")
    po.set_suppliers(eng, m["mall_id"], {i: {"supplier": "가나식품"} for i in "ABC"})
    corp.choose(eng, "p-bulk", codes[0][1], "B", "ip", at=IN)
    with pytest.raises(corp.MallError, match="마감한 뒤"):
        po.create_batch(eng, m["mall_id"], by="t")
    corp.close_mall(eng, m["mall_id"])  # 나머지 2개는 기본 선물(A)
    b, sh = _batch(eng, m["mall_id"])
    assert {r[0]: r[2] for r in sh["가나식품"][1:]} == {"감귤": 1, "한과": 2} and b["orders"] == 3
    assert "수령지" in sh["가나식품"][0][3]


def test_tracking_file_round_trip_and_problems(eng):
    m, codes = _mall(eng, "p-trk")
    po.set_suppliers(eng, m["mall_id"], {"A": {"supplier": "가나식품"}, "B": {"supplier": "가나식품"}})
    corp.choose(eng, "p-trk", codes[0][1], "A", "ip", shipping=SHIP, consent=True, at=IN)
    corp.choose(eng, "p-trk", codes[1][1], "B", "ip", shipping=SHIP, consent=True, at=IN)
    b = po.create_batch(eng, m["mall_id"], by="t")
    wb = load_workbook(io.BytesIO(po.render(eng, m["mall_id"], b["batch_id"], supplier="가나식품")[0]))
    ws = wb["가나식품"]
    ws.cell(row=2, column=10, value="012345678901")  # 텍스트로 채움 — 앞자리 0 유지
    ws.cell(row=3, column=10, value=123456789012)  # 숫자로 바뀜 — 자동 복원하지 않음
    buf = io.BytesIO()
    wb.save(buf)
    rows, problems = po.read_tracking("발주서_회신.xlsx", buf.getvalue())
    oid1, oid2 = ws.cell(row=2, column=1).value, ws.cell(row=3, column=1).value
    assert rows == [{"order_id": oid1, "tracking": "012345678901"}]
    assert problems[0]["order_id"] == oid2 and "숫자" in problems[0]["why"]
    csv_rows, csv_problems = po.read_tracking(
        "x.csv", f"주문번호,송장번호\n{oid1},9999-1\n{oid1},8888\n{oid2},1.23457E+11\nOBAD,1\n".encode()
    )
    assert csv_rows == [] and {p["order_id"] for p in csv_problems} == {oid1, oid2}
    wb2 = Workbook()
    wb2.active.append(["아무", "칸"])
    b2 = io.BytesIO()
    wb2.save(b2)
    assert po.read_tracking("x.xlsx", b2.getvalue()) == ([], [])


def test_set_tracking_same_conflict_and_no_regress(eng):
    m, codes = _mall(eng, "p-conf")
    po.set_suppliers(eng, m["mall_id"], {"A": {"supplier": "가나식품"}})
    corp.choose(eng, "p-conf", codes[0][1], "A", "ip", shipping=SHIP, consent=True, at=IN)
    oid = corp.orders(eng, m["mall_id"])[0]["order_id"]
    assert corp.set_tracking(eng, m["mall_id"], [{"order_id": oid, "tracking": "111"}], shipped=True)["n"] == 1
    again = corp.set_tracking(eng, m["mall_id"], [{"order_id": oid, "tracking": "111"}], shipped=True)
    assert again == {"n": 0, "skipped": 0, "same": 1, "conflicts": []}  # 같은 파일 다시 올림 — 처리 안 함
    diff = corp.set_tracking(eng, m["mall_id"], [{"order_id": oid, "tracking": "222"}])
    assert diff["conflicts"] == [{"order_id": oid, "now": "111", "file": "222"}]
    assert corp.orders(eng, m["mall_id"])[0]["tracking"] == "111"  # 덮어쓰지 않음
    corp.mark(eng, m["mall_id"], [oid], "delivered")
    assert corp.set_tracking(eng, m["mall_id"], [{"order_id": oid, "tracking": "111"}], shipped=True)["skipped"] == 1
    assert corp.orders(eng, m["mall_id"])[0]["ship_status"] == "delivered"  # 되돌아가지 않음


def test_routes(eng):
    from app.main import app

    cl = TestClient(app)
    m, codes = _mall(eng, "p-route")
    base = f"/admin/api/corpmall/{m['mall_id']}"
    assert cl.post(f"{base}/po").status_code == 401
    assert cl.post(f"{base}/suppliers", json={"suppliers": {"A": {"supplier": "가나식품"}}}, headers=H).json()["ok"]
    assert cl.post(f"{base}/po", headers=H).status_code == 400  # 주문 없음
    corp.choose(eng, "p-route", codes[0][1], "A", "ip", shipping=SHIP, consent=True, at=IN)
    b = cl.post(f"{base}/po", headers=H).json()
    assert b["ok"] and b["orders"] == 1
    assert cl.get(f"{base}/po", headers=H).json()["batches"][0]["batch_id"] == b["batch_id"]
    f = cl.get(f"{base}/po/{b['batch_id']}/file", params={"supplier": "가나식품"}, headers=H)
    assert (
        f.status_code == 200
        and f.headers["cache-control"] == "no-store"
        and "attachment" in f.headers["content-disposition"]
    )
    assert cl.get(f"{base}/po/NOPE/file", headers=H).status_code == 404
    oid = corp.orders(eng, m["mall_id"])[0]["order_id"]
    up = cl.post(
        f"{base}/tracking-file",
        headers=H,
        files={"file": ("회신.csv", f"주문 번호,송장\n{oid},5555\n".encode(), "text/csv")},
        data={"shipped": "true"},
    )
    assert up.json() == {"ok": True, "read": 1, "problems": [], "n": 1, "skipped": 0, "same": 0, "conflicts": []}
    assert corp.orders(eng, m["mall_id"])[0]["ship_status"] == "shipped"
    bad = cl.post(f"{base}/tracking-file", headers=H, files={"file": ("x.csv", b"a,b\n1,2\n", "text/csv")})
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
