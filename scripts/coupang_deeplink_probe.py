"""쿠팡 파트너스 딥링크 API 로 '검색 결과 링크'를 만들 수 있는지 확인 (2026-11-22, 2단계 검증 항목).

    uv run python scripts/coupang_deeplink_probe.py "엑스트라 버진 올리브유"
    uv run python scripts/coupang_deeplink_probe.py "올리브유" --sub-id commercetest

쿠팡 검색 결과 주소(https://www.coupang.com/np/search?q=…)를 딥링크 API 에 넣어 파트너스 링크(link.coupang.com/…)가
나오는지, 응답 코드·메시지·걸린 시간을 출력한다. 화면에는 아무것도 바꾸지 않는다. 한 번 실행 = 딥링크 API 1회 호출.
결과는 claude/coupang_gap_design_2026-11-22.md §4 '검증 항목'에 적는다 (검색 주소 허용 여부 · 호출 제한 · 링크 유효 기간).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PATH = "/v2/providers/affiliate_open_api/apis/openapi/v1/deeplink"


def search_url(keyword: str) -> str:
    return "https://www.coupang.com/np/search?q=" + quote(" ".join(keyword.split()))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="쿠팡 검색 결과 딥링크 확인")
    ap.add_argument("keyword")
    ap.add_argument("--sub-id", default=None, help="채널 아이디 (없으면 .env COUPANG_SUB_ID)")
    args = ap.parse_args(argv)
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    import requests

    from app.services import coupang_api

    if not coupang_api.is_coupang_available():
        print("쿠팡 API 키가 없거나 COUPANG_API_ENABLED=true 가 아니에요.")
        return 1
    body = {"coupangUrls": [search_url(args.keyword)]}
    sub = args.sub_id or coupang_api.coupang_sub_id()
    if sub:
        body["subId"] = sub
    headers = {"Authorization": coupang_api._build_authorization("POST", PATH, ""), "Content-Type": "application/json"}
    t0 = time.monotonic()
    r = requests.post(coupang_api.COUPANG_DOMAIN + PATH, headers=headers, data=json.dumps(body), timeout=10)
    ms = round((time.monotonic() - t0) * 1000)
    print(f"요청 주소: {body['coupangUrls'][0]}")
    print(f"HTTP {r.status_code} · {ms}ms")
    try:
        data = r.json()
    except ValueError:
        print(r.text[:500])
        return 1
    print(json.dumps(data, ensure_ascii=False, indent=2)[:2000])
    links = [d.get("shortenUrl") or d.get("landingUrl") for d in (data.get("data") or []) if isinstance(d, dict)]
    print(
        "결과:",
        "검색 결과 딥링크 만들어짐 → " + links[0] if links and links[0] else "딥링크 없음 (위 응답 메시지 확인)",
    )
    return 0 if links else 2


if __name__ == "__main__":
    raise SystemExit(main())
