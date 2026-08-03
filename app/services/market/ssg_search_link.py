from __future__ import annotations

from urllib.parse import quote_plus


SSG_SEARCH_BASE_URL = "https://www.ssg.com/search.ssg"


def build_ssg_search_url(
    keyword: str | None,
) -> str:
    """SSG.COM 통합검색 이동 URL을 생성합니다."""

    normalized_keyword = " ".join(
        str(keyword or "").strip().split()
    )

    if not normalized_keyword:
        return "https://www.ssg.com/"

    encoded_keyword = quote_plus(
        normalized_keyword
    )

    return (
        f"{SSG_SEARCH_BASE_URL}"
        f"?query={encoded_keyword}"
    )
