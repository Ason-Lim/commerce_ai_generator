"""보존 기간 작업 — 매일 새벽 launchd 가 부른다 (ops/launchd/com.commerce_ai.privacy_retention.plist, 2026-11-21).

    uv run python scripts/privacy_retention.py --dry-run   # 바꾸지 않고 건수만
    uv run python scripts/privacy_retention.py             # 접고 → 가명 → 지우기

규칙은 app/services/privacy/retention.py. 결과는 한 줄씩 출력하고 DB privacy_job_log 에도 남긴다.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="보존 기간 작업 (접고 지우기)")
    ap.add_argument("--dry-run", action="store_true", help="바꾸지 않고 건수만 보기")
    args = ap.parse_args(argv)

    from dotenv import load_dotenv
    from sqlalchemy import create_engine

    from app.core.config import resolve_database_url
    from app.services.privacy.retention import Retention

    load_dotenv(ROOT / ".env")
    engine = create_engine(resolve_database_url(), pool_pre_ping=True)
    report = Retention(engine, dry_run=args.dry_run).run()
    for r in report:
        note = f" — {r['note']}" if r.get("note") else ""
        print(f"[{'시험' if args.dry_run else '실행'}] {r['step']:<12} {r['target']:<40} {r['rows']:>7}건"
              f"  기준 {r['cutoff'] or '-'}{note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
