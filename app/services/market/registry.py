from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional

from app.services.market.kurly_search_link import (
    build_kurly_search_url,
)
from app.services.market.ssg_search_link import (
    build_ssg_search_url,
)

@dataclass(frozen=True)
class PlatformConfig:
    """Commerce AI V8 플랫폼 공통 설정."""

    id: str
    display_name: str
    platform_type: str
    enabled: bool
    collection_priority: int

    collector_type: str
    collector_name: Optional[str] = None
    source_platform: Optional[str] = None

    supports_dawn_delivery: bool = False
    supports_same_day_delivery: bool = False
    supports_scheduled_delivery: bool = False
    supports_parcel_delivery: bool = True
    supports_pickup: bool = False
    requires_address_check: bool = False

    trust_score: float = 50.0
    quality_score: float = 50.0
    freshness_score: float = 50.0
    price_score: float = 50.0
    delivery_score: float = 50.0
    premium_score: float = 50.0
    bulk_purchase_score: float = 50.0
    gift_score: float = 50.0

    aliases: tuple[str, ...] = field(
        default_factory=tuple
    )

    domain_markers: tuple[str, ...] = field(
        default_factory=tuple
    )

    search_url_builder: Optional[
        Callable[[str], str]
    ] = None


PLATFORM_REGISTRY: Dict[str, PlatformConfig] = {
    "naver": PlatformConfig(
        id="naver",
        display_name="네이버쇼핑",
        platform_type="marketplace",
        enabled=True,
        collection_priority=1,
        collector_type="direct",
        collector_name="naver_shopping",
        supports_parcel_delivery=True,
        requires_address_check=False,
        trust_score=72.0,
        quality_score=65.0,
        freshness_score=60.0,
        price_score=88.0,
        delivery_score=62.0,
        premium_score=55.0,
        bulk_purchase_score=70.0,
        gift_score=65.0,
        aliases=(
            "네이버",
            "네이버쇼핑",
            "naver",
            "naver shopping",
        ),
    
        domain_markers=(
            "shopping.naver.com",
            "search.shopping.naver.com",
            "smartstore.naver.com",
            "brand.naver.com",
        ),
    ),
        

    "coupang": PlatformConfig(
        id="coupang",
        display_name="쿠팡",
        platform_type="marketplace",
        enabled=True,
        collection_priority=1,
        collector_type="direct",
        collector_name="coupang_partners",
        supports_dawn_delivery=True,
        supports_same_day_delivery=True,
        supports_scheduled_delivery=False,
        supports_parcel_delivery=True,
        requires_address_check=False,
        trust_score=82.0,
        quality_score=72.0,
        freshness_score=72.0,
        price_score=85.0,
        delivery_score=96.0,
        premium_score=58.0,
        bulk_purchase_score=86.0,
        gift_score=62.0,
        aliases=(
            "쿠팡",
            "coupang",
        ),
        
        domain_markers=(
            "coupang.com",
            "link.coupang.com",
        ),
    ),

    "ssg": PlatformConfig(
        id="ssg",
        display_name="SSG.COM",
        platform_type="grocery_mart",
        enabled=True,
        collection_priority=1,
        collector_type="partner_filter",
        collector_name="naver_shopping_filter",
        source_platform="naver",
        supports_dawn_delivery=True,
        supports_same_day_delivery=True,
        supports_scheduled_delivery=True,
        supports_parcel_delivery=True,
        supports_pickup=True,
        requires_address_check=True,
        trust_score=90.0,
        quality_score=88.0,
        freshness_score=90.0,
        price_score=76.0,
        delivery_score=91.0,
        premium_score=82.0,
        bulk_purchase_score=75.0,
        gift_score=84.0,
        aliases=(
            "SSG",
            "SSG.COM",
            "SSG닷컴",
            "쓱닷컴",
            "신세계몰",
            "이마트몰",
        ),

        domain_markers=(
            "ssg.com",
            "emart.ssg.com",
            "shinsegaemall.ssg.com",
        ),
        search_url_builder=build_ssg_search_url,
    ),


    "oasis": PlatformConfig(
        id="oasis",
        display_name="오아시스마켓",
        platform_type="fresh_grocery",
        enabled=True,
        collection_priority=1,
        collector_type="partner_filter",
        collector_name="naver_shopping_filter",
        source_platform="naver",
        supports_dawn_delivery=True,
        supports_same_day_delivery=False,
        supports_scheduled_delivery=False,
        supports_parcel_delivery=True,
        supports_pickup=False,
        requires_address_check=True,
        trust_score=86.0,
        quality_score=91.0,
        freshness_score=95.0,
        price_score=74.0,
        delivery_score=82.0,
        premium_score=78.0,
        bulk_purchase_score=66.0,
        gift_score=72.0,
        aliases=(
            "오아시스",
            "오아시스마켓",
            "oasis",
            "oasis market",
        ),
        domain_markers=(
            "oasis.co.kr",
        ),
    ),

    "kurly": PlatformConfig(
        id="kurly",
        display_name="컬리",
        platform_type="fresh_grocery",
        enabled=False,
        collection_priority=1,
        collector_type="future",
        collector_name=None,
        supports_dawn_delivery=True,
        supports_same_day_delivery=False,
        supports_scheduled_delivery=False,
        supports_parcel_delivery=True,
        supports_pickup=False,
        requires_address_check=True,
        trust_score=88.0,
        quality_score=94.0,
        freshness_score=94.0,
        price_score=66.0,
        delivery_score=90.0,
        premium_score=96.0,
        bulk_purchase_score=58.0,
        gift_score=88.0,
        aliases=(
            "컬리",
            "마켓컬리",
            "kurly",
            "market kurly",
            "market_kurly",
        ),

        domain_markers=(
            "kurly.com",
            "redirect.kurly.com",
        ),
        search_url_builder=build_kurly_search_url,
    ),

    "lotte_mart": PlatformConfig(
        id="lotte_mart",
        display_name="롯데마트",
        platform_type="grocery_mart",
        enabled=False,
        collection_priority=1,
        collector_type="future",
        collector_name=None,
        supports_dawn_delivery=False,
        supports_same_day_delivery=True,
        supports_scheduled_delivery=True,
        supports_parcel_delivery=True,
        supports_pickup=True,
        requires_address_check=True,
        trust_score=85.0,
        quality_score=84.0,
        freshness_score=87.0,
        price_score=80.0,
        delivery_score=84.0,
        premium_score=70.0,
        bulk_purchase_score=82.0,
        gift_score=76.0,
        aliases=(
            "롯데마트",
            "롯데마트몰",
            "lotte mart",
            "lottemart",
        ),
        domain_markers=(
            "lottemart.com",
            "lotteon.com",
        ),
    ),

    "gs_shop": PlatformConfig(
        id="gs_shop",
        display_name="GS SHOP",
        platform_type="home_shopping",
        enabled=False,
        collection_priority=2,
        collector_type="future",
        collector_name=None,
        supports_dawn_delivery=False,
        supports_same_day_delivery=False,
        supports_scheduled_delivery=False,
        supports_parcel_delivery=True,
        supports_pickup=False,
        requires_address_check=False,
        trust_score=83.0,
        quality_score=80.0,
        freshness_score=68.0,
        price_score=76.0,
        delivery_score=68.0,
        premium_score=76.0,
        bulk_purchase_score=92.0,
        gift_score=90.0,
        aliases=(
            "GS SHOP",
            "GS샵",
            "지에스샵",
            "gsshop",
        ),
        domain_markers=(
            "gsshop.com",
            "m.gsshop.com",
        ),
    ),

    "cj_onstyle": PlatformConfig(
        id="cj_onstyle",
        display_name="CJ온스타일",
        platform_type="home_shopping",
        enabled=False,
        collection_priority=2,
        collector_type="future",
        collector_name=None,
        supports_dawn_delivery=False,
        supports_same_day_delivery=False,
        supports_scheduled_delivery=False,
        supports_parcel_delivery=True,
        supports_pickup=False,
        requires_address_check=False,
        trust_score=84.0,
        quality_score=82.0,
        freshness_score=68.0,
        price_score=75.0,
        delivery_score=68.0,
        premium_score=82.0,
        bulk_purchase_score=90.0,
        gift_score=93.0,
        aliases=(
            "CJ온스타일",
            "CJ몰",
            "CJmall",
            "CJ mall",
            "cjonstyle",
        ),
        domain_markers=(
            "cjonstyle.com",
            "display.cjonstyle.com",
        ),
    ),
}


