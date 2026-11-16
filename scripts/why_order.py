"""오늘 대화에서 같은 검색어의 추천 순서가 왜 달랐는지 본다 (읽기 전용).

    uv run python scripts/why_order.py 귤

세션 상태(recipe_chat_session)의 '최근 본 상품'에서 그 검색어 결과를 시간순으로 꺼내,
후보별 중량·100g당·대용량 판정과 고른 역할을 보여 준다. DB 를 바꾸지 않는다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import sqlalchemy

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import DATABASE_URL  # noqa: E402
from app.services.chat import explain  # noqa: E402


def main(query: str) -> None:
    eng = sqlalchemy.create_engine(DATABASE_URL, future=True)
    with eng.connect() as conn:
        rows = conn.execute(sqlalchemy.text(
            "SELECT session_id, state_json, updated_at FROM recipe_chat_session "
            "WHERE updated_at > now() - interval '1 day' ORDER BY updated_at")).all()
    found = 0
    for sid, raw, upd in rows:
        state = json.loads(raw or "{}")
        for s in state.get("seen") or []:
            if (s.get("query") or "").replace(" ", "") != query.replace(" ", ""):
                continue
            found += 1
            cards = s.get("cards") or []
            print(f"\n=== 세션 {sid[:8]} · {s.get('at')} · 후보 {len(cards)}개")
            weighed = 0
            for c in sorted(cards, key=lambda c: (c.get("rank") or 99)):
                bulk = explain.bulk_size(c, query)
                if c.get("per100g") and not bulk:
                    weighed += 1
                print(f"  {c.get('rank') or '-':>2} {c.get('role') or '':<7} {c.get('price') or 0:>7,}원 "
                      f"중량 {c.get('weight_g') or '-'} · 100g당 {c.get('per100g') or '-'} "
                      f"{'· 대용량 ' + bulk if bulk else ''}| {(c.get('title') or '')[:40]}")
            print(f"  → 100g당 비교 가능(대용량 제외) {weighed}개 — 2개 이상이어야 '가성비'로 고름")
    if not found:
        print("오늘 그 검색어 결과가 없어요.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "귤")
