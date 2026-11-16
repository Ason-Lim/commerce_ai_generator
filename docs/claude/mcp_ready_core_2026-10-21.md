# 프로토콜 중립 커머스 코어 + MCP 서버

작성일 2026-10-21 · 대상 `integrated_system` · 이전 문서: commerce_platform 통합 아키텍처(10-16), 소비자 UI/UX 설계(10-20)

## 1. 한 줄 요약

**코어는 어떤 프로토콜도 모른다. 웹·MCP·UCP·ACP 는 코어 앞뒤에 붙는 어댑터다.**

```
           앞단(누가 우리를 부르나)                       뒷단(우리가 누구를 부르나)
  ┌──────────────────────────┐                     ┌────────────────────────────────┐
  │ consumer 웹  POST /api/chat │──┐              ┌──│ CatalogSource                    │
  │ MCP 서버  (Claude·ChatGPT) │──┼─▶ 코어 서비스 ─┼──│  예시몰 · 쿠팡 · 네이버          │
  │ (나중) UCP/ACP 판매사 역할  │──┘   recommend   │  │  (나중) UCP catalog · ACP feed   │
  └──────────────────────────┘       handoff     │  ├────────────────────────────────┤
                                    ▲            └──│ CheckoutGateway (지금은 없음)    │
                              domain/models         │  (나중) UCP · ACP checkout       │
                              Money·Measure·Offer   └────────────────────────────────┘
```

규칙 하나: **`shared/domain` 과 `shared/services` 는 `mcp`, UCP, ACP 를 import 하지 않는다.**
그래야 프로토콜이 바뀌거나 늘어도 추천 규칙(실구매가·미확인·유료 분리)은 한 곳에만 있다.

## 2. 파일

```
shared/domain/models.py        Money(정수 원) · Measure(정수 step+단위) · Evidence · Merchant · Offer · SearchQuery
shared/domain/ports.py         CatalogSource · CheckoutGateway · CheckoutQuote · ClickLog
shared/services/recommend.py   검색 → 정렬(실구매가 확정 우선) → 추천/참고/유료 분리 → 비교
shared/services/handoff.py     /go/{token} 이동. 직전 결과 + 판매처 도메인만 허용
shared/adapters/sample_catalog.py   예시몰
shared/adapters/protocol_stubs.py   UCP 자리 + authority binding 검사 (등록 안 함)
mcp_server/server.py           코어를 MCP 도구 4개 + 정책 리소스 1개로 노출
tests/test_core_and_mcp.py     10개 테스트 (도메인·서비스·MCP 왕복)
```

## 3. 이 모델이 지키는 것

| 원칙 | 코드 |
|---|---|
| 실구매가 우선, 배송비 모르면 0원 아님 | `Offer.total()` 은 배송비 None 이면 None. 정렬에서 확정된 것 먼저 |
| 금액에 float 금지 | `Money.amount` 정수 강제. UCP·ACP 최소 단위 정수와 그대로 호환 |
| 중량·100g당 | `Measure(value, unit, scale)` — UCP 수량 표현과 같은 방식(Rec20 코드) |
| 근거와 미확인 구분 | `Evidence.status` verified/unverified/missing, `Offer.unknowns()` |
| 유료 소개 분리 | `is_sponsored` → `SearchResult.sponsored`, 순위에 안 들어감 |
| 안전한 이동 | `HandoffService` — https + 판매처 도메인 + 발급한 토큰만. UCP `continue_url` 에도 같은 검사 |
| 한 마켓 장애 격리 | 소스별 예외를 `source_errors` 로 모으고 나머지 결과는 반환 |
| 외부 공개 형태 고정 | `Offer.to_public()` 한 곳. 원가·마진 같은 내부 값이 새지 않음 |

## 4. MCP 서버

