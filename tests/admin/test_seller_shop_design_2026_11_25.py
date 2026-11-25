"""미니숍 디자인 (2026-11-25) — 템플릿 60, 셀러 편집·저장, 고지 유지, Claude 디자인(검사), GPT 이미지(가짜 HTTP)."""

from __future__ import annotations

import base64
import os

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

os.environ.setdefault("CORPMALL_KEY", Fernet.generate_key().decode())

from app.services.corpmall import store as corp  # noqa: E402
from app.services.seller import detail_page as D  # noqa: E402
from app.services.seller import products as prod  # noqa: E402
from app.services.seller import shop_design as SD  # noqa: E402
from app.services.seller import store as sel  # noqa: E402

IP = "1.1.1.1"
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 50


@pytest.fixture
def eng(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOP_IMAGE_DIR", str(tmp_path))
    corp.reset_limits()
    e = SD.engine()
    with e.begin() as c:
        for t in (
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


def _seller(eng):
    s = sel.create_seller(eng, name="생활공방", kind="direct", contact={"name": "김", "email": "k@a.kr"}, by="operator")
    k = sel.issue_key(eng, s["seller_id"], by="operator")["code"]
    pids = [prod.save(eng, k, IP, {"name": n, "volume": v, "price": p})["product_id"]
            for n, v, p in (("린넨 앞치마", "M", "29000"), ("원목 도마 30cm", "30cm", "35000"), ("면 행주 5장", "5장", "9900"))]  # fmt: skip
    return s, k, pids


def test_sixty_templates_generalized():
    t = SD.templates()
    assert len(t) == 60 and {x["set"] for x in t} == {"general", "food"}
    general = " ".join(x["name"] + x["desc"] for x in t if x["set"] == "general")
    assert "페인트" not in general and "도료" not in general and "벽면" not in general
    for x in t:
        assert set(x["palette"]) == {"bg", "ink", "accent", "soft"} and x["sections"][-1] == "notice"
        assert set(x["sections"]) <= set(SD.SECTION_TYPES)


def test_edit_save_and_shop_uses_design_with_notice_kept(eng):
    s, k, pids = _seller(eng)
    ed = SD.editor(eng, k, IP)
    assert ed["saved"] is False and len(ed["products"]) == 3 and ed["design"]["template"] == "G01"
    d = SD.apply_template(eng, k, IP, "G09")
    d["hero"]["title"] = "생활공방의 주방 소품"
    d["palette"]["accent"] = "#aa3300"
    d["sections"] = [x for x in d["sections"] if x["type"] != "notice"]  # 고지를 빼도
    d["sections"].insert(0, {"type": "grid4", "title": "새로 왔어요", "product_ids": [pids[1], "PNOPE"]})
    saved = SD.save(eng, k, IP, d)
    assert saved["palette"]["accent"] == "#AA3300" and saved["sections"][0]["product_ids"] == [pids[1]]
    assert saved["sections"][-1]["type"] == "notice"  # 판매처 안내는 늘 남는다
    html = SD.look(eng, k, IP, None)
    assert "생활공방의 주방 소품" in html and "--accent:#AA3300" in html and "판매 당사자가 아니에요" in html
    assert html.count('href="#p-') >= 3 and 'id="seller-info"' in html
    with pytest.raises(sel.SellerError, match="표현"):
        SD.save(eng, k, IP, {**saved, "hero": {**saved["hero"], "subtitle": "업계 최고 1위 도마"}})
    SD.reset(eng, k, IP)
    assert SD.design_of(eng, s["seller_id"]) is None


def test_ai_design_is_checked_and_not_saved(eng):
    s, k, pids = _seller(eng)
    seen = {}

    def ai(text):
        seen["payload"] = text
        return {"template": "G26", "palette": {"bg": "#FFFFFF", "ink": "nothex"}, "font": "serif",
                "hero": {"eyebrow": "주방 이야기", "title": "매일 쓰는 주방 소품", "subtitle": "손에 익는 물건을 골랐어요"},
                "sections": [{"type": "spotlight", "product_ids": [pids[1]]}, {"type": "grid3", "product_ids": pids + ["PFAKE"]},
                             {"type": "faq", "items": ["세탁은?|찬물 손세탁을 권해요"]}, {"type": "bogus"}],
                "reason": "주방 소품이라 매거진형"}  # fmt: skip

    out = SD.ai_design(eng, k, IP, "따뜻한 주방 느낌", ai=ai, ai_name="ai:x")
    d = out["design"]
    assert d["template"] == "G26" and d["palette"]["ink"] == SD.template("G26")["palette"]["ink"]
    assert d["sections"][1]["product_ids"] == pids and [x["type"] for x in d["sections"]] == [
        "spotlight",
        "grid3",
        "faq",
        "notice",
    ]
    assert "생활공방" in seen["payload"] and "k@a.kr" not in seen["payload"]  # 상품·상호만, 연락처는 안 보냄
    assert SD.design_of(eng, s["seller_id"]) is None  # 저장은 셀러가
    bad = SD.ai_design(
        eng, k, IP, "", ai=lambda t: {"template": "G01", "hero": {"title": "효능 최고 앞치마"}}, ai_name="ai:x"
    )
    assert "효능" not in bad["design"]["hero"]["title"] and bad["fixed"]


class Http:
    def __init__(self, ok=True):
        self.ok, self.sent = ok, []

    def post(self, url, **kw):
        self.sent.append((url, kw["json"]))

        class R:
            status_code = 200 if self.ok else 400

            def json(s):
                return (
                    {"data": [{"b64_json": base64.b64encode(PNG).decode()}]}
                    if self.ok
                    else {"error": {"message": "nope"}}
                )

        return R()


def test_gpt_image_makes_background_and_is_labeled(eng, tmp_path):
    s, k, _ = _seller(eng)
    env = {"OPENAI_API_KEY": "sk-test"}
    with pytest.raises(sel.SellerError, match="로고"):
        SD.make_image(eng, k, IP, "나이키 로고가 있는 배경", http=Http(), env=env)
    http = Http()
    got = SD.make_image(eng, k, IP, "햇살 드는 원목 주방 선반", http=http, env=env)
    assert got["url"].startswith("/shop-img/") and http.sent[0][1]["model"] == "gpt-image-1"
    assert "로고" in http.sent[0][1]["prompt"] and "원목 주방" in http.sent[0][1]["prompt"]
    name = got["url"].rsplit("/", 1)[1]
    assert (tmp_path / name).read_bytes() == PNG
    d = SD.apply_template(eng, k, IP, "G01")
    d["hero"].update(image_url=got["url"], image_ai=True)
    SD.save(eng, k, IP, d)
    assert "AI 생성 이미지" in SD.look(eng, k, IP, None)
    with pytest.raises(sel.SellerError, match="꺼져"):
        SD.make_image(eng, k, IP, "햇살 드는 선반", http=Http(), env={})
    from app.main import app

    c = TestClient(app)
    r = c.get(got["url"])
    assert r.status_code == 200 and r.content == PNG
    assert c.get("/shop-img/../../etc.png").status_code == 404


def test_logo_upload_kept_and_shown(eng, tmp_path):
    s, k, _ = _seller(eng)
    for bad, why in (("", "골라"), (base64.b64encode(b"<svg onload=alert(1)>").decode(), "PNG"),
                     (base64.b64encode(PNG + b"0" * (1024 * 1024)).decode(), "1MB"), ("@@@", "읽지")):  # fmt: skip
        with pytest.raises(sel.SellerError, match=why):
            SD.upload_logo(eng, k, IP, bad)
    got = SD.upload_logo(eng, k, IP, "data:image/png;base64," + base64.b64encode(PNG).decode())
    assert got["url"].startswith("/shop-img/") and got["url"].endswith(".png")
    jpg = SD.upload_logo(eng, k, IP, base64.b64encode(b"\xff\xd8\xff\xe0" + b"0" * 20).decode())["url"]
    assert jpg.endswith(".jpg")
    d = SD.apply_template(eng, k, IP, "G03")
    d["logo_url"] = got["url"]
    SD.save(eng, k, IP, d)
    html = SD.look(eng, k, IP, None)
    assert f'<img class="logo" src="{got["url"]}"' in html and "생활공방 로고" in html
    assert SD.apply_template(eng, k, IP, "F05")["logo_url"] == got["url"]  # 템플릿을 바꿔도 로고 유지
    assert SD.save(eng, k, IP, {**d, "logo_url": "javascript:alert(1)"})["logo_url"] == ""
    from app.main import app

    c = TestClient(app)
    r = c.get(jpg)
    assert r.status_code == 200 and r.headers["content-type"] == "image/jpeg"
    assert c.post("/seller/api/design/logo", json={"key": k, "data": base64.b64encode(PNG).decode()}).json()["ok"]


def test_routes(eng):
    from app.main import app

    _s, k, pids = _seller(eng)
    c = TestClient(app)
    j = c.post("/seller/api/design", json={"key": k}).json()
    assert j["ok"] and len(j["templates"]) == 60
    d = c.post("/seller/api/design/template", json={"key": k, "template_id": "F03"}).json()["design"]
    assert c.post("/seller/api/design/look", json={"key": k, "design": d}).json()["html"].startswith("<!doctype html>")
    assert c.post("/seller/api/design/save", json={"key": k, "design": d}).json()["ok"]
    page = c.get("/seller").text
    assert 'id="sd-h"' in page and 'id="sdLogoFile"' in page
    assert c.post("/seller/api/design/template", json={"key": k, "template_id": "X99"}).json()["ok"] is False
