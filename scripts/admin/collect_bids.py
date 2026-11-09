#!/usr/bin/env python3
"""B2B 입찰 공고 정기 수집 (cron · 서버 정기 작업용) — integrated_system scripts/collect_bids.py 를 옮겼다.

    python -m scripts.admin.collect_bids --days 7            # 나라장터 (G2B_SERVICE_KEY 필요)
    python -m scripts.admin.collect_bids --days 7 --keyword 선물세트

저장: B2B_DB_URL (기본 data/admin/b2b.sqlite3).  수집 자체가 안 되면 종료 코드 1.
"""
import argparse
import sys

from app.admin.b2b.gift_monitor.collectors import collect_all


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--keyword", action="append", help="공고명 검색어 (여러 번 지정 가능)")
    ap.add_argument("--kind", action="append", choices=["물품", "용역", "기타"],
                    help="공고 종류 (기본: 물품 · 용역)")
    a = ap.parse_args(argv)
    res = collect_all(a.days, a.keyword, kinds=tuple(a.kind) if a.kind else ("물품", "용역"))
    for r in res["results"]:
        print("\n".join(r["log"]))
    print(f"신규 {res['new']}건 / 조회 {res['found']}건")
    return 0 if any("완료" in line for r in res["results"] for line in r["log"]) else 1


if __name__ == "__main__":
    sys.exit(main())
