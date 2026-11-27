"""Shopify Global Catalog 검색 (UCP MCP `search_catalog`) — 2026-11-26.

- 주소: https://catalog.shopify.com/api/ucp/mcp (JSON-RPC tools/call, meta.ucp-agent.profile = 우리 플랫폼 프로필)
- 키(선택): Dev Dashboard › Agents 의 API 키(SHOPIFY_CATALOG_CLIENT_ID·SECRET) → api.shopify.com/auth/access_token
  (client_credentials, 60분) → Authorization: Bearer. 키가 없으면 키 없이 부른다(호출 한도가 낮음).
- **결과를 저장·캐시하지 않는다**(Shopify Catalog 안내: "Do not cache results or re-host merchant images").
  같은 검색이 동시에 들어오면 한 번만 부르고 응답이 끝나면 버린다(single-flight — 보관 아님). 토큰만 메모리에 둔다.
- 개인정보를 보내지 않는다: 검색어·배송 국가(KR)·통화만.
"""
from __future__ import annotations

import os
import threading
import time
import uuid
from dataclasses import dataclass, field

import requests

ENDPOINT = "https://catalog.shopify.com/api/ucp/mcp"
TOKEN_URL = "https://api.shopify.com/auth/access_token"
DEFAULT_PROFILE = "https://trendguide.kr/.well-known/ucp"
MAX_BYTES = 2_000_000
MAX_PARALLEL = 4                       # 동시에 Shopify 로 나가는 검색 수 (우리 서버·상대 한도 보호)

_slots = threading.BoundedSemaphore(MAX_PARALLEL)
_minute: list[float] = []                # 지난 60초 Shopify 호출 시각 (서버 전체 상한 — 2026-11-27 대화 결과 칸)
_minute_lock = threading.Lock()


def _per_min() -> int:
    try:
        return max(1, int(os.getenv("SHOPIFY_CATALOG_PER_MIN") or 60))
    except ValueError:
        return 60


def _take_minute_slot() -> bool:
    now = time.time()
    with _minute_lock:
        while _minute and now - _minute[0] > 60:
            _minute.pop(0)
        if len(_minute) >= _per_min():
            return False
        _minute.append(now)
        return True
_token_lock = threading.Lock()
_token: dict = {}
_flight_lock = threading.Lock()
_flights: dict[tuple, "_Flight"] = {}


@dataclass
class Offer:
    """화면에 보낼 상품 한 줄 — 받은 값 그대로(가격은 최소 단위 정수 → 표시는 화면에서)."""
    title: str
    url: str                            # 받은 상품 주소 그대로(귀속 파라미터 포함)
    checkout_url: str | None
    image: str | None
    price: int | None                   # 최소 단위(센트 등)
    currency: str | None
    seller: str | None
    seller_domain: str | None
    refund_policy: str | None
    available: bool | None


@dataclass
class Result:
    ok: bool
    offers: list[Offer] = field(default_factory=list)
    error: str | None = None
    code: str | None = None
    checked_at: float = field(default_factory=time.time)


def enabled() -> bool:
    return (os.getenv("SHOPIFY_CATALOG") or "1").strip() != "0"


def profile_url() -> str:
    url = (os.getenv("UCP_PLATFORM_PROFILE_URL") or "").strip()
    return url if url.startswith("https://") else DEFAULT_PROFILE


def _bearer(http) -> str | None:
    cid, sec = os.getenv("SHOPIFY_CATALOG_CLIENT_ID"), os.getenv("SHOPIFY_CATALOG_CLIENT_SECRET")
    if not (cid and sec):
        return None
    with _token_lock:
        if _token.get("v") and _token.get("exp", 0) > time.time() + 60:
            return _token["v"]
        try:
            r = http.post(TOKEN_URL, json={"client_id": cid, "client_secret": sec, "grant_type": "client_credentials"},
                          timeout=10, allow_redirects=False)
            tok = r.json().get("access_token") if r.status_code == 200 else None
        except Exception:  # noqa: BLE001 — 토큰 실패는 키 없이 부르기로
            tok = None
        if tok:
            _token.update(v=tok, exp=time.time() + 55 * 60)
        return tok


def request_body(query: str, *, ships_to: str = "KR", currency: str = "USD", limit: int = 8,
                 price_max: int | None = None) -> dict:
    catalog: dict = {"query": query, "context": {"address_country": ships_to, "currency": currency, "language": "ko"},
                     "filters": {"available": True, "ships_to": {"country": ships_to}},
                     "pagination": {"limit": max(1, min(int(limit), 50))}}
    if price_max:
        catalog["filters"]["price"] = {"max": int(price_max)}
    return {"jsonrpc": "2.0", "id": str(uuid.uuid4()), "method": "tools/call",
            "params": {"name": "search_catalog",
                       "arguments": {"meta": {"ucp-agent": {"profile": profile_url()}}, "catalog": catalog}}}


def _https(v) -> str | None:
    return v if isinstance(v, str) and v.startswith("https://") else None


def _money(m) -> tuple[int | None, str | None]:
    if not isinstance(m, dict):
        return None, None
    amt = m.get("amount")
    try:
        amt = int(amt) if amt is not None else None
    except (TypeError, ValueError):
        amt = None
    cur = m.get("currency") if isinstance(m.get("currency"), str) else None
    return amt, cur


