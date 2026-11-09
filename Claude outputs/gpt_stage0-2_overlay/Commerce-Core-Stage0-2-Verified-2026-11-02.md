# Commerce AI 0~2단계 소스 검토·서비스 보완 결과

기준일: 2026-11-02 (KST)
입력: commerce_ai_generator_review_2026-11-02.zip 및 commerce_core_stage0-2_2026-11-02(1).md.

## 결과

첨부된 실제 소스에서 기존 공통 모델과 wrapper의 존재를 확인했다. 중복 wrapper를 새로 만드는 대신 누락된 점수·경로 provenance와 근거 사용 판정을 보완했다. 현재 추출본에서만 변경했으며 Mac 원본에는 반영되지 않았다. REST 호출 교체, MCP 공개, 상세페이지 수집, 실제 API·LLM 호출은 수행하지 않았다.

공통 모델의 commerce.v1과 상태 6종은 내부 잠정 계약이다. 이번 변경은 공개 계약·canonical Product/Offer 발급 책임·기존 Tier A 보류 항목을 확정하지 않는다.

## 0. 확인한 호출 관계

| 구간 | 실제 소스 및 호출 |
|---|---|
| 채팅 진입 | app/api/chat_routes.py:148 chat → ChatService.handle |
| 기본 추천 공급 | app/services/chat/service.py:75 default_shopping → app/main.py:336 natural_language_recommendations |
| 정식 추천 | app/services/recommendation_pipeline.py:299 run_recommendation_pipeline → compose_production_recommendation_provider → provider.recommend → canonical_result_to_compatibility_response |
| 정식 경로 태그 | app/main.py:348 recommendation_path=canonical_provider |
| 실패 대체 경로 | main.py의 DB 조회·개인화·adaptive 정렬 후 :810 recommendation_path=db_fallback |
| 쇼핑 첫 턴 | service.py:503 _shopping_turn → 예산 파싱·검색어 추출 → _fetch → 카드 보강 → 관련성 필터 → 업체 결과 합류 → 쇼핑커넥트 별도 목록 → explain.choose → KAMIS 주석 |
| 실제 최종 선택 | app/services/chat/explain.py:125 choose. 역할별 선택 후 남은 자리는 입력 순서를 따름 |
| 재선택 경로 | service.py:340 관심 상품 비교, :370 예산 응답도 choose 호출. 현재 검색 wrapper에는 미포함 |
| 공통 검색 | app/services/commerce/search.py collect → 같은 카드 처리 함수·choose → search_products가 공통 모델로 투영 |
| 레시피 공통 조회 | app/services/commerce/recipes.py get_recipe → RecipeResolver.get/find → 원문/AI 제안 구분하여 투영 |

REST의 기존 ChatService는 아직 공통 검색 wrapper를 호출하지 않는다. 따라서 이번 결과는 0~2단계 공통 서비스 검증이며 3단계 REST 통합 완료가 아니다. wrapper가 app.services.chat.service 내부 helper에 의존하므로 transport 독립 서비스로의 완전 분리 역시 완료된 것은 아니다.

## 1. 필드 매핑

