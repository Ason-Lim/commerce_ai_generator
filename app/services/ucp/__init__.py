"""UCP(Universal Commerce Protocol) 구매자(플랫폼) 쪽 — 판매자 카탈로그 읽기 전용 (2026-11-04 p40).

아직 어떤 화면·MCP 경로에도 연결하지 않는다 (AST 테스트로 보장).  기본 꺼짐: UCP_CATALOG=1 과
UCP_PLATFORM_PROFILE_URL(공개 https 주소의 우리 플랫폼 프로필) 둘 다 있어야 실제 호출한다.

  discovery.py  판매자 /.well-known/ucp 프로필 읽기 · 버전·capability 협상
  client.py     catalog.search 호출 (REST · MCP 전송)
  mapping.py    UCP 상품·옵션(variant) → 기존 상품 카드 dict (옵션마다 카드 1개, 판매자 단위 가격 그대로)
  registry.py   쓸 판매자 등록부 data/ucp/merchants.csv
  platform.py   우리 플랫폼 프로필 문서 · 사용 여부

사양: https://ucp.dev/2026-08-25/specification/overview/ , catalog: https://ucp.dev/specification/shopping/catalog/
결제·장바구니·회원 연결(identity linking)은 쓰지 않는다 — 지금처럼 판매처 페이지로 이동만 한다.
판매자 쪽(우리가 판매자 프로필을 내는 일, 배송 fulfillment)은 별도 단계.
"""
