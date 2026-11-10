"""R0 진단: 채팅 클릭 기록이 왜 0건인가 · 채팅 쇼핑 대화가 실제로 있었나 (DB에 남기지 않음).

1. 채팅 세션 기록(recipe_chat_session.state_json)에서 쇼핑 대화 수·기간·마지막 결과 수를 센다 (읽기만).
2. 채팅 /go 리다이렉트와 같은 인자로 analytics_logger.log_product_click 을 실제로 실행하되,
   바깥 트랜잭션을 열어 두고 끝에 되돌린다(ROLLBACK) → DB에는 아무것도 남지 않는다.
   예외가 나면 어느 단계(클릭 INSERT · 선호도 · 세션 문맥)에서 났는지 기록한다.

사용 (Mac): .venv/bin/python scripts/r0_chat_click_probe.py
결과: docs/claude/r0_chat_click_probe_<날짜>.md
"""
from __future__ import annotations

import json
import sys
import traceback
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine, text  # noqa: E402

from app.core.config import resolve_database_url  # noqa: E402


def chat_sessions(engine) -> dict:
    with engine.connect() as c:
        c.execute(text("SET TRANSACTION READ ONLY"))
        try:
            rows = c.execute(text("SELECT session_id, state_json, updated_at FROM recipe_chat_session")).mappings().all()
        except Exception:  # noqa: BLE001 — updated_at 이 없을 수 있음
            c.rollback()
            c.execute(text("SET TRANSACTION READ ONLY"))
            rows = c.execute(text("SELECT session_id, state_json FROM recipe_chat_session")).mappings().all()
    shopping_sessions = shopping_turns = with_items = 0
    times = []
    paths: dict = {}
    for r in rows:
        try:
            st = json.loads(r["state_json"]) if isinstance(r["state_json"], str) else (r["state_json"] or {})
        except ValueError:
            continue
        turns = [t for t in st.get("turns") or [] if t.get("stage") == "shopping"]
        if turns:
            shopping_sessions += 1
            shopping_turns += len(turns)
        for t in turns:
            paths[t.get("path") or "(기록 없음)"] = paths.get(t.get("path") or "(기록 없음)", 0) + 1
        if st.get("last_items"):
            with_items += 1
        if r.get("updated_at"):
            times.append(r["updated_at"])
    return {"sessions": len(rows), "shopping_sessions": shopping_sessions, "shopping_turns_kept": shopping_turns,
            "sessions_with_last_items": with_items,
            "first_update": min(times) if times else None, "last_update": max(times) if times else None,
            "shopping_turn_paths": paths}


def probe_click(engine) -> dict:
    from app.services import analytics_logger as al

    conn = engine.connect()
    outer = conn.begin()

    class _Eng:
        @contextmanager
        def begin(self):
            nested = conn.begin_nested()       # SAVEPOINT — 실패해도 바깥 트랜잭션은 살아 있음
            try:
                yield conn
                nested.commit()
            except Exception:
                nested.rollback()
                raise

    original = al.get_engine
    al.get_engine = lambda: _Eng()
    result = {"ok": False, "error": None, "where": None}
    try:
        # chat_routes._redirect 와 같은 인자 (/go 경유)
        al.log_product_click(session_id="r0-probe-session", query="chat", product={
            "product_url": "https://link.coupang.com/r0-probe", "selected_section": "chat",
            "recommendation_mode": "ranking"})
        n = conn.execute(text("SELECT count(*) FROM product_click_log WHERE session_id = 'r0-probe-session'")).scalar()
        result.update(ok=True, rows_written_in_txn=n)
    except Exception as exc:  # noqa: BLE001
        tb = traceback.extract_tb(exc.__traceback__)
        frames = [f"{Path(f.filename).name}:{f.lineno} {f.name}" for f in tb if "app/" in f.filename]
        result.update(error=f"{type(exc).__name__}: {str(exc).splitlines()[0][:300]}", where=frames[-3:])
    finally:
        al.get_engine = original
        outer.rollback()                       # 아무것도 남기지 않는다
        conn.close()
    return result


def main():
    engine = create_engine(resolve_database_url(), pool_pre_ping=True)
    now = datetime.now(timezone.utc)
    sessions = chat_sessions(engine)
    click = probe_click(engine)
    with engine.connect() as c:
        left = c.execute(text("SELECT count(*) FROM product_click_log WHERE session_id = 'r0-probe-session'")).scalar()
    L = ["# R0 진단 — 채팅 클릭 기록 · 채팅 쇼핑 대화", "", f"- 실행: {now.isoformat(timespec='seconds')}", "",
         "## 1. 채팅 세션 (recipe_chat_session, 읽기만)", ""]
    L += [f"- {k}: {v}" for k, v in sessions.items()]
    L += ["", "## 2. 채팅 /go 클릭 기록 재현 (끝에 되돌림)", ""]
    if click["ok"]:
        L.append(f"- 성공 — 트랜잭션 안에서 {click['rows_written_in_txn']}행 기록 후 되돌림. 기록 코드 자체는 동작함")
        L.append("- 따라서 0건은 '클릭이 없었다' 또는 '서버가 /go 를 거치지 않았다(쇼핑커넥트 바로 이동 등)'일 가능성")
    else:
        L.append(f"- **실패**: {click['error']}")
        L.append(f"- 위치: {' → '.join(click['where'] or [])}")
        L.append("- 채팅 /go·/api/click 은 이 예외를 잡아 경고 로그만 남기므로 클릭이 조용히 사라짐")
    L.append(f"- 되돌림 확인: 진단 세션 행 {left}개 남음 (0이어야 함)")
    L += ["", "## 3. 추천 경로 기록", "",
          "- `recommendation_path`(canonical_provider / db_fallback)는 지금 어디에도 저장되지 않음 → 과거 fallback 비율은 셀 수 없음",
          "- 2026-11-10부터 채팅 쇼핑 대화 기록(turns)에 경로를 남김 → 이후 대화부터 비율 집계 가능", ""]
    out = ROOT / "docs" / "claude" / f"r0_chat_click_probe_{now.astimezone().strftime('%Y-%m-%d')}.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print(f"저장: {out}  (클릭 재현 {'성공' if click['ok'] else '실패'}, 남은 진단 행 {left})")


if __name__ == "__main__":
    main()
