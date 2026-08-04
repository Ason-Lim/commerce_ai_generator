# IRG-MA-2026-013-WINE

## Cross-domain Regression Verification Report

| Item | Value |
|---|---|
| Project | Commerce AI Generator |
| Domain | 12_Wine |
| Authority | 99_Integration Verification Authority |
| Status | BLOCKED |
| Result | NOT COMPLETED |
| Date | 2026-08-04 |

## Available Evidence

```text
Wine tests: 141 passed
Wine tests after alias expansion: 144 passed
Registry/provider/resolver selected tests: 402 passed, 590 deselected
Wine-focused registry/provider/resolver tests: 81 passed, 914 deselected
Compilation: compile_exit_code=0
```

Provider IDs were unique and Wine was registered once.

## Routing Matrix

| Product | Expected | Observed | Result |
|---|---|---|---|
| 에티오피아 아라비카 원두 | coffee | coffee | PASS |
| 프랑스 브리 치즈 | cheese | cheese | PASS |
| 국내산 한우 1++ 등심 | beef | beef | PASS |
| 프리미엄 도퍼 어린양 프렌치랙 | lamb | lamb | PASS |
| 보어 어린 염소 갈비 | goat | beef | FAIL |
| 토종닭 가슴살 | chicken | chicken | PASS |
| 훈제오리 슬라이스 | duck | duck | PASS |
| 사슴 안심 스테이크 | venison | beef | FAIL |
| 고당도 사과 | fruit | fruit | PASS |

## Decision

```text
CROSS-DOMAIN REGRESSION VERIFICATION NOT COMPLETED
```

Closure requires resolution of `RC-RUNTIME-001`, a passing routing matrix, full regression, compilation, and change-scope review.

**Issued by:** 99_Integration Verification Authority
