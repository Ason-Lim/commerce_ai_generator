"""판매처 엑셀 변환기 (2026-11-26) — .xlsx·EUC-KR CSV·표준 칸, 모르는 양식은 멈춤, 같은 이름·다른 용량 묶기, 미리보기는 저장 안 함."""

from __future__ import annotations

import base64
import io

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook

from app.services.seller import catalog
from app.services.seller import convert as CV
from app.services.seller import products as prod
from app.services.seller import store as sel
from tests.admin.test_seller_naver_export_2026_11_25 import COLS, IP, _seller, csv_of, eng, row  # noqa: F401

ROWS = [
    row(
        **{
            "상품번호(스마트스토어)": "2001",
            "상품명": "가짜 우드바니쉬 목재보호 200ml[소용량/개인용]",
            "할인가": "9000",
        }
    ),
    row(
        **{"상품번호(스마트스토어)": "2002", "상품명": "가짜 우드 바니쉬 목재보호 1L[소용량/개인용]", "할인가": "35000"}
    ),
    row(
        **{
            "상품번호(스마트스토어)": "2003",
            "상품명": "가짜 우드바니쉬 목재보호 5L[대용량/전문가용]",
            "할인가": "160000",
        }
    ),
    row(
        **{"상품번호(스마트스토어)": "2004", "상품명": "가짜 오일 마감재 1L", "할인가": "45000", "판매상태": "판매중지"}
    ),
    row(**{"상품번호(스마트스토어)": "2005", "상품명": "가짜 UV 코팅제 1L", "할인가": "40000"}),
    row(**{"상품번호(스마트스토어)": "2006", "상품명": "가짜 UV 코팅제 1L 새 포장", "할인가": "41000"}),
]


def b64(b: bytes) -> str:
    return base64.b64encode(b).decode()


def _xlsx(text: str, junk_top=True) -> bytes:
    wb = Workbook()
    ws = wb.active
    if junk_top:
        ws.append(["상품 조회 결과"])  # 위쪽 안내 줄
    for line in text.lstrip("﻿").splitlines():
        ws.append(line.split(","))
    b = io.BytesIO()
    wb.save(b)
    return b.getvalue()


def test_groups_same_name_different_volume():
    rows, notes = catalog.naver_export_rows(csv_of(*ROWS), group_same=True)
    g = list(notes["groups"].values())
    assert (
        len(g) == 1
        and g[0]["name"] == "가짜 우드바니쉬 목재보호"
        and [u["volume"] for u in g[0]["units"]] == ["200ml", "1L", "5L"]
    )
    by = {r["ext_no"]: r for r in rows}
    assert by["2001"]["group_no"] == by["2003"]["group_no"] and by["2001"]["option"] == "200ml"
    assert not by["2004"]["group_no"] and not by["2005"]["group_no"]  # 같은 용량이 겹치면 묶지 않음
    plain, _ = catalog.naver_export_rows(csv_of(*ROWS))
    assert not any(r["group_no"] for r in plain)  # 고르지 않으면 그대로
    assert catalog.base_name("가짜 우드 바니쉬 1L[소용량]") == catalog.base_name("가짜 우드바니쉬 5L")


def test_read_xlsx_cp949_and_unknown(eng):
    text = csv_of(*ROWS)
    assert CV.detect(CV.read_file("p.xlsx", b64(_xlsx(text))))[0] == "naver_export"
    assert CV.detect(CV.read_file("p.csv", b64(text.lstrip("﻿").encode("cp949"))))[0] == "naver_export"
    with pytest.raises(sel.SellerError, match="모르는 판매처 양식"):
        CV.detect(CV.read_file("x.csv", b64("업체상품코드,노출상품명,판매가격\n1,가,100\n".encode())))
    with pytest.raises(sel.SellerError, match=r"\.xls"):
        CV.read_file("old.xls", b64(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"0" * 20))
    with pytest.raises(sel.SellerError, match="5MB"):
        CV.read_file("big.csv", b64(b"0" * (5 * 1024 * 1024 + 1)))


def test_preview_saves_nothing_then_sync_groups(eng):
    s, k = _seller(eng)
    pv = CV.preview(eng, k, IP, "상품.xlsx", "data:application/octet-stream;base64," + b64(_xlsx(csv_of(*ROWS))))
    assert pv["rows"] == 6 and len(pv["groups"]) == 1 and any("판매 꺼짐" in n for n in pv["notes"])
    assert prod.list_mine(eng, k, IP) == []  # 미리보기는 저장 안 함
    got = catalog.import_std_csv(eng, k, IP, "naver", pv["csv"], group_same=True)
    assert got["ok"] and got["added"] == 6 and got["groups"] == 1
    units = catalog.units_of(eng, s["seller_id"])
    gids = {u["group_id"] for u in units.values() if u["ext_no"] in ("2001", "2002", "2003")}
    assert len(gids) == 1 and len({u["group_id"] for u in units.values()}) == 4


def test_route(eng):
    from app.main import app

    _s, k = _seller(eng)
    c = TestClient(app)
    j = c.post("/seller/api/convert", json={"key": k, "filename": "p.csv", "data": b64(csv_of(*ROWS).encode())}).json()
    assert j["ok"] and j["convert"]["label"] == "스마트스토어 상품 조회 파일" and j["convert"]["sample"][0]["group"]
    r = c.post(
        "/seller/api/sync", json={"key": k, "channel": "naver", "csv": j["convert"]["csv"], "group_same": True}
    ).json()
    assert r["ok"] and r["groups"] == 1
    assert 'id="syncGroup"' in c.get("/seller").text
