"""R0 통제 검증: 채팅 추천 경로 저장 · 관리자 클릭(chat_internal) 저장이 실제 DB에서 되는가.

실제 앱(app.main.app)을 테스트 클라이언트로 띄워
  1. '사과 추천해줘' — 주 경로(쿠팡 API 1회 호출) → 세션 기록의 path = canonical_provider 인지
  2. 같은 요청, 주 경로를 강제로 실패시켜 DB 예비 경로 → path = db_fallback 인지
  3. 2번 세션에서 관리자 토큰으로 /go/{세션}/1 클릭 → product_click_log 에 query='chat_internal' 로 저장되는지
를 확인하고, **이 검증이 만든 기록(세션 2개의 행)은 마지막에 모두 지운다** (session_id 열이 있는 모든 테이블에서 이 두 세션만).

사용 (Mac): .venv/bin/python scripts/r0_controlled_check.py
결과: docs/claude/r0_controlled_check_<날짜>.md
"""
from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except ImportError:
        pass
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine, text

    import app.main as m
    from app.admin.auth import expected_token
    from app.core.config import resolve_database_url

    now = datetime.now(timezone.utc)
    eng = create_engine(resolve_database_url(), pool_pre_ping=True)
    result, sessions = {}, []

    def turn_paths(sid):
        with eng.connect() as c:
            raw = c.execute(text("SELECT state_json FROM recipe_chat_session WHERE session_id = :s"), {"s": sid}).scalar()
        st = json.loads(raw) if isinstance(raw, str) else (raw or {})
        return [t.get("path") for t in st.get("turns") or [] if t.get("stage") == "shopping"]

    try:
        with TestClient(m.app) as client, redirect_stdout(io.StringIO()):
            r1 = client.post("/api/chat", json={"message": "사과 추천해줘"}).json()
            sessions.append(r1["session_id"])
            original = m.run_recommendation_pipeline

            def _fail(*_a, **_k):
                raise RuntimeError("forced db fallback (R0 controlled check)")
            m.run_recommendation_pipeline = _fail
            try:
                r2 = client.post("/api/chat", json={"message": "사과 추천해줘"}).json()
            finally:
                m.run_recommendation_pipeline = original
            sessions.append(r2["session_id"])
            go = client.get(f"/go/{r2['session_id']}/1", follow_redirects=False,
                            headers={"X-Access-Token": expected_token()})
        result["canonical_paths"] = turn_paths(sessions[0])
        result["fallback_paths"] = turn_paths(sessions[1])
        result["go_status"] = go.status_code
        result["go_location_is_product"] = go.headers.get("location", "/") != "/"
        with eng.connect() as c:
            rows = c.execute(text("SELECT query, product_name, rank, selected_section FROM product_click_log "
                                  "WHERE session_id = :s"), {"s": sessions[1]}).mappings().all()
        result["click_rows"] = [dict(r) for r in rows]
    finally:
        cleaned = {}
        if sessions:
            with eng.begin() as c:
                tables = [r[0] for r in c.execute(text(
                    "SELECT table_name FROM information_schema.columns WHERE table_schema = 'public' "
                    "AND column_name = 'session_id' AND table_name IN (SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_type = 'BASE TABLE')"))]
                for t in tables:
                    n = c.execute(text(f'DELETE FROM "{t}" WHERE session_id = ANY(:ids)'), {"ids": sessions}).rowcount
                    if n:
                        cleaned[t] = n
        result["cleaned"] = cleaned

    ok_paths = result.get("canonical_paths") == ["canonical_provider"] and result.get("fallback_paths") == ["db_fallback"]
    ok_click = any(r["query"] == "chat_internal" for r in result.get("click_rows") or [])
    L = ["# R0 통제 검증 — 추천 경로 저장 · 관리자 클릭 저장", "", f"- 실행: {now.isoformat(timespec='seconds')}", "",
         f"- 주 경로 요청의 기록 path: {result.get('canonical_paths')} → {'통과' if result.get('canonical_paths') == ['canonical_provider'] else '**실패**'}",
         f"- 예비 경로 강제 요청의 기록 path: {result.get('fallback_paths')} → {'통과' if result.get('fallback_paths') == ['db_fallback'] else '**실패**'}",
         f"- 관리자 토큰 /go 클릭: 응답 {result.get('go_status')}, 상품으로 이동 {result.get('go_location_is_product')}",
         f"- 저장된 클릭: {result.get('click_rows')} → {'통과' if ok_click else '**실패**'}",
         f"- 정리: 검증 세션 2개의 행 삭제 {result.get('cleaned')}", "",
         "※ 실행 중인 서버(run_prod.sh 등)는 코드를 다시 읽어야 새 기록 방식이 적용됨 — 서버 재시작 필요", ""]
    out = ROOT / "docs" / "claude" / f"r0_controlled_check_{now.astimezone().strftime('%Y-%m-%d')}.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print(f"저장: {out}  (경로 {'통과' if ok_paths else '실패'}, 관리자 클릭 {'통과' if ok_click else '실패'}, 정리 {result.get('cleaned')})")


if __name__ == "__main__":
    main()
