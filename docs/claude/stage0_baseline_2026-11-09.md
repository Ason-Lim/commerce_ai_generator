# 0단계 기준선 확인 (2026-11-09, 읽기 전용)

## 1. 저장소 상태
- 브랜치 `main`, HEAD `658c661 Initial commit` (2026-10-19, 35파일 거버넌스 기록), 총 902커밋, 원격 `Ason-Lim/commerce_ai_generator`
- **미커밋 변경 177건**: 수정 13파일(+270/−50, 추천 score/identity/reason 엔진·main.py·coupang_api 등), 미추적 1,622파일
- 10-19 이후 3주간 개발분(관리자 화면, /api/chat, UCP, trends, affiliate, partners, cross_border 등)이 전부 커밋되지 않은 상태

## 2. 커밋 전 위험 (중요)
- 미추적 파일 중 **실제 API 키가 든 파일 8개 + .env가 들어 있는 tgz**: `.env.backup_*` 2개, `b2b_install_backups/*/env.before` 2개, `recipe_chat_api_backups/**/.env.*` 4개, `transfer_20261029_1515/commerce.tgz`
- `.gitignore`는 `.env`만 막고 `.env.*`·`*_backups/`·`*.tgz`는 막지 않음 → `git add -A` 시 GitHub로 키 유출
- 대용량: `recipe_chat_api_backups` 106MB(단일 tgz 82MB, GitHub 100MB 한도 근접), `var/recipes/recipes.json` 10MB, `ocr_results` 8MB

## 3. PM-1/PM-2 경로 대조
| 항목 | 전달된 기록 | 실제 저장소 | 판정 |
|---|---|---|---|
| PM-1 정식 경로 | app/services/comparison/compare_identity_engine.py | 존재(112줄), 761a83b 이후 미변경 | 일치 |
| PM-2 정식 경로 | app/services/comparison/compare_snapshot_engine.py | 존재(254줄), 761a83b 이후 미변경 | 일치 |
| 호환 전달자 | recommendation/ 아래 전달자 | compare_identity_engine.py(11줄)·compare_snapshot_engine.py(9줄) 존재. 앱 코드는 모두 정식 경로 사용, 전달자 사용처는 테스트 1곳(test_comparison.py) | 일치 |
| PM-2 의존 | price_signal_engine·score_engine은 추천 소유 | snapshot 엔진이 recommendation.score_engine·price_signal_engine import | 일치 |
| **차이** | — | **score_engine.py가 F2-A1 레거시 제거 후보 목록에 포함** → PM-2 정식 경로가 제거 후보에 의존 (test_f2a 실패 원인) | **경계 충돌, 00_1 결정 필요** |
| score_engine 변경 | — | 미커밋 수정 +45/−? (identity_engine·reason_engine·platform_score_engine도 수정) | 1단계 전 커밋·검토 필요 |

## 4. 추천 진입점·배포 경로
- 추천: `GET /recommendations/nl`(run_recommendation_pipeline), `/recommendations/v2`, `/recommendations/revisit`, `POST /generate`, `/track-click`
- 대화: `POST /api/chat`, `/go/...` 리다이렉트, `POST /api/click`, `/api/trends/surge`
- 관리자: `/admin/*` (trends, connect, conversations, clicks, b2b/*)
- 배포: `run_prod.sh`(frontend 빌드 → uvicorn :8001 단일 서버), `run_api.sh`, `stop_api.sh`

## 5. 테스트 기준선
- 실행 환경: Linux Python 3.10 임시 venv (Mac .venv는 Python 3.14 — Mac에서 재확인 권장), 캐시 미생성
- **5,487건: 5,474 통과 / 8 실패 / 5 건너뜀**

| 실패 | 원인 | 분류 |
|---|---|---|
| test_persistence_i5b_...(2) | `ensure_collector_v2_columns` 함수 없음 — i7b2 DDL 분리 이후 특성화 테스트 미갱신 | 테스트 노후 |
| test_f2a_has_no_external_textual_module_references | PM-2 snapshot 엔진·apple 테스트가 제거 후보(score_engine 등) 참조 | **경계 충돌** |
| test_seafood_registry_integration(2) | 레지스트리에 sauce·duck 등 공급자 추가, 순서 기대값 노후 | 미커밋 변경과 테스트 불일치 |
| test_recipe_discover trace | 저장소 .env의 CHAT_DEV_TRACE가 환경변수보다 우선 | 환경 의존 |
| test_reselect_golden budget_5man | 광고 고지 문구(수수료 → 무료 운영 문구) 변경, 골든 파일 미갱신 | 의도된 정책 변경, 골든 갱신 필요 |
| test_at_48_pending_scope | `git status`가 2파일이어야 통과 — 작업 트리 상태에 의존 | 테스트 설계 문제 |

→ **실제 기능 회귀로 보이는 실패는 없음.** 다만 PM-2 ↔ F2-A1 경계 충돌은 1단계(추천 근거 표시) 범위와 직결.

## 6. 1단계로 넘어가기 전 필요한 것
1. .gitignore 보강(.env.*, env.before, *_backups/, *.tgz, ocr_results/, Claude outputs/) 후 기준선 커밋 + 원격 푸시 또는 git bundle 백업
2. 00_1 결정: score_engine을 F2-A1 제거 후보에서 뺄지(PM-2 의존 유지) — 1단계 화면이 score_engine 출력을 그대로 쓰므로 선결
3. 노후 테스트 4종 갱신, at_48·trace 테스트의 환경 의존 제거