| 도구 | 성격 | 하는 일 |
|---|---|---|
| `search_products(query, budget_max_krw?, servings?, limit?)` | 읽기 전용 | ranked / reference / sponsored 로 나눠 반환 |
| `compare_offers(offer_ids)` | 읽기 전용 | 2~3개를 실구매가·100g당·개당으로 비교, 가장 유리한 값 표시 |
| `get_offer(offer_id)` | 읽기 전용 | 근거·미확인 포함 상세 |
| `create_purchase_link(offer_id)` | 링크 발급만 | 우리 `/go/{token}` URL. 결제 없음 |
| 리소스 `commerce://policy` | | AI 가 결과를 보여줄 때 지킬 표시 원칙 |

결제·주문·회원 정보 도구는 **의도적으로 없다.** 링크 발급 외에는 모두 `read_only_hint=True`.

### 실행

```bash
pip install "mcp>=1.2"          # 1.x(FastMCP)와 2.x(MCPServer) 모두 지원
python -m pytest -q             # 10 passed
python -m mcp_server.server     # stdio
MCP_TRANSPORT=http PUBLIC_BASE_URL=https://<도메인> python -m mcp_server.server   # 원격
```

Claude Desktop 로컬 연결 (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "commerce-recommender": {
      "command": "/Users/<사용자>/<경로>/integrated_system/.venv/bin/python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/Users/<사용자>/<경로>/integrated_system"
    }
  }
}
```

## 5. integrated_system 에 넣는 방법 (기존 코드 기준)

| 기존 | 할 일 |
|---|---|
| `shared/markets/*` 의 Offer | `shared/domain/models.Offer` 로 통일. 쿠팡·네이버 어댑터가 `CatalogSource` 를 구현하도록 `search()` 시그니처만 맞춤 |
| `shared/engines/recommender.py` | 정렬·필터를 `services/recommend.py` 로 옮기거나, commerce_ai 랭커를 `RecommendationService` 안에서 호출 |
| `consumer/app.py` `/go/{sid}/{rank}` | `HandoffService.resolve()` 호출로 교체. 기존 경로는 유지 |
| `consumer/presenter.py` | `Offer.to_public()` 결과로 블록 생성 → 웹과 MCP 의 숫자가 항상 같음 |
| b2b | 변경 없음. MCP 서버는 consumer 코어만 노출 (b2b 는 사내망 유지) |

## 6. 단계별 로드맵

| 단계 | 조건 | 할 일 | 코어 변경 |
|---|---|---|---|
| **0. 지금** | — | 코어 정리, 실 마켓 어댑터를 `CatalogSource` 로 | 이 패키지 |
| **1. MCP 로컬** | 실 마켓 키 연결 후 | Claude Desktop 에 stdio 로 붙여 직접 써 보기 (내부 검증용) | 없음 |
| **2. MCP 원격 공개** | 추천 품질 확인 후 | Streamable HTTP + HTTPS 배포, 요청 제한, 클릭 로그로 MCP 경유 매출 측정 | 없음 |
| **3. UCP/ACP 구매자 쪽** | UCP·ACP 판매사가 추천 대상에 생길 때 | `protocol_stubs.py` 를 채워 `UcpCatalog`·`UcpCheckout` 등록, `Merchant.channels` 에 UCP 추가 | 없음 |
| **4. 판매자 쪽** | 직접 판매 시작 시 (B2B 선물 공급 등) | 별도 `merchant/` 앱: `/.well-known/ucp`, checkout-sessions, PSP | 별도 판단 |

MCP 를 먼저 하는 이유: 판매사·결제사가 준비될 필요가 없고, 우리 추천을 AI 대화창 안으로 넣는 일이라 **지금 수익 모델(판매처 이동 + 제휴 수수료)을 그대로 유지**한다.

## 7. 원격 공개(2단계) 전에 확인할 것

- 인증: 공개 읽기 도구라도 요청 제한(IP·키) 필요. 2.x 는 `token_verifier` 로 토큰 검증 가능
- `create_purchase_link` 의 session_id 를 MCP 세션별로 분리 (지금은 고정값 `"mcp"`)
- `RecommendationService._index` 를 메모리 대신 store(core 스키마)로 — 프로세스가 여러 개면 필요
- 제휴 링크 정책: 쿠팡 파트너스 등은 AI 경유 노출·고지 문구 규정을 확인 후 공개
