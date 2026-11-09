from __future__ import annotations

import hashlib
import re
from typing import Any

from app.services.common.text_utils import (
    clean_display_text,
)

from app.services.common.url_utils import (
    get_raw_product_url,
    is_search_url,
)

from app.services.common.weight_utils import (
    get_weight_text_from_item,
    normalize_weight_to_grams,
)

from .score_engine import (
    get_brix_value,
)

def get_effective_price_value(
    item,
):
    """추천/표시에 사용할 유효 가격 숫자."""

    item = item or {}

    candidates = [
        item.get("final_price"),
        item.get("sale_price"),
        item.get("discounted_price"),
        item.get("lprice"),
        item.get("price"),
        item.get("effective_price"),
    ]

    for value in candidates:
        try:
            number = float(
                value or 0
            )

            if number > 0:
                return number
        except (TypeError, ValueError):
            continue

    return 0.0

def calculate_price_consistency_score(
    item,
):
    """가격·중량·단가 일관성 점수."""

    item = item or {}

    price = get_effective_price_value(
        item
    )

    price_per_100g = (
        item.get("price_per_100g")
        or item.get("unit_price_100g")
        or item.get("unit_price_per_100g")
        or item.get("price_100g")
    )

    try:
        price_per_100g = float(
            price_per_100g or 0
        )
    except (TypeError, ValueError):
        price_per_100g = 0.0

    weight_text = get_weight_text_from_item(
        item
    )

    weight_g = normalize_weight_to_grams(
        weight_text
    )

    score = 0

    if price > 0:
        score += 25

    if weight_g > 0:
        score += 25

    if price_per_100g > 0:
        score += 25

    if (
        price > 0
        and weight_g > 0
        and price_per_100g > 0
    ):
        expected_price = (
            price_per_100g
            * (weight_g / 100)
        )

        gap_ratio = abs(
            price - expected_price
        ) / max(
            price,
            expected_price,
        )

        if gap_ratio <= 0.08:
            score += 25
        elif gap_ratio <= 0.20:
            score += 12
        else:
            score -= 25

    return max(
        0,
        min(int(score), 100),
    )
    
    
def is_generic_product_name(
    name,
) -> bool:
    """Hero에 올리기에는 너무 넓은 상품명인지 판단합니다."""

    name = clean_display_text(
        name
    )

    compact_name = re.sub(
        r"\s+",
        "",
        name,
    )

    generic_names = {
        "사과",
        "고당도사과",
        "꿀사과",
        "부사",
        "홍로",
        "시나노골드",
    }

    if compact_name in generic_names:
        return True

    if (
        len(compact_name) <= 6
        and not re.search(
            r"\d",
            compact_name,
        )
    ):
        return True

    return False

def is_kurly_search_identity_weak(
    item,
    display=None,
):
    """컬리 검색 URL처럼 정확한 상품 식별이 어려운 경우를 판단합니다."""

    item = item or {}
    display = display or {}

    raw_url = get_raw_product_url(
        item
    )

    seller_text = clean_display_text(
        display.get("seller_text")
        or display.get("seller_display")
        or item.get("seller_name")
        or item.get("seller")
        or ""
    )

    raw_name = clean_display_text(
        item.get("product_name")
        or item.get("raw_name")
        or item.get("title")
        or display.get("name")
        or ""
    )

    is_kurly = (
        "컬리" in seller_text
        or "마켓컬리" in seller_text
        or "kurly" in raw_url.lower()
        or "컬리" in raw_name
    )

    if not is_kurly:
        return False

    if "redirect.kurly.com/entry" in raw_url:
        return False

    return bool(
        is_search_url(raw_url)
        or not raw_url
    )

def calculate_brix_confidence_score(
    item,
    display=None,
):
    """맛 중심 추천용 Brix 신뢰도 점수."""

    item = item or {}
    display = display or {}

    brix = get_brix_value(
        item
    )

    raw_name = clean_display_text(
        item.get("product_name")
        or item.get("raw_name")
        or item.get("title")
        or display.get("name")
        or ""
    )

    raw_url = get_raw_product_url(
        item
    )

    weight_text = (
        display.get("weight_text")
        or get_weight_text_from_item(item)
    )

    score = 0

    if brix >= 15:
        score += 55
    elif brix >= 14:
        score += 42
    elif brix >= 13:
        score += 30
    elif item.get("is_high_brix"):
        score += 12

    if re.search(
        r"\d{2}(?:\.\d+)?\s*brix",
        raw_name,
        re.IGNORECASE,
    ):
        score += 25

    if weight_text:
        score += 10

    if raw_url and not is_search_url(raw_url):
        score += 10

    return max(
        0,
        min(int(score), 100),
    )

