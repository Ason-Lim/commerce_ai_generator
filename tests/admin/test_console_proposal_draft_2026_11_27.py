"""2026-11-27 사용자: 'G2B-… 제안서 만들어 주세요'가 분석에서 멈추고 제안서가 안 나옴 (공고 본문에 인원·예산·품목 없음)."""
from __future__ import annotations

from datetime import date

import pytest

from app.admin.b2b import bids as bidstore
from app.admin.b2b import console as C
from app.admin.b2b import evidence, proposal_ai
from app.admin.b2b.bids import BidNotice

TODAY = date(2026, 11, 27)
EMPTY = BidNotice(bid_id="G2B-R26BK01844679-000", title="인천국제공항보안㈜ 27-29년도 복지몰 위탁운영 사업사 선정 공고",
                  agency="인천국제공항보안 주식회사", deadline="2026-12-08 11:00:00", verification="verified_api",
                  summary="복지몰 위탁운영 사업자 선정")
OTHER = BidNotice(bid_id="G2B-R26BK01851097-000", title="[수의시담] 2027년도 홍보기념품 구매 단가계약(타올 핸드워시 세트)",
                  agency="한전KDN(주)", deadline="2026-12-04 11:00:00", verification="verified_api", summary="")


@pytest.fixture
def con(monkeypatch, tmp_path):
    store = {b.bid_id: b for b in (EMPTY, OTHER)}
    monkeypatch.setattr(evidence, "all_candidates", lambda: [])
    monkeypatch.setattr(bidstore, "ensure_seed", lambda: None)
    monkeypatch.setattr(bidstore, "get", lambda k: store.get(k))
    monkeypatch.setattr(bidstore, "list_bids", lambda: list(store.values()))
    monkeypatch.setattr(proposal_ai, "enabled", lambda: False)
    from app.admin.b2b import request_parser
    monkeypatch.setattr(C, "parse_with_llm", lambda text, base=None: request_parser.parse(text, base))   # 외부 AI 없이
    monkeypatch.setattr(C, "DOCS", tmp_path, raising=False)
    monkeypatch.setattr(C.trends, "analyze", lambda today=None: None)
    return C.Console()


def _types(out):
    return [b.get("type") for b in out["blocks"]]


def test_proposal_for_bid_without_conditions_makes_draft(con):
    out = con.run(None, "G2B-R26BK01844679-000 제안서 만들어 주세요.", today=TODAY)
    md = " ".join(b.get("md", "") for b in out["blocks"])
    assert "제안서 초안" in md and "300명 1인당 3만원" in md
    w = next(iter(con.ws.values()))
    assert w.req is not None and w.req.title == EMPTY.title and w.draft_only
    assert "docs" in _types(out) and w.docs                            # 제안서 파일이 실제로 만들어짐


def test_analyze_without_conditions_offers_draft_and_condition_chips(con):
    out = con.run(None, "G2B-R26BK01844679-000 분석해줘", today=TODAY)
    acts = next(b for b in out["blocks"] if b.get("type") == "actions")["items"]
    assert "G2B-R26BK01844679-000 제안서 초안 만들어줘" in acts


def test_condition_after_empty_bid_attaches_to_that_bid(con):
    wid = con.run(None, "G2B-R26BK01844679-000 분석해줘", today=TODAY)
    w = next(iter(con.ws.values()))
    con.run(w.id, "300명 1인당 3만원 생활용품 1종 5영업일 배송", today=TODAY)
    assert w.req and w.req.headcount == 300 and w.req.title == EMPTY.title and wid


def test_new_bid_number_is_not_built_on_previous_bid(con):
    con.run(None, "G2B-R26BK01844679-000 제안서 만들어 주세요", today=TODAY)
    w = next(iter(con.ws.values()))
    con.run(w.id, "G2B-R26BK01851097-000 제안서 만들어줘", today=TODAY)
    assert w.bid_id == "G2B-R26BK01851097-000" and w.req.title == OTHER.title
