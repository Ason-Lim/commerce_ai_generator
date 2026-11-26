"""2026-11-26 환율 — 관세청 관세환율(수입) 우선 · 하루 한 번 파일 · 실패하면 Frankfurter · 그다음 .env."""

from __future__ import annotations

import pytest

from app.services.public_price import fx

XML_OK = """<response><header><resultCode>00</resultCode><resultMsg>정상서비스.</resultMsg></header><body><items>
<item><aplyBgnDt>20261122</aplyBgnDt><cntySgn>US</cntySgn><currSgn>USD</currSgn><fxrt>1,398.5</fxrt><imexTp>2</imexTp><mtryUtNm>US Dollar</mtryUtNm></item>
<item><aplyBgnDt>20261122</aplyBgnDt><cntySgn>JP</cntySgn><currSgn>JPY</currSgn><fxrt>9.12</fxrt><imexTp>2</imexTp><mtryUtNm>Yen</mtryUtNm></item>
</items></body></response>""".encode()
XML_KEY = """<OpenAPI_ServiceResponse><cmmMsgHeader><errMsg>SERVICE ERROR</errMsg>
<returnAuthMsg>SERVICE_KEY_IS_NOT_REGISTERED_ERROR</returnAuthMsg><returnReasonCode>30</returnReasonCode></cmmMsgHeader></OpenAPI_ServiceResponse>""".encode()


class R:
    def __init__(self, status=200, content=b"", js=None):
        self.status_code, self.content, self._js = status, content, js

    def json(self):
        return self._js


class Http:
    def __init__(self, customs=None, frank=None):
        self.customs, self.frank, self.urls = customs, frank, []

    def get(self, url, params=None, timeout=None, headers=None):
        self.urls.append(url)
        if url.startswith(fx.CUSTOMS_URL):
            if isinstance(self.customs, Exception):
                raise self.customs
            return self.customs
        return self.frank or R(500)


@pytest.fixture(autouse=True)
def clean(tmp_path, monkeypatch):
    monkeypatch.setenv("FX_CACHE_DIR", str(tmp_path))
    monkeypatch.setenv("KAT_REALTIME_API_KEY", "abc+/=")
    monkeypatch.delenv("DIRECT_USD_KRW", raising=False)
    for k in ("CHAMGA_SERVICE_KEY", "G2B_SERVICE_KEY", "NTS_SERVICE_KEY"):
        monkeypatch.delenv(k, raising=False)
    fx._fail_until.clear()


def test_customs_request_and_parse():
    http = Http(R(content=XML_OK))
    data = fx.customs_rates("20261126", http=http)
    assert data["rates"] == {"USD": 1398.5, "JPY": 9.12} and data["applied"] == "20261122"
    url = http.urls[0]
    assert "weekFxrtTpcd=2" in url and "aplyBgnDt=20261126" in url and "serviceKey=abc%2B%2F%3D" in url


def test_portal_key_error_is_reported():
    with pytest.raises(fx.FxError, match="SERVICE_KEY_IS_NOT_REGISTERED"):
        fx.customs_rates(http=Http(R(content=XML_KEY)))


def test_usd_krw_customs_cached_once_per_day():
    http = Http(R(content=XML_OK))
    a = fx.usd_krw(http=http)
    b = fx.usd_krw(http=http)
    assert a["rate"] == 1398.5 and a["source"] == "관세청 과세환율(수입)" and a["date"] == "2026-11-22"
    assert b == a and len(http.urls) == 1


def test_fallback_frankfurter_then_env(monkeypatch):
    http = Http(ConnectionError("x"), R(js={"date": "2026-11-26", "rates": {"KRW": 1401.2}}))
    r = fx.usd_krw(http=http)
    assert r["kind"] == "reference" and r["rate"] == 1401.2
    fx._fail_until.clear()
    monkeypatch.setenv("DIRECT_USD_KRW", "1390")
    r = fx.usd_krw(http=Http(ConnectionError("x"), R(500)))
    assert r == {"rate": 1390.0, "source": "운영자 설정값", "date": "", "kind": "manual", "stale": False}


def test_recent_saved_table_used_when_customs_down(tmp_path):
    (tmp_path / "customs_20261120.json").write_text('{"rates": {"USD": 1380.0}, "applied": "20261115"}', encoding="utf-8")
    r = fx.usd_krw(http=Http(ConnectionError("x")))
    assert r["rate"] == 1380.0 and r["stale"] is True


def test_no_key_no_source_returns_none(monkeypatch):
    monkeypatch.delenv("KAT_REALTIME_API_KEY")
    assert fx.usd_krw(http=Http(R(500), R(500))) is None
