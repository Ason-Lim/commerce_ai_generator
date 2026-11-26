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


OWN: list[str] = []


@pytest.fixture(autouse=True)
def _own(monkeypatch):
    OWN.clear()
    monkeypatch.setattr(naver_api, "allowed", lambda sid, env=None: sid in OWN)


def _seller(eng, name="한라농장", own=True):
    s = store.create_seller(eng, name=name, kind="direct", contact={"name": "김", "email": "k@a.kr"}, by="operator")
    store.set_status(eng, s["seller_id"], "active", by="operator", reason="ok")
    if own:
        OWN.append(s["seller_id"])
    return s["seller_id"], store.issue_key(eng, s["seller_id"], by="operator")["code"]


def test_only_operator_own_stores_naver_policy(eng, monkeypatch):
    """네이버 정책: 내스토어 앱 키를 다른 셀러에게서 받아 서비스하면 안 됨 → 직영 스토어(NAVER_OWN_SELLERS)만."""
    monkeypatch.undo()  # 실제 allowed 로
    monkeypatch.setattr(naver_api.time, "sleep", lambda s: None)
    sid, k = _seller(eng, own=False)
    st = naver_api.status(eng, k, IP)
    assert st["allowed"] is False and "커머스솔루션" in st["not_allowed"]
    with pytest.raises(store.SellerError, match="직영 스토어"):
        naver_api.save_key(eng, k, IP, client_id=CID, secret=SECRET)
    assert naver_api.allowed(sid, {"NAVER_OWN_SELLERS": f"X1, {sid}"}) and not naver_api.allowed(sid, {})


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
    _s2, k2 = _seller(eng, "나농장", own=False)
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


# ── 이어받기·호출 제한 실측 (2026-11-26) ──────────────────────────────────
class Http429(Http):
    """search 를 n번째 호출부터 계속 429 로 막는다(Retry-After 1초)."""

    def __init__(self, items, origins, *, block_after=None, origin_block=None):
        super().__init__(items, origins)
        self.block_after, self.search_n, self.origin_block = block_after, 0, origin_block

    def post(self, url, **kw):
        if url.endswith("/v1/products/search"):
            self.search_n += 1
            if self.block_after is not None and self.search_n > self.block_after:
                return R429()
        return super().post(url, **kw)

    def get(self, url, **kw):
        if self.origin_block and url.rsplit("/", 1)[1] == self.origin_block:
            return R429()
        return super().get(url, **kw)


class R429(R):
    def __init__(self):
        super().__init__(429, {"code": "GW.RATE_LIMIT"})
        self.headers = {"Retry-After": "1"}


def test_resume_after_rate_limit_and_limit(eng, monkeypatch):
    sid, k = _seller(eng)
    naver_api.save_key(eng, k, IP, client_id=CID, secret=SECRET, store_slug="halla")
    monkeypatch.setattr(naver_api, "PAGE_SIZE", 2)
    items = [item(100 + i, 900 + i, name=f"감귤 {i}") for i in range(5)]
    origins = {str(100 + i): origin(name=f"감귤 {i}") for i in range(5)}
    waits = []
    monkeypatch.setattr(naver_api.time, "sleep", lambda s: waits.append(s))
    # 1회차: 2쪽까지 읽고 3쪽 검색이 계속 429 → 읽은 4개 반영, 3쪽부터 이어받기
    r1 = naver_api.sync(eng, k, IP, http=Http429(items, origins, block_after=2), set_base=True)
    assert r1["added"] >= 1 and r1["resume_page"] == 3 and r1["stopped"] == "rate" and r1["missing"] == 0
    assert 1 in waits and r1["measure"]["rate_waits"] == 3  # Retry-After 를 따름
    st = naver_api.status(eng, k, IP)
    assert st["last_report"]["resume_page"] == 3
    # 2회차: 3쪽부터 — 마지막 1개, 끝까지 → 이어받기 지움
    http = Http429(items, origins)
    r2 = naver_api.sync(eng, k, IP, http=http)
    assert r2["start_page"] == 3 and r2["resume_page"] is None and r2["missing"] == 0
    pages = [c for c in http.calls if c[1].endswith("/v1/products/search")]
    assert len(pages) == 1
    assert len([u for u in catalog.units_of(eng, sid).values() if u.get("channel") == "naver"]) == 5
    # 상세 조회가 429 면 그 쪽에서 멈추고 그 쪽부터 다시
    r3 = naver_api.sync(eng, k, IP, http=Http429(items, origins, origin_block="102"))
    assert r3["resume_page"] == 2 and r3["stopped"] == "rate"
    # 한 번 상한
    monkeypatch.setattr(naver_api, "MAX_PRODUCTS", 3)
    got = naver_api.fetch(
        naver_api.Client(CID, SECRET, http=Http(items, origins), sleep=lambda s: None), start_page=1, limit=3
    )
    assert got["fetched"] == 3 and got["next_page"] == 2 and got["stopped"] == "limit" and got["measure"]["calls"] >= 4
