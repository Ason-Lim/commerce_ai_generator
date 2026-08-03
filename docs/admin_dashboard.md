# Commerce AI Generator 백오피스 지표 정의서

## 1. 목적

Commerce AI Generator의 추천 품질, 사용자 선호도, 노출 성과를 측정하여 추천 알고리즘을 지속적으로 개선한다.

---

# 2. 핵심 KPI

## 총 검색 수

데이터 출처

```sql
search_log
```

의미

사용자가 추천을 요청한 횟수

활용

* 서비스 사용량 측정
* 추천 기능 이용 추세 분석

---

## 총 노출 수

데이터 출처

```sql
impression_log
```

의미

사용자에게 추천 상품이 화면에 노출된 횟수

활용

* 추천 엔진 사용량 측정
* 상품 노출 규모 확인

---

## 총 상품 클릭 수

현재 상태

```text
Streamlit 단계에서는 미사용
```

향후

```text
Next.js 전환 후 활성화
```

데이터 출처

```sql
product_click_log
```

---

## 전체 CTR

공식

```text
클릭수 ÷ 노출수 × 100
```

현재

```text
테스트 데이터 포함
```

운영 CTR 아님

---

# 3. 추천 모드 성과

데이터 출처

```sql
vw_recommendation_mode_ctr
```

분석 항목

* Quality 추천
* Price 추천
* Trust 추천
* Exploration 추천

목적

추천 전략별 성과 비교

예시

```text
Quality 42%
Price 29%
Trust 14%
Exploration 14%
```

---

# 4. 상품별 성과 분석

데이터 출처

```sql
vw_product_performance
```

분석 항목

* 상품명
* 노출수
* 클릭수
* CTR

목적

반응이 좋은 상품 파악

활용

* Hero 후보 선정
* 품질 추천 강화

---

# 5. 플랫폼별 성과 분석

데이터 출처

```sql
vw_platform_performance
```

분석 항목

* 네이버쇼핑
* 컬리
* 향후 쿠팡
* 향후 SSG

목적

플랫폼별 공급 경쟁력 분석

활용

* 플랫폼 확장 우선순위 결정
* 제휴 전략 수립

---

# 6. 추천 순위별 성과

데이터 출처

```sql
vw_rank_performance
```

분석 항목

* 1위
* 2위
* 3위
* ...
* 10위

목적

Hero 상품 노출 효과 분석

활용

* 추천 UI 개선
* 노출 전략 개선

---

# 7. 추천 방식 선호도

데이터 출처

```sql
vw_recommendation_feedback
```

분석 항목

* Quality
* Price
* Trust
* Exploration

목적

사용자 선호 추천 방식 분석

향후 활용

```text
추천 점수 자동 보정
```

예시

```text
Quality 사용률 ↑
→ Quality Boost 증가

Price 사용률 ↑
→ Price Boost 증가
```

---

# 8. 검색어 분석

데이터 출처

```sql
search_log
```

분석 항목

* 인기 검색어 TOP10
* 검색량 추이

목적

수요 파악

예시

```text
사과
참외
고당도 과일
선물세트
```

---

# 9. 추천 기준 분석

분석 항목

* 품질 추천
* 가성비 추천
* 신뢰 추천
* 탐색 추천

목적

추천 모드 사용 패턴 파악

---

# 10. 검색 의도 분석

데이터 출처

```sql
user_context_log
```

분석 항목

* 선물 대상
* 예산대
* 시즌/상황
* 추가 질문 필요 여부

목적

AI 컨텍스트 품질 향상

---

# 11. Streamlit 클릭 로그 정책

현재 CTA는 HTML 링크 기반이다.

```html
<a href="상품URL">
```

이 방식은 클릭 시 Python 함수가 실행되지 않는다.

따라서

```python
log_product_click()
```

는 호출되지 않는다.

현재 단계에서는

```text
impression_log 중심 운영
```

을 사용한다.

---

# 12. Next.js 최종 구조

향후 구현

```text
사용자 클릭
↓
POST /api/log/click
↓
product_click_log 저장
↓
상품 페이지 이동
```

사용자는 로깅을 인지하지 않는다.

---

# 13. 향후 로드맵

Phase 1 완료

✅ 추천 엔진
✅ 노출 로그
✅ 상품 성과
✅ 플랫폼 성과
✅ 순위 성과
✅ 추천 방식 선호도

Phase 2

⏳ CTR 정상화
⏳ 상품 CTR 기반 자동 추천

Phase 3

⏳ Revisit 추천
⏳ 사용자 프로필 추천
⏳ AI 자동 랭킹 최적화

---
