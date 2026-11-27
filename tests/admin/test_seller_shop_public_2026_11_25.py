"""⑧ 미니숍 고객 공개 · UCP 공개 (창 5, 2026-11-25) — 꺼짐/시험/정식 단계, 정식 공개 조건(확정 고지·운영사 정보·
셀러 사업자 정보 확인·공개 동의), 중개 고지 자리, 고시 원문 대조 칸, UCP 카탈로그 응답이 공식 스키마에 맞는지."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

os.environ.setdefault("CORPMALL_KEY", Fernet.generate_key().decode())

from app.services.corpmall import store as corp  # noqa: E402
from app.services.seller import detail_page as D  # noqa: E402
from app.services.seller import products as prod  # noqa: E402
from app.services.seller import shop_public as SP  # noqa: E402
from app.services.seller import store as sel  # noqa: E402

from tests.admin.test_seller_detail_page_2026_11_25 import GOOD, IP, MEMO, NOTICE_AGRI  # noqa: E402

H = {"X-Access-Token": "test-token"}
BIZ = {"trade_name": "한라농장", "ceo": "김한라", "address": "제주 서귀포시 1", "phone": "064-000-0000",
       "email": "halla@example.kr", "biz_no": "220-81-62517", "mail_order_no": "2026-제주서귀포-0001"}  # fmt: skip
OPERATOR = {"trade_name": "시험운영사", "ceo": "홍길동", "address": "서울 1", "phone": "02-000-0000", "email": "op@example.kr",
            "biz_no": "220-81-62517", "mail_order_no": "2026-서울-0001", "hosting": "자체 서버", "terms_url": "/terms",
            "privacy_url": "/privacy"}  # fmt: skip
FIX = Path(__file__).resolve().parents[1] / "services" / "ucp" / "fixtures"


@pytest.fixture
def eng(monkeypatch):
    monkeypatch.delenv("SHOP_PUBLIC", raising=False)
    monkeypatch.delenv("SHOP_NOTICE_FILE", raising=False)
    corp.reset_limits()
    e = SP.engine()
    from app.services.seller import scm

    scm.meta.create_all(e)
    with e.begin() as c:
        for t in (
            SP.t_biz,
            D.t_detail,
            scm.t_stock,
            prod.t_listing,
            prod.t_product,
            sel.t_event,
            sel.t_key,
            sel.t_seller,
        ):
            c.execute(t.delete())
    return e


def _shop(eng, name="한라농장"):
    s = sel.create_seller(eng, name=name, kind="direct", contact={"name": "김", "email": "k@a.kr"}, by="operator")
    sel.set_status(eng, s["seller_id"], "active", by="operator", reason="ok")
    k = sel.issue_key(eng, s["seller_id"], by="operator")["code"]
    pid = prod.save(eng, k, IP, {"name": "제주 감귤", "volume": "5kg", "price": "23900", "origin": "제주",
                                 "sale_url": "https://smartstore.naver.com/x/products/1", "category": "식품>과일>감귤"})["product_id"]  # fmt: skip
    D.save_inputs(eng, k, IP, pid, {"memo": MEMO, "notice_kind": "agri", "notice": NOTICE_AGRI})
    D.generate(eng, k, IP, pid, ai=lambda t: GOOD, ai_name="ai:x")
    D.review(eng, D.submit(eng, k, IP, pid)["current"]["detail_id"], "approved", by="operator")
    prod.review(eng, pid, "approved", by="operator")
    return s["seller_id"], k, pid


def _notice_file(tmp_path, monkeypatch, **kw):
    n = json.loads(SP.NOTICE_FILE.read_text(encoding="utf-8")) | kw
    f = tmp_path / "notice.json"
    f.write_text(json.dumps(n, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setenv("SHOP_NOTICE_FILE", str(f))


def test_committed_notice_is_a_draft_so_formal_is_closed():
    n = json.loads(SP.NOTICE_FILE.read_text(encoding="utf-8"))
    assert n["confirmed"] is False  # 확정 전 — 법률 검토안 문구
    assert "통신판매중개자" in n["texts"]["top"] and "일체" not in json.dumps(n, ensure_ascii=False)
    assert "고지 문구 확정 (shop_notice.json confirmed)" in SP.formal_missing(n)


def test_off_by_default_everything_404(eng):
    from app.main import app

    sid, _k, _pid = _shop(eng)
    c = TestClient(app)
    for path in ("/shop", f"/shop/{sid}", "/.well-known/ucp", "/ucp/platform.json"):
        assert c.get(path).status_code == 404, path
    assert c.post("/ucp/v1/catalog/search", json={"query": "감귤"}).status_code == 404


def test_test_mode_opens_with_banner_notices_and_noindex(eng, monkeypatch):
    from app.main import app

    monkeypatch.setenv("SHOP_PUBLIC", "test")
    sid, _k, pid = _shop(eng)
    c = TestClient(app)
    r = c.get(f"/shop/{sid}")
    assert (
        r.status_code == 200
        and "noindex" in r.headers["x-robots-tag"]
        and "default-src 'none'" in r.headers["content-security-policy"]
    )
    t = r.text
    assert "시험 운영 중" in t and 'content="noindex,nofollow"' in t
    assert "통신판매중개자로서 통신판매의 당사자가 아닙니다" in t  # 첫 화면 상단 고지
    assert t.index("네이버 스마트스토어") < t.index("판매처에서 보기")  # 판매처 이동 전 고지가 버튼 위
    assert "판매자 정보" in t and "— (확인 전)" in t and "3영업일" in t
    assert f'id="p-{pid}"' in t
    assert "1. 품목 또는 명칭" in t and "6-3. 수입 농수축산물" in t  # 고시 원문 번호 칸
    assert sid in c.get("/shop").text
    # 품절이면 빠진다
    from app.services.seller import scm

    scm.set_stock(eng, _k, IP, pid, stock=0, sold_out=True, restock_on=None)
    assert f'id="p-{pid}"' not in c.get(f"/shop/{sid}").text


def test_formal_needs_confirmed_notice_operator_and_verified_consenting_seller(eng, monkeypatch, tmp_path):
    from app.main import app

    monkeypatch.setenv("SHOP_PUBLIC", "1")
    sid, k, _pid = _shop(eng)
    c = TestClient(app)
    assert c.get(f"/shop/{sid}").status_code == 404  # 확정 문구 없음
    _notice_file(tmp_path, monkeypatch, confirmed=True, operator=OPERATOR)
    assert SP.formal_missing() == []
    assert c.get(f"/shop/{sid}").status_code == 404  # 셀러 사업자 정보 없음
    with pytest.raises(sel.SellerError, match="먼저"):
        SP.biz_consent(eng, k, IP, True)
    with pytest.raises(sel.SellerError, match="사업자등록번호"):
        SP.biz_save(eng, k, IP, BIZ | {"biz_no": "123-45-67890"})
    SP.biz_save(eng, k, IP, BIZ)
    SP.biz_consent(eng, k, IP, True)
    assert c.get(f"/shop/{sid}").status_code == 404  # 운영자 확인 전
    with pytest.raises(sel.SellerError):
        SP.biz_verify(eng, sid, ok=True, by="ai")  # 운영자만
    assert c.post(f"/admin/api/seller-biz/{sid}/verify", headers=H, json={"ok": True}).json()["biz"]["verified"]
    r = c.get(f"/shop/{sid}")
    assert r.status_code == 200 and "x-robots-tag" not in r.headers and "시험 운영" not in r.text
    assert (
        "시험운영사는 통신판매중개자로서" in r.text
        and "2026-제주서귀포-0001" in r.text
        and "bizCommPop.do?wrkr_no=2208162517" in r.text
    )
    # 정보를 바꾸면 확인이 풀려 다시 안 보인다
    SP.biz_save(eng, k, IP, BIZ | {"phone": "064-111-1111"})
    assert c.get(f"/shop/{sid}").status_code == 404
    SP.biz_verify(eng, sid, ok=True, by="operator")
    assert c.get(f"/shop/{sid}").status_code == 200
    SP.biz_consent(eng, k, IP, False)  # 동의 철회
    assert c.get(f"/shop/{sid}").status_code == 404
    lst = c.get("/admin/api/seller-biz", headers=H).json()
    assert lst["mode"] == "formal" and lst["sellers"][0]["public"] is False


def test_seller_api_biz_is_own_only(eng, monkeypatch):
    from app.main import app

    monkeypatch.setenv("SHOP_PUBLIC", "test")
    _sid, k, _ = _shop(eng)
    _sid2, k2, _ = _shop(eng, "나농장")
    c = TestClient(app)
    assert c.post("/seller/api/biz/save", json={"key": k, "info": BIZ}).json()["ok"]
    other = c.post("/seller/api/biz", json={"key": k2}).json()["biz"]
    assert other["info"]["trade_name"] == "" and other["mode"] == "test"
    assert c.post("/seller/api/biz/save", json={"key": k, "info": {"x": 1}}).json()["ok"] is False
    assert 'id="ms-h"' in c.get("/seller").text


def _validator():
    from tests.services.ucp.test_ucp_catalog import SEARCH_SCHEMA, Http

    from app.services.ucp import schemas

    return schemas, schemas.prepare(SEARCH_SCHEMA, http=Http())


def test_ucp_catalog_conforms_to_official_schema_and_carries_disclosure(eng, monkeypatch):
    from app.main import app

    monkeypatch.setenv("SHOP_PUBLIC", "test")
    monkeypatch.setenv("SITE_URL", "https://app.example.kr")
    sid, _k, pid = _shop(eng)
    c = TestClient(app)
    prof = c.get("/.well-known/ucp").json()["ucp"]
    assert prof["payment_handlers"] == {} and set(prof["capabilities"]) == {
        "dev.ucp.shopping.catalog.search",
        "dev.ucp.shopping.catalog.lookup",
    }
    assert prof["services"]["dev.ucp.shopping"][0]["endpoint"] == "https://app.example.kr/ucp/v1"
    # 우리 플랫폼 협상 코드로 읽어도 맞게 협상된다
    from app.services.ucp import discovery

    m = discovery.negotiate("app.example.kr", {"ucp": prof})
    assert m.ok and m.transport == "rest" and m.endpoint == "https://app.example.kr/ucp/v1"
    data = c.post("/ucp/v1/catalog/search", json={"query": "감귤"}).json()
    assert [p["id"] for p in data["products"]] == [pid]
    v = data["products"][0]["variants"][0]
    assert v["price"] == {"amount": 23900, "currency": "KRW"} and v["seller"]["name"] == "한라농장"
    assert v["url"].startswith("https://smartstore.naver.com/")
    disc = [m for m in data["messages"] if m.get("presentation") == "disclosure"]
    assert disc and "통신판매중개자" in disc[0]["content"] and disc[0]["path"] == "$.products[0]"
    schemas, prepared = _validator()
    ok, errors = schemas.validate_search_response(data, prepared)
    assert ok, errors
    assert c.post("/ucp/v1/catalog/search", json={"query": "사과"}).json()["products"] == []
    look = c.post("/ucp/v1/catalog/lookup", json={"ids": [pid, "nope"]}).json()
    assert [p["id"] for p in look["products"]] == [pid]
    assert c.post("/ucp/v1/catalog/lookup", json={"ids": []}).status_code == 400
    ok, errors = schemas.validate_search_response(look, prepared)  # 응답 모양은 search 와 같다
    assert ok, errors


def test_platform_profile_published_only_when_asked(monkeypatch):
    from app.main import app

    c = TestClient(app)
    assert c.get("/ucp/platform.json").status_code == 404
    monkeypatch.setenv("UCP_PLATFORM_PUBLIC", "1")
    j = c.get("/ucp/platform.json").json()
    assert j["ucp"]["payment_handlers"] == {}


# ── 고시 원문 대조 (2026-11-25) ──
def test_notice_fields_follow_the_notice_numbering():
    agri = [label for _k, label in D.NOTICE["agri"]["fields"]]
    assert [x.split(".")[0] for x in agri] == ["1", "2", "3", "4", "5", "6-1", "6-2", "6-3", "7", "8", "9", "10"]
    proc = [label for _k, label in D.NOTICE["processed"]["fields"]]
    assert [x.split(".")[0] for x in proc[:6]] == ["1-1", "1-2", "1-3", "1-4", "1-5", "1-6"]
    assert "재확인" in D.NOTICE["processed"]["source"]


def test_old_legal_field_is_carried_to_6_1():
    old = {k: v for k, v in NOTICE_AGRI.items() if k not in ("gmo_gi",)} | {"legal": "지리적표시 제00호"}
    assert D.notice_values("agri", old)["gmo_gi"] == "지리적표시 제00호"
    assert "gmo_gi" not in {m["key"] for m in D.missing_notice("agri", old)}
