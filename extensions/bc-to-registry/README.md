# bc-to-registry — 브랜드커넥트 링크를 등록부에 저장 (크롬 확장, 2026-11-19)

브랜드커넥트 화면에서 **사람이 '링크 발급'을 누르면**, 오른쪽 아래 'commerce_ai 등록부' 창에 그 상품이 나오고
**'등록부에 저장'** 한 번으로 `data/naver_connect_links.csv` 에 들어갑니다 (관리자 API `POST /admin/api/connect/links`).
상품명·스토어명·판매가(할인 전)·할인가·수수료율은 브랜드커넥트 응답 값 그대로 — 손으로 붙여 넣지 않습니다.

## 설치 (맥 Chrome)
1. `chrome://extensions` → 오른쪽 위 '개발자 모드' 켜기 → '압축해제된 확장 프로그램을 로드합니다' →
   `~/commerce_ai_generator/extensions/bc-to-registry` 폴더 선택 (stage2 에서 시험할 때는 stage2 쪽 폴더).
2. 확장 '세부정보' → '확장 프로그램 옵션' → 서버 주소(기본 `http://localhost:8001`)·관리자 토큰 저장 → '연결 확인'.
3. 브랜드커넥트 상품 검색 화면을 새로고침.

## 브랜드커넥트 창 여는 법 (둘 중 하나)
- 툴바의 초록 **'등'** 아이콘 → 브랜드커넥트 상품 찾기가 지금 창의 오른쪽 절반 창으로 열린다(이미 열려 있으면 앞으로).
  아이콘이 안 보이면 주소창 오른쪽 퍼즐 조각 → 이 확장 옆 핀(📌).
- 관리자 화면 트렌드 → 네이버 → '브랜드커넥트 상품 찾기'의 **브랜드커넥트 열기** (키워드를 복사해 둠).

## 쓰는 법
- 검색하면 검색어가 '키워드' 칸에 들어옵니다(고칠 수 있음, 고친 뒤에는 다음 검색어로 덮어쓰지 않음).
- '링크 발급'을 누르면 그 상품이 '방금 발급'으로 맨 위에 나옵니다. 검색 결과 중 예전에 발급해 둔 상품도 아래에 나옵니다.
- 이미 등록부에 있는 링크는 '저장됨 ✓'. 서버가 거부하면(중복·주류·건강기능식품·다른 상품 링크 등) 그 이유를 그대로 보여 줍니다.
- ↻ = 등록부 다시 읽기, ⚙ = 설정.

## 정책 선
- 브랜드커넥트 검색·발급 API 를 확장이 **스스로 부르지 않습니다**. `page_hook.js` 는 페이지가 부른 응답의 사본만 읽습니다.
- 버튼 한 번 = 한 상품. 자동·일괄 저장 없음.
- 서버 주소는 `localhost`/`127.0.0.1` 만 허용(토큰이 공개 주소로 나가지 않게). 토큰은 `chrome.storage.local` 에만, 화면에 다시 보이지 않음.

## 파일
- `lib/registry_row.js` — 응답 → 등록부 행 순수 함수 (확장·테스트 공용)
- `page_hook.js` — MAIN world, fetch/XHR 응답 읽기만
- `content.js`, `content.css` — 오른쪽 아래 창
- `background.js` — commerce_ai 관리자 API 호출 (브랜드커넥트 탭의 우리 스크립트에서 온 요청만)
- `options.html`, `options.js` — 서버 주소·토큰

## 테스트
- `node --test extensions/bc-to-registry/test/*.test.js`
- 서버 쪽: `tests/services/affiliate/test_connect_registry.py::test_admin_accepts_the_row_the_extension_sends`
