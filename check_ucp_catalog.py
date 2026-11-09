# check_ucp_catalog.py — UCP 판매자 카탈로그 시험 (읽기 전용, 결제·장바구니 없음). (2026-11-04 p40)
# 등록부(data/ucp/merchants.csv, 없으면 data/ucp/merchants_template.csv)의 '사용·시험' 판매자에 대해
#   1) /.well-known/ucp 발견·협상  2) 우리 프로필 주소가 있으면 catalog.search 1회  3) 상품 카드로 바꾼 결과를 보여 준다.
# 화면·DB 에는 아무것도 반영하지 않는다.  우리 프로필 주소: .env UCP_PLATFORM_PROFILE_URL (공개 https).
# 사용: python check_ucp_catalog.py "wool runner"        (판매자 지정: python check_ucp_catalog.py 감귤 mall.example.kr)
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.getcwd(), ".env"))
from app.services.ucp import client, discovery, mapping, platform, registry, schemas  # noqa: E402

query = sys.argv[1] if len(sys.argv) > 1 else "감귤"
hosts = [{"host": h, "name": h} for h in sys.argv[2:]]
if not hosts:
    if not registry.path().exists() and Path("data/ucp/merchants_template.csv").exists():
        os.environ["UCP_MERCHANTS_CSV"] = "data/ucp/merchants_template.csv"
    hosts = registry.load(("사용", "시험"))
profile = platform.profile_url()
print(f"우리 프로필: {profile or '없음 (UCP_PLATFORM_PROFILE_URL) — 발견·협상만 확인'}")
if profile:
    problems = schemas.check_published_profile(profile, http=requests)
    print("  게시 점검(https·리다이렉트 없음·Cache-Control·JSON·platform 스키마): "
          + ("통과 — 판매자가 실제로 받아 주는지는 아래 검색으로 확인" if not problems else "문제 있음"))
    for p in problems:
        print(f"   ! {p}")
for m in hosts:
    merchant = discovery.discover(m["host"], http=requests)
    print(f"\n[{m['host']}] 협상: {'가능' if merchant.ok else '불가'} — 판 {merchant.version}, 전송 {merchant.transport}, "
          f"search {merchant.search}, lookup {merchant.lookup}" + ("" if merchant.ok else f", 사유 {merchant.reason}"))
    if not (merchant.ok and profile):
        continue
    out = client.search(merchant, query, http=requests, limit=5, profile_url=profile)
    if not out.ok:
        for e in out.schema_errors[:5]:
            print(f"   · {e}")
        print(f"  검색 실패: {out.code} — {out.error}" + (f" (이동 주소 {out.continue_url})" if out.continue_url else ""))
        continue
    print("  응답 스키마 검증: 통과 (요청 전 schema·참조 확보, 검증 중 조회 없음)")
    cards, skipped = mapping.cards_from(out, merchant, m["name"])
    print(f"  상품 {len(out.response['products'])}개 → 원화 카드 {len(cards)}개, 뺀 것 {len(skipped)}개")
    # 원본 상품 (통화 그대로) — 원화가 아니어서 카드에서 빠진 상품도 확인용으로 보여 준다
    for prod in out.response["products"][:5]:
        vs = prod.get("variants") or []
        prices = sorted({(v.get("price") or {}).get("amount") for v in vs if isinstance((v.get("price") or {}).get("amount"), int)})
        cur = next(((v.get("price") or {}).get("currency") for v in vs if v.get("price")), "")
        digits = mapping.MINOR_DIGITS.get(cur, 0)
        shown = [f"{a / 10 ** digits:,.{digits}f}" for a in prices[:3]]
        print(f"   · {prod.get('title', '')[:50]} | 옵션 {len(vs)}개 | {cur} {' / '.join(shown)}{' …' if len(prices) > 3 else ''} | {prod.get('url') or ''}")
    for c in cards[:5]:
        print(f"   - {c['title'][:40]} | {c['price']:,}원 | {c['unit_price_text'] or '단위 가격 없음'}(판매자 표시·비교 미사용) | {c['url']}")
    for s in skipped[:5]:
        print(f"   x {s['title'][:40]} — {s['reason']}")
