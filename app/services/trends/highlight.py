"""홈 카테고리 '이번 주 주목' 대표 상품 (2026-11-23 저녁 — 사용자 채택 B).

* 그 카테고리에서 가장 많이 오른 키워드 하나로 쿠팡 검색 1번 → 이름에 그 키워드가 든 식품 상품 (화면은 3개 + 더 보기).
  (2026-11-23 21:44 사용자 요청: 그래프 빼고, 상품 사진, 3개씩, 더 보기)
* **파일·DB 에 저장하지 않는다** — 쿠팡 검색 캐시(메모리 10분)와 이동용 메모리 표(10분)만 (오픈 API 약관 제5조 ③).
* 아무 키워드나 검색하지 않게: 지금 홈 응답의 '이번 주 주목' 키워드만 받는다(라우트에서 확인).
* 이동은 /home/hgo/{키} → 클릭 기록(상품명 없이 링크만) 뒤 쿠팡 제휴 링크. 10분이 지나 표에 없으면 쿠팡 검색 화면(제휴 아님).
"""
from __future__ import annotations

import hashlib
import re
import threading
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

KST = timezone(timedelta(hours=9))
TTL = 600
_LOCK = threading.Lock()
_GO: dict[str, tuple[float, str, str]] = {}          # 키 → (받은 시각, 제휴 링크, 키워드)
IMAGE_HOSTS = ("coupangcdn.com", "coupang.com")      # 파트너스 API 사진은 ads-partners.coupang.com
MAX_ITEMS = 10
SEARCH_LIMIT = 10                                   # 쿠팡 검색 API 한 번에 최대 10개 — 넘기면 오류(빈 결과)
LINK_HOSTS = ("link.coupang.com", "www.coupang.com", "coupang.com")


def _https(url: str | None, hosts) -> str | None:
    m = re.match(r"^https://([^/]+)/", url or "")
    return url if m and any(m.group(1) == h or m.group(1).endswith("." + h) for h in hosts) else None


def _flat(s: str) -> str:
    return re.sub(r"\s+", "", s or "")


def picks(keyword: str, search=None, limit: int = MAX_ITEMS) -> list[dict]:
    """키워드 → 대표 상품들 (이름에 키워드가 든 식품만, 같은 링크 한 번)."""
    from app.services.commerce.nonfood import is_non_food_category, is_non_food_item

    if search is None:
        from app.services.coupang_api import search_coupang_products as search
    out, seen = [], set()
    fetched = datetime.now(KST).isoformat(timespec="minutes")
    for it in search(keyword, SEARCH_LIMIT) or []:
        title = str(it.get("product_name") or it.get("name") or "")
        url = _https(it.get("product_url"), LINK_HOSTS)
        if not title or not url or url in seen or _flat(keyword) not in _flat(title) \
                or is_non_food_item(title, it.get("category_name")) or is_non_food_category(it.get("category_name")):
            continue
        seen.add(url)
        key = hashlib.sha1(url.encode()).hexdigest()[:12]
        with _LOCK:
            now = time.monotonic()
            for k in [k for k, v in _GO.items() if now - v[0] > TTL]:
                _GO.pop(k, None)
            _GO[key] = (now, url, keyword)
        price = it.get("price")
        out.append({"keyword": keyword, "title": title[:120], "image": _https(it.get("image_url"), IMAGE_HOSTS),
                    "price_krw": int(price) if isinstance(price, (int, float)) and price > 0 else None,
                    "rocket": bool(it.get("is_rocket")), "go_url": f"/home/hgo/{key}", "fetched_at": fetched})
        if len(out) >= limit:
            break
    return out


def pick(keyword: str, search=None) -> dict | None:
    """키워드 → 대표 상품 하나 (없으면 None)."""
    got = picks(keyword, search, 1)
    return got[0] if got else None


def target(key: str) -> tuple[str, bool]:
    """(이동 주소, 제휴 링크인지). 10분이 지났으면 쿠팡 검색 화면."""
    with _LOCK:
        hit = _GO.get(key)
    if hit and time.monotonic() - hit[0] <= TTL:
        return hit[1], True
    kw = hit[2] if hit else ""
    return ("https://www.coupang.com/np/search?q=" + quote(kw)) if kw else "/", False


__all__ = ["pick", "picks", "target", "TTL", "MAX_ITEMS"]
