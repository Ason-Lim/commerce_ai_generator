"""공급사 목록 (2026-11-04) — "공영홈쇼핑 기념품에 제공할 수 있는 공급사 리스트업", "건강식품 도매업체 조사해".

이전에는 이런 지시를 알아듣는 도구가 없어 '분석할 공고나 조건을 찾지 못했어요'로 끝났다.

이미 가진 근거에서만 모은다 (인터넷에서 새 업체를 지어내지 않는다).
  1) B2B 근거 저장소 — 상품 후보의 공급사별 묶음 (견적 단가가 있는지 · 공개 판매가 관측만 있는지 구분)
  2) 협력 후보 쇼핑몰 허락 기록부 (data/partners/permissions.csv — 온브릭스 등, 상태·허락일)
'협력 가능'은 판정하지 않는다: 견적·공급 확인 전에는 모두 '확인 필요'다.
"""
from __future__ import annotations

import re
from collections import defaultdict

from app.admin.b2b.evidence import infer_category

CATEGORY_WORDS = (
    ("건강기능식품", r"건강\s*기능\s*식품|건강\s*식품|건기식|홍삼|비타민|유산균|영양제"),
    ("생활용품", r"생활\s*용품|타월|수건|세제|주방"),
    ("식품", r"식품|먹거리|과일|농산물|축산|수산|한우|간식"),
)


# 판매 구분 (2026-11-04) — 같은 '가격'이라도 소매가와 도매·공급가는 뜻이 다르다. 화면·리포트에 항상 같이 적는다.
SALE_TYPES = {
    "supplier_quote": ("wholesale", "도매 · 공급 견적"),
    "supply_table": ("wholesale", "도매 · 공급가표"),
    "wholesale": ("wholesale", "도매 · 도매몰 단가"),          # 도매꾹(dome) — 최소구매수량 있음
    "consign": ("consign", "위탁 · 도매몰 공급가"),            # 도매매(supply) — 1개부터 위탁 배송
    "public_retail": ("retail", "소매 · 공개 판매가"),
    "public_display_unit_unknown": ("retail", "소매 · 공개 판매가(단위 미확인)"),
    "public_option_unconfirmed": ("retail", "소매 · 공개 판매가(옵션 미확인)"),
}
SALE_LABEL = {"wholesale": "도매", "consign": "위탁", "retail": "소매", "unknown": "구분 미확인"}


def sale_type(price_kind: str | None, moq: int | None = None) -> tuple[str, str]:
    """(구분 코드, 화면 문구).  모르는 종류는 '구분 미확인' — 소매·도매로 짐작하지 않는다."""
    kind, label = SALE_TYPES.get(price_kind or "", ("unknown", "구분 미확인"))
    if kind == "wholesale" and moq and moq > 1:
        label += f" · 최소 {moq:,}개"
    return kind, label


def dict_rx(category: str) -> str:
    """카테고리를 부르는 낱말 정규식 (없으면 이름 그대로)."""
    return next((rx for cat, rx in CATEGORY_WORDS if cat == category), re.escape(category))


def category_from(text: str) -> str | None:
    for cat, rx in CATEGORY_WORDS:
        if re.search(rx, text or ""):
            return cat
    return None


def supplier_rows(cands, category: str | None = None) -> list[dict]:
    """상품 후보 → 공급사별 한 줄.  예시(샘플) 데이터는 빼고, 견적 단가가 있는 공급사를 먼저."""
    groups: dict[str, list] = defaultdict(list)
    for c in cands:
        if getattr(c, "is_sample", False):
            continue
        cat = c.category or infer_category(c.name or "")
        if category and cat != category:
            continue
        groups[(c.supplier or "미상").strip() or "미상"].append((c, cat))
    rows = []
    for name, items in groups.items():
        if name == "미상":
            continue
        quoted = sum(1 for c, _ in items if c.unit_price_quote)
        sources = sorted({c.source for c, _ in items})
        kinds: dict[str, int] = {}
        for c, _ in items:
            k = sale_type(c.price_kind)[0]
            kinds[k] = kinds.get(k, 0) + 1
        rows.append({
            "supplier": name,
            "products": len(items),
            "categories": sorted({cat for _, cat in items if cat}),
            "examples": list(dict.fromkeys(c.name for c, _ in items))[:3],
            "quoted": quoted,
            "basis": "견적 단가 있음" if quoted else "공개 판매가 관측만",
            "sources": sources,
            "sale": [{"kind": k, "label": SALE_LABEL[k], "n": n}
                     for k, n in sorted(kinds.items(), key=lambda kv: ("wholesale", "consign", "retail", "unknown").index(kv[0]))],
        })
    rows.sort(key=lambda r: (-r["quoted"], -r["products"], r["supplier"]))
    return rows


def partner_rows() -> list[dict]:
    """협력 후보 쇼핑몰 허락 기록부 (업체·상태·허락일·메모 일부)."""
    try:
        from app.services.partners import feed
    except Exception:  # noqa: BLE001
        return []
    out = []
    for name, r in feed.permissions().items():
        memo = (r.get("메모") or "").strip()
        out.append({"supplier": name, "status": r.get("상태") or "미확인", "since": r.get("허락일") or "",
                    "memo": (memo[:60] + "…") if len(memo) > 60 else memo})
    return out
