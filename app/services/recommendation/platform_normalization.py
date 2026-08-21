def normalize_text(value) -> str:
    return str(value or "").strip()


def detect_platform(item: dict) -> str:
    platform = normalize_text(item.get("platform")).lower()
    source = normalize_text(item.get("source")).lower()
    source_type = normalize_text(item.get("source_type")).lower()
    mall_name = normalize_text(item.get("mall_name"))
    seller_name = normalize_text(item.get("seller_name"))
    url = normalize_text(item.get("product_url")).lower()

    text = " ".join([platform, source, source_type, mall_name, seller_name, url]).lower()

    if "coupang" in text or "쿠팡" in text:
        return "coupang"

    if "kurly" in text or "컬리" in text or "마켓컬리" in text:
        return "kurly"

    if "naver" in text or "네이버" in text or "smartstore" in text:
        return "naver"

    return platform or "unknown"


def detect_source(item: dict) -> str:
    source = normalize_text(item.get("source"))
    source_type = normalize_text(item.get("source_type"))
    url = normalize_text(item.get("product_url")).lower()

    if source:
        return source

    if source_type:
        return source_type

    if "link.coupang.com" in url or "coupang.com" in url:
        return "coupang_partners"

    if "smartstore.naver.com" in url:
        return "naver_api"

    if "kurly.com" in url:
        return "kurly_selenium_html"

    return "unknown"


def detect_seller(item: dict) -> str:
    mall_name = normalize_text(item.get("mall_name"))
    seller_name = normalize_text(item.get("seller_name"))
    platform = detect_platform(item)

    if platform == "coupang":
        return "쿠팡"

    if mall_name:
        # "네이버/판매처" 형태 정리
        if mall_name.startswith("네이버/"):
            return mall_name.replace("네이버/", "").strip()

        return mall_name

    if seller_name:
        if seller_name.startswith("네이버/"):
            return seller_name.replace("네이버/", "").strip()

        return seller_name

    if platform == "naver":
        return "네이버쇼핑"

    if platform == "kurly":
        return "마켓컬리"

    return "판매처 확인 필요"


def build_display_market(platform: str, seller: str, source: str) -> str:
    if platform == "coupang":
        return "쿠팡"

    if platform == "kurly":
        return seller or "마켓컬리"

    if platform == "naver":
        if seller and seller != "네이버쇼핑":
            return f"네이버쇼핑 · {seller}"
        return "네이버쇼핑"

    return seller or source or "판매처 확인 필요"


def build_platform_label(platform: str) -> str:
    labels = {
        "coupang": "쿠팡",
        "naver": "네이버쇼핑",
        "kurly": "마켓컬리",
        "unknown": "기타",
    }
    return labels.get(platform, platform)


def normalize_platform_item(item: dict) -> dict:
    result = dict(item)

    platform = detect_platform(result)
    source = detect_source(result)
    seller = detect_seller(result)
    display_market = build_display_market(platform, seller, source)

    result["platform"] = platform
    result["source"] = source
    result["seller_name"] = seller
    result["platform_name"] = display_market
    result["display_market"] = display_market
    result["platform_label"] = build_platform_label(platform)

    if platform == "coupang":
        result["is_coupang"] = True
        result["is_ad"] = True
        result["platform_notice"] = result.get(
            "platform_notice"
        ) or result.get(
            "partner_notice"
        ) or "쿠팡 파트너스 활동의 일환으로 일정액의 수수료를 제공받을 수 있습니다."
    else:
        result["is_coupang"] = False
        result["is_ad"] = bool(result.get("is_ad", False))
        result["platform_notice"] = result.get("platform_notice") or ""

    return result


def normalize_platform_items(items: list[dict]) -> list[dict]:
    return [
        normalize_platform_item(item)
        for item in items
        if isinstance(item, dict)
    ]
