"""UCP 판매자 카탈로그 읽기 (2026-11-04 p40) — 발견·협상, 검색 호출(REST·MCP), 카드 변환, 기본 꺼짐, 미연결."""
from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from app.services.ucp import client, discovery, mapping, platform, registry

FIX = Path(__file__).parent / "fixtures"
APP = Path(__file__).resolve().parents[3] / "app"
PROFILE = "https://commerce-ai.example.kr/.well-known/ucp"


def fx(name):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


class Resp:
    def __init__(self, status=200, body=None, headers=None):
        self.status_code, self._body, self.headers = status, body, headers or {}
        self.content = json.dumps(body).encode() if body is not None else b""

    def json(self):
        if self._body is None:
            raise ValueError("no json")
        return self._body


class Http:
    def __init__(self, get=None, post=None):
        self._get, self._post, self.calls = get, post, []

    def get(self, url, **kw):
        self.calls.append(("GET", url, kw))
        return self._get

    def post(self, url, **kw):
        self.calls.append(("POST", url, kw))
        return self._post


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    discovery.clear_cache()
    for k in ("UCP_CATALOG", "UCP_PLATFORM_PROFILE_URL", "UCP_MERCHANTS_CSV"):
        monkeypatch.delenv(k, raising=False)


# ── 발견·협상 ──────────────────────────────────────────────

def test_mcp_only_profile_like_shopify():
    m = discovery.negotiate("shop.example.com", fx("profile_mcp_only.json"))
    assert m.ok and m.version == "2026-08-25" and m.transport == "mcp" and m.search and m.lookup
    assert m.endpoint == "https://shop.example.com/api/ucp/mcp"


def test_rest_is_preferred_and_trailing_slash_removed():
    m = discovery.negotiate("mall.example.kr", fx("profile_rest.json"))
    assert m.ok and m.version == "2026-04-08" and m.transport == "rest" and m.endpoint == "https://mall.example.kr/ucp/v1"


@pytest.mark.parametrize("change, reason", [
    (lambda u: u.update(version="2025-01-01", supported_versions={}), "공통 판 없음"),
    (lambda u: u["capabilities"].pop("dev.ucp.shopping.catalog.search"), "catalog.search 미지원"),
    (lambda u: u["services"]["dev.ucp.shopping"][0].update(endpoint="http://shop.example.com/mcp"), "전송"),
])
def test_unusable_profiles(change, reason):
    doc = fx("profile_mcp_only.json")
    change(doc["ucp"])
    m = discovery.negotiate("shop.example.com", doc)
    assert not m.ok and reason in m.reason


def test_discover_fetches_well_known_and_caches():
    http = Http(get=Resp(200, fx("profile_mcp_only.json"), {"Cache-Control": "max-age=600"}))
    a = discovery.discover("Shop.Example.com", http=http, now=lambda: 1000)
    b = discovery.discover("shop.example.com", http=http, now=lambda: 1500)
    assert a.ok and b is a and len(http.calls) == 1
    assert http.calls[0][1] == "https://shop.example.com/.well-known/ucp"


@pytest.mark.parametrize("host", ["", "localhost", "127.0.0.1:8080", "a b.com", "evil.com/../x"])
def test_bad_hosts_are_not_called(host):
    http = Http(get=Resp(200, fx("profile_mcp_only.json")))
    assert not discovery.discover(host, http=http).ok and http.calls == []


def test_missing_profile():
    m = discovery.discover("www.kurly.com", http=Http(get=Resp(404, None)))
    assert not m.ok and "HTTP 404" in m.reason


# ── 검색 호출 ──────────────────────────────────────────────

def test_rest_search_sends_ucp_agent_and_request_id():
    m = discovery.negotiate("mall.example.kr", fx("profile_rest.json"))
    http = Http(post=Resp(200, fx("search_krw.json")))
    out = client.search(m, "감귤", http=http, limit=5, profile_url=PROFILE)
    assert out.ok and len(out.response["products"]) == 3
    method, url, kw = http.calls[0]
    assert (method, url) == ("POST", "https://mall.example.kr/ucp/v1/catalog/search")
    assert kw["headers"]["UCP-Agent"] == f'profile="{PROFILE}"' and kw["headers"]["Request-Id"]
    assert kw["json"]["query"] == "감귤" and kw["json"]["pagination"] == {"limit": 5}
    assert kw["json"]["context"] == {"address_country": "KR", "language": "ko-KR", "currency": "KRW"}


def test_mcp_search_uses_tools_call_with_meta():
    m = discovery.negotiate("shop.example.com", fx("profile_mcp_only.json"))
    http = Http(post=Resp(200, {"jsonrpc": "2.0", "id": "1", "result": {"structuredContent": fx("search_krw.json")}}))
    out = client.search(m, "감귤", http=http, profile_url=PROFILE)
    assert out.ok
    rpc = http.calls[0][2]["json"]
    assert rpc["method"] == "tools/call" and rpc["params"]["name"] == "search_catalog"
    assert rpc["params"]["arguments"]["meta"] == {"ucp-agent": {"profile": PROFILE}}


def test_profile_unreachable_is_reported_with_continue_url():
    """실제 Shopify 판매자 응답(2026-11-04)과 같은 모양 — 우리 프로필을 못 가져오면 거절."""
    m = discovery.negotiate("shop.example.com", fx("profile_mcp_only.json"))
    out = client.search(m, "감귤", http=Http(post=Resp(422, fx("mcp_profile_unreachable.json"))), profile_url=PROFILE)
    assert not out.ok and out.code == "profile_unreachable" and out.continue_url == "https://shop.example.com/"


