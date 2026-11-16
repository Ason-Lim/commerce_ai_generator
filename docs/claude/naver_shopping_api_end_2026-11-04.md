# 네이버 쇼핑 검색 API 종료와 다른 쇼핑몰 연결 (2026-11-04)

질문: '감귤' 입력 시 SSG·컬리·롯데마트·홈플러스·GS fresh 등 여러 쇼핑몰 상품을 함께 추천할 수 있나 (현재 쿠팡만). 관련: affiliate_policy_responses_2026-11.md
## 네이버 쇼핑 검색 API — 종료 확인 (2026-11-04 21:4x)
- 직접 확인: 같은 키(.env NAVER_CLIENT_ID)로 `/v1/search/shop.json` → HTTP 404 `SE05` "Invalid search api (존재하지 않는 검색 api 입니다.)". 같은 키로 `news.json`·`blog.json` 은 200 정상 → 키 문제가 아니라 API 자체가 없음.
- 2차 자료: 네이버 개발자센터 공지 「검색 '쇼핑/책/전문자료' API 서비스 종료 안내」 https://developers.naver.com/notice/article/32564 — 적용 2026-07-31 (공지 원문은 이 환경에서 열리지 않아 아래 2차 자료로 확인). NAVER API HUB 이관 대상(뉴스·블로그 등 10종, 검색어 트렌드, 쇼핑인사이트)에 쇼핑 검색은 없음, 대체 API 없음.
  - https://github.com/NomaDamas/k-skill/issues/786 (2026-11-03 같은 SE05 재현)
  - https://waffleboard.io/blog/naver-search-api-hub-migration-guide
- 영향
  - 몰별 검색(SSG·오아시스는 registry 에 '네이버 쇼핑 결과 판매처 필터'로 정의)은 쓸 수 없음. 컬리·롯데마트는 원래 수집 방법 없음.
  - 레거시 수집기 collect_naver_products 는 7/31 이후 실패 → DB(online_food_price_snapshot)의 네이버 행은 종료 전 자료. 대화 DB 대체 경로(db_product_collector.fetch_products_from_db)는 수집 시각 제한 없이 이 행을 섞을 수 있음 → 오래된 가격 노출 가능성 (맥에서 check_naver_malls.py 로 수집 시각 확인 필요).
  - 쇼핑인사이트(클릭 추이)·검색어 트렌드는 살아 있으나 상품·가격·링크는 주지 않음 — 트렌드용.
  - 고객 편의용 네이버쇼핑 검색 링크(p29)는 API 와 무관하게 동작.
- 남은 길 (스크래핑 제외 원칙 유지): ① 각 몰 공식 제휴·상품 데이터 제공 문의(SSG·컬리·롯데ON·홈플러스·GS fresh) ② 제휴 마케팅 네트워크의 상품 피드 제공 여부 조사(미확인) ③ 기존 업체 상품 피드(partners/feed) 확대.
- 확인 스크립트: `check_naver_malls.py` (읽기 전용 — API 1회 확인, DB 원천별 수집 시각, 예전 네이버 행의 판매처 분포 → Claude outputs/naver_malls_20261104.csv).
