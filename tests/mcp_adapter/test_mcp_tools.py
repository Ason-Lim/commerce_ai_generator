"""MCP 도구 2개 (2026-11-02): 웹·공통 서비스와 같은 상품·순위, 제휴 링크는 허용 전까지 비움, 레시피 조회."""
from __future__ import annotations

import asyncio
import importlib.util
import json

import pytest

from app.domain.commerce.requests import SearchRequest
from app.mcp_adapter import tools
from app.services.commerce.search import search_products
from app.services.recipe_chat.catalog import RecipeResolver
from tests.services.chat.conftest import FakeShopping
from tests.services.chat.test_commerce_contract import ITEMS, _registry


def _sig(items):
    return [(i["score"]["rank"], i["product"]["key"], i["product"]["title"], i["offer"]["price_krw"]) for i in items]


def test_search_matches_the_service_and_holds_affiliate_links(tmp_path, monkeypatch):
    monkeypatch.setenv("NAVER_CONNECT_REGISTRY_CSV", _registry(tmp_path))
    held = tools.food_search_products("사과 추천해줘", shopping=FakeShopping(items=ITEMS), env={})
    full = search_products(SearchRequest(text="사과 추천해줘"), shopping=FakeShopping(items=ITEMS)).model_dump(mode="json")
    assert held["schema_version"] == "commerce.v1" and held["status"] == "ok"
    same = [i for i in full["items"] if i["section"] != "connect"]
    assert _sig(held["items"]) == _sig(same)                              # 순위·상품은 그대로
    assert not [i for i in held["items"] if i["section"] == "connect"]    # 쇼핑커넥트 등록 목록은 뺀다
    for it in held["items"]:
        if it["offer"]["link_type"] == "affiliate":
            assert it["offer"]["product_url"] is None
        else:
            assert it["offer"]["product_url"]
    assert tools.AFFILIATE_HELD in held["warnings"]
    assert held["disclosure"] == full["disclosure"]
    json.dumps(held, ensure_ascii=False)


def test_affiliate_links_only_when_allowed(tmp_path, monkeypatch):
    monkeypatch.setenv("NAVER_CONNECT_REGISTRY_CSV", _registry(tmp_path))
    monkeypatch.setenv("NAVER_CONNECT_ON_SITE", "1")       # 네이버가 외부 웹/앱 활동을 허용한 경우만
    out = tools.food_search_products("사과 추천해줘", shopping=FakeShopping(items=ITEMS), env={"MCP_AFFILIATE_LINKS": "1"})
    assert any(i["section"] == "connect" for i in out["items"])
    assert all(i["offer"]["product_url"] for i in out["items"])
    assert tools.AFFILIATE_HELD not in out["warnings"]


def test_limit_is_clamped_and_blank_text_is_refused_without_calling_the_seller_api():
    for blank in ("", "   ", None):
        shop = FakeShopping(items=ITEMS)
        out = tools.food_search_products(blank, limit=99, shopping=shop, env={})
        assert out["status"] == "error" and out["errors"][0]["code"] == "bad_request"
        assert shop.calls == []                                      # p35: 판매처 API 를 부르지 않음
    shop = FakeShopping(items=ITEMS)
    tools.food_search_products("사과 추천", limit=99, shopping=shop, env={})
    assert len(shop.calls) == 1


def test_affiliate_images_are_held_with_links():
    items = [dict(it, image_url="https://ads-partners.coupang.com/image1/x.jpg") for it in ITEMS]
    out = tools.food_search_products("사과 추천해줘", shopping=FakeShopping(items=items), env={})
    for it in out["items"]:
        if it["offer"]["link_type"] == "affiliate":
            assert it["product"]["image_url"] is None and it["offer"]["product_url"] is None
        else:
            assert it["product"]["image_url"]


