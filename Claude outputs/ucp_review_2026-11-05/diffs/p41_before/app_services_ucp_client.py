"""catalog.search 호출 (p40) — REST: POST {endpoint}/catalog/search · MCP: tools/call search_catalog.

결과는 판매자 응답 그대로(dict) 돌려주고, 상품 카드 변환은 mapping.py 가 한다.
실패도 예외 대신 SearchOutcome 으로 — 판매자 하나가 실패해도 다른 결과는 보여 줄 수 있게 (한 판매처 장애 격리).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from app.services.ucp import platform
from app.services.ucp.discovery import Merchant

MAX_BYTES = 2_000_000


@dataclass
class SearchOutcome:
    host: str
    ok: bool
    response: dict | None = None
    error: str | None = None            # 사람이 읽는 사유
    code: str | None = None             # 판매자 오류 코드 (profile_unreachable · not_found · rate_limited …)
    continue_url: str | None = None     # 판매자가 준 웹 이동 주소 (협상 실패 등)
    messages: list = field(default_factory=list)


def search_request(query: str, *, limit: int = 10, country: str = "KR", language: str = "ko-KR",
                   currency: str = "KRW") -> dict:
    """사양 catalog_search search_request.  context 는 비인증 힌트 — 개인정보(주소·IP)는 넣지 않는다."""
    return {"query": query, "context": {"address_country": country, "language": language, "currency": currency},
            "pagination": {"limit": max(1, min(int(limit), 50))}}


def _continue(data) -> str | None:
    url = (data or {}).get("continue_url") if isinstance(data, dict) else None
    return url if isinstance(url, str) and url.startswith("https://") else None


def search(merchant: Merchant, query: str, *, http, limit: int = 10, profile_url: str | None = None) -> SearchOutcome:
    """판매자 하나에 상품 검색.  profile_url 이 없으면(공개 프로필 없음) 호출하지 않는다."""
    profile = profile_url or platform.profile_url()
    if not merchant.ok:
        return SearchOutcome(merchant.host, False, error=merchant.reason or "쓸 수 없는 판매자")
    if not profile:
        return SearchOutcome(merchant.host, False, error="우리 플랫폼 프로필 주소(UCP_PLATFORM_PROFILE_URL) 없음",
                             code="no_platform_profile")
    body = search_request(query, limit=limit)
    rid = str(uuid.uuid4())
    try:
        if merchant.transport == "rest":
            r = http.post(f"{merchant.endpoint}/catalog/search", json=body, timeout=15,
                          headers={"Content-Type": "application/json", "Accept": "application/json",
                                   "Request-Id": rid, "UCP-Agent": f'profile="{profile}"'})
        else:
            r = http.post(merchant.endpoint, timeout=15,
                          headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
                          json={"jsonrpc": "2.0", "id": rid, "method": "tools/call",
                                "params": {"name": "search_catalog",
                                           "arguments": {"meta": {"ucp-agent": {"profile": profile}}, "catalog": body}}})
    except Exception as e:  # noqa: BLE001
        return SearchOutcome(merchant.host, False, error=f"연결 실패 ({type(e).__name__})", code="network")
    if len(r.content or b"") > MAX_BYTES:
        return SearchOutcome(merchant.host, False, error="응답이 너무 큼", code="too_large")
    if r.status_code == 429:
        return SearchOutcome(merchant.host, False, error="판매자 호출 한도 초과", code="rate_limited")
    try:
        data = r.json()
    except ValueError:
        return SearchOutcome(merchant.host, False, error=f"JSON 아님 (HTTP {r.status_code})", code="bad_response")
    if not isinstance(data, dict):
        return SearchOutcome(merchant.host, False, error="응답 형식 아님", code="bad_response")
    if merchant.transport == "mcp":
        if data.get("error"):
            err = data["error"]
            detail = err.get("data") if isinstance(err.get("data"), dict) else {}
            return SearchOutcome(merchant.host, False, error=err.get("message") or "판매자 오류",
                                 code=detail.get("code") or str(err.get("code")), continue_url=_continue(detail))
        result = (data or {}).get("result") or {}
        if result.get("isError"):
            return SearchOutcome(merchant.host, False, error="판매자 도구 오류", code="tool_error")
        data = result.get("structuredContent")
        if not isinstance(data, dict):
            return SearchOutcome(merchant.host, False, error="structuredContent 없음", code="bad_response")
    elif r.status_code != 200:
        return SearchOutcome(merchant.host, False, error=f"HTTP {r.status_code}", code=str(r.status_code),
                             continue_url=_continue(data))
    ucp = data.get("ucp")
    messages = data.get("messages") if isinstance(data.get("messages"), list) else []
    if isinstance(ucp, dict) and ucp.get("status") == "error":
        first = next((m for m in messages if isinstance(m, dict)), {})
        return SearchOutcome(merchant.host, False, error=first.get("content") or "판매자 오류",
                             code=first.get("code"), continue_url=_continue(data), messages=messages)
    if not isinstance(data.get("products"), list):
        return SearchOutcome(merchant.host, False, error="products 없음", code="bad_response")
    return SearchOutcome(merchant.host, True, response=data, messages=messages)
