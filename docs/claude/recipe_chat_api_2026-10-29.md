# 대화 API 이전 — commerce_ai_generator /api/chat (쇼핑·레시피) · 2026-10-29

결정: React(`integrated_system/ui_ux`)의 대화 API를 integrated_system `consumer/app.py`(:8000)에서 **commerce_ai_generator `POST /api/chat`(:8001)** 로 옮김. 인트로·컴포넌트는 그대로, `npm run dev:commerce`(`.env.commerce`)로 프록시 대상만 변경.

- 쇼핑: 기존 `/recommendations/nl` 함수 호출 → `product_list` 블록, `/go/{sid}/{rank}` 는 그 세션에 보여 준 URL로만
- 레시피: `app/services/recipe_chat` 가 기존 `recipe_session`(EPIS 467 크림소스파스타 스냅샷, save_direct·flow·resume·동시수정 검증) 재사용
  - 직접 남은 양만 저장, 팩 용량×잔량%는 참고 계산(저장 안 함), 컵 단위 환산 안 함, 보유량 입력으로 충분·부족·구매동의 불변
  - 조리·대체 질문은 '원문 근거'와 '일반 조리 제안(원문 아님)'을 분리, 상품 검색은 명시 요청 때만
- NLU: food-nlu 의 LLMClient(DeepSeek 호출 계약 동일)·사전 프롬프트(바이트 동일)·validate 를 `app/services/nlu` 로 이식. 외부 폴더 로딩/sys.path/`/Users/...` 제거
- NLU 사전(intent/slot/entity)은 food-nlu 의 별도 DB(postgres) → `scripts.migrate_nlu_dictionary`(dry-run 기본, 충돌 행 미덮어쓰기)로 commerce DB 이관 필요
- 새 테이블: `recipe_chat_session` (sql/recipe_chat_tables.sql, IF NOT EXISTS)

## 1단계 — 레시피 카드 + 공공 레시피 카탈로그
- 카탈로그 5,198건 → `recipe_catalog` 테이블 (`scripts.import_recipe_catalog`, dry-run 기본). `recipe_card` 블록, 사진은 이용 조건 확인한 출처만(`RECIPE_IMAGE_SOURCES=foodsafety`)
- 식품안전나라 COOKRCP01 키는 식품안전나라 발급(공공데이터포털 운영계정 절차와 별개로 보임). 호출은 수집 때만

## 2단계 — 쉽게 보기 · 일반 팁 · 화면 정리
- **쉽게 보기** (`easy_view.py`): DeepSeek가 원문 단계를 정리, 서버가 원문과 대조(모든 단계 포함, 새 숫자·재료·분량 금지), 실패 시 1회 재시도 후 원문. 백그라운드 생성 + `GET /api/recipe/easy` 폴링 + `recipe_easy_view` 캐시, `scripts.build_recipe_easy_views`
- 컵 분량: 원문 + 참고 mL 기본 표시(1컵=200mL, 보유량 계산에는 미사용) → **6단계에서 기본 표시 제거**. 비슷한 레시피는 재료 겹침 순

## 3단계 — 완성 사진 먼저 · 부족한 재료
- 카드 순서: 완성 사진 → 설명 → 재료 → 부족한 재료 → 만드는 순서 → 팁
- 사진: 식품안전나라 큰 사진(`image_large`, 재수집 필요), EPIS는 **AI 생성 이미지**(OpenAI Images, "AI 생성 예시 이미지" 표시, `recipe_ai_image`, 하루 상한 30)
- 부족한 재료: 고객 판단·남은 양 표시, '부족'/'없음' 버튼 → 대화로 기록, '부족한 재료 상품 보기'를 누를 때만 검색

## 4단계 — 데이터 품질 · 출처 정책
- 품질 대시보드: 5,198건 중 카드 가능 4,494건(86.5%), 문제 12건
- **농사로 향토·종가음식 사용 안 함** → `RECIPE_CATALOG_SOURCES`(기본 `foodsafety,epis`)
- 수집기 개선: 여러 묶음 재료 분량 합산(+`parts`), 괄호 오류·묶음 표기 처리. 식품안전나라 133건 합산·21건 복구
- **출처는 카드 맨 아래에만**, **'원문 그대로' 버튼 없앰**. AI 기본법(2026-01-22) 표시 의무 → AI 다듬음·AI 이미지 표시 유지. EPIS 이용 조건 미확인

