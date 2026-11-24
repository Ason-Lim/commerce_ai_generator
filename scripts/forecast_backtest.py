"""예측 백테스트 실행 (2026-11-24) — 기준선 3종 + 선행 곡선 탐색기, Q1(지금 100위 밖 → 7·14·28일 안 100위 진입).

    uv run python scripts/forecast_backtest.py 2025-01-06 2025-10-27          # 매주 월요일
    uv run python scripts/forecast_backtest.py 2025-01-06 2025-10-27 --no-explorer --step 14

순위 폴더는 NAVER_DAILY_RANK_DIR(.env). 결과 표를 출력하고 var/forecast/backtest_<시작>_<끝>.json 에 저장(커밋하지 않음).
예측은 예측일까지의 파일만 읽는다. 2024·2025 는 탐색·개발 자료 — 규칙 비교용.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

NAMES = {"recent": "최근 유지", "last_year": "전년 같은 주", "event_rel": "행사 상대일", "explorer": "탐색기"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="예측 백테스트")
    ap.add_argument("start")
    ap.add_argument("end")
    ap.add_argument("--step", type=int, default=7)
    ap.add_argument("--no-explorer", action="store_true")
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
    res = bt.run(rank_dir, dt.date.fromisoformat(args.start), dt.date.fromisoformat(args.end), step=args.step,
                 methods=bt.BASELINES if args.no_explorer else bt.METHODS)  # fmt: skip
    print(f"순위 폴더 {rank_dir} ({kind}) · 예측일 {res['dates']}개 · 건너뜀 {len(res['skipped'])}")
    print(
        f"{'방법':<8} {'기간':>4} {'정답':>6} {'예측':>6} {'적중':>5} {'정밀도':>7} {'재현율':>7} {'상위20':>7} {'선행':>5} {'놓친주요':>8}"
    )
    pc = lambda v: "—" if v is None else f"{v * 100:.1f}%"  # noqa: E731
    for m, byh in res["metrics"].items():
        for h, x in byh.items():
            print(
                f"{NAMES.get(m, m):<8} {h:>3}일 {x['n_true']:>6} {x['n_pred']:>6} {x['hits']:>5} {pc(x['precision']):>7} "
                f"{pc(x['recall']):>7} {pc(x['top20_precision']):>7} {x['lead_median'] or '—':>5} {pc(x['major_missed']):>8}"
                + (f"  추가 적중 {x['extra_hits']}" if 'extra_hits' in x else "")
            )
    out = ROOT / "var" / "forecast"
    out.mkdir(parents=True, exist_ok=True)
    f = out / f"backtest_{args.start}_{args.end}.json"
    f.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"저장: {f} (커밋하지 않음)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