def _preview_partner(tmp_path, monkeypatch):
    import csv

    monkeypatch.setenv("PARTNER_PREVIEW", "1")                     # 웹 개발 화면용 설정이 켜져 있는 상황
    monkeypatch.setenv("PARTNER_DATA_DIR", str(tmp_path))
    with (tmp_path / "permissions.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["업체", "상태"])
        w.writeheader()
        w.writerow({"업체": "온브릭스", "상태": "요청함"})
    (tmp_path / "onbrix").mkdir()
    with (tmp_path / "onbrix" / "products_sample.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)    # data/partners/*/products_sample.csv 와 같은 열
        w.writerow(["상품ID", "상품명", "품목", "품종", "중량(g)", "수량", "판매가", "정가", "배송비", "당도(Brix)", "산지",
                    "등급", "상품URL", "이미지URL", "재고상태", "가격기준일시", "비고"])
        w.writerow(["SAMPLE-1", "(예시) 사과 부사 5kg", "사과", "부사", "5000", "", "19900", "", "0", "", "", "",
                    "https://www.onbrix.co.kr/", "", "판매중", "2026-11-02 09:00", "미리 보기용 예시"])


def test_web_service_still_shows_preview_when_its_setting_is_on(tmp_path, monkeypatch):
    _preview_partner(tmp_path, monkeypatch)
    full = search_products(SearchRequest(text="사과 추천해줘"), shopping=FakeShopping(items=ITEMS))
    assert full.provenance.preview_data is True and any("(예시)" in i.product.title for i in full.items)


def test_mcp_call_excludes_preview_by_its_own_policy(tmp_path, monkeypatch):
    """p37: 프로세스 환경(PARTNER_PREVIEW=1)과 상관없이 MCP 호출은 미리 보기 상품을 넣지 않는다 — 보류가 아니라 정상 결과."""
    _preview_partner(tmp_path, monkeypatch)
    out = tools.food_search_products("사과 추천해줘", shopping=FakeShopping(items=ITEMS), env={})
    assert out["status"] == "ok" and out["provenance"]["preview_data"] is False
    assert not any("(예시)" in i["product"]["title"] for i in out["items"])
    assert __import__("os").environ["PARTNER_PREVIEW"] == "1"     # 환경 변수는 건드리지 않음


def test_mcp_fails_closed_on_the_explicit_preview_flag(monkeypatch):
    """명시 값(provenance.preview_data)이 참이면 통째로 보류 — 경고 문구가 바뀌어도 동작."""
    from app.domain.commerce.models import CommerceResult, Provenance

    def fake(req, **kw):
        assert kw.get("allow_preview") is False
        return CommerceResult(request_id="r", status="ok", warnings=["문구가 달라져도"],
                              provenance=Provenance(preview_data=True))

    monkeypatch.setattr("app.services.commerce.search.search_products", fake)
    out = tools.food_search_products("사과", shopping=FakeShopping(items=ITEMS), env={})
    assert out["status"] == "held" and out["errors"][0]["code"] == "preview_data_blocked" and out["items"] == []


def test_server_does_not_mutate_the_preview_env():
    src = (__import__("pathlib").Path(tools.__file__).with_name("server.py")).read_text(encoding="utf-8")
    assert 'os.environ["PARTNER_PREVIEW"]' not in src


def test_server_binds_the_db_engine_once(monkeypatch):
    """MCP 서버도 웹처럼 DB 연결을 등록해야 레시피 카탈로그를 읽는다 (p36, EngineProviderUnboundError)."""
    from app.db import engine_provider, lifecycle
    from app.mcp_adapter import server

    class FakeLifecycle:
        made = 0

        def __init__(self):
            FakeLifecycle.made += 1
            self.engine = object()

        def initialize(self):
            return self.engine

    monkeypatch.setattr(lifecycle, "EngineLifecycle", FakeLifecycle)
    engine_provider.unbind_engine()
    try:
        server._bind_engine()
        first = engine_provider.get_engine()
        server._bind_engine()                                       # 두 번째는 그대로
        assert engine_provider.get_engine() is first and FakeLifecycle.made == 1
    finally:
        engine_provider.unbind_engine()


def test_server_keeps_working_when_db_is_unreachable(monkeypatch, capsys):
    from app.db import engine_provider, lifecycle
    from app.mcp_adapter import server

    class Broken:
        def __init__(self):
            raise RuntimeError("no db")

    monkeypatch.setattr(lifecycle, "EngineLifecycle", Broken)
    engine_provider.unbind_engine()
    server._bind_engine()
    assert not engine_provider.is_bound() and "DB 연결 등록 실패" in capsys.readouterr().err


def test_search_adds_non_affiliate_naver_search_links(monkeypatch):
    """2026-11-04: 웹 대화와 같은 네이버쇼핑 검색 링크 — 제휴 링크를 비워 둔 상태에서도 나온다 (제휴 아님)."""
    from urllib.parse import quote

    out = tools.food_search_products("사과 추천해줘", shopping=FakeShopping(items=ITEMS), env={})
    links = out["naver_search"]
    assert links and links[0]["query"] == "사과"
    assert links[0]["url"] == "https://search.shopping.naver.com/search/all?query=" + quote("사과")
    assert all(l["affiliate"] is False and l["link_type"] == "search" and l["check"] for l in links)
    assert len(links) <= 3
    assert tools.food_search_products("와인 추천해줘", shopping=FakeShopping(items=[]), env={})["naver_search"] == []
    monkeypatch.setenv("NAVER_SEARCH_LINKS", "0")
    assert tools.food_search_products("사과 추천해줘", shopping=FakeShopping(items=ITEMS), env={})["naver_search"] == []
