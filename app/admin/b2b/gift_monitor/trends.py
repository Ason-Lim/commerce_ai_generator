"""입찰 트렌드 분석 — gift_trend_analyzer 대시보드의 집계(유형·예산대·기업유형·자격요건)를 이식하고
기관유형·시기·월별 마감 분포를 더했다. 리포트 문장은 집계 숫자에서만 만든다.

기본값으로 신뢰 등급이 낮은 공고(legacy_unverified)는 통계에서 뺀다.
"""
from __future__ import annotations

import re
from collections import Counter
from datetime import date, timedelta

from app.admin.b2b import bids as store
from app.admin.b2b.gift_monitor import classify


def _pool(include_unverified: bool, include_legacy: bool) -> list[store.BidNotice]:
    out = []
    for b in store.list_bids():
        if b.verification == "legacy_unverified" and not include_legacy:
            continue
        if b.verification == "unverified" and not include_unverified:
            continue
        out.append(b)
    return out


# ── 분석 기간 (2026-11-23 사용자 요청: 최근 7일·30일·3개월·기간 설정) ──
PRESETS = {"7d": ("최근 7일", 7), "30d": ("최근 30일", 30), "3m": ("최근 3개월", 91)}
_RANGE = re.compile(r"(20\d\d[-./]\s*\d{1,2}[-./]\s*\d{1,2})\.?\s*(?:~|-|부터|에서)\s*(20\d\d[-./]\s*\d{1,2}[-./]\s*\d{1,2})")


def parse_period(prompt: str | None, today: date | None = None) -> dict:
    """문장 속 기간 → {key, label, start, end}. 없으면 전체 기간."""
    today = today or date.today()
    p = prompt or ""
    m = _RANGE.search(p)
    if m:
        a, b = classify.parse_date(m.group(1)), classify.parse_date(m.group(2))
        if a and b:
            a, b = min(a, b), max(a, b)
            return {"key": "custom", "label": "기간 설정", "start": a, "end": b}
    if re.search(r"(?:최근|지난)\s*(?:3|세)\s*개월|(?:최근|지난)\s*90\s*일|3m\b", p):
        key = "3m"
    elif re.search(r"(?:최근|지난)\s*(?:30\s*일|한\s*달|1\s*개월)|30d\b", p):
        key = "30d"
    elif re.search(r"(?:최근|지난)\s*(?:7\s*일|일주일|1\s*주)|7d\b", p):
        key = "7d"
    else:
        return {"key": "all", "label": "전체 기간", "start": None, "end": None}
    label, days = PRESETS[key]
    return {"key": key, "label": label, "start": today - timedelta(days=days - 1), "end": today}


def _basis_date(b: store.BidNotice) -> date | None:
    """공고일(게시일) 기준 — 없으면 마감일."""
    return classify.parse_date(b.posted) or classify.parse_date(b.deadline)


def _dt(s: str | None) -> str | None:
    """'2026-11-20 10:00:00' · '2026-11-20T17:00' → '2026.11.20. 10:00' (시간 없으면 날짜만)."""
    d = classify.parse_date(s)
    if not d:
        return None
    t = re.search(r"[T\s](\d{1,2}):(\d{2})", str(s))
    return f"{d:%Y.%m.%d.}" + (f" {int(t.group(1)):02d}:{t.group(2)}" if t else "")


def _dist(counter: Counter, order: list[str]) -> list[dict]:
    total = sum(counter.values()) or 1
    keys = order + [k for k in counter if k not in order]
    return [{"label": k, "count": counter.get(k, 0), "pct": round(counter.get(k, 0) * 100 / total)} for k in keys
            if counter.get(k, 0) or k in order]


