"""판매자 프로필(/.well-known/ucp) 읽기와 협상 (p40).

협상 (사양 overview): 정확한 판 하나를 고르고 → 양쪽이 광고한 capability 교집합 → capability 마다 공통 최고 판.
우리가 쓰는 것은 catalog.search(·lookup) 하나뿐이라, 그것이 없으면 이 판매자는 쓰지 않는다.

p41 (GPT 검토 22:31, 사양 overview 규범):
- 프로필·schema 를 가져올 때 https 만, 리다이렉트(3xx)를 따라가지 않는다 (MUST NOT follow redirects).
- capability·service 의 schema URL 출처는 이름의 namespace 와 맞아야 한다 — 'dev.ucp.shopping.catalog.search' 의
  schema 는 ucp.dev 에서 와야 한다 (MUST match … MUST reject the entity).  안 맞는 항목은 버린다.
- 캐시: 판매자 Cache-Control 을 그대로 따른다 — 헤더 없음·no-store·no-cache·private 는 보관 안 함 (p45).
- 협상 성공 = '이 판매자에게 검색을 보낼 수 있음'일 뿐, 실제 검색 성공·응답 스키마 적합은 client 에서 따로 판정한다.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field

from urllib.parse import urlsplit

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
    schemas: dict = field(default_factory=dict)              # 협상한 capability → schema URL (출처 검증 통과분)
    rejected: list[str] = field(default_factory=list)        # 출처 검증에 떨어진 항목


def valid_host(host: str) -> bool:
    return bool(_HOST_RE.match((host or "").strip().lower()))


def _https(url) -> str | None:
    url = (url or "").strip() if isinstance(url, str) else ""
    return url.rstrip("/") if url.startswith("https://") and " " not in url else None


def origin_ok(name: str, url: str | None) -> bool:
    """schema URL 출처 = 이름의 namespace (호스트를 뒤집은 값이 이름과 같거나 라벨 경계 접두사).  https 만."""
    if not url:
        return True                        # schema 를 밝히지 않은 항목은 출처 검사 대상 아님 (사양 기본 schema 사용)
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.hostname:
        return False
    rev = ".".join(reversed(parts.hostname.lower().split(".")))
    return name == rev or name.startswith(rev + ".")


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
    if not isinstance(caps, dict):         # 판 2026-01 형식(목록)은 이름만 읽는다
        caps = {c.get("name"): [c] for c in caps if isinstance(c, dict) and c.get("name")}
    names, schemas, rejected = [], {}, []
    for name, entries in caps.items():
        entries = entries if isinstance(entries, list) else [entries]
        ok_entries = [e for e in entries if isinstance(e, dict) and origin_ok(name, e.get("schema"))]
        if not ok_entries:
            rejected.append(name)
            continue
        names.append(name)
        pick = next((e for e in ok_entries if e.get("version") == version), ok_entries[0])
        schemas[name] = pick.get("schema")
    m = Merchant(host, False, capabilities=names, version=version, schemas=schemas, rejected=rejected)
    if version is None:
        m.reason = f"공통 판 없음 (판매자 {', '.join(theirs) or '없음'})"
        return m
    m.search = "dev.ucp.shopping.catalog.search" in names
    m.lookup = "dev.ucp.shopping.catalog.lookup" in names
    if not m.search:
        m.reason = ("catalog.search schema 출처 불일치" if "dev.ucp.shopping.catalog.search" in rejected
                    else "catalog.search 미지원")
        return m
    services = ((ucp.get("services") or {}).get("dev.ucp.shopping") or []) if isinstance(ucp.get("services"), dict) else []
    usable = {}
    for svc in services:
        if not isinstance(svc, dict):
            continue
        if not origin_ok("dev.ucp.shopping", svc.get("schema")):
            m.rejected.append(f"dev.ucp.shopping[{svc.get('transport')}]")
            continue
        usable.setdefault(svc.get("transport"), _https(svc.get("endpoint")))
    for transport in ("rest", "mcp"):          # REST 를 먼저, 없으면 MCP (Shopify 는 MCP 만 광고)
        if usable.get(transport):
            m.transport, m.endpoint = transport, usable[transport]
            break
    if not m.endpoint:
        m.reason = "쓸 수 있는 전송(rest·mcp https endpoint) 없음"
        return m
    m.ok = True
    return m


def cache_seconds(headers, now: float | None = None) -> int:
    """판매자 프로필을 몇 초 재사용할지 (p45, GPT 검토 11-06).  판매자의 Cache-Control 을 그대로 따른다:
    헤더 없음 → 0 (보관 안 함, 매번 가져옴) · no-store·private → 0 · no-cache → 0 (재사용 전 재검증 = 다시 가져옴)
    · max-age=N → 남은 유효 시간 (최대 1일).  우리 프로필의 게시 규칙(public·max-age≥60)과는 별개다.
    p46: max-age 는 받은 시점부터 새로 시작하지 않는다 (RFC 9111) — 남은 시간 = max-age − 현재 나이,
    현재 나이 = max(Age 헤더, 지금 − Date 헤더)."""
    import email.utils

    h = headers or {}
    cc = (h.get("Cache-Control") or h.get("cache-control") or "").lower()
    if not cc or any(d in cc for d in ("no-store", "no-cache", "private")):
        return 0
    hit = re.search(r"max-age=(\d+)", cc)
    if not hit:
        return 0
    age = 0
    raw_age = (h.get("Age") or h.get("age") or "").strip()
    if raw_age.isdigit():
        age = int(raw_age)
    raw_date = h.get("Date") or h.get("date")
    if raw_date and now is not None:
        try:
            age = max(age, int(now - email.utils.parsedate_to_datetime(raw_date).timestamp()))
        except (TypeError, ValueError, OverflowError):
            pass
    return max(0, min(int(hit.group(1)) - max(age, 0), 86_400))


def discover(host: str, *, http, now=time.time) -> Merchant:
    """https://<host>/.well-known/ucp 를 읽어 협상한다.  http: requests 와 같은 get(url, timeout, headers)."""
    host = (host or "").strip().lower()
    if not valid_host(host):
        return Merchant(host, False, "호스트 형식 아님")
    hit = _cache.get(host)
    if hit and hit[0] > now():
        return hit[1]
    try:
        r = http.get(f"https://{host}/.well-known/ucp", timeout=10, allow_redirects=False,
                     headers={"Accept": "application/json", "User-Agent": "commerce-ai-ucp/0.1"})
    except Exception as e:  # noqa: BLE001
        return Merchant(host, False, f"연결 실패 ({type(e).__name__})")
    if 300 <= r.status_code < 400:
        m = Merchant(host, False, f"프로필 리다이렉트 (HTTP {r.status_code}) — 사양상 따라가지 않음")
    elif r.status_code != 200:
        m = Merchant(host, False, f"이 주소에서 유효 프로필 미확인 (HTTP {r.status_code})")
    elif len(r.content or b"") > MAX_BYTES:
        m = Merchant(host, False, "프로필이 너무 큼")
    else:
        try:
            m = negotiate(host, r.json())
        except ValueError:
            m = Merchant(host, False, "이 주소에서 유효 프로필 미확인 (JSON 아님)")
    ttl = cache_seconds(getattr(r, "headers", {}), now=now())
    if ttl > 0:
        _cache[host] = (now() + ttl, m)
    else:
        _cache.pop(host, None)
    return m


def clear_cache() -> None:
    _cache.clear()
