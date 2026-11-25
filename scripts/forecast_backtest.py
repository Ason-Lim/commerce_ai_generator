"""예측 백테스트 실행 (2026-11-24, 검토 반영) — 기준선 3종 + 선행 곡선 탐색기(전체·반복만).

    uv run python scripts/forecast_backtest.py 2025-01-06 2025-10-27                  # Q1, 매주
    uv run python scripts/forecast_backtest.py 2025-01-06 2025-10-27 --q1p            # Q1′: 최근 28일 안 100위 안이던 키워드 제외
    uv run python scripts/forecast_backtest.py 2025-01-06 2025-10-27 --min-share 0.9  # 미래 관측률 기준을 높여 견주기
    uv run python scripts/forecast_backtest.py 2025-01-06 2025-10-27 --no-explorer --step 14

순위 폴더는 NAVER_DAILY_RANK_DIR(.env). 모든 기간을 판정할 수 있는 예측일만 쓴다(같은 평가일 비교).
결과 표 + 건너뛴 예측일(달별·이유) + 합집합으로도 놓친 주요 상승을 출력하고 var/forecast/ 에 저장(커밋하지 않음).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NAMES = {"recent": "최근 유지", "last_year": "전년 같은 주", "last_year_lunar": "전년 기준*", "event_rel": "행사 상대일", "explorer": "탐색기",
         "explorer_repeat": "탐색기(반복만)"}  # fmt: skip


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="예측 백테스트")
    ap.add_argument("start")
    ap.add_argument("end")
    ap.add_argument("--step", type=int, default=7)
    ap.add_argument("--no-explorer", action="store_true")
    ap.add_argument("--q1p", action="store_true", help="Q1′ — 최근 28일 안 100위 안이던 키워드 제외")
    ap.add_argument("--min-share", type=float, default=0.6, help="미래 관측일 최소 비율(기본 0.6)")
    args = ap.parse_args(argv)
    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
    except ImportError:
        pass
    from app.services.trends import period
    from app.services.trends.forecast import backtest as bt

    rank_dir, kind = period.rank_dir_from_env()
    if rank_dir is None:
        print("순위 폴더가 없어요 — .env 의 NAVER_DAILY_RANK_DIR 를 확인해 주세요")
        return 1
    q = "q1p" if args.q1p else "q1"
    res = bt.run(rank_dir, dt.date.fromisoformat(args.start), dt.date.fromisoformat(args.end), step=args.step,
                 methods=bt.BASELINES if args.no_explorer else bt.METHODS, question=q, min_share=args.min_share)  # fmt: skip
    print(f"순위 폴더 {rank_dir} ({kind}) · 질문 {'Q1′' if args.q1p else 'Q1'} · 미래 관측률 ≥ {args.min_share:.0%}")
    print(f"예측일 {res['dates']}개 판정 · 건너뜀 {len(res['skipped'])} (달별 {res['skipped_by_month']})")
    reasons: dict[str, int] = {}
    for x in res["skipped"]:
        reasons[x["why"]] = reasons.get(x["why"], 0) + 1
    for why, n in reasons.items():
        print(f"  - {why}: {n}")
    print(f"판정한 예측일: {', '.join(d[5:] for d in res['evaluated'])}")
    pc = lambda v: "—" if v is None else f"{v * 100:.1f}%"  # noqa: E731
    print(f"\n{'방법':<10} {'기간':>4} {'정답':>6} {'예측':>6} {'적중':>5} {'정밀도':>7} {'재현율':>7} {'재현(기존)':>9} "
          f"{'상위20':>7} {'상위20·7일+':>10} {'선행*':>5} {'놓친주요':>8}")  # fmt: skip
    for m, byh in res["metrics"].items():
        for h, x in byh.items():
            print(f"{NAMES.get(m, m):<10} {h:>3}일 {x['n_true']:>6} {x['n_pred']:>6} {x['hits']:>5} {pc(x['precision']):>7} "
                  f"{pc(x['recall']):>7} {pc(x['recall_known']):>9} {pc(x['top20_precision']):>7} "
                  f"{pc(x['top20_lead7']):>10} {x['lead_median'] if x['lead_median'] is not None else '—':>5} "
                  f"{pc(x['major_missed']):>8}" + (f"  추가 적중 {x['extra_hits']}" if "extra_hits" in x else ""))  # fmt: skip
    print("\n못 맞힌 이유 — 28일 · 제출 상위 20 기준 (7일+ 앞서 적중 / 늦게 적중 / 시점 어긋남 / 작년 키워드 안 옴):")
    for m, byh in res["metrics"].items():
        b = (byh.get(28) or {}).get("miss_breakdown")
        if b and b["lead"] is not None:
            print(f"  {NAMES.get(m, m):<10} {pc(b['lead']):>6} / {pc(b['late']):>6} / {pc(b['timing']):>6} / {pc(b['gone']):>6}")
    print("\n합집합(모든 방법)으로도 놓친 주요 상승(50위 안까지):")
    for h, u in res["union"].items():
        print(
            f"  {h}일: {pc(u['major_missed_all'])} (주요 상승 {u['major']}건 · 그중 처음 등장 {u['major_first_seen']}건 = {pc(u['first_seen_share'])})"
        )
    print("\n* 전년 기준 = 비교 기준(2026-11-25 결정) — 평소 전년 같은 주, 설·추석 D-35~D+7 은 전년 같은 명절 날짜에 맞춤")
    print("* 선행 = 그 방법이 맞힌 사례의 첫 관측 진입까지 일수(중앙값) — 방법끼리 견주는 값이 아님. "
          "상위20·7일+ = 제출한 상위 20 중 첫 진입이 7일 이상 뒤인 적중 ÷ 제출 수")  # fmt: skip
    out = ROOT / "var" / "forecast"
    out.mkdir(parents=True, exist_ok=True)
    f = out / f"backtest_{q}_{args.start}_{args.end}_m{int(args.min_share * 100)}.json"
    f.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"저장: {f} (커밋하지 않음)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
