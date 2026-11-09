"""UCP 판매자 카탈로그 읽기 (2026-11-04 p40) — 발견·협상, 검색 호출(REST·MCP), 카드 변환, 기본 꺼짐, 미연결."""
from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from app.services.ucp import client, discovery, mapping, platform, registry, schemas

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


SCHEMA_DIR = FIX / "schemas_2026-08-25"
SCHEMA_FILES = json.loads((SCHEMA_DIR / "_index.json").read_text(encoding="utf-8"))["files"]


class Http:
    """가짜 HTTP — ucp.dev schema 는 내려받아 둔 공식 파일로 응답 (오프라인)."""

    def __init__(self, get=None, post=None):
        self._get, self._post, self.calls = get, post, []

    def get(self, url, **kw):
        if url in SCHEMA_FILES:
            return Resp(200, json.loads((SCHEMA_DIR / SCHEMA_FILES[url]).read_text(encoding="utf-8")))
        self.calls.append(("GET", url, kw))
        return self._get

    def post(self, url, **kw):
        self.calls.append(("POST", url, kw))
        return self._post


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    discovery.clear_cache()
    schemas.clear_cache()
    for k in ("UCP_CATALOG", "UCP_PLATFORM_PROFILE_URL", "UCP_MERCHANTS_CSV"):
        monkeypatch.delenv(k, raising=False)


# ── 발견·협상 ──────────────────────────────────────────────

def test_mcp_only_profile_like_shopify():
    m = discovery.negotiate("shop.example.com", fx("profile_mcp_only.json"))
    assert m.ok and m.version == "2026-08-25" and m.transport == "mcp" and m.search and m.lookup
    assert m.endpoint == "https://shop.example.com/api/ucp/mcp"


def test_rest_is_preferred_and_trailing_slash_removed():
    m = discovery.negotiate("mall.example.kr", fx("profile_rest.json"))
    assert m.ok and m.version == "2026-08-25" and m.transport == "rest" and m.endpoint == "https://mall.example.kr/ucp/v1"


def test_older_supported_version_is_negotiated():
    doc = fx("profile_rest.json")
    doc["ucp"]["version"] = "2026-04-08"
    assert discovery.negotiate("mall.example.kr", doc).version == "2026-04-08"


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
    assert not m.ok and "HTTP 404" in m.reason and "유효 프로필 미확인" in m.reason   # 미지원 확정이 아님


# ── 검색 호출 ──────────────────────────────────────────────

def test_rest_search_sends_ucp_agent_and_request_id():
    m = discovery.negotiate("mall.example.kr", fx("profile_rest.json"))
    http = Http(post=Resp(200, fx("search_krw.json")))
    out = client.search(m, "감귤", http=http, limit=5, profile_url=PROFILE)
    assert out.ok and len(out.response["products"]) == 4 and out.schema_valid is True
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
    return mapping._to_cards(fx("search_krw.json"), host="mall.example.kr", merchant_name="예시몰",
                             now=lambda: dt.datetime(2026, 11, 4, 22, 30), version="2026-08-25", transport="rest")


def test_one_card_per_available_krw_variant():
    got, skipped = cards()
    assert [c["title"] for c in got] == ["제주 노지 감귤 3kg", "제주 노지 감귤 5kg", "감귤 선물세트 (한라봉 혼합)"]
    assert [c["price"] for c in got] == [18900, 27900, 39000]          # KRW 최소 단위 = 원
    reasons = [s["reason"] for s in skipped]
    assert "판매 불가(품절 등)" in reasons and "원화 가격 아님" in reasons
    assert any(r.startswith("단위 판매 (가격이 kg당)") for r in reasons)    # p41: kg당 가격은 팩 가격처럼 넣지 않음
    assert all(c["affiliate"] is False and c["direct"] and c["seen_at"] == "2026-11-04 22:30" for c in got)


def test_merchant_unit_price_is_shown_but_never_used_for_comparison():
    three, five, gift = cards()[0]
    # p45: 판매자 단위가격은 seller_unit_price 로 보존·표시만, 추천용 값은 비움
    assert three["seller_unit_price"]["amount"] == 630 and three["seller_unit_price"]["is_100g"] is True
    assert three["unit_price_text"] == "100g당 630원 (판매자 표시)"
    assert five["unit_price_text"] == "1kg당 5,580원 (판매자 표시)"                # 1kg 기준 → 환산하지 않음
    for c in (three, five, gift):
        assert c["per100g"] is None and c["per_unit"] is None and c["weight_g"] is None
        assert c["price_compare_blocked"] == "ucp_seller_unit_price"
    assert gift["seller_unit_price"] is None and gift["unit_price_text"] is None


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


