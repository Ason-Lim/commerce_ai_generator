"""/recommendations/nl 최종 표시 순위 스냅샷·비교 (읽기 전용 연결).

1단계 전 정리(뷰 평점·리뷰 점수 제외, 가격 결합 URL 한정)의 전후 순위를 남긴다.
main.natural_language_recommendations를 그대로 부른다 — 응답의 rank가 화면 표시 순위다.

  capture <label>   : var/ranking_snapshots/<label>.json 에 기록
                      db_fallback = pipeline을 강제로 실패시켜 DB 뷰 경로만 (기본)
                      pipeline    = 실제 호출 — 쿠팡·네이버 API 실시간 호출이라 --with-pipeline일 때만
  compare <a> <b>   : 두 스냅샷 비교 → docs/claude/stage1_ranking_compare_<a>_vs_<b>.md

사용 (Mac):
  .venv/bin/python scripts/stage1_ranking_snapshot.py capture before
  (변경 적용)
  .venv/bin/python scripts/stage1_ranking_snapshot.py capture after
  .venv/bin/python scripts/stage1_ranking_snapshot.py compare before after

DB 연결에 default_transaction_read_only=on을 걸어, 추천 호출 중 쓰기가 있으면 오류로 기록된다.
session_id 없이 호출하므로 개인화 가산점은 들어가지 않는다.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SNAP_DIR = ROOT / "var" / "ranking_snapshots"
PRIORITIES = ["ranking", "trust", "quality", "price", "discovery", "exploration", "trust_adaptive"]
EXTRA_QUERIES = ["고당도 사과", "선물용 배", "샤인머스캣"]


def _setup():
    from sqlalchemy import create_engine

    import app.main as m
    from app.core.config import resolve_database_url

    # 앱과 같은 URL, 단 모든 트랜잭션을 읽기 전용으로
    engine = create_engine(
        resolve_database_url(),
        pool_pre_ping=True,
        connect_args={"options": "-c default_transaction_read_only=on"},
    )
    m.engine_lifecycle._engine = engine  # lifespan의 initialize() 대신
    m.bind_engine(engine)                # pipeline이 쓰는 engine_provider에도 같은 엔진
    return m


def _queries(m):
    from sqlalchemy import text

    with m._get_canonical_engine().connect() as c:
        fruits = [r[0] for r in c.execute(text(
            "SELECT DISTINCT fruit_name FROM vw_ai_recommendation_final "
            "WHERE fruit_name IS NOT NULL ORDER BY 1"))]
    return list(dict.fromkeys(fruits + EXTRA_QUERIES))      # 같은 질의 중복 제거 (예: 과일 이름 '샤인머스캣')


def _call(m, q, priority, force_fallback):
    original = m.run_recommendation_pipeline
    if force_fallback:
        def _fail(*_a, **_k):
            raise RuntimeError("forced db fallback (snapshot)")
        m.run_recommendation_pipeline = _fail
    try:
        with redirect_stdout(io.StringIO()):
            result = m.natural_language_recommendations(q=q, priority=priority, session_id=None)
        items = result.get("items") or []
        return {
            "path": str(result.get("recommendation_path")),
            "error": None,
            "items": [
                {
                    "rank": it.get("rank"),
                    "key": it.get("product_url") or it.get("url") or it.get("product_name"),
                    "name": str(it.get("product_name") or it.get("name") or "")[:40],
                    "final_recommendation_score": _num(it.get("final_recommendation_score")),
                    "adaptive_score": _num(it.get("adaptive_score")),
                    "price_per_100g": _num(it.get("price_per_100g")),
                    "price": _num(it.get("price")),
                }
                for it in items
            ],
        }
    except Exception as exc:  # noqa: BLE001
        return {"path": None, "error": f"{type(exc).__name__}: {str(exc)[:200]}", "items": []}
    finally:
        m.run_recommendation_pipeline = original


def _num(v):
    try:
        return None if v is None else round(float(v), 3)
    except (TypeError, ValueError):
        return None


def capture(label: str):
    m = _setup()
    queries = _queries(m)
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                          capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "app"], cwd=ROOT,
                           capture_output=True, text=True).stdout.strip()
    data = {
        "meta": {"label": label, "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "head": head, "app_uncommitted": bool(dirty), "queries": queries,
                 "priorities": PRIORITIES},
        "pipeline": {}, "db_fallback": {},
    }
    # canonical pipeline은 쿠팡·네이버 API를 실시간 호출한다(app/services/market/collector.py).
    # 호출 제한·결과 변동 때문에 기본은 DB fallback만 기록하고, --with-pipeline일 때만 함께 기록.
    with_pipeline = "--with-pipeline" in sys.argv
    data["meta"]["with_pipeline"] = with_pipeline
    for q in queries:
        for p in PRIORITIES:
            k = f"{q}|{p}"
            if with_pipeline:
                data["pipeline"][k] = _call(m, q, p, force_fallback=False)
            data["db_fallback"][k] = _call(m, q, p, force_fallback=True)
    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    out = SNAP_DIR / f"{label}.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    errors = sum(1 for path in ("pipeline", "db_fallback") for v in data[path].values() if v["error"])
    print(f"저장: {out}  (질의 {len(queries)} × 모드 {len(PRIORITIES)}, 오류 {errors})")


def _kind(ra, rb, mode: str = "") -> str:
    la = [i["key"] for i in ra["items"]]
    lb = [i["key"] for i in rb["items"]]
    if la == lb:
        return "same"
    # 순위별 점수 열이 같으면 같은 점수끼리 자리만 바뀐 것. 가격 모드만 100g당 가격이 정렬 키.
    # (탐색·발견 모드의 노출·클릭 수는 스냅샷에 없어 점수 열로만 판정 — 근사)
    if mode == "price":
        sig = lambda r: [(i["price_per_100g"], i["final_recommendation_score"], i["adaptive_score"]) for i in r["items"]]
    else:
        sig = lambda r: [(i["final_recommendation_score"], i["adaptive_score"]) for i in r["items"]]
    if sig(ra) == sig(rb):
        return "tie"
    return "order" if set(la) == set(lb) else "set"


def compare(a: str, b: str):
    A = json.loads((SNAP_DIR / f"{a}.json").read_text(encoding="utf-8"))
    B = json.loads((SNAP_DIR / f"{b}.json").read_text(encoding="utf-8"))
    L = [f"# 최종 표시 순위 비교: {a} → {b}", "",
         f"- {a}: {A['meta']['run_at']} HEAD `{A['meta']['head']}`" + (" +미커밋" if A['meta']['app_uncommitted'] else ""),
         f"- {b}: {B['meta']['run_at']} HEAD `{B['meta']['head']}`" + (" +미커밋" if B['meta']['app_uncommitted'] else ""),
         f"- 질의 {len(set(A['meta']['queries']))}개 × 모드 {len(A['meta']['priorities'])}개 = {len(set(A['meta']['queries'])) * len(A['meta']['priorities'])}, "
         f"각 상위 10, session_id 없음 (질의: {', '.join(dict.fromkeys(A['meta']['queries']))})", ""]
    for path in ("pipeline", "db_fallback"):
        if not A[path] or not B[path]:
            continue
        keys = sorted(set(A[path]) | set(B[path]))
        same = tie_only = order_changed = set_changed = 0
        rows = []
        path_kinds = {}
        for k in keys:
            ra, rb = A[path].get(k), B[path].get(k)
            if not ra or not rb:
                continue
            path_kinds.setdefault((ra["path"], rb["path"]), 0)
            path_kinds[(ra["path"], rb["path"])] += 1
            kind = _kind(ra, rb, k.rsplit("|", 1)[1])
            if kind == "same":
                same += 1
                continue
            if kind == "tie":
                tie_only += 1
            elif kind == "order":
                order_changed += 1
            else:
                set_changed += 1
            la = [i["key"] for i in ra["items"]]
            lb = [i["key"] for i in rb["items"]]
            names = {i["key"]: i["name"] for i in ra["items"] + rb["items"]}
            top_a = " / ".join(names[x][:14] for x in la[:3])
            top_b = " / ".join(names[x][:14] for x in lb[:3])
            out_n = len(set(la) - set(lb))
            label = {"tie": "동점 내 자리", "order": "순서", "set": "구성"}[kind]
            rows.append(f"| {k} | {label} | {out_n} | {top_a} | {top_b} |")
        by_mode = {}
        for k in keys:
            ra, rb = A[path].get(k), B[path].get(k)
            if not ra or not rb:
                continue
            mode = k.rsplit("|", 1)[1]
            by_mode.setdefault(mode, {"same": 0, "tie": 0, "order": 0, "set": 0})[_kind(ra, rb, mode)] += 1
        L += [f"## {path}", "",
              f"- 같음 {same} · 동점 내 자리만 {tie_only} · 순서 바뀜 {order_changed} · 구성 바뀜 {set_changed}"
              f" (총 {same + tie_only + order_changed + set_changed})",
              "- '동점 내 자리': 순위별 점수 열(가격 모드는 100g당 가격 포함)은 같고 같은 점수끼리 자리만 바뀐 경우",
              "- 경로(전→후): " + ", ".join(f"{x}→{y} {n}" for (x, y), n in path_kinds.items()), "",
              "| 모드 | 같음 | 동점 내 자리 | 순서 | 구성 |", "|---|---|---|---|---|"]
        L += [f"| {m} | {c['same']} | {c['tie']} | {c['order']} | {c['set']} |" for m, c in by_mode.items()]
        L += [""]
        errs = [(k, B[path][k]["error"]) for k in keys if B[path].get(k, {}).get("error")]
        if errs:
            L += [f"- {b} 오류 {len(errs)}건 (예: {errs[0][0]} — {errs[0][1]})", ""]
        if rows:
            L += ["| 질의·모드 | 변화 | 빠진 상품 | 전 상위 3 | 후 상위 3 |", "|---|---|---|---|---|"] + rows[:60] + [""]
    out = ROOT / "docs" / "claude" / f"stage1_ranking_compare_{a}_vs_{b}.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print(f"저장: {out}")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "capture":
        capture(sys.argv[2])
    elif len(sys.argv) >= 4 and sys.argv[1] == "compare":
        compare(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
        sys.exit(1)
