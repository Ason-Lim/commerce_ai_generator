"""1인 비용·이익 구조 — '미확인은 0원이 아니다'.

1인 예산(VAT 포함이면 ÷1.1 한 공급가액) − 매입 − 포장 − 물류창고 − 택배 − 교환·반품 예비 − 운영·CS − 폐쇄몰 구축비 배분
− 일반관리비 − 기타 = 1인 이익(이윤) → 이익률 · 총 이익(× 인원)

* 모든 항목이 채워져야 이익을 계산한다. 하나라도 비면 '산출 불가'.
* 항목마다 근거를 남긴다: 견적·계약(확인됨) / 가정 / 입력값. 전부 견적·계약일 때만 '확정', 아니면 '추정'.
  (2026-11-11: 협력 물류창고·택배사가 아직 없어 택배·창고비는 '가정'으로 넣고 추정으로 계산하는 일이 많다)
* 목표 이익률을 주면 '그 이익을 남기려면 매입가가 얼마 이하여야 하는가'(최대 매입가)를 계산한다 — 소싱 기준.
* 공개 판매가를 매입가로 '가정'한 시나리오는 별도로, 가정임을 명시해서만 보여준다.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.admin.b2b.models import BidRequirement, Candidate

COMPONENTS = [
    ("supply", "상품 매입가 (공급사 인도 기준)"),
    ("packaging", "추가 포장"),
    ("warehouse", "물류창고 (입고·보관·피킹·출고 작업)"),
    ("shipping", "택배 (도서산간 포함)"),
    ("return_reserve", "교환·반품 예비비"),
    ("ops_cs", "운영·CS·하자 대응"),
    ("mall_build", "폐쇄몰 구축비 배분"),
    ("admin_overhead", "일반관리비"),
    ("other", "기타 확인 비용"),
]
CONFIRMED = {"견적", "계약"}


class CostLine(BaseModel):
    key: str
    label: str
    amount: int | None = None
    basis: str = "미확인"


class CostAnalysis(BaseModel):
    budget_per_person: int | None
    vat_included: bool | None
    net_budget: int | None = None          # VAT 를 뺀 1인 공급가액 (비용·이익은 이 기준)
    lines: list[CostLine]
    known_total: int
    unknown: list[str]
    residual: int | None                   # 1인 이익(이윤) — 모든 항목이 채워졌을 때만
    margin_rate: float | None = None       # 이익 ÷ 공급가액
    total_profit: int | None = None        # 1인 이익 × 인원
    status: str = "산출 불가"              # 확정 | 추정 | 산출 불가
    assumed: list[str] = Field(default_factory=list)
    target_margin_rate: float | None = None
    max_supply_for_target: int | None = None
    scenarios: list[dict] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


def _norm(v) -> tuple[int | None, str]:
    if v is None:
        return None, "미확인"
    if isinstance(v, dict):
        amt = v.get("amount")
        return (int(amt) if amt is not None else None), (v.get("basis") or ("입력값" if amt is not None else "미확인"))
    return int(v), "입력값"


def analyze(req: BidRequirement, inputs: dict | None = None, proxy_candidates: list[Candidate] | None = None,
            mall_build_total: int | None = None, *, admin_rate: float | None = None,
            target_margin_rate: float | None = None) -> CostAnalysis:
    """inputs: {항목: 원 | {"amount": 원, "basis": "견적"|"계약"|"가정"}} — 금액은 VAT 별도(공급가액).
    admin_rate: 일반관리비를 공급가액의 비율로 (예: 0.05). target_margin_rate: 목표 이익률 (예: 0.10)."""
    inputs = dict(inputs or {})
    b = req.budget_per_person
    net = (round(b / 1.1) if req.vat_included else b) if b else None
    if mall_build_total is not None and req.headcount:
        inputs["mall_build"] = {"amount": round(mall_build_total / req.headcount),
                                "basis": f"고정비 {mall_build_total:,}원 ÷ {req.headcount:,}명"}
    if admin_rate is not None and net and "admin_overhead" not in inputs:
        inputs["admin_overhead"] = {"amount": round(net * admin_rate), "basis": f"공급가액의 {admin_rate:.0%}"}
    lines = []
    for key, label in COMPONENTS:
        amt, basis = _norm(inputs.get(key))
        lines.append(CostLine(key=key, label=label, amount=amt, basis=basis))
    known = sum(l.amount for l in lines if l.amount is not None)
    unknown = [l.label for l in lines if l.amount is None]
    assumed = [l.label for l in lines if l.amount is not None and l.basis == "가정"]
    residual = (net - known) if (net and not unknown) else None
    status = "산출 불가" if residual is None else (
        "확정" if all(l.basis in CONFIRMED or l.basis.startswith("고정비") or l.basis.startswith("공급가액의") for l in lines)
        else "추정")
    margin = round(residual / net, 4) if residual is not None and net else None
    total = residual * req.headcount if residual is not None and req.headcount else None

    max_supply = None
    if target_margin_rate is not None and net:
        others = [l for l in lines if l.key != "supply"]
        if all(l.amount is not None for l in others):
            max_supply = round(net * (1 - target_margin_rate)) - sum(l.amount for l in others)

    scenarios = []
    for c in proxy_candidates or []:
        if c.observed_price is None or not b:
            continue
        gap = b - c.observed_price
        scenarios.append({
            "candidate": c.name, "assumed_supply": c.observed_price,
            "gap_before_other_costs": gap,
            "verdict": ("추가 비용 전에도 예산 초과 — B2B 견적 없이는 실행 가능성 입증 불가" if gap < 0
                        else "차액은 확정 수익이 아님 — 포장·창고·택배·운영비 확인 전"),
        })

    notes = []
    if req.vat_included and b:
        notes.append(f"1인 예산 {b:,}원은 VAT 포함 — 비용·이익은 공급가액 {net:,}원 기준으로 계산합니다 (항목 금액도 VAT 별도로 넣어 주세요).")
    elif req.vat_included is None and b:
        notes.append("VAT 기준이 공고에서 확인되지 않아 1인 예산 전체를 공급가액으로 보고 계산했습니다 — VAT 포함이면 이익이 약 9% 줄어듭니다.")
    if assumed:
        notes.append("가정값 포함: " + ", ".join(assumed) + " — 협력사 견적·계약으로 바꾸기 전까지 이익은 추정입니다.")
    if req.min_online_price and b:
        notes.append(f"온라인가 {req.min_online_price:,}원 이상은 '상품 가치' 조건이며 매입가 의무가 아니므로 "
                     f"{b - req.min_online_price:,}원을 이익으로 확정하지 않습니다.")
    if req.headcount and req.categories:
        n = sum(x.count for x in req.categories)
        notes.append(f"{req.headcount:,}명은 전체 {n}종 선택에 대한 예정 인원입니다. 상품별 주문량은 미확인으로 두며 "
                     f"{req.headcount:,}÷{n} 균등 수량을 적용하지 않습니다.")
    if req.vat_included is not None:
        notes.append("VAT " + ("포함" if req.vat_included else "별도") + " 기준 — 견적별 VAT 기준을 반드시 명시받고 세무 처리는 별도 확인합니다.")
    return CostAnalysis(budget_per_person=b, vat_included=req.vat_included, net_budget=net, lines=lines, known_total=known,
                        unknown=unknown, residual=residual, margin_rate=margin, total_profit=total, status=status,
                        assumed=assumed, target_margin_rate=target_margin_rate, max_supply_for_target=max_supply,
                        scenarios=scenarios, notes=notes)
