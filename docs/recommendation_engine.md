# Commerce AI Recommendation Engine v0.1

## 1. 목적

Commerce AI Recommendation Engine은 단순 최저가 추천 엔진이 아니다.

사용자의 검색 의도(Context)와 상품 데이터를 결합하여 가장 적합한 상품을 추천하는 것을 목표로 한다.

추천은 다음 요소를 종합적으로 평가한다.

* 가격
* 품질
* 신뢰도
* 사용자 반응
* 추천 맥락(Context)

---

# 2. 추천 모드

Commerce AI는 여러 추천 모드를 제공한다.

---

## ranking

기본 추천

사용자에게 가장 먼저 보여주는 추천 결과

---

평가 기준

* 가격
* 품질
* 신뢰도
* 사용자 반응

종합 점수 기반

---

사용 위치

* Hero 카드
* 기본 추천 결과

---

## price

가성비 추천

---

목적

가격 경쟁력이 높은 상품 추천

---

평가 기준

* 가격
* 할인율
* 단위가격

---

가중치

price_score 중심

---

사용 위치

* 가성비 추천 탭

---

## quality

품질 추천

---

목적

품질이 우수한 상품 추천

---

평가 기준

* 평점
* 리뷰수
* 당도(Brix)
* 품질 관련 정보

---

가중치

quality_score 중심

---

사용 위치

* 품질 추천 탭

---

## trust

신뢰 추천

---

목적

안전하게 구매 가능한 상품 추천

---

평가 기준

* 판매자 신뢰도
* 리뷰 수
* 상품 안정성

---

가중치

trust_score 중심

---

사용 위치

* 신뢰 추천 탭

---

## exploration

탐색 추천

---

목적

사용자가 아직 보지 않은 상품 탐색

---

평가 기준

* 노출 적음
* 클릭 적음
* 신규 상품

---

사용 위치

* 탐색 추천 탭

---

## revisit

재방문 추천

---

목적

과거 행동을 반영한 추천

---

평가 기준

* 최근 클릭
* 최근 관심
* 최근 검색

---

사용 위치

* 재방문 사용자

---

# 3. 추천 점수 구조

추천 점수는 여러 점수의 조합이다.

---

최종 점수

final_score

---

구성 요소

* price_score
* quality_score
* trust_score
* engagement_score

---

# 4. Price Score

가격 경쟁력

---

평가 항목

* 현재 가격
* 할인율
* 동일상품 비교 가격
* 단위가격

---

범위

0 ~ 100

---

예시

최저가 상품

price_score = 100

---

# 5. Quality Score

품질 점수

---

평가 항목

* 평점
* 리뷰 수
* Brix
* 품질 정보

---

예시

고당도 사과

Brix 15

평점 4.9

리뷰 300개

quality_score 상승

---

# 6. Trust Score

신뢰 점수

---

평가 항목

* 판매자
* 리뷰 수
* 데이터 완성도

---

예시

가격 있음

중량 있음

리뷰 있음

평점 있음

↓

trust_score 상승

---

# 7. Engagement Score

사용자 반응 점수

---

평가 항목

* 클릭
* 관심
* 재방문
* 구매

---

현재 단계

클릭 로그 기반

---

향후

구매 로그 포함

---

# 8. Ranking 가중치

현재 기본값

price_score = 30%

quality_score = 30%

trust_score = 20%

engagement_score = 20%

---

최종 점수

final_score =
0.30 × price_score +
0.30 × quality_score +
0.20 × trust_score +
0.20 × engagement_score

---

# 9. 추천 이유 생성

추천 결과에는 추천 이유를 표시한다.

---

예시

이 상품은

* 가격 경쟁력이 높고
* 리뷰 수가 많으며
* 사용자 반응이 우수하여

추천되었습니다.

---

# 10. 사용자 반응 학습

수집 대상

---

impression

노출

---

click

클릭

---

favorite

관심

---

purchase

구매

---

# 11. 로그 활용 원칙

모든 CTA 클릭은 로그를 남긴다.

---

필수 항목

