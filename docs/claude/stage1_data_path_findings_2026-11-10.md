# 1단계 시작 전 데이터 경로 점검 (2026-11-10)

기준: main `1926036`. 근거: `docs/claude/stage1_view_identity_price_check_2026-11-10.md`, `docs/claude/stage1_view_chain_2026-11-10.md`, `sql/reference/*.current.sql`(19개 뷰 정의 덤프, Mac DB 읽기 전용). 실행 환경: Mac DB 조회 + 저장소 코드 읽기.

## 추천 경로
- `/api/chat`(React) 쇼핑 턴 → `main.natural_language_recommendations` → **먼저 canonical pipeline**(`run_recommendation_pipeline`), 실패 시 **DB fallback**(`vw_ai_recommendation_final` SQL, `main.py` 474~)
- DB fallback은 `score_engine`을 쓰지 않음. 순위 = 뷰의 `final_recommendation_score`(+mode·product·개인화 boost)
- canonical pipeline의 데이터 출처는 이번 점검에서 미추적 → 다음 확인

## 발견
| # | 항목 | 내용 | 영향 |
|---|---|---|---|
| F1 | 상품 id | `product_id`가 `vw_ai_adaptive_recommendation`까지 있고 `vw_ai_adaptive_recommendation_v3`에서 빠짐. 최종 뷰 51컬럼에 id 없음 | `product_url`이 사실상 키(294건 중 중복 1건: G마켓 털보네사과 9kg 2행) |
| F2 | 가격 결합 | `main.py` LATERAL이 URL **또는 상품명**으로 `online_food_price_snapshot`을 붙임. 판매처 조건 안에 `OR s.product_name = r.product_name`이 있어 판매처 조건이 사실상 무효 | 12건(4%)이 다른 판매처 스냅샷과 결합 (예: 롯데ON 상품에 G마켓 가격) |
| F3 | 가격 테이블 2개 | 뷰 가격은 `product_price_snapshot`(product_master 사슬), main.py 보강 가격은 `online_food_price_snapshot` | 같은 화면에서 서로 다른 출처의 가격이 섞일 수 있음 |
| F4 | 100g당 가격 | 출처: 스냅샷 4% / kg당 단가÷10 49% / 상품명 중량 추정 11% / **없음 35%** | 추정은 상품명의 **마지막 중량**을 씀 → "5kg 7.5kg 15kg"이면 15kg → 100g당 가격 과소 |
| F5 | 확인 시각 | `online_food_price_snapshot.collected_at` 2026-04-24 ~ **2026-07-16**, 결합 294건 전부 30일 초과. 뷰의 `collected_at`은 `vw_trust_first_recommendation`에서 빠짐. `main.py` 응답에도 없음 | 1단계 "모든 가격에 확인 시각" 미충족 |
| F6 | **평점·리뷰가 DB 점수에 들어감** | `vw_recommendation_score`: review_score 15% + rating_score 10% (값 없으면 30·50점 기본). `vw_trust_first_recommendation`: 리뷰 35% + 평점 25%. 출처 구분 없음(`product_quality_snapshot`) | 2026-11-02 결정(스크래핑 평점·리뷰 점수 제외)이 DB fallback 경로에는 미적용. PR #2는 `score_engine`만 고침 |
| F7 | 플랫폼 점수 | `trust_platform_score`: 컬리 80, 우체국 75, 네이버·쿠팡 70, 기타 60 (가중 15%) | 제휴 여부 점수는 아니지만 판매처 이름으로 신뢰 점수를 줌 — 근거 확인 필요 |
| F8 | 라벨 문구 | "리뷰 검증 고당도 추천", "평점 우수 고당도 추천", "리뷰 검증 추천" | 미검증 리뷰를 "검증"으로 표현 — 근거 없는 단정 |

## 1단계 범위와의 관계
- 로드맵 1단계는 "새 산식 없음, 순위 불변(1926036 기준)". F6·F7을 고치면 DB fallback 순위가 바뀜 → 1단계 안에서 고치면 기준과 충돌
- F1·F2·F4·F5·F8은 **표시·결합 정리**로 다룰 수 있음. 단 순위 영향이 있는 것: F2(결합 가격이 바뀌면 가격 모드의 100g당 가격 정렬이 바뀜), F4(상품명 중량 추정값을 정렬에서 빼면 가격 모드 순위가 바뀜 — 지금은 계산 방식을 바꾸지 않음)
- F2를 URL 일치로 한정해도 상품·옵션 동일성이 검증된 것은 아님 — 최종 뷰에 `product_id`가 없고 URL 중복 1건이 있음

## 결정 (2026-11-10, 사용자)
- **F6 평점·리뷰 DB 점수: 1단계 전에 고침** → 고친 뒤의 결과를 1단계 '순위 불변' 기준점으로 삼음
  - 방식: 새 가중치 없이 모든 상품의 평점·리뷰를 '값 없음'으로 처리(뷰의 기존 기본값 리뷰 30·평점 50을 전 상품에 적용). `vw_recommendation_score`·`vw_trust_first_recommendation`만 수정, 컬럼 구성 유지. 리뷰·평점 근거 라벨 3줄('리뷰 검증 …', '평점 우수 …') 삭제
