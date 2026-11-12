"""B2B 제안서 AI 본문 (2026-11-12) — Claude 작성 → 자동 검사 → GPT 검증 → [확인 필요] 표시 → 제안서에 끼우기."""
from datetime import date

from app.admin.b2b import costing, evidence, proposal, proposal_ai
from app.admin.b2b.models import BidRequirement, CategoryNeed

REQ = BidRequirement(bid_id="KVE-20261101", agency="한국가상에너지공사", headcount=1200, budget_per_person=50000,
                     vat_included=True, categories=[CategoryNeed(name="식품", count=3), CategoryNeed(name="생활용품", count=1)],
                     min_online_price=55000, setup_days=7, delivery_business_days=5, exchange_business_days=7)
BODY = {
    "understanding": "임직원 1,200명에게 1인 50,000원(VAT 포함) 예산으로 4종 중 1개를 선택하게 하는 사업입니다.",
    "strategy": ["관측 소매가와 확정 공급단가를 나눠 검증합니다.", "업계 최초 AI 폐쇄몰로 99% 만족을 보장합니다."],
    "evaluation": [["기술(80)", "기한 준수", "조항별 이행표로 7일 구축·5영업일 배송을 대조"]],
    "differentiation": ["평가위원이 조항별로 대조할 수 있는 이행표를 제출합니다."],
    "operations": ["명부 기반 계정 발급과 1인 1개 선택 제한을 적용합니다."],
    "risks": ["감귤은 관측 기준 미달이라 대체 상품을 준비합니다.", "감점风险을 줄입니다."],
    "evidence_table": [["감귤", "52,000원(11-05)", "검증 전", "[확인 필요: 견적]", "관측 기준 미달"],
                       ["한우", "69,000원(11-05)", "검증 전", "[확인 필요: 견적]", "조건 충족합니다"]],
    "questions": ["예산 상한과 온라인 최저가 하한의 관계를 확인 요청합니다."],
}


def _run(verify=None):
    cost = costing.analyze(REQ, {})
    return proposal_ai.run(REQ, [], {"company_name": "[제안사명]"}, cost, write_call=lambda t: BODY,
                           verify_call=verify, env={"OPENAI_API_KEY": "k"})


def test_auto_checks_flag_invented_claims_han_and_unverified_fulfilment():
    r = _run(verify=lambda t: {"items": []})
    flagged = {(x["field"], x["i"]): x["auto"] for x in r["lines"] if x["auto"]}
    assert any("최초" in a or "99" in a for a in flagged[("strategy", 1)])
    assert flagged[("risks", 1)] == ["한자·중국어 섞임"]
    assert any("충족" in a for a in flagged[("evidence_table", 1)])
    assert ("strategy", 0) not in flagged and ("risks", 0) not in flagged       # 미달·검증 전은 정상
    assert r["body"]["strategy"][1].endswith("]") and "[확인 필요: 검토 의견" in r["body"]["strategy"][1]
    assert r["raw"]["strategy"][1] == BODY["strategy"][1] and r["verified"]


def test_verifier_notes_are_added_and_missing_verifier_is_said():
    lines = proposal_ai.lines_of(BODY)
    k = next(n for n, (f, i, _t) in enumerate(lines) if f == "operations")
    r = _run(verify=lambda t: {"items": [{"i": k, "ok": False, "note": "중복 주문 차단 방식 근거 없음"}]})
    assert "중복 주문 차단 방식 근거 없음" in r["body"]["operations"][0]
    r2 = proposal_ai.run(REQ, [], {}, None, write_call=lambda t: BODY, env={})       # GPT 키 없음
    assert r2["verified"] is False


def test_ai_body_is_placed_into_the_proposal_and_chapters_renumbered():
    r = _run(verify=lambda t: {"items": []})
    p = proposal.build(REQ, [], profile={}, cost=costing.analyze(REQ, {}), mode="external", today=date(2026, 11, 12),
                       ai=r["body"])
    ids = [s.id for s in p.sections]
    assert ids.index("strategy") == ids.index("understanding") + 1 and "evaluation" in ids and "questions" in ids
    numbered = [s.title for s in p.sections if s.title[0].isdigit()]
    assert [t.split(".")[0] for t in numbered] == [str(i) for i in range(1, len(numbered) + 1)]
    und = next(s for s in p.sections if s.id == "understanding")
    assert any(e.kind == "para" and e.text.startswith("임직원 1,200명") for e in und.elements)
    assert p.todo_count >= 3                                                    # 검토 의견 문장은 노란 표시로


def test_enabled_needs_claude_key_and_can_be_turned_off():
    assert proposal_ai.enabled({"ANTHROPIC_API_KEY": "k"}) and not proposal_ai.enabled({"ANTHROPIC_API_KEY": "k", "B2B_PROPOSAL_AI": "0"})
    assert not proposal_ai.enabled({})
