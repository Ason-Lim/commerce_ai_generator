"""행동 가점 제외 적용 검증 (2026-11-10): 새 순위가 '가점 6종을 뺀 예측 순위'와 같은지.

  1. RANKING_USE_BEHAVIOR=1 로 stage1_behavior_counterfactual.py 를 돌려 예측(cf_keys)을 만든다 (예전 동작 재현 + 가점 제외 예측)
  2. 기본 동작(가점 제외)으로 stage1_ranking_snapshot.py capture <이름> 을 찍는다
  3. 이 스크립트로 둘을 비교한다 — 같으면 순위 변동이 가점 제거로 설명된다

사용 (Mac): .venv/bin/python scripts/stage1_behavior_check.py <스냅샷 이름>
결과: docs/claude/stage1_behavior_check_<스냅샷 이름>.md
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAP = ROOT / "var" / "ranking_snapshots"


def session_check(queries, modes) -> dict:
    import io
    from contextlib import redirect_stdout

    from sqlalchemy import create_engine, text

    sys.path.insert(0, str(ROOT))
    import app.main as m
    from app.core.config import resolve_database_url

    engine = create_engine(resolve_database_url(), pool_pre_ping=True,
                           connect_args={"options": "-c default_transaction_read_only=on"})
    m.engine_lifecycle._engine = engine
    m.bind_engine(engine)
    with engine.connect() as c:
        sessions = [r[0] for r in c.execute(text(
            "SELECT session_id FROM user_product_preference GROUP BY session_id "
            "ORDER BY sum(click_count) DESC NULLS LAST LIMIT 3"))]
    same, diff, combos = 0, [], 0
    for q in queries:
        for p in modes:
            with redirect_stdout(io.StringIO()):
                base = [i.get("product_url") for i in m.db_fallback_recommendations(q=q, priority=p, session_id=None)["items"]]
            for sid in sessions:
                combos += 1
                with redirect_stdout(io.StringIO()):
                    got = [i.get("product_url") for i in m.db_fallback_recommendations(q=q, priority=p, session_id=sid)["items"]]
                if got == base:
                    same += 1
                else:
                    diff.append(f"{q}|{p}|세션 {sid[:8]}…")
    return {"sessions": sessions, "combos": combos, "same": same, "diff": diff}


def main(label: str):
    cf = json.loads((SNAP / "behavior_counterfactual.json").read_text(encoding="utf-8"))
    snap = json.loads((SNAP / f"{label}.json").read_text(encoding="utf-8"))["db_fallback"]
    rows, ok, bad, missing = [], 0, [], 0
    for r in cf["results"]:
        k = f"{r['query']}|{r['mode']}"
        if k not in snap or "cf_keys" not in r:
            missing += 1
            continue
        actual = [i["key"] for i in snap[k]["items"]]
        if actual == r["cf_keys"]:
            ok += 1
        else:
            bad.append((k, r["cf_keys"], actual))
        rows.append((k, r["cur_keys"] == r["cf_keys"], actual == r["cf_keys"]))
    L = [f"# 행동 가점 제외 적용 검증 ({label})", "",
         f"- 예측: behavior_counterfactual.json ({cf['run_at']}, 재현 불일치 {len(cf.get('repro_fail') or [])}건)",
         f"- 비교 {ok + len(bad)}개 조합 · **예측과 같음 {ok} · 다름 {len(bad)}** · 비교 못함 {missing}",
         "- 같음 = 새 순위의 변동이 행동 가점 6종 제거로 모두 설명됨", "",
         "| 질의·모드 | 예전과 같았나 | 예측과 같음 |", "|---|---|---|"]
    L += [f"| {k} | {'예' if same_old else '아니오(변동)'} | {'예' if match else '**아니오**'} |" for k, same_old, match in rows]
    for k, exp, act in bad[:10]:
        L += ["", f"### 다름: {k}", f"- 예측: {exp}", f"- 실제: {act}"]
    # 세션 개인화 점검: 클릭·선호 기록이 있는 실제 세션으로 불러도 순위가 세션 없음과 같은가
    sess = session_check(sorted({r["query"] for r in cf["results"]}), sorted({r["mode"] for r in cf["results"]}))
    L += ["", "## 세션 개인화 점검 (행동 기록이 있는 실제 세션 vs 세션 없음)", "",
          f"- 세션 {len(sess['sessions'])}개 × 조합 {sess['combos']}개 · **같음 {sess['same']} · 다름 {len(sess['diff'])}**",
          "- 같음 = 방문·클릭 이력이 개인화 보정으로 다시 순위에 들어오지 않음"]
    L += [f"- 다름: {d}" for d in sess["diff"][:10]]
    out = ROOT / "docs" / "claude" / f"stage1_behavior_check_{label}.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"저장: {out}  (예측과 같음 {ok}, 다름 {len(bad)}, 비교 못함 {missing})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1])