| 기존 입력/카드 | 공통 모델 | 의미·한계 |
|---|---|---|
| pid/key | Product.product_id/key | 기존 로컬 참조. canonical 식별자로 승격하지 않음 |
| title/image/weight_g/unit_count/seller_claims | Product 동명 필드 및 image_url | 원문 판매자 주장과 검증 사실 구분 필요 |
| mall | Offer.platform | 플랫폼 표기 |
| source (= item_to_card의 seller_name 우선) | Offer.merchant | 플랫폼과 같은 값, 빈 값, 판매처 기본 문구면 None |
| url | Offer.product_url | safe_url 통과한 링크 |
| price/shipping_fee/total | Offer.price_krw/shipping_krw/total_krw | 정수 원. 배송비 미확인은 None. 원천 카드가 price 누락을 0으로 바꾸는 기존 동작은 보존됨 |
| per100g/per_unit | Offer.per100g_krw/per_unit_krw | 원래 계산값 투영. 이번에 계산식 변경 없음 |
| affiliate/affiliate_program/direct | Offer.link_type/affiliate_program/opens_directly | 제휴·직접 이동 구분 |
| rank/role/role_label/why | ScoreDetail.rank/role/role_label/reasons | choose 이후 표시 순서·역할·사유 |
| 명시적 final_score/v8_final_score | ScoreDetail.engine_score | 기존 의미 유지. 다른 점수를 임의로 최종 점수로 채우지 않음 |
| score/final_score/v8_final_score/v7_final_score/final_recommendation_score/adaptive_score | **ScoreDetail.upstream_scores** | 이번 추가. 실제로 제공된 유한 숫자만 원래 필드명으로 보존. 점수 간 동일성·계산식은 추정하지 않음 |
| 원천 item.rank | **ScoreDetail.upstream_rank** | 이번 추가. 최종 표시 rank와 구분 |
| result.recommendation_path | **Provenance.recommendation_path** | 이번 추가. 실제 응답의 분기 태그 보존 |
| 정식/대체 분기 | **ScoreDetail.fallback_used** | canonical_provider=False, db_fallback=True, 미제공/미확인=None. 업체·등록부 항목에 공급자 분기를 잘못 적용하지 않음 |
| rating/review_count | Evidence(method=unknown) | 원천 출처 미확인, 점수 사용 미허용. 상위 엔진의 소비 차단을 의미하지 않음 |
| market_ref | ShoppingItem.price_reference | KAMIS 참고, choose 이후 추가 |

실제 compatibility 응답은 score를 사용하며 canonical 경로는 v7_final_score 또는 final_recommendation_score에서 alias를 만든다. DB fallback의 score는 base 값이고 정렬에는 adaptive 값 등 다른 기준이 개입한다. 기존 wrapper는 final_score/v8_final_score만 보아 이 정보를 누락하고 있었다. 이번에는 upstream_scores로 분리 보존하며 engine_score를 compatibility alias로 대체하지 않았다.

## 2. 수행한 코드 보완

- app/domain/commerce/models.py: upstream_scores, upstream_rank, recommendation_path 추가. fallback_used의 기본값을 False에서 None으로 변경하여 미확인을 미사용으로 단정하지 않음.
- app/services/commerce/search.py: 공급자의 분기 태그·실제 점수 필드·상위 순위를 공통 응답으로 전달. bool, NaN, Infinity, 숫자 문자열을 점수로 자동 승격하지 않음. 표시 순위·상품 선택은 기존 함수 사용.
- app/domain/commerce/policies.py: score_usable이 usable_for_score=True와 verified를 함께 요구. html/ocr/unknown은 차단 유지.
- tests/services/chat/test_commerce_provenance.py: 위 누락·오판정에 대한 16개 회귀 사례 추가.

score_usable 보완은 해당 함수의 반환 판정을 바로잡은 것이다. 현재 검색 경로가 이 함수를 실제 추천 엔진 입력 gate로 호출하는 것은 아니다. 따라서 상위 엔진 전체의 Evidence 기반 통제가 구현되었다고 주장하지 않는다.

추가 필드는 additive하지만 fallback_used의 nullable 전환은 향후 reader가 확인해야 한다. 현재 외부 REST/MCP에 wrapper가 연결되지 않았다는 범위에서 수정했다.

## 3. 검증 결과

실행 환경: 이 작업 공간 Linux Python 3.12. Mac .venv 환경과 별개. 테스트용 pytest·SQLAlchemy·python-dotenv를 설치했다. 원격 API를 호출하지 않는 fixture 테스트를 실행했다.

| 실행 | 결과 |
|---|---|
| 수정 전 기존 계약 테스트 | 20 passed |
| 새 회귀 테스트를 수정 전 코드에 실행 | 13 failed, 3 passed |
| 보완 후 기존 계약 + 새 회귀 | 36 passed |
| 보완 후 위 2개 + shopping_reasons + shopping_relevance + partner_products | **67 passed** |

실행 명령:

```bash
python -m pytest tests/services/chat/test_commerce_contract.py tests/services/chat/test_commerce_provenance.py tests/services/chat/test_shopping_reasons.py tests/services/chat/test_shopping_relevance.py tests/services/chat/test_partner_products.py -q
```

전체 5천여 테스트는 이번에 재실행하지 않았다. 첨부 _review의 before 5010/after 5030 및 실패 11건은 제공 로그를 확인한 값이다. 이번 67개 통과를 전체 회귀·실판매처·배포 검증으로 확대하지 않는다. 실제 파일 삭제 가능성이 보고된 test_surge도 실행하지 않았다.

