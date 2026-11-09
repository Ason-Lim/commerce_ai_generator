"""협상한 capability 의 schema 가져오기·응답 검증 (p41, 사양 overview "Platforms MUST fetch and compose schemas for
negotiated capabilities before making requests" · 요청/응답 검증).

- 가져오기: https 만, 리다이렉트를 따라가지 않음, 크기 제한, 출처(origin) = 이름의 namespace (dev.ucp.* → ucp.dev).
- 합성: 우리가 활성화하는 확장(extension)은 없다 → 기본 capability schema 그대로가 합성 결과다.
  확장을 켜는 단계가 오면 여기서 base + extension 을 합친다.
- 검증기: jsonschema + referencing 은 필수 (p45, requirements.txt).  없으면 판매자에게 요청하지 않는다.
- p47: 문서 안에 포함된 리소스($id)를 가리키는 참조는 외부에서 가져오지 않는다 (별도 주소가 404여도 해석 가능하면 통과).
- 순서 (p45·p46): prepare() 가 요청 전에 협상 schema·모든 참조를 확보하고(중첩 $id 기준 주소 반영) 검증기를 만들어 모든
  $ref 해석을 확인 → 요청 → 그 검증기로만 검증 (검증 중 조회 없음).  지원하지 않는 참조 구조·조회 실패는 요청 전에 보류.
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
    try:
        r = http.get(url, timeout=15, allow_redirects=False,
                     headers={"Accept": "application/schema+json, application/json"})
    except Exception as e:  # noqa: BLE001 — p46: 타임아웃·연결 실패도 '확보 실패'로 (호출부까지 예외가 새지 않게)
        raise SchemaError(f"schema 조회 실패 ({type(e).__name__}): {url}") from e
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


def require_validator() -> None:
    """jsonschema·referencing 은 UCP 사용 시 필수 (p45, requirements.txt).  없으면 SchemaError — 판매자 요청 전에 중단."""
    try:
        import jsonschema  # noqa: F401
        import referencing  # noqa: F401
    except ImportError as e:
        raise SchemaError("jsonschema·referencing 없음 — UCP 판매자 요청을 하지 않음 (requirements.txt 설치 필요)") from e


UNSUPPORTED_KEYS = ("$dynamicRef", "$recursiveRef", "$dynamicAnchor", "$recursiveAnchor")


def embedded_ids(doc, base: str) -> set[str]:
    """문서 안의 리소스 주소들 (최상위 $id 와 중첩 $id, 기준 주소 반영, '#' 앞부분) (p47).
    이 주소를 가리키는 참조는 문서 안에서 해석되므로 따로 가져오지 않는다 (JSON Schema 2020-12 core §9.2 — 포함 리소스)."""
    from urllib.parse import urljoin

    out: set[str] = set()

    def go(node, b):
        if isinstance(node, dict):
            if isinstance(node.get("$id"), str):
                b = urljoin(b, node["$id"])
                out.add(b.split("#")[0])
            for k, v in node.items():
                if k not in ("const", "enum", "examples", "default"):
                    go(v, b)
        elif isinstance(node, list):
            for v in node:
                go(v, b)

    go(doc, base)
    return out


def _walk(node, base: str):
    """(그 위치의 기준 주소, $ref) 를 모두 낸다.  중첩 $id 가 있으면 그 아래의 기준 주소를 바꾼다 (p46).
    지원하지 않는 참조 구조($dynamicRef 등)는 SchemaError — 요청 전에 보류."""
    from urllib.parse import urljoin

    if isinstance(node, dict):
        if isinstance(node.get("$id"), str):
            base = urljoin(base, node["$id"])
        bad = [k for k in UNSUPPORTED_KEYS if k in node]
        if bad:
            raise SchemaError(f"지원하지 않는 참조 구조 {bad[0]} ({base})")
        if isinstance(node.get("$ref"), str):
            yield base, node["$ref"]
        for k, v in node.items():
            if k not in ("$ref", "const", "enum", "examples", "default"):
                yield from _walk(v, base)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v, base)


def _subresources(doc, base: str):
    """(절대 주소, 그 노드) — 중첩 $id 를 가진 포함 리소스 (최상위 제외) (p47)."""
    from urllib.parse import urljoin

    def go(node, b, top):
        if isinstance(node, dict):
            if isinstance(node.get("$id"), str):
                b = urljoin(b, node["$id"])
                if not top:
                    yield b.split("#")[0], node
            for k, v in node.items():
                if k not in ("const", "enum", "examples", "default"):
                    yield from go(v, b, False)
        elif isinstance(node, list):
            for v in node:
                yield from go(v, b, False)

    yield from go(doc, base, True)


class Prepared:
    """요청 전에 만든 검증 준비물 — 문서 묶음·참조가 모두 해석된 registry·search_response 검증기 (p46)."""

    def __init__(self, url: str, bundle: dict[str, dict], validator):
        self.url, self.bundle, self.validator = url, bundle, validator


def prepare(schema_url: str, *, http, max_docs: int = 80) -> Prepared:
    """협상한 schema 와 모든 참조를 **요청 전에** 가져오고, 검증기를 만들고, 모든 $ref 가 실제로 해석되는지 확인한다.
    p45: 문서 수집.  p46: 중첩 $id 기준 주소 반영 · 리소스·검증기 구성과 참조 해석 확인까지 요청 전에 ·
    네트워크 예외도 SchemaError.  하나라도 안 되면 SchemaError — 호출한 쪽은 판매자에게 요청을 보내지 않는다."""
    from urllib.parse import urljoin

    require_validator()
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import SchemaError as JsonSchemaError
    from referencing import Registry, Resource
    from referencing.exceptions import Unresolvable
    from referencing.jsonschema import DRAFT202012

    if not schema_url:
        raise SchemaError("협상한 catalog.search schema 주소 없음")
    root = schema_url.split("#")[0]
    bundle: dict[str, dict] = {}
    embedded: set[str] = set()       # p47: 이미 받은 문서 안에 들어 있는 리소스 주소 — 따로 GET 하지 않는다
    pending: list[str] = []           # 참조된 외부 문서 후보 (받은 문서를 모두 훑은 뒤 하나씩 가져온다)
    failed: dict[str, SchemaError] = {}

    def take(url: str, doc: dict) -> None:
        bundle[url] = doc
        embedded.update(u for u in embedded_ids(doc, url) if u != url)
        for base, ref in _walk(doc, url):
            target = urljoin(base, ref).split("#")[0]
            if target and target not in bundle:
                pending.append(target)

    take(root, fetch(root, http=http))
    while pending:
        url = pending.pop(0)
        if url in bundle or url in embedded or url in failed:
            continue                  # 문서 안에서 해석되는 참조는 외부에서 가져오지 않는다
        if len(bundle) >= max_docs:
            raise SchemaError(f"참조 schema 가 너무 많음 (>{max_docs})")
        try:
            take(url, fetch(url, http=http))
        except SchemaError as e:      # 뒤에 받는 문서에 포함된 리소스일 수 있다 — 끝까지 본 뒤 판정
            failed[url] = e
    missing = [u for u in failed if u not in embedded]
    if missing:
        raise failed[missing[0]]
    for url in [u for u in bundle if u in embedded and u != root]:
        del bundle[url]               # 같은 주소가 문서 안에도 있으면 문서 안의 것을 쓴다 (중복 등록 방지)

    def no_network(uri):
        raise SchemaError(f"미리 확보하지 않은 참조: {uri}")

    try:
        resources = [(u, Resource.from_contents(d, default_specification=DRAFT202012)) for u, d in bundle.items()]
        resources += [(u, Resource.from_contents(node, default_specification=DRAFT202012))
                      for url, d in bundle.items() for u, node in _subresources(d, url)]   # p47: 포함 리소스도 절대 주소로
        registry = Registry(retrieve=no_network).with_resources(resources).crawl()
        for url, doc in bundle.items():
            Draft202012Validator.check_schema(doc)
            for base, ref in _walk(doc, url):
                registry.resolver(base_uri=base).lookup(ref)              # 해석 안 되면 Unresolvable
        registry.resolver(base_uri=root).lookup(f"{root}#/$defs/search_response")
        validator = Draft202012Validator({"$ref": f"{root}#/$defs/search_response"}, registry=registry)
    except SchemaError:
        raise
    except (Unresolvable, JsonSchemaError) as e:
        raise SchemaError(f"schema 참조 해석 실패 ({type(e).__name__}: {str(e)[:120]})") from e
    except Exception as e:  # noqa: BLE001
        raise SchemaError(f"schema 준비 실패 ({type(e).__name__}: {str(e)[:120]})") from e
    return Prepared(root, bundle, validator)


def validate_search_response(data: dict, prepared: Prepared) -> tuple[bool, list[str]]:
    """요청 전에 만든 검증기로만 검증한다 — 검증 중 네트워크 조회 없음.  (통과 여부, 오류들)."""
    try:
        errors = [f"{'/'.join(map(str, e.absolute_path)) or '(최상위)'}: {e.message[:160]}"
                  for e in prepared.validator.iter_errors(data)]
    except Exception as e:  # noqa: BLE001
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
