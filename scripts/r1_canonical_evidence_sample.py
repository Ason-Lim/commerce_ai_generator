"""R1 표본 (주 경로 canonical · 쿠팡 실시간): 점수 근거가 실제로 얼마나 채워지고 쓰이는가.

질의마다 run_recommendation_pipeline 을 한 번 부른다(쿠팡 파트너스 API 실시간 호출 — 호출 수 제한·간격 둠).
결과 후보의 canonical_score(2026-11-10부터 응답에 실림)로
  - 구성요소(quality·price·trust·popularity·market·identity)별 '값이 채워진 비율'과 '실제 순위 계산에 쓰인 비율'(가중치>0)
  - insufficient_evidence 경고 비율, 최종 점수 분포(서로 다른 값 수)
  - 가설 점검: 최종 순위와 가격 순위의 상관(스피어만) — '가격 + 쿠팡 검색 순서가 사실상의 순위'인지
를 센다. DB에는 쓰지 않는다.

사용 (Mac): .venv/bin/python scripts/r1_canonical_evidence_sample.py [--max-calls 12] [--gap 3]
결과: docs/claude/r1_canonical_evidence_<날짜>.md (+ var/ranking_snapshots/r1_canonical_sample.json)
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import time
from collections import Counter
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

QUERIES = ["사과", "샤인머스캣", "한우 등심", "고등어", "귤", "우유"]
MODES = ["ranking", "price"]
COMPONENTS = ("quality", "price", "trust", "popularity", "market", "identity")


def _spearman(a, b):
    n = len(a)
    if n < 3:
        return None
    ra = {v: i for i, v in enumerate(sorted(range(n), key=lambda i: a[i]))}
    rb = {v: i for i, v in enumerate(sorted(range(n), key=lambda i: b[i]))}
    d2 = sum((ra[i] - rb[i]) ** 2 for i in range(n))
    return round(1 - 6 * d2 / (n * (n * n - 1)), 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-calls", type=int, default=12)
    ap.add_argument("--gap", type=float, default=3.0)
    args = ap.parse_args()

    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except ImportError:
        pass
    from sqlalchemy import create_engine

    from app.core.config import resolve_database_url
    from app.db.engine_provider import bind_engine
    from app.services.recommendation_pipeline import run_recommendation_pipeline

    # 파이프라인이 DB를 읽는 단계가 있으면 읽기 전용 연결로 (쓰기는 오류가 됨)
    bind_engine(create_engine(resolve_database_url(), pool_pre_ping=True,
                              connect_args={"options": "-c default_transaction_read_only=on"}))

    now = datetime.now(timezone.utc)
    runs, calls = [], 0
    for q in QUERIES:
        for mode in MODES:
            if calls >= args.max_calls:
                break
            if calls:
                time.sleep(args.gap)
            calls += 1
            t0 = time.time()
            try:
                with redirect_stdout(io.StringIO()):
                    res = run_recommendation_pipeline(q=q, priority=mode, session_id=None, limit=10)
                err = None
            except Exception as exc:  # noqa: BLE001
                res, err = {}, f"{type(exc).__name__}: {str(exc)[:160]}"
            items = res.get("items") or []
            runs.append({
                "query": q, "mode": mode, "error": err, "seconds": round(time.time() - t0, 1),
                "warnings": res.get("warnings"),
                "items": [{"rank": it.get("rank"), "name": str(it.get("product_name") or it.get("title") or "")[:40],
                           "mall": it.get("mall_name") or it.get("platform") or it.get("platform_name"),
                           "price": it.get("price"), "canonical_score": it.get("canonical_score")} for it in items],
            })

    filled, used, total = Counter(), Counter(), 0
    insufficient, distinct_scores, corr = 0, [], []
    for r in runs:
        scores = []
        for it in r["items"]:
            cs = it.get("canonical_score") or {}
            if not cs:
                continue
            total += 1
            for c in cs.get("components") or {}:
                filled[c] += 1
            for c, w in (cs.get("weights") or {}).items():
                if w:
                    used[c] += 1
            if "insufficient_evidence" in (cs.get("warnings") or []):
                insufficient += 1
            scores.append(cs.get("final_score"))
        distinct_scores.append(len(set(scores)))
        priced = [(it["rank"], it["price"]) for it in r["items"] if isinstance(it.get("price"), (int, float))]
        if len(priced) >= 3:
            corr.append((f"{r['query']}|{r['mode']}", _spearman([p[0] for p in priced], [p[1] for p in priced])))

    out_json = ROOT / "var" / "ranking_snapshots" / "r1_canonical_sample.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps({"run_at": now.isoformat(timespec="seconds"), "runs": runs}, ensure_ascii=False,
                                   indent=1, default=str), encoding="utf-8")

    L = ["# R1 표본 — 주 경로(canonical, 쿠팡 실시간) 점수 근거", "",
         f"- 실행: {now.isoformat(timespec='seconds')} · 호출 {calls}회(간격 {args.gap:g}초) · 후보 {total}개",
         f"- 오류 {sum(1 for r in runs if r['error'])}회" + "".join(f" · {r['query']}|{r['mode']}: {r['error']}" for r in runs if r["error"]),
         "", "## 구성요소별 채움·사용 비율", "", "| 구성요소 | 값 있음 | 순위 계산에 쓰임 |", "|---|---|---|"]
    for c in COMPONENTS:
        L.append(f"| {c} | {filled[c]}/{total} ({(filled[c] / total * 100) if total else 0:.0f}%) | "
                 f"{used[c]}/{total} ({(used[c] / total * 100) if total else 0:.0f}%) |")
    L += ["", f"- 근거 부족(insufficient_evidence) 후보: {insufficient}/{total}",
          f"- 질의별 서로 다른 최종 점수 수(10개 중): {distinct_scores}", "",
          "## 가설 점검: 최종 순위 ↔ 가격 순위 (스피어만, 1에 가까울수록 '싼 순서')", ""]
    L += [f"- {k}: {v}" for k, v in corr] or ["- 계산할 수 있는 결과 없음"]
    used_names = [c for c in COMPONENTS if used[c]]
    L += ["", "## 해석 메모", "",
          "- '값 있음'이 낮은 구성요소는 점수에 들어가지 않는다(가용 근거만으로 가중치 재배분) — 설계대로",
          f"- 이번 표본에서 순위 계산에 쓰인 구성요소: **{', '.join(used_names) or '없음'}** "
          f"(나머지 {', '.join(c for c in COMPONENTS if not used[c]) or '없음'}는 0건)",
          "- 가격 순위와의 상관이 높으면 순위는 사실상 가격순 — 품질 기여는 scripts/r1_quality_contribution.py 로 따로 확인",
          "- 표본이 작아(질의 6 × 모드 2) 경향 확인용. 쿠팡 검색 순서 자체와의 비교는 원래 순서가 응답에 없어 못 함", ""]
    out = ROOT / "docs" / "claude" / f"r1_canonical_evidence_{now.astimezone().strftime('%Y-%m-%d')}.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print(f"저장: {out}  (호출 {calls}, 후보 {total})")


if __name__ == "__main__":
    main()