# ── p41 (GPT 검토 22:31) ────────────────────────────────────

SEARCH_SCHEMA = "https://ucp.dev/2026-08-25/schemas/shopping/catalog_search.json"


def test_fixture_search_response_conforms_to_official_schema():
    prepared = schemas.prepare(SEARCH_SCHEMA, http=Http())
    assert len(prepared.bundle) > 10                                   # 참조까지 모두 미리 확보
    ok, errors = schemas.validate_search_response(fx("search_krw.json"), prepared)
    assert ok is True and errors == []


def test_schema_violation_fails_the_search():
    m = discovery.negotiate("mall.example.kr", fx("profile_rest.json"))
    bad = fx("search_krw.json")
    del bad["products"][0]["price_range"]
    out = client.search(m, "감귤", http=Http(post=Resp(200, bad)), profile_url=PROFILE)
    assert not out.ok and out.code == "schema_invalid" and out.schema_valid is False
    assert any("price_range" in e for e in out.schema_errors)


@pytest.mark.parametrize("profile", ["profile_rest.json", "profile_mcp_only.json"])
def test_without_validator_no_request_is_sent(monkeypatch, profile):
    """p45: 검증기는 필수 — 없으면 판매자 요청 0회."""
    import sys

    monkeypatch.setitem(sys.modules, "jsonschema", None)
    m = discovery.negotiate("x.example.kr", fx(profile))
    http = Http(post=Resp(200, fx("search_krw.json")))
    out = client.search(m, "감귤", http=http, profile_url=PROFILE)
    assert not out.ok and out.code == "schema_unavailable"
    assert not any(c[0] == "POST" for c in http.calls)


@pytest.mark.parametrize("name, url, ok", [
    ("dev.ucp.shopping.catalog.search", "https://ucp.dev/2026-08-25/schemas/shopping/catalog_search.json", True),
    ("dev.ucp.shopping.catalog.search", "https://evil.example.com/catalog_search.json", False),
    ("dev.ucp.shopping.catalog.search", "http://ucp.dev/x.json", False),
    ("dev.ucp.shopping.catalog.search", "https://ucp.dev.evil.com/x.json", False),
    ("com.shopify.catalog", "https://shopify.com/schemas/catalog.json", True),
    ("com.shopifyx.catalog", "https://shopify.com/schemas/catalog.json", False),          # 라벨 경계
    ("dev.ucp.shopping.catalog.search", None, True),
])
def test_schema_origin_must_match_namespace(name, url, ok):
    assert discovery.origin_ok(name, url) is ok


def test_capability_with_foreign_schema_is_rejected():
    doc = fx("profile_mcp_only.json")
    doc["ucp"]["capabilities"]["dev.ucp.shopping.catalog.search"] = [
        {"version": "2026-08-25", "schema": "https://evil.example.com/catalog_search.json"}]
    m = discovery.negotiate("shop.example.com", doc)
    assert not m.ok and "출처 불일치" in m.reason and "dev.ucp.shopping.catalog.search" in m.rejected


def test_profile_redirect_is_not_followed():
    http = Http(get=Resp(301, None, {"Location": "https://other.example.com/.well-known/ucp"}))
    m = discovery.discover("shop.example.com", http=http)
    assert not m.ok and "리다이렉트" in m.reason
    assert http.calls[0][2]["allow_redirects"] is False


def test_search_redirect_is_not_followed():
    m = discovery.negotiate("mall.example.kr", fx("profile_rest.json"))
    http = Http(post=Resp(302, None, {"Location": "https://elsewhere.example.com/"}))
    out = client.search(m, "감귤", http=http, profile_url=PROFILE)
    assert not out.ok and out.code == "redirect" and http.calls[0][2]["allow_redirects"] is False


