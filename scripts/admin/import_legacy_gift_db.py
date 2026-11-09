#!/usr/bin/env python3
"""기존 smallbiz-monitor / gift_trend_analyzer SQLite 의 gift_bids 를 관리자 B2B 저장소로 가져온다
(integrated_system scripts/import_legacy_gift_db.py 를 옮김).

    python -m scripts.admin.import_legacy_gift_db ~/anti_online/data/smallbiz_programs.db

모두 '미검증 기존 데이터(legacy_unverified)'로 저장되고 목록 · 트렌드 기본값에서 빠진다.
"""
import sys

from app.admin.b2b.gift_monitor.collectors import import_legacy_db, legacy_status_counts


def main(argv=None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print(__doc__)
        return 2
    n = import_legacy_db(args[0])
    print(f"가져온 공고 {n}건 (모두 '미검증 기존 데이터'로 표시) · 상태별 {legacy_status_counts()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
