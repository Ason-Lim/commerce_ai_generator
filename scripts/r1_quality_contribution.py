"""R1 품질 기여 검증 (오프라인): 같은 쿠팡 후보로 '품질+가격'(실제) 순위와 '가격만' 순위를 비교.

입력: var/ranking_snapshots/r1_canonical_sample.json (r1_canonical_evidence_sample.py 결과, API 다시 부르지 않음)
- 실제 순위: canonical final_score (가용 근거 quality·price 의 가중 합)
- 가격만: price 구성요소 내림차순 (동점은 실제 순위 순)
- 상위 3·5 진입·이탈과 그 차이를 만든 quality 값, 상품명에서 읽힌 품질 근거를 남긴다

사용: python scripts/r1_quality_contribution.py
결과: docs/claude/r1_quality_contribution_<날짜>.md
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    data = json.loads((ROOT / "var" / "ranking_snapshots" / "r1_canonical_sample.json").read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    L = ["# R1 품질 기여 검증 — 같은 쿠팡 후보, '품질+가격' vs '가격만'", "",
         f"- 입력: r1_canonical_sample.json ({data['run_at']}), 쿠팡 API 다시 부르지 않음", ""]
    summary = []
    detail = []
    for r in data["runs"]:
        items = [it for it in r["items"] if it.get("canonical_score")]
        if len(items) < 3:
            continue
        actual = sorted(items, key=lambda it: it["rank"])
        price_only = sorted(actual, key=lambda it: -(it["canonical_score"]["components"].get("price") or 0))
        qs = [it["canonical_score"]["components"].get("quality") for it in actual]
        w = actual[0]["canonical_score"].get("weights") or {}
        row = {"key": f"{r['query']}|{r['mode']}", "weights": {k: round(v, 2) for k, v in w.items()},
               "quality_values": sorted({q for q in qs if q is not None}),
               "same_order": [i["name"] for i in actual] == [i["name"] for i in price_only]}
        for k in (1, 3, 5):
            a = [i["name"] for i in actual[:k]]
            p = [i["name"] for i in price_only[:k]]
            row[f"top{k}_same_set"] = set(a) == set(p)
        summary.append(row)
        if not row["same_order"]:
            moved = []
            for pos, it in enumerate(actual[:5], start=1):
                ppos = [i["name"] for i in price_only].index(it["name"]) + 1
                if ppos != pos:
                    c = it["canonical_score"]["components"]
                    moved.append(f"- {it['name']}: 실제 {pos}위 / 가격만 {ppos}위 — quality {c.get('quality')} · price {c.get('price')}")
            detail.append((row["key"], moved))
    n = len(summary)
    L += ["## 요약", "",
          f"- 결과 {n}개 중 순서 완전히 같음 {sum(s['same_order'] for s in summary)} · "
          f"1위 같음 {sum(s['top1_same_set'] for s in summary)} · 상위 3 구성 같음 {sum(s['top3_same_set'] for s in summary)} · "
          f"상위 5 구성 같음 {sum(s['top5_same_set'] for s in summary)}", "",
          "| 질의·모드 | 가중치(실제) | quality 값 종류 | 순서 같음 | 1위 | 상위3 | 상위5 |", "|---|---|---|---|---|---|---|"]
    yn = lambda b: "같음" if b else "**다름**"  # noqa: E731
    for s in summary:
        L.append(f"| {s['key']} | {s['weights']} | {s['quality_values']} | {yn(s['same_order'])} | "
                 f"{yn(s['top1_same_set'])} | {yn(s['top3_same_set'])} | {yn(s['top5_same_set'])} |")
    L += ["", "## 순서가 다른 결과 — 상위 5 안에서 자리가 바뀐 상품", ""]
    for key, moved in detail:
        L += [f"### {key}"] + (moved or ["- 상위 5 밖에서만 다름"]) + [""]
    L += ["## quality 값의 출처 (코드 확인, 2026-11-10)", "",
          "- `provider.build_score_components`: quality = `fruit_quality_score` → `food_intelligence_score` → `v7_quality_score` 중 처음 있는 값",
          "- `food_intelligence_engine`: 식품 분류 기본점(과일·채소·고기·수산·유제품 55, 가공 50, 모름 45) + 상품명 속성(유기농·비건 +8, 선물 +5) + 인증 표기 점수×0.4; 과일이면 과일 품질 점수(당도 표기 등)와 45:55로 섞음",
          "- 즉 quality 는 **판매자 상품명 표기와 분류에서 나온 점수**이고, 검증된 품질 근거가 아님 (근거 판정 정책상 title_parse 값은 점수 사용 '차단' 대상)",
          ""]
    out = ROOT / "docs" / "claude" / f"r1_quality_contribution_{now.astimezone().strftime('%Y-%m-%d')}.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print(f"저장: {out}  (결과 {n}, 순서 같음 {sum(s['same_order'] for s in summary)}, "
          f"1위 같음 {sum(s['top1_same_set'] for s in summary)})")


if __name__ == "__main__":
    main()
