"""예보 장부 — 어제 기준 예보 저장 + 지난 예보 채점 (2026-11-25). 매주 월요일 launchd 로 돌린다.

uv run python scripts/forecast_ledger.py            # 어제 기준 저장(있으면 그대로) + 성적 출력
uv run python scripts/forecast_ledger.py --report   # 저장 없이 성적만
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main(argv: list[str] | None = None) -> int:
    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
    except ImportError:
        pass
    from app.services.trends import period
    from app.services.trends.forecast import ledger

    ap = argparse.ArgumentParser(description="예보 장부")
    ap.add_argument("--report", action="store_true", help="저장하지 않고 성적만")
    args = ap.parse_args(argv)
    rank_dir, kind = period.rank_dir_from_env()
    if rank_dir is None:
        print("순위 폴더가 없어요 — .env 의 NAVER_DAILY_RANK_DIR 를 확인해 주세요")
        return 1
    if not args.report:
        day = dt.date.today() - dt.timedelta(days=1)
        r = ledger.save(rank_dir, day)
        print(f"{day} 예보: {r['status']} → {r['path']}")
    if not args.report:  # 2026-11-25: 지식 묶음·데이터셋도 매주 새로 (AI에게 묻기가 최신 결과를 근거로)
        from app.services.trends.forecast import knowledge as kn

        snap = kn.build(rank_dir)
        ds = kn.export_week(snap)
        print(f"지식 묶음 {snap['path']} · 데이터셋 {ds['rows']}줄 → {ds['path']}")
    res = ledger.evaluate(rank_dir)
    t = res["target"]
    print(f"채점 {res['graded_weeks']}주 · 대기 {res['pending']}주 · 목표 재설정까지 {t['weeks_left']}주 ({t['rule']})")
    for x in res["summary"].values():
        rate = "—" if x["lead7_rate"] is None else f"{x['lead7_rate'] * 100:.1f}%"
        vs = "" if x["vs_baseline_pp"] is None else f" ({x['vs_baseline_pp']:+.1f}%p)"
        print(f"  {x['name']:<14} 선행 적중 {x['lead7']}/{x['submitted']} = {rate}{vs}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