@pytest.mark.parametrize("cc, seconds", [
    (None, 0), ("public, max-age=10", 10), ("max-age=600", 600), ("public, max-age=999999", 86_400),
    ("no-store", 0), ("no-cache, max-age=600", 0), ("private, max-age=600", 0), ("public", 0),
])
def test_merchant_profile_cache_follows_its_headers(cc, seconds):
    """p45: 판매자 Cache-Control 그대로 — 헤더 없음·no-store·no-cache·private 는 보관 안 함, max-age 는 그 초만."""
    assert discovery.cache_seconds({"Cache-Control": cc} if cc else {}) == seconds
    http = Http(get=Resp(200, fx("profile_mcp_only.json"), {"Cache-Control": cc} if cc else {}))
    discovery.discover("shop.example.com", http=http, now=lambda: 1000)
    discovery.discover("shop.example.com", http=http, now=lambda: 1000 + max(seconds - 1, 0))
    assert len(http.calls) == (1 if seconds > 1 else 2)
    if seconds:
        discovery.discover("shop.example.com", http=http, now=lambda: 1000 + seconds)
        assert len(http.calls) == 2                                    # 만료되면 다시 가져옴


@pytest.mark.parametrize("ref, yes", [
    ({"value": 100, "unit": "GRM"}, True), ({"value": 1000, "unit": "GRM", "scale": 1}, True),
    ({"value": 100, "unit": "GRM", "scale": 1}, False),            # 10g
    ({"value": 1, "unit": "HGM"}, False),                         # 다른 단위 코드는 환산하지 않음
    ({"value": 100, "unit": "g"}, False),                         # Rec20 코드가 아니면 아님
    ({"value": 100, "unit": "MLT"}, False), ({"value": "100", "unit": "GRM"}, False), (None, False),
])
def test_is_100g_checks_unit_value_and_scale(ref, yes):
    assert mapping.is_100g(ref) is yes


def test_unit_price_needs_same_currency_and_same_unit():
    base = {"price": {"amount": 18900, "currency": "KRW"},
            "unit_price": {"amount": 630, "currency": "KRW", "measure": {"value": 3000, "unit": "GRM"},
                           "reference": {"value": 100, "unit": "GRM"}}}
    assert mapping._unit_price(base, "KRW")["is_100g"] is True
    assert mapping._unit_price(base, "USD") is None                                   # price 통화와 다름
    wrong = json.loads(json.dumps(base))
    wrong["unit_price"]["measure"]["unit"] = "KGM"
    assert mapping._unit_price(wrong, "KRW") is None                                  # measure·reference 단위 다름


@pytest.mark.parametrize("qu, each", [(None, True), ({"unit": "C62"}, True), ({"unit": "C62", "scale": 0}, True),
                                      ({"unit": "KGM", "scale": 1}, False), ({"unit": "LBR", "scale": 2, "increment": 25}, False),
                                      ({"unit": "C62", "scale": 2}, False), ("each", False)])
def test_sold_each(qu, each):
    assert mapping.sold_each({} if qu is None else {"quantity_unit": qu}) is each


def test_provenance_is_kept_and_score_is_blocked():
    three = cards()[0][0]
    u = three["ucp"]
    assert (u["host"], u["product_id"], u["variant_id"], u["version"], u["transport"]) == (
        "mall.example.kr", "prod_citrus", "var_3kg", "2026-08-25", "rest")
    assert u["seen_at"] == "2026-11-04 22:30" and u["score_use"] == "block"


@pytest.mark.parametrize("status, headers, expect", [
    (200, {"Cache-Control": "public, max-age=3600", "Content-Type": "application/json"}, []),
    (301, {"Location": "https://trendguide.co.kr/.well-known/ucp"}, ["리다이렉트"]),
    (200, {"Cache-Control": "max-age=600", "Content-Type": "application/json"}, ["public"]),          # GitHub Pages 기본값 모양
    (200, {"Cache-Control": "public, max-age=30", "Content-Type": "application/json"}, ["max-age≥60"]),
    (200, {"Cache-Control": "public, max-age=3600, no-cache", "Content-Type": "application/json"}, ["no-cache"]),
    (200, {"Cache-Control": "public, max-age=3600", "Content-Type": "application/octet-stream"}, ["Content-Type"]),
])
def test_published_profile_check(status, headers, expect):
    http = Http(get=Resp(status, platform.platform_profile() if status == 200 else None, headers))
    problems = schemas.check_published_profile("https://trendguide.kr/.well-known/ucp", http=http)
    assert (problems == []) if not expect else all(any(word in p for p in problems) for word in expect)


