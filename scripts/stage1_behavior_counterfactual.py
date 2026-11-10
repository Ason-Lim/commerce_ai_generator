"""행동 가점을 뺀 순위와 지금 순위 비교 (1단계, 읽기 전용 · 기록·점수는 바꾸지 않음).

DB 예비 경로의 행동 기반 가점 6종 (2026-11-10 저장소·DB 정의 확인):
  뷰 안   click_boost (vw_ai_adaptive_recommendation)          ← product_click_log
          ctr_boost · rank_ctr_boost (vw_ai_adaptive_recommendation_v3) ← recommendation_impression_log + product_click_log
          ctr_feedback_boost (vw_product_ctr_boost)             ← recommendation_impression_log + product_click_log
  main.py product_boost (vw_product_boost ← vw_product_performance) ← impression_log + product_click_log
          mode_boost (vw_recommendation_mode_boost ← vw_recommendation_feedback) ← impression_log
            (mode_boost 는 같은 모드의 모든 상품에 같은 값 → 일반 정렬 순서에는 영향 없음)
행동 기록은 모두 2026-07-16 이후 새 기록이 없음 (docs/claude/stage1_impression_audit_2026-11-10.md).

비교 방법
  1. db_fallback_recommendations 의 SQL 에서 LIMIT 10 만 크게 바꿔 후보 전체를 받는다 (같은 SQL·같은 DB).
  2. 지금 순위: main.py 와 같은 규칙(SQL 정렬 → 상위 10 → Python 정렬)으로 다시 만든다.
     실제 LIMIT 10 결과와 같은지 먼저 확인한다 (재현 검사).
  3. 행동 가점 제외 순위: final' = round(min(100, trust_first + price_drop_boost), 1),
     정렬값' = final' + context_boost (+ 개인화는 session_id 없음 → 0), product_boost·mode_boost = 0.
  탐색·발견 모드는 정렬 자체가 노출·클릭 수 기반이라 '제외 순위'를 정의할 수 없어 제외한다.

사용 (Mac): .venv/bin/python scripts/stage1_behavior_counterfactual.py
결과: docs/claude/stage1_behavior_counterfactual_<날짜>.md (+ var/ranking_snapshots/behavior_counterfactual.json)
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

MODES = ["ranking", "trust", "quality", "price", "trust_adaptive"]
EXTRA_QUERIES = ["고당도 사과", "선물용 배"]
BIG = 100000


def _setup():
    from sqlalchemy import create_engine

    import app.main as m
    from app.core.config import resolve_database_url

    engine = create_engine(resolve_database_url(), pool_pre_ping=True,
                           connect_args={"options": "-c default_transaction_read_only=on"})
    m.engine_lifecycle._engine = engine
    m.bind_engine(engine)
    return m


def _fetch(m, q, priority, limit_all: bool):
    original = m.text
    if limit_all:
        def patched(sql, *a, **k):
            if "vw_ai_recommendation_final" in sql:
                sql = sql.replace("LIMIT 10", f"LIMIT {BIG}")
            return original(sql, *a, **k)
        m.text = patched
    try:
        with redirect_stdout(io.StringIO()):
            return m.db_fallback_recommendations(q=q, priority=priority, session_id=None)["items"]
    finally:
        m.text = original


def _f(v, d=0.0):
    try:
        return float(v) if v is not None else d
    except (TypeError, ValueError):
        return d


def _order(items, priority, *, behavior: bool):
    """main.py 규칙 재현: SQL ORDER BY → 상위 10 → Python 정렬. behavior=False 면 행동 가점 6종을 뺀 값으로."""
    adaptive = priority.endswith("_adaptive")
    base = priority.replace("_adaptive", "")
    rows = []
    for it in items:
        tf, pd = _f(it.get("view_trust_first_score")), _f(it.get("price_drop_boost"))
        if behavior:
            final = _f(it.get("final_recommendation_score"))
            mb, pb = _f(it.get("mode_boost")), _f(it.get("product_boost"))
            sort_val = _f(it.get("adaptive_score"))
        else:
            final = round(min(100.0, tf + pd), 1)
            mb = pb = 0.0
            # 행동 가점이 아닌 main.py 가산(문맥) + 개인화(session_id 없음 → 0)는 그대로 둔다
            sort_val = final + sum(_f(it.get(k)) for k in ("context_boost", "personal_boost", "fruit_affinity_boost",
                                                           "user_product_boost", "revisit_boost",
                                                           "session_context_boost"))
        rows.append({"key": it.get("product_url"), "name": str(it.get("product_name") or "")[:30],
                     "final": final, "sql_key": final + mb + pb if adaptive else final, "sort": sort_val,
                     "p100": it.get("price_per_100g") or 999999, "item": it})
    rows.sort(key=lambda r: r["key"] or "")
    rows.sort(key=lambda r: -r["sql_key"])                      # ORDER BY … DESC, r.product_url
    top = rows[:10]
    if base == "price":
        top = sorted(top, key=lambda r: (r["p100"], -r["final"], -r["sort"]))
    else:
        top = sorted(top, key=lambda r: r["sort"], reverse=True)
    return top


def _boosts(it):
    tf, ad, v3 = (_f(it.get(k), None) for k in ("view_trust_first_score", "view_adaptive_score", "view_adaptive_score_v3"))
    return {
        "click": None if ad is None or tf is None else round(ad - tf, 2),
        "ctr": _f(it.get("view_ctr_boost")), "rank_ctr": _f(it.get("view_rank_ctr_boost")),
        "ctr_feedback": _f(it.get("ctr_feedback_boost")), "product": _f(it.get("product_boost")),
        "mode": _f(it.get("mode_boost")),
    }


def main():
    m = _setup()
    from sqlalchemy import text

    with m._get_canonical_engine().connect() as c:
        fruits = [r[0] for r in c.execute(text("SELECT DISTINCT fruit_name FROM vw_ai_recommendation_final "
                                               "WHERE fruit_name IS NOT NULL ORDER BY 1"))]
    queries = list(dict.fromkeys(fruits + EXTRA_QUERIES))
    now = datetime.now(timezone.utc)
    results, repro_fail = [], []
    for q in queries:
        for p in MODES:
            full = _fetch(m, q, p, limit_all=True)
            actual = [it.get("product_url") for it in _fetch(m, q, p, limit_all=False)]
            cur = _order(full, p, behavior=True)
            cf = _order(full, p, behavior=False)
            cur_keys, cf_keys = [r["key"] for r in cur], [r["key"] for r in cf]
            if cur_keys != actual:
                repro_fail.append(f"{q}|{p}")
            entered = [r for r in cf if r["key"] not in cur_keys]
            left = [r for r in cur if r["key"] not in cf_keys]
            moves = []
            for i, r in enumerate(cur, start=1):
                if r["key"] in cf_keys:
                    j = cf_keys.index(r["key"]) + 1
                    if i != j:
                        moves.append({"name": r["name"], "now": i, "without": j, "boosts": _boosts(r["item"])})
            results.append({
                "query": q, "mode": p, "candidates": len(full), "same": cur_keys == cf_keys,
                "same_set": set(cur_keys) == set(cf_keys),
                "left": [{"name": r["name"], "now": cur_keys.index(r["key"]) + 1, "boosts": _boosts(r["item"])} for r in left],
                "entered": [{"name": r["name"], "without": cf_keys.index(r["key"]) + 1, "boosts": _boosts(r["item"])}
                            for r in entered],
                "moves": moves,
                "with_behavior_in_top10": sum(1 for r in cur if any(v for k, v in _boosts(r["item"]).items()
                                                                    if k != "mode" and v)),
            })

    out_json = ROOT / "var" / "ranking_snapshots" / "behavior_counterfactual.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps({"run_at": now.isoformat(timespec="seconds"), "results": results,
                                    "repro_fail": repro_fail}, ensure_ascii=False, indent=1, default=str),
                        encoding="utf-8")

    n = len(results)
    same = sum(r["same"] for r in results)
    same_set = sum(r["same_set"] and not r["same"] for r in results)
    changed_set = n - same - same_set
    L = ["# 행동 가점 6종을 뺀 순위 비교 (DB 예비 경로, 읽기 전용)", "",
         f"- 실행: {now.isoformat(timespec='seconds')} · 질의 {len(queries)} × 모드 {len(MODES)} = {n}, 상위 10, session_id 없음",
         "- 탐색·발견 모드는 정렬 자체가 노출·클릭 수 기반이라 제외",
         f"- 재현 검사(지금 순위를 규칙으로 다시 만든 결과 = 실제 상위 10): "
         + ("**모두 일치**" if not repro_fail else f"**불일치 {len(repro_fail)}건** — {', '.join(repro_fail[:6])} (아래 결과는 참고만)"),
         "", "## 요약", "",
         f"- 순위 그대로 {same} · 순서만 바뀜 {same_set} · **상위 10 구성 바뀜 {changed_set}** (총 {n})", "",
         "| 모드 | 그대로 | 순서만 | 구성 | 상위 10 안 행동 가점 상품 수(평균) |", "|---|---|---|---|---|"]
    for p in MODES:
        rs = [r for r in results if r["mode"] == p]
        L.append(f"| {p} | {sum(r['same'] for r in rs)} | {sum(r['same_set'] and not r['same'] for r in rs)} | "
                 f"{sum(not r['same_set'] for r in rs)} | {sum(r['with_behavior_in_top10'] for r in rs) / max(1, len(rs)):.1f} |")
    L += ["", "## 바뀐 질의 상세 (가점: click·ctr·rank_ctr·ctr_feedback·product)", ""]
    fmt = lambda b: " ".join(f"{k} {v:g}" for k, v in b.items() if k != "mode" and v)  # noqa: E731
    for r in results:
        if r["same"]:
            continue
        L.append(f"### {r['query']} · {r['mode']} (후보 {r['candidates']})")
        for x in r["left"]:
            L.append(f"- 빠짐: {x['name']} (지금 {x['now']}위) — {fmt(x['boosts']) or '가점 없음'}")
        for x in r["entered"]:
            L.append(f"- 들어옴: {x['name']} (제외 시 {x['without']}위) — {fmt(x['boosts']) or '가점 없음'}")
        for x in r["moves"][:6]:
            L.append(f"- 이동: {x['name']} {x['now']}→{x['without']}위 — {fmt(x['boosts']) or '가점 없음'}")
        L.append("")
    L += ["## 해석 주의", "",
          "- 행동 기록은 2026-07-16 이후 새 기록이 없고(Streamlit 시절), 노출 분모(recommendation_impression_log)는 2026-05-30에 끊김 → 이 가점은 **과거 행동 가점 · 실제 노출 미검증**",
          "- 이 비교는 순위를 바꾸지 않는다. 가점을 뺄지는 점수 연구(R3)에서 결정",
          ""]
    out = ROOT / "docs" / "claude" / f"stage1_behavior_counterfactual_{now.astimezone().strftime('%Y-%m-%d')}.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print(f"저장: {out}" + (f"  (재현 불일치 {len(repro_fail)}건)" if repro_fail else "  (재현 검사 일치)"))


if __name__ == "__main__":
    main()