@pytest.mark.parametrize("resp, code", [
    (Resp(429, {"error": "slow down"}), "rate_limited"),
    (Resp(200, {"ucp": {"status": "error"}, "messages": [{"type": "error", "code": "not_found", "content": "없음"}]}),
     "not_found"),
    (Resp(200, ["not", "a", "dict"]), "bad_response"),
    (Resp(500, None), "bad_response"),
])
def test_rest_errors(resp, code):
    m = discovery.negotiate("mall.example.kr", fx("profile_rest.json"))
    out = client.search(m, "감귤", http=Http(post=resp), profile_url=PROFILE)
    assert not out.ok and out.code == code


def test_no_platform_profile_means_no_call():
    m = discovery.negotiate("mall.example.kr", fx("profile_rest.json"))
    http = Http(post=Resp(200, fx("search_krw.json")))
    out = client.search(m, "감귤", http=http)
    assert not out.ok and out.code == "no_platform_profile" and http.calls == []


# ── 카드 변환 ──────────────────────────────────────────────

def cards():
    import datetime as dt
    return mapping.to_cards(fx("search_krw.json"), host="mall.example.kr", merchant_name="예시몰",
                            now=lambda: dt.datetime(2026, 11, 4, 22, 30))


def test_one_card_per_available_krw_variant():
    got, skipped = cards()
    assert [c["title"] for c in got] == ["제주 노지 감귤 3kg", "제주 노지 감귤 5kg", "감귤 선물세트 (한라봉 혼합)"]
    assert [c["price"] for c in got] == [18900, 27900, 39000]          # KRW 최소 단위 = 원
    assert {s["reason"] for s in skipped} == {"판매 불가(품절 등)", "원화 가격 아님"}
    assert all(c["affiliate"] is False and c["direct"] and c["seen_at"] == "2026-11-04 22:30" for c in got)


def test_merchant_unit_price_is_used_as_is_never_recomputed():
    three, five, gift = cards()[0]
    assert three["per100g"] == 630                                    # 기준 100g → 그대로 (18900/30=630 과 같아도 계산 아님)
    assert five["per100g"] is None                                    # 기준 1kg → 100g 로 환산하지 않음
    assert five["unit_price_text"] == "1kg당 5,580원 (판매자 표시)"
    assert gift["per100g"] is None and gift["unit_price_text"] is None


def test_unsafe_urls_dropped_and_disclosure_kept():
    _three, _five, gift = cards()[0]
    assert gift["url"] is None                                        # javascript: 링크는 버림
    assert gift["ucp"]["disclosures"] == ["이 상품은 견과류를 사용하는 시설에서 포장합니다."]
    assert cards()[0][0]["image"] == "https://img.example.kr/citrus.jpg"


@pytest.mark.parametrize("price, expect", [
    ({"amount": 100, "currency": "KRW"}, 100), ({"amount": 100.5, "currency": "KRW"}, None),
    ({"amount": True, "currency": "KRW"}, None), ({"amount": -1, "currency": "KRW"}, None),
    ({"amount": 100, "currency": "USD"}, None), (None, None),
])
def test_won(price, expect):
    assert mapping.won(price) == expect


# ── 플랫폼 프로필 · 사용 여부 · 등록부 ─────────────────────────

def test_platform_profile_has_required_parts_and_no_payment():
    u = platform.platform_profile()["ucp"]
    assert u["version"] == platform.SPEC_VERSION and set(u) >= {"services", "capabilities", "payment_handlers"}
    assert set(u["capabilities"]) == set(platform.CAPABILITIES) and u["payment_handlers"] == {}
    assert not any("checkout" in k or "cart" in k for k in u["capabilities"])


@pytest.mark.parametrize("flag, url, on", [(None, None, False), ("1", None, False), ("1", "http://x.kr/p", False),
                                            ("0", PROFILE, False), ("1", PROFILE, True)])
def test_enabled_only_with_flag_and_https_profile(monkeypatch, flag, url, on):
    if flag:
        monkeypatch.setenv("UCP_CATALOG", flag)
    if url:
        monkeypatch.setenv("UCP_PLATFORM_PROFILE_URL", url)
    assert platform.enabled() is on


def test_registry_reads_only_requested_states(tmp_path, monkeypatch):
    p = tmp_path / "m.csv"
    p.write_text("호스트,이름,상태,확인일,메모\nmall.example.kr,예시몰,사용,2026-11-04,\nallbirds.com,Allbirds,시험,,\n"
                 "bad host,x,사용,,\nstop.example.kr,중지몰,중지,,\n", encoding="utf-8")
    monkeypatch.setenv("UCP_MERCHANTS_CSV", str(p))
    assert [m["host"] for m in registry.load()] == ["mall.example.kr"]
    assert [m["host"] for m in registry.load(("사용", "시험"))] == ["mall.example.kr", "allbirds.com"]


def test_missing_registry_is_empty(monkeypatch, tmp_path):
    monkeypatch.setenv("UCP_MERCHANTS_CSV", str(tmp_path / "none.csv"))
    assert registry.load() == []


def test_not_wired_into_any_app_path_yet():
    """연결 결정 전에는 ucp 패키지 밖의 어떤 앱 모듈도 불러오지 않는다."""
    for path in APP.rglob("*.py"):
        if "ucp" in path.parts:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = ([node.module] if isinstance(node, ast.ImportFrom) and node.module else
                     [a.name for a in node.names] if isinstance(node, ast.Import) else [])
            assert not any(n.startswith("app.services.ucp") for n in names), path
