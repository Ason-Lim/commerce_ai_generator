from app.services.market.collector import (
    collect_market_products,
    fetch_naver_products_from_db,
)

from app.services.market.delivery_policy import (
    build_platform_delivery_policy,
    calculate_delivery_score,
)

from app.services.market.normalizer import (
    normalize_market_item,
    normalize_market_items,
)

from app.services.market.partner_market_adapter import (
    extract_partner_market_items,
)

from app.services.market.platform_matcher import (
    detect_platform_from_item,
    detect_platform_from_mall_name,
    normalize_mall_name,
)

from app.services.market.registry import (
    PLATFORM_REGISTRY,
    PlatformConfig,
    get_enabled_platform_ids,
    get_partner_platform_ids,
    get_platform_config,
    list_platform_configs,
    platform_config_to_dict,
    require_platform_config,
)

from app.services.market.deduplicator import (
    deduplicate_market_items,
    normalize_product_name,
)

from app.services.market.kurly_search_link import (
    build_kurly_search_url,
)
from app.services.market.search_url_builder import (
    build_platform_search_url,
    normalize_platform_name,
    normalize_search_keyword,
)
from app.services.market.ssg_search_link import (
    build_ssg_search_url,
)

from app.services.market.aggregator import (
    aggregate_market_items,
)

__all__ = [
    "PLATFORM_REGISTRY",
    "PlatformConfig",
    "build_platform_delivery_policy",
    "calculate_delivery_score",
    "normalize_market_item",
    "normalize_market_items",
    "extract_partner_market_items",
    "detect_platform_from_item",
    "detect_platform_from_mall_name",
    "normalize_mall_name",
    "get_enabled_platform_ids",
    "get_partner_platform_ids",
    "get_platform_config",
    "list_platform_configs",
    "platform_config_to_dict",
    "require_platform_config",
    "deduplicate_market_items",
    "normalize_product_name",
    "build_platform_search_url",
    "build_kurly_search_url",
    "build_ssg_search_url",
    "normalize_platform_name",
    "normalize_search_keyword",
    "aggregate_market_items",
]