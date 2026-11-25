"""셀러 주소 이름 — 링크에 회사 이름 (/shop/renerpaint, 관리자 미리보기), 같은 이름의 다른 회사 구분 (2026-11-25)."""

from __future__ import annotations

import os

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

os.environ.setdefault("CORPMALL_KEY", Fernet.generate_key().decode())

from app.services.corpmall import store as corp  # noqa: E402
from app.services.seller import catalog, shop_public  # noqa: E402
from app.services.seller import products as prod  # noqa: E402
from app.services.seller import store as sel  # noqa: E402

IP = "1.1.1.1"
H = {"X-Access-Token": "test-token"}


@pytest.fixture
def eng(monkeypatch):
    monkeypatch.delenv("SHOP_PUBLIC", raising=False)
    corp.reset_limits()
    e = shop_public.engine()
    with e.begin() as c:
        for t in (
            catalog.t_slug,
            catalog.t_store,
            shop_public.t_biz,
            prod.t_product,
            sel.t_event,
            sel.t_key,
            sel.t_seller,
        ):
            c.execute(t.delete())
    return e


def _seller(eng, name):
    s = sel.create_seller(eng, name=name, kind="direct", contact={"name": "김", "email": "k@a.kr"}, by="operator")
    return s["seller_id"], sel.issue_key(eng, s["seller_id"], by="operator")["code"]


def test_rules_and_same_name_other_company(eng):
    a, _ = _seller(eng, "레너페인트")
    b, kb = _seller(eng, "레너페인트")  # 같은 상호, 다른 회사
    assert catalog.set_slug(eng, a, "RenerPaint", by="operator") == {"slug": "renerpaint"}
    for bad in ("ab", "1paint", "rener_paint", "rener--paint", "admin", "레너"):
        with pytest.raises(sel.SellerError):
            catalog.set_slug(eng, b, bad, by="operator")
    with pytest.raises(sel.SellerError):
        catalog.set_slug(eng, b, "renerpaint2", by="ai")  # 운영자만
    shop_public.biz_save(eng, kb, IP, {"trade_name": "레너페인트", "biz_no": "220-81-62517"})
    catalog.set_store_url(eng, b, "https://smartstore.naver.com/rener-busan", by="operator")
    with pytest.raises(sel.SellerError, match="다른 셀러") as ei:
        catalog.set_slug(eng, b, "renerpaint", by="operator")
    msg = str(ei.value)
    assert "renerpaint-2517" in msg and "rener-busan" in msg  # 사업자번호 끝 4자리 · 몰 이름 후보
    assert catalog.set_slug(eng, b, "renerpaint-2517", by="operator")["slug"] == "renerpaint-2517"
    assert catalog.resolve_seller(eng, "renerpaint") == a and catalog.resolve_seller(eng, "renerpaint-2517") == b
    assert catalog.resolve_seller(eng, a) == a and catalog.resolve_seller(eng, "nope") is None
    assert catalog.set_slug(eng, a, "", by="operator") == {"slug": ""}


def test_links_use_the_name(eng, monkeypatch):
    from app.main import app

    a, k = _seller(eng, "레너페인트")
    pid = prod.save(eng, k, IP, {"name": "우드 바니쉬", "volume": "1L", "price": "35000"})["product_id"]
    c = TestClient(app)
    assert c.post(f"/admin/api/seller/{a}/slug", headers=H, json={"slug": "renerpaint"}).json()["slug"] == "renerpaint"
    row = next(x for x in c.get("/admin/api/seller", headers=H).json()["sellers"] if x["seller_id"] == a)
    assert row["slug"] == "renerpaint" and row["shop_preview"] == "/admin/seller/renerpaint/shop"
    assert c.get("/admin/seller/renerpaint/shop", headers=H).status_code == 200
    r = c.get(f"/admin/seller/renerpaint/preview/{pid}", headers=H)
    assert r.status_code == 200 and "우드 바니쉬" in r.text
    b, _ = _seller(eng, "다른회사")
    c.post(f"/admin/api/seller/{b}/slug", headers=H, json={"slug": "other-co"})
    assert c.get(f"/admin/seller/other-co/preview/{pid}", headers=H).status_code == 404  # 다른 셀러 이름으로는 안 열림
    monkeypatch.setenv("SHOP_PUBLIC", "test")
    sel.set_status(eng, a, "active", by="operator", reason="ok")
    assert c.get("/shop/renerpaint").status_code == 200
    assert shop_public.biz_get(eng, k, IP)["url"] == "/shop/renerpaint"
