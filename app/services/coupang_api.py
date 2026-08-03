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
        "partner_notice": "이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.",
    }


def search_coupang_products(keyword: str, limit: int = 10):
    if not is_coupang_available():
        return []

    method = "GET"
    path = "/v2/providers/affiliate_open_api/apis/openapi/products/search"
    query = f"keyword={quote(keyword)}&limit={limit}"

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
