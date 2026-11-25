"""⑥ 스마트스토어 상품 가져오기 (창 5, 2026-11-25) — 커머스API 읽기 전용, 키 암호화, 표준 칸 변환, 칸 주인 규칙,
새 상품 상세페이지 입력 미리 채우기(사진 권리는 셀러가), 오류 문구."""

from __future__ import annotations

import base64
import os
import re
from pathlib import Path

import bcrypt
import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

os.environ.setdefault("CORPMALL_KEY", Fernet.generate_key().decode())

from app.services.corpmall import store as corp  # noqa: E402
from app.services.seller import catalog, detail_page, naver_api, products, store  # noqa: E402

IP = "1.1.1.1"
SECRET = bcrypt.gensalt().decode()
CID = "AbCdEf1234567890xyz"


class R:
    def __init__(self, status=200, body=None):
        self.status_code, self._b, self.headers = status, body or {}, {}

    def json(self):
        return self._b


def origin(name="제주 노지 감귤", price=23900, combos=None, notice=None, certs=None):
    return {"originProduct": {
        "name": name, "salePrice": price, "stockQuantity": 30, "statusType": "SALE",
        "images": {"representativeImage": {"url": "https://shop-phinf.pstatic.net/a.jpg"},
                   "optionalImages": [{"url": "https://shop-phinf.pstatic.net/b.jpg"}, {"url": "http://x/c.jpg"}]},
        "deliveryInfo": {"deliveryFee": {"deliveryFeeType": "CONDITIONAL_FREE", "baseFee": 3000, "freeConditionalAmount": 30000}},
        "customerBenefit": {"immediateDiscountPolicy": {"discountMethod": {"value": 10, "unitType": "PERCENT"}}},
        "detailAttribute": {
            "originAreaInfo": {"content": "국산(제주특별자치도)"},
            "productCertificationInfos": certs or [],
            "sellerCodeInfo": {"sellerManagementCode": "GG-01"},
            "naverShoppingSearchInfo": {"brandName": "한라", "manufacturerName": "한라농장"},
            "optionInfo": {"optionCombinations": combos or []},
            "productInfoProvidedNotice": notice or {
                "productInfoProvidedNoticeType": "AGRICULTURAL_PRODUCTS",
                "agriculturalProducts": {"productName": "감귤", "packageUnit": "5kg", "producer": "한라농장",
                                         "location": "제주", "packDateText": "2026-12 수확", "keep": "서늘한 곳",
                                         "customerServicePhoneNumber": "064-000-0000", "mysteryField": "x",
                                         "returnCostReason": "상세 참조"}}},
    }}  # fmt: skip


