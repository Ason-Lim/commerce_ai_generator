# Brix 기준표 엔진 연결 — 검토 자료 (2026-11-05)

대상: 2026-11-04~05에 작업한 품종별 Brix 기준표의 세 엔진 연결 (커밋 전, 작업 폴더 상태).
이번 패키지는 **읽기 전용 검증**입니다. 앞서 지적된 1~3번(당도·신뢰도 분리, 경고 분리, fallback·하한 공백 표시)은 **코드에 반영하지 않았고**, 7장에 수정 설계안으로만 적었습니다.

## 1. 판정 요약

| 항목 | 결과 |
|---|---|
| 변경 범위 | 엔진 3개 수정 + 새 파일 2개 (기준표 모듈, 테스트). 커밋 없음 |
| 변경 전 재현 | HEAD 기준 세 파일 복원 사본. 해시가 봉인 문서와 일치 (fruit_engine abc9f00, score_engine da565ba, identity_engine 56ca156) |
| 전체 테스트 | 변경 전 5,351개 중 실패 7 / 변경 후 5,387개 중 실패 7. **실패 ID 7개 동일**, 새 실패 없음 |
| 실제 상품 영향 (쿠팡 130개) | 품질 Brix 가점 52개 변화, 39개 검색어×모드 중 17개 순서 변화, 1위 변화 6개 |
| 새로 드러난 문제 | ① '최대N brix' 상한 주장을 실측처럼 판정 ② 냉동·병조림 등 가공품에 생과 기준 적용 ③ 품종 키워드 2개 이상이면 긴 키워드가 이김(꿀사과 홍로 → 후지) ④ Brix 신뢰도가 당도 구간에 따라 움직임(감귤 11Brix: 45→87) |

## 2. 변경 파일

| 파일 | 상태 | 내용 |
|---|---|---|
| `app/services/food_intelligence/brix_standards.py` | 새 파일 | 64행 기준표, 출처 53건, `find_standard`·`classify_brix`·`item_brix_tier` |
| `app/services/food_intelligence/engines/fruit_engine.py` | 수정 | `judge_brix` 추가, `score_brix`가 위임. 결과에 `fruit_brix_tier`·`fruit_brix_standard` 추가, 사유 문장 1줄 추가 |
| `app/services/recommendation/score_engine.py` | 수정 | `calculate_brix_quality_points`로 Brix 부분 분리 |
| `app/services/recommendation/identity_engine.py` | 수정 | `_brix_confidence_tier_points`로 당도 구간 부분 분리. 나머지 가산(+25·+10·+10)과 경고 조건은 그대로 |
| `tests/services/food_intelligence/test_brix_standards.py` | 새 파일 | 36개 |

해시: `diffs/file_hashes.txt`. 전후 소스: `sources_before/`(HEAD), `sources_after/`(작업 폴더). diff: `diffs/`.

## 3. 테스트 결과

실행 환경: 맥에 연결된 Linux 셸, Python 3.10, requirements.txt 설치본(맥 .venv는 이 셸에서 실행 불가). 180초 제한 때문에 4묶음(food / recommendation / cross_border+chat / 나머지)으로 나눠 같은 명령을 두 트리에 실행 (`test_logs/run_chunk.sh`).

| | 테스트 | 통과 | 실패 | 건너뜀 |
|---|---|---|---|---|
| 변경 전 | 5,351 | 5,339 | 7 | 5 |
| 변경 후 | 5,387 | 5,375 | 7 | 5 |

실패 7개 (변경 전후 ID·첫 줄 메시지 동일, `test_logs/failures_compare.json`, 전체 traceback은 각 묶음 `.log`와 `_junit.xml`):

| 테스트 | 원인 (메시지 기준) |
|---|---|
| `tests/services/chat/test_recipe_discover.py::test_the_trace_reaches_the_api_only_in_dev_mode` | `KeyError: 'trace'` — 개발 추적 설정 관련 |
| `tests/services/cross_border/test_tracx_smartship_observed_route_event_history_projector.py::test_at_48_pending_scope_is_exactly_two_files` | `git status --porcelain`가 파일 2개만이어야 함. 이미 미커밋 항목 160여 개로 실패 중. **이번 변경으로 목록에 5개 추가**(수정 3, 새 파일 2) — 메시지 끝의 개수만 다름 (`git_status_base_vs_after.diff`) |
| `tests/services/food/knowledge/seafood/test_seafood_registry_integration.py::test_legacy_provider_relative_order_is_preserved` | 지식 제공자 순서 불일치 |
| `tests/services/food/knowledge/seafood/test_seafood_registry_integration.py::test_seafood_provider_is_appended_after_legacy_providers` | 위와 같음 |
| `tests/services/recommendation/test_f2a_legacy_surface_removal_boundary.py::test_f2a_has_no_external_textual_module_references` | 제거 후보 모듈 참조: `compare_snapshot_engine.py`, `test_apple_explanation_claim_copy.py` (변경 전후 전체 메시지 동일) |
| `tests/test_persistence_i5b_collector_per_item_boundary_characterization.py::test_ddl_ensure_function_is_explicitly_separate_from_i5b_transaction_characterization` | `function not found: ensure_collector_v2_columns` |
| `tests/test_persistence_i5b_collector_per_item_boundary_characterization.py::test_ddl_boundary_is_not_used_as_evidence_for_per_item_update_atomicity` | 위와 같음 |

