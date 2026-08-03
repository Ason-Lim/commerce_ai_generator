from __future__ import annotations

from urllib.parse import quote_plus


KURLY_HOME_URL = "https://www.kurly.com/"
KURLY_SEARCH_BASE_URL = "https://www.kurly.com/search"


def build_kurly_search_url(
    keyword: str | None,
) -> str:
    """컬리 검색 URL을 생성합니다."""

    normalized_keyword = " ".join(
        str(keyword or "").strip().split()
    )

    if not normalized_keyword:
        return ""

    return (
        f"{KURLY_SEARCH_BASE_URL}"
        f"?sword={quote_plus(normalized_keyword)}"
    )