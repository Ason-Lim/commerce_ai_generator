"""시장가 비교 (2026-11-26) — 참가격(가짜 응답)·KAMIS 판정, 단위 못 맞추면 판정 안 함, 쿠팡은 조회만(저장 안 함)."""

from __future__ import annotations

import datetime as dt

import pytest
from fastapi.testclient import TestClient

from app.admin.b2b import market_price as MP
from app.services.public_price import chamga, kamis

H = {"X-Access-Token": "test-token"}
GOODS = """<?xml version="1.0" encoding="UTF-8"?><response><result>
<item><goodId>35</goodId><goodName>해표 꽃소금(1kg)</goodName><productEntpCode>484</productEntpCode><goodUnitDivCode>G</goodUnitDivCode><goodBaseCnt>100</goodBaseCnt><goodSmlclsCode>030204006</goodSmlclsCode><goodTotalCnt>1000</goodTotalCnt><goodTotalDivCode>G</goodTotalDivCode></item>
<item><goodId>1709</goodId><goodName>2080 오리지날 미세모(10개)</goodName><productEntpCode>461</productEntpCode><goodUnitDivCode>EA</goodUnitDivCode><goodBaseCnt>1</goodBaseCnt><goodSmlclsCode>030301024</goodSmlclsCode><goodTotalCnt>10</goodTotalCnt><goodTotalDivCode>EA</goodTotalDivCode></item>
<item><goodId>88</goodId><goodName>농심 신라면(120g*5입)</goodName><productEntpCode>1</productEntpCode><goodUnitDivCode>G</goodUnitDivCode><goodBaseCnt>100</goodBaseCnt><goodSmlclsCode>1</goodSmlclsCode><goodTotalCnt>600</goodTotalCnt><goodTotalDivCode>G</goodTotalDivCode></item>
</result></response>"""


def price_xml(day, gid, prices):
    vo = "".join(f"<iros.openapi.service.vo.goodPriceVO><goodInspectDay>{day}</goodInspectDay><entpId>{i}</entpId><goodId>{gid}</goodId>"
                 f"<goodPrice>{p}</goodPrice><inputDttm>2026-10-29 13:19:38</inputDttm></iros.openapi.service.vo.goodPriceVO>"
                 for i, p in enumerate(prices, 1))  # fmt: skip
    return f'<?xml version="1.0" encoding="UTF-8"?><response><result>{vo}</result><resultCode>00</resultCode><resultMsg>ok</resultMsg></response>'


class Http:
    def __init__(self, day="20261023"):
        self.day, self.calls = day, []

    def get(self, url, **kw):
        self.calls.append(url)
        assert "serviceKey=k%2Bey" in url  # 키는 주소 인코딩

        class R:
            status_code = 200

        r = R()
        if "getProductInfoSvc.do" in url:
            r.content = GOODS.encode()
        elif "getProductPriceInfoSvc" in url:
            day = url.split("goodInspectDay=")[1][:8]
            gid = url.split("goodId=")[1].split("&")[0]
            prices = {"35": [3200, 3500, 3980, 3300], "88": [4200, 4480, 3980]}.get(gid, []) if day == self.day else []
            r.content = (
                price_xml(day, gid, prices)
                if prices
                else '<?xml version="1.0"?><response><result/><resultCode>00</resultCode></response>'
            ).encode()
        else:
            raise AssertionError(url)
        return r


ENV = {"KAT_REALTIME_API_KEY": "k+ey"}


@pytest.fixture(autouse=True)
def _dirs(tmp_path, monkeypatch):
    monkeypatch.setenv("CHAMGA_CACHE_DIR", str(tmp_path / "chamga"))
    chamga._mem.clear()
    monkeypatch.setattr(kamis, "reference", lambda card: None)


def test_match_amount_and_tokens():
    gs = chamga.goods(http=Http(), env=ENV)
    assert [g["name"] for g in chamga.match("해표 꽃소금 1kg", gs)][0] == "해표 꽃소금(1kg)"
    assert chamga.match("국산 감귤 5kg", gs) == []
    assert chamga.amount("신라면 120g x 5개") == (600.0, "g") and chamga.amount("간장 1.8L") == (1800.0, "ml")


