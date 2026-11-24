"""수주 문의 → 폐쇄몰 초안 (2026-11-24) — 설계 claude/b2b_stage2_settle_2026-11-24.md.

B2B 문의 창구(#105)에서 '수주'로 바꾼 문의를 폐쇄몰 초안으로 옮긴다.
* 문의에서: 발주처 이름 · 시기(제목) · 받는 방법(미정이면 직원 집 배송) · 인원·1인 예산(정산 계약값의 처음 값) · 콘솔 공고 번호.
* 상품: 운영자가 공급사 근거(evidence)의 후보에서 고른다. 후보의 **견적 단가만** 매입 단가로 옮긴다
  (공개 판매가·도매몰 관측가는 매입 단가가 아님 — 비워 두고 '단가 확인 필요'). 상품 사진은 사용 허락 확인 전이라 옮기지 않는다.
* 초안(draft)으로만 만든다 — 직원은 못 들어온다. 운영자가 상품·기간·매뉴얼을 확인하고 '열기'.
* 문의에는 만든 폐쇄몰을 기록하고(이벤트), 몰에는 문의 번호를 남겨 정산이 계약값을 찾을 수 있게 한다.
"""

from __future__ import annotations

import re

from app.services.corpmall import store

_ID_RE = re.compile(r"[^A-Za-z0-9_-]")


def candidates(q: str = "", limit: int = 60) -> list[dict]:
    """폐쇄몰에 넣을 수 있는 상품 후보(공급사 근거) — 이름·공급사·견적 단가·관측가 구분. 판정은 하지 않는다(콘솔에서)."""
    from app.admin.b2b import evidence
    from app.admin.b2b.suppliers import sale_type

    words = [w for w in re.split(r"\s+", (q or "").strip()) if w]
    out = []
    for c in evidence.all_candidates():
        text = f"{c.name} {c.option or ''} {c.supplier} {c.category or ''}"
        if words and not all(w in text for w in words):
            continue
        kind, label = sale_type(c.price_kind, c.min_order_qty)
        out.append(
            {
                "candidate_id": c.candidate_id,
                "name": c.name,
                "option": c.option,
                "supplier": c.supplier,
                "category": c.category,
                "quote": c.unit_price_quote,
                "observed_price": c.observed_price,
                "price_label": label,
                "stock": c.stock_status,
            }
        )
    out.sort(key=lambda d: (d["quote"] is None, d["name"]))
    return out[:limit]


def _item_id(cid: str, used: set) -> str:
    base = _ID_RE.sub("", cid)[-30:] or "item"
    out, n = base, 2
    while out in used:
        out, n = f"{base[:26]}-{n}", n + 1
    used.add(out)
    return out


def from_inquiry(
    eng,
    inquiry_id: str,
    *,
    slug: str,
    opens_at: str,
    closes_at: str,
    candidate_ids: list[str],
    title: str | None = None,
    delivery_mode: str | None = None,
    default_item: str | None = None,
    by: str = "operator",
) -> dict:
    """수주 문의 → 폐쇄몰 초안. 문의가 '수주'가 아니면 거부."""
    from app.admin.b2b import evidence
    from app.services.b2b_inquiry import store as inq

    ieng = inq.engine()
    d = inq.get(ieng, inquiry_id)
    if d is None:
        raise store.MallError("없는 문의예요")
    if d["status"] != "won":
        raise store.MallError("'수주'로 바꾼 문의만 폐쇄몰 초안으로 옮길 수 있어요")
    if not candidate_ids:
        raise store.MallError("폐쇄몰에 넣을 상품을 하나 이상 골라 주세요")
    by_id = {c.candidate_id: c for c in evidence.all_candidates()}
    missing = [x for x in candidate_ids if x not in by_id]
    if missing:
        raise store.MallError("없는 후보예요: " + ", ".join(missing[:3]))
    used: set = set()
    items = []
    for cid in candidate_ids:
        c = by_id[cid]
        items.append(
            {
                "id": _item_id(cid, used),
                "name": c.name,
                "desc": c.option or None,
                "tier": None,
                "supplier": c.supplier,
                "supplier_id": None,
                "supplier_sku": None,
                "unit_cost": c.unit_price_quote,  # 견적 단가만 — 없으면 None(단가 확인 필요)
                "supplier_candidate_id": cid,
            }
        )
    mode = delivery_mode or ("individual" if d["delivery"] in ("individual", "undecided") else d["delivery"])
    if mode == "coupon":
        raise store.MallError("모바일 쿠폰 몰은 2차예요 — 직원 집 배송이나 회사 일괄 배송으로 골라 주세요")
    default_id = None
    if default_item:
        default_id = next((it["id"] for it, cid in zip(items, candidate_ids, strict=True) if cid == default_item), None)
    spec = {
        "slug": slug,
        "client": d["company"],
        "title": title or f"{d['occasion']} 임직원 선물",
        "opens_at": opens_at,
        "closes_at": closes_at,
        "delivery_mode": mode,
        "items": items,
        "default_item_id": default_id,
        "bid_id": d.get("bid_id"),
        "inquiry_id": inquiry_id,
        "contract": {
            "headcount": d.get("headcount"),
            "unit_price": d.get("budget_per_person"),
            "vat_mode": "included",
            "basis": "headcount",
            "source": "문의 조건(확정 전)",
        },
    }
    m = store.create_mall(eng, spec)
    inq._update(ieng, inquiry_id, inq._ev("mall_draft", by, mall_id=m["mall_id"], slug=m["slug"]))
    with eng.begin() as c:
        store._event(c, m["mall_id"], "from_inquiry", {"inquiry_id": inquiry_id, "items": len(items), "by": by})
    return m


__all__ = ["candidates", "from_inquiry"]
