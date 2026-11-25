"""스마트스토어 '상품 조회' CSV 그대로 올리기 (2026-11-25) — 실제 셀러 파일과 같은 칸(머리줄)의 가짜 자료로 시험.
실제 파일은 저장소에 넣지 않는다."""

from __future__ import annotations

import os

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

os.environ.setdefault("CORPMALL_KEY", Fernet.generate_key().decode())

from app.services.corpmall import store as corp  # noqa: E402
from app.services.seller import catalog, scm  # noqa: E402
from app.services.seller import products as prod  # noqa: E402
from app.services.seller import store as sel  # noqa: E402

IP = "1.1.1.1"
HEAD = "﻿그룹상품번호,상품번호(스마트스토어),판매자상품코드,상품명,채널,스마트스토어전용 상품명,쇼핑윈도전용 상품명,판매상태,전시상태,재고수량,판매가,할인가,판매자할인,네이버부담할인,옵션,추가상품,상품속성,최소구매수량,최대구매수량,복수구매할인,포인트(상품구매),포인트(상품구매/관리자),포인트(텍스트리뷰 작성),포인트(포토/동영상리뷰 작성),포인트(한달사용 텍스트리뷰 작성),포인트(한달사용 포토/동영상리뷰 작성),포인트(알림받기동의고객 리뷰 작성),무이자할부,사은품,풀필먼트사,배송속성,기준시간,묶음배송,배송비유형,배송비결제방식,기본배송비,반품배송비,교환배송비,반품안심케어,네이버쇼핑 등록(스마트스토어),네이버쇼핑 등록(쇼핑윈도),네이버쇼핑상품번호(스마트스토어),네이버쇼핑상품번호(쇼핑윈도),네이버쇼핑상품번호(수급윈도),표준그룹EP ID(스마트스토어),표준그룹EP ID(쇼핑윈도),전용상품 (스마트스토어),전용상품 (쇼핑윈도),대분류,중분류,소분류,세분류,제조사명,브랜드명,브랜드ID,모델명,브랜드인증,자체제작,맞춤제작,인증정보,판매자바코드,판매자 내부코드1,판매자 내부코드2,대표이미지 URL,판매시작일,판매종료일,모바일 미리보기 생성일,결제여부,상품등록일,최종수정일,구독유형"
COLS = HEAD.split(",")


def row(**kw):
    base = {"상품번호(스마트스토어)": "1001", "상품명": "가짜 우드 바니쉬 1L", "채널": "스마트스토어", "판매상태": "판매중",
            "전시상태": "전시중", "재고수량": "30", "판매가": "35000", "할인가": "31500", "옵션": "N",
            "배송비유형": "조건부 무료", "기본배송비": "3000", "대분류": "생활/건강", "중분류": "공구", "소분류": "페인트",
            "세분류": "수성페인트", "제조사명": "가짜제조", "브랜드명": "가짜", "대표이미지 URL": "https://example.com/a.png"}  # fmt: skip
    base.update(kw)
    return ",".join(base.get(c, "") for c in COLS)


def csv_of(*rows):
    return HEAD + "\n" + "\n".join(rows) + "\n"


@pytest.fixture
def eng():
    corp.reset_limits()
    e = catalog.engine()
    with e.begin() as c:
        for t in (catalog.t_unit, catalog.t_group, catalog.t_base, scm.t_stock, prod.t_listing, prod.t_product,
                  sel.t_event, sel.t_key, sel.t_seller):  # fmt: skip
            c.execute(t.delete())
    return e


def _seller(eng, channel="naver"):
    s = sel.create_seller(eng, name="가공방", kind="direct", contact={"name": "김", "email": "k@a.kr"}, by="operator")
    sel.set_status(eng, s["seller_id"], "active", by="operator", reason="ok")
    k = sel.issue_key(eng, s["seller_id"], by="operator")["code"]
    if channel != "manual":
        catalog.set_base_channel(eng, k, IP, channel)
    return s, k


def test_detects_and_converts_real_header():
    assert catalog.is_naver_export(COLS)
    rows, notes = catalog.naver_export_rows(csv_of(
        row(),
        row(**{"상품번호(스마트스토어)": "1002", "상품명": "가짜 바니쉬 .3.78L", "옵션": "Y", "할인가": ""}),
        row(**{"상품번호(스마트스토어)": "1003", "상품명": "가짜 오일 500ml", "판매상태": "판매중지"}),
        row(**{"상품번호(스마트스토어)": "1004", "상품명": "가짜 페인트 1kg", "판매상태": "품절", "재고수량": "5"}),
    ))  # fmt: skip
    n = {r["ext_no"]: catalog.normalize(r) for r in rows}
    assert n["1001"]["price"] == 31500 and n["1001"]["list_price"] == 35000 and n["1001"]["volume"] == "1L"
    assert (
        n["1001"]["category"] == ["생활/건강", "공구", "페인트", "수성페인트"]
        and n["1001"]["ship"]["type"] == "conditional"
    )
    assert n["1002"]["price"] == 35000 and n["1002"]["volume"] == "3.78L"  # 할인가 없으면 판매가
    assert n["1003"]["on"] is False and n["1004"]["stock"] == 0
    assert notes["option_products"] == ["1002"] and notes["off"] == 2


