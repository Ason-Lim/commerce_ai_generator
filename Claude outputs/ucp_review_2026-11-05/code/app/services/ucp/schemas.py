"""협상한 capability 의 schema 가져오기·응답 검증 (p41, 사양 overview "Platforms MUST fetch and compose schemas for
negotiated capabilities before making requests" · 요청/응답 검증).

- 가져오기: https 만, 리다이렉트를 따라가지 않음, 크기 제한, 출처(origin) = 이름의 namespace (dev.ucp.* → ucp.dev).
- 합성: 우리가 활성화하는 확장(extension)은 없다 → 기본 capability schema 그대로가 합성 결과다.
  확장을 켜는 단계가 오면 여기서 base + extension 을 합친다.
- 검증기: jsonschema + referencing (맥 .venv 에 있음).  없으면 검증하지 않았다고 표시한다 (통과로 치지 않음).
- schema 안의 $ref 도 같은 규칙으로 가져온다 (ucp.dev 판 경로).
"""
from __future__ import annotations

from urllib.parse import urlsplit

from app.services.ucp.discovery import origin_ok

MAX_BYTES = 1_000_000
SEARCH = "dev.ucp.shopping.catalog.search"
_cache: dict[str, dict] = {}


class SchemaError(Exception):
    pass


def default_url(capability: str, version: str) -> str | None:
    """판매자가 schema 를 밝히지 않았을 때 사양의 기본 schema (판별)."""
    return {SEARCH: f"https://ucp.dev/{version}/schemas/shopping/catalog_search.json"}.get(capability)


def fetch(url: str, *, http, name: str = "dev.ucp") -> dict:
    if url in _cache:
        return _cache[url]
    parts = urlsplit(url)
    if parts.scheme != "https" or not origin_ok(name, url):
        raise SchemaError(f"schema 출처 불일치: {url}")
    r = http.get(url, timeout=15, allow_redirects=False, headers={"Accept": "application/schema+json, application/json"})
    if r is None or r.status_code != 200:
        raise SchemaError(f"schema HTTP {getattr(r, 'status_code', None)}: {url}")
    if len(r.content or b"") > MAX_BYTES:
        raise SchemaError(f"schema 너무 큼: {url}")
    try:
        doc = r.json()
    except ValueError as e:
        raise SchemaError(f"schema JSON 아님: {url}") from e
    _cache[url] = doc
    return doc


def validate_search_response(data: dict, *, schema_url: str, http) -> tuple[bool | None, list[str]]:
    """(검증 결과, 오류들).  결과 None = 검증기 없음(검증 안 함)."""
    try:
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
    except ImportError:
        return None, ["jsonschema 없음 — 응답 스키마 검증 안 함"]
    try:
        root = fetch(schema_url, http=http)

        def retrieve(uri):
            return Resource.from_contents(fetch(uri.split("#")[0], http=http))

        registry = Registry(retrieve=retrieve).with_resource(schema_url, Resource.from_contents(root))
        validator = Draft202012Validator({"$ref": f"{schema_url}#/$defs/search_response"}, registry=registry)
        errors = [f"{'/'.join(map(str, e.absolute_path)) or '(최상위)'}: {e.message[:160]}"
                  for e in validator.iter_errors(data)]
    except SchemaError as e:
        return False, [str(e)]
    except Exception as e:  # noqa: BLE001 — 참조 해석 실패 등
        return False, [f"검증 실패 ({type(e).__name__}: {str(e)[:120]})"]
    return not errors, errors[:20]


def check_published_profile(url: str, *, http) -> list[str]:
    """우리 프로필 게시 상태 점검 (사양 overview 게시 규범) → 문제 목록 (빈 목록 = 통과).
    https · 리다이렉트 없음(3xx 금지) · Cache-Control 에 public + max-age ≥ 60, private/no-store/no-cache 없음 ·
    JSON · ucp.json platform_schema 적합.  통과해도 '판매자가 실제로 받아 주는지'는 별개 (실제 검색으로 확인)."""
    import re

    problems = []
    if not url.startswith("https://"):
        return ["https 주소가 아님"]
    try:
        r = http.get(url, timeout=10, allow_redirects=False, headers={"Accept": "application/json"})
    except Exception as e:  # noqa: BLE001
        return [f"접속 실패 ({type(e).__name__})"]
    if 300 <= r.status_code < 400:
        return [f"리다이렉트 (HTTP {r.status_code} → {r.headers.get('Location')}) — 프로필 주소는 리다이렉트 금지"]
    if r.status_code != 200:
        return [f"HTTP {r.status_code}"]
    cc = (r.headers.get("Cache-Control") or "").lower()
    age = re.search(r"max-age=(\d+)", cc)
    if "public" not in cc or not age or int(age.group(1)) < 60:
        problems.append(f"Cache-Control 에 public 과 max-age≥60 필요 (지금: '{cc or '없음'}')")
    if any(d in cc for d in ("private", "no-store", "no-cache")):
        problems.append(f"Cache-Control 에 private/no-store/no-cache 금지 (지금: '{cc}')")
    if "json" not in (r.headers.get("Content-Type") or "").lower():
        problems.append(f"Content-Type 이 JSON 아님 ({r.headers.get('Content-Type')})")
    try:
        doc = r.json()
    except ValueError:
        return problems + ["JSON 아님"]
    try:
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
    except ImportError:
        return problems + ["jsonschema 없음 — 스키마 적합성 확인 안 함"]
    version = ((doc or {}).get("ucp") or {}).get("version") or ""
    root = f"https://ucp.dev/{version}/schemas/ucp.json"
    try:
        registry = Registry(retrieve=lambda uri: Resource.from_contents(fetch(uri.split("#")[0], http=http)))
        errors = list(Draft202012Validator({"$ref": f"{root}#/$defs/platform_schema"}, registry=registry)
                      .iter_errors((doc or {}).get("ucp")))
    except Exception as e:  # noqa: BLE001
        return problems + [f"스키마 확인 실패 ({type(e).__name__})"]
    return problems + [f"스키마: {'/'.join(map(str, e.absolute_path)) or '(최상위)'} {e.message[:120]}" for e in errors[:10]]


def clear_cache() -> None:
    _cache.clear()