## 5단계 — 관리자 백엔드 통합 (/admin)
사용자 결정: commerce_ai_generator 하나로 통합. integrated_system 소비자 백엔드 → **관리자 백엔드**, B2B는 commerce_ai 시스템의 일부로 **별도 탭**. FastAPI `/admin` 하나, 로그인 1곳(`ADMIN_ACCESS_TOKEN`).
- **운영 탭** `/admin`: 판매처 API 점검(쿠팡·네이버, 키 값 비노출) · 대화·추천 기록(`recipe_chat_session`·재료 답변·`search_log`·`product_click_log`, 읽기 전용) · 장바구니·결제 뼈대(토스·Stripe·PayPal 설정 여부, 국내/해외 분기 미리보기, 결제 안 함)
- **B2B 탭** `/admin/b2b`: integrated_system b2b 콘솔(공고 분석·후보·원가·견적요청서·제안서) · `/admin/b2b/monitor` 선물 입찰 모니터(나라장터 API 포함) · `/admin/b2b/evidence` 공급사 근거
- 코드: `app/admin/{auth,routes}.py`, `app/admin/ops/`, `app/admin/b2b/`, `app/admin/shared/`, `scripts/admin/{collect_bids,import_legacy_gift_db}.py`. 데이터 기본 `data/admin/`(SQLite), 운영은 Postgres 권장. 관리자 LLM `ADMIN_LLM_PROVIDER`(사용자 설정: anthropic)
- 보류: React 화면(ui_ux)과 매일 예시 카드를 만드는 integrated_system 작업은 배포 단계에서 함께 옮김

## 6단계 — 답변 화면 겹침 · 실행 가능한 조리 설명 (easy-v3)
- **겹침 원인**: `ChatWindow`가 Tailwind에 없는 색 `canvas`를 써서 헤더·입력창 배경이 투명했음 → `paper`로 교체. 자동 스크롤을 문서 스크롤 하나로 정리(긴 답변은 시작부터, 위에서 읽는 중이면 위치 유지). 반응형 브라우저 검증만 — **실기기 키보드·iOS Safari 미검증**
- **조리 설명** (`easy_view.py`, PROMPT_VERSION `easy-v3`): 특징+전체 진행 / 재료 "N인분 기준·원문 분량" / 번호 목록 단계(큰 카드 없음, 조리 모드 없음) / 단계별 "다음으로 넘어가는 때" / 필요한 단계만 주의·잘 안 되면(최대 4) / 출처에서 원문과 일반 조리 제안 구분
  - 원문 순서 변경·재료 투입 단계 이동·새 숫자/분량 → 거부. 완료 신호는 원문 구절(6자 이상)이면 **구절 그대로** '원문' 표시, 아니면 지시 없는 상태만 '일반 제안'. 단계 시작 조건은 앞 단계 신호로 이동
  - 기본 재료표에서 컵→mL 환산 제거(원문이 컵 용량을 정하지 않음, 고객이 기준을 고를 때만 참고값). 인분·시간·난이도·열량은 '원문 표기'
- **실제 DeepSeek 검증**(deepseek-v4-flash, Mac dry-run): v2에서 '원문' 신호가 "2분 더 끓이기"를 빠뜨린 바꿔쓰기, 원문에 없는 조건, 원문과 어긋난 팁 → v3에서 해소. v3에서 단계 시작 조건이 다음 단계에 붙는 문제 → 검사로 앞 단계로 이동
- 남은 위험: 팁·보충이 원문과 미묘하게 어긋나는지는 자동 검사 불가(프롬프트 규칙만). 저장은 `scripts.build_recipe_easy_views --apply`
- 백업: `recipe_chat_api_backups/20261029_1700_layout`, `20261029_2330_step3`
