# check_ucp_profiles.py — 쇼핑몰이 UCP(Universal Commerce Protocol) 판매자 프로필을 공개했는지 확인. 읽기 전용. (2026-11-04)
# 각 몰의 https://<호스트>/.well-known/ucp 를 한 번씩 GET 해서 JSON 프로필이 있으면 버전·capability 를 보여 준다.
# 상품 페이지를 수집하지 않는다 (UCP 가 에이전트용으로 정한 공개 발견 주소만 본다).
# 2026-11-04 결과: 국내 몰 모두 이 주소에서 유효 프로필 미확인 (403·405·HTML 은 판단 불가), 비교용 allbirds.com(Shopify) 은 2026-08-25 프로필 있음(catalog.search·lookup 포함).
# 사용: python check_ucp_profiles.py            (호스트 추가: python check_ucp_profiles.py www.example.co.kr)
import sys

import requests

HOSTS = ["www.ssg.com", "emart.ssg.com", "www.kurly.com", "www.lotteon.com", "front.homeplus.co.kr", "www.gsshop.com",
         "www.gsfresh.com", "www.oasis.co.kr", "www.coupang.com", "www.11st.co.kr", "www.gmarket.co.kr", "allbirds.com"]
for host in sys.argv[1:] or HOSTS:
    url = f"https://{host}/.well-known/ucp"
    try:
        r = requests.get(url, timeout=10, allow_redirects=False, headers={"User-Agent": "commerce-ai-ucp-check/0.1", "Accept": "application/json"})
        try:
            ucp = (r.json() or {}).get("ucp") or {}
        except ValueError:
            ucp = {}
        caps = ucp.get("capabilities") or {}
        names = list(caps) if isinstance(caps, dict) else [c.get("name") for c in caps if isinstance(c, dict)]
        if ucp.get("version"):
            print(f"{host}: 프로필 있음 — 버전 {ucp['version']}, capability {', '.join(n for n in names if n)}")
        else:
            print(f"{host}: 이 주소에서 유효 프로필 미확인 (HTTP {r.status_code}) — 미지원 확정 아님")
    except Exception as e:  # noqa: BLE001
        print(f"{host}: 확인 실패 ({type(e).__name__})")
