"""미니숍 실험실·템플릿 관리 (2026-11-26) — 관리자 전용 테스트 셀러(공개 안 함), 상담용 디자인 요약, 템플릿 고치기·새로·숨김."""

from __future__ import annotations

import os

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

os.environ.setdefault("CORPMALL_KEY", Fernet.generate_key().decode())

from app.services.corpmall import store as corp  # noqa: E402
from app.services.seller import detail_page as D  # noqa: E402
from app.services.seller import products as prod  # noqa: E402
from app.services.seller import shop_design as SD  # noqa: E402
from app.services.seller import shop_lab as L  # noqa: E402
from app.services.seller import shop_public  # noqa: E402
from app.services.seller import store as sel  # noqa: E402

IP = "1.1.1.1"
H = {"X-Access-Token": "test-token"}


@pytest.fixture
def eng(monkeypatch):
    monkeypatch.setenv("SHOP_PUBLIC", "test")
    corp.reset_limits()
    e = L.engine()
    shop_public.engine()
    with e.begin() as c:
        for t in (
            L.t_lab,
            SD.t_tpl,
            SD.t_usage,
            SD.t_design,
            D.t_detail,
            prod.t_listing,
            prod.t_product,
            sel.t_event,
            sel.t_key,
            sel.t_seller,
        ):
            c.execute(t.delete())
    return e


def _tpl(**kw):
    t = {
        k: SD.template("G01")[k]
        for k in ("set", "group", "name", "desc", "palette", "font", "dark", "hero", "sections")
    }
    return {**t, **kw}


def test_lab_seller_is_private_and_works_like_a_seller(eng):
    got = L.open_lab(eng, by="operator")
    sid = got["seller_id"]
    assert got["url"].startswith("/seller#k=") and L.is_lab(eng, sid)
    code = got["url"].split("k=")[1]
    assert len(prod.list_mine(eng, code, IP)) == 8  # 데모 상품
    again = L.open_lab(eng, by="operator")
    assert again["seller_id"] == sid  # 하나만
    with pytest.raises(sel.SellerError):
        sel.resolve(eng, code, IP)  # 이전 코드는 막힘
    with pytest.raises(sel.SellerError):
        L.open_lab(eng, by="ai")  # 운영자만
    sel.set_status(eng, sid, "active", by="operator", reason="시험") if hasattr(sel, "set_status") else None
    assert all(x["seller_id"] != sid for x in shop_public.public_sellers(eng))  # 승인해도 공개 안 함


def test_design_summary_for_support(eng):
    s = sel.create_seller(eng, name="생활공방", kind="direct", contact={"name": "김", "email": "k@a.kr"}, by="operator")
    k = sel.issue_key(eng, s["seller_id"], by="operator")["code"]
    assert L.design_summary(eng, s["seller_id"])["saved"] is False
    prod.save(eng, k, IP, {"name": "린넨 앞치마", "volume": "M", "price": "29000"})
    d = SD.apply_template(eng, k, IP, "G09")
    SD.save(eng, k, IP, d)
    got = L.design_summary(eng, s["seller_id"])
    assert got["saved"] and got["template"] == "G09" and got["sections"][-1] == "판매처 안내" and got["logo"] is False
    assert sel.resolve(eng, k, IP)["seller_id"] == s["seller_id"]  # 셀러 코드는 그대로


