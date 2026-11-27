"""2026-11-27 도매몰에 맞는 후보가 없으면 쿠팡·네이버 검색 — 공고명 상품어 먼저, 쿠팡 결과는 저장·외부 AI 전송·가격 기재 안 함."""
from datetime import date, datetime

from app.admin.b2b import evidence, proposal, proposal_ai, sourcing
from app.admin.b2b.models import BidRequirement, CategoryNeed
from app.admin.shared.models import Offer

REQ = BidRequirement(bid_id="T-1", title="2027년 설 명절 임직원 타올 핸드워시 세트 구매", agency="가상공사", headcount=300,
                     budget_per_person=30000, categories=[CategoryNeed(name="생활용품", count=1)])


def _offer(mall, title, price, pid):
    return Offer(mall=mall, mall_label="쿠팡" if mall == "coupang" else "네이버", mall_product_id=pid, title=title,
                 price=price, url=f"https://{mall}.example/{pid}", observed_at=datetime(2026, 11, 27))


class FakeMarkets:
    def __init__(self):
        self.queries = []

    def search(self, q, limit=20):
        self.queries.append(q)
        return [_offer("coupang", "송월 호텔 타올 핸드워시 선물세트", 29000, "c1"),
                _offer("naver", "타올 핸드워시 2종 세트", 31000, "n1")] if "타올" in q else []


def test_title_query_keeps_product_words():
    assert sourcing.title_query(REQ) == "타올 핸드워시 세트"


def test_discover_searches_title_first_and_does_not_store_coupang_when_off(monkeypatch):
    monkeypatch.setenv("B2B_COUPANG_KEEP", "0")
    stored = []
    monkeypatch.setattr(sourcing, "upsert_candidate", stored.append)
    monkeypatch.setattr(sourcing.store, "recent_observations", lambda *a, **k: [])
    m = FakeMarkets()
    found = sourcing.discover(REQ, ["생활용품"], markets=m)
    assert m.queries[0] == "타올 핸드워시 세트"
    assert {c.source for c in found} == {"market_search", "market_search_transient"}
    assert [c.name for c in stored] == ["타올 핸드워시 2종 세트"]              # 네이버만 저장
    cp = next(c for c in found if sourcing.is_transient(c))
    assert cp.supplier == "쿠팡" and any("저장하지 않음" in n for n in cp.notes)


def test_coupang_candidate_not_sent_to_ai_and_price_not_printed_when_off(monkeypatch):
    monkeypatch.setenv("B2B_COUPANG_KEEP", "0")
    monkeypatch.setattr(sourcing, "upsert_candidate", lambda c: None)
    monkeypatch.setattr(sourcing.store, "recent_observations", lambda *a, **k: [])
    found = sourcing.discover(REQ, ["생활용품"], markets=FakeMarkets())
    evs = evidence.evaluate_all(REQ, found, today=date(2026, 11, 27))
    sent = [c["상품"] for c in proposal_ai.facts(REQ, evs, {})["후보 상품 (관측 가격 — 확정 단가 아님)"]]
    assert sent == ["타올 핸드워시 2종 세트"]
    p = proposal.build(REQ, evs, profile={}, mode="external", today=date(2026, 11, 27), ai={"evidence_table": []})
    flat = " ".join(" ".join(r) for s in p.sections for e in s.elements if e.kind == "table" for r in e.rows)
    assert "송월 호텔 타올 핸드워시 선물세트" in flat and "29,000" not in flat


def test_default_keeps_coupang_and_sends_to_ai(monkeypatch):
    """2026-11-27 사용자 결정: 제안 준비용이라 쿠팡 후보도 저장하고 제안서 AI 가 알게."""
    monkeypatch.delenv("B2B_COUPANG_KEEP", raising=False)
    stored = []
    monkeypatch.setattr(sourcing, "upsert_candidate", stored.append)
    monkeypatch.setattr(sourcing.store, "recent_observations", lambda *a, **k: [])
    found = sourcing.discover(REQ, ["생활용품"], markets=FakeMarkets())
    assert {c.source for c in found} == {"market_search"} and len(stored) == 2
    evs = evidence.evaluate_all(REQ, found, today=date(2026, 11, 27))
    sent = {c["상품"]: c["관측 가격"] for c in proposal_ai.facts(REQ, evs, {})["후보 상품 (관측 가격 — 확정 단가 아님)"]}
    assert sent["송월 호텔 타올 핸드워시 선물세트"] == 29000