def test_upload_as_is_through_sync_route(eng):
    from app.main import app

    _s, k = _seller(eng)
    c = TestClient(app)
    j = c.post("/seller/api/sync", json={"key": k, "channel": "naver", "csv": "﻿" + csv_of(row(), row(**{"상품번호(스마트스토어)": "1002", "옵션": "Y"})), "full": True}).json()  # fmt: skip
    assert j["ok"] and j["added"] == 2 and j["source"] == "스마트스토어 상품 조회 파일"
    assert any("옵션" in x for x in j["notes"]) and any("원산지" in x for x in j["notes"])
    mine = prod.list_mine(eng, k, IP)
    assert {m["status"] for m in mine} == {"pending"}  # 검수 대기
    # 다시 올리면 바뀐 가격만 바로 반영
    j = c.post("/seller/api/sync", json={"key": k, "channel": "naver", "csv": csv_of(row(**{"할인가": "29900"}), row(**{"상품번호(스마트스토어)": "1002", "옵션": "Y"})), "full": True}).json()  # fmt: skip
    assert j["fast"] == 1 and j["unchanged"] == 1


def test_naver_file_needs_naver_base(eng):
    _s, k = _seller(eng, channel="coupang")
    with pytest.raises(sel.SellerError, match="네이버"):
        catalog.import_std_csv(eng, k, IP, "coupang", csv_of(row()))


# ── 몰 주소 (관리자 셀러 목록 '몰' 칸, 2026-11-25) ──
def test_store_url_fills_product_links_and_shows_in_admin_list(eng):
    from app.main import app

    catalog.t_store.create(eng, checkfirst=True)
    with eng.begin() as c:
        c.execute(catalog.t_store.delete())
    s, k = _seller(eng)
    catalog.import_std_csv(eng, k, IP, "naver", csv_of(row(), row(**{"상품번호(스마트스토어)": "1002"})))
    assert {p["sale_url"] for p in prod.list_mine(eng, k, IP)} == {""}
    with pytest.raises(sel.SellerError):
        catalog.set_store_url(eng, s["seller_id"], "https://smartstore.naver.com/renner", by="ai")
    with pytest.raises(sel.SellerError, match="https"):
        catalog.set_store_url(eng, s["seller_id"], "http://x.kr", by="operator")
    c = TestClient(app)
    H = {"X-Access-Token": "test-token"}
    r = c.post(
        f"/admin/api/seller/{s['seller_id']}/store", headers=H, json={"url": "https://smartstore.naver.com/renner"}
    ).json()
    assert r["ok"] and r["filled"] == 2
    assert {p["sale_url"] for p in prod.list_mine(eng, k, IP)} == {
        "https://smartstore.naver.com/renner/products/1001",
        "https://smartstore.naver.com/renner/products/1002",
    }
    row_ = next(x for x in c.get("/admin/api/seller", headers=H).json()["sellers"] if x["seller_id"] == s["seller_id"])
    assert row_["store_url"] == "https://smartstore.naver.com/renner" and row_["shop_preview"].endswith("/shop")
    # 이후 CSV 는 처음부터 링크가 들어감
    j = catalog.import_std_csv(eng, k, IP, "naver", csv_of(row(), row(**{"상품번호(스마트스토어)": "1003"})))
    assert not any("몰 주소" in x for x in j["notes"])
    assert "https://smartstore.naver.com/renner/products/1003" in {p["sale_url"] for p in prod.list_mine(eng, k, IP)}
    assert catalog.store_slug("https://brand.naver.com/abc/") == "abc" and catalog.store_slug("https://x.kr") == ""


# ── 샘플 화면에서 찾은 것 (2026-11-25): 사진 · 용량 두 번 · 인증 N ──
def test_images_prefilled_and_cert_flag_ignored(eng):
    from app.services.seller import detail_page

    detail_page.meta.create_all(eng)
    with eng.begin() as c:
        c.execute(detail_page.t_detail.delete())
    _s, k = _seller(eng)
    csv = csv_of(
        row(**{"인증정보": "N", "대표이미지 URL": "http://shop1.phinf.naver.net/a/b.png"}),
        row(**{"상품번호(스마트스토어)": "1002", "대표이미지 URL": "http://example.com/x.png"}),
    )
    j = catalog.import_std_csv(eng, k, IP, "naver", csv)
    assert j["prefilled"] == 1
    assert all(not p["declared"].get("certs") for p in prod.list_mine(eng, k, IP))  # 'N' 은 인증이 아님
    units = {u["ext_no"]: pid for pid, u in catalog.units_of(eng, _s["seller_id"]).items()}
    cur = detail_page.get(eng, k, IP, units["1001"])["current"]["inputs"]
    assert cur["images"][0]["url"] == "https://shop-phinf.pstatic.net/a/b.png" and cur["image_ok"] is False
    assert detail_page.with_volume("가짜 우드 바니쉬 1L", "1L") == "가짜 우드 바니쉬 1L"
    assert detail_page.with_volume("레너페인트 1kg", "1 KG") == "레너페인트 1kg"
    assert detail_page.with_volume("감귤", "5kg") == "감귤 5kg"
    html = detail_page.shop_page(eng, _s["seller_id"], banner=None, sample=True)
    assert "가짜 우드 바니쉬 1L 1L" not in html and "shop-phinf.pstatic.net/a/b.png" in html
