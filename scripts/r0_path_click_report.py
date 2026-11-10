"""R0 집계 (읽기 전용): 채팅 추천 경로 비율 · 채팅 클릭 기록 (2026-11-10 이후 쌓인 기록).

- 추천 경로: recipe_chat_session.state_json 의 쇼핑 대화(turns, stage=shopping)의 path
  (canonical_provider = 주 경로·쿠팡 실시간 / db_fallback = DB 예비 경로 / 기록 없음 = 2026-11-10 이전 대화)
  ※ 세션마다 최근 대화 몇 개만 남으므로 '최근 대화 표본'의 비율이다.
- 클릭: product_click_log 의 query = 'chat'(고객) / 'chat_internal'(관리자 로그인 브라우저, 우리 시험) 날짜별

사용 (Mac): .venv/bin/python scripts/r0_path_click_report.py
결과: docs/claude/r0_path_click_report_<날짜>.md
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import create_engine, text  # noqa: E402

from app.core.config import resolve_database_url  # noqa: E402


def main():
    now = datetime.now(timezone.utc)
    eng = create_engine(resolve_database_url(), pool_pre_ping=True)
    paths, sessions_with_path = Counter(), 0
    with eng.connect() as c:
        c.execute(text("SET TRANSACTION READ ONLY"))
        for (raw,) in c.execute(text("SELECT state_json FROM recipe_chat_session")):
            try:
                st = json.loads(raw) if isinstance(raw, str) else (raw or {})
            except ValueError:
                continue
            got = [t.get("path") or "(기록 없음)" for t in st.get("turns") or [] if t.get("stage") == "shopping"]
            paths.update(got)
            sessions_with_path += any(p != "(기록 없음)" for p in got)
        clicks = c.execute(text("""
            SELECT created_at::date AS day, query, count(*) AS n, count(DISTINCT session_id) AS sessions
            FROM product_click_log WHERE query IN ('chat', 'chat_internal')
            GROUP BY 1, 2 ORDER BY 1 DESC, 2""")).mappings().all()
    recorded = {k: v for k, v in paths.items() if k != "(기록 없음)"}
    total = sum(recorded.values())
    L = ["# R0 집계 — 채팅 추천 경로 · 채팅 클릭", "", f"- 실행: {now.isoformat(timespec='seconds')} (읽기 전용)", "",
         "## 추천 경로 (쇼핑 대화, 세션별 최근 대화 표본)", "",
         f"- 경로가 기록된 대화 {total}개 · 세션 {sessions_with_path}개 · 기록 없음(2026-11-10 이전) {paths.get('(기록 없음)', 0)}개", ""]
    if total:
        L += ["| 경로 | 대화 | 비율 |", "|---|---|---|"]
        L += [f"| {k} | {v} | {v / total * 100:.0f}% |" for k, v in sorted(recorded.items(), key=lambda x: -x[1])]
    else:
        L.append("- 아직 경로가 기록된 대화가 없음")
    L += ["", "## 채팅 클릭 (날짜별)", "", "- chat = 고객 · chat_internal = 관리자 로그인 브라우저(우리 시험)", ""]
    if clicks:
        L += ["| 날짜 | 구분 | 클릭 | 세션 |", "|---|---|---|---|"]
        L += [f"| {r['day']} | {r['query']} | {r['n']} | {r['sessions']} |" for r in clicks]
    else:
        L.append("- 아직 채팅 클릭 기록 없음")
    L += ["", "## 행동 신호 재도입 조건 점검 (2026-11-10 결정)", "",
          "1. 채팅 화면의 노출과 클릭이 같은 결과로 기록되는가 — 클릭은 기록 시작(위 표). **노출은 아직 기록 안 함**",
          "2. 우리 테스트 세션을 걸러 내는가 — 관리자 로그인 브라우저는 chat_internal 로 구분. 가족·지인 시험 세션은 아직 구분 못 함",
          "3. 표본이 충분한가 — 위 고객(chat) 클릭 수로 판단", ""]
    out = ROOT / "docs" / "claude" / f"r0_path_click_report_{now.astimezone().strftime('%Y-%m-%d')}.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print(f"저장: {out}  (경로 기록 대화 {total}, 채팅 클릭 {sum(r['n'] for r in clicks)})")


if __name__ == "__main__":
    main()
