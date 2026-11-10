"""채팅 최종 표시 순위 스냅샷 + 근거 화면 검사 집계 (1단계, 읽기 전용).

근거 화면(app/admin/ops/evidence.build_report)을 DB 예비 경로로 모든 질의에 돌려
  - 화면 순위(explain.choose 이후 picks → others 순)와 역할을 기록하고
  - 점수 재계산 불일치, 확인 시각 없음·오래된 가격, 100g당 비교 불가, 문구 검사 경고, 과거 행동 가점 적용을 센다.
외부 API는 부르지 않는다(주 경로 제외). 모드는 고객 문장 규칙(자동)으로 정한다.

사용 (Mac):
  .venv/bin/python scripts/stage1_display_snapshot.py capture <이름>
  .venv/bin/python scripts/stage1_display_snapshot.py compare <이름1> <이름2>
결과: var/ranking_snapshots/display_<이름>.json, docs/claude/stage1_display_<이름>.md (compare: _vs_)
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
SNAP = ROOT / "var" / "ranking_snapshots"
EXTRA = ["고당도 사과", "선물용 배", "3만원 이하 샤인머스캣", "부모님 선물 망고"]
COUNTS = ("count", "price_missing", "price_stale", "per100g_not_comparable", "check_warnings", "score_mismatch",
          "behavior_applied", "behavior_reference_only")


def _setup():
    from sqlalchemy import create_engine

    import app.main as m
    from app.core.config import resolve_database_url

    engine = create_engine(resolve_database_url(), pool_pre_ping=True,
                           connect_args={"options": "-c default_transaction_read_only=on"})
    m.engine_lifecycle._engine = engine
    m.bind_engine(engine)
    return m


def capture(label):
    m = _setup()
    from sqlalchemy import text

    from app.admin.ops import evidence

    with m._get_canonical_engine().connect() as c:
        fruits = [r[0] for r in c.execute(text("SELECT DISTINCT fruit_name FROM vw_ai_recommendation_final "
                                               "WHERE fruit_name IS NOT NULL ORDER BY 1"))]
    queries = list(dict.fromkeys(fruits + EXTRA))
    out = {"label": label, "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "queries": {}}
    for q in queries:
        with redirect_stdout(io.StringIO()):
            rep = evidence.build_report(q, shopping=evidence.forced_db_shopping())
        out["queries"][q] = {
            "path": rep["path"], "summary": rep["summary"], "error": rep["error"], "audit": rep["audit"],
            "rows": [{"rank": r["display_rank"], "section": r["section"], "role": r["role"],
                      "role_key": r.get("role_key"), "url": r["url"],
                      "title": r["title"][:40], "checks": r["checks"],
                      "score_ok": None if not r["score"].get("available") else
                      (r["score"].get("view_matches") is not False and r["score"].get("main_matches") is not False)}
                     for r in rep["rows"]],
        }
    SNAP.mkdir(parents=True, exist_ok=True)
    (SNAP / f"display_{label}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    tot = {k: sum(v["summary"].get(k, 0) for v in out["queries"].values()) for k in COUNTS}
    L = [f"# 채팅 최종 표시 순위 · 근거 검사 ({label})", "",
         f"- 실행: {out['run_at']} · DB 예비 경로 · 질의 {len(queries)}개 · 모드 자동(고객 문장 규칙)", "",
         "## 합계", "", "| " + " | ".join(COUNTS) + " |", "|" + "---|" * len(COUNTS),
         "| " + " | ".join(str(tot[k]) for k in COUNTS) + " |", "",
         "## 질의별", "", "| 질의 | 결과 | 추천(역할) | 확인 시각 없음 | 오래된 가격 | 100g 비교 불가 | 문구 경고 | 점수 불일치 | 행동 가점 |",
         "|---|---|---|---|---|---|---|---|---|"]
    for q, v in out["queries"].items():
        s = v["summary"]
        picks = " / ".join(f"{r['role']}:{r['title'][:12]}" for r in v["rows"] if r["section"] == "picks")
        L.append(f"| {q} | {s['count']} | {picks or '-'} | {s['price_missing']} | {s['price_stale']} | "
                 f"{s['per100g_not_comparable']} | {s['check_warnings']} | {s['score_mismatch']} | {s.get('behavior_applied', 0)} |")
    warn = [(q, r) for q, v in out["queries"].items() for r in v["rows"] if r["checks"]]
    L += ["", f"## 문구 검사 경고 ({len(warn)})", ""]
    L += [f"- {q} · {r['rank']}위 {r['role'] or ''} {r['title']}: {'; '.join(r['checks'])}" for q, r in warn[:40]]
    md = ROOT / "docs" / "claude" / f"stage1_display_{label}.md"
    md.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"저장: {md}  (점수 불일치 {tot['score_mismatch']}, 문구 경고 {tot['check_warnings']})")


def compare(a, b):
    """순서·후보(구역+URL+역할 키)와 배지 문구를 나눠 비교한다 — 문구만 바꾼 변경은 '순서 같음 · 문구 다름'."""
    A = json.loads((SNAP / f"display_{a}.json").read_text(encoding="utf-8"))
    B = json.loads((SNAP / f"display_{b}.json").read_text(encoding="utf-8"))
    same, label_only, diff, label_changes = 0, [], [], {}
    for q in sorted(set(A["queries"]) | set(B["queries"])):
        ra = A["queries"].get(q, {}).get("rows", [])
        rb = B["queries"].get(q, {}).get("rows", [])
        oa = [(r["section"], r["url"], r.get("role_key")) for r in ra]
        ob = [(r["section"], r["url"], r.get("role_key")) for r in rb]
        if [x[:2] for x in oa] != [x[:2] for x in ob] or (
                all(x[2] is not None for x in oa + ob) and oa != ob):
            diff.append(q)
            continue
        changes = [(x["role"], y["role"]) for x, y in zip(ra, rb) if x["role"] != y["role"]]
        for c in changes:
            label_changes[c] = label_changes.get(c, 0) + 1
        if changes:
            label_only.append(q)
        else:
            same += 1
    L = [f"# 채팅 최종 표시 순위 비교: {a} → {b}", "",
         f"- 순서·후보 같음 {same + len(label_only)} (그중 배지 문구만 다름 {len(label_only)}) · **순서·후보 다름 {len(diff)}**", ""]
    L += [f"- 순서·후보 다름: {q}" for q in diff]
    if label_changes:
        L += ["", "## 배지 문구 변화", ""] + [f"- {x or '없음'} → {y or '없음'}: {n}건" for (x, y), n in label_changes.items()]
    md = ROOT / "docs" / "claude" / f"stage1_display_{a}_vs_{b}.md"
    md.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"저장: {md}  (순서·후보 같음 {same + len(label_only)}, 그중 문구만 다름 {len(label_only)}, 순서·후보 다름 {len(diff)})")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "capture":
        capture(sys.argv[2])
    elif len(sys.argv) >= 4 and sys.argv[1] == "compare":
        compare(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
        sys.exit(1)
