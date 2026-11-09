"""우리 플랫폼 프로필과 사용 여부 (p40).

UCP 판매자는 모든 요청의 플랫폼 프로필 URI(HTTP `UCP-Agent: profile="…"`, MCP meta `ucp-agent.profile`)를
직접 가져와 검증한다 — 공개 https 주소에 이 문서가 없으면 판매자가 `profile_unreachable` 로 거절한다
(2026-11-04 Shopify 판매자에 시험 호출로 확인).
"""
from __future__ import annotations

import os

SPEC_VERSION = "2026-08-25"
SUPPORTED_VERSIONS = ("2026-08-25", "2026-04-08")      # 협상 때 고를 수 있는 판(새 판이 앞)
SPEC = f"https://ucp.dev/{SPEC_VERSION}/specification/overview/"
CAPABILITIES = ("dev.ucp.shopping.catalog.search", "dev.ucp.shopping.catalog.lookup")


def profile_url() -> str | None:
    url = (os.getenv("UCP_PLATFORM_PROFILE_URL") or "").strip()
    return url if url.startswith("https://") else None


def enabled() -> bool:
    """UCP_CATALOG=1 이고 공개 https 프로필 주소가 있을 때만 실제 판매자에 요청한다."""
    return (os.getenv("UCP_CATALOG") or "0").strip() == "1" and profile_url() is not None


def platform_profile() -> dict:
    """우리 플랫폼 프로필 (사양 ucp.json platform_schema: services · capabilities · payment_handlers 필수).
    카탈로그 읽기만 광고한다 — 결제를 하지 않으므로 payment_handlers 는 비어 있다."""
    base = f"https://ucp.dev/{SPEC_VERSION}"
    return {"ucp": {
        "version": SPEC_VERSION,
        "services": {"dev.ucp.shopping": [
            {"version": SPEC_VERSION, "spec": SPEC, "transport": "rest",
             "schema": f"{base}/services/shopping/rest.openapi.json"},
            {"version": SPEC_VERSION, "spec": SPEC, "transport": "mcp",
             "schema": f"{base}/services/shopping/mcp.openrpc.json"}]},
        "capabilities": {
            "dev.ucp.shopping.catalog.search": [{"version": SPEC_VERSION, "spec": f"{base}/specification/shopping/catalog/",
                                                 "schema": f"{base}/schemas/shopping/catalog_search.json"}],
            "dev.ucp.shopping.catalog.lookup": [{"version": SPEC_VERSION, "spec": f"{base}/specification/shopping/catalog/",
                                                 "schema": f"{base}/schemas/shopping/catalog_lookup.json"}]},
        "payment_handlers": {},
    }}
