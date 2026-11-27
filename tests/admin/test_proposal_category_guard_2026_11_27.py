"""2026-11-27 버그: '타올 핸드워시 세트' 공고 제안서의 상품별 가격 근거표에 사과배·한우 우족·황새치·가다랑어가 들어감.
원인: 공고 품목 구성이 비어 있으면 카테고리 판정을 건너뛰어 식품 묶음 후보가 모두 HOLD 로 AI 입력에 들어감."""
from datetime import date

from app.admin.b2b import evidence, proposal, proposal_ai
from app.admin.b2b.models import BidRequirement, Candidate, CategoryNeed

TOWEL = BidRequirement(bid_id="T-1", title="타올 핸드워시 세트", agency="가상공사", headcount=300, budget_per_person=50000,
                       vat_included=None)
FOOD = [Candidate(candidate_id=f"f{i}", supplier="s", name=n, category="식품", observed_price=p, price_kind="public_retail",
                  observed_date=date(2026, 10, 12))
        for i, (n, p) in enumerate([("이롬팜스 사과배 혼합 선물세트 1호", 49900), ("한우 우족선물세트 건강53호", 34900),
                                    ("황새치 뱃살 중", 32000), ("가다랑어 로인", 19000)])]
TOWEL_C = Candidate(candidate_id="t1", supplier="s", name="송월 호텔타올 핸드워시 세트", category="생활용품",
                    observed_price=29000, price_kind="public_retail", observed_date=date(2026, 11, 20))
AI_BODY = {"evidence_table": [[c.name, f"{c.observed_price:,}원", "검증 전", "[확인 필요: 견적]", "HOLD"] for c in FOOD]}


def _table(p):
    sec = next(s for s in p.sections if s.id == "products")
    return next(e for e in sec.elements if e.kind == "table" and e.headers and e.headers[0] == "후보 상품")


def test_empty_categories_never_make_candidates_eligible():
    evs = evidence.evaluate_all(TOWEL, FOOD, today=date(2026, 11, 27))
    assert all(e.decision != "ELIGIBLE" for e in evs)
    assert all(any(x.label == "품목 구분" and x.status == "UNKNOWN" for x in e.checks) for e in evs)


def test_facts_drop_candidates_when_bid_categories_missing():
    evs = evidence.evaluate_all(TOWEL, FOOD, today=date(2026, 11, 27))
    fx = proposal_ai.facts(TOWEL, evs, {})
    assert fx["후보 상품 (관측 가격 — 확정 단가 아님)"] == [] and "다른 품목" in fx["후보 상품 안내"]


def test_facts_keep_only_matching_category():
    req = TOWEL.model_copy(update={"categories": [CategoryNeed(name="생활용품", count=2)]})
    evs = evidence.evaluate_all(req, FOOD + [TOWEL_C], today=date(2026, 11, 27))
    names = [c["상품"] for c in proposal_ai.facts(req, evs, {})["후보 상품 (관측 가격 — 확정 단가 아님)"]]
    assert names == ["송월 호텔타올 핸드워시 세트"]


def test_ai_evidence_rows_of_other_items_are_replaced():
    evs = evidence.evaluate_all(TOWEL, FOOD, today=date(2026, 11, 27))
    p = proposal.build(TOWEL, evs, profile={}, mode="external", today=date(2026, 11, 27), ai=AI_BODY)
    t = _table(p)
    flat = " ".join(" ".join(r) for r in t.rows)
    assert not any(w in flat for w in ("사과배", "우족", "황새치", "가다랑어"))
    assert len(t.rows) == 1 and "후보 발굴 중" in flat


def test_ai_evidence_rows_of_matching_items_stay():
    req = TOWEL.model_copy(update={"categories": [CategoryNeed(name="생활용품", count=2)]})
    evs = evidence.evaluate_all(req, FOOD + [TOWEL_C], today=date(2026, 11, 27))
    body = {"evidence_table": AI_BODY["evidence_table"] + [[TOWEL_C.name, "29,000원", "검증 전", "[확인 필요: 견적]", "HOLD"]]}
    t = _table(proposal.build(req, evs, profile={}, mode="external", today=date(2026, 11, 27), ai=body))
    assert [r[0] for r in t.rows] == [TOWEL_C.name]


# ── 2026-11-27 GPT 검토(보완): 가격 근거표는 코드가 후보 필드로 만든다 — AI 가 쓴 가격·관측일·판정은 통과시키지 않음 ──
def test_ai_evidence_price_and_verdict_are_not_trusted():
    req = TOWEL.model_copy(update={"categories": [CategoryNeed(name="생활용품", count=2)]})
    evs = evidence.evaluate_all(req, [TOWEL_C], today=date(2026, 11, 27))
    body = {"evidence_table": [[TOWEL_C.name, "9,900원 (소매, 2026-11-01)", "최저가 확인됨", "8,000원", "ELIGIBLE: 확정"]]}
    row = _table(proposal.build(req, evs, profile={}, mode="external", today=date(2026, 11, 27), ai=body)).rows[0]
    assert row[0] == TOWEL_C.name
    assert row[1] == "29,000원 (소매, 2026-11-20)"               # 후보 근거 필드
    assert "9,900" not in " ".join(row) and "8,000" not in " ".join(row) and "확정" not in row[4]
    assert row[3] == "[확인 필요: 견적]" and row[4].startswith("HOLD")


def test_coupang_kept_price_only_in_internal(monkeypatch):
    c = TOWEL_C.model_copy(update={"supplier": "쿠팡", "source": "market_search", "candidate_id": "cp1"})
    req = TOWEL.model_copy(update={"categories": [CategoryNeed(name="생활용품", count=2)]})
    evs = evidence.evaluate_all(req, [c], today=date(2026, 11, 27))
    ext = _table(proposal.build(req, evs, profile={}, mode="external", today=date(2026, 11, 27), ai={})).rows[0]
    inn = _table(proposal.build(req, evs, profile={}, mode="internal", today=date(2026, 11, 27), ai={})).rows[0]
    assert "제출 시점 판매처 화면 증빙" in ext[1] and "29,000" not in ext[1]
    assert inn[1].startswith("29,000원")
