# score_engine 00_1 결정·리팩터링 (2026-11-09)

상태: 1차 커밋 06f72f1(브랜치 stage1/score-engine-00_1, 원격 푸시됨) + 검증 보완 2차 커밋 → PR

## 00_1 결정 적용 범위 (구분)
- **00_1 자체**: F2-A1 텍스트 참조 금지 패턴에서 score_engine·compare_engine 제외 (PM-2 의존 보존). test_f2a에 보존·금지 목록 비중첩 검사.
- **00_1과 별개 변경 — 근거를 각각 연결**
  - 평점·리뷰 기본 제외: 사용자 결정 2026-11-02 (스크래핑 평점·리뷰는 DB 보관, 점수 제외) · 2026-11-03 (검증 로그 값만 verified)
  - 탐색 모드 NameError 수정: 버그 (이전엔 exploration 정렬 전부 실패)
  - quality 100 상한, total을 상한 적용값으로: 산식 정합성 (화면 세부 점수와 total 일치)
  - `_adaptive` total 가중치: 정합성. mode_score는 원래 base priority를 써서 순위 영향 없음, total만 변함
  - 캐시 신뢰도 0 → 0 유지 (이전 50): 버그
  - dict search_context trend_boost 반영: 호환성. 비교 입력에서는 미사용

## explain_score_inputs() (1단계 내부 시범용)
- inputs_used: 실제 사용값과 brix 출처(field:<이름> / text), 평점은 사용 시에만 값
- defaults_applied: brix 0, 단위가격 0, Identity 캐시 없을 때 신뢰도 50
- excluded: 평점 제외 코드 flag_missing / flag_false / flag_not_true + review_source
- formula_id + formula_status="local_unreleased" — 배포·검증 계보 버전으로 표시 금지
- affiliate_bonus: False

## 테스트 (Mac Python 3.14, 2026-11-09 사용자 실행)
- 전체: **5,508 통과 / 7 실패 / 5 건너뜀**
- 실패 7건 = 0단계 기준선의 8건에서 f2a 경계 충돌 1건을 뺀 목록과 동일 (recipe_discover trace, reselect_golden, at_48, seafood 2, persistence_i5b 2) → 새 실패 없음
- 참고 Linux 3.10: 보완 전 전체 5,497 / 7 / 5, 보완 후 대상 범위 1,267 통과
- 평점 제외 경로: 키 없음·False·None·"True"·1 각각 평점 없는 상품과 같은 점수 + 제외 코드, 파싱 불가 평점은 0

## 전후 점수·순위 비교 (엔진 단계만)
스크립트 scripts/compare_score_engine_versions.py. 결과 docs/claude/score_engine_compare_{fixture,db}_2026-11-09.{md,json}

**실데이터 (Mac, vw_ai_recommendation_final 294건, 읽기 전용)**

| 모드 | 순위 변화 | 상위 10 유지 |
|---|---|---|
| trust | 9 | 10/10 |
| quality | 7 | 8/10 |
| price | 6 | 10/10 |
| mix | 6 | 8/10 |
| discovery | 10 | 8/10 |
| exploration | 이전 294건 전부 NameError → 이후 정상 | — |

- 점수가 바뀐 상품은 5건뿐 — 모두 페이지 보강 평점·리뷰가 있던 상품(만다린·애플망고 등). 다른 상품의 순위 변화는 이 5건의 하락에 따른 연쇄
- 가장 큰 변화: trust 모드 1위였던 애플망고 선물세트(평점 반영)가 8위로
- quality 상한·캐시 신뢰도 0 수정은 이 데이터에서 실제 영향 없음
- 관찰: 뷰에 상품 id 컬럼이 없어 행 번호(rowN)로 식별 — 실행마다 같은 행 순서인지 보장 안 됨. 대부분 상품 가격 점수 0 (뷰에 price_per_100g 없음으로 보임 — 별도 확인)

**대표 입력 fixture 8건**: 스크래핑 평점 상품 trust 2→7위, 신뢰도 0 상품 price 2→6위, 품질·가격 상한은 점수만 변함

**범위 한계**: main.py·explain.choose 이후 최종 표시 순위는 미확인 → 1단계 내부 시범에서 확인

## 백업
recipe_chat_api_backups/20261109_score_engine_refactor/

## 다음
1. 2차 커밋 → PR → main 병합
2. 추천 화면 내부 시범: 가격 관측 시각·점수 입력·제외 사유·최종 표시 순위
3. 별도 확인: vw_ai_recommendation_final의 상품 id·price_per_100g
