"""integrated_system tests/test_b2b.py — 관리자 백엔드(/admin/b2b)로 옮긴 뒤에도 같은 동작인지 (경로만 바뀜)."""
from datetime import date

from fastapi.testclient import TestClient

from app.admin.b2b import costing, evidence, proposal
from app.admin.b2b.models import BidRequirement, Candidate, CategoryNeed
from app.admin.b2b.request_parser import parse

TODAY = date(2026, 10, 16)
IBK = ("IBK서비스-2026008 예정 인원 2,090명, 1인당 44,000원(VAT 포함), 총예산 91,960,000원. "
       "식품 2종·건강기능식품 2종·생활용품 2종 구성, 온라인 기준 최저가 40,000원 이상. "
       "계약일로부터 5일 이내 폐쇄몰 구축·등재, 직원 선택일부터 5영업일 이내 국내 지정 주소 배송, "
       "반품 접수일부터 7영업일 이내 교환 배송.")


def test_parser_extracts_with_quotes():
    r = parse(IBK)
    assert (r.headcount, r.budget_per_person, r.min_online_price) == (2090, 44000, 40000)
    assert (r.delivery_business_days, r.exchange_business_days, r.setup_days) == (5, 7, 5)
    assert [c.name for c in r.categories] == ["식품", "건강기능식품", "생활용품"]
    assert all(p.quote for p in r.provenance)


def _full(**kw):
    base = dict(candidate_id="t", supplier="s", name="참기름 선물세트", option="300ml 2병", category="식품",
                online_min_price_verified=45000, observed_date=TODAY, unit_price_quote=36000,
                quote_valid_until=date(2026, 12, 31), packaging_cost=1000, shipping_cost=3000,
                delivery_days=3, exchange_days=5, stock_status="confirmed_available", quantity_available=5000)
    base.update(kw)
    return Candidate(**base)


def test_unknown_is_never_eligible():
    req = parse(IBK)
    assert evidence.evaluate(_full(), req, TODAY).decision == "ELIGIBLE"
    assert evidence.evaluate(_full(shipping_cost=None), req, TODAY).decision == "HOLD"
    assert evidence.evaluate(_full(delivery_days=9), req, TODAY).decision == "EXCLUDED"
    assert evidence.evaluate(_full(category="생활용품", name="x"), parse("식품 2종"), TODAY).decision == "EXCLUDED"


def test_real_bundle_items_all_hold_or_excluded():
    evs = evidence.evaluate_all(parse(IBK), evidence.bundle_to_candidates(
        __import__("json").loads((evidence.DATA / "evidence_bundle_v2.json").read_text())), TODAY)
    assert evs and all(e.decision != "ELIGIBLE" for e in evs)


def test_cost_unknown_is_not_zero():
    req = BidRequirement(budget_per_person=44000, headcount=2090)
    a = costing.analyze(req, {"supply": 36000})
    assert a.residual is None and len(a.unknown) == 8 and a.status == "산출 불가"
    b = costing.analyze(req, dict(supply=36000, packaging=1500, warehouse=0, shipping=3500, return_reserve=0, ops_cs=800,
                                  admin_overhead=0, other=0), mall_build_total=3_000_000)
    assert b.residual == 44000 - 36000 - 1500 - 3500 - 800 - round(3_000_000 / 2090)


def test_profit_uses_net_of_vat_and_marks_assumptions():
    """2026-11-11: 이윤·일반관리비·택배·물류창고 → 1인 이익·이익률·총 이익. 협력사가 없어 가정값이면 '추정'."""
    req = BidRequirement(budget_per_person=55000, vat_included=True, headcount=1000)
    c = costing.analyze(req, {"supply": {"amount": 32000, "basis": "견적"}, "packaging": {"amount": 1000, "basis": "견적"},
                              "warehouse": {"amount": 700, "basis": "가정"}, "shipping": {"amount": 3500, "basis": "가정"},
                              "return_reserve": 300, "ops_cs": 800, "other": 0}, mall_build_total=2_000_000,
                        admin_rate=0.05, target_margin_rate=0.10)
    assert c.net_budget == 50000 and c.lines[-2].amount == 2500           # 관리비 = 공급가액 5%
    assert c.residual == 50000 - 32000 - 1000 - 700 - 3500 - 300 - 800 - 2000 - 2500 - 0 == 7200
    assert c.margin_rate == 0.144 and c.total_profit == 7_200_000 and c.status == "추정"
    assert c.assumed == ["물류창고 (입고·보관·피킹·출고 작업)", "택배 (도서산간 포함)"]
    assert c.max_supply_for_target == 45000 - (50000 - 32000 - 7200) == 34200     # 이익률 10%를 남기는 최대 매입가
    sure = costing.analyze(req, {k: {"amount": 0, "basis": "계약"} for k, _ in costing.COMPONENTS})
    assert sure.status == "확정"


