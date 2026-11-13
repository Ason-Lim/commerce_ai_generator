"""쿠팡 채널 아이디(subId) 연결 확인 — 검색 1번으로 돌려받은 상품 링크에 채널이 실렸는지 본다 (2026-11-13).

사용 (Mac): uv run python scripts/check_coupang_subid.py [검색어]
  .env 의 COUPANG_SUB_ID 를 붙여 쿠팡 파트너스 검색 API 를 1번 부르고, 상품 링크에 그 값이 들어 있는지 출력한다.
  최종 확인은 다음 날 15시 이후 파트너스 '리포트'의 채널 ID 칸.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except ImportError:
        pass
    from app.services.coupang_api import coupang_sub_id, search_coupang_products

    sid = coupang_sub_id()
    print(f"COUPANG_SUB_ID = {sid or '(없음 — 붙이지 않음)'}")
    items = search_coupang_products(sys.argv[1] if len(sys.argv) > 1 else "사과", limit=2)
    if not items:
        print("검색 결과 없음 — 키·호출 한도·네트워크를 확인하세요")
        return
    for it in items:
        url = str(it.get("product_url") or it.get("url") or "")
        has = bool(sid) and sid.lower() in url.lower()
        print(f"- {str(it.get('product_name'))[:30]} · 링크에 채널 {'있음' if has else '없음'}")
    print("링크에 '있음'이면 연결 성공. 실적 반영은 파트너스 리포트(매일 15시 갱신)에서 채널 ID 칸으로 확인.")


if __name__ == "__main__":
    main()