def test_our_generated_profile_passes_the_official_platform_schema():
    http = Http(get=Resp(200, platform.platform_profile(), {"Cache-Control": "public, max-age=3600",
                                                            "Content-Type": "application/json; charset=utf-8"}))
    assert schemas.check_published_profile("https://trendguide.kr/.well-known/ucp", http=http) == []
    broken = platform.platform_profile()
    del broken["ucp"]["payment_handlers"]
    http = Http(get=Resp(200, broken, {"Cache-Control": "public, max-age=3600", "Content-Type": "application/json"}))
    assert any("payment_handlers" in p for p in schemas.check_published_profile("https://trendguide.kr/.well-known/ucp", http=http))



# ── p45 (GPT 검토 11-06) ────────────────────────────────────

class FailingRefHttp(Http):
    """협상 schema 는 주지만 참조 하나는 실패하는 가짜 HTTP."""

    def __init__(self, fail_url, **kw):
        super().__init__(**kw)
        self.fail_url = fail_url

    def get(self, url, **kw):
        if url == self.fail_url:
            self.calls.append(("GET", url, kw))
            return Resp(500, None)
        return super().get(url, **kw)


@pytest.mark.parametrize("profile", ["profile_rest.json", "profile_mcp_only.json"])
@pytest.mark.parametrize("fail", ["https://ucp.dev/2026-08-25/schemas/shopping/catalog_search.json",
                                  "https://ucp.dev/2026-08-25/schemas/shopping/types/variant.json",
                                  "https://ucp.dev/2026-08-25/schemas/common/types/price.json"])
def test_any_schema_failure_means_zero_merchant_posts(profile, fail):
    """협상 schema 든 깊은 참조 하나든, 확보에 실패하면 REST·MCP 모두 판매자 POST 0회."""
    m = discovery.negotiate("x.example.kr", fx(profile))
    http = FailingRefHttp(fail, post=Resp(200, fx("search_krw.json")))
    out = client.search(m, "감귤", http=http, profile_url=PROFILE)
    assert not out.ok and out.code == "schema_unavailable"
    assert not any(c[0] == "POST" for c in http.calls)


def test_validation_does_not_fetch_after_the_request():
    """요청 뒤 검증 단계에서는 네트워크 조회가 없다 (미리 확보한 것만)."""
    m = discovery.negotiate("mall.example.kr", fx("profile_rest.json"))
    http = Http(post=Resp(200, fx("search_krw.json")))
    order = []
    real_get, real_post = http.get, http.post
    http.get = lambda url, **kw: (order.append("GET"), real_get(url, **kw))[1]
    http.post = lambda url, **kw: (order.append("POST"), real_post(url, **kw))[1]
    out = client.search(m, "감귤", http=http, profile_url=PROFILE)
    assert out.ok and out.schema_valid is True
    assert order[-1] == "POST" and "GET" not in order[order.index("POST"):]


def test_cards_only_from_validated_outcomes():
    m = discovery.negotiate("mall.example.kr", fx("profile_rest.json"))
    ok = client.search(m, "감귤", http=Http(post=Resp(200, fx("search_krw.json"))), profile_url=PROFILE)
    got, _ = mapping.cards_from(ok, m, "예시몰")
    assert got and all(c["ucp"]["version"] == "2026-08-25" for c in got)
    bad = fx("search_krw.json")
    del bad["products"][0]["price_range"]
    failed = client.search(m, "감귤", http=Http(post=Resp(200, bad)), profile_url=PROFILE)
    assert failed.response is None
    for outcome in (failed, client.SearchOutcome("mall.example.kr", True, response=fx("search_krw.json"))):
        with pytest.raises(ValueError):
            mapping.cards_from(outcome, m, "예시몰")                  # 검증 표시 없는 결과로는 못 만듦


def test_each_with_order_increment_is_held_and_price_not_multiplied():
    resp = fx("search_krw.json")
    v = resp["products"][1]["variants"][0]
    v["quantity_unit"] = {"unit": "C62", "scale": 0, "increment": 6}
    got, skipped = mapping._to_cards(resp, host="mall.example.kr", merchant_name="예시몰")
    held = next(s for s in skipped if s["title"].startswith("감귤 선물세트"))
    assert held["reason"] == "6개 단위 주문 · 현재 카드에서 주문 조건 표시 불가"
    assert held["price"] == {"amount": 39000, "currency": "KRW"}          # 1개 기준 가격 그대로 (묶음 가격 아님)
    assert all(not c["title"].startswith("감귤 선물세트") for c in got)