def to_offers(data: dict) -> list[Offer]:
    """structuredContent.products → Offer. 판매 가능한 첫 변형(옵션)의 값 — 없으면 상품 최저가."""
    out: list[Offer] = []
    for p in data.get("products") or []:
        if not isinstance(p, dict) or not p.get("title"):
            continue
        variants = [v for v in p.get("variants") or [] if isinstance(v, dict)]
        v = next((x for x in variants if (x.get("availability") or {}).get("available") is not False), None)
        if v is None and variants:
            continue                                     # 모든 옵션 품절
        url = _https((v or {}).get("url")) or _https(p.get("url"))
        if not url:
            continue
        price, cur = _money((v or {}).get("price")) if v else _money((p.get("price_range") or {}).get("min"))
        seller = p.get("seller") if isinstance(p.get("seller"), dict) else ((v or {}).get("seller") or {})
        links = seller.get("links") if isinstance(seller.get("links"), (dict, list)) else {}
        refund = None
        if isinstance(links, dict):
            refund = _https(links.get("refund_policy"))
        elif isinstance(links, list):
            refund = next((_https(x.get("url")) for x in links if isinstance(x, dict) and x.get("type") == "refund_policy"), None)
        media = next((m for m in p.get("media") or [] if isinstance(m, dict) and m.get("type", "image") == "image"), {})
        out.append(Offer(title=str(p["title"])[:200], url=url, checkout_url=_https((v or {}).get("checkout_url")),
                         image=_https(media.get("url")), price=price, currency=cur,
                         seller=(seller.get("name") or None), seller_domain=(seller.get("domain") or None),
                         refund_policy=refund,
                         available=((v or {}).get("availability") or {}).get("available") if v else None))
    return out


def _call(body: dict, http) -> Result:
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    tok = _bearer(http)
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    if not _take_minute_slot():
        return Result(False, error="해외 상점 조회가 몰려 잠시 쉬어 가요", code="busy")
    if not _slots.acquire(timeout=8):
        return Result(False, error="요청이 몰려 잠시 뒤에 다시 시도해 주세요", code="busy")
    try:
        r = http.post(ENDPOINT, json=body, headers=headers, timeout=12, allow_redirects=False)
    except Exception as e:  # noqa: BLE001
        return Result(False, error=f"연결 실패 ({type(e).__name__})", code="network")
    finally:
        _slots.release()
    if len(r.content or b"") > MAX_BYTES:
        return Result(False, error="응답이 너무 큼", code="too_large")
    if r.status_code == 429:
        return Result(False, error="Shopify 호출 한도 — 잠시 뒤에 다시", code="rate_limited")
    if r.status_code in (401, 403):
        return Result(False, error="Shopify 인증 실패 — 키 확인", code="auth")
    try:
        data = r.json()
    except ValueError:
        return Result(False, error=f"JSON 아님 (HTTP {r.status_code})", code="bad_response")
    if not isinstance(data, dict):
        return Result(False, error="응답 형식 아님", code="bad_response")
    if data.get("error"):
        err = data["error"] if isinstance(data["error"], dict) else {}
        return Result(False, error=err.get("message") or "Shopify 오류", code=str(err.get("code") or "error"))
    res = data.get("result") or {}
    if res.get("isError"):
        return Result(False, error="Shopify 도구 오류", code="tool_error")
    sc = res.get("structuredContent")
    if not isinstance(sc, dict):
        return Result(False, error="structuredContent 없음", code="bad_response")
    ucp = sc.get("ucp") if isinstance(sc.get("ucp"), dict) else {}
    if ucp.get("status") == "error":
        msg = next((m for m in sc.get("messages") or [] if isinstance(m, dict)), {})
        return Result(False, error=msg.get("content") or "Shopify 오류", code=msg.get("code") or "error")
    return Result(True, offers=to_offers(sc))


class _Flight:
    def __init__(self):
        self.done = threading.Event()
        self.result: Result | None = None


def search(query: str, *, http=requests, ships_to: str = "KR", currency: str = "USD", limit: int = 8,
           price_max: int | None = None) -> Result:
    """한 번 부르고 끝(저장 없음). 같은 검색이 동시에 오면 먼저 온 호출의 결과를 같이 쓴다."""
    if not enabled():
        return Result(False, error="해외 직구 검색이 꺼져 있어요 (SHOPIFY_CATALOG=0)", code="disabled")
    q = " ".join((query or "").split())[:100]
    if not q:
        return Result(False, error="검색어 없음", code="empty")
    key = (q.lower(), ships_to, currency, limit, price_max)
    with _flight_lock:
        f = _flights.get(key)
        leader = f is None
        if leader:
            f = _flights[key] = _Flight()
    if not leader:
        f.done.wait(15)
        return f.result or Result(False, error="시간 초과", code="timeout")
    try:
        f.result = _call(request_body(q, ships_to=ships_to, currency=currency, limit=limit, price_max=price_max), http)
        return f.result
    finally:
        with _flight_lock:
            _flights.pop(key, None)                      # 응답이 끝나면 버림 — 다음 요청은 새로 부른다
        f.done.set()
