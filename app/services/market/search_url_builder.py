from __future__ import annotations

from app.services.market.platform_matcher import (
    detect_platform_from_mall_name,
)
from app.services.market.registry import (
    get_platform_config,
)


def normalize_search_keyword(
    keyword: str | None,
) -> str:
    """플랫폼 검색 URL에 사용할 검색어를 정규화합니다."""

    return " ".join(
        str(keyword or "").strip().split()
    )


def normalize_platform_name(
    platform: str | None,
) -> str:
    """플랫폼 이름 또는 별칭을 Registry 플랫폼 ID로 변환합니다."""

    normalized_platform = str(
        platform or ""
    ).strip()

    if not normalized_platform:
        return ""

    detected_platform = detect_platform_from_mall_name(
        normalized_platform
    )

    if detected_platform:
        return detected_platform

    return normalized_platform.lower()


def build_platform_search_url(
    platform: str | None,
    keyword: str | None,
) -> str:
    """Registry에 등록된 플랫폼 검색 URL을 생성합니다."""

    platform_id = normalize_platform_name(
        platform
    )
    normalized_keyword = normalize_search_keyword(
        keyword
    )

    if not platform_id or not normalized_keyword:
        return ""

    config = get_platform_config(
        platform_id
    )

    if config is None:
        return ""

    builder = config.search_url_builder

    if not callable(builder):
        return ""

    try:
        search_url = builder(
            normalized_keyword
        )
    except (TypeError, ValueError):
        return ""

    return str(search_url or "").strip()