def _coupang(title, price):
    from app.services.chat import explain

    return explain.enrich({"key": title[:8], "title": title, "price": price, "total": price, "mall": "쿠팡"}, {})


def _ucp_cards(unit_amount, title_suffix):
    from app.services.chat import explain

    resp = fx("search_krw.json")
    for prod in resp["products"]:
        prod["title"] = prod["title"] + title_suffix
        for v in prod["variants"]:
            if v.get("unit_price"):
                v["unit_price"]["amount"] = unit_amount
    got, _ = mapping._to_cards(resp, host="mall.example.kr", merchant_name="예시몰")
    return [explain.enrich(dict(c), {}) for c in got]                 # enrich 를 거쳐도 다시 채워지지 않아야


@pytest.mark.parametrize("unit_amount, suffix", [(630, ""), (1, " 10kg"), (99999, " 100g x 50팩"), (5, " 1kg 2kg")])
def test_seller_unit_price_and_title_weight_never_change_roles_or_order(unit_amount, suffix):
    """판매자 단위가격·상품명 중량만 바꿔도 enrich → choose 의 역할·순서가 같다."""
    from app.services.chat import explain

    base = [_coupang("제주 감귤 3kg", 21000), _coupang("제주 감귤 5kg", 30000)]
    ucp = _ucp_cards(unit_amount, suffix)
    assert all(c["per100g"] is None and c["weight_g"] is None and c["per_unit"] is None for c in ucp)
    def sig(picked):          # 카드 식별 = UCP 옵션 ID (상품명이 바뀌면 enrich 의 key 도 바뀌므로)
        return [((c.get("ucp") or {}).get("variant_id") or c["title"], c["role"]) for c in picked["picks"] + picked["others"]]

    picked = explain.choose(base + ucp, ask="감귤")
    assert sig(picked) == sig(explain.choose(base + _ucp_cards(630, ""), ask="감귤"))
    value = next(c for c in picked["picks"] if c["role"] == "value")
    assert value["mall"] == "쿠팡"                                      # 가성비는 비교 가능한 카드끼리만


def test_blocked_cards_stay_blocked_after_reweigh():
    from app.services.chat import explain

    card = dict(_ucp_cards(630, " 3kg")[0], per100g=1, weight_g=3000)    # 예전 값이 남아 있어도
    again = explain.reweigh(card)
    assert again["per100g"] is None and again["weight_g"] is None



# ── p46 (GPT 검토 11-06 17:11) ──────────────────────────────

class MapHttp(Http):
    """주소 → 문서 사전으로 응답하는 가짜 HTTP (스키마 구조 시험용).  없는 주소는 404, 예외 주소는 예외."""

    def __init__(self, docs, raise_on=None, **kw):
        super().__init__(**kw)
        self.docs, self.raise_on = docs, raise_on or {}

    def get(self, url, **kw):
        self.calls.append(("GET", url, kw))
        if url in self.raise_on:
            raise self.raise_on[url]
        return Resp(200, self.docs[url]) if url in self.docs else Resp(404, None)


T = "https://ucp.dev/test"


def _root(search_ref):
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": f"{T}/root.json",
            "$defs": {"search_response": {"$ref": search_ref}}}


def test_nested_id_is_the_base_for_relative_refs():
    """sub/base.json 안의 'leaf.json' 은 sub/leaf.json 이다 (루트의 leaf.json 이 아님)."""
    docs = {f"{T}/root.json": _root("sub/base.json"),
            f"{T}/sub/base.json": {"$id": f"{T}/sub/base.json", "$ref": "leaf.json"},
            f"{T}/sub/leaf.json": {"type": "object", "required": ["products"]},
            f"{T}/leaf.json": {"type": "string"}}                       # 잘못 찾으면 이걸 쓰게 됨
    prepared = schemas.prepare(f"{T}/root.json", http=MapHttp(docs))
    assert f"{T}/sub/leaf.json" in prepared.bundle and f"{T}/leaf.json" not in prepared.bundle
    assert schemas.validate_search_response({"products": []}, prepared)[0] is True
    assert schemas.validate_search_response({}, prepared)[0] is False


