# Commerce AI Logging Design v1.0

## 1. 목적

Commerce AI의 추천 품질은 사용자 반응 데이터를 기반으로 지속적으로 향상된다.

따라서 모든 추천 결과에 대해 노출, 클릭, 관심, 구매 행동을 추적할 수 있는 구조를 설계한다.

---

## 2. 핵심 원칙

사용자는 로깅을 의식하지 않아야 한다.

사용자가 경험하는 흐름은 다음과 같다.

상품 보러가기 클릭

↓

상품 페이지 이동

백그라운드에서는 로그가 저장된다.

---

## 3. 로그 종류

### search_log

사용자 검색 기록

수집 항목

* session_id
* query
* priority
* result_count
* top_product_name
* top_product_score

---

### product_click_log

상품 클릭 기록

수집 항목

* session_id
* query
* product_id
* product_name
* seller_name
* product_url
* recommendation_mode
* selected_priority
* selected_section
* rank
* platform
* mall_name
* price
* clicked_at

---

### impression_log

추천 결과 노출 기록

수집 항목

* session_id
* query
* product_id
* rank
* recommendation_mode

---

### recommendation_result_log

추천 결과 생성 기록

향후 확장 예정

---

## 4. recommendation_mode 정의

허용 값

```text
ranking
price
quality
trust
exploration
revisit
```

금지 값

```text
unknown
hero
NULL
빈 문자열
```

---

## 5. UI 위치 정의

selected_section

```text
hero
main
related
exploration
```

설명

* hero = 1위 추천 상품
* main = 2~4위 추천 상품
* related = 연관 추천
* exploration = 탐색 추천

---

## 6. priority 정의

selected_priority

```text
value
quality
trust
ranking
```

설명

* value = 가성비 추천
* quality = 품질 추천
* trust = 신뢰 추천
* ranking = 기본 추천

---

## 7. 로그 검증 SQL

추천 모드 확인

```sql
SELECT
    recommendation_mode,
    COUNT(*) AS click_count
FROM product_click_log
GROUP BY recommendation_mode
ORDER BY click_count DESC;
```

---

최근 클릭 확인

```sql
SELECT *
FROM product_click_log
ORDER BY id DESC
LIMIT 20;
```

---

## 8. 로그 품질 검증

정상 상태

```text
ranking
price
quality
trust
exploration
revisit
```

비정상 상태

```text
unknown
hero
NULL
빈 문자열
```

---

## 9. unknown 처리 정책

unknown은 정상 추천 데이터로 사용하지 않는다.

발생 원인

* recommendation_mode 누락
* fallback 값 사용
* 잘못된 UI 연결

현재 정책

```python
if not recommendation_mode:
    recommendation_mode = "ranking"
```

추가로 콘솔 경고를 출력한다.

```python
WARNING: recommendation_mode missing
```

---

## 10. 추천 엔진 학습 활용

추천 엔진은 클릭 데이터를 학습에 활용한다.

활용 항목

* 클릭 수
* 클릭률
* 관심도
* 재방문

현재 단계

```text
click_count
ctr_pct
```

활용

향후 단계

```text
favorite
purchase
```

추가 활용

---

## 11. Streamlit 클릭 로그 한계

현재 Streamlit UI의 CTA는 HTML 링크 기반이다.

```html
<a href="상품URL">
```

이 방식은 클릭 시 Python 함수가 실행되지 않는다.

따라서

```python
log_product_click()
```

가 호출되지 않는다.

---

## 12. Streamlit 임시 전략

현재 단계에서는 UX 안정성을 우선한다.

유지할 방식:

<a href="상품URL">

장점:

새 탭 이동
Hero UI 유지
사용자 경험 우수

단점:

클릭 로그 수집 불가
CTR 분석은 제한적임

현재 정책:

Streamlit 단계에서는 impression_log를 중심으로 노출 분석을 수행한다.
product_click_log는 과거 테스트 로그로 보존한다.
신규 클릭 로그 수집은 Next.js 전환 후 구현한다.


---


## 13. Next.js 최종 전략

Next.js 최종 전략

Next.js 전환 후 다음 구조를 사용한다.

사용자 클릭
↓
POST /api/log/click
↓
product_click_log 저장
↓
상품 상세 페이지 이동

사용자는 로깅을 인지하지 않는다.


---

## 14. 추천 품질 향상 로드맵

### Phase 1

* ranking
* trust

---

### Phase 2

* price
* quality

---

### Phase 3

* exploration

---

### Phase 4

* revisit

---

### Phase 5

* 개인화 추천

---

## 15. 현재 구현 상태

완료

```text
search_log
product_click_log v2
platform_master
recommendation_engine.md
design.md
logging.md
```

진행 중

```text
recommendation_mode 분리
exploration 추천 복구
클릭 로그 전략
```

예정

```text
Next.js 전환
사용자 반응 기반 추천
개인화 추천
```