## 4. OCR 실제 구현 확인 및 이전 문서 보정

현재 확인한 범위에서 commerce_ai_local_ocr/는 독립 오프라인 도구다. app/·scripts/·tests/에서 이 패키지나 read_image/read_pdf에 대한 참조 검색 결과는 없었다. 기존 검색 wrapper에 OCR이 연결되어 있다고 볼 근거가 없다.

| 구성 | 확인한 구현 |
|---|---|
| engine.py | Tesseract subprocess, TSV에서 text/confidence/bbox 추출. read_image 결과는 OCR_EXTRACTED_UNVERIFIED 또는 NO_TEXT_DETECTED, field_validation=NOT_PERFORMED |
| regions.py | 후보 영역 검출, 2배 확대·전처리, map_word로 원본 좌표 환산. source_sha256, image_sha256, 원본 크기, bbox, scale을 bundle.json에 보존 |
| 영역 한계 | coverage=PARTIAL_CANDIDATES_ONLY, 생략 영역 수 기록. 전체 필드 추출 보장이 아님 |
| review.py | 선택 영역을 OpenAI에 추출·대조 최대 2회 요청하는 선택 기능. 실행은 하지 않음 |
| 호출 기록 | receipt에 attempted_calls와 응답 usage를 기록하는 코드가 있음. cost_usd=None. 따라서 사용량 계측 전체가 없다고 단정하면 부정확하며 금액 정산·공통 서비스 집계와 구분해야 함 |
| 검증 상태 | 도구 결과의 field_validation=NOT_PERFORMED, human_review=PENDING. LLM 대조만으로 상품 사실 검증이나 점수 허용이 성립하지 않음 |

이전 OCR 보완 설계 중 해시·좌표·전처리 관계·일부 사용량 기록은 이미 구현돼 있다. 새로 중복 구현하기보다 기존 bundle을 evidence 모델에 연결할 매핑이 필요하다. 상품/Offer/옵션 연결, 용도별 허용 판정, 충돌 저장·해결, 통합 정책 gate는 이번 조사로 완료가 입증되지 않았다.

수집 대상은 첨부 응답에서 정한 **허락 기록이 있는 업체 제공 자료 등**을 기준으로 한다. 현재 partners/feed.py도 상품 표시·이미지 표시·가격 비교·외부 AI 전송을 별도 권한으로 구분한다. 이미지 표시 허락만으로 OCR 처리나 외부 AI 전송 허락을 추론하면 안 된다. 이번 작업은 보관된 쿠팡·네이버 상세페이지 수집기를 다시 사용하지 않았다.

## 5. 남은 작업

1. 이번 수정 파일을 Mac의 현재 파일과 diff로 대조하고 백업 후 반영한다. 첨부 ZIP 기준과 달라진 부분이 있으면 단순 덮어쓰지 않는다.
2. Mac .venv에서 같은 67개 테스트를 실행한다.
3. provider의 warnings, engine_version 등 공통 projection에 아직 전달하지 않는 metadata와 오류 범위를 추가 매핑한다. 비교는 fixture의 검증 범위로 한정한다.
4. REST 교체 단계에서 첫 쇼핑 턴 외 예산 응답·관심 상품 재비교의 choose 경로와 NLU memo·상태 저장·링크 동작을 함께 보존한다.
5. OCR은 허용된 로컬 이미지 fixture 하나와 기존 bundle로부터 상품·옵션·증거 연결을 먼저 검증한다. HTML/OCR 점수 차단은 유지한다.
6. 공개 계약/클라이언트 호환성을 확인한 후 MCP 1차 도구를 연결한다.

## 묶음 사용

전달 ZIP에는 이번 수정본의 공통 모델·서비스 파일, 기존 계약 테스트와 새 회귀 테스트, 기준 대비 patch, 원본 파일 SHA-256, 이 보고서, 테스트 로그가 들어 있다. 자동 적용 스크립트는 포함하지 않았다. app/services/chat/service.py, app/main.py, 기존 점수 엔진은 수정하지 않았다. 첨부 소스 전체의 대체본이 아니라 0~2단계 검토·보완 파일 묶음이다.