def test_embedded_id_inside_a_document_changes_the_base():
    docs = {f"{T}/root.json": {**_root("#/$defs/inner"),
                               "$defs": {"search_response": {"$ref": "#/$defs/inner"},
                                         "inner": {"$id": f"{T}/nested/inner.json", "$ref": "leaf.json"}}},
            f"{T}/nested/leaf.json": {"type": "object"}}
    prepared = schemas.prepare(f"{T}/root.json", http=MapHttp(docs))
    assert f"{T}/nested/leaf.json" in prepared.bundle


@pytest.mark.parametrize("docs, why", [
    ({f"{T}/root.json": _root("#/$defs/missing")}, "해석"),                         # 없는 위치를 가리킴
    ({f"{T}/root.json": {"$id": f"{T}/root.json", "$defs": {}}}, "해석"),            # search_response 없음
    ({f"{T}/root.json": _root("sub/base.json"),
      f"{T}/sub/base.json": {"$dynamicRef": "#meta"}}, "지원하지 않는"),             # 지원하지 않는 참조 구조
    ({f"{T}/root.json": _root("sub/base.json")}, "HTTP 404"),                         # 참조 문서 없음
    ({f"{T}/root.json": {**_root("#"), "type": 5}}, "해석"),                          # schema 자체가 잘못됨
])
@pytest.mark.parametrize("profile", ["profile_rest.json", "profile_mcp_only.json"])
def test_unresolvable_or_unsupported_schema_means_zero_posts(docs, why, profile):
    doc = fx(profile)
    doc["ucp"]["capabilities"]["dev.ucp.shopping.catalog.search"] = [{"version": "2026-08-25",
                                                                       "schema": f"{T}/root.json"}]
    m = discovery.negotiate("x.example.kr", doc)
    assert m.ok and m.schemas["dev.ucp.shopping.catalog.search"] == f"{T}/root.json"
    http = MapHttp(docs, post=Resp(200, fx("search_krw.json")))
    out = client.search(m, "감귤", http=http, profile_url=PROFILE)
    assert not out.ok and out.code == "schema_unavailable" and why in out.error
    assert not any(c[0] == "POST" for c in http.calls)


@pytest.mark.parametrize("exc", [TimeoutError("timed out"), ConnectionError("reset")])
@pytest.mark.parametrize("profile", ["profile_rest.json", "profile_mcp_only.json"])
def test_schema_fetch_timeout_returns_schema_unavailable(exc, profile):
    """스키마 GET 의 타임아웃·연결 실패가 예외로 새지 않고 결과 객체로, 판매자 POST 0회."""
    m = discovery.negotiate("x.example.kr", fx(profile))
    deep = "https://ucp.dev/2026-08-25/schemas/shopping/types/variant.json"

    class Flaky(Http):
        def get(self, url, **kw):
            if url == deep:
                self.calls.append(("GET", url, kw))
                raise exc
            return super().get(url, **kw)

    http = Flaky(post=Resp(200, fx("search_krw.json")))
    out = client.search(m, "감귤", http=http, profile_url=PROFILE)
    assert not out.ok and out.code == "schema_unavailable" and type(exc).__name__ in out.error
    assert not any(c[0] == "POST" for c in http.calls)


@pytest.mark.parametrize("headers, now, seconds", [
    ({"Cache-Control": "max-age=10", "Age": "9"}, None, 1),
    ({"Cache-Control": "max-age=10", "Age": "15"}, None, 0),
    ({"Cache-Control": "public, max-age=60", "Date": "Fri, 06 Nov 2026 08:00:00 GMT"}, 1793952030.0, 30),
    ({"Cache-Control": "max-age=60", "Date": "Fri, 06 Nov 2026 08:00:00 GMT", "Age": "50"}, 1793952030.0, 10),
    ({"Cache-Control": "max-age=60", "Date": "not a date"}, 1793952030.0, 60),
    ({"Cache-Control": "max-age=60", "Date": "Fri, 06 Nov 2026 09:00:00 GMT"}, 1793952030.0, 60),   # 미래 Date → 나이 0
])
def test_cache_uses_only_the_remaining_freshness(headers, now, seconds):
    assert discovery.cache_seconds(headers, now=now) == seconds


