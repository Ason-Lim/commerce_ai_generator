"""대화 이어 묻기 다중 차례 시험 — 차례마다 유효 조건 · 쿠팡 호출 수 · 표시 목록 · 복원 결과를 한 표로 (2026-11-22).

외부 검토(11-22 17:07) 권고: '올리브유 → 로켓배송만 → 1L짜리로 → 더 찾아보기 → 처음 조건으로'를 실제로 돌려
각 단계의 유효 조건·API 호출 수·표시 후보·복원 결과를 남긴다.

사용 (Mac, 운영과 같은 .env):
    uv run python scripts/followup_scenario.py                       # 기본 시나리오, 실제 쿠팡 API
    uv run python scripts/followup_scenario.py 사과 "싼 순으로" "2kg으로" "처음 조건으로"
    uv run python scripts/followup_scenario.py --fake                # 가짜 검색 결과 (API·DB 없이 흐름만)
결과: 화면 출력 + docs/claude/followup_scenario_<날짜시각>.md
주의: 실제 실행은 채팅 세션 하나를 운영 DB 에 남긴다(일반 대화와 같은 90일 보존). 쿠팡 호출은 표의 '호출' 합계만큼.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DEFAULT = ["올리브유", "로켓배송만", "1L짜리로", "더 찾아보기", "처음 조건으로"]
KST = timezone(timedelta(hours=9))


def fake_service():
    """API·DB 없이 흐름만 보는 가짜 (sqlite 메모리 DB · 검색어별 고정 결과)."""
    import sqlite3
    from app.services.chat.service import ChatService
    from app.services.recipe_chat.service import RecipeChat

    def cp(name, price, i, rocket=False):
        return {"product_name": name, "price": price, "platform": "coupang", "mall_name": "쿠팡", "is_coupang": True,
                "is_rocket": rocket, "category_name": "식품",
                "product_url": f"https://link.coupang.com/re/AFFSDP?pageKey=1&itemId={i}&vendorItemId=9{i}"}

    table = {
        "올리브유": [cp("해표 압착 올리브유 500ml", 6900, 1, True), cp("살부루아 올리브유 1L", 19900, 2),
                 cp("커클랜드 엑스트라버진 올리브유 3L", 71980, 3, True), cp("올리타리아 엑스트라 버진 올리브유 1L", 15900, 4),
                 cp("피에트로코리첼리 올리브유 500ml", 11500, 5)],
        "올리브유 1L": [cp("살부루아 올리브유 1L", 19900, 2), cp("해표 올리브유 1L", 12900, 11, True)],
        "올리브오일": [cp("코스트코 올리브오일 2L", 29900, 9, True), cp("데체코 올리브오일 1L", 17900, 10)],
    }
    import tempfile

    from tests.services.chat.conftest import DDL, SqliteDb     # 테스트와 같은 오프라인 저장소 (가짜 시험 전용)

    path = Path(tempfile.mkdtemp()) / "chat.sqlite3"
    raw = sqlite3.connect(path)
    raw.executescript(DDL)
    raw.close()
    db = SqliteDb(path)

    def shop(q, priority, sid):
        return {"items": list(table.get(q, [])), "recommendation_path": "canonical_provider"}

    return ChatService(db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))


def run(messages: list[str], service) -> list[dict]:
    from app.services.chat import followup as fu

    rows, sid = [], None
    for n, msg in enumerate(messages, 1):
        res = service.handle(sid, message=msg)
        sid = res["session_id"]
        meta = res.get("meta") or {}
        state, _rev, _persist = service._load(sid)
        info = state.get("followup") or {}
        lists = [b["data"] for b in res["blocks"] if b["type"] == "product_list"]
        texts = [b["data"].get("md", "") for b in res["blocks"] if b["type"] in ("text", "notice")]
        rows.append({
            "n": n, "msg": msg, "stage": res["stage"],
            "cond": fu.describe_conds(info.get("conds")) or "—",
            "base": info.get("query") or "—", "origin": info.get("origin") or "—",
            "calls": meta.get("coupang_calls", 0), "session_calls": meta.get("session_coupang_calls", 0),
            "asked": meta.get("followup_searches", 0),
            "lists": [f"{d.get('title') or '추천'}: {len(d['items'])}" for d in lists],
            "top": [c["title"][:24] for d in lists[:1] for c in d["items"][:3]],
            "say": next((t for t in texts if "**광고**" not in t), "")[:120],
        })
    return rows


def table(rows: list[dict]) -> str:
    out = ["| 차례 | 말 | 단계 | 기준 묶음(처음) | 유효 조건 | 쿠팡 호출(이 차례/누적) | 다시 찾기 요청 | 표시 목록 | 첫 목록 앞 3개 | 첫 안내 |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        out.append(f"| {r['n']} | {r['msg']} | {r['stage']} | {r['base']} ({r['origin']}) | {r['cond']} | "
                   f"{r['calls']}/{r['session_calls']} | {r['asked']} | {'<br>'.join(r['lists']) or '—'} | "
                   f"{'<br>'.join(r['top']) or '—'} | {r['say'].replace('|', '/')} |")
    return "\n".join(out)


def main(argv: list[str]) -> None:
    fake = "--fake" in argv
    messages = [a for a in argv if a != "--fake"] or DEFAULT
    if fake:
        service = fake_service()
    else:
        from app.api.chat_routes import get_chat_service

        service = get_chat_service()
    rows = run(messages, service)
    md = table(rows)
    print(md)
    stamp = datetime.now(KST).strftime("%Y-%m-%d_%H%M")
    out = ROOT / "docs" / "claude" / f"followup_scenario_{stamp}{'_fake' if fake else ''}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(f"# 이어 묻기 다중 차례 시험 ({stamp}{', 가짜 검색' if fake else ', 실제 쿠팡 API'})\n\n"
                   f"시나리오: {' → '.join(messages)}\n\n{md}\n", encoding="utf-8")
    print(f"\n저장: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main(sys.argv[1:])
