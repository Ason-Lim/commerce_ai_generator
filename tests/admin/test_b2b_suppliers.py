"""B2B 콘솔 '공급사 리스트업' (2026-11-04): 이전에는 공고 분석으로 가서 '분석할 공고나 조건을 찾지 못했어요'로 끝났다."""
from __future__ import annotations

import json
import re
from datetime import date

from app.admin.b2b import console, evidence, suppliers
from app.admin.b2b.models import Candidate


def _route(p: str) -> str:
    return next((a for a, rx in console.ROUTES if re.search(rx, p, re.IGNORECASE)), "analyze")


def test_supplier_prompts_route_to_the_supplier_list_and_others_stay():
    for p in ("공영홈쇼핑 기념품에 제공할 수 있는 공급사를 리스트업 해주세요", "도매 공급업체 리스트업을 해주세요",
              "공영홈쇼핑 기념품 용역을 위해 건강식품 도매업체를 조사해"):
        assert _route(p) == "suppliers", p
    assert _route("공급사에 보낼 견적 요청서 만들어줘") == "rfq"
    assert _route("제안서 작성해줘") == "proposal" and _route("후보 더 찾아줘") == "discover"
    assert _route("입찰중 공고 보여줘") == "list_bids" and _route("G2B-R26BK01790508-000 분석해줘") == "analyze"


def _c(cid, supplier, name, quote=None, sample=False):
    return Candidate(candidate_id=cid, supplier=supplier, name=name, unit_price_quote=quote, is_sample=sample,
                     observed_date=date(2026, 11, 1))


def test_rows_group_by_supplier_quoted_first_and_skip_samples():
    rows = suppliers.supplier_rows([
        _c("1", "농민연합", "비가림 황금향"), _c("2", "농민연합", "비가림 황금향"), _c("3", "농민연합", "사과 선물세트"),
        _c("4", "홍삼나라", "6년근 홍삼정 선물세트", quote=32000), _c("5", "예시몰", "예시 상품", sample=True),
        _c("6", "미상", "참기름")])
    assert [r["supplier"] for r in rows] == ["홍삼나라", "농민연합"]
    assert rows[0]["basis"] == "견적 단가 있음" and rows[1]["basis"] == "공개 판매가 관측만"
    assert rows[1]["products"] == 3 and rows[1]["examples"] == ["비가림 황금향", "사과 선물세트"]
    assert [r["supplier"] for r in suppliers.supplier_rows([_c("4", "홍삼나라", "홍삼정"), _c("1", "농민연합", "사과")],
                                                           "건강기능식품")] == ["홍삼나라"]


def test_category_words():
    assert suppliers.category_from("건강식품 도매업체를 조사해") == "건강기능식품"
    assert suppliers.category_from("식품 공급사 보여줘") == "식품"
    assert suppliers.category_from("공급사 리스트업") is None


def test_real_bundle_has_suppliers():
    cands = evidence.bundle_to_candidates(json.loads((evidence.DATA / "evidence_bundle_v2.json").read_text()))
    rows = suppliers.supplier_rows(cands)
    assert rows and all(r["supplier"] != "미상" for r in rows)
