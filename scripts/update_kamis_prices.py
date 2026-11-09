"""KAMIS 일일 시세를 받아 data/kamis/daily_YYYY-MM-DD.json 에 저장 (서버 정기 작업용, 하루 1회).

사용: python scripts/update_kamis_prices.py
(서버는 요청 때 오늘 파일이 없으면 한 번 받아 보지만, 정기 작업으로 미리 받아 두면 첫 요청이 기다리지 않는다.)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from app.services.public_price import kamis  # noqa: E402

data = kamis.fetch_daily()
if not data:
    sys.exit("KAMIS_API_KEY / KAMIS_CERT_ID 가 .env 에 없어요.")
path = kamis.save_daily(data)
rows = kamis.parse(data)
print(f"저장: {path} · 비교 가능한 품목 {len(rows)}개 (소매 {sum(r['cls'] == '소매' for r in rows)} · "
      f"도매 {sum(r['cls'] == '도매' for r in rows)})")
