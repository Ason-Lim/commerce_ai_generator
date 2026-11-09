"""도매꾹 도매몰 검색 (2026-11-04) — 실제 호출 없음: 응답을 가짜로 둔다.  판매 구분(도매·위탁·소매) 표기도 함께."""
from __future__ import annotations

from datetime import date

import pytest

from app.admin.b2b import domeggook, suppliers
from app.admin.b2b.console import Console

TODAY = date(2026, 11, 4)


def fake(market_seen):
    def get(url):
        market_seen.append(url)
        dome = "market=dome" in url
        return {"domeggook": {"header": {"numberOfItems": 2}, "list": {"item": [
            {"no": "101", "title": "6년근 홍삼정 스틱 30포 선물세트", "price": "18,500", "unitQty": "10", "id": "hong01",
             "nick": "홍삼나라", "comOnly": True, "url": "https://domeggook.com/101", "deli": {"who": "P", "fee": "3000"}},
            {"no": "102", "title": "프로바이오틱스 유산균 60캡슐", "price": 9900, "unitQty": 1 if not dome else 5,
             "id": "bio02", "nick": "바이오팜", "url": "https://domeggook.com/102", "deli": {"who": "S"}},
            {"no": "", "title": "번호 없는 상품", "price": 100},
        ]}}}
    return get


def test_search_maps_wholesale_and_consign():
    seen = []
    dome = domeggook.search("홍삼", "dome", get=fake(seen), key="k" * 32)
    assert [o["no"] for o in dome] == ["101", "102"] and dome[0]["price"] == 18500 and dome[0]["moq"] == 10
    assert dome[0]["business_only"] and dome[0]["ship"] == "배송비 선결제" and dome[1]["ship"] == "무료배송"
    assert "aid=" + "k" * 32 in seen[0] and "kw=%ED%99%8D%EC%82%BC" in seen[0]
    c = domeggook.to_candidate(dome[0], TODAY)
    assert c.price_kind == "wholesale" and c.min_order_qty == 10 and c.source == "domeggook"
    assert c.category == "건강기능식품" and c.unit_price_quote is None          # 도매가는 견적이 아니다
    assert suppliers.sale_type(c.price_kind, c.min_order_qty) == ("wholesale", "도매 · 도매몰 단가 · 최소 10개")
    sup = domeggook.to_candidate(domeggook.search("x", "supply", get=fake([]), key="k")[1], TODAY)
    assert sup.price_kind == "consign" and suppliers.sale_type(sup.price_kind)[0] == "consign"
    with pytest.raises(domeggook.DomeggookError):
        domeggook.search("홍삼", get=fake([]), key="")


def test_sale_types_never_guess():
    assert suppliers.sale_type("public_retail") == ("retail", "소매 · 공개 판매가")
    assert suppliers.sale_type("supplier_quote")[0] == "wholesale"
    assert suppliers.sale_type("weird") == ("unknown", "구분 미확인") and suppliers.sale_type(None)[0] == "unknown"


def test_keyword_extraction():
    k = Console.wholesale_keyword
    assert k("도매꾹에서 홍삼 찾아줘") == "홍삼"
    assert k("도매매에서 프로바이오틱스 위탁 상품 보여줘") == "프로바이오틱스"
    assert k("건강식품 도매몰에서 조회") == "" and k("도매꾹에서 건강기능식품 공급사 찾아줘") == ""


def test_console_wholesale_route(monkeypatch):
    seen = []
    monkeypatch.setenv("DOMEGGOOK_API_KEY", "k" * 32)
    monkeypatch.setattr(domeggook, "_get", fake(seen))
    stored = []
    monkeypatch.setattr("app.admin.b2b.evidence.upsert_candidate", stored.append)
    con = Console()
    r = con.run(None, "도매꾹에서 홍삼 찾아줘", TODAY)
    assert r["action"] == "wholesale" and len(seen) == 1 and "market=dome" in seen[0]
    rows = next(b for b in r["blocks"] if b["type"] == "wholesale")["rows"]
    assert rows[0]["sale_label"] == "도매 · 도매몰 단가 · 최소 10개" and rows[0]["seller"] == "홍삼나라"
    assert len(stored) == 2 and all(c.price_kind == "wholesale" for c in stored)
    seen.clear()
    r = con.run(None, "건강식품 도매몰에서 모두 조회", TODAY)
    assert len(seen) == 6                                     # 대표 검색어 3개 × 도매꾹·도매매
    labels = {x["sale_kind"] for x in next(b for b in r["blocks"] if b["type"] == "wholesale")["rows"]}
    assert labels == {"wholesale", "consign"}
    assert con.run(None, "건강기능식품 공급사 보여줘", TODAY)["action"] == "suppliers"   # 저장소 목록은 그대로


def test_console_without_key(monkeypatch):
    monkeypatch.delenv("DOMEGGOOK_API_KEY", raising=False)
    r = Console().run(None, "도매꾹에서 홍삼 찾아줘", TODAY)
    assert r["action"] == "wholesale" and "DOMEGGOOK_API_KEY" in r["blocks"][0]["md"]


def test_supplier_rows_carry_sale_kinds():
    c = domeggook.to_candidate(domeggook.search("x", "dome", get=fake([]), key="k")[0], TODAY)
    [row] = suppliers.supplier_rows([c], "건강기능식품")
    assert row["supplier"] == "홍삼나라 (도매꾹)" and row["sale"] == [{"kind": "wholesale", "label": "도매", "n": 1}]
