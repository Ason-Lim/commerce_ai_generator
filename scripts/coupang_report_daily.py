"""쿠팡 파트너스 리포트 매일 저장 (2026-11-24, 클릭·구매 연결 ②).

    uv run python scripts/coupang_report_daily.py            # 채널마다 최근 30일(어제까지) 받아 덮어쓰기
    uv run python scripts/coupang_report_daily.py --days 7

매일 오후 3시 30분 뒤 한 번(쿠팡 리포트는 다음 날 오후 갱신). 결과는 측정 DB(var/measure — 커밋하지 않음)에만.
화면 출력에는 금액을 쓰지 않는다. 호출 수: 리포트 4종 × 채널 수(최대 3) = 12번, 검색과 같은 1분 한도 계산.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="쿠팡 파트너스 리포트 매일 저장")
    ap.add_argument("--days", type=int, default=30)
    args = ap.parse_args(argv)
    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
    except ImportError:
        pass
    from app.services.measure import coupang_report

    bad = 0
    for r in coupang_report.run_daily(days=max(1, min(args.days, 90))):
        print(f"{r['channel']:<6} {r['kind']:<10} {r['status']:<8} {r['rows']:>5}행 {r.get('note') or ''}")
        bad += r["status"] == "error"
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