- **F7 플랫폼 점수: 보류** (2026-11-10 사용자 — "이름값 있는 플랫폼이라고 점수를 높게 줄 수 없다") → 같은 변경에서 모든 판매처 60(기존 '기타' 값)
  - 결과: `trust_first_score`는 고당도 여부 두 값(53.25 / 44.5)만 남음 → 점수 체계 재검토 `claude/scoring_review_2026-11-10.md`
  - 파일: `scripts/stage1_view_rating_fix.py` → `sql/migrations/2026-11-10_view_unverified_signal_exclusion.sql`(+ `_rollback.sql`)
- **F2 가격 결합: 끊음** — `main.py` LATERAL을 `s.product_url = r.product_url`로 한정. 결합이 없으면 뷰 가격·계산값 사용
- 전후 비교: `scripts/stage1_ranking_snapshot.py`(DB fallback 경로의 최종 표시 순위, 읽기 전용 연결). canonical pipeline은 쿠팡·네이버 API를 실시간 호출하므로 기본 제외(`--with-pipeline` 선택)
- 리눅스 테스트: chat·recommendation 범위 1,758 통과 / 2 실패(둘 다 기준선 기존 실패)

## 순위 비교 결과 (2026-11-10, Mac DB, DB fallback 경로, 질의 9 × 모드 7 = 63, 상위 10, session_id 없음)
스냅샷 `var/ranking_snapshots/`, 비교 `docs/claude/stage1_ranking_compare_*.md`

| 구간 | 같음 | 동점 내 자리만 | 순서 | 구성 |
|---|---|---|---|---|
| s0 변경 전 → s1 뷰 보정(trust_first만 적용됨) | 52 | 0 | 6 | 5 |
| s1 → s2 가격 결합 URL 한정 | 63 | 0 | 0 | 0 |
| s2 → s3 뷰 보정 완료(vw_recommendation_score 추가 적용) | 58 | 4 | 0 | 1 |
| s0 → s3 전체 | 47 | — | 10 | 6 |

- **실제 변화**: 망고 — 가격 모드를 뺀 5개 모드에서 상위 10 중 3개 교체(평점이 있던 애플망고 선물세트 등이 내려감). 멜론 — 순서 변화. 가격 모드는 망고 1건만 구성 변화
- **가격 결합 URL 한정은 상위 10에 영향 없음** — 잘못 결합되던 12건은 대부분 상위 10 밖, 들어간 1건(머스크멜론)은 같은 가격
- **s2→s3 변화 5건은 전부 동점 재배열**: `recommendation_score`는 최종 순위에 쓰이지 않음. 같은 점수끼리 DB가 정하는 임의 순서가 뷰 정의 변경으로 바뀐 것(사과 탐색 1건은 정렬 키 노출·클릭 수가 스냅샷에 없어 '구성'으로 분류됐으나 같은 점수끼리 교체)
- 적용 스크립트 버그: 첫 적용 때 주석 줄 처리 문제로 `vw_recommendation_score`가 빠짐 → 수정 후 재적용, 검사값 `{'r': 1, 'g': 1, 'tr': 1, 'tg': 1, 'tp': 1}`

## 동점 문제 (F9) — 순위 불변 검사의 전제
- 상위 10 결과 63개 중 **55개에 동점**(같은 adaptive_score)이 있음. 평점·리뷰·플랫폼을 상수로 바꾼 뒤 기본 점수가 두 값뿐이라 더 많아짐
- DB는 동점 순서를 보장하지 않아 뷰 정의·실행 계획만 바뀌어도 순서와 LIMIT 10에 드는 상품이 바뀜 → 이대로는 '순위 불변' 검사가 성립하지 않음
- 조치: `main.py` DB fallback의 모든 ORDER BY 끝에 `r.product_url` 추가(동점 시 고정 순서). Python 정렬은 안정 정렬이라 그대로 이어받음. 이 순서 자체에 의미는 없음 — 재현성만 위한 것
- 남는 한계: URL 중복 1건(같은 URL 2행)은 여전히 동점 가능

## 1단계 순위 기준점
- **s4 = 뷰 보정 완료 + 가격 결합 URL 한정 + 동점 고정 순서** 적용 직후. 두 번 찍어 같음을 확인한 뒤 확정

## 남은 결정
- F8 표시 라벨 문구, 채팅 카드의 '평점 4.9' 배지(service.py) — 1단계 내부 화면 작업에서 다룸

## 다음 확인
- canonical pipeline은 `app/services/market/collector.py`로 쿠팡 API(·네이버 쇼핑 API)를 실시간 호출 — 네이버 쇼핑 API 종료 후 동작과 fallback 발생 빈도 (`recommendation_path` 로그)
- `product_quality_snapshot`의 평점·리뷰 건수와 출처
