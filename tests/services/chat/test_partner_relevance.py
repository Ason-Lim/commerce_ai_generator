"""업체 상품 관련성 (2026-11-03 p36): 상품 낱말을 모두 담아야 하고, 꾸밈 낱말(용도·원산지·포장·때)은 요구하지 않는다.
실제 MCP 호출에서 '한우 등심' 검색에 '한우 양지 국거리'·'한우 찜갈비'가 들어온 것을 계기로."""
from __future__ import annotations

import csv

import pytest

from app.domain.commerce.requests import SearchRequest
from app.services.commerce.search import partner_match, partner_terms_required, search_products
from tests.services.chat.conftest import FakeShopping


@pytest.mark.parametrize("title, terms, ok", [
    ("한우 1+등급 양지 국거리 500g", ["한우", "등심"], False),
    ("한우 1++등급 찜갈비 1kg", ["한우", "등심"], False),
    ("한우 1++등급 등심 구이용 300g", ["한우", "등심"], True),
    ("국산 삼겹살 500g", ["국산", "삼겹살", "구이용"], True),       # 꾸밈 낱말(국산·구이용)은 필수 아님
    ("국산 목살 500g", ["국산", "삼겹살", "구이용"], False),
    ("명절 한우 세트 1kg", ["명절", "한우", "세트"], True),
    ("부사 사과 5kg", ["사과"], True),
    ("배 신고 7.5kg", ["사과"], False),
])
def test_partner_match(title, terms, ok):
    assert partner_match(title, terms) is ok


def test_all_qualifier_terms_fall_back_to_the_terms_themselves():
    assert partner_terms_required(["선물세트"]) == ["선물세트"]
    assert partner_terms_required(["국산", "삼겹살", "구이용"]) == ["삼겹살"]


def test_search_keeps_only_matching_partner_products(tmp_path, monkeypatch):
    monkeypatch.setenv("PARTNER_PREVIEW", "1")
    monkeypatch.setenv("PARTNER_DATA_DIR", str(tmp_path))
    with (tmp_path / "permissions.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["업체", "상태"])
        w.writeheader()
        w.writerow({"업체": "한우이츠", "상태": "요청함"})
    (tmp_path / "hanwooeats").mkdir()
    with (tmp_path / "hanwooeats" / "products_sample.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["상품ID", "상품명", "품목", "품종", "중량(g)", "수량", "판매가", "정가", "배송비", "당도(Brix)", "산지",
                    "등급", "상품URL", "이미지URL", "재고상태", "가격기준일시", "비고"])
        for pid, name, kind, price in (("S1", "(예시) 한우 1+등급 양지 국거리 500g", "양지", 32900),
                                       ("S2", "(예시) 한우 1++등급 등심 구이용 300g", "등심", 46900),
                                       ("S3", "(예시) 한우 1++등급 찜갈비 1kg", "갈비", 89000)):
            w.writerow([pid, name, "소", kind, "", "", price, "", "0", "", "국내산", "1++", "https://hanwooeats.com/", "",
                        "판매중", "2026-11-02 09:00", "예시"])
    coupang = [{"product_name": "농협안심한우 등심 1등급 300g", "price": 39000,
                "product_url": "https://www.coupang.com/vp/products/1", "platform_name": "쿠팡", "is_coupang": True}]
    res = search_products(SearchRequest(text="한우 등심 추천"), shopping=FakeShopping(items=coupang))
    partner = sorted(i.product.title for i in res.items if i.offer.link_type == "partner")
    assert partner == ["(예시) 한우 1++등급 등심 구이용 300g"]


@pytest.mark.parametrize("title, terms, ok", [
    ("국산 삼겹살 500g", ["국산", "삼겹살"], True),
    ("국내산 삼겹살 500g", ["국산", "삼겹살"], True),             # 같은 뜻의 표기
    ("삼겹살 500g", ["국산", "삼겹살"], False),                   # p37: 원산지 표기가 없으면 조건을 확인할 수 없음
    ("수입 삼겹살 500g", ["국산", "삼겹살"], False),
    ("한우 등심 냉동 300g", ["냉장", "한우", "등심"], False),      # 보관 상태가 다름
    ("한우 등심 냉장 300g", ["냉장", "한우", "등심"], True),
    ("명절 한우 세트", ["명절", "한우", "세트"], True),            # 꾸밈 낱말(때·포장)은 여전히 필수 아님
])
def test_origin_and_storage_words_are_conditions(title, terms, ok):
    assert partner_match(title, terms) is ok
