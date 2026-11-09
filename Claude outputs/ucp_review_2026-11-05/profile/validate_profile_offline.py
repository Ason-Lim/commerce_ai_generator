"""생성 프로필을 보관된 ucp.dev 2026-08-25 공식 schema 로 오프라인 검증 (네트워크 없음)."""
import json, sys, os
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
FIX = "tests/services/ucp/fixtures/schemas_2026-08-25"
idx = json.load(open(f"{FIX}/_index.json"))
url2file = idx.get("files", {})
def retrieve(uri):
    uri = uri.split("#")[0]
    name = url2file.get(uri) or uri.split("/schemas/")[-1].replace("/", "__")
    return Resource.from_contents(json.load(open(os.path.join(FIX, name))))
root = "https://ucp.dev/2026-08-25/schemas/ucp.json"
reg = Registry(retrieve=retrieve)
prof = json.load(open(sys.argv[1]))
errs = list(Draft202012Validator({"$ref": f"{root}#/$defs/platform_schema"}, registry=reg).iter_errors(prof.get("ucp")))
print("platform_schema 오류:", len(errs))
for e in errs[:10]: print(" -", "/".join(map(str, e.absolute_path)), e.message[:200])
