from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any, Optional
from urllib.parse import urlparse

from app.services.market.registry import (
    PLATFORM_REGISTRY,
)


def normalize_mall_name(
    value: Optional[str],
) -> str:
    """몰·플랫폼 이름을 비교 가능한 문자열로 정규화합니다."""

    if not value:
        return ""

    normalized = str(value).strip().lower()
    normalized = re.sub(
        r"[^0-9a-z가-힣]",
        "",
        normalized,
    )

    return normalized


def detect_platform_from_mall_name(
    mall_name: Optional[str],
) -> Optional[str]:
    """몰 이름과 별칭을 이용해 플랫폼 ID를 판별합니다."""

    normalized = normalize_mall_name(mall_name)

    if not normalized:
        return None

    for platform_id, config in PLATFORM_REGISTRY.items():
        candidates = {
            normalize_mall_name(config.display_name),
            normalize_mall_name(platform_id),
        }

        candidates.update(
            normalize_mall_name(alias)
            for alias in config.aliases
        )

        candidates.discard("")

        # 정확히 일치하는 이름을 우선합니다.
        if normalized in candidates:
            return platform_id

        # 쇼핑몰 이름에 부가 문구가 붙은 경우를 처리합니다.
        if any(
            candidate in normalized
            or normalized in candidate
            for candidate in candidates
            if len(candidate) >= 3
        ):
            return platform_id

    return None


def _get_mapping_value(
    source: Mapping[str, Any] | None,
    *keys: str,
) -> str:
    """딕셔너리에서 첫 번째 유효한 문자열 값을 반환합니다."""

    if not source:
        return ""

    for key in keys:
        value = source.get(key)

        if value is None:
            continue

        normalized = str(value).strip()

        if normalized:
            return normalized

    return ""


def _extract_url_host(
    value: str | None,
) -> str:
    """URL에서 호스트 이름을 안전하게 추출합니다."""

    normalized_url = str(value or "").strip().lower()

    if not normalized_url:
        return ""

    try:
        parsed = urlparse(normalized_url)
        return str(parsed.netloc or "").lower()
    except (TypeError, ValueError):
        return ""


def _detect_platform_from_url(
    url: str | None,
) -> Optional[str]:
    """상품 URL의 도메인으로 플랫폼을 판별합니다."""

    normalized_url = str(url or "").strip().lower()

    if not normalized_url:
        return None

    host = _extract_url_host(normalized_url)

    # URL 스킴이 없는 값도 보조적으로 판별합니다.
    url_text = " ".join(
        value
        for value in [
            host,
            normalized_url,
        ]
        if value
    )

def _detect_platform_from_url(
    url: str | None,
) -> Optional[str]:
    """Registry에 등록된 도메인 정보로 플랫폼을 판별합니다."""

    normalized_url = str(
        url or ""
    ).strip().lower()

    if not normalized_url:
        return None

    host = _extract_url_host(
        normalized_url
    )

    url_text = " ".join(
        value
        for value in (
            host,
            normalized_url,
        )
        if value
    )

    for platform_id, config in PLATFORM_REGISTRY.items():
        for marker in config.domain_markers:
            normalized_marker = str(
                marker or ""
            ).strip().lower()

            if (
                normalized_marker
                and normalized_marker in url_text
            ):
                return platform_id

    return None

def detect_platform_from_item(
    item: Mapping[str, Any] | None,
    display: Mapping[str, Any] | None = None,
) -> Optional[str]:
    """상품 데이터와 표시 데이터에서 플랫폼 ID를 판별합니다.

    판별 우선순위:

    1. 명시적인 platform/platform_id 필드
    2. mall_name/source/seller 등의 플랫폼 관련 필드
    3. 상품 URL 도메인
    4. 판별할 수 없으면 None
    """

    item = item or {}
    display = display or {}

    # 1. 플랫폼을 명시하는 필드를 가장 먼저 검사합니다.
    explicit_values = [
        _get_mapping_value(
            item,
            "platform_id",
            "platform",
            "market_platform",
            "channel",
        ),
        _get_mapping_value(
            display,
            "platform_id",
            "platform",
            "market_platform",
            "channel",
        ),
    ]

    for value in explicit_values:
        platform_id = detect_platform_from_mall_name(
            value
        )

        if platform_id:
            return platform_id

    # 2. 몰 이름과 판매처 관련 필드를 검사합니다.
    mall_values = [
        _get_mapping_value(
            item,
            "mall_name",
            "mall",
            "market_name",
            "source",
            "source_name",
            "seller_name",
            "seller",
        ),
        _get_mapping_value(
            display,
            "mall_name",
            "mall",
            "market_name",
            "source",
            "source_name",
            "seller_name",
            "seller",
        ),
    ]

    for value in mall_values:
        platform_id = detect_platform_from_mall_name(
            value
        )

        if platform_id:
            return platform_id

    # 3. 상품 URL을 보조 신호로 사용합니다.
    url_values = [
        _get_mapping_value(
            item,
            "product_url",
            "detail_url",
            "link",
            "url",
            "landing_url",
        ),
        _get_mapping_value(
            display,
            "product_url",
            "detail_url",
            "link",
            "url",
            "landing_url",
        ),
    ]

    for value in url_values:
        platform_id = _detect_platform_from_url(
            value
        )

        if platform_id:
            return platform_id

    return None