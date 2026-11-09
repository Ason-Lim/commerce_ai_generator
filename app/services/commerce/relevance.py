"""판매처(쿠팡·네이버) 검색 결과 관련성 — 새 규칙 후보의 '영향 비교'용 분류 (2026-11-03 p39).

아직 실제 경로(검색·재선택·MCP)에 연결하지 않는다 — 비교 결과를 확인한 뒤 적용 여부를 정한다 (GPT 검토 17:13).
기존 규칙(service.relevant)은 검색 낱말 중 하나만 맞아도 통과 → '한우 등심'에 '한우 … 스테이크 소고기'가 들어온다.

분류 (상품명에 낱말이 없다고 '다른 상품'으로 확정하지 않는다 — 확인할 수 없다는 뜻):
    keep                   상품 낱말이 모두 있고 조건(원산지·보관)도 확인됨
    item_unconfirmed       요청한 품목·부위 확인 불가 — 상품 낱말 중 상품명(또는 같은 부류 말)에 없는 것이 있음
    condition_unconfirmed  품목은 맞지만 원산지·보관 조건 확인 불가 — 상품명에 같은 뜻 표기가 없음
    old_excluded           기존 규칙에서도 빠지던 결과
"""
from __future__ import annotations

# 확인된 조건 동의어 — 상품명에 이 말이 있으면 조건이 표기된 것으로 본다 (근거를 같이 적는다)
#   한우: 국내에서 사육된 한우 품종 소고기를 가리키는 말 → 국산
#   한돈: 국내산 돼지고기 공동 브랜드(한돈자조금) → 국산
CONDITION_SYNONYMS: dict[str, tuple[str, ...]] = {"국산": ("한우", "한돈"), "국내산": ("한우", "한돈")}

LABELS = {"keep": "유지", "item_unconfirmed": "요청 품목·부위 확인 불가", "condition_unconfirmed": "원산지·보관 조건 확인 불가",
          "old_excluded": "기존에도 제외"}


def classify(title: str, terms: list[str] | None) -> dict:
    """{'verdict', 'missing': [확인 못 한 낱말], 'synonym': [동의어로 확인한 조건 '국산←한우']}."""
    from app.services.chat.service import relevant
    from app.services.commerce.search import CONDITIONS, _w, partner_terms_required

    terms = [t for t in (terms or []) if (t or "").strip()]
    if not terms:
        return {"verdict": "keep", "missing": [], "synonym": []}
    if not relevant(title, terms):
        return {"verdict": "old_excluded", "missing": [], "synonym": []}
    missing = [t for t in partner_terms_required(terms) if _w(t) not in CONDITIONS and not relevant(title, [t])]
    if missing:
        return {"verdict": "item_unconfirmed", "missing": missing, "synonym": []}
    cond_missing, synonym = [], []
    for t in terms:
        w = _w(t)
        if w not in CONDITIONS:
            continue
        if any(form in (title or "") for form in CONDITIONS[w]):
            continue
        hit = next((s for s in CONDITION_SYNONYMS.get(w, ()) if s in (title or "")), None)
        if hit:
            synonym.append(f"{w}←{hit}")
        else:
            cond_missing.append(t)
    if cond_missing:
        return {"verdict": "condition_unconfirmed", "missing": cond_missing, "synonym": synonym}
    return {"verdict": "keep", "missing": [], "synonym": synonym}
