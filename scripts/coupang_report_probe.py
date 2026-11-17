"""쿠팡 파트너스 리포트 API 응답 모양 확인 (읽기 전용, 2026-11-16).

    uv run python scripts/coupang_report_probe.py 20261110 20261116

클릭·주문·취소·수익 리포트를 채널(COUPANG_SUB_ID)별로 한 번씩 받아 var/coupang_reports/ 에 그대로 저장하고,
화면에는 필드 이름과 행 수만 보여 준다(금액은 출력하지 않음). 클릭→구매 연결 설계 전에
'리포트가 어떤 단위(날짜·상품·채널)로 오는지'를 실제 응답으로 확인하려는 도구다.
호출 수: 리포트 4종 × 채널 수. 검색과 같은 1분 한도 계산(coupang_rate)을 쓴다.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services import coupang_rate  # noqa: E402
from app.services.coupang_api import COUPANG_DOMAIN, _build_authorization  # noqa: E402

BASE = "/v2/providers/affiliate_open_api/apis/openapi/v1/reports/"
KINDS = ("clicks", "orders", "cancels", "commission")


def fetch(kind: str, start: str, end: str, sub_id: str | None) -> dict:
    path = BASE + kind
    query = f"startDate={start}&endDate={end}" + (f"&subId={sub_id}" if sub_id else "")
    if not coupang_rate.acquire():
        return {"error": "1분 호출 한도에 가까워 건너뜀"}
    r = requests.get(f"{COUPANG_DOMAIN}{path}?{query}", timeout=10,
                     headers={"Authorization": _build_authorization("GET", path, query),
                              "Content-Type": "application/json"})
    try:
        body = r.json()
    except ValueError:
        body = {"text": r.text[:500]}
    return {"status": r.status_code, "body": body}


def shape(body) -> tuple[int, list[str]]:
    rows = body.get("data") if isinstance(body, dict) else None
    if isinstance(rows, dict):
        rows = rows.get("data") or rows.get("list") or [rows]
    rows = rows if isinstance(rows, list) else []
    keys = sorted({k for r in rows if isinstance(r, dict) for k in r})
    return len(rows), keys


def main(start: str, end: str) -> None:
    out = ROOT / "var" / "coupang_reports"
    out.mkdir(parents=True, exist_ok=True)
    subs = [s for s in (os.getenv("COUPANG_SUB_ID"), os.getenv("COUPANG_TEST_SUB_ID")) if s] or [None]
    for sub in subs:
        for kind in KINDS:
            res = fetch(kind, start, end, sub)
            f = out / f"{kind}_{sub or 'all'}_{start}_{end}.json"
            f.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
            body = res.get("body") or {}
            n, keys = shape(body)
            code = body.get("rCode") if isinstance(body, dict) else None
            msg = (body.get("rMessage") or "") if isinstance(body, dict) else ""
            print(f"{sub or '(채널 없음)':<14} {kind:<10} HTTP {res.get('status')} rCode={code} {msg[:40]} "
                  f"행 {n} · 필드 {', '.join(keys) or '-'}")
    print(f"\n원본 저장: {out} (커밋하지 않음 — var/)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("사용법: uv run python scripts/coupang_report_probe.py 시작일(YYYYMMDD) 종료일(YYYYMMDD)")
    main(sys.argv[1], sys.argv[2])
