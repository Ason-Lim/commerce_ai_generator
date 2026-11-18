"""쿠팡 검색 API 원본 응답 확인 (읽기 전용, 2026-11-17).

    uv run python scripts/coupang_search_probe.py 귤

검색 1번의 원본 응답을 var/coupang_reports/search_raw_<검색어>.json 에 그대로 저장하고, 상품마다 오는 필드 이름과
값의 종류를 보여 준다. 우리 코드(normalize_coupang_product)가 버리는 필드 중에 재고·판매 가능 여부 같은 값이
있는지 보려는 도구. 검색 1번 = 호출 1번 (1분 한도 계산 coupang_rate 사용).
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services import coupang_rate  # noqa: E402
from app.services.coupang_api import COUPANG_DOMAIN, _build_authorization, coupang_sub_id  # noqa: E402

USED = {"productName", "productPrice", "productUrl", "productImage", "isRocket", "isFreeShipping"}   # 지금 쓰는 값
WATCH = ("stock", "sold", "soldout", "available", "status", "sale", "inventory", "quantity", "out")


def main(keyword: str) -> None:
    path = "/v2/providers/affiliate_open_api/apis/openapi/products/search"
    query = f"keyword={quote(keyword)}&limit=10" + (f"&subId={coupang_sub_id()}" if coupang_sub_id() else "")
    if not coupang_rate.acquire():
        sys.exit("1분 호출 한도에 가까워요. 잠시 뒤 다시 실행해 주세요.")
    r = requests.get(f"{COUPANG_DOMAIN}{path}?{query}", timeout=10,
                     headers={"Authorization": _build_authorization("GET", path, query), "Content-Type": "application/json"})
    body = r.json()
    out = ROOT / "var" / "coupang_reports"
    out.mkdir(parents=True, exist_ok=True)
    f = out / f"search_raw_{keyword}.json"
    f.write_text(json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")

    data = body.get("data") or {}
    print(f"HTTP {r.status_code} · rCode={body.get('rCode')} {body.get('rMessage') or ''}")
    print("data 바로 아래 필드:", ", ".join(sorted(data)) if isinstance(data, dict) else type(data).__name__)
    items = data.get("productData") or [] if isinstance(data, dict) else []
    print(f"상품 {len(items)}개\n")
    kinds: dict[str, Counter] = {}
    for it in items:
        for k, v in it.items():
            kinds.setdefault(k, Counter())[type(v).__name__ if v not in (None, "") else "빈 값"] += 1
    print(f"{'필드':<22} {'우리 사용':<8} 값 종류(상품 수)")
    for k in sorted(kinds):
        flag = "쓰는 중" if k in USED else ("★ 확인" if any(w in k.lower() for w in WATCH) else "")
        print(f"{k:<22} {flag:<8} {dict(kinds[k])}")
    print(f"\n원본 저장: {f} (커밋하지 않음 — var/)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "귤")
