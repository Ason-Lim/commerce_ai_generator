"""국립종자원 품종코드 전체 목록 내려받기 (2026-11-11) — 품종 이름 확인용.

  .env : SEED_VARIETY_API_KEY=<data.mafra.go.kr 에서 발급한 키>
  실행 : uv run python scripts/sync_seed_varieties.py
  결과 : data/reference/seed_varieties.json  (rows: VAR_CD · VAR_NM_KOR · VAR_NM_ENG)

한 번에 최대 1,000건(API 제한)씩, 하루 호출 한도(1,000회) 안에서 끝까지 받는다. 서버가 응답하지 않으면 기존 파일은 그대로 둔다.
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.reference.seed_varieties import DEFAULT_PATH  # noqa: E402

BASE = "http://211.237.50.150:7080/openapi"
GRID = "Grid_20200114000000000604_1"
PAGE = 1000
MESSAGES = {"INFO-100": "인증키가 유효하지 않아요 (.env 의 SEED_VARIETY_API_KEY 확인)",
            "INFO-200": "공개되지 않았거나 데이터가 없어요", "ERROR-350": "오늘 호출 한도를 넘었어요"}


def fetch(key: str, start: int, end: int) -> dict:
    r = requests.get(f"{BASE}/{key}/json/{GRID}/{start}/{end}", timeout=30)
    r.raise_for_status()
    body = r.json().get(GRID) or {}
    code = (body.get("result") or {}).get("code")
    if code and code != "INFO-000":
        raise RuntimeError(f"{code}: {MESSAGES.get(code, (body.get('result') or {}).get('message'))}")
    return body


def main() -> int:
    load_dotenv(ROOT / ".env")
    key = (os.getenv("SEED_VARIETY_API_KEY") or "").strip()
    if not key:
        print(".env 에 SEED_VARIETY_API_KEY 가 없어요.")
        return 1
    rows: list[dict] = []
    first = fetch(key, 1, PAGE)
    total = int(first.get("totalCnt") or 0)
    rows += first.get("row") or []
    for start in range(PAGE + 1, total + 1, PAGE):
        time.sleep(0.2)
        rows += fetch(key, start, min(start + PAGE - 1, total)).get("row") or []
        print(f"  {len(rows):,}/{total:,}", end="\r")
    keep = [{k: r.get(k) for k in ("VAR_CD", "VAR_NM_KOR", "VAR_NM_ENG")} for r in rows]
    DEFAULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = DEFAULT_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps({"source": "국립종자원 품종코드", "fetched_at": datetime.now(timezone.utc).isoformat(),
                               "total": total, "rows": keep}, ensure_ascii=False), encoding="utf-8")
    tmp.replace(DEFAULT_PATH)
    print(f"품종 {len(keep):,}건 저장 → {DEFAULT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