def analyze(include_unverified: bool = True, include_legacy: bool = False, today: date | None = None,
            period: dict | None = None) -> dict:
    period = period or {"key": "all", "label": "전체 기간", "start": None, "end": None}
    pool = _pool(include_unverified, include_legacy)
    undated = 0
    if period.get("start") or period.get("end"):
        kept = []
        for b in pool:
            d = _basis_date(b)
            if d is None:
                undated += 1
            elif (not period.get("start") or d >= period["start"]) and (not period.get("end") or d <= period["end"]):
                kept.append(b)
        pool = kept
    excluded = {
        "legacy": sum(b.verification == "legacy_unverified" for b in store.list_bids()) if not include_legacy else 0,
        "unverified": sum(b.verification == "unverified" for b in store.list_bids()) if not include_unverified else 0,
    }
    dv = [(b, b.derived(today)) for b in pool]
    types = Counter(d["bid_type"] for _, d in dv)
    comp = Counter(d["company_type"] for _, d in dv)
    quals = Counter(q for _, d in dv for q in d["qualifications"])
    bands = Counter(d["budget_band"] for _, d in dv)
    inst = Counter(b.institution_type for b, _ in dv)
    occ = Counter(d["occasion"] for _, d in dv)
    status = Counter(d["status"] for _, d in dv)
    months = Counter()
    for b, _ in dv:
        if dd := classify.parse_date(b.deadline):
            months[f"{dd.year}-{dd.month:02d}"] += 1
    budgets = [b.budget for b, _ in dv if b.budget]
    total = len(pool)

    def share(c: Counter, k: str) -> int:
        return round(c.get(k, 0) * 100 / total) if total else 0

    physical = sum(v for k, v in types.items() if k.startswith("선물세트"))
    report = []
    if total:
        top_t = types.most_common(1)[0]
        report.append(f"집계 대상 {total}건 중 가장 많은 유형은 '{top_t[0]}'({top_t[1]}건, {share(types, top_t[0])}%)입니다. "
                      f"실물 선물세트는 {round(physical * 100 / total)}%, 상품권(온누리·모바일)은 "
                      f"{share(types, '온누리상품권') + share(types, '모바일상품권')}%입니다.")
        if budgets:
            budgets.sort()
            med = budgets[len(budgets) // 2]
            report.append(f"금액이 기재된 {len(budgets)}건의 예산 중앙값은 {med:,}원이고, 최소 {budgets[0]:,}원 · 최대 {budgets[-1]:,}원입니다. "
                          f"금액 미기재는 {bands.get('금액 미기재', 0)}건입니다.")
        if quals:
            q, n = quals.most_common(1)[0]
            report.append(f"자격·요건 키워드는 '{q}'이 {n}건으로 가장 자주 나타납니다 (규칙 키워드 기준이며 원문 평가표 확인 필요).")
        top_inst = inst.most_common(1)[0]
        report.append(f"기관 유형은 '{top_inst[0]}'이 {top_inst[1]}건으로 가장 많습니다.")
        open_n = status.get("입찰중", 0) + status.get("마감임박", 0)
        report.append(f"현재 참여 가능한 공고(입찰중·마감임박)는 {open_n}건입니다.")
    else:
        report.append("이 기간에 해당하는 공고가 없습니다. 기간을 넓혀 보세요." if period["key"] != "all" else
                      "집계할 공고가 없습니다. 나라장터 수집이나 공고 직접 등록으로 데이터를 쌓아 주세요.")
    if excluded["legacy"]:
        report.append(f"미검증 기존 데이터 {excluded['legacy']}건은 통계에서 제외했습니다.")

    dates = sorted(d for d in (_basis_date(b) for b in pool) if d)
    last = store.last_collected()
    newest = max((b.posted for b in store.list_bids() if classify.parse_date(b.posted)),
                 key=lambda x: (classify.parse_date(x), str(x)), default=None)
    info = {
        "key": period["key"], "label": period["label"],
        "start": (period.get("start") or (dates[0] if dates else None)),
        "end": (period.get("end") or (dates[-1] if dates else None)),
        "basis": "공고일 기준 (공고일이 없으면 마감일)",
        "undated": undated,
        "last_collected": _dt(last["at"]) if last else None,
        "last_source": (last or {}).get("source"),
        "newest_posted": _dt(newest),
    }
    for k in ("start", "end"):
        info[k] = info[k].isoformat() if info[k] else None
    if period["key"] != "all":
        report.insert(0, f"분석 기간은 {period['label']}({period['start']:%Y.%m.%d.} ~ {period['end']:%Y.%m.%d.}, 공고일 기준)입니다."
                      + (f" 날짜를 알 수 없는 공고 {undated}건은 뺐습니다." if undated else ""))
    return {
        "period": info,
        "total": total, "excluded": excluded,
        "kpi": {"open": status.get("입찰중", 0), "closing": status.get("마감임박", 0), "closed": status.get("입찰마감", 0),
                "physical_pct": round(physical * 100 / total) if total else 0,
                "voucher_pct": (share(types, "온누리상품권") + share(types, "모바일상품권")),
                "median_budget": sorted(budgets)[len(budgets) // 2] if budgets else None},
        "bid_types": _dist(types, classify.BID_TYPES),
        "budget_bands": _dist(bands, classify.BUDGET_BANDS),
        "company_types": _dist(comp, classify.COMPANY_TYPES),
        "qualifications": _dist(quals, classify.QUALIFICATIONS),
        "institution_types": _dist(inst, classify.INSTITUTION_TYPES[:-1]),
        "occasions": _dist(occ, classify.OCCASIONS),
        "deadline_months": [{"label": k, "count": months[k]} for k in sorted(months)],
        "report": report,
    }
