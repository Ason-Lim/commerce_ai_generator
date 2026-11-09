"""판매자 프로필(/.well-known/ucp) 읽기와 협상 (p40).

협상 (사양 overview): 정확한 판 하나를 고르고 → 양쪽이 광고한 capability 교집합 → capability 마다 공통 최고 판.
우리가 쓰는 것은 catalog.search(·lookup) 하나뿐이라, 그것이 없으면 이 판매자는 쓰지 않는다.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field

from app.services.ucp import platform

MAX_BYTES = 256_000
_HOST_RE = re.compile(r"^(?=.{1,253}$)[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$")
_cache: dict[str, tuple[float, "Merchant"]] = {}


@dataclass
class Merchant:
    host: str
    ok: bool
    reason: str = ""                          # 쓰지 못하는 이유 (ok=False)
    version: str | None = None                # 협상한 판
    transport: str | None = None              # 'rest' | 'mcp'
    endpoint: str | None = None
    capabilities: list[str] = field(default_factory=list)   # 판매자가 광고한 전체
    search: bool = False
    lookup: bool = False


def valid_host(host: str) -> bool:
    return bool(_HOST_RE.match((host or "").strip().lower()))


def _https(url) -> str | None:
    url = (url or "").strip() if isinstance(url, str) else ""
    return url.rstrip("/") if url.startswith("https://") and " " not in url else None


def _versions(ucp: dict) -> list[str]:
    out = [ucp.get("version")] if isinstance(ucp.get("version"), str) else []
    sv = ucp.get("supported_versions")
    if isinstance(sv, dict):
        out += [k for k in sv if isinstance(k, str)]
    elif isinstance(sv, list):
        out += [v for v in sv if isinstance(v, str)]
    return out


def negotiate(host: str, doc: dict) -> Merchant:
    """프로필 문서 → Merchant.  판·전송·endpoint·catalog.search 가 모두 맞아야 ok."""
    ucp = (doc or {}).get("ucp") if isinstance(doc, dict) else None
    if not isinstance(ucp, dict):
        return Merchant(host, False, "프로필 형식 아님")
    theirs = _versions(ucp)
    version = next((v for v in platform.SUPPORTED_VERSIONS if v in theirs), None)
    caps = ucp.get("capabilities") or {}
    names = list(caps) if isinstance(caps, dict) else [c.get("name") for c in caps if isinstance(c, dict) and c.get("name")]
    m = Merchant(host, False, capabilities=names, version=version)
    if version is None:
        m.reason = f"공통 판 없음 (판매자 {', '.join(theirs) or '없음'})"
        return m
    m.search = "dev.ucp.shopping.catalog.search" in names
    m.lookup = "dev.ucp.shopping.catalog.lookup" in names
    if not m.search:
        m.reason = "catalog.search 미지원"
        return m
    services = ((ucp.get("services") or {}).get("dev.ucp.shopping") or []) if isinstance(ucp.get("services"), dict) else []
    usable = {s.get("transport"): _https(s.get("endpoint")) for s in services if isinstance(s, dict)}
    for transport in ("rest", "mcp"):          # REST 를 먼저, 없으면 MCP (Shopify 는 MCP 만 광고)
        if usable.get(transport):
            m.transport, m.endpoint = transport, usable[transport]
            break
    if not m.endpoint:
        m.reason = "쓸 수 있는 전송(rest·mcp https endpoint) 없음"
        return m
    m.ok = True
    return m


def _max_age(headers) -> int:
    cc = (headers or {}).get("Cache-Control") or (headers or {}).get("cache-control") or ""
    hit = re.search(r"max-age=(\d+)", cc)
    return min(int(hit.group(1)), 86_400) if hit else 3_600


def discover(host: str, *, http, now=time.time) -> Merchant:
    """https://<host>/.well-known/ucp 를 읽어 협상한다.  http: requests 와 같은 get(url, timeout, headers)."""
    host = (host or "").strip().lower()
    if not valid_host(host):
        return Merchant(host, False, "호스트 형식 아님")
    hit = _cache.get(host)
    if hit and hit[0] > now():
        return hit[1]
    try:
        r = http.get(f"https://{host}/.well-known/ucp", timeout=10,
                     headers={"Accept": "application/json", "User-Agent": "commerce-ai-ucp/0.1"})
    except Exception as e:  # noqa: BLE001
        return Merchant(host, False, f"연결 실패 ({type(e).__name__})")
    if r.status_code != 200:
        m = Merchant(host, False, f"프로필 없음 (HTTP {r.status_code})")
    elif len(r.content or b"") > MAX_BYTES:
        m = Merchant(host, False, "프로필이 너무 큼")
    else:
        try:
            m = negotiate(host, r.json())
        except ValueError:
            m = Merchant(host, False, "프로필이 JSON 아님")
    _cache[host] = (now() + _max_age(getattr(r, "headers", {})), m)
    return m


def clear_cache() -> None:
    _cache.clear()