* recommendation_mode
* rank
* product_id
* product_name
* price
* platform
* mall_name

---

unknown 저장 금지

unknown은 오류 상태로 간주

---

# 12. 동일상품 매칭 연동

추천 엔진은 동일상품 매칭 결과를 활용한다.

---

예시

네이버

↓

쿠팡

↓

컬리

↓

이마트몰

↓

우체국쇼핑

---

비교 항목

* 가격
* 단위가격
* 리뷰
* 품질

---

# 13. AI 추천 설명

Commerce AI는 추천 이유를 설명한다.

---

예시

"이 상품은 동일 상품군 대비 가격 경쟁력이 높고 리뷰 수가 많아 추천되었습니다."

---

전문 용어 사용 금지

CTR → 사용자 반응

Conversion → 구매 전환

Engagement → 관심도

---

# 14. 향후 확장

v0.2

클릭 기반 추천

---

v0.3

재방문 추천

---

v0.4

구매 기반 추천

---

v0.5

개인화 추천

---


# 15. Adaptive Score v1


## 목적

사용자의 추천 방식 선호도를 추천 점수에 반영한다.

기존 추천 엔진은 상품 데이터 중심으로 동작한다.

Adaptive Score는 사용자 행동 데이터를 활용하여 추천 엔진을 점진적으로 학습시키는 첫 단계이다.

---

## 공식

```text
adaptive_score =
final_recommendation_score
+
mode_boost
```

---

## mode_boost

데이터 출처

```sql
vw_recommendation_mode_boost
```

---

현재 기준

| recommendation_mode | mode_boost |
| ------------------- | ---------: |
| quality             |          5 |
| price               |          3 |
| trust               |          1 |
| exploration         |          1 |

---

예시

```text
final_recommendation_score = 71.3
mode_boost = 5

adaptive_score = 76.3
```

---

## 현재 상태

Adaptive Score는 API 응답에만 포함된다.

현재 정렬은 다음 기준을 유지한다.

```text
final_recommendation_score DESC
```

---

## 정렬 반영 정책

충분한 운영 데이터가 확보되기 전까지는
Adaptive Score를 실제 랭킹에 반영하지 않는다.

현재 단계

```text
adaptive_score 생성
```

다음 단계

```text
adaptive_score 검증
```

향후

```text
adaptive_score 기반 정렬
```

---

# 16. 노출 기반 학습 구조

현재 Commerce AI는 클릭보다 노출 데이터를 우선 활용한다.

이유

```text
Streamlit CTA 구조에서는
안정적인 클릭 수집이 어렵다.
```

---

현재 활용 데이터

```text
impression_log
```

분석 항목

* 추천 모드별 노출
* 상품별 노출
* 플랫폼별 노출
* 순위별 노출
* 추천 방식 선호도

---

# 17. 현재 구현 상태

## 완료

✅ 추천 엔진

✅ Context 분석

✅ Hero 추천

✅ impression_log

✅ 추천 모드 성과 분석

✅ 상품 성과 분석

✅ 플랫폼 성과 분석

✅ 추천 순위별 성과 분석

✅ 추천 방식 선호도 분석

✅ Adaptive Score v1

---

## 보류

⏸ Revisit 추천

⏸ 개인화 추천

⏸ 구매 기반 추천

⏸ CTR 기반 자동 학습

---

## Next.js 전환 후

구현 예정

```text
사용자 클릭
↓
POST /api/log/click
↓
product_click_log 저장
↓
상품 페이지 이동
```

---



# 18. Commerce AI Learning Roadmap

v0.1

기본 추천 엔진

---

v0.2

노출 기반 학습

---

v0.3

클릭 기반 학습

---

v0.4

재방문 추천

---

v0.5

개인화 추천

---

v1.0

Commerce AI Learning Recommendation Engine

## Adaptive Score v2

Adaptive Score v2는 추천 점수를 실제 정렬에 반영하는 실험 모드이다.

공식:

```text
adaptive_score =
final_recommendation_score
+ mode_boost
+ product_boost