def get_platform_config(
    platform_id: str,
) -> Optional[PlatformConfig]:
    """플랫폼 ID로 설정을 반환한다."""

    normalized = (platform_id or "").strip().lower()
    return PLATFORM_REGISTRY.get(normalized)


def require_platform_config(
    platform_id: str,
) -> PlatformConfig:
    """플랫폼 설정이 없으면 예외를 발생시킨다."""

    config = get_platform_config(platform_id)

    if config is None:
        raise KeyError(
            f"unknown platform: {platform_id}"
        )

    return config


def list_platform_configs(
    enabled_only: bool = False,
    platform_type: Optional[str] = None,
) -> List[PlatformConfig]:
    """조건에 맞는 플랫폼 설정 목록을 반환한다."""

    configs = list(PLATFORM_REGISTRY.values())

    if enabled_only:
        configs = [
            config
            for config in configs
            if config.enabled
        ]

    if platform_type:
        normalized_type = platform_type.strip().lower()
        configs = [
            config
            for config in configs
            if config.platform_type == normalized_type
        ]

    return sorted(
        configs,
        key=lambda config: (
            config.collection_priority,
            config.display_name,
        ),
    )


def get_enabled_platform_ids() -> List[str]:
    return [
        config.id
        for config in list_platform_configs(
            enabled_only=True
        )
    ]


def get_partner_platform_ids() -> List[str]:
    return [
        config.id
        for config in list_platform_configs(
            enabled_only=True
        )
        if config.collector_type == "partner_filter"
    ]


def platform_config_to_dict(
    platform_id: str,
) -> Dict[str, object]:
    config = require_platform_config(platform_id)
    return asdict(config)