class Http:
    """네이버 흉내 — 토큰 서명을 실제로 검증한다."""

    def __init__(self, items, origins, *, token_status=200, token_code=None, search_429=0):
        self.items, self.origins, self.calls = items, origins, []
        self.token_status, self.token_code, self.search_429 = token_status, token_code, search_429

    def post(self, url, **kw):
        self.calls.append(("POST", url))
        if url.endswith("/v1/oauth2/token"):
            d = kw["data"]
            assert d["type"] == "SELF" and d["grant_type"] == "client_credentials"
            want = base64.b64encode(
                bcrypt.hashpw(f"{d['client_id']}_{d['timestamp']}".encode(), SECRET.encode())
            ).decode()
            if self.token_status != 200:
                return R(self.token_status, {"code": self.token_code})
            assert d["client_secret_sign"] == want
            return R(200, {"access_token": "tok", "expires_in": 10800})
        if url.endswith("/v1/products/search"):
            if self.search_429:
                self.search_429 -= 1
                return R(429, {"code": "GW.RATE_LIMIT"})
            page, size = kw["json"]["page"], kw["json"]["size"]
            chunk = self.items[(page - 1) * size : page * size]
            return R(
                200,
                {
                    "contents": chunk,
                    "totalElements": len(self.items),
                    "totalPages": max(1, -(-len(self.items) // size)),
                },
            )
        raise AssertionError(url)

    def get(self, url, **kw):
        self.calls.append(("GET", url))
        assert kw["headers"]["Authorization"] == "Bearer tok"
        no = url.rsplit("/", 1)[1]
        return R(200, self.origins[no]) if no in self.origins else R(404, {"code": "NOT_FOUND"})


def item(no, cpn, name="제주 노지 감귤", cat="식품>과일>감귤", status="SALE"):
    return {"originProductNo": no, "channelProducts": [{"channelProductNo": cpn, "name": name, "statusType": status,
                                                         "wholeCategoryName": cat, "salePrice": 23900}]}  # fmt: skip


@pytest.fixture
def eng(monkeypatch):
    monkeypatch.setattr(naver_api.time, "sleep", lambda s: None)
    corp.reset_limits()
    e = naver_api.engine()
    from app.services.seller import scm

    scm.meta.create_all(e)
    with e.begin() as c:
        for t in (naver_api.t_key, detail_page.t_detail, catalog.t_unit, catalog.t_group, catalog.t_base, scm.t_stock,
                  products.t_listing, products.t_product, store.t_event, store.t_key, store.t_seller):  # fmt: skip
            c.execute(t.delete())
    return e


def _seller(eng, name="한라농장"):
    s = store.create_seller(eng, name=name, kind="direct", contact={"name": "김", "email": "k@a.kr"}, by="operator")
    store.set_status(eng, s["seller_id"], "active", by="operator", reason="ok")
    return s["seller_id"], store.issue_key(eng, s["seller_id"], by="operator")["code"]


def test_read_only_module_has_no_write_calls():
    src = Path(naver_api.__file__).read_text(encoding="utf-8")
    assert not re.search(r"\.(put|patch|delete)\(", src)
    paths = set(re.findall(r'f?"(/v\d/[a-z0-9/_-]+)', src))
    assert paths <= {"/v1/oauth2/token", "/v1/products/search", "/v2/products/origin-products/"}, paths


def test_key_is_encrypted_and_never_shown(eng):
    sid, k = _seller(eng)
    with pytest.raises(store.SellerError, match="시크릿"):
        naver_api.save_key(eng, k, IP, client_id=CID, secret="plain")
    st = naver_api.save_key(eng, k, IP, client_id=CID, secret=SECRET, store_slug="halla")
    assert st["connected"] and SECRET not in str(st) and CID not in str(st) and st["store_slug"] == "halla"
    with eng.connect() as c:
        raw = c.execute(naver_api.t_key.select()).mappings().first()
    assert SECRET not in raw["enc"] and CID not in raw["enc"]
    with eng.connect() as c:
        ev = [r["detail"] for r in c.execute(store.t_event.select()).mappings()]
    assert SECRET not in str(ev)
    assert naver_api.delete_key(eng, k, IP)["connected"] is False


def test_rows_from_options_discount_ship_notice():
    combos = [
        {"id": 11, "optionName1": "3kg", "price": 0, "stockQuantity": 5, "usable": True},
        {"id": 12, "optionName1": "5kg", "price": 8000, "stockQuantity": 0, "usable": False},
    ]
    rows, dp = naver_api.rows_from(
        900, origin(combos=combos), item(900, 7001)["channelProducts"][0], store_slug="halla"
    )
    assert [r["ext_no"] for r in rows] == ["900-11", "900-12"]
    assert rows[0]["price"] == 21510 and rows[0]["list_price"] == 23900  # 10% 즉시할인, 10원 단위
    assert rows[1]["price"] == 29510 and rows[1]["display"] == "판매중지"
    assert rows[0]["sale_url"] == "https://smartstore.naver.com/halla/products/7001"
    assert rows[0]["ship_type"] == "조건부 무료" and rows[0]["free_over"] == 30000
    assert rows[0]["origins"] == "국산(제주특별자치도)" and rows[0]["seller_code"] == "GG-01"
    assert (
        dp["notice_kind"] == "agri" and dp["notice"]["volume"] == "5kg" and dp["notice"]["cs_phone"] == "064-000-0000"
    )
    assert dp["unknown_notice"] == ["mysteryField"]  # 모르는 칸은 보고 (공통 안내 칸은 뺌)
    assert [i["url"] for i in dp["images"]] == [
        "https://shop-phinf.pstatic.net/a.jpg",
        "https://shop-phinf.pstatic.net/b.jpg",
    ]
    for r in rows:
        catalog.normalize(r)  # 표준 칸 검사 통과


def test_preview_changes_nothing_then_sync_imports_and_prefills(eng):
    sid, k = _seller(eng)
    naver_api.save_key(eng, k, IP, client_id=CID, secret=SECRET, store_slug="halla")
    items = [
        item(900, 7001),
        item(901, 7002, "국산 무농약 쌀 10kg", "식품>농산물>쌀"),
        item(902, 7003, status="DELETE"),
    ]
    origins = {
        "900": origin(),
        "901": origin(
            "국산 무농약 쌀 10kg",
            39000,
            certs=[{"name": "무농약", "certificationNumber": "12-34-567", "agentName": "국립농산물품질관리원"}],
        ),
    }
    http = Http(items, origins, search_429=1)
    p = naver_api.preview(eng, k, IP, http=http)
    assert p["total"] == 3 and p["units"] == 2 and p["problems"] == [] and p["unknown_notice"] == ["mysteryField"]
    assert products.list_mine(eng, k, IP) == []  # 미리보기는 아무것도 바꾸지 않음
    with pytest.raises(store.SellerError, match="기준 판매처"):
        naver_api.sync(eng, k, IP, http=Http(items, origins))
    r = naver_api.sync(eng, k, IP, http=Http(items, origins), set_base=True)
    assert r["added"] == 2 and r["prefilled"] == 2 and catalog.base_channel(eng, sid) == "naver"
    mine = {x["name"]: x for x in products.list_mine(eng, k, IP)}
    rice = mine["국산 무농약 쌀 10kg"]
    assert rice["status"] == "pending" and rice["declared"]["certs"][0]["kind"] == "무농약"  # 판매자 표기 · 검수 대기
    assert all(f["source"] != "verified" for f in rice["facts"])
    d = detail_page.get(eng, k, IP, mine["제주 노지 감귤"]["product_id"])["current"]["inputs"]
    assert d["notice_kind"] == "agri" and d["notice"]["producer"] == "한라농장" and d["image_ok"] is False
    # 셀러가 고친 입력은 다시 가져와도 덮어쓰지 않는다 · 가격만 바뀌면 바로 반영
    detail_page.save_inputs(eng, k, IP, mine["제주 노지 감귤"]["product_id"], {"memo": "직접 쓴 메모", "notice": {}})
    origins["900"] = origin(price=25900)
    r2 = naver_api.sync(eng, k, IP, http=Http(items, origins))
    assert r2["fast"] == 1 and r2["added"] == 0 and r2["prefilled"] == 0
    assert (
        detail_page.get(eng, k, IP, mine["제주 노지 감귤"]["product_id"])["current"]["inputs"]["memo"] == "직접 쓴 메모"
    )
    # 판매처에서 사라지면 우리 몰 판매 끔
    r3 = naver_api.sync(eng, k, IP, http=Http(items[1:], origins))
    assert r3["missing"] == 1
    st = naver_api.status(eng, k, IP)
    assert st["last_report"]["missing"] == 1 and st["last_error"] == ""


def test_ip_error_is_explained_and_recorded(eng):
    _sid, k = _seller(eng)
    naver_api.save_key(eng, k, IP, client_id=CID, secret=SECRET)
    with pytest.raises(store.SellerError, match="API호출 IP"):
        naver_api.preview(eng, k, IP, http=Http([], {}, token_status=403, token_code="GW.IP_NOT_ALLOWED"))
    assert "API호출 IP" in naver_api.status(eng, k, IP)["last_error"]
    with pytest.raises(store.SellerError, match="먼저 넣어"):
        naver_api.delete_key(eng, k, IP) and naver_api.preview(eng, k, IP, http=Http([], {}))


def test_sellers_are_isolated_and_routes(eng, monkeypatch):
    from app.main import app

    _s1, k1 = _seller(eng)
    _s2, k2 = _seller(eng, "나농장")
    c = TestClient(app)
    j = c.post(
        "/seller/api/naver/key", json={"key": k1, "client_id": CID, "secret": SECRET, "store_slug": "halla"}
    ).json()
    assert j["ok"] and j["naver"]["connected"]
    assert c.post("/seller/api/naver", json={"key": k2}).json()["naver"]["connected"] is False
    monkeypatch.setattr(
        naver_api,
        "_client_for",
        lambda eng, sid, http: (
            naver_api.Client(CID, SECRET, http=Http([item(900, 7001)], {"900": origin()})),
            {"store_slug": "halla"},
        ),
    )
    assert c.post("/seller/api/naver/look", json={"key": k1}).json()["preview"]["units"] == 1
    j = c.post("/seller/api/naver/sync", json={"key": k1, "set_base": True}).json()
    assert j["ok"] and j["sync"]["added"] == 1
    assert 'id="nv-h"' in c.get("/seller").text
