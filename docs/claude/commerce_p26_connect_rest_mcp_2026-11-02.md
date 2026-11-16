# p26 — 쇼핑커넥트 등록부 정리 · test_surge 격리 · 급상승→발급 요청 · 쇼핑 턴 공통 서비스 교체 · MCP 도구 2개 (2026-11-02)

백업: `recipe_chat_api_backups/20261102_p26_connect_registry/` (변경 전 원본). 커밋하지 않음.
검증 환경: 클라우드 컨테이너에 관련 모듈만 복사(Python 3.13). 맥 .venv 전체 테스트는 미실행.

## 1. 쇼핑커넥트 등록부 — 화면 경로는 하나
- 화면에 링크를 붙이는 곳은 `app/services/chat/service.py` 의 `connect_links()` 하나 (등록부 = `NAVER_CONNECT_REGISTRY_CSV`).
- 보강: 발급 링크 도메인(naver.me·brandconnect.naver.com)만 표시, 주류 상품 줄·실적 제외 유형(정기구독·정기배송·렌탈·쇼핑윈도·장보기) 줄 제외.
- 등록 링크가 없는 검색어 → 발급 요청 대기열 (`SC_REQUEST_QUEUE=1` 일 때만, 실패해도 대화 계속).
- `app/services/affiliate/naver_shopping_connect.py` 는 운영 도구(import 점검·match·queue·queue-trends). `attach_links()` 는 화면에 연결하지 않음(중복 방지). DB 경로는 저장소 루트 기준.

## 2. test_surge 격리
- 관리자 블로그 초안 저장 경로가 `surge.ROOT/var/blog_drafts` 고정 → 시험에서 `S.ROOT` 를 tmp_path 로 바꿈. 운영 코드 무수정.

## 3. 급상승 식품 → 발급 요청 (M5)
- `surge.run_from_env` 저장 직후 `queue_trends_from_report` (SC_REQUEST_QUEUE=1 일 때만). 대상: status surging/new, 주류 제외, 등록부에 이미 있으면 제외. reason=trend_dish.

## 4. 쇼핑 턴 → 공통 서비스
- `_shopping_turn` 이 `services/commerce/search.collect()` 를 씀 (annotate_prices=False — 시세 줄은 기존대로 `_result_blocks`). `collect` 반환에 `found` 추가.
- 예산 답변 턴·관심 상품 비교는 새 검색이 아니라 저장 후보 재선택이라 이번에 바꾸지 않음.
- 비교: 변경 전/후 같은 330개 테스트 — 실패 7개 동일(복사하지 않은 모듈 때문), 통과 314 → 314 + 신규.

## 5. MCP 도구 2개 (로컬 stdio 전용)
- `app/mcp_adapter/tools.py` (프로토콜 무관) · `server.py` (`python -m app.mcp_adapter.server`, mcp 1.x/2.x).
- `food_search_products`, `food_get_recipe` — 읽기 전용, 결과는 commerce.v1 그대로.
- 제휴 링크: `MCP_AFFILIATE_LINKS=1` 이 아니면 제휴 상품 product_url 비움 + 쇼핑커넥트 목록 제외 + 경고. 순위 불변.
- 원격(HTTP) 공개 안 함 — 요청 제한·키·제휴 정책 확인 후.

## p27 (2026-11-02 밤) — 발급 요청 알림
- 관리자 트렌드 탭 `#requests` 섹션: 남은/발급 완료/건너뜀 목록, 이유(급상승·검색 미매칭), 요청 횟수, 등록부에 링크가 생겼는지 표시, '발급 완료'·'건너뛰기'·'되돌리기' 버튼, '이 리포트에서 올리기'. 둘러보기(guest) 모드에서는 숨김.
- API: `GET /admin/api/connect/requests`, `POST /admin/api/connect/requests/{id}` {status}, `POST /admin/api/connect/queue-trends` {date}. 모두 관리자 토큰 필요.
- 블로그 초안: 응답에 `link_needs`(need/have/alcohol), 저장 파일 맨 위에 '[운영 메모 — 블로그에 붙여 넣지 마세요]' 블록. 본문(body)에는 넣지 않음.
- 백업: `recipe_chat_api_backups/20261102_p27_connect_admin/`.

## 사용자 확인 필요
- 맥에서 전체 테스트 실행 (이전 기준 11 failed).
- `.env`: `NAVER_CONNECT_REGISTRY_CSV`(절대 경로로 설정됨 — 서버 이전 시 상대 경로로), `SC_REQUEST_QUEUE=1` 설정됨.
- `pip install "mcp>=1.2"` 후 Claude Desktop 로컬 연결로 시험.
- 쿠팡 파트너스·네이버 쇼핑커넥트의 AI 에이전트 경유 링크 허용 여부 문의.