def test_console_reads_warehouse_courier_overhead_and_target_margin():
    from app.admin.b2b.console import Console, Workspace

    w = Workspace(id="t")
    w.req = BidRequirement(budget_per_person=55000, vat_included=True, headcount=1000)
    w.evals = []
    Console()._cost(w, "매입가 32000(견적) 포장 1000 창고 700(가정) 택배 3500(가정) 반품 300 운영 800 기타 0 관리비 5% 이윤 10% 구축비 200만원", None)
    assert w.cost.residual == 7200 and w.cost.status == "추정" and w.cost.max_supply_for_target == 34200


def test_external_proposal_has_no_internal_appendix():
    req = parse(IBK)
    evs = [evidence.evaluate(_full(), req, TODAY)]
    cost = costing.analyze(req, {"supply": 36000})
    ext = proposal.build(req, evs, profile={}, cost=cost, mode="external", today=TODAY)
    html = proposal.to_html(ext)
    assert not any(s.internal_only for s in ext.sections)
    assert "36,000" not in html            # 원가 비노출
    assert "[확인 필요: 제안사명]" in html  # 미확인은 지어내지 않음
    internal = proposal.build(req, evs, profile={}, cost=cost, mode="internal", today=TODAY)
    assert any(s.internal_only for s in internal.sections)


def test_docx_export(tmp_path):
    req = parse(IBK)
    p = proposal.build(req, [], profile={}, mode="external", today=TODAY)
    out = proposal.to_docx(p, tmp_path / "p.docx")
    assert out.stat().st_size > 5000


def test_console_requires_token_and_runs(admin_client):
    c = admin_client
    assert c.post("/admin/b2b/api/run", json={"prompt": "공고 목록"}).status_code == 401
    h = {"X-Access-Token": "test-token"}
    r = c.post("/admin/b2b/api/run", json={"prompt": "IBK서비스-2026008 분석해줘", "today": "2026-10-16"}, headers=h).json()
    assert r["action"] == "analyze" and any(b["type"] == "candidates" for b in r["blocks"])
    r2 = c.post("/admin/b2b/api/run", json={"workspace_id": r["workspace_id"], "prompt": "제안서 작성해줘"}, headers=h).json()
    docs = next(b for b in r2["blocks"] if b["type"] == "docs")["items"]
    assert c.get(docs[0]["href"], headers=h).status_code == 200
    assert c.get("/admin/b2b/files/..%2Fcore.sqlite3", headers=h).status_code == 404


def test_polish_rejects_new_numbers(monkeypatch):
    class Fake:
        enabled = True

        def chat_json(self, *a, **k):
            return {"lines": ["2,090명 대상, 업계 1위 10년 실적"]}
    monkeypatch.setattr(proposal, "LLMClient", lambda: Fake())
    assert proposal._polish(["2,090명 대상"]) == ["2,090명 대상"]


def test_category_need_model():
    assert CategoryNeed(name="식품", count=2).count == 2


def test_candidate_records_evidence_coverage():
    req = parse(IBK)
    ev = evidence.evaluate(_full(), req, TODAY)
    assert ev.candidate.evidence_coverage is not None
    assert ev.candidate.rankability in ("DETERMINATE", "INDETERMINATE", "UNKNOWN")
    hold = evidence.evaluate(_full(shipping_cost=None), req, TODAY)
    assert hold.candidate.missing_terms


def test_proposal_files_use_pretendard(tmp_path):
    """2026-11-12: 제안서 글꼴 Pretendard (SIL OFL — 상업 사용 가능)."""
    import re
    import zipfile

    from app.admin.b2b import proposal_templates

    req = parse(IBK)
    p = proposal.build(req, [evidence.evaluate(_full(), req, TODAY)], profile={}, mode="external", today=TODAY)
    h = zipfile.ZipFile(proposal.to_hwpx(p, tmp_path / "p.hwpx")).read("Contents/header.xml").decode()
    assert set(re.findall(r'face="([^"]+)"', h)) == {"Pretendard"}
    d = zipfile.ZipFile(proposal.to_docx(p, tmp_path / "p.docx")).read("word/styles.xml").decode()
    assert "Pretendard" in d and "Malgun" not in d
    assert proposal_templates.Template.model_fields["font_office"].default == "Pretendard"
