"""p41 검토 3항목 + 단위가격 소비 경로 재현 (읽기 전용, 저장소 파일을 바꾸지 않음)."""
import builtins, json, sys, os
sys.path.insert(0, os.getcwd())
from app.services.ucp import discovery, mapping, schemas

print("## 1. 검증기 없을 때")
real_import = builtins.__import__
def no_jsonschema(name, *a, **k):
    if name.split(".")[0] in ("jsonschema", "referencing"):
        raise ImportError(name)
    return real_import(name, *a, **k)
builtins.__import__ = no_jsonschema
try:
    print("  validate_search_response →", schemas.validate_search_response({"products": []}, schema_url="https://ucp.dev/x.json", http=None))
finally:
    builtins.__import__ = real_import
print("  client.search: schema_valid None 이면 ok 를 바꾸지 않음 (client.py 103-110행) → check_ucp_catalog.py 는 '검증 안 함' 출력 후 mapping.to_cards 진행")
print("  requirements.txt 의 jsonschema/referencing:", [l.strip() for l in open("requirements.txt") if "jsonschema" in l or "referencing" in l] or "없음")

print("\n## 2. 프로필 캐시 TTL (discovery._max_age)")
for cc in ["max-age=10", "public, max-age=30", "max-age=600", "no-store", "private, max-age=5", "no-cache", ""]:
    print(f"  Cache-Control {cc!r:24} → 보관 {discovery._max_age({'Cache-Control': cc})}초")
print("  schemas._cache: TTL 없음 (프로세스 수명 동안 보관)")
print("  게시 점검(schemas.check_published_profile)의 max-age≥60 은 '우리 프로필의 게시 조건' — 위 캐시 보관 시간과 별개 로직")

print("\n## 3. 판매 단위 (mapping._is_single_unit 계열)")
fn = mapping.sold_each
print("  판정 함수:", fn.__name__)
for qu in [None, {"unit": "C62", "display_text": "each"}, {"unit": "C62", "display_text": "each", "increment": 6},
           {"unit": "LBR", "scale": 2, "increment": 25, "display_text": "lb"}, {"unit": "LBR", "scale": 2, "display_text": "lb"},
           {"unit": "KGM", "display_text": "kg"}]:
    print(f"  quantity_unit={json.dumps(qu, ensure_ascii=False)} → 한 개 가격 카드로 만듦: {fn({'quantity_unit': qu} if qu else {})}")

print("\n## 4. 판매자 단위가격이 비교 입력에 들어가는 경로")
from app.services.chat import explain
card = {"title": "UCP 시험 상품", "price": 10000, "per100g": 500, "score_use": "block", "key": "u1"}
print("  explain.choose 는 score_use 를 읽는가:", "score_use" in open("app/services/chat/explain.py").read())
enriched = explain.enrich(dict(card), {})
print("  explain.enrich 를 거친 뒤 per100g:", enriched.get("per100g"), "(판매자 값 500 → 상품명 중량이 없으면 None 으로 덮어씀)")
enriched2 = explain.enrich(dict(card, title="UCP 시험 상품 1kg"), {})
print("  상품명에 1kg 이 있으면:", enriched2.get("per100g"), "(판매자 unit_price 대신 재계산 — 사양 MUST NOT recompute 와 충돌)")
picked = explain.choose([dict(card, key="u1"), dict(card, key="u2", price=12000, per100g=300)])
print("  enrich 없이 choose 에 넣으면 1번 역할:", [(p['key'], p['role']) for p in picked['picks']][:2], "→ score_use='block' 이어도 per100g 로 '가성비' 선택")
print("  현재 app/ 안에서 ucp 카드를 공통 검색·대화에 넣는 코드: 없음 (미연결)")
