import contextlib
import contextvars
import os
import hmac
import hashlib
import requests
from datetime import datetime
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv(".env")

COUPANG_ACCESS_KEY = os.getenv("COUPANG_ACCESS_KEY")
COUPANG_SECRET_KEY = os.getenv("COUPANG_SECRET_KEY")
COUPANG_PARTNER_ID = os.getenv("COUPANG_PARTNER_ID")
COUPANG_API_ENABLED = os.getenv("COUPANG_API_ENABLED", "false").lower() == "true"

COUPANG_DOMAIN = "https://api-gateway.coupang.com"


def _build_authorization(method: str, path: str, query: str = "") -> str:
    now = datetime.utcnow().strftime("%y%m%dT%H%M%SZ")
    message = now + method + path + query

    signature = hmac.new(
        COUPANG_SECRET_KEY.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return (
        f"CEA algorithm=HmacSHA256, "
        f"access-key={COUPANG_ACCESS_KEY}, "
        f"signed-date={now}, "
        f"signature={signature}"
    )


def is_coupang_available() -> bool:
    return bool(
        COUPANG_API_ENABLED
        and COUPANG_ACCESS_KEY
        and COUPANG_SECRET_KEY
        and COUPANG_PARTNER_ID
    )


def normalize_coupang_product(item: dict, keyword: str = "") -> dict:
    return {
        "product_name": item.get("productName", ""),
        "name": item.get("productName", ""),
        "price": item.get("productPrice", 0),
        "product_url": item.get("productUrl", ""),
        "image_url": item.get("productImage", ""),
        "mall_name": "쿠팡",
        "seller_name": "쿠팡",
        "platform": "coupang",
        "source": "coupang_partners",
        "keyword": keyword,
        "is_coupang": True,
        "is_ad": True,
        # 2026-11-21: 쿠팡 분류 이름 — 식품 사이트에 신발·가전이 섞이지 않게 대화·검색 서비스에서 본다 (없으면 None)
        "category_name": item.get("categoryName") or None,
        # 2026-11-01: 판매처 API가 주는 배송 표시를 그대로 남긴다 (값이 없으면 None — 추정하지 않음)
        "is_rocket": item.get("isRocket") if isinstance(item.get("isRocket"), bool) else None,
        "is_free_shipping": item.get("isFreeShipping") if isinstance(item.get("isFreeShipping"), bool) else None,
        "partner_notice": "이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.",
    }


_SUB_ID_OVERRIDE: contextvars.ContextVar = contextvars.ContextVar("coupang_sub_id_override", default=None)


def _valid_sub_id(v: str | None) -> str | None:
    import re

    v = (v or "").strip()
    return v if re.fullmatch(r"[A-Za-z0-9]{8,20}", v) else None


def coupang_sub_id() -> str | None:
    """쿠팡 파트너스 채널 아이디(subId) — 실적 보고서에서 '어디서 생긴 클릭·구매인지' 나눈다 (2026-11-13).
    .env COUPANG_SUB_ID (예: commerce). 파트너스 '채널 아이디 관리'에서 만든 이름만 쓴다.
    파트너스 규칙(생성 화면): 8~20자 숫자·영어 대소문자 — 규칙에 맞지 않으면 붙이지 않음.
    2026-11-21: sub_id_channel() 안에서는 그 채널 아이디를 쓴다 (블로그 초안 링크를 사이트와 나눠 집계)."""
    override = _SUB_ID_OVERRIDE.get()
    return override if override else _valid_sub_id(os.getenv("COUPANG_SUB_ID"))


def coupang_blog_sub_id() -> str | None:
    """블로그(applesodda) 전용 채널 아이디 — .env COUPANG_BLOG_SUB_ID. 없거나 규칙에 안 맞으면 None (2026-11-21 결정)."""
    return _valid_sub_id(os.getenv("COUPANG_BLOG_SUB_ID"))


@contextlib.contextmanager
def sub_id_channel(sub_id: str | None):
    """이 블록 안의 쿠팡 검색 링크에 sub_id 채널을 붙인다. None 이면 기본 채널 그대로."""
    token = _SUB_ID_OVERRIDE.set(_valid_sub_id(sub_id))
    try:
        yield
    finally:
        _SUB_ID_OVERRIDE.reset(token)


DEEPLINK_PATH = "/v2/providers/affiliate_open_api/apis/openapi/v1/deeplink"


def coupang_search_page(keyword: str) -> str:
    """쿠팡 사이트 검색 결과 주소 (파트너스 링크로 바꾸기 전)."""
    return "https://www.coupang.com/np/search?q=" + quote(" ".join((keyword or "").split()))


def search_deeplink(keyword: str, timeout: float = 5.0) -> str | None:
    """쿠팡 검색 결과 화면으로 가는 파트너스 링크 (2026-11-22 확인: 딥링크 API 가 검색 주소를 받아
    link.coupang.com/a/… 를 줌, subid 반영). 키가 없거나 실패하면 None — 호출하는 쪽이 저장해 두고 다시 쓴다."""
    if not is_coupang_available() or not (keyword or "").strip():
        return None
    from app.services import coupang_rate

    if not coupang_rate.acquire():
        return None
    body = {"coupangUrls": [coupang_search_page(keyword)]}
    sub = coupang_sub_id()
    if sub:
        body["subId"] = sub
    try:
        r = requests.post(COUPANG_DOMAIN + DEEPLINK_PATH, timeout=timeout, json=body,
                          headers={"Authorization": _build_authorization("POST", DEEPLINK_PATH, "")})
        data = (r.json() or {}).get("data") or []
        url = (data[0] or {}).get("shortenUrl") if data else None
    except Exception:  # noqa: BLE001 — 링크가 없으면 블록을 빼면 된다
        return None
    return url if isinstance(url, str) and url.startswith("https://link.coupang.com/") else None


# 2026-11-22: 같은 검색어 결과를 잠깐 저장해 다시 쓴다 — 후보가 적을 때 더 찾기·이어 묻기로 호출이 늘어도
# 1분 한도(넘기면 24시간 막힘)를 지키게. 빈 결과·오류는 저장하지 않는다. 가격은 저장한 시각 기준이라 짧게.
# COUPANG_SEARCH_CACHE_MINUTES (기본 60, 0 이면 끔).
_SEARCH_CACHE: dict[tuple[str, int, str], tuple[float, list]] = {}
_SEARCH_CACHE_MAX = 500


def _cache_minutes() -> float:
    try:
        return max(0.0, float(os.getenv("COUPANG_SEARCH_CACHE_MINUTES", "60")))
    except ValueError:
        return 60.0


def search_coupang_products(keyword: str, limit: int = 10):
    if not is_coupang_available():
        return []
    import time as _time

    minutes = _cache_minutes()
    key = (" ".join((keyword or "").split()), int(limit), coupang_sub_id() or "")
    hit = _SEARCH_CACHE.get(key) if minutes else None
    if hit and _time.time() - hit[0] < minutes * 60:
        from app.services.chat import turn_metrics       # 2026-11-23 3-D ②: 차례별 쿠팡 캐시 사용 수

        turn_metrics.bump("coupang_cache_hits")
        return [dict(x) for x in hit[1]]
    items = _search_coupang_products(keyword, limit)
    if minutes and items:
        if len(_SEARCH_CACHE) >= _SEARCH_CACHE_MAX:
            for old_key in sorted(_SEARCH_CACHE, key=lambda k: _SEARCH_CACHE[k][0])[:_SEARCH_CACHE_MAX // 5]:
                _SEARCH_CACHE.pop(old_key, None)
        _SEARCH_CACHE[key] = (_time.time(), [dict(x) for x in items])
    return items


def _search_coupang_products(keyword: str, limit: int = 10):
    from app.services import coupang_rate

    if not coupang_rate.acquire():          # 1분 한도(문서: 50번) 직전 — 넘기면 24시간 사용 제한
        print("[Coupang API] 1분 호출 한도에 가까워 이번 검색은 건너뜀")
        return []
    from app.services.chat import turn_metrics           # 2026-11-23 3-D ②: 차례별 실제 쿠팡 호출 수

    turn_metrics.bump("coupang_calls")

    method = "GET"
    path = "/v2/providers/affiliate_open_api/apis/openapi/products/search"
    query = f"keyword={quote(keyword)}&limit={limit}"
    if coupang_sub_id():
        query += f"&subId={coupang_sub_id()}"

    authorization = _build_authorization(method, path, query)

    url = f"{COUPANG_DOMAIN}{path}?{query}"

    headers = {
        "Authorization": authorization,
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(url, headers=headers, timeout=7)
        response.raise_for_status()
        data = response.json()

        products = data.get("data", {}).get("productData", [])
        return [normalize_coupang_product(item, keyword) for item in products]

    except Exception as e:
        print(f"[Coupang API Error] {e}")
        return []