## 4. 기준표 모듈 점검 (`verification/`)

- 64행, `fruit` 값 기준 **18개 품목** (만감류·수박·참외·체리·망고·무화과 등을 따로 셈). 이전 보고의 "16개 품목"은 잘못된 숫자.
- 근거 유형: research 39 · official 9 · estimate 9 · channel 7. 출처 없는 행 4개(시나노스위트, 천도, 장희, 킹스베리 — 모두 estimate).
- **출하 하한(floor) 없는 행 50/64.** 이 행들은 지금 `high` 미만이면 모두 '보통'으로 판정 — '하한 미만'을 구분하지 못함 (7장 3번).
- 같은 키워드를 쓰는 행 없음. 각 키워드 단독 입력은 모두 자기 행으로 판정.
- 품종 키워드가 같은 과일의 품목 키워드를 포함하는 겹침 29건 — 품종 우선 규칙으로 의도대로 처리.
- 오판 위험(실제 판정 결과):
  - `꿀사과 홍로 5kg` → 후지(부사) — 키워드 길이 우선 규칙 때문 (꿀사과 3자 > 홍로 2자)
  - `골든볼 황금사과` → 시나노골드 — '황금사과' 별칭이 품종을 특정하지 못함
  - `…황금향 레드향 한라봉 천혜향` → 한라봉 — 복수 품종 상품
  - `냉동딸기`·`딸기잼`·`사과즙`·`복숭아 병조림` → 생과 기준 적용
- 문서 표와 모듈 대조: 문서 표는 모듈 값으로 작성했고 작성 직후 64행을 수동 대조. 기계 대조용으로 `brix_table_dump.csv`(모듈 전체 행) 첨부.

## 5. 호출 경로 (정적 확인)

| 엔진 | 호출 경로 | 순위 영향 |
|---|---|---|
| `fruit_engine.calculate_fruit_quality` | `food_intelligence_engine.enrich_item_with_food_intelligence` → `RecommendationProvider`(food_enricher) → `fruit_quality_score` → canonical Q 축 | `/recommendations/v2`, `/nl` canonical, 대화 API·MCP(엔진 상위 10개 선택)까지 |
| `score_engine.calculate_ai_scores` | Streamlit(`streamlit_app.py` 5곳), `product_card_renderer`, `reason_engine.build_reason_list` | Streamlit 화면 점수·정렬, 추천 사유 문구 |
| `identity_engine.calculate_brix_confidence_score` | `validate_product_identity` → `enrich_item_identity` → `_brix_confidence` | Streamlit 품질 모드 정렬 2순위, 혼합 정렬의 `min(price_confidence, brix_confidence)`, `score_engine.calculate_mode_score`의 `brix_confidence × 0.20`, 카드 문구 "Brix 입력 신뢰 점수 N점" |

이번 측정(6장)은 canonical 순위와 세 점수만 다뤘고, **Streamlit 정렬과 `calculate_mode_score`는 측정하지 않았음.**

## 6. 실제 상품 영향 (`impact/`)

입력: 쿠팡 파트너스 검색 13개 검색어 × 10개 = 130개 (2026-11-05 수집, `coupang_samples_20261105.json`). 같은 입력을 두 트리에서 `impact_probe.py`로 실행 — 수집기만 고정 목록으로 바꾼 `RecommendationProvider`로 MIX·QUALITY·PRICE 순위 산출.