def get_product_identity_key(
    item,
    display=None,
):
    """상품 동일성 판단용 안정 키를 생성합니다."""

    item = item or {}
    display = display or {}

    raw_url = get_raw_product_url(
        item
    )

    platform = clean_display_text(
        item.get("platform_name")
        or item.get("mall_name")
        or item.get("source")
        or display.get("platform_name")
        or ""
    )

    seller = clean_display_text(
        item.get("seller_name")
        or item.get("seller")
        or display.get("seller_text")
        or display.get("seller_display")
        or ""
    )

    name = clean_display_text(
        item.get("product_name")
        or item.get("raw_name")
        or item.get("title")
        or display.get("name")
        or ""
    )

    weight = clean_display_text(
        display.get("weight_text")
        or get_weight_text_from_item(item)
    )

    brix = get_brix_value(
        item
    )

    raw_key = "|".join([
        platform.lower(),
        seller.lower(),
        raw_url.lower(),
        name.lower(),
        weight.lower(),
        f"{brix:.1f}" if brix else "",
    ])

    return hashlib.sha1(
        raw_key.encode("utf-8")
    ).hexdigest()
    
def validate_product_identity(
    item,
    display=None,
):
    """상품 동일성 검증 레이어 V2."""

    item = item or {}
    display = display or {}

    raw_url = get_raw_product_url(
        item
    )

    display_name = clean_display_text(
        display.get("name")
        or item.get("product_name")
        or item.get("title")
        or ""
    )

    raw_name = clean_display_text(
        item.get("product_name")
        or item.get("raw_name")
        or item.get("title")
        or ""
    )

    price = get_effective_price_value(
        item
    )

    price_confidence = calculate_price_consistency_score(
        item
    )

    brix_confidence = calculate_brix_confidence_score(
        item,
        display=display,
    )

    weak_kurly_search = is_kurly_search_identity_weak(
        item,
        display=display,
    )

    score = 100
    warnings = []

    if not raw_url:
        score -= 35
        warnings.append("상품 URL 없음")
    elif is_search_url(raw_url):
        score -= 45
        warnings.append("검색 URL")

    if (
        "kurly.com/search" in raw_url
        or "www.kurly.com/search" in raw_url
    ):
        score -= 25
        warnings.append("컬리 검색 URL")

    if is_generic_product_name(
        display_name
    ):
        score -= 30
        warnings.append("상품명 과도하게 일반적")

    if (
        not raw_name
        or len(raw_name.replace(" ", "")) <= 5
    ):
        score -= 15
        warnings.append("원본 상품명 부족")

    if price <= 0:
        score -= 25
        warnings.append("가격 없음")

    if price_confidence < 50:
        score -= 20
        warnings.append("가격/단가 불일치 가능성")

    if weak_kurly_search:
        score -= 25
        warnings.append("컬리 검색형 상품 가격 숨김")

    if (
        get_brix_value(item) >= 13
        and brix_confidence < 50
    ):
        score -= 10
        warnings.append("Brix 신뢰도 낮음")

    identity_score = max(
        0,
        min(int(score), 100),
    )

    return {
        "is_valid": identity_score >= 45,
        "identity_score": identity_score,
        "price_confidence": price_confidence,
        "brix_confidence": brix_confidence,
        "identity_key": get_product_identity_key(
            item,
            display=display,
        ),
        "warnings": warnings,
    }

def enrich_item_identity(
    item,
    display=None,
):
    """item에 Identity V2 결과를 캐싱합니다."""

    if "_identity_validation" not in item:
        validation = validate_product_identity(
            item,
            display=display,
        )

        item["_identity_validation"] = validation
        item["_identity_score"] = validation.get(
            "identity_score",
            0,
        )
        item["_price_confidence"] = validation.get(
            "price_confidence",
            0,
        )
        item["_brix_confidence"] = validation.get(
            "brix_confidence",
            0,
        )
        item["_product_identity_key"] = validation.get(
            "identity_key",
            "",
        )

    return item["_identity_validation"]


def calculate_product_identity_score(
    item,
    display=None,
):
    validation = validate_product_identity(
        item,
        display=display,
    )

    return validation.get(
        "identity_score",
        0,
    )


def is_product_identity_reliable(
    item,
    display=None,
):
    validation = validate_product_identity(
        item,
        display=display,
    )

    return (
        validation.get("is_valid", False)
        and validation.get("identity_score", 0) >= 60
    )