def test_ucp_card_key_is_stable_across_title_changes_and_enrich():
    from app.services.chat import explain

    a = _ucp_cards(630, "")
    b = _ucp_cards(630, " 이름 변경 10kg")
    assert [c["key"] for c in a] == [c["key"] for c in b]
    raw, _ = mapping._to_cards(fx("search_krw.json"), host="mall.example.kr", merchant_name="예시몰")
    assert [c["key"] for c in raw] == [c["key"] for c in a]           # 변환 key == enrich 뒤 key
    assert all(c["price_compare_blocked"] for c in a + b)            # 차단 표시도 enrich 를 지나 보존


# ── p47 (GPT 검토 11-06 17:25): 문서 안에 포함된 리소스는 따로 가져오지 않는다 ─────────────

def _gets(http):
    return [c[1] for c in http.calls if c[0] == "GET"]


def test_embedded_resource_with_anchor_is_resolved_inside_the_document():
    """GPT 재현: 문서 안 $id 'nested.json' + $anchor 'x' 를 'nested.json#x' 로 참조 — 별도 주소가 404여도 통과, GET 없음."""
    docs = {f"{T}/root.json": {**_root("nested.json#x"),
                               "$defs": {"search_response": {"$ref": "nested.json#x"},
                                         "nested": {"$id": "nested.json",
                                                    "$defs": {"x": {"$anchor": "x", "type": "object",
                                                                    "required": ["products"]}}}}}}
    http = MapHttp(docs)
    prepared = schemas.prepare(f"{T}/root.json", http=http)
    assert _gets(http) == [f"{T}/root.json"]                                # nested.json 은 가져오지 않음
    assert schemas.validate_search_response({"products": []}, prepared)[0] is True
    assert schemas.validate_search_response({}, prepared)[0] is False


def test_embedded_resource_found_in_a_later_document_is_not_a_failure():
    """'c.json#x' 참조가 먼저 나오고, c.json 은 뒤에 받는 b.json 안에 포함 — c.json 404 는 실패가 아니다."""
    docs = {f"{T}/root.json": {**_root("#/$defs/both"),
                               "$defs": {"search_response": {"$ref": "#/$defs/both"},
                                         "both": {"allOf": [{"$ref": "c.json#x"}, {"$ref": "b.json"}]}}},
            f"{T}/b.json": {"$id": f"{T}/b.json", "$defs": {"c": {"$id": "c.json",
                                                                 "$defs": {"x": {"$anchor": "x", "type": "object"}}}}}}
    http = MapHttp(docs)
    prepared = schemas.prepare(f"{T}/root.json", http=http)
    assert f"{T}/c.json" not in prepared.bundle
    assert schemas.validate_search_response({"products": []}, prepared)[0] is True
    assert schemas.validate_search_response("문자열", prepared)[0] is False


def test_root_without_id_uses_retrieval_url_for_embedded_ids():
    docs = {f"{T}/root.json": {"$defs": {"search_response": {"$ref": "inner.json"},
                                         "inner": {"$id": "inner.json", "type": "object", "required": ["products"]}}}}
    http = MapHttp(docs)
    prepared = schemas.prepare(f"{T}/root.json", http=http)
    assert _gets(http) == [f"{T}/root.json"]
    assert schemas.validate_search_response({}, prepared)[0] is False


@pytest.mark.parametrize("profile", ["profile_rest.json", "profile_mcp_only.json"])
def test_truly_external_missing_ref_still_holds_the_request(profile):
    """포함 리소스가 아닌 실제 외부 참조가 없으면 그대로 보류 (POST 0회)."""
    doc = fx(profile)
    doc["ucp"]["capabilities"]["dev.ucp.shopping.catalog.search"] = [{"version": "2026-08-25",
                                                                       "schema": f"{T}/root.json"}]
    m = discovery.negotiate("x.example.kr", doc)
    docs = {f"{T}/root.json": {**_root("other.json#x"),
                               "$defs": {"search_response": {"$ref": "other.json#x"},
                                         "nested": {"$id": "nested.json", "$anchor": "x"}}}}
    http = MapHttp(docs, post=Resp(200, fx("search_krw.json")))
    out = client.search(m, "감귤", http=http, profile_url=PROFILE)
    assert not out.ok and out.code == "schema_unavailable" and "404" in out.error
    assert f"{T}/other.json" in _gets(http) and f"{T}/nested.json" not in _gets(http)
    assert not any(c[0] == "POST" for c in http.calls)