- 상품명에 Brix 숫자: 16/130. 숫자 없이 고당도·당도 문구만: 42/130 (가점 14 → 6). 기준표 없음: 3/130.
- 값이 바뀐 상품: `fruit_brix_score` 52, `fruit_quality_score` 52, `ai_quality` 9, `brix_confidence` 6. `identity_score`·경고 변화 0.
- 순위: 39개 중 순서 변화 17, 1위 변화 6, 상위 3 변화 14 (`impact_rankings.csv`). 1위가 바뀐 예: 샤인머스캣 QUALITY(19brix → '최대21브릭스'), 수박 MIX('고당도' 문구 → '최대16brix'), 배 QUALITY('초초고당도' 문구 → '당도선별 알뜰배').
- **'최대N brix' 9건이 모두 해당 숫자로 판정** — 8건 최상(최대21브릭스 샤인머스캣, 최대20brix 복숭아 등). 상한 주장이 대표값처럼 쓰임.
- **가공품 의심 10건**(냉동딸기, 병조림, 스테비아 토마토)에 생과 기준 적용.
- **신뢰도가 당도 구간을 따라 움직임**: 같은 근거(상품명 숫자·중량·URL)인데 감귤 11Brix 45→87, 12brix 35→77, 샤인머스캣 19brix 100→87, 단감 최대15brix 90→65.

## 7. 지적 1~3에 대한 수정 설계안 (미적용)

### 7-1. 당도 수준과 근거 신뢰도 분리
- `brix_level_score` — 품종별 구간 점수만 (지금의 당도 부분). 용도: 당도 수준 비교.
- `brix_evidence_score` — 당도와 무관한 근거만: 상품명·설명에 숫자 표기(값 일치는 `claim_source.brix_claim_source`), 측정 방법 문구(광센서·비파괴·당도선별), 중량 표기, 실제 상품 URL. 같은 근거면 품종·Brix와 상관없이 같은 점수.
- `brix_confidence` — 지금 값(당도+근거 합산)을 **이름은 유지하되 레거시 합산값으로 명시**, 기존 정렬 호환용으로만 남김. 카드 문구 "Brix 입력 신뢰 점수"는 `brix_evidence_score`로 바꾸고 "판매자 표기 근거" 라벨 사용. 어느 점수도 "검증된 당도" 설명에 쓰지 않음.
- 같이 고칠 것: 상품명 숫자 정규식 `\d{2}…brix`는 한 자리(토마토 7~9) 표기를 놓침 → `\d{1,2}`, `브릭스`·`bx` 포함.

### 7-2. 경고 분리
- 근거 경고: "Brix 주장이 있는데(숫자 또는 고당도 문구) `brix_evidence_score`가 기준 미만" → `Brix 근거 부족`. 당도 크기와 무관하므로 수박 11·토마토 8도 포착.
- 당도 안내: 품종 구간 결과는 `warnings`(식별 점수 감점)에 넣지 않고 별도 `brix_notice`로만 전달.
- 결정 필요: 근거 경고의 감점 크기(현재 -10 유지 여부)와 기준값.

### 7-3. fallback과 하한 공백 명시
- 판정 결과에 `brix_rule` 필드: `variety_standard:<품종>` / `fruit_common:<품목>` / `legacy_fixed:no_standard`(기준표 없음, 이전 16·15·14·13 구간) / `no_value_text_only` / `no_value`. 세 엔진이 같은 값을 결과에 남김.
- 지금 `fruit_brix_tier=None`이 '기준표 없음'과 '숫자·문구 모두 없음'을 함께 뜻함 → 위 필드로 구분.
- floor 없는 50행: `high` 미만을 '보통'으로 묶지 않고 `below_high_floor_unknown`으로 따로 판정. **점수는 정책 결정 필요** — (A) 보통과 같은 점수 + 표시, (B) 판정 보류 후 이전 구간. 어느 쪽이든 0으로 메우지 않음.
- 테스트: 중량을 뺀 당도 구간 단위 테스트는 유지하고, 중량·URL이 있는 사례를 따로 두어 +10·+10 가산을 확인.

### 7-4. 이번 검증에서 추가로 나온 것 (결정 필요)
- '최대N brix'·'최고N brix': 상한 주장으로 보고 한 구간 낮추거나 '문구만'과 같게 취급할지.
- 가공품(냉동·잼·즙·병조림·말린): 기준표 적용 제외 목록.
- 복수 품종 키워드: 키워드 길이 대신 '품종이 둘 이상이면 품목 공통 기준' 등 규칙.

## 8. 남은 확인

- Streamlit 정렬과 `calculate_mode_score`(×0.20)의 변경 전후 차이 — 미측정.
- 맥 .venv(Python 3.14)에서 같은 테스트 결과인지 — 미확인.
- 변경 권한: `score_engine.py`·`identity_engine.py`가 담당 범위 밖이면 승인 대조 필요.
- 만감류 11.5·황금향 10의 현행 시행 여부 — 조례 원문 미확인.
