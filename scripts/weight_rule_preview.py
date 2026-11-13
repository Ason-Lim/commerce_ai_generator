"""예비 경로(/recommendations/nl) 중량 규칙 변경 미리보기 — 읽기 전용 (2026-11-11).

지금: app/main.py estimate_weight_grams (여러 중량이면 마지막 값)
바꿀 것: 채팅과 같은 app/services/chat/explain.parse_weight (여러 중량이면 계산 안 함 → '중량 옵션이 있어요')

DB 의 price_per_100g 가 비어 있어 main.py 가 상품명으로 계산하는 상품만 나온다.
결과: docs/claude/weight_rule_preview_2026-11-11.md

사용 (Mac):  uv run python scripts/weight_rule_preview.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from stage1_ranking_snapshot import _call, _queries, _setup  # noqa: E402

KIND_KO = {"single": "중량 1개", "multiplied": "곱하기", "ambiguous": "중량 옵션(여러 중량)", "bonus": "증정분",
           "count_unclear": "개수 불명(500g 2팩 등)", "multiply_unclear": "곱하기 불명", "none": "중량 표기 없음"}


def _price(item):
    p = item.get("effective_price") or item.get("final_price") or item.get("sale_price") or item.get("price")
    try:
        return float(p or 0)
    except (TypeError, ValueError):
        return 0.0


def main():
    from app.services.chat.explain import parse_weight, weight_note

    m = _setup()
    seen: dict[str, dict] = {}
    original = m.calculate_price_per_100g

    def wrapped(item):
        old = original(item)
        name = item.get("product_name") or ""
        if name not in seen and not (item.get("unit_price_per_kg") or item.get("price_per_kg")):
            parsed = parse_weight(name)
            price = _price(item)
            new = price / (parsed["weight"] / 100) if parsed["weight"] and price > 0 else 0
            seen[name] = {"old": old, "old_w": m.estimate_weight_grams(name), "new": new,
                          "kind": parsed["kind"], "found": parsed["found"], "price": price,
                          "note": weight_note(name)}
        return old

    m.calculate_price_per_100g = wrapped
    qs = _queries(m)
    for q in qs:
        _call(m, q, "price", True)

    changed = {n: r for n, r in seen.items() if round(r["old"] or 0) != round(r["new"] or 0)}
    by_kind: dict[str, int] = {}
    for r in changed.values():
        by_kind[r["kind"]] = by_kind.get(r["kind"], 0) + 1

    lines = ["# 예비 경로 중량 규칙 변경 미리보기 (2026-11-11)", "",
             f"- 질의 {len(qs)}개 · 상품명으로 100g당을 계산한 상품 {len(seen)}개 · 값이 바뀌는 상품 **{len(changed)}개**",
             "- 바뀌는 이유: " + (", ".join(f"{KIND_KO.get(k, k)} {v}개" for k, v in sorted(by_kind.items())) or "없음"),
             "- 'price'(가격순) 우선순위에서만 순서에 영향 — 100g당이 비면 목록 뒤로 간다", "",
             "| 상품명 | 가격 | 지금 중량 → 100g당 | 바뀐 뒤 | 읽은 중량 |", "|---|---:|---|---|---|"]
    for n, r in sorted(changed.items(), key=lambda x: x[1]["kind"]):
        now = f"{r['old_w']:g}g → {round(r['old']):,}원" if r["old"] else "계산 안 함"
        after = (f"{round(r['new']):,}원" if r["new"]
                 else f"{r['note']['label']} ({r['note']['detail']})" if r["note"] else "계산 안 함")
        lines.append(f"| {n.replace('|', '/')} | {r['price']:,.0f} | {now} | {after} | {' · '.join(r['found']) or '—'} |")
    out = ROOT / "docs" / "claude" / "weight_rule_preview_2026-11-11.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"계산 대상 {len(seen)}개, 바뀌는 상품 {len(changed)}개 → {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