def test_chamga_compare_per_100g_and_survey_day():
    http = Http()
    today = dt.date(2026, 11, 26)
    got = chamga.compare("해표 꽃소금 1kg", 4500, http=http, env=ENV, today=today)
    assert got["day"] == "20261023" and got["n"] == 4 and got["median"] == 3400
    assert got["per"] == "100g당" and got["own_per"] == 450 and got["market_per"] == 340 and got["verdict"] == "higher"
    n_calls = len(http.calls)
    chamga.compare("해표 꽃소금 500g", 1500, http=http, env=ENV, today=today)  # 조사일·가격은 남겨 둔 것을 씀
    assert len(http.calls) == n_calls
    low = chamga.compare("농심 신라면 120g 5개입", 3900, http=http, env=ENV, today=today)
    assert low["verdict"] == "lower" and low["pct"] < 0
    no_unit = chamga.compare("해표 꽃소금 선물", 4000, http=http, env=ENV, today=today)
    assert no_unit["verdict"] is None and "용량" in no_unit["why"]
    with pytest.raises(chamga.ChamgaError, match="인증키"):
        chamga._get("getProductInfoSvc.do", {}, http=http, env={})


def test_compare_combines_kamis_and_handles_errors(monkeypatch):
    http = Http()
    monkeypatch.setattr(chamga, "survey_day", lambda **kw: "20261023")
    got = MP.compare("해표 꽃소금 1kg", "3,400원", http=http, env=ENV)
    assert got["price"] == 3400 and got["verdict"] == "similar" and got["label"] == "시장가와 비슷해요"
    monkeypatch.setattr(kamis, "reference", lambda card: {"cls": "소매", "item": "감귤", "kinds": ["노지"], "measure": "g", "step": 100,
                                                          "ref": 500, "own": 600, "pct": 20, "day": "2026-11-25", "graded": True})  # fmt: skip
    both = MP.compare("해표 꽃소금 1kg", 3400, http=http, env=ENV)
    assert both["kamis"]["verdict"] == "higher" and both["verdict"] == "mixed"
    assert MP.compare("", 100)["error"] and MP.compare("x", "가격")["error"]
    rows = MP.compare_many("해표 꽃소금 1kg, 4500\n농심 신라면 120g 5개입, 3900", http=http, env=ENV)
    assert [r["chamga"]["verdict"] for r in rows] == ["higher", "lower"]


def test_coupang_lookup_is_view_only(tmp_path):
    seen = []

    def fake(k):
        seen.append(k)
        return [{"name": "꽃소금 1kg", "price": 3900, "product_url": "https://link.coupang.com/x", "is_rocket": True, "fetched_at": "2026-11-26T01:00:00+00:00"},
                {"name": "꽃소금 1kg 2개", "price": 7100, "product_url": "https://link.coupang.com/y"}, {"name": "가격 없음", "price": 0}]  # fmt: skip

    got = MP.coupang_lookup("해표 꽃소금 1kg", search=fake)
    assert got["n"] == 2 and got["median"] == 5500 and got["min"] == 3900 and "저장하지 않고" in got["notice"]
    assert "판정" not in str(got.get("verdict", ""))  # 판정 없음
    assert MP.coupang_lookup("a", search=fake)["error"]


def test_routes(monkeypatch):
    from app.main import app

    monkeypatch.setattr(MP, "coupang_lookup", lambda k, **kw: {"items": [], "n": 0, "keyword": k, "notice": "조회만"})
    monkeypatch.setattr(chamga, "compare", lambda *a, **k: None)
    c = TestClient(app)
    assert c.post("/admin/api/b2b-market/compare", json={"name": "a", "price": "1"}).status_code in (401, 403)
    j = c.post("/admin/api/b2b-market/compare", headers=H, json={"name": "해표 꽃소금 1kg", "price": "3500"}).json()
    assert j["label"] == "견줄 공공 시세가 없어요"
    r = c.post("/admin/api/b2b-market/coupang", headers=H, json={"keyword": "꽃소금"})
    assert r.headers["cache-control"] == "no-store" and r.json()["notice"] == "조회만"
    assert (
        len(c.post("/admin/api/b2b-market/compare-many", headers=H, json={"lines": "a, 1\nb, 2"}).json()["rows"]) == 2
    )
    page = c.get("/admin/b2b/market", headers=H).text
    assert 'id="mCp"' in page and "/admin/b2b/market" in c.get("/admin/b2b/settle", headers=H).text
