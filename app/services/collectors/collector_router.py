from app.services.collectors.naver_smartstore_json_collector import enrich_naver_smartstore_product


def detect_collector_type(item):
    url = (
        item.get("product_url")
        or item.get("url")
        or item.get("redirect_url")
        or item.get("raw_link")
        or ""
    ).lower()

    mall_name = (
        item.get("mall_name")
        or item.get("seller_name")
        or item.get("platform_name")
        or ""
    ).lower()

    if "smartstore.naver.com" in url:
        return "naver_smartstore"

    if ("컬리n마트" in mall_name or "컬리" in mall_name) and "smartstore.naver.com" in url:
        return "naver_smartstore"

    return "unknown"


def enrich_product_by_router(item):
    collector_type = detect_collector_type(item)

    if collector_type == "naver_smartstore":
        return enrich_naver_smartstore_product(item)

    return {
        **item,
        "_collector_type": collector_type,
        "_collector_status": "skipped",
        "_collector_reason": "지원하지 않는 수집 대상입니다.",
    }
