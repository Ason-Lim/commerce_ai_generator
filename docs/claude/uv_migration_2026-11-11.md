# uv 전환 기록 (0단계 기준선 보강, 2026-11-11)

## 바뀐 것
- `pyproject.toml` 신설 — 의존성 정의, ruff·ty 설정. 버전 하한 = 2026-11-11 MacBook .venv 설치 버전
- `uv.lock` 신설 — 106개 패키지 고정. 기존 .venv 와 겹치는 95개는 버전이 모두 같음
- `requirements.txt` · `requirements-dev.txt` — uv.lock 에서 생성한 고정 버전 목록으로 교체 (uv 없는 환경용)
- `run_api.sh` — uv 가 있으면 `uv run --locked` 로 실행 (없는 패키지만 설치, 기존 패키지 삭제 안 함). uv 가 없으면 예전 방식
- `CLAUDE.md` · `.claude/settings.json` 신설 — 작업 규칙, Astral 플러그인(uv·ruff·ty 스킬, ty LSP) 활성화
- `app/services/recommendation/reason_engine.py` — `calculate_hidden_gem_score` import 누락 수정 (discovery 유형 근거 생성 시 NameError, 레거시 경로)

## requirements.txt 에 빠져 있던 패키지
| 패키지 | 쓰는 곳 | 처리 |
|---|---|---|
| mcp 2.3.0 | app/mcp_adapter/server.py | 기본 의존성에 추가 |
| xlrd 2.0.1 | app/services/nts_excel.py (.xls) | 기본 의존성에 추가 |
| pypdf | app/admin/b2b/gift_monitor/collectors.py (공고문 PDF) | 기본 의존성에 추가 — 기존 .venv 에도 없었음 |
| anthropic | app/admin/shared/llm.py (LLM_PROVIDER=anthropic 일 때만) | 선택 그룹 llm-anthropic |
| selenium·bs4·webdriver-manager·lxml | scripts/ 스크래핑 (보관, 미사용) | 선택 그룹 legacy-scrapers |

## 테스트 비교 (Python 3.14, Linux)
- 전환 전 (.venv 와 같은 버전): 5544 통과 · 5 건너뜀 · 7 실패
- 전환 후 (uv.lock): 5544 통과 · 5 건너뜀 · 7 실패 — 실패 목록 동일
- 전환 전부터 실패하던 7건:
  - tests/services/chat/test_recipe_discover.py::test_the_trace_reaches_the_api_only_in_dev_mode
  - tests/services/chat/test_reselect_golden.py::test_reselect_turns_match_golden
  - tests/services/cross_border/test_tracx_smartship_observed_route_event_history_projector.py::test_at_48_pending_scope_is_exactly_two_files
  - tests/services/food/knowledge/seafood/test_seafood_registry_integration.py::test_legacy_provider_relative_order_is_preserved
  - tests/services/food/knowledge/seafood/test_seafood_registry_integration.py::test_seafood_provider_is_appended_after_legacy_providers
  - tests/test_persistence_i5b_collector_per_item_boundary_characterization.py::test_ddl_boundary_is_not_used_as_evidence_for_per_item_update_atomicity
  - tests/test_persistence_i5b_collector_per_item_boundary_characterization.py::test_ddl_ensure_function_is_explicitly_separate_from_i5b_transaction_characterization

## ruff 기준선
- 설정 적용 후 105건 (설정 전 659건). 저장소 전체 포맷은 하지 않음 (501개 파일 대상)
- 남겨 둔 확인 필요 항목 (동작에 영향 가능, 결정 필요):
  - app/main.py — `estimate_weight_grams` 가 두 번 정의됨. 앞(126행)은 여러 중량 중 **최솟값**, 뒤(204행)는 **마지막 값**을 쓰며 실제로는 뒤쪽이 사용됨. `calculate_price_per_100g` 도 중복(166·246행)
  - app/ui/streamlit_app.py:3816 — `build_platform_search_url` 재정의가 정의되지 않은 `normalize_search_keyword`·`SEARCH_URL_BUILDERS` 를 사용 (레거시 화면)
- ty: 393건 진단 — 참고용

## Mac 에서 할 일
1. `brew install uv` (없으면)
2. `uv sync` — 기존 .venv 를 uv.lock 에 맞춤 (lock 에 없는 tiktoken·regex·pip 등은 제거됨. 남기려면 `uv sync --inexact`)
3. 보관 스크립트를 돌릴 때만 `uv sync --inexact --group legacy-scrapers`
4. Mac mini: 저장소 clone → `uv sync --no-dev` → `uv run playwright install chromium`

## 추가 수정 (2026-11-11 10:30)
- Mac 에 Python 3.15 도 설치돼 있어 uv 가 3.15 를 골랐고, pyarrow(streamlit 의존) 가 3.15용 빌드 파일이 없어 설치 실패 → `.python-version` = 3.14, `requires-python = ">=3.14,<3.15"` 로 고정
- 이 과정에서 기존 .venv 는 uv 가 지우고 새로 만들었음 (패키지는 uv.lock 으로 그대로 복원됨)

## 실패 7건 정리 (2026-11-11 11시) → 5549 통과 · 5 건너뜀 · 0 실패
| 테스트 | 원인 | 처리 |
|---|---|---|
| recipe_discover trace | dev_trace_on()이 .env 의 CHAT_DEV_TRACE=0 을 환경변수보다 우선 → 테스트의 setenv 무시 | 테스트에서 dev_trace_on 을 직접 지정 |
| reselect_golden | 상품에 `partner` 필드, "상품 5개 한눈에 비교하기"(compare_cta) 블록이 추가된 뒤 골든 미갱신. 순서·가격·문구 변화 없음 확인 | 골든 파일 재생성 |
| tracx at_48 | 커밋 전 git status 에 새 파일 2개만 있는지 보던 일회성 검사 | 삭제 |
| seafood 순서 2건 | 이후 등록된 sauce·compound_seasoning 미반영 | 기대 순서 갱신 |
| i5b DDL 2건 | ensure_collector_v2_columns 는 8ae055c 에서 수집기 밖으로 분리됨 | "분리 유지" 확인 테스트 1개로 교체 |
