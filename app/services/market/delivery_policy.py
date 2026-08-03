from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.services.market.registry import (
    get_platform_config,
)


DELIVERY_AVAILABLE = "available"
DELIVERY_PARTIAL = "partial"
DELIVERY_ADDRESS_REQUIRED = "address_required"
DELIVERY_UNKNOWN = "unknown"
DELIVERY_UNAVAILABLE = "unavailable"


def _build_delivery_types(
    platform: str,
) -> List[str]:
    config = get_platform_config(platform)

    if config is None:
        return []

    delivery_types: List[str] = []

    if config.supports_dawn_delivery:
        delivery_types.append("dawn")

    if config.supports_same_day_delivery:
        delivery_types.append("same_day")

    if config.supports_scheduled_delivery:
        delivery_types.append("scheduled")

    if config.supports_parcel_delivery:
        delivery_types.append("parcel")

    if config.supports_pickup:
        delivery_types.append("pickup")

    return delivery_types


def build_platform_delivery_policy(
    platform: str,
    user_region: Optional[str] = None,
) -> Dict[str, Any]:
    """
    플랫폼 기본 배송 정책을 반환한다.

    user_region은 향후 주소 기반 배송 판정 엔진을 위해
    현재 인터페이스에 포함한다.
    """

    normalized = (platform or "").strip().lower()
    config = get_platform_config(normalized)

    if config is None:
        return {
            "delivery_type": [],
            "delivery_availability": DELIVERY_UNKNOWN,
            "delivery_region_summary": None,
            "delivery_requires_address_check": False,
            "delivery_notice": None,
        }

    if normalized == "oasis":
        summary = (
            "오아시스·새벽배송은 일부 지역에서 이용 가능"
        )
        notice = (
            "배송지에 따라 오아시스 배송과 새벽배송 가능 여부가 "
            "달라집니다. 미지원 지역은 일반 택배로 배송될 수 있습니다."
        )

    elif normalized == "ssg":
        summary = (
            "배송지와 상품에 따라 쓱배송 가능 여부가 달라짐"
        )
        notice = (
            "쓱배송 가능 여부와 배송 시간은 배송지 및 상품에 따라 "
            "달라집니다."
        )

    elif normalized == "coupang":
        summary = (
            "상품과 배송지에 따라 빠른 배송 가능 여부가 달라짐"
        )
        notice = None

    elif normalized == "naver":
        summary = "판매처별 배송 조건 확인 필요"
        notice = None

    else:
        summary = (
            "배송지와 상품별 배송 조건 확인 필요"
            if config.requires_address_check
            else "상품별 배송 조건 확인 필요"
        )
        notice = None

    availability = (
        DELIVERY_ADDRESS_REQUIRED
        if config.requires_address_check
        else DELIVERY_UNKNOWN
    )

    return {
        "delivery_type": _build_delivery_types(
            normalized
        ),
        "delivery_availability": availability,
        "delivery_region_summary": summary,
        "delivery_requires_address_check": (
            config.requires_address_check
        ),
        "delivery_notice": notice,
    }


def calculate_delivery_score(
    availability: str,
    preferred_fast_delivery: bool = False,
) -> float:
    base_scores = {
        DELIVERY_AVAILABLE: 100.0,
        DELIVERY_PARTIAL: 72.0,
        DELIVERY_ADDRESS_REQUIRED: 62.0,
        DELIVERY_UNKNOWN: 50.0,
        DELIVERY_UNAVAILABLE: 0.0,
    }

    score = base_scores.get(
        availability,
        50.0,
    )

    if preferred_fast_delivery:
        if availability == DELIVERY_ADDRESS_REQUIRED:
            score -= 8.0
        elif availability == DELIVERY_UNKNOWN:
            score -= 12.0
        elif availability == DELIVERY_UNAVAILABLE:
            score = 0.0

    return max(
        0.0,
        min(100.0, score),
    )
