"""score_engine 변경 전후 점수·순위 비교 (읽기 전용).

변경 전 = git 기준 커밋(기본 26776c6, 0단계 기준선)의 score_engine.py
변경 후 = 작업 트리의 score_engine.py

사용:
  python scripts/compare_score_engine_versions.py                 # 대표 입력(고정 fixture)
  python scripts/compare_score_engine_versions.py --db --limit 300 # Mac: DB 후보(읽기 전용 조회)
  옵션 --base <커밋>, --out <폴더>

범위: 엔진 단계(calculate_ai_scores → calculate_mode_score)의 정렬만 비교한다.
main.py·explain.choose의 필터·병합·역할 선택 이후 최종 표시 순위는 이 스크립트로 확인되지 않는다.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

ENGINE_PATH = "app/services/recommendation/score_engine.py"
PRIORITIES = ["trust", "quality", "price", "mix", "discovery", "exploration",
              "quality_adaptive", "price_adaptive"]

# 각 변경점을 드러내는 대표 입력 (실데이터 아님)
FIXTURES = [
    {"_id": "A_scraped_rating", "_note": "페이지 보강 평점·리뷰 (검증 표시 없음)",
     "rating": 4.9, "review_count": 12000, "review_source": "kurly_page",
     "brix": 13, "price_per_100g": 700},
    {"_id": "B_verified_rating", "_note": "A와 같지만 검증 표시 True",
     "rating": 4.9, "review_count": 12000, "rating_score_usable": True,
     "brix": 13, "price_per_100g": 700},
    {"_id": "C_click_reaction", "_note": "평점 없음, 클릭·CTR 반응 높음",
     "click_count": 25, "ctr_pct": 22, "impression_count": 120,
     "final_recommendation_label": "사용자 반응 우수 추천", "brix": 13, "price_per_100g": 800},
    {"_id": "D_quality_cap", "_note": "고당도 + 검증 평점 (품질 100 상한)",
     "brix": 17, "rating": 4.9, "review_count": 11000, "rating_score_usable": True,
     "price_per_100g": 1300},
    {"_id": "E_price_cap", "_note": "저가 + 할인 + 가격하락 (가격 100 상한)",
     "price_per_100g": 350, "discount_rate": 20, "price_drop_boost": 10, "brix": 12},
    {"_id": "F_zero_confidence", "_note": "Identity 캐시 신뢰도 0 (이전엔 50으로 처리)",
     "_brix_confidence": 0, "_price_confidence": 0, "brix": 15, "price_per_100g": 600},
    {"_id": "G_new_item", "_note": "노출·클릭 없는 신규 상품 (탐색 모드)",
     "impression_count": 0, "click_count": 0, "brix": 14, "price_per_100g": 650},
    {"_id": "H_plain", "_note": "보통 상품",
     "brix": 14, "price_per_100g": 900, "click_count": 3, "ctr_pct": 4, "impression_count": 80},
]


def _load_module(name: str, source: str):
    tmp = Path(tempfile.mkdtemp()) / f"{name}.py"
    tmp.write_text(source, encoding="utf-8")
    spec = importlib.util.spec_from_file_location(name, tmp)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_engines(base: str):
    old_src = subprocess.run(["git", "show", f"{base}:{ENGINE_PATH}"], cwd=ROOT,
                             check=True, capture_output=True, text=True).stdout
    new_src = (ROOT / ENGINE_PATH).read_text(encoding="utf-8")
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                          capture_output=True, text=True).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain", "--", ENGINE_PATH], cwd=ROOT,
                                capture_output=True, text=True).stdout.strip())
    return (_load_module("score_engine_before", old_src),
            _load_module("score_engine_after", new_src),
            {"base": base, "head": head, "engine_uncommitted_changes": dirty})


def _score(engine, item, priority):
    base = str(priority).replace("_adaptive", "")
    try:
        scores = engine.calculate_ai_scores(dict(item), priority=priority)
        mode = engine.calculate_mode_score(dict(item), dict(scores), base, search_context=None)
        return {"scores": scores, "mode_score": round(float(mode), 3), "error": None}
    except Exception as exc:  # 이전 엔진의 탐색 모드 NameError 등을 기록
        return {"scores": None, "mode_score": None, "error": f"{type(exc).__name__}: {exc}"}


def _ranks(results):
    ok = [(pid, r["mode_score"]) for pid, r in results.items() if r["mode_score"] is not None]
    ordered = sorted(ok, key=lambda x: (-x[1], x[0]))
    return {pid: i + 1 for i, (pid, _) in enumerate(ordered)}


def compare(items, old, new):
    report = {}
    for priority in PRIORITIES:
        before = {it["_id"]: _score(old, it, priority) for it in items}
        after = {it["_id"]: _score(new, it, priority) for it in items}
        rb, ra = _ranks(before), _ranks(after)
        rows = []
        for it in items:
            pid = it["_id"]
            rows.append({
                "id": pid, "note": it.get("_note", ""),
                "rank_before": rb.get(pid), "rank_after": ra.get(pid),
                "mode_before": before[pid]["mode_score"], "mode_after": after[pid]["mode_score"],
                "scores_before": before[pid]["scores"], "scores_after": after[pid]["scores"],
                "error_before": before[pid]["error"], "error_after": after[pid]["error"],
            })
        report[priority] = rows
    return report


def load_db_items(limit: int):
    from sqlalchemy import create_engine, text
    from app.core.config import DATABASE_URL

    eng = create_engine(DATABASE_URL, pool_pre_ping=True)
    with eng.connect() as conn:
        conn.execute(text("SET TRANSACTION READ ONLY"))
        rows = conn.execute(text("SELECT * FROM vw_ai_recommendation_final LIMIT :n"),
                            {"n": limit}).mappings().all()
    items = []
    for i, row in enumerate(rows):
        item = dict(row)
        item["_id"] = str(item.get("id") or item.get("product_id") or f"row{i}")
        item["_note"] = str(item.get("product_name") or "")[:40]
        items.append(item)
    return items


def _fmt(v):
    return "-" if v is None else (f"{v:g}" if isinstance(v, float) else str(v))


def to_markdown(report, meta, source, top_n=20):
    lines = [
        "# score_engine 변경 전후 점수·순위 비교",
        "",
        f"- 실행: {meta['run_at']}  ·  입력: {source} ({meta['n_items']}건)",
        f"- 변경 전: `{meta['base']}`  ·  변경 후: HEAD `{meta['head']}`"
        + ("  (+ 미커밋 수정 포함)" if meta["engine_uncommitted_changes"] else ""),
        "- 범위: 엔진 단계 정렬만. main.py·explain.choose 이후 최종 표시 순위는 별도 확인 필요.",
        "",
        "## 요약 (모드별 순위가 바뀐 상품 수)",
        "",
        "| 모드 | 순위 변화 | 이전 오류 | 이후 오류 |",
        "|---|---|---|---|",
    ]
    for priority, rows in report.items():
        changed = sum(1 for r in rows if r["rank_before"] != r["rank_after"])
        eb = sum(1 for r in rows if r["error_before"])
        ea = sum(1 for r in rows if r["error_after"])
        lines.append(f"| {priority} | {changed}/{len(rows)} | {eb} | {ea} |")

    for priority, rows in report.items():
        lines += ["", f"## {priority}", "",
                  "| 상품 | 설명 | 순위 전→후 | 모드점수 전→후 | quality | trust | price | popularity | total |",
                  "|---|---|---|---|---|---|---|---|---|"]
        shown = sorted(rows, key=lambda r: (r["rank_after"] or 10**9))[:top_n]
        for r in shown:
            sb, sa = r["scores_before"] or {}, r["scores_after"] or {}
            cells = [f"{_fmt(sb.get(k))}→{_fmt(sa.get(k))}"
                     for k in ("quality", "trust", "price", "popularity", "total")]
            mode_b = r["error_before"].split(":")[0] if r["error_before"] else _fmt(r["mode_before"])
            lines.append(f"| {r['id']} | {r['note']} | {_fmt(r['rank_before'])}→{_fmt(r['rank_after'])} "
                         f"| {mode_b}→{_fmt(r['mode_after'])} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="26776c6")
    parser.add_argument("--db", action="store_true", help="vw_ai_recommendation_final 읽기 전용 조회")
    parser.add_argument("--limit", type=int, default=300)
    parser.add_argument("--out", default="docs/claude")
    args = parser.parse_args()

    old, new, meta = load_engines(args.base)
    if args.db:
        items, source, suffix = load_db_items(args.limit), "DB vw_ai_recommendation_final", "db"
    else:
        items, source, suffix = FIXTURES, "대표 입력 fixture", "fixture"

    meta.update(run_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                n_items=len(items), source=source)
    report = compare(items, old, new)

    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    stem = f"score_engine_compare_{suffix}_{datetime.now().strftime('%Y-%m-%d')}"
    (out / f"{stem}.json").write_text(
        json.dumps({"meta": meta, "report": report}, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8")
    (out / f"{stem}.md").write_text(to_markdown(report, meta, source), encoding="utf-8")
    print(f"저장: {out / stem}.md / .json")


if __name__ == "__main__":
    main()