def test_templates_edit_new_hide_restore(eng):
    assert len(SD.templates(eng)) == 60
    t = L.save_template(
        eng,
        _tpl(id="G01", name="시그니처 스튜디오 2", hero="poster", sections=["grid4", "notice", "faq"]),
        by="operator",
    )
    assert t["kind"] == "edited" and t["name"] == "시그니처 스튜디오 2" and t["sections"] == ["grid4", "faq", "notice"]
    new = L.save_template(eng, _tpl(set="food", name="반찬 가게"), by="operator", new=True)
    assert new["id"] == "C01" and new["kind"] == "custom" and len(SD.templates(eng)) == 61
    for bad, why in ((_tpl(palette={"bg": "red"}), "색"), (_tpl(name="효능 최고 템플릿"), "표현"), (_tpl(sections=["notice"]), "섹션"),
                     (_tpl(hero="nope"), "배치"), (_tpl(set="x"), "세트")):  # fmt: skip
        with pytest.raises(sel.SellerError, match=why):
            L.save_template(eng, {**bad, "id": "G02"}, by="operator")
    with pytest.raises(sel.SellerError):
        L.save_template(eng, _tpl(id="G02"), by="ai")
    # 숨김 — 셀러 고르기에서 빠지지만 이미 고른 셀러 화면은 그대로
    s = sel.create_seller(eng, name="생활공방", kind="direct", contact={"name": "김", "email": "k@a.kr"}, by="operator")
    k = sel.issue_key(eng, s["seller_id"], by="operator")["code"]
    prod.save(eng, k, IP, {"name": "린넨 앞치마", "volume": "M", "price": "29000"})
    SD.save(eng, k, IP, SD.apply_template(eng, k, IP, "G05"))
    L.hide_template(eng, "G05", True, by="operator")
    assert "G05" not in {x["id"] for x in SD.editor(eng, k, IP)["templates"]}
    with pytest.raises(sel.SellerError, match="없는 템플릿"):
        SD.apply_template(eng, k, IP, "G05")
    assert "판매처 안내" in SD.look(eng, k, IP, None) or "판매 당사자" in SD.look(eng, k, IP, None)
    assert L.users_of(eng) == {"G05": 1}
    # 고친 배치는 그 템플릿을 쓰는 셀러 화면에 반영
    L.save_template(eng, _tpl(id="G05", hero="poster"), by="operator")
    assert 'class="hero split poster"' in SD.look(eng, k, IP, None)
    back = L.restore_template(eng, "G05", by="operator")
    assert back["kind"] == "base" and not back["hidden"] and back["hero"] == SD.base_templates()[4]["hero"]
    with pytest.raises(sel.SellerError, match="숨기기"):
        L.restore_template(eng, "C01", by="operator")
    # 세트에 보이는 템플릿 하나는 남긴다
    for t in [x for x in SD.templates(eng) if x["set"] == "food" and x["id"] != "F01"]:
        L.hide_template(eng, t["id"], True, by="operator")
    with pytest.raises(sel.SellerError, match="하나는"):
        L.hide_template(eng, "F01", True, by="operator")


def test_preview_and_routes(eng):
    from app.main import app

    c = TestClient(app)
    assert c.post("/admin/api/shop-lab/open").status_code in (401, 403)
    r = c.post("/admin/api/shop-lab/open", headers=H).json()
    assert r["ok"] and r["url"].startswith("/seller#k=")
    html = L.preview_template(eng, _tpl(name="미리보기 시험", hero="center"))
    assert "미리보기 시험" in html and "린넨 앞치마" in html and 'class="hero center' in html
    j = c.get("/admin/api/shop-templates", headers=H).json()
    assert len(j["templates"]) == 60 and set(j["sets"]) == {"general", "food"}
    assert (
        c.post("/admin/api/shop-templates/look", headers=H, json={"template": _tpl()})
        .json()["html"]
        .startswith("<!doctype html>")
    )
    assert (
        c.post("/admin/api/shop-templates/new", headers=H, json={"template": _tpl(name="새 것")}).json()["template"][
            "id"
        ]
        == "C01"
    )
    assert c.post("/admin/api/shop-templates/C01/hide", headers=H, json={"hidden": True}).json()["template"]["hidden"]
    assert c.post("/admin/api/shop-templates/save", headers=H, json={"template": _tpl(id="Z99")}).status_code == 400
    assert c.get(f"/admin/api/shop-lab/seller/{r['seller_id']}", headers=H).json()["saved"] is False
    assert c.get("/admin/api/seller", headers=H).json()["sellers"][0]["lab"] is True
    assert c.get(f"/shop/{r['seller_id']}").status_code == 404
    page = c.get("/admin/seller", headers=H).text
    assert 'id="lab-h"' in page and 'id="tp-h"' in page